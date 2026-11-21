import json
import os
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient
from app.data import load_dataset, validate, COLUMNS
from app.forecasting import predict, backtest
from app.planning import Item, PlanRequest, allocate
from app.main import app

class DataTests(unittest.TestCase):
    def setUp(self):
        self.frame, self.audit, self.meta = load_dataset()

    def test_demo_is_explicit(self):
        self.assertEqual(self.meta['kind'], 'synthetic_demo')

    def test_missing_column(self):
        with self.assertRaises(ValueError): validate(self.frame.drop(columns='sku'))

    def test_invalid_quantity(self):
        frame = self.frame[COLUMNS].copy(); frame.loc[0,'quantity'] = float('inf')
        with self.assertRaises(ValueError): validate(frame)

    def test_null_identifiers(self):
        frame = self.frame[COLUMNS].copy(); frame.loc[0,'sku'] = None
        with self.assertRaises(ValueError): validate(frame)

    def test_cancellation_not_sales(self):
        frame = pd.DataFrame([['C1','A','2024-01-01',-2,3],['2','A','2024-01-01',4,3]],columns=COLUMNS)
        clean, report = validate(frame)
        self.assertEqual(report['cancellation_rows'],1)
        self.assertEqual(int(clean.loc[clean.is_sale,'quantity'].sum()),4)

    def test_duplicates_flagged_not_dropped(self):
        raw = pd.concat([self.frame[COLUMNS].head(1)]*2,ignore_index=True)
        clean, report = validate(raw)
        self.assertEqual(len(clean),2); self.assertEqual(report['possible_duplicate_rows'],1)

    def test_checksum_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.csv'; p.write_text('not the original')
            p.with_suffix('.meta.json').write_text(json.dumps(self.meta))
            with self.assertRaisesRegex(ValueError,'checksum'): load_dataset(p)

    def test_uci_aliases(self):
        raw = self.frame[COLUMNS].head(2).rename(columns={'invoice':'Invoice','sku':'StockCode','date':'InvoiceDate','quantity':'Quantity','unit_price':'Price'})
        clean,_=validate(raw); self.assertEqual(len(clean),2)

class ForecastTests(unittest.TestCase):
    def setUp(self): self.frame,_,_=load_dataset()

    def test_future_sales_cannot_change_past_forecast(self):
        cutoff=self.frame.date.max()-pd.Timedelta(days=14); sku='SKU-001'
        before=predict(self.frame,sku,cutoff)
        altered=self.frame.copy(); altered.loc[altered.date>cutoff,'quantity']=999999
        self.assertEqual(before,predict(altered,sku,cutoff))

    def test_horizon_dates(self):
        cutoff=self.frame.date.max(); rows=predict(self.frame,'SKU-001',cutoff,10)
        self.assertEqual(len(rows),10)
        self.assertEqual(rows[0]['date'],(cutoff+pd.Timedelta(days=1)).date().isoformat())

    def test_backtests_include_two_baselines(self):
        rows=backtest(self.frame,'SKU-001')
        self.assertEqual({r['method'] for r in rows},{'mean_28','weekday_mean'})

    def test_zero_actual_wape_is_undefined(self):
        frame=self.frame.copy(); last=frame.date.max()
        frame.loc[(frame.sku=='SKU-001')&(frame.date>last-pd.Timedelta(days=7)),'quantity']=0
        frame,_=validate(frame[COLUMNS])
        recent=[r for r in backtest(frame,'SKU-001') if r['cutoff']==(last-pd.Timedelta(days=7)).date().isoformat()]
        self.assertTrue(all(r['wape'] is None for r in recent))

class PlannerTests(unittest.TestCase):
    def item(self,**kw): return Item(**({'sku':'A','unit_cost_pence':125,'on_hand':0,'pack':4,'moq':6}|kw))

    def test_zero_budget(self):
        r=allocate(PlanRequest(budget_pence=0,items=[self.item()]),{'A':20})
        self.assertEqual(r['spent_pence'],0)

    def test_budget_and_capacity(self):
        for budget in [0,500,1000,3000]:
            for capacity in [0,4,8,20]:
                r=allocate(PlanRequest(budget_pence=budget,capacity_units=capacity,items=[self.item()]),{'A':20})
                self.assertLessEqual(r['spent_pence'],budget)
                self.assertLessEqual(r['occupied_units_after_plan'],capacity)
                n=r['rows'][0]['order_units']; self.assertTrue(n==0 or (n>=8 and n%4==0))

    def test_existing_inventory_counts(self):
        with self.assertRaises(ValueError): allocate(PlanRequest(capacity_units=5,items=[self.item(on_hand=6)]),{'A':20})

    def test_no_overbuy_for_zero_target(self):
        r=allocate(PlanRequest(items=[self.item(on_hand=50)]),{'A':20})
        self.assertEqual(r['rows'][0]['order_units'],0)

    def test_duplicate_sku_rejected(self):
        with self.assertRaises(ValueError): PlanRequest(items=[self.item(),self.item()])

    def test_nonfinite_forecast(self):
        with self.assertRaises(ValueError): allocate(PlanRequest(items=[self.item()]),{'A':float('nan')})

    def test_deterministic_tie(self):
        items=[self.item(sku='B'),self.item(sku='A')]
        a=allocate(PlanRequest(items=items,budget_pence=1000),{'A':20,'B':20})
        b=allocate(PlanRequest(items=list(reversed(items)),budget_pence=1000),{'A':20,'B':20})
        self.assertEqual(a,b)

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.old=os.environ.get('STOCKFLOW_DB')
        os.environ['STOCKFLOW_DB']=str(Path(self.temp.name)/'test.db')
        self.client=TestClient(app)

    def tearDown(self):
        if self.old is None: os.environ.pop('STOCKFLOW_DB',None)
        else: os.environ['STOCKFLOW_DB']=self.old
        self.temp.cleanup()

    def test_dashboard(self): self.assertEqual(self.client.get('/').status_code,200)
    def test_health(self):
        value=self.client.get('/api/health').json()
        self.assertEqual(value['status'],'ok')
        self.assertEqual(value['llm'],'local_rules_no_llm')
        self.assertEqual(value['assistant_mode'],'local rules / no LLM')
    def test_unknown_product(self): self.assertEqual(self.client.get('/api/forecast/unknown').status_code,404)
    def test_unknown_assumptions(self):
        r=self.client.post('/api/plans',json={'items':[{'sku':'unknown','unit_cost_pence':1,'on_hand':0}]})
        self.assertEqual(r.status_code,422)
    def test_persist_exact_snapshot(self):
        r=self.client.post('/api/plans',json={'items':[{'sku':'SKU-001','unit_cost_pence':100,'on_hand':0}]} )
        self.assertEqual(r.status_code,200)
        result=r.json(); saved=self.client.get('/api/plans/'+result['id']).json()
        self.assertEqual(saved,result); self.assertFalse(saved['optimality_claim'])
    def test_negative_budget(self):
        r=self.client.post('/api/plans',json={'budget_pence':-1,'items':[{'sku':'SKU-001','unit_cost_pence':1,'on_hand':0}]})
        self.assertEqual(r.status_code,422)

if __name__=='__main__': unittest.main()
