"""Immutable dataset directories, published by atomic directory rename."""
import hashlib
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from .data import ALIASES, COLUMNS, validate, ROOT

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_raw(source):
    source=Path(source)
    if source.suffix.lower()=='.xlsx':
        return pd.concat(pd.read_excel(source,sheet_name=None).values(),ignore_index=True)
    if source.suffix.lower()!='.csv': raise ValueError('Use CSV or XLSX')
    return pd.read_csv(source,dtype={'Invoice':str,'InvoiceNo':str,'StockCode':str,'invoice':str,'sku':str})

def preview(raw):
    raw=raw.rename(columns=ALIASES)
    missing=sorted(set(COLUMNS)-set(raw.columns))
    if missing: raise ValueError('Missing columns: '+', '.join(missing))
    canonical=raw[COLUMNS].copy(); reasons=pd.Series('',index=raw.index,dtype=str)
    def flag(mask,code): reasons.loc[mask]+=code+';'
    for col in ['invoice','sku']:
        flag(raw[col].isna() | raw[col].astype(str).str.strip().eq(''),'missing_'+col)
    dates=pd.to_datetime(raw.date,errors='coerce'); flag(dates.isna(),'invalid_date')
    for col in ['quantity','unit_price']:
        values=pd.to_numeric(raw[col],errors='coerce')
        flag(values.isna() | ~values.between(-1e9,1e9),'invalid_'+col)
        if col=='quantity': flag(values.notna() & values.mod(1).ne(0),'fractional_quantity')
        else: flag(values.lt(0),'negative_price')
    rejected=canonical.loc[reasons.ne('')].copy(); rejected['reason_codes']=reasons[reasons.ne('')]
    clean,audit=validate(canonical.loc[reasons.eq('')])
    audit.update({'input_rows':len(raw),'quarantined_rows':len(rejected),'retained_rows':len(clean),
                  'reason_counts':{c:int(reasons.str.contains(c).sum()) for c in sorted(set(';'.join(reasons).split(';'))-{''})},
                  'latest_day_may_be_partial':True,'zero_fill_assumption':'zero recorded sales, not verified demand'})
    sales=clean[clean.is_sale]
    if not sales.empty:
        audit['missing_calendar_days']=len(pd.date_range(sales.date.min(),sales.date.max()).difference(sales.date.unique()))
        audit['product_entry_exit']={str(k):{'first':str(v['min'].date()),'last':str(v['max'].date())} for k,v in sales.groupby('sku').date.agg(['min','max']).iterrows()}
    return clean,rejected,audit

def publish(source,registry=None,quarantine=False,source_url='user supplied; unverified origin',license_name='unverified',extra_metadata=None):
    registry=Path(registry or ROOT/'data/registry'); registry.mkdir(parents=True,exist_ok=True)
    clean,rejected,audit=preview(read_raw(source))
    if len(rejected) and not quarantine: raise ValueError('Invalid rows: preview and explicitly use --quarantine')
    if not clean.is_sale.any(): raise ValueError('No eligible sales')
    version=str(uuid.uuid4()); stage=registry/('.stage-'+version); stage.mkdir()
    try:
        shutil.copy2(source,stage/('raw'+Path(source).suffix))
        clean[COLUMNS].to_csv(stage/'transactions.csv',index=False); rejected.to_csv(stage/'quarantine.csv',index=False)
        meta={'version':version,'kind':'imported_historical_unverified_origin' if source_url.startswith('user') else 'real_historical_transactions',
              'source_url':source_url,'license':license_name,'attribution':'Chen, D. (2012). Online Retail II. DOI:10.24432/C5CG6D',
              'download_or_import_utc':datetime.now(timezone.utc).isoformat(),'source_file_sha256':sha(source),
              'sha256':sha(stage/'transactions.csv'),'currency':'GBP (original UCI); scenario costs independently assumed','audit':audit,
              'raw_privacy':'Original local snapshot may contain customer identifiers; never served by API.'}
        if extra_metadata:
            if set(extra_metadata) & set(meta): raise ValueError('Extra metadata cannot replace core provenance')
            meta.update(extra_metadata)
        (stage/'transactions.meta.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
        (stage/'manifest.json').write_text(json.dumps({'version':version,'canonical':'transactions.csv','metadata':'transactions.meta.json'}),encoding='utf-8')
        stage.rename(registry/version)
    except BaseException:
        shutil.rmtree(stage,ignore_errors=True); raise
    return registry/version/'transactions.csv'

def datasets(registry=None):
    root=Path(registry or ROOT/'data/registry')
    return [json.loads(p.read_text(encoding='utf-8')) for p in sorted(root.glob('*/transactions.meta.json')) if not p.parent.name.startswith('.')]
