# Expanded portfolio coverage and release evidence

## What changed

The earlier studies used five high-volume products. This extension samples **40 different products**, excluding all five earlier SKUs, using first-sixty-day volume and recorded-sales sparsity. Existing forecast methods/hyperparameters remain unchanged. The same retailer is still the only data source; this is a retrospective exploratory cross-product generalisation check, not independent external validation or a fresh confirmatory holdout.

The initial development-only v3 sample contained manual code M. That selection was retained, and amendment v3a declared an item-code format rule before any new-cohort forecast evaluation. A new selection and canonical version were published rather than silently editing the old sample. The identifier rule is a heuristic: it excludes accounting/service-like codes but cannot prove every accepted code is physical merchandise. The original final result/receipt and v2 study remain byte-identical.

## Coverage and eligibility

Selection ends 2010-01-29. Cohort seed 20261121. Eligible pool: 2673 products. Quota deficits are retained; no future outcomes or final model performance were used to select products.

|Stratum|Eligible products|Selected|Unfilled quota|
|---|---:|---:|---:|
|low_sparse|891|8|0|
|low_dense|0|0|8|
|middle_sparse|879|8|0|
|middle_dense|12|8|0|
|high_sparse|641|8|0|
|high_dense|250|8|0|


No eligible low-volume/dense products satisfy this particular volume-tercile/calendar definition. That empty cell is a population property under the declared rules, not an omitted model loss. Missing/pre-entry days in the sixty-day selection calendar are explicitly assumed zero recorded sales. Sales capture and opening days are unverified.

## Frozen-method evaluation

13 non-overlapping seven-day origins, targets ending 2011-12-01. Complete paired coverage: **True**. Failures: 0. Actual-unit denominators and product-day counts are retained for every model; no method is removed after losing.

|Method|Absolute error / actual units|WAPE|MAE units|Mean seasonal MASE|Defined / undefined scaling folds|
|---|---:|---:|---:|---:|---:|
|mean_28|13541.36 / 10417|129.99%|3.720|0.811|520 / 0|
|weekday_mean|13328.12 / 10417|127.95%|3.662|0.779|520 / 0|
|seasonal_naive|15435.00 / 10417|148.17%|4.240|0.883|520 / 0|
|croston_sba|14427.22 / 10417|138.50%|3.964|1.229|520 / 0|
|ridge|13942.82 / 10417|133.85%|3.830|0.874|520 / 0|


