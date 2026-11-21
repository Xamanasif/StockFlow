import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from .data import ROOT, load_dataset, code_hash
from .forecasting import predict, backtest, history as daily_history
from .planning import PlanRequest, allocate
from .optimizer import optimize
from .registry import datasets
from .research import select_products
from .simulation import Scenario, compare
from .storage import db, digest, save_assumptions, challenge, confirm

app=FastAPI(title='StockFlow',version='1.0.0')
log=logging.getLogger('stockflow')
log.setLevel(logging.INFO)
if not log.handlers: log.addHandler(logging.StreamHandler())

@lru_cache(maxsize=4)
def cached_dataset(path,mtime,size):
    return load_dataset(path)

def dataset():
    path=Path(os.environ.get('STOCKFLOW_CSV',ROOT/'data/demo_transactions.csv')).resolve()
    stat=path.stat()
    meta=path.with_suffix('.meta.json').stat()
    return cached_dataset(str(path),(stat.st_mtime_ns,meta.st_mtime_ns),stat.st_size)

def public_metadata(metadata):
    # Preserve audit totals but keep full-workbook product dictionaries in local evidence.
    value=json.loads(json.dumps(metadata))
    for name in ['audit','original_row_accounting']:
        if name in value: value[name].pop('product_entry_exit',None)
    return value

@app.middleware('http')
async def observe(request:Request,call_next):
    request_id=str(uuid.uuid4()); start=time.monotonic()
    try:
        response=await call_next(request); response.headers['X-Request-ID']=request_id
        try: data_hash=dataset()[2]['sha256']
        except (OSError,ValueError): data_hash=None
        log.info(json.dumps({'request_id':request_id,'run_id':request.path_params.get('run_id'),
                             'route':request.scope.get('route').path if request.scope.get('route') else 'static',
                             'duration_ms':round((time.monotonic()-start)*1000),'status':response.status_code,
                             'code_version':'1.0.0','method_version':'weekday_mean-v1; replay-v1','dataset_sha256':data_hash,
                             'error_category':'client_error' if 400<=response.status_code<500 else 'server_error' if response.status_code>=500 else None}))
        return response
    except Exception:
        log.error(json.dumps({'request_id':request_id,'category':'unhandled_server_error'}))
        return Response(json.dumps({'detail':'Internal error; inspect local server logs','request_id':request_id}),status_code=500,media_type='application/json')

@app.get('/api/health')
def health():
    return {'status':'ok','stage':'portfolio prototype','llm':'configured_unverified' if os.environ.get('GROQ_API_KEY') else 'local_rules_no_llm','assistant_mode':'Groq adapter configured' if os.environ.get('GROQ_API_KEY') else 'local rules / no LLM','execution':'local review; no external orders'}

@app.get('/api/ready')
def ready():
    try:
        _,_,m=dataset()
        with db() as con: con.execute('SELECT 1')
        return {'ready':True,'dataset_sha256':m['sha256']}
    except (ValueError,OSError): raise HTTPException(503,'Data or storage unavailable')

@app.get('/api/datasets')
def list_datasets():
    return {'available':[{'version':'demo','kind':'synthetic_demo'},*[public_metadata(m) for m in datasets()]],'selection':'STOCKFLOW_CSV server environment; restart after changing'}

@app.get('/api/overview')
def overview():
    frame,audit,metadata=dataset()
    skus=select_products(frame)
    return {'provenance':public_metadata(metadata),'quality':audit,'cutoff':str(frame.date.max().date()),'skus':skus,
            'selection':'up to five products ranked using first 60 days only','calendar_assumption':'Missing days mean zero recorded sales under scenario coverage assumption; not verified demand.'}

@app.post('/api/datasets/{version}/select')
def select_dataset(version:str):
    if version=='demo': path=ROOT/'data/demo_transactions.csv'
    else:
        registered={m['version'] for m in datasets()}
        if version not in registered: raise HTTPException(404,'Unknown registered version')
        path=ROOT/'data/registry'/version/'transactions.csv'
    os.environ['STOCKFLOW_CSV']=str(path)
    return {'selected':version,'scope':'single-process local session; restart uses STOCKFLOW_CSV environment or demo'}

@app.get('/api/forecast/{sku}')
def forecast(sku:str):
    frame,_,metadata=dataset()
    if sku not in set(frame.loc[frame.is_sale,'sku']): raise HTTPException(404,'Unknown SKU')
    try:
        s=daily_history(frame,sku,frame.date.max())
        return {'evidence_id':'product:'+sku+':'+metadata['sha256'],'sku':sku,'dataset_sha256':metadata['sha256'],
                'forecast':predict(frame,sku,frame.date.max()),'history':[{'date':str(d.date()),'units':int(v)} for d,v in s.tail(56).items()],
                'backtests':backtest(frame,sku),'uncertainty':'See saved calibrated research evaluation; this operational baseline is a point forecast.'}
    except ValueError as exc: raise HTTPException(422,str(exc))

