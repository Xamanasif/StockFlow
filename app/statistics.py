"""Paired temporal resampling with explicit small-sample and dependence limitations."""
import math
import json
import numpy as np
import pandas as pd

from .forecasting import history
from .research import METHODS, forecast, metrics, select_products


def extended_folds(frame, weeks=13):
    if not 2 <= weeks <= 26:
        raise ValueError('Use between 2 and 26 historical weeks')
    last = frame.date.max()-pd.Timedelta(days=1)
    rows, failures = [], []
    products = select_products(frame)
    for offset in range(14+7*(weeks-1), 13, -7):
        cutoff = last-pd.Timedelta(days=offset)
        for sku in products:
            actual_series = history(frame, sku, cutoff+pd.Timedelta(days=7))
            for method in METHODS:
                try:
                    prediction = forecast(frame, sku, cutoff, 7, method)
                    actual = actual_series.reindex(pd.to_datetime([r['date'] for r in prediction]), fill_value=0).to_numpy()
                    rows.append({'cutoff': str(cutoff.date()), 'sku': sku, 'method': method,
                                 **metrics(actual, [r['units'] for r in prediction]),
                                 'actual': actual.tolist(), 'predictions': prediction})
                except ValueError as exc:
                    failures.append({'cutoff': str(cutoff.date()), 'sku': sku, 'method': method, 'error': str(exc)})
    return {'products': products, 'weeks': weeks, 'rows': rows, 'failures': failures,
            'latest_target_date': str((last-pd.Timedelta(days=7)).date()),
            'label': 'Exploratory historical extension after original final inspection; not a new holdout'}


def paired_block_comparison(rows, challenger, baseline='weekday_mean', replicates=2000, block_weeks=2, seed=20261121):
    if not 100 <= replicates <= 100000 or not 1 <= block_weeks <= 13:
        raise ValueError('Invalid resampling bounds')
    def indexed(method):
        group = [r for r in rows if r['method'] == method]
        mapping = {(r['cutoff'], r['sku']): r for r in group}
        if len(mapping) != len(group):
            raise ValueError('Duplicate product/fold observations')
        return mapping
    first, second = indexed(challenger), indexed(baseline)
    if not first or first.keys() != second.keys():
        raise ValueError('Paired comparison requires identical nonempty product/fold coverage')
    for key in first:
        if first[key]['actual'] != second[key]['actual'] or first[key]['observations'] != second[key]['observations']:
            raise ValueError('Contradictory paired actuals or observation counts')
        if [p['date'] for p in first[key]['predictions']] != [p['date'] for p in second[key]['predictions']]:
            raise ValueError('Paired target dates differ')
    cutoffs = sorted({key[0] for key in first})
    if len(cutoffs) < 2 or block_weeks > len(cutoffs):
        raise ValueError('Insufficient weekly blocks')
    if any((pd.Timestamp(b)-pd.Timestamp(a)).days != 7 for a, b in zip(cutoffs, cutoffs[1:])):
        raise ValueError('Weekly blocks must be contiguous, ordered seven days apart')
    blocks = []
    for cutoff in cutoffs:
        keys = [key for key in first if key[0] == cutoff]
        blocks.append([sum(first[k]['absolute_error'] for k in keys),
                       sum(second[k]['absolute_error'] for k in keys),
                       sum(first[k]['actual_units'] for k in keys),
                       sum(first[k]['observations'] for k in keys)])
    matrix = np.asarray(blocks, dtype=float)
    totals = matrix.sum(axis=0)
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(cutoffs), size=(replicates, math.ceil(len(cutoffs)/block_weeks)))
    indices = ((starts[:, :, None]+np.arange(block_weeks)) % len(cutoffs)).reshape(replicates, -1)[:, :len(cutoffs)]
    samples = matrix[indices].sum(axis=1)
    valid = samples[:, 2] > 0
    deltas = 100*(samples[valid, 0]-samples[valid, 1])/samples[valid, 2]
    mae_deltas = (samples[:, 0]-samples[:, 1])/samples[:, 3]
    return {'challenger': challenger, 'baseline': baseline, 'weeks': len(cutoffs),
            'paired_product_folds': len(first), 'actual_units': float(totals[2]), 'observations': int(totals[3]),
            'wape_delta_percentage_points': float(100*(totals[0]-totals[1])/totals[2]) if totals[2] else None,
            'wape_delta_resampling_interval_95': np.quantile(deltas, [.025, .975]).tolist() if len(deltas) else None,
            'mae_delta_units': float((totals[0]-totals[1])/totals[3]),
            'mae_delta_resampling_interval_95': np.quantile(mae_deltas, [.025, .975]).tolist(),
            'replicates': replicates, 'valid_wape_replicates': int(valid.sum()),
            'undefined_wape_replicates': int((~valid).sum()), 'block_weeks': block_weeks, 'seed': seed,
            'interpretation': 'Negative difference favors challenger. Exploratory circular moving-week-block resampling; small sample, stationarity assumptions and unadjusted multiple comparisons limit inference.'}


