# Actual evaluation evidence

Commands and machine-readable records: `artifacts/development.json`, `artifacts/real-development.json` when present, and separate `*final.json`. Each records data/protocol/code hashes, timestamp, versions and seed. The script preserves previous output versions. No Git commit exists in the supplied folder; source content hashes substitute for a commit identifier.

## Synthetic development forecasts

Denominator: 734 recorded units across 70 product-days, five products and two seven-day folds. These are constructed demo transactions, not company impact. All evaluated methods appear below.

|Method|WAPE|MAE units|Bias units|Empirical coverage|Mean interval width|
|---|---:|---:|---:|---:|---:|
|mean_28|25.86%|2.711|42.00|56/70|7.843|
|weekday_mean|17.93%|1.880|38.12|47/70|5.300|
|seasonal_naive|20.44%|2.143|38.00|61/70|6.771|
|croston_sba|24.89%|2.610|30.65|58/70|8.465|
|ridge|20.02%|2.100|48.27|53/70|6.220|


Weekday mean beats Ridge on this development metric; its intervals under-cover the nominal 80% target. The ML challenger is retained as a loss. No universal forecasting or service improvement is established. Product rows include regular/intermittent segment membership, raw errors and predictions; aggregate global WAPE weights high-volume products more strongly.

## Identical-scenario purchasing comparison

Costs are hypothetical GBP amounts, including purchase outlay, holding, order and shortfall charges. Terminal inventory receives no credit; this is neither profit nor financial ROI. Paid pipeline, initial stock, and weekly cash grants are explicit in each row. Fill rate is fulfilled proxy units / all proxy units, not customer-order service rate.

|Forecast|Policy|Filled/proxy units|Scenario cost GBP|Mean stock units|Pareto|
|---|---|---:|---:|---:|---|
|mean_28|fixed|383/734|1114.62|93.71|False|
|mean_28|greedy|389/734|1102.38|92.00|False|
|mean_28|milp|385/734|1109.75|94.64|False|
|weekday_mean|fixed|403/734|1073.92|88.71|False|
|weekday_mean|greedy|403/734|1073.92|88.71|False|
|weekday_mean|milp|379/734|1123.51|103.64|False|
|seasonal_naive|fixed|379/734|1122.85|95.36|False|
|seasonal_naive|greedy|405/734|1070.70|94.29|False|
|seasonal_naive|milp|412/734|1055.34|91.71|True|
|croston_sba|fixed|377/734|1126.90|95.71|False|
|croston_sba|greedy|391/734|1098.38|92.00|False|
|croston_sba|milp|371/734|1139.48|103.43|False|
|ridge|fixed|403/734|1073.92|88.71|False|
|ridge|greedy|395/734|1090.14|90.29|False|
|ridge|milp|395/734|1091.56|100.43|False|


Sensitivity evidence: eight one-at-a-time variants in `development.json:sensitivity`: cash grants, lead time, shortfall ratio, initial stock and synthetic variability. Rows retain losing regimes; inspect costs and unmet units jointly. All forecast/policy combinations in each regime share an exogenous sequence hash. The static MILP solves weighted target coverage at a review; it does not optimise the entire replay cost.

## Real-data status

An official-source workbook was actually imported and its development experiment saved. See real-development.json and real-import.json; the latter records full-workbook accounting and subset selection. Read its metrics below, separately from demo results.

## Evidence categories

Unit/API tests establish constructed invariants. Browser tests exercise a synthetic user workflow. Forecast results evaluate recorded-sales prediction. Replay results depend on invented procurement/inventory assumptions. Provider mocks exercise adapter behavior; they do not measure live model reasoning. A final receipt prevents automatic repeated access; an owner with filesystem access can bypass it, so this is a procedural guard, not an access-control guarantee.

### Real development metrics

|Method|Absolute error / actual units|WAPE|Coverage|
|---|---:|---:|---:|
|mean_28|3389.11 / 4087|82.92%|61/70|
|weekday_mean|3342.62 / 4087|81.79%|65/70|
|seasonal_naive|3425.00 / 4087|83.80%|68/70|
|croston_sba|5701.81 / 4087|139.51%|68/70|
|ridge|3193.87 / 4087|78.15%|69/70|

## One-use real final period

Final actual denominator: 2,132 recorded units, 35 product-days (five products, seven days). All methods were evaluated once; no settings or deployed policy were changed based on this result. Receipt: artifacts/FINAL-<dataset-hash>.json.

|Method|Absolute error / actual units|WAPE|Coverage|Mean width units|
|---|---:|---:|---:|---:|
|mean_28|1801.75 / 2132|84.51%|31/35|164.72|
|weekday_mean|1694.88 / 2132|79.50%|35/35|220.10|
|seasonal_naive|1505.00 / 2132|70.59%|35/35|244.46|
|croston_sba|2813.47 / 2132|131.96%|33/35|251.26|
|ridge|1739.32 / 2132|81.58%|33/35|200.30|

Seasonal naive beats Ridge on this final period, reversing the development ranking. High absolute percentage errors and wide intervals remain important limitations, not suppressed results. No final-based retuning was performed. Exact numerical source bytes matching the saved code hash are archived in artifacts/source-at-final.zip; subsequent registry display and browser-harness fixes changed no forecast, optimiser or replay logic.

## Real development decision cross-comparison

|Forecast|Policy|Filled / proxy units|Scenario cost GBP|Average stock units|
|---|---|---:|---:|---:|
|mean_28|fixed|456/4087|7668.14|65.29|
|mean_28|greedy|456/4087|7668.14|65.29|
|mean_28|milp|456/4087|7665.27|44.79|
|weekday_mean|fixed|456/4087|7668.14|65.29|
|weekday_mean|greedy|456/4087|7668.14|65.29|
|weekday_mean|milp|456/4087|7665.27|44.79|
|seasonal_naive|fixed|456/4087|7668.14|65.29|
|seasonal_naive|greedy|456/4087|7668.14|65.29|
|seasonal_naive|milp|456/4087|7665.27|44.79|
|croston_sba|fixed|60/4087|8484.20|237.14|
|croston_sba|greedy|60/4087|8484.20|237.14|
|croston_sba|milp|456/4087|7665.27|44.79|
|ridge|fixed|260/4087|8078.98|196.29|
|ridge|greedy|260/4087|8078.98|196.29|
|ridge|milp|456/4087|7665.27|44.79|

Under the default tight budget and common exogenous sequence, Ridge has lower development WAPE but greedy replay fulfils 260/4,087 proxy units, versus weekday mean 456/4,087. This constructed scenario does not establish a general causal effect. Static MILP reaches 456/4,087 for both forecast methods; forecast accuracy and purchasing policy are separate decisions. The replay budget is deliberately tight relative to these volumes, and all procurement/penalty inputs remain assumptions.
