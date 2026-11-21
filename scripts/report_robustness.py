"""Render a transparent exploratory report and standalone scientific figure."""
import json

from app.data import ROOT


def main():
    source = ROOT/'artifacts/exploratory-robustness.json'
    result = json.loads(source.read_text(encoding='utf-8'))
    rows = result['forecast_summary']
    paired = [r for r in result['paired_resampling'] if r['block_weeks']==2]
    table = '|Method|Absolute error / actual units|WAPE|MAE units|Signed bias units|\n|---|---:|---:|---:|---:|\n'
    for row in rows:
        table += f"|{row['method']}|{row['absolute_error']:.2f} / {row['actual_units']:.0f}|{row['wape']:.2%}|{row['mae']:.2f}|{row['signed_error']:.2f}|\n"
    intervals = '|Alternative vs weekday mean|WAPE difference (pp)|95% resampling interval (pp)|Block length (weeks)|\n|---|---:|---:|---:|\n'
    for row in result['paired_resampling']:
        low, high = row['wape_delta_resampling_interval_95']
        intervals += f"|{row['challenger']}|{row['wape_delta_percentage_points']:.2f}|[{low:.2f}, {high:.2f}]|{row['block_weeks']}|\n"
    policies = '|Forecast|Policy|Mean scenario cost GBP|Range GBP|Mean unit fill|Cost wins/ties/losses vs weekday greedy|\n|---|---|---:|---:|---:|---:|\n'
    for row in result['policy_summary']:
        policies += f"|{row['method']}|{row['policy']}|{row['cost_pence_mean']/100:.2f}|{row['cost_pence_min']/100:.2f}–{row['cost_pence_max']/100:.2f}|{row['fill_rate_mean']:.2%}|{row['cost_wins']}/{row['cost_ties']}/{row['cost_losses']}|\n"
    methods = {r['method']:r for r in rows}
    relative = 1-methods['weekday_mean']['absolute_error']/methods['ridge']['absolute_error']
    report = f'''# Exploratory research extension: forecasts, decisions and uncertainty

This extension was specified on 2026-11-21 **after the original final result had been inspected**. It is not new confirmatory holdout evidence. The original protocol, final receipt and result were preserved byte-for-byte; source hashes are recorded in the JSON. No model settings or original final outcomes were changed. The source and algorithm snapshot for the original final evaluation remains in source-at-final.zip.

## Business question and finding

Does better forecasting reliably produce a better purchasing decision? Evidence does not establish a universal relationship. On thirteen historical weekly folds, weekday mean has {relative:.2%} lower absolute error than Ridge. The earlier seven-day final favored seasonal naive, whereas the wider exploratory sample favors weekday mean. This rank instability cautions against selecting a model from one short period. Under tight assumed budgets, the policy and inventory constraints can dominate the forecast difference.

## Historical forecast evaluation

Five fixed methods, five products selected from the first sixty days, thirteen seven-day origins and 455 shared product-days; denominator **32,660 recorded units**. Dates and actual/predicted rows are retained in exploratory-robustness.json. Latest target date: {result['evaluation']['latest_target_date']}. First and last cutoffs: {min(r['cutoff'] for r in result['evaluation']['rows'])} through {max(r['cutoff'] for r in result['evaluation']['rows'])}. Zero missing calendar days are an assumption about recorded sales, not unconstrained demand. All methods and losses are retained.

{table}

![Historical WAPE and paired resampling intervals](../artifacts/forecast-robustness.png)

## Paired temporal resampling

Each weekly block keeps all products together. Circular fixed-length blocks resample neighboring weeks and wrap the end of the historical sample to its start. Each replicate recomputes both absolute error and actual-unit denominator. With two-week blocks, Ridge-minus-weekday WAPE is +14.77 percentage points; the approximate percentile interval is [7.39, 20.51]. Negative differences favor the alternative; positive differences favor weekday mean. All 2,000 ratio replicates had defined denominators in this actual run.

{intervals}

The point estimate is the observed finite-sample difference. The interval is conditional on a small, selected, temporally dependent historical sample and block-resampling assumptions. Thirteen weeks are few; circular boundaries are artificial, longer dependence/nonstationarity can invalidate inference, and multiple comparisons were not adjusted. A nonzero interval is not proof of universal model superiority. One-, two- and three-week intervals are all reported rather than selecting the most favorable one. This is not an independent confirmation after final inspection.

Method context: the [arch project's time-series bootstrap documentation](https://bashtage.github.io/arch/doc/bootstrap/timeseries-bootstraps.html) distinguishes circular fixed-length blocks with wrap-around from ordinary non-wrapping moving blocks. StockFlow implements its bounded NumPy resampling directly; it does not depend on the arch library. See statistics.paired_block_comparison and the sign/denominator/pairing tests.

## Decision robustness under common inputs

Seventy-five replay runs: five forecast methods × three purchasing policies × five seeds (2026–2030). Every seed shares the same exogenous sequence across policies. Seeds vary lead-time jitter only; the same fourteen-day proxy demand totals **4,087 recorded units** in every run. Starting inventory, weekly cash grants and all cost parameters are identical. No revenue, profit or realised savings is estimated.

{policies}

Static MILP sometimes reduces hypothetical cost by a small amount while fill rates tie; Ridge/greedy and Croston/greedy lose under the default tight cash regime. This is a narrow static-coverage optimiser, not a dynamic cost optimum. The five seed outcomes are supplier-jitter robustness checks, not independent customer-demand studies. Interpret alongside the eight original one-factor sensitivity regimes in real-development.json. Paid pipeline and terminal inventory remain visible in each daily run.

## SQL evidence and scope

real-analytics-v2.json records the development-only SQL mart: **13,287 loaded canonical lines**, **306,947 positive-sale units**, 142 later canonical lines excluded, and source/cutoff identities. These are five selected products, not a million-row SQL benchmark. The original full-workbook import separately audited 1,067,371 source lines. SQL transaction and calendar totals are reconciled against Python before commit. Canonical row ordinals identify positions in the canonical subset; they are not original Excel row numbers.

Read ANALYTICS_QUERIES.sql for joins, CTEs, window frames, cancellation accounting and development ABC segmentation. A preceding-seven-day window ends at 1 PRECEDING, and zero-filled calendar rows make row counts correspond to days after first sale. ABC uses first-sixty-day units within the subset and is not a profitability classification. Approximate observed sale value is explicitly separated from assumed procurement costs.

## Reproduction and boundaries

Protocol: EXPLORATORY_PROTOCOL_V2.md, SHA-256 `{result['protocol_sha256']}`. Source SHA-256 `{result['code_sha256']}`; dataset SHA-256 `{result['dataset_sha256']}`. Exact command: `{result['command']}`. Original final hashes before/after are in the JSON. Software/platform versions and UTC timestamp accompany the results.

Run to a new output path to preserve previous exploratory evidence. Do not delete the original FINAL receipt or rerun final evaluation. No new training algorithms, tuned policies or paid model calls were introduced. No research novelty, publication acceptance, production deployment, authenticated purchasing, causal inventory benefit or PhD equivalence is claimed. Independent external data and prospective decisions would be needed for stronger generalisation.
'''
    (ROOT/'docs/RESEARCH_EXTENSION_REPORT.md').write_text(report, encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig, axes = plt.subplots(1,2,figsize=(13,4.8),layout='constrained')
    labels = [r['method'].replace('_',' ') for r in rows]
    values = [100*r['wape'] for r in rows]
    axes[0].barh(labels,values,color=['#47738c' if r['method']!='weekday_mean' else '#087b76' for r in rows])
    axes[0].invert_yaxis(); axes[0].set_xlim(0,max(values)*1.2)
    for i,v in enumerate(values): axes[0].text(v+1,i,f'{v:.2f}%',va='center')
    axes[0].set_xlabel('Global WAPE (%) | 32,660 recorded units')
    axes[0].set_title('13 historical weekly folds · 455 product-days')
    for i,row in enumerate(paired):
        low,high=row['wape_delta_resampling_interval_95']; point=row['wape_delta_percentage_points']
        axes[1].errorbar(point,i,xerr=[[point-low],[high-point]],fmt='o',color='#174d9c',capsize=4)
    axes[1].set_yticks(range(len(paired)),[r['challenger'].replace('_',' ') for r in paired]); axes[1].invert_yaxis()
    axes[1].axvline(0,color='#666',linestyle='--',linewidth=1)
    axes[1].set_xlabel('Alternative − weekday mean WAPE (percentage points)')
    axes[1].set_title('95% resampling intervals · two-week blocks')
    fig.suptitle('Exploratory analysis after final inspection · no final-period rerun',fontsize=13)
    fig.savefig(ROOT/'artifacts/forecast-robustness.png',dpi=180)
    fig.savefig(ROOT/'artifacts/forecast-robustness.svg')
    plt.close(fig)
    print('Wrote research extension report and PNG/SVG figure; relative error reduction:',relative)


if __name__=='__main__':
    main()
