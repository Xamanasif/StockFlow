"""Cohort leakage, heterogeneous metric boundaries and release failure semantics."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import pandas as pd

from app.coverage import select_cohort, seasonal_scale, coverage_study
from app.data import COLUMNS, load_dataset, validate
from app.main import app
from app.research import METHODS, forecast


class CoverageTests(unittest.TestCase):
    def fixture(self):
        start=pd.Timestamp('2024-01-01')
        rows=[]
        for i in range(12):
            frequency=[1,2,4,8][i%4]
            for day in range(180):
                if day%frequency==0:
                    rows.append([f'{i}-{day}',f'P{i:02}',start+pd.Timedelta(days=day),i+1,2])
        return validate(pd.DataFrame(rows,columns=COLUMNS))[0]

    def test_cohort_is_deterministic_excludes_old_and_ignores_later_sales(self):
        frame=self.fixture()
        expected=select_cohort(frame,excluded=['P00'],per_stratum=2)
        altered=frame.copy()
        altered.loc[altered.date>altered.date.min()+pd.Timedelta(days=59),'quantity']=999999
        self.assertEqual(expected,select_cohort(altered,excluded=['P00'],per_stratum=2))
        self.assertEqual(expected,select_cohort(frame.sample(frac=1,random_state=3),excluded=['P00'],per_stratum=2))
        self.assertNotIn('P00',[r['sku'] for r in expected['products']])

    def test_strata_accounting_and_underfilled_quotas_are_visible(self):
        result=select_cohort(self.fixture(),per_stratum=8)
        self.assertEqual(sum(r['selected_products'] for r in result['strata']),len(result['products']))
        self.assertTrue(any(r['quota_shortfall']>0 for r in result['strata']))
        self.assertTrue(all(r['selected_products']<=8 for r in result['strata']))
        self.assertEqual(len({r['sku'] for r in result['products']}),len(result['products']))

    def test_late_or_single_sale_products_are_ineligible(self):
        frame=self.fixture()
        start=frame.date.min()
        raw=pd.concat([frame[COLUMNS],pd.DataFrame([['x','LATE',start+pd.Timedelta(days=20),5,2],['y','LATE',start+pd.Timedelta(days=30),5,2],['z','ONE',start,2,2]],columns=COLUMNS)],ignore_index=True)
        clean,_=validate(raw)
        result=select_cohort(clean)
        self.assertFalse({'LATE','ONE'} & {r['sku'] for r in result['products']})

    def test_manual_service_codes_are_excluded_by_declared_item_identifier_rule(self):
        frame=self.fixture()
        frame['sku']=frame.sku.str.replace('P','100',regex=False)
        manual=frame[frame.sku.eq('10000')].copy();manual['sku']='M'
        combined=pd.concat([frame,manual],ignore_index=True)
        result=select_cohort(combined,physical_codes_only=True)
        self.assertNotIn('M',[r['sku'] for r in result['products']])
        self.assertTrue(result['products'])

    def test_seasonal_scale_has_training_only_units_and_undefined_edges(self):
        self.assertEqual(seasonal_scale(list(range(14))),7)
        self.assertIsNone(seasonal_scale([0]*28))
        self.assertIsNone(seasonal_scale([3]*28))
        self.assertIsNone(seasonal_scale([1]*7))
        with self.assertRaises(ValueError):seasonal_scale([1,float('nan')])

    def test_isolating_product_preserves_all_frozen_forecasts(self):
        frame,_,_=load_dataset();sku='SKU-001';cutoff=frame.date.max()-pd.Timedelta(days=20)
        for method in METHODS:
            self.assertEqual(forecast(frame,sku,cutoff,7,method),forecast(frame[frame.sku.eq(sku)],sku,cutoff,7,method))

    def selection(self):
        return {'products':[{'sku':'SKU-001','stratum':'fixture_dense'},{'sku':'SKU-002','stratum':'fixture_sparse'}],
                'strata':[{'stratum':'fixture_dense'},{'stratum':'fixture_sparse'}]}

    def test_study_preserves_pairing_and_excludes_final_actuals(self):
        frame,_,_=load_dataset()
        result=coverage_study(frame,self.selection(),weeks=2)
        self.assertTrue(result['complete_paired_coverage'])
        self.assertEqual(len(result['rows']),20)
        changed=frame.copy();changed.loc[changed.date>=changed.date.max()-pd.Timedelta(days=7),'quantity']=999999
        self.assertEqual(result,coverage_study(changed,self.selection(),weeks=2))
        for row in result['rows']:
            if row['seasonal_scale_units']:
                self.assertAlmostEqual(row['mase'],row['mae']/row['seasonal_scale_units'])

    def test_missing_history_blocks_inference_and_keeps_failures(self):
        frame,_,_=load_dataset()
        changed=frame[~frame.sku.eq('SKU-001') | (frame.date>frame.date.max()-pd.Timedelta(days=5))]
        result=coverage_study(changed,self.selection(),weeks=2)
        self.assertFalse(result['complete_paired_coverage'])
        self.assertTrue(result['failures'])
        self.assertEqual(result['paired_resampling'],[])
        bad=copy.deepcopy(self.selection());bad['products']*=2
        with self.assertRaises(ValueError):coverage_study(frame,bad,weeks=2)

    def test_api_labels_cohort_source_and_does_not_return_all_prediction_rows(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'artifacts').mkdir()
            selection={'selection':{'strata':[]}}
            study={'scope':'exploratory','product_count':2,'weeks':13,'latest_target_date':'2011-01-01',
                   'summary':[],'segments':[],'failures':[],'complete_paired_coverage':True,'rows':['not-for-screen']}
            result={'utc':'fixture','dataset_sha256':'other','protocol_sha256':'p','study':study,'protected_before':{'x':'h'},'protected_after':{'x':'h'}}
            (root/'artifacts/coverage-selection-v3a.json').write_text(json.dumps(selection))
            (root/'artifacts/coverage-study-v3a.json').write_text(json.dumps(result))
            source=Path(__file__).resolve().parents[1]/'data/demo_transactions.csv'
            with patch('app.main.ROOT',root),patch.dict(os.environ,{'STOCKFLOW_CSV':str(source)}),TestClient(app) as client:
                response=client.get('/api/research/coverage')
            self.assertEqual(response.status_code,200)
            self.assertTrue(response.json()['stale_for_active_dataset'])
            self.assertTrue(response.json()['prior_evidence_preserved'])
            self.assertNotIn('rows',response.json())


class ReleaseTests(unittest.TestCase):
    def test_global_interpreter_cannot_claim_isolated_acceptance(self):
        from scripts import verify_release
        with patch.object(sys,'argv',['verify','--require-isolated']),patch.object(sys,'prefix','same'),patch.object(sys,'base_prefix','same'):
            with self.assertRaises(SystemExit):verify_release.main()

    def test_failed_command_is_recorded_and_never_promoted_to_pass(self):
        from scripts import verify_release
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'requirements.lock').write_text('fixture')
            def run(command,**kwargs):
                return SimpleNamespace(returncode=1 if 'unittest' in command else 0,stdout='Ran 2 tests\n',stderr='')
            with patch.object(verify_release,'ROOT',root),patch.object(verify_release,'code_hash',return_value='fixed'),patch.object(sys,'argv',['verify']),patch.object(verify_release.subprocess,'run',side_effect=run),patch('builtins.print'):
                with self.assertRaises(SystemExit):verify_release.main()
            reports=list((root/'artifacts/releases').glob('*/report.json'))
            self.assertEqual(len(reports),1)
            report=json.loads(reports[0].read_text())
            self.assertEqual(report['status'],'failed')
            self.assertFalse(report['browser_requested'])
            self.assertEqual(next(r for r in report['checks'] if r['check']=='unit_api')['tests'],2)


if __name__=='__main__':
    unittest.main()
