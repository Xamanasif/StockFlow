"""Human-readable cohort coverage report, retaining failures, zero scales and losses."""
import json

from app.data import ROOT


def main():
    result=json.loads((ROOT/'artifacts/coverage-study-v3a.json').read_text(encoding='utf-8'))
    selection=json.loads((ROOT/'artifacts/coverage-selection-v3a.json').read_text(encoding='utf-8'))
    study=result['study']
    def pct(value):return 'undefined' if value is None else f'{100*value:.2f}%'
    def number(value):return 'undefined' if value is None else f'{value:.3f}'
    strata='|Stratum|Eligible products|Selected|Unfilled quota|\n|---|---:|---:|---:|\n'
    for row in selection['selection']['strata']:
        strata+=f"|{row['stratum']}|{row['eligible_products']}|{row['selected_products']}|{row['quota_shortfall']}|\n"
    summary='|Method|Absolute error / actual units|WAPE|MAE units|Mean seasonal MASE|Defined / undefined scaling folds|\n|---|---:|---:|---:|---:|---:|\n'
    for row in study['summary']:
        summary+=f"|{row['method']}|{row['absolute_error']:.2f} / {row['actual_units']:.0f}|{pct(row['wape'])}|{number(row['mae'])}|{number(row['mean_product_fold_mase'])}|{row['mase_defined_product_folds']} / {row['mase_undefined_product_folds']}|\n"
    segments='|Stratum|Method|Actual units|Product-days|WAPE|MAE units|\n|---|---|---:|---:|---:|---:|\n'
    for segment in study['segments']:
        for row in segment['methods']:
            segments+=f"|{segment['stratum']}|{row['method']}|{row['actual_units']:.0f}|{row['observations']}|{pct(row['wape'])}|{number(row['mae'])}|\n"
    products='|Product|Stratum|Actual units|Mean28 WAPE|Weekday WAPE|Seasonal naive WAPE|Croston WAPE|Ridge WAPE|\n|---|---|---:|---:|---:|---:|---:|---:|\n'
    outcomes={method:{'wins':0,'ties':0,'losses':0} for method in ['mean_28','seasonal_naive','croston_sba','ridge']}
    for product in study['products']:
        rows={r['method']:r for r in product['methods']}
        products+=f"|{product['sku']}|{product['stratum']}|{rows['weekday_mean']['actual_units']:.0f}|"+'|'.join(pct(rows[m]['wape']) for m in ['mean_28','weekday_mean','seasonal_naive','croston_sba','ridge'])+'|\n'
        for method,counts in outcomes.items():
            difference=rows[method]['absolute_error_difference_vs_weekday']
            counts['wins' if difference < -1e-9 else 'losses' if difference > 1e-9 else 'ties']+=1
    pair='|Alternative vs weekday|WAPE difference (pp)|95% two-week block resampling interval (pp)|\n|---|---:|---:|\n'
    for row in study['paired_resampling']:
        interval=row['wape_delta_resampling_interval_95']
        pair+=f"|{row['challenger']}|{number(row['wape_delta_percentage_points'])}|{'undefined' if interval is None else f'[{interval[0]:.2f}, {interval[1]:.2f}]'}|\n"
    text=f'''# Expanded portfolio coverage and release evidence

## What changed

The earlier studies used five high-volume products. This extension samples **{study['product_count']} different products**, excluding all five earlier SKUs, using first-sixty-day volume and recorded-sales sparsity. Existing forecast methods/hyperparameters remain unchanged. The same retailer is still the only data source; this is a retrospective exploratory cross-product generalisation check, not independent external validation or a fresh confirmatory holdout.

The initial development-only v3 sample contained manual code M. That selection was retained, and amendment v3a declared an item-code format rule before any new-cohort forecast evaluation. A new selection and canonical version were published rather than silently editing the old sample. The identifier rule is a heuristic: it excludes accounting/service-like codes but cannot prove every accepted code is physical merchandise. The original final result/receipt and v2 study remain byte-identical.

## Coverage and eligibility

Selection ends {selection['selection']['selection_end']}. Cohort seed {selection['selection']['seed']}. Eligible pool: {selection['selection']['eligible_products']} products. Quota deficits are retained; no future outcomes or final model performance were used to select products.

{strata}

No eligible low-volume/dense products satisfy this particular volume-tercile/calendar definition. That empty cell is a population property under the declared rules, not an omitted model loss. Missing/pre-entry days in the sixty-day selection calendar are explicitly assumed zero recorded sales. Sales capture and opening days are unverified.

## Frozen-method evaluation

{study['weeks']} non-overlapping seven-day origins, targets ending {study['latest_target_date']}. Complete paired coverage: **{study['complete_paired_coverage']}**. Failures: {len(study['failures'])}. Actual-unit denominators and product-day counts are retained for every model; no method is removed after losing.

{summary}

MASE = product-fold MAE divided by mean absolute seven-day training difference. The scaling denominator uses training history only. A zero/insufficient scale is undefined, not zero. Mean MASE weights defined product-folds equally; global WAPE weights actual units. Zero-target products may have undefined WAPE while still having finite absolute error. See [Forecasting: Principles and Practice, scaled errors](https://otexts.com/fpp3/toolbox.html#scaled-errors) for the seasonal scaling definition.

## Segment results

{segments}

## Every selected product

{products}

Alternative product absolute-error wins/ties/losses versus weekday mean (ties use tolerance1e-9): `{json.dumps(outcomes,sort_keys=True)}`. These are descriptive within-cohort results, not independent significance tests. A method may lose overall while helping individual products; the full table is retained.

## Paired temporal uncertainty

{pair}

The existing resampling method keeps each weekly cross-section together and resamples two-week circular blocks,2000 replicates. Negative differences favor the alternative. Thirteen weeks, artificial wrap-around, shared retailer effects, retrospective design and unadjusted comparisons limit inference. No causal savings or universal model superiority follows from these intervals.

## Reproduction and source identity

Commands: `python -m scripts.prepare_coverage --version v3a`, `python -m scripts.evaluate_coverage`, `python -m scripts.report_coverage`. Existing selection/evaluation outputs refuse overwrite. Protocol: COVERAGE_PROTOCOL_V3A.md, hash `{result['protocol_sha256']}`. Dataset: `{result['dataset_sha256']}`. Evaluation source: `{result['code_sha256']}`. Exact original final/v2 hashes before and after are in coverage-study-v3a.json; matching source bytes are archived separately when verification completes.

## Release verification

Run `python -m scripts.verify_release --require-isolated --browser` from a virtual environment installed from requirements.lock. Each run has its own timestamped artifacts/releases directory, captured command output and a machine-readable report. Failed commands, source changes and changed protected evidence produce failed status; a global interpreter cannot claim isolated acceptance. The actual most recent local run is linked in artifacts/acceptance-v3.json. Remote CI is configured to use this same verifier, but is unverified until a remote run is observed.

## Remaining boundaries

Same retailer, historical recorded sales, assumed inventory/costs, no verified lost demand, no prospective intervention, no external users or cloud deployment, and no independently demonstrated owner mastery. A numerical portfolio rating is subjective; the work here strengthens measurable coverage and reproducibility instead of manufacturing results or impact.
'''
    (ROOT/'docs/COVERAGE_AND_RELEASE_REPORT.md').write_text(text,encoding='utf-8')
    print('Wrote expanded coverage report; products:',study['product_count'])


if __name__=='__main__':
    main()