@app.post('/api/assumptions')
def assumptions(request:PlanRequest):
    with db() as con: h=save_assumptions(con,request.model_dump())
    return {'hash':h,'currency':'GBP','provenance':{k:'user-supplied scenario assumption' for k in request.model_dump()},'fields':'Inventory, procurement costs and lead times are not measured from transactions.'}

@app.get('/api/assumptions')
def get_assumptions():
    with db() as con:
        row=con.execute("SELECT a.hash,a.payload FROM assumptions a JOIN settings s ON a.hash=s.value WHERE s.key='assumptions'").fetchone()
    return {'hash':row[0],'values':json.loads(row[1]),'currency':'GBP','provenance':'user scenario assumptions'} if row else {'values':None,'status':'No saved assumptions'}

@app.post('/api/plans')
def plan(request:PlanRequest,policy:str='greedy',idempotency_key:str | None=Header(default=None,max_length=100)):
    frame,_,metadata=dataset()
    if policy not in ['greedy','milp']: raise HTTPException(422,'Unknown policy')
    if any(i.sku not in set(frame.loc[frame.is_sale,'sku']) for i in request.items): raise HTTPException(422,'Assumptions contain unknown SKU')
    try:
        totals={i.sku:sum(x['units'] for x in predict(frame,i.sku,frame.date.max(),request.horizon_days+i.lead_days)) for i in request.items}
        result=optimize(request,totals) if policy=='milp' else allocate(request,totals)
    except ValueError as exc: raise HTTPException(422,str(exc))
    result.update({'assumptions':request.model_dump(),'assumptions_hash':digest(request.model_dump()),'provenance':public_metadata(metadata),
                   'assumption_field_provenance':{'currency':'GBP','fields':{k:'user-supplied scenario assumption' for k in request.model_dump() if k!='items'},
                       'items':{i.sku:{k:'user-supplied scenario assumption' for k in i.model_dump()} for i in request.items}},
                   'cutoff':str(frame.date.max().date()),'created_utc':datetime.now(timezone.utc).isoformat(),
                   'forecast_method':'weekday_mean','code_version':'1.0.0','code_sha256':code_hash(),'status':'proposal_only_not_purchase_order'})
    h=digest(result); run_id=str(uuid.uuid4())
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        fingerprint=digest({'request':request.model_dump(),'dataset':metadata['sha256'],'policy':policy})
        if idempotency_key:
            prior=con.execute('SELECT fingerprint,run_id FROM idempotency WHERE key=?',(idempotency_key,)).fetchone()
            if prior:
                if prior[0]!=fingerprint: raise HTTPException(409,'Idempotency key already used for different inputs')
                row=con.execute('SELECT hash,payload FROM runs WHERE id=?',(prior[1],)).fetchone()
                return {'id':prior[1],'sha256':row[0],**json.loads(row[1])}
        save_assumptions(con,request.model_dump())
        con.execute('INSERT INTO runs VALUES(?,?,?,?)',(run_id,datetime.now(timezone.utc).isoformat(),h,json.dumps(result,sort_keys=True,allow_nan=False)))
        if idempotency_key: con.execute('INSERT INTO idempotency VALUES(?,?,?)',(idempotency_key,fingerprint,run_id))
    return {'id':run_id,'sha256':h,**result}

@app.get('/api/plans')
def history():
    with db() as con:
        rows=con.execute('SELECT r.id,r.created,r.hash,v.label FROM runs r LEFT JOIN reviews v ON v.run_id=r.id ORDER BY r.created DESC LIMIT 100').fetchall()
    return [{'id':r[0],'created':r[1],'sha256':r[2],'review':r[3]} for r in rows]

@app.get('/api/plans/{run_id}')
def read_plan(run_id:str):
    with db() as con: row=con.execute('SELECT hash,payload FROM runs WHERE id=?',(run_id,)).fetchone()
    if not row: raise HTTPException(404,'Plan not found')
    payload=json.loads(row[1])
    if digest(payload)!=row[0]: raise HTTPException(409,'Snapshot integrity failure')
    return {'id':run_id,'sha256':row[0],**payload}

@app.post('/api/plans/{run_id}/review')
def review(run_id:str):
    p=read_plan(run_id)
    return {'preview':p,**challenge(run_id,p['sha256'],p['provenance']['sha256'],p.get('assumptions_hash',digest(p['assumptions'])))}

class Confirmation(BaseModel):
    model_config=ConfigDict(extra='forbid')
    token:str=Field(max_length=80)
    sha256:str=Field(min_length=64,max_length=64)

@app.post('/api/confirm')
def confirmation(request:Confirmation):
    try: return confirm(request.token,request.sha256,dataset()[2]['sha256'])
    except ValueError as exc: raise HTTPException(409,str(exc))

