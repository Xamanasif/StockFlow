# StockFlow — resume bullets and evidence

These bullets emphasise demonstrated business/data/engineering work relevant to the supplied internship role. The project is AI-assisted; the owner must personally reproduce the pipeline, explain the mathematics and make tested changes before claiming independent mastery. No PhD-level novelty, employer deployment or realised savings claim is established.

- Engineered a Python/SQL inventory decision platform integrating provenance-tracked retail data, reconciled analytical marts, mixed-integer replenishment and inventory simulation to support budget-constrained purchasing decisions with explicit costs, capacity and uncertainty.
- Benchmarked five forecasting methods across 13 exploratory rolling-origin folds covering 32,660 recorded units; weekday forecasting delivered 16.24% lower absolute error than Ridge, quantified through paired temporal block resampling and block-length sensitivity analysis.
- Implemented FastAPI services, immutable proposal snapshots, version-bound review and a restricted evidence assistant; validated data reconciliation, temporal leakage, optimisation feasibility and concurrent workflows through automated API, invariant and browser tests.

## Evidence and limitations, separate from the bullets

Business system: app/analytics.py, app/planning.py, app/optimizer.py, app/simulation.py, docs/ANALYTICS_QUERIES.sql, artifacts/real-analytics-v2.json, artifacts/worked-proposal.json. Original ingestion audited 1,067,371 workbook rows. SQL/research uses only five products selected using the first sixty days; the SQL mart loads 13,287 development-period canonical rows and reconciles 306,947 positive-sale units. Do not describe this as a million-row SQL performance benchmark.

Statistical finding: artifacts/exploratory-robustness.json:forecast_summary and paired_resampling; docs/EXPLORATORY_PROTOCOL_V2.md and docs/RESEARCH_EXTENSION_REPORT.md. Absolute errors are 24,891.5 for weekday mean and 29,716.821410974215 for Ridge; 1−24,891.5/29,716.821410974215=16.2377% lower absolute error. Both use the same 32,660 recorded units, 455 product-days, 65 product-folds and 13 weekly blocks. WAPE remains high: 76.21% versus 90.99%. The two-week-block resampling interval for Ridge minus weekday WAPE is 7.39–20.51 percentage points; it is exploratory, assumes temporal block behavior, and does not adjust multiple comparisons. One-/two-/three-week interval sensitivity is retained. This study was specified after the original final inspection; it is not independent confirmatory evidence.

Decision evidence: fifteen forecast/policy combinations across five shared lead-time seeds produce 75 replay runs. Starting stock, costs and demand proxy are assumed/shared, and losing regimes are retained. The original seven-day final favors seasonal naive over Ridge and has not been rerun; neither study establishes universal forecasting superiority or causal service improvement.

Engineering: artifacts/test-results-v2.json (72 passed), artifacts/tests-v2.txt, artifacts/browser.json, app/storage.py and tests/test_analytics_research.py. The browser exercised the complete local workflow, SQL evidence and a mismatched-source research warning. Concurrent ETL/review tests, rollback tests and read-only bounded reporting support inspectability; they are not security certification. Local confirmation has no identity assurance and does not place external orders. Live Groq remains unverified and offline behavior is explicitly labelled.

Reproducibility: artifacts/source-exploratory-v2.zip matches the exploratory run source hash. Original final source/result/receipt remain separately preserved. artifacts/acceptance-v2.json records new evidence identities. Remote CI and clean-environment/cloud deployment remain unverified. Read ROLE_ALIGNMENT.md and PROJECT_MASTER_GUIDE.md sections10–11 for independent ownership tasks. The original draft bullets remain in RESUME_EVIDENCE.v1.md.

## v3a evidence boundary for the bullets above

The 16.24% lower-error comparison above refers only to the original five-product exploratory study, not the newer forty-product cohort. The broader cohort has much higher percentage errors and all five methods are worse than the post-hoc zero-forecast diagnostic under WAPE. Read COVERAGE_AND_RELEASE_REPORT.md before discussing forecast readiness. The broadened evaluation and clean isolated verification strengthen engineering/research evidence; they do not establish realised business benefits or external validity. Original final and v2 results remain preserved.