MASE = product-fold MAE divided by mean absolute seven-day training difference. The scaling denominator uses training history only. A zero/insufficient scale is undefined, not zero. Mean MASE weights defined product-folds equally; global WAPE weights actual units. Zero-target products may have undefined WAPE while still having finite absolute error. See [Forecasting: Principles and Practice, scaled errors](https://otexts.com/fpp3/toolbox.html#scaled-errors) for the seasonal scaling definition.

## Segment results

|Stratum|Method|Actual units|Product-days|WAPE|MAE units|
|---|---|---:|---:|---:|---:|
|low_sparse|mean_28|156|728|334.52%|0.717|
|low_sparse|weekday_mean|156|728|406.73%|0.872|
|low_sparse|seasonal_naive|156|728|175.00%|0.375|
|low_sparse|croston_sba|156|728|364.50%|0.781|
|low_sparse|ridge|156|728|282.94%|0.606|
|low_dense|mean_28|0|0|undefined|undefined|
|low_dense|weekday_mean|0|0|undefined|undefined|
|low_dense|seasonal_naive|0|0|undefined|undefined|
|low_dense|croston_sba|0|0|undefined|undefined|
|low_dense|ridge|0|0|undefined|undefined|
|middle_sparse|mean_28|1080|728|172.67%|2.562|
|middle_sparse|weekday_mean|1080|728|154.10%|2.286|
|middle_sparse|seasonal_naive|1080|728|178.80%|2.652|
|middle_sparse|croston_sba|1080|728|219.39%|3.255|
|middle_sparse|ridge|1080|728|144.55%|2.144|
|middle_dense|mean_28|1522|728|113.87%|2.381|
|middle_dense|weekday_mean|1522|728|106.38%|2.224|
|middle_dense|seasonal_naive|1522|728|132.92%|2.779|
|middle_dense|croston_sba|1522|728|124.05%|2.594|
|middle_dense|ridge|1522|728|124.86%|2.610|
|high_sparse|mean_28|3174|728|136.28%|5.942|
|high_sparse|weekday_mean|3174|728|138.93%|6.057|
|high_sparse|seasonal_naive|3174|728|155.80%|6.793|
|high_sparse|croston_sba|3174|728|140.15%|6.110|
|high_sparse|ridge|3174|728|147.50%|6.431|
|high_dense|mean_28|4485|728|113.63%|7.000|
|high_dense|weekday_mean|4485|728|111.49%|6.869|
|high_dense|seasonal_naive|4485|728|139.64%|8.603|
|high_dense|croston_sba|4485|728|114.89%|7.078|
|high_dense|ridge|4485|728|119.47%|7.360|


## Every selected product

|Product|Stratum|Actual units|Mean28 WAPE|Weekday WAPE|Seasonal naive WAPE|Croston WAPE|Ridge WAPE|
|---|---|---:|---:|---:|---:|---:|---:|
|90192|low_sparse|17|163.87%|161.76%|188.24%|146.61%|158.15%|
|84508C|low_sparse|32|171.43%|139.06%|143.75%|129.64%|130.44%|
|85036A|low_sparse|99|177.71%|174.75%|182.83%|161.69%|155.05%|
|90178A|low_sparse|2|200.00%|187.50%|200.00%|241.06%|267.59%|
|21736|low_sparse|0|undefined|undefined|undefined|undefined|undefined|
|85106|low_sparse|6|4320.24%|6429.17%|166.67%|4497.77%|2718.99%|
|35233|low_sparse|0|undefined|undefined|undefined|undefined|undefined|
|84709B|low_sparse|0|undefined|undefined|undefined|undefined|undefined|
|20705|middle_sparse|9|191.27%|173.61%|155.56%|272.43%|331.43%|
|21039|middle_sparse|115|144.63%|137.72%|148.70%|143.56%|162.53%|
|22222|middle_sparse|114|124.75%|123.68%|145.61%|123.29%|134.01%|
|46776C|middle_sparse|64|129.97%|110.74%|131.25%|116.15%|117.87%|
|85128|middle_sparse|0|undefined|undefined|undefined|undefined|undefined|
|72802B|middle_sparse|744|186.59%|162.10%|192.74%|150.85%|121.88%|
|22322|middle_sparse|34|199.16%|212.87%|182.35%|275.21%|447.71%|
|35096B|middle_sparse|0|undefined|undefined|undefined|undefined|undefined|
|21431|middle_dense|0|undefined|undefined|undefined|undefined|undefined|
|20749|middle_dense|577|106.20%|97.60%|130.16%|103.83%|91.59%|
|21756|middle_dense|137|121.72%|106.57%|137.96%|120.03%|135.18%|
|21624|middle_dense|60|139.88%|128.54%|175.00%|130.44%|349.34%|
|22215|middle_dense|72|155.65%|144.44%|183.33%|147.92%|189.40%|
|21770|middle_dense|502|102.18%|96.02%|121.91%|104.17%|91.46%|
|79160|middle_dense|37|214.86%|293.24%|148.65%|304.01%|294.95%|
|22120|middle_dense|137|120.49%|101.00%|130.66%|117.03%|113.17%|
|21983|high_sparse|721|145.73%|139.25%|172.40%|141.92%|147.23%|
|20977|high_sparse|367|178.68%|180.82%|158.58%|190.12%|167.70%|
|22080|high_sparse|641|110.16%|110.14%|128.08%|104.15%|100.99%|
|20652|high_sparse|69|149.12%|152.72%|175.36%|147.59%|274.57%|
|22185|high_sparse|426|135.62%|125.32%|155.87%|130.29%|142.70%|
|20970|high_sparse|619|101.55%|97.17%|139.10%|100.41%|97.17%|
|22287|high_sparse|227|166.27%|167.68%|196.04%|165.36%|152.75%|
|21746|high_sparse|104|217.51%|398.80%|200.00%|390.40%|588.13%|
|21755|high_dense|448|92.90%|92.52%|126.56%|93.23%|107.39%|
|21908|high_dense|1217|121.16%|120.90%|144.70%|117.27%|110.00%|
|85014B|high_dense|744|121.29%|119.93%|150.94%|120.60%|103.22%|
|84988|high_dense|1032|112.92%|109.04%|141.76%|114.57%|113.61%|
|22122|high_dense|0|undefined|undefined|undefined|undefined|undefined|
|21164|high_dense|223|139.67%|136.38%|149.33%|139.76%|282.86%|
|82483|high_dense|749|97.11%|92.19%|120.83%|96.48%|99.10%|
|21407|high_dense|72|137.35%|142.36%|154.17%|138.67%|199.18%|


Alternative product absolute-error wins/ties/losses versus weekday mean (ties use tolerance1e-9): `{"croston_sba": {"losses": 28, "ties": 0, "wins": 12}, "mean_28": {"losses": 25, "ties": 7, "wins": 8}, "ridge": {"losses": 27, "ties": 0, "wins": 13}, "seasonal_naive": {"losses": 27, "ties": 7, "wins": 6}}`. These are descriptive within-cohort results, not independent significance tests. A method may lose overall while helping individual products; the full table is retained.

## Paired temporal uncertainty

|Alternative vs weekday|WAPE difference (pp)|95% two-week block resampling interval (pp)|
|---|---:|---:|
|mean_28|2.047|[-4.84, 8.13]|
|seasonal_naive|20.225|[4.46, 36.50]|
|croston_sba|10.551|[8.12, 12.91]|
|ridge|5.901|[1.15, 9.76]|


The existing resampling method keeps each weekly cross-section together and resamples two-week circular blocks,2000 replicates. Negative differences favor the alternative. Thirteen weeks, artificial wrap-around, shared retailer effects, retrospective design and unadjusted comparisons limit inference. No causal savings or universal model superiority follows from these intervals.

## Reproduction and source identity

Commands: `python -m scripts.prepare_coverage --version v3a`, `python -m scripts.evaluate_coverage`, `python -m scripts.report_coverage`. Existing selection/evaluation outputs refuse overwrite. Protocol: COVERAGE_PROTOCOL_V3A.md, hash `16df76804cba0ce14599372fe269fbcf406f5a81846a9dd0af181eaf941f4db1`. Dataset: `b2792ab819d26c2485ec9249ebc7c0e56a56cd02036754c8c46fa412d1f08173`. Evaluation source: `d51f317f434f7d3f9490745b837690fc3280c882348230c8580c17c47604764b`. Exact original final/v2 hashes before and after are in coverage-study-v3a.json; matching source bytes are archived separately when verification completes.

## Release verification

Run `python -m scripts.verify_release --require-isolated --browser` from a virtual environment installed from requirements.lock. Each run has its own timestamped artifacts/releases directory, captured command output and a machine-readable report. Failed commands, source changes and changed protected evidence produce failed status; a global interpreter cannot claim isolated acceptance. The actual most recent local run is linked in artifacts/acceptance-v3.json. Remote CI is configured to use this same verifier, but is unverified until a remote run is observed.

## Remaining boundaries

Same retailer, historical recorded sales, assumed inventory/costs, no verified lost demand, no prospective intervention, no external users or cloud deployment, and no independently demonstrated owner mastery. A numerical portfolio rating is subjective; the work here strengthens measurable coverage and reproducibility instead of manufacturing results or impact.

## Important post-hoc null diagnostic

All five tested methods have WAPE above 100% on this broader cohort. For nonnegative actuals, always predicting zero has absolute error equal to actual units, so WAPE is exactly 100% whenever actual units are positive. Here that means 10,417 absolute-error units and MAE 10,417/3,640=2.8618. This arithmetic diagnostic was added after the cohort results; it is not presented as a pre-specified sixth model. See artifacts/coverage-null-diagnostic-v3a.json.

The frozen forecast methods therefore do not demonstrate adequate portfolio-wide forecasting accuracy on this diverse sample. Mean seasonal MASE below 1 can coexist with WAPE above 1 because its training-derived scales and product-fold weighting differ. Neither metric should be used to hide the other. Zero forecasting is not a recommended purchasing policy: it can favor underforecasting under absolute-error metrics, while decisions depend on shortage/holding costs and stock availability. The system remains a scenario decision prototype, not a validated automatic replenishment policy. The forty-product sample is stratified, not population-weighted; its global results describe this selected cohort, not the retailer's whole catalogue.
