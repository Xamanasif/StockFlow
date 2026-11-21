"""Semantic checks for SQL reconciliation, temporal pairing and new read-only reports."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import copy
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import pandas as pd

from app import analytics
from app.data import COLUMNS, load_dataset, validate
from app.main import app
from app.statistics import extended_folds, paired_block_comparison, summarize_policy_seeds


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)/'mart.db'
        start = pd.Timestamp('2024-01-01')
        rows = [[str(i), 'A', start+pd.Timedelta(days=i), i+1, 2] for i in range(30)]
        rows.extend([['B1','B',start,5,3],['C1','A',start+pd.Timedelta(days=3),-1,2]])
        self.frame, _ = validate(pd.DataFrame(rows, columns=COLUMNS))
        self.meta = {'sha256':'fixture-source-v1'}

    def tearDown(self):
        self.temp.cleanup()

    def test_sql_daily_reconciles_with_actual_fixture_arithmetic(self):
        built = analytics.build_mart(self.frame,self.meta,self.path)
        report = analytics.read_report(self.path,self.meta['sha256'])
        self.assertEqual(report['accounting']['positive_sale_units'],sum(range(1,23))+5)
        self.assertEqual(sum(r['recorded_units'] for r in report['products']),258)
        self.assertEqual(report['totals']['cancellation_rows'],1)
        self.assertEqual(report['cutoff'],'2024-01-22')
        self.assertEqual(built['accounting']['loaded_rows']+built['accounting']['excluded_later_rows'],len(self.frame))

    def test_idempotence_and_foreign_keys(self):
        first = analytics.build_mart(self.frame,self.meta,self.path)
        second = analytics.build_mart(self.frame,self.meta,self.path)
        self.assertEqual(first['run_id'],second['run_id'])
        self.assertEqual(second['status'],'existing_immutable_version')
        with closing(sqlite3.connect(self.path)) as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM mart_runs').fetchone()[0],1)
            self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_concurrent_loads_produce_one_version(self):
        with ThreadPoolExecutor(2) as pool:
            rows=list(pool.map(lambda _:analytics.build_mart(self.frame,self.meta,self.path),range(2)))
        self.assertEqual(rows[0]['run_id'],rows[1]['run_id'])
        self.assertEqual({r['status'] for r in rows},{'created','existing_immutable_version'})

    def test_preceding_window_excludes_current_row(self):
        result = analytics.build_mart(self.frame,self.meta,self.path)
        with closing(sqlite3.connect(self.path)) as con:
            row = con.execute('SELECT recorded_units,preceding_seven_day_units FROM v_daily_evidence WHERE run_id=? AND sku=? AND day=?',(result['run_id'],'A','2024-01-08')).fetchone()
        self.assertEqual(row,(8,28))

    def test_calendar_assumptions_and_abc_use_development_only(self):
        analytics.build_mart(self.frame,self.meta,self.path)
        products = {r['sku']:r for r in analytics.read_report(self.path,self.meta['sha256'])['products']}
        self.assertEqual(products['B']['assumed_zero_days'],21)
        self.assertEqual(products['A']['abc_class'],'A')
        self.assertEqual(products['B']['abc_class'],'C')

    def test_final_window_refused_and_later_rows_cannot_change_loaded_totals(self):
        with self.assertRaises(ValueError):
            analytics.build_mart(self.frame,self.meta,self.path,cutoff=self.frame.date.max())
        changed = self.frame.copy()
        changed.loc[changed.date>pd.Timestamp('2024-01-22'),'quantity']=999999
        analytics.build_mart(changed,self.meta,self.path)
        report = analytics.read_report(self.path,self.meta['sha256'])
        self.assertEqual(report['accounting']['positive_sale_units'],258)

    def test_midload_failure_rolls_back_every_fact_and_run(self):
        trigger="CREATE TRIGGER fail_daily BEFORE INSERT ON fact_daily_sales BEGIN SELECT RAISE(ABORT,'constructed disk-stage failure'); END;"
        with patch.object(analytics,'SCHEMA',analytics.SCHEMA+trigger):
            with self.assertRaises(sqlite3.IntegrityError):
                analytics.build_mart(self.frame,self.meta,self.path)
        with closing(sqlite3.connect(self.path)) as con:
            for table in ['mart_runs','dim_product','fact_transaction','fact_daily_sales']:
                self.assertEqual(con.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],0)

    def test_source_text_is_bound_as_values_and_wrong_hash_never_falls_back(self):
        changed = self.frame.copy()
        changed.loc[changed.sku.eq('B'),'sku']="B'); DROP TABLE mart_runs; --"
        analytics.build_mart(changed,self.meta,self.path)
        report = analytics.read_report(self.path,self.meta['sha256'])
        self.assertEqual(len(report['products']),2)
        with self.assertRaises(LookupError): analytics.read_report(self.path,'wrong-source')

    def test_api_reads_matching_dataset_and_missing_mart_is_404(self):
        frame,_,meta = load_dataset()
        with patch.dict(os.environ,{'STOCKFLOW_ANALYTICS':str(self.path),'STOCKFLOW_CSV':str(Path(__file__).resolve().parents[1]/'data/demo_transactions.csv')}):
            with TestClient(app) as client:
                self.assertEqual(client.get('/api/analytics').status_code,404)
                analytics.build_mart(frame,meta,self.path)
                response=client.get('/api/analytics')
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.json()['dataset_sha256'],meta['sha256'])

    def test_robustness_api_labels_other_source_and_returns_bounded_summary(self):
        import json
        root=Path(self.temp.name);(root/'artifacts').mkdir()
        fixture={'utc':'fixture','scope':'exploratory','dataset_sha256':'different','code_sha256':'c','protocol_sha256':'p',
                 'forecast_summary':[],'paired_resampling':[],'policy_summary':[],
                 'evaluation':{'weeks':13,'latest_target_date':'2024-01-01','rows':['large details omitted']},
                 'protected_final_before':{'id':'hash'},'protected_final_after':{'id':'hash'},'scenario_runs':['large details omitted']}
        (root/'artifacts/exploratory-robustness.json').write_text(json.dumps(fixture),encoding='utf-8')
        source=Path(__file__).resolve().parents[1]/'data/demo_transactions.csv'
        with patch('app.main.ROOT',root),patch.dict(os.environ,{'STOCKFLOW_CSV':str(source)}),TestClient(app) as client:
            response=client.get('/api/research/robustness')
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json()['stale_for_active_dataset'])
        self.assertTrue(response.json()['final_evidence_preserved'])
        self.assertNotIn('scenario_runs',response.json())


def paired_rows(zero=False):
    rows=[]
    for week in range(4):
        cutoff=pd.Timestamp('2024-01-01')+pd.Timedelta(days=7*week)
        for sku in ['A','B']:
            for method,predicted in [('weekday_mean',2),('ridge',1)]:
                actual=[0 if zero else 1]*7
                rows.append({'cutoff':str(cutoff.date()),'sku':sku,'method':method,'actual':actual,
                             'observations':7,'actual_units':sum(actual),'absolute_error':sum(abs(predicted-a) for a in actual),
                             'predictions':[{'date':str((cutoff+pd.Timedelta(days=i+1)).date()),'units':predicted} for i in range(7)]})
    return rows


class StatisticalTests(unittest.TestCase):
    def test_paired_constant_effect_has_correct_sign_units_and_interval(self):
        result=paired_block_comparison(paired_rows(),'ridge',replicates=500)
        self.assertEqual(result['wape_delta_percentage_points'],-100)
        self.assertEqual(result['wape_delta_resampling_interval_95'],[-100,-100])
        self.assertEqual(result['actual_units'],56)
        self.assertEqual(result['mae_delta_units'],-1)

    def test_zero_denominator_is_undefined_in_every_replicate(self):
        result=paired_block_comparison(paired_rows(True),'ridge',replicates=500)
        self.assertIsNone(result['wape_delta_percentage_points'])
        self.assertIsNone(result['wape_delta_resampling_interval_95'])
        self.assertEqual(result['undefined_wape_replicates'],500)
        self.assertEqual(result['mae_delta_units'],-1)

    def test_unpaired_duplicate_contradictory_dates_and_noncontiguous_weeks_fail(self):
        rows=paired_rows()
        bad=copy.deepcopy(rows);bad.pop()
        with self.assertRaises(ValueError):paired_block_comparison(bad,'ridge')
        with self.assertRaises(ValueError):paired_block_comparison(rows+[rows[0]],'ridge')
        bad=copy.deepcopy(rows);bad[0]['actual'][0]=4
        with self.assertRaises(ValueError):paired_block_comparison(bad,'ridge')
        bad=copy.deepcopy(rows);bad[0]['predictions'][0]['date']='2025-01-01'
        with self.assertRaises(ValueError):paired_block_comparison(bad,'ridge')
        bad=[r for r in rows if r['cutoff']!='2024-01-08']
        with self.assertRaises(ValueError):paired_block_comparison(bad,'ridge')

    def test_seeded_resampling_is_reproducible(self):
        rows=paired_rows();rows[-1]['absolute_error']=4
        self.assertEqual(paired_block_comparison(rows,'ridge',replicates=500),paired_block_comparison(rows,'ridge',replicates=500))

    def test_extended_research_does_not_use_final_actuals(self):
        frame,_,_=load_dataset()
        before=extended_folds(frame,weeks=2)
        changed=frame.copy();changed.loc[changed.date>=changed.date.max()-pd.Timedelta(days=7),'quantity']=999999
        self.assertEqual(before,extended_folds(changed,weeks=2))
        self.assertLessEqual(pd.Timestamp(before['latest_target_date']),frame.date.max()-pd.Timedelta(days=8))

    def test_seed_summary_checks_fairness_and_retains_losses(self):
        rows=[]
        for seed in [1,2]:
            for method,cost in [('weekday_mean',100),('ridge',120)]:
                rows.append({'seed':seed,'method':method,'policy':'greedy','exogenous_sha256':str(seed),
                             'proxy_demand_units':10,'scenario_cost_pence':cost,'fill_rate':.5,
                             'assumptions':{'seed':seed,'initial_stock':0}})
        result=summarize_policy_seeds(rows)
        ridge=next(r for r in result if r['method']=='ridge')
        self.assertEqual(ridge['cost_losses'],2)
        self.assertEqual(ridge['paired_cost_difference_pence_mean'],20)
        bad=copy.deepcopy(rows);bad[-1]['exogenous_sha256']='different'
        with self.assertRaises(ValueError):summarize_policy_seeds(bad)
        bad=copy.deepcopy(rows);bad[-1]['assumptions']['initial_stock']=10
        with self.assertRaises(ValueError):summarize_policy_seeds(bad)


if __name__=='__main__':
    unittest.main()
