# Understanding the first half

## Data, assumptions and decisions are separate

`app/data.py` reduces input to invoice, product, date, quantity and sale price. Cancellation codes and nonpositive quantities are not treated as positive product sales. Possible duplicate rows are flagged, not silently removed: two legitimate identical lines could exist. A file checksum identifies exactly which canonical dataset was used; it proves byte identity, not source truth or business correctness.

The demo is constructed, and the metadata says so. A real import does not create real inventory or supplier data. Costs and stock entered on the dashboard remain assumptions even when sales are real. This distinction matters when describing the project on a resume.

## Forecasting

`history` uses only rows at or before the cutoff. `weekday_mean` calculates each future weekday's average from the last 56 calendar days. `mean_28` repeats the recent daily average. These are understandable baselines, not trained ML models.

The leakage test changes future quantities dramatically and verifies that a past prediction does not move. That is stronger than merely checking that a function returns seven rows. Backtest WAPE is sum of absolute errors divided by sum of actual recorded units. When the denominator is zero, WAPE is undefined and returned as null, not fabricated as zero. Signed error is also retained so overforecasting and underforecasting can be distinguished.

The zero-filled calendar is an assumption. A day without an invoice may represent no sales, closure or missing data. New-product history is also incomplete. Explain these limitations instead of interpreting every zero as customer demand.

## Planning

`PlanRequest` validates bounds and uniqueness. Purchasing money is integer pence, avoiding floating-point budget breaches. For each product, target stock covers forecast sales over lead time plus review horizon. On-hand and on-order are subtracted. Requested quantities respect pack sizes and the smallest pack multiple at least as large as MOQ.

The allocator repeatedly selects the affordable lot with highest priority-weighted expected coverage per penny. The first lot must satisfy MOQ. Existing stock counts against capacity. The algorithm can leave budget unused if no feasible lot fits. It must display uncovered targets rather than inventing money or relaxing constraints.

This is a greedy heuristic. It can lose to a global optimiser when selecting one large lot blocks a better combination. Its priority score is neither expected profit nor measured customer value. Time-of-arrival is not simulated yet; shortages before replenishment arrives cannot be estimated by the current aggregate plan.

## API and storage

The browser sends planning assumptions to `POST /api/plans`. The backend reads the selected dataset, forecasts eligible products, allocates lots and stores the exact JSON snapshot with SHA-256 and a UUID. `GET /api/plans/{id}` returns that saved snapshot. This makes a calculation inspectable, but the SQLite owner could still edit records. Do not call it tamper-proof or authenticated approval.

## Your next contributions

1. Trace one product manually from invoice lines to daily series, forecast, coverage target and chosen lot.
2. Find a two-product counterexample where greedy allocation is suboptimal.
3. Test whether an unseen product should have a zero forecast or an explicit insufficient-history status.
4. Define event timing for arrivals, demand, returns, ordering and holding cost before coding a simulator.
5. Explain why sales data alone cannot establish historical stockouts.
6. Compare global WAPE against mean per-product WAPE and explain their different weighting.
7. Explain why a checksum is not proof of trustworthy data.
8. Decide how a manager can approve a specific immutable proposal after assumptions have changed.
9. Add a meaningful importer failure test using a temporary CSV/XLSX file.
10. Document a result that challenges your preferred model or policy.

