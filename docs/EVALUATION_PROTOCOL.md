# Evaluation protocol v1

Written during implementation on 2026-11-20, before new experiments; not a historical preregistration. Preserve this file and its hash in every result. Any revision must have a new version and explain the change.

Scope: observed positive-price sales, cancellation and adjustment rows excluded. Missing calendar days mean zero recorded sales by explicit assumption, not zero latent demand. The latest day is excluded from research because it may be partial.

Eligibility and selection: at most five products, ranked by positive-sale units in the first 60 calendar days, ties by SKU. Require first sale by day 14 and at least 28 days since entry at each forecast origin. Never select on final performance. Demo and real data are separate runs.

Windows relative to last complete date L: development ends L-42; calibration origins L-42,L-35,L-28 (7 days each); development comparison origins L-21,L-14; final origin L-7, horizon 7. Training uses only dates <= origin. Final evaluation requires --final, uses an exclusive per-dataset receipt, and refuses repeat access. Development runs do not evaluate final actuals. A failed final attempt remains recorded and must be investigated, not silently rerun.

Methods: trailing 28-day mean, weekday mean over 56 days, seasonal naive (last week's sales), Croston SBA (alpha .1), and recursive Ridge regression with lag 1/7/14, trailing mean 7 and weekday. Ridge scaling and fit are fold-local. No promotions, prices or future lags. Fixed settings; no tuning on these windows. Minimum 28 training days. All eligible products and failures are reported.

Uncertainty: absolute residuals from preceding calibration forecasts, method/product specific; finite-sample 80% split-conformal quantile ceil((n+1)*.8), capped at sample count. Symmetric nonnegative-clipped intervals. Report coverage numerator/denominator and mean width. Temporal dependence means coverage is empirical, not guaranteed.

Metrics: global absolute error / actual units (WAPE, null for zero denominator), MAE per product-day, signed forecast-minus-actual bias, product and intermittent/regular segment totals. Keep every method, including losses. Select development champion by global WAPE only; no final-based selection.

Decision study: cross all forecast methods with fixed reorder, greedy and static MILP over identical observed-sales sequences. Lost sales, no returns; arrivals at start of day, fulfilment, holding/shortfall cost, end-of-day review and orders; minimum next-day arrival. Weekly cash grants, pack/MOQ and aggregate physical-plus-pipeline reservations. Cost ratios, lead times, budgets, initial stock and synthetic variability varied one at a time. Report fill-rate numerator/denominator, unmet units, stock/capital, purchase/holding/order/shortfall costs separately. No causal or realised savings claims.

Evidence includes UTC timestamp, seed 2026, data/protocol/source hashes, exact command and software versions. Final and development outputs use distinct paths. Real-data evidence is absent until an actual successful import and experiment.