@app.post('/api/compare')
def comparison(scenario:Scenario):
    frame,_,metadata=dataset()
    try: rows=compare(frame,select_products(frame),scenario)
    except ValueError as exc: raise HTTPException(422,str(exc))
    return {'dataset_sha256':metadata['sha256'],'provenance':public_metadata(metadata),'results':rows,'limitations':'Observed-sales proxy; assumed costs/inventory; no realised savings; paid pipeline commitments; physical-plus-pipeline capacity reserved.'}

@app.get('/api/evaluation')
def evaluation():
    p=ROOT/'artifacts/development.json'
    if not p.exists(): raise HTTPException(404,'Run python -m scripts.evaluate first')
    value=json.loads(p.read_text(encoding='utf-8'))
    return {**value,'stale_for_active_dataset':value['dataset_sha256']!=dataset()[2]['sha256']}

@app.get('/api/analytics')
def analytics():
    from .analytics import read_report
    try:
        return read_report(Path(os.environ.get('STOCKFLOW_ANALYTICS',ROOT/'data/analytics.db')),dataset()[2]['sha256'])
    except (FileNotFoundError,LookupError) as exc:
        raise HTTPException(404,str(exc))

@app.get('/api/research/robustness')
def robustness_evidence():
    path=ROOT/'artifacts/exploratory-robustness.json'
    if not path.exists(): raise HTTPException(404,'Run python -m scripts.robustness --data <canonical CSV> first')
    value=json.loads(path.read_text(encoding='utf-8'))
    return {k:value[k] for k in ['utc','scope','dataset_sha256','code_sha256','protocol_sha256','forecast_summary','paired_resampling','policy_summary']} | {
        'stale_for_active_dataset':value['dataset_sha256']!=dataset()[2]['sha256'],
        'weeks':value['evaluation']['weeks'],'latest_target_date':value['evaluation']['latest_target_date'],
        'final_evidence_preserved':value['protected_final_before']==value['protected_final_after']}

@app.get('/api/plans/{run_id}/export')
def export(run_id:str,format:str='json'):
    p=read_plan(run_id)
    if format=='csv':
        import csv,io
        out=io.StringIO(); keys=['sku','requested_units','order_units','spend_pence','uncovered_target_units']
        writer=csv.writer(out); writer.writerow(['plan_id','snapshot_sha256','dataset_sha256',*keys])
        for r in p['rows']:
            values=[p['id'],p['sha256'],p['provenance']['sha256'],*[r[k] for k in keys]]
            writer.writerow(["'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v for v in values])
        return Response(out.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=proposal.csv'})
    if format not in ['json','report']: raise HTTPException(422,'Use csv/json/report')
    return Response('StockFlow decision report\nGBP minor units; assumed stock/cost/lead times; proposal only.\n'+json.dumps(p,indent=2) if format=='report' else json.dumps(p,indent=2),media_type='text/plain' if format=='report' else 'application/json')

@app.get('/api/research/coverage')
def coverage_evidence():
    path=ROOT/'artifacts/coverage-study-v3a.json'
    selection_path=ROOT/'artifacts/coverage-selection-v3a.json'
    if not path.exists() or not selection_path.exists():
        raise HTTPException(404,'Run scripts.prepare_coverage and scripts.evaluate_coverage first')
    value=json.loads(path.read_text(encoding='utf-8'))
    selection=json.loads(selection_path.read_text(encoding='utf-8'))
    study=value['study']
    return {'utc':value['utc'],'scope':study['scope'],'dataset_sha256':value['dataset_sha256'],
            'protocol_sha256':value['protocol_sha256'],'product_count':study['product_count'],'weeks':study['weeks'],
            'latest_target_date':study['latest_target_date'],'summary':study['summary'],'segments':study['segments'],
            'strata':selection['selection']['strata'],'failures':study['failures'],
            'complete_paired_coverage':study['complete_paired_coverage'],
            'stale_for_active_dataset':value['dataset_sha256']!=dataset()[2]['sha256'],
            'prior_evidence_preserved':value['protected_before']==value['protected_after']}

class Question(BaseModel):
    model_config=ConfigDict(extra='forbid')
    question:str=Field(min_length=1,max_length=2000)
    run_id:str=Field(min_length=1,max_length=80)

@app.post('/api/assistant')
def assistant(q:Question):
    from .assistant import answer
    p=read_plan(q.run_id)
    current=get_assumptions()
    return answer(q.question,p,dataset()[2]['sha256'],current_assumptions_hash=current.get('hash'))

@app.api_route('/api/{unknown:path}',methods=['GET','POST','PUT','DELETE','PATCH'])
def unknown_api(unknown:str):
    raise HTTPException(404,'Unknown API route')

app.mount('/',StaticFiles(directory=ROOT/'app/static',html=True),name='dashboard')
