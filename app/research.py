"""Fold-local forecasting and explicit empirical uncertainty; no holdout selection."""
import math
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from .forecasting import history

METHODS = ['mean_28', 'weekday_mean', 'seasonal_naive', 'croston_sba', 'ridge']

def features(values, day):
    return [values[-1], values[-7], values[-14], np.mean(values[-7:]), day.dayofweek]

def forecast(frame, sku, cutoff, horizon=7, method='mean_28'):
    if method not in METHODS or not 1 <= horizon <= 90:
        raise ValueError('Unsupported method or horizon')
    s = history(frame, sku, cutoff)
    if len(s) < 28:
        raise ValueError('Insufficient history: require 28 days since first sale')
    values = s.tolist()
    dates = pd.date_range(pd.Timestamp(cutoff)+pd.Timedelta(days=1), periods=horizon)
    model = None
    if method == 'ridge':
        x = [features(values[:i], s.index[i]) for i in range(14, len(s))]
        model = make_pipeline(StandardScaler(), Ridge(alpha=10)).fit(x, values[14:])
    nonzero = np.flatnonzero(s.to_numpy() > 0)
    rate = 0.
    if len(nonzero):
        z, p, prev = values[nonzero[0]], float(nonzero[0]+1), nonzero[0]
        for i in nonzero[1:]:
            z += .1*(values[i]-z); p += .1*((i-prev)-p); prev = i
        rate = .95*z/p
    output = []
    for day in dates:
        if method == 'mean_28': v = s.tail(28).mean()
        elif method == 'weekday_mean': v = s.tail(56)[s.tail(56).index.dayofweek == day.dayofweek].mean()
        elif method == 'seasonal_naive': v = values[-7]
        elif method == 'croston_sba': v = rate
        else: v = model.predict([features(values, day)])[0]
        v = max(0., float(v)); values.append(v)
        output.append({'date': day.date().isoformat(), 'units': v})
    return output

def metrics(actual, predicted):
    a, p = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    total = float(a.sum()); error = float(abs(a-p).sum())
    return {'actual_units': total, 'absolute_error': error, 'observations': len(a),
            'wape': error/total if total else None, 'mae': error/len(a) if len(a) else None,
            'signed_error': float((p-a).sum())}

def radius(errors, level=.8):
    if not errors: return None
    return float(sorted(errors)[min(len(errors), math.ceil((len(errors)+1)*level))-1])

def select_products(frame):
    start = frame.date.min(); end = start+pd.Timedelta(days=59)
    sales = frame[frame.is_sale & (frame.date <= end)]
    first = sales.groupby('sku').date.min()
    eligible = first[first <= start+pd.Timedelta(days=13)].index
    totals = sales[sales.sku.isin(eligible)].groupby('sku').quantity.sum()
    return sorted(totals.index, key=lambda x: (-totals[x], x))[:5]

def evaluate(frame, final=False):
    last = frame.date.max()-pd.Timedelta(days=1)
    products = select_products(frame); rows = []; failures = []
    for sku in products:
        actual_series = history(frame, sku, last)
        for method in METHODS:
            errors = []
            for offset in [42,35,28]:
                cutoff = last-pd.Timedelta(days=offset)
                try:
                    pred = forecast(frame,sku,cutoff,7,method)
                    a = actual_series.reindex(pd.to_datetime([p['date'] for p in pred]),fill_value=0).to_numpy()
                    errors.extend(abs(a-np.array([p['units'] for p in pred])).tolist())
                except ValueError as exc: failures.append({'sku':sku,'method':method,'stage':'calibration','error':str(exc)})
            q = radius(errors)
            for offset in ([7] if final else [21,14]):
                cutoff = last-pd.Timedelta(days=offset)
                try:
                    pred = forecast(frame,sku,cutoff,7,method)
                    a = actual_series.reindex(pd.to_datetime([p['date'] for p in pred]),fill_value=0).to_numpy()
                    p = np.array([v['units'] for v in pred]); lower = np.maximum(0,p-(q or 0)); upper=p+(q or 0)
                    rows.append({'sku':sku,'method':method,'cutoff':str(cutoff.date()),
                                 'segment':'intermittent' if (actual_series.loc[:cutoff]==0).mean()>.5 else 'regular',
                                 **metrics(a,p),'interval_radius':q,'covered':int(((a>=lower)&(a<=upper)).sum()) if q is not None else None,
                                 'width_sum':float((upper-lower).sum()) if q is not None else None,
                                 'predictions':pred,'actual':a.tolist()})
                except ValueError as exc: failures.append({'sku':sku,'method':method,'stage':'evaluation','error':str(exc)})
    summary=[]
    for method in METHODS:
        subset=[r for r in rows if r['method']==method]; n=sum(r['observations'] for r in subset)
        total=sum(r['actual_units'] for r in subset); ae=sum(r['absolute_error'] for r in subset)
        valid=[r for r in subset if r['covered'] is not None]; interval_n=sum(r['observations'] for r in valid)
        summary.append({'method':method,'actual_units':total,'observations':n,'absolute_error':ae,
                        'wape':ae/total if total else None,'mae':ae/n if n else None,
                        'signed_error':sum(r['signed_error'] for r in subset),
                        'covered':sum(r['covered'] for r in valid),'interval_observations':interval_n,
                        'coverage':sum(r['covered'] for r in valid)/interval_n if interval_n else None,
                        'mean_width':sum(r['width_sum'] for r in valid)/interval_n if interval_n else None})
    segments=[]
    for method in METHODS:
        for segment in ['regular','intermittent']:
            group=[r for r in rows if r['method']==method and r['segment']==segment]
            n=sum(r['observations'] for r in group); total=sum(r['actual_units'] for r in group)
            ae=sum(r['absolute_error'] for r in group)
            segments.append({'method':method,'segment':segment,'observations':n,'actual_units':total,
                             'absolute_error':ae,'wape':ae/total if total else None,
                             'mae':ae/n if n else None,'signed_error':sum(r['signed_error'] for r in group)})
    return {'split':'final' if final else 'development','products':products,'rows':rows,'failures':failures,'summary':summary,'segment_summary':segments}
