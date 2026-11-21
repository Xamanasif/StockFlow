"""Reproducible research artefacts. Final access leaves a non-reusable receipt."""
import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import sklearn
import scipy
from app.data import ROOT, load_dataset, code_hash
from app.registry import sha
from app.research import evaluate, select_products
from app.simulation import Scenario, compare

def main():
    p=argparse.ArgumentParser(); p.add_argument('--data',type=Path); p.add_argument('--final',action='store_true'); p.add_argument('--sensitivity',action='store_true')
    p.add_argument('--output',type=Path,default=ROOT/'artifacts/development.json'); args=p.parse_args()
    frame,_,meta=load_dataset(args.data)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    protocol=ROOT/'docs/EVALUATION_PROTOCOL.md'
    if args.final:
        if args.output.name=='development.json': raise SystemExit('Final requires distinct --output')
        receipt=ROOT/'artifacts'/('FINAL-'+meta['sha256']+'.json')
        with receipt.open('x',encoding='utf-8') as f:
            json.dump({'status':'started; never automatically rerun','utc':datetime.now(timezone.utc).isoformat(),'protocol_sha256':sha(protocol)},f)
    result={'utc':datetime.now(timezone.utc).isoformat(),'dataset_sha256':meta['sha256'],'provenance':meta,
            'protocol_sha256':sha(protocol),'code_sha256':code_hash(),'seed':2026,'command':'python -m scripts.evaluate '+' '.join(sys.argv[1:]),
            'versions':{'python':platform.python_version(),'pandas':pd.__version__,'scikit_learn':sklearn.__version__,'scipy':scipy.__version__},
            'evaluation':evaluate(frame,args.final)}
    if not args.final:
        products=select_products(frame); rows=compare(frame,products,Scenario())
        result['comparison']=rows
        if args.sensitivity:
            variants=[('budget_low',{'budget_pence':5000}),('budget_high',{'budget_pence':80000}),('lead_long',{'lead_days':10}),
                      ('shortfall_low',{'shortfall_pence':20}),('shortfall_high',{'shortfall_pence':1000}),('initial_zero',{'initial_stock':0}),
                      ('initial_high',{'initial_stock':80}),('synthetic_variability',{'variability':1.})]
            result['sensitivity']={name:compare(frame,products,Scenario(**change)) for name,change in variants}
    if args.output.exists():
        backup=args.output.with_name(args.output.stem+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
        args.output.rename(backup)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'output':str(args.output),'summary':result['evaluation']['summary'],'failures':len(result['evaluation']['failures'])},indent=2))

if __name__=='__main__': main()
