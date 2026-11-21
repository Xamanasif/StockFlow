"""Development-only stratified cohort and frozen-method portfolio coverage study."""
import hashlib
import re

import numpy as np
import pandas as pd

from .forecasting import history
from .research import METHODS, forecast, metrics
from .statistics import paired_block_comparison, summarize


def select_cohort(frame, excluded=(), per_stratum=8, seed=20261121, physical_codes_only=False):
    if not 1 <= per_stratum <= 20:
        raise ValueError('Invalid stratum quota')
    start = frame.date.min()
    development = frame[frame.is_sale & (frame.date <= start+pd.Timedelta(days=59))]
    candidates = []
    for sku, group in development.groupby('sku'):
        if physical_codes_only and not re.fullmatch(r'[0-9]{5}[A-Za-z]{0,2}',str(sku)):
            continue
        if sku in set(excluded) or group.date.min() > start+pd.Timedelta(days=13) or group.date.nunique() < 2:
            continue
        candidates.append({'sku':str(sku),'development_units':int(group.quantity.sum()),
                           'recorded_sale_days':int(group.date.nunique()),
                           'zero_recorded_day_fraction':1-group.date.nunique()/60,
                           'first_sale':str(group.date.min().date())})
    candidates.sort(key=lambda r:(r['development_units'],r['sku']))
    for i,row in enumerate(candidates):
        volume=['low','middle','high'][min(2,3*i//len(candidates))]
        density='sparse' if row['zero_recorded_day_fraction']>.5 else 'dense'
        row['stratum']=volume+'_'+density
        row['selection_rank']=hashlib.sha256(f'{seed}:{row["sku"]}'.encode()).hexdigest()
    strata=[]; selected=[]
    for volume in ['low','middle','high']:
        for density in ['sparse','dense']:
            name=volume+'_'+density
            group=sorted([r for r in candidates if r['stratum']==name],key=lambda r:r['selection_rank'])
            take=group[:per_stratum]
            selected.extend(take)
            strata.append({'stratum':name,'eligible_products':len(group),'selected_products':len(take),
                           'requested_products':per_stratum,'quota_shortfall':max(0,per_stratum-len(group))})
    if not selected:
        raise ValueError('No eligible development products')
    return {'selection_start':str(start.date()),'selection_end':str((start+pd.Timedelta(days=59)).date()),
            'seed':seed,'excluded_products':sorted(excluded),'eligible_products':len(candidates),
            'identifier_rule':'five digits plus up to two letters; heuristic excludes manual/service codes' if physical_codes_only else 'all canonical sale SKUs',
            'strata':strata,'products':selected,
            'limitations':'First-60-day descriptive volume/density strata; pre-entry and missing dates are assumed zero recorded sales. Quotas are not filled from other strata.'}


def seasonal_scale(training, period=7):
    values=np.asarray(training,dtype=float)
    if values.ndim!=1 or not np.isfinite(values).all() or period<1:
        raise ValueError('Invalid MASE scaling history')
    if len(values)<=period:
        return None
    scale=float(np.abs(values[period:]-values[:-period]).mean())
    return scale if scale>0 else None


def coverage_study(frame,selection,weeks=13):
    if not 2<=weeks<=26:
        raise ValueError('Invalid weekly fold count')
    if len({r['sku'] for r in selection['products']})!=len(selection['products']):
        raise ValueError('Duplicate cohort products')
    last=frame.date.max()-pd.Timedelta(days=1)
    groups={str(sku):group for sku,group in frame.groupby('sku')}
    rows=[];failures=[]
    for product in selection['products']:
        sku=product['sku']
        if sku not in groups:
            raise ValueError('Selected product missing from canonical source')
        product_frame=groups[sku]
        for offset in range(14+7*(weeks-1),13,-7):
            cutoff=last-pd.Timedelta(days=offset)
            for method in METHODS:
                try:
                    train=history(product_frame,sku,cutoff)
                    scale=seasonal_scale(train)
                    prediction=forecast(product_frame,sku,cutoff,7,method)
                    dates=pd.to_datetime([p['date'] for p in prediction])
                    actual=history(product_frame,sku,cutoff+pd.Timedelta(days=7)).reindex(dates,fill_value=0).to_numpy()
                    metric=metrics(actual,[p['units'] for p in prediction])
                    rows.append({'sku':sku,'stratum':product['stratum'],'cutoff':str(cutoff.date()),'method':method,
                                 **metric,'seasonal_scale_units':scale,'mase':metric['mae']/scale if scale is not None else None,
                                 'actual':actual.tolist(),'predictions':prediction})
                except ValueError as exc:
                    failures.append({'sku':sku,'cutoff':str(cutoff.date()),'method':method,'error':str(exc)})
    def aggregate(group):
        summary=summarize(group)
        for row in summary:
            mase=[r['mase'] for r in group if r['method']==row['method'] and r['mase'] is not None]
            count=sum(r['method']==row['method'] for r in group)
            row.update({'mean_product_fold_mase':float(np.mean(mase)) if mase else None,
                        'mase_defined_product_folds':len(mase),'mase_undefined_product_folds':count-len(mase)})
        return summary
    products=[]
    for product in selection['products']:
        subset=[r for r in rows if r['sku']==product['sku']]
        methods=aggregate(subset)
        baseline=next(r for r in methods if r['method']=='weekday_mean')
        for row in methods:
            row['absolute_error_difference_vs_weekday']=row['absolute_error']-baseline['absolute_error']
        products.append({'sku':product['sku'],'stratum':product['stratum'],'methods':methods})
    expected=len(selection['products'])*weeks*len(METHODS)
    paired=[]
    if not failures and len(rows)==expected:
        paired=[paired_block_comparison(rows,m,block_weeks=2) for m in METHODS if m!='weekday_mean']
    return {'scope':'Retrospective exploratory cross-product coverage; same retailer, frozen methods, no new confirmatory holdout',
            'weeks':weeks,'product_count':len(selection['products']),'expected_product_method_folds':expected,
            'observed_product_method_folds':len(rows),'latest_target_date':str((last-pd.Timedelta(days=7)).date()),
            'summary':aggregate(rows),'segments':[{'stratum':s['stratum'],'methods':aggregate([r for r in rows if r['stratum']==s['stratum']])} for s in selection['strata']],
            'products':products,'paired_resampling':paired,'failures':failures,'rows':rows,
            'complete_paired_coverage':not failures and len(rows)==expected,
            'mase_definition':'Product-fold MAE / mean absolute seven-day training difference; undefined for zero scale. Mean MASE weights defined product-folds equally.'}