def summarize(rows):
    output = []
    for method in METHODS:
        subset = [r for r in rows if r['method'] == method]
        denominator = sum(r['actual_units'] for r in subset)
        ae = sum(r['absolute_error'] for r in subset)
        n = sum(r['observations'] for r in subset)
        output.append({'method': method, 'actual_units': denominator, 'observations': n,
                       'absolute_error': ae, 'wape': ae/denominator if denominator else None,
                       'mae': ae/n if n else None, 'signed_error': sum(r['signed_error'] for r in subset)})
    return output


def summarize_policy_seeds(seed_runs, baseline=('weekday_mean', 'greedy')):
    seeds = sorted({r['seed'] for r in seed_runs})
    if len(seeds) < 2:
        raise ValueError('At least two common seeds required')
    by_seed = {}
    for seed in seeds:
        rows = [r for r in seed_runs if r['seed'] == seed]
        keys = {(r['method'], r['policy']) for r in rows}
        if len(keys) != len(rows) or len({r['exogenous_sha256'] for r in rows}) != 1 or len({r['proxy_demand_units'] for r in rows}) != 1:
            raise ValueError('Duplicate policies or unequal exogenous inputs within seed')
        if baseline not in keys:
            raise ValueError('Missing paired baseline')
        if len({json.dumps(r['assumptions'],sort_keys=True) for r in rows})!=1:
            raise ValueError('Scenario assumptions differ within seed')
        by_seed[seed] = {(r['method'], r['policy']): r for r in rows}
    assumptions = [{k:v for k,v in r['assumptions'].items() if k!='seed'} for r in seed_runs]
    if len({json.dumps(a,sort_keys=True) for a in assumptions})!=1:
        raise ValueError('Only the seed may vary across this comparison')
    keys = set(by_seed[seeds[0]])
    if any(set(by_seed[seed]) != keys for seed in seeds):
        raise ValueError('Unequal policy coverage across seeds')
    output = []
    for method, policy in sorted(keys):
        rows = [by_seed[seed][method, policy] for seed in seeds]
        differences = [r['scenario_cost_pence']-by_seed[r['seed']][baseline]['scenario_cost_pence'] for r in rows]
        fill = [r['fill_rate'] for r in rows if r['fill_rate'] is not None]
        costs = [r['scenario_cost_pence'] for r in rows]
        output.append({'method': method, 'policy': policy, 'seeds': seeds,
                       'cost_pence_mean': float(np.mean(costs)), 'cost_pence_min': min(costs), 'cost_pence_max': max(costs),
                       'fill_rate_mean': float(np.mean(fill)) if fill else None,
                       'fill_rate_min': min(fill) if fill else None, 'fill_rate_max': max(fill) if fill else None,
                       'paired_cost_difference_pence_mean': float(np.mean(differences)),
                       'cost_wins': sum(d < 0 for d in differences), 'cost_ties': sum(d == 0 for d in differences),
                       'cost_losses': sum(d > 0 for d in differences),
                       'baseline': {'method': baseline[0], 'policy': baseline[1]}})
    return output
