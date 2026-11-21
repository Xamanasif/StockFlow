"""Retain an actual saved local demo proposal and independently traced arithmetic."""
import json
import os
from fastapi.testclient import TestClient
from app.data import ROOT, load_dataset
from app.forecasting import history, predict
from app.main import app

def main():
    previous=os.environ.pop('STOCKFLOW_CSV',None)
    try:
        frame,_,meta=load_dataset()
        body={'budget_pence':10000,'capacity_units':500,'horizon_days':14,
              'items':[{'sku':f'SKU-{i:03}','unit_cost_pence':100+i*50,'on_hand':12,'on_order':0,'lead_days':7,'pack':6,'moq':12,'priority':1} for i in range(1,6)]}
        with TestClient(app) as client:
            r=client.post('/api/plans',json=body,headers={'Idempotency-Key':'worked-example-v1'}); r.raise_for_status(); plan=r.json()
            saved=client.get('/api/plans/'+plan['id']).json(); assert saved==plan
        (ROOT/'artifacts/worked-proposal.json').write_text(json.dumps(saved,indent=2),encoding='utf-8')
        item=body['items'][0]; cutoff=frame.date.max(); series=history(frame,item['sku'],cutoff)
        pred=predict(frame,item['sku'],cutoff,21); row=next(r for r in plan['rows'] if r['sku']==item['sku'])
        trace={'label':'synthetic demo; assumed procurement and stock','invoice_rows':frame.loc[frame.sku.eq(item['sku'])].tail(3).astype(str).to_dict('records'),
               'last_seven_calendar_units':{str(d.date()):v for d,v in series.tail(7).items()},'forecast_21_days':pred,
               'forecast_sum':sum(v['units'] for v in pred),'assumptions':item,'allocation':row,'dataset_sha256':meta['sha256'],'run_id':plan['id']}
        (ROOT/'artifacts/worked-trace.json').write_text(json.dumps(trace,indent=2),encoding='utf-8')
        text=f'''# Actual saved worked example\n\nSynthetic demo, assumed GBP procurement/stock. Run `{plan['id']}`; snapshot `{plan['sha256']}`.\n\nFor {item['sku']}, last seven calendar units are {series.tail(7).tolist()}. Lead+review=21 days, expected units={trace['forecast_sum']:.4f}; stock=12, on-order=0, pack=6, MOQ=12. Rounded requested units={row['requested_units']}; allocated={row['order_units']}; uncovered rounded target={row['uncovered_target_units']}. Row cash={row['order_units']} × {row['unit_cost_pence']} = {row['spend_pence']} pence.\n\nPlan total spends {plan['spent_pence']} of {body['budget_pence']} pence and reserves {plan['occupied_units_after_plan']} units. Sum row spends and compare to this total. Full source rows, dates, forecast and inputs are in worked-trace.json; exact persisted response is worked-proposal.json. This is a constructed scenario, not a historical order.\n'''
        (ROOT/'artifacts/worked-example.md').write_text(text,encoding='utf-8'); print(text)
    finally:
        if previous is not None: os.environ['STOCKFLOW_CSV']=previous

if __name__=='__main__': main()
