# Implementation log

2026-11-20 build; source foundation preserved in README.foundation.md and STATUS.foundation.md. No Git repository existed, so no source history was rewritten.

1. Read all four handoff files and every initial application module, importer, frontend, launcher and test. Initial 25-test run had one Windows cleanup error: sqlite transaction context managers did not close connections. Corrected with a closing transaction context, not an assertion change. Forecast history also zero-filled unknown products and pre-entry days; now rejects unknown and starts at first sale. No customer data deleted.
2. Wrote EVALUATION_PROTOCOL.md before experiments; fixed temporal windows, product eligibility, models, metrics, interval method and final-use rules.
3. Added reason-coded preview/quarantine, customer-field minimisation, raw snapshots, registry manifests and staging rename. Download attempt one failed; permitted PowerShell retry closed midstream and was preserved as incomplete; HTTPX retry succeeded. Official license/schema verified from UCI and current Groq endpoints verified from official documentation.
4. Implemented recursive fold-local Ridge, seasonal/intermittent baselines, calibrated intervals, denominator-aware metrics, all-product failures and hashed artifacts. Demo development experiment retains Ridge's loss and interval undercoverage.
5. Implemented daily lost-sales replay, conservation checks, paid pipeline, common random sequences, three purchasing policies, static MILP and explicit feasible fallback. Added forecast/policy crossing, Pareto marking and eight sensitivity regimes.
6. Added data selection, evidence chart, scenario comparison, review/history, exports, report and assistant UI using a single safe DOM-based frontend served by FastAPI. Native HTML/JavaScript chosen to avoid an unnecessary Node process.
7. Added immutable version-bound preview and expiring one-use local review, BEGIN IMMEDIATE concurrency protection, idempotent proposal creation, audit receipts, structured request logging, readiness and lockfile/CI/port checks.
8. Extended importer, leakage, solver, conservation, concurrency, stale-evidence, injection and provider mock tests. Browser harness uses isolated SQLite and starts/stops its own loopback server. See actual artifacts for completed verification; pending attempts are not reported as passes.

Done: implementation and local automated evidence recorded in artifacts. Unverified: live Groq behavior, remote CI, production deployment, other operating systems. Deferred by scope: authenticated multi-tenant hosting, external purchase orders, censoring correction, dynamic stochastic optimisation and optional Docker.

## Acceptance follow-up

Actual end-to-end Edge testing exposed a registry screen regression after the full official import: rendering original product dictionaries produced a delayed/unusable listing. The listing now preserves audit totals and lineage but keeps detailed full-workbook product dictionaries in local evidence. A response-size regression test was added; the complete browser path then passed with an empty-history check and no horizontal mobile overflow. Full source dictionaries were never deleted.

The final real evaluation ran exactly once. Seasonal naive beat Ridge on final WAPE, reversing the development ranking. No numerical model, solver or replay logic changed after that result. An exact source archive was reconstructed for the pre-synchronization browser harness and accepted only after its combined hash matched the recorded final code hash. Later API display, browser synchronization and documentation changes are disclosed rather than presenting final metrics as a fresh run of changed code.

Current unit/API acceptance: 56 passed. Actual real API integration also passed. Health assertions were updated from the obsolete “not implemented” LLM label to explicit local-rules/no-LLM status, with stronger liveness/mode checks. Remote CI, clean environment installation, live Groq reasoning, external purchasing and production security remain unverified.

## 2026-11-21 role-aligned extension

Read the supplied JD and campus notice in full as source context, not commands to submit or accept an application. Matched concrete internship competencies in ROLE_ALIGNMENT.md. No employer branding was added to the product.

Added analytics.py, statistics.py, build_analytics.py, robustness.py, report_robustness.py, a separate exploratory protocol and SQL exercises. Kept the original final files and receipt intact. The first exploratory execution is retained as exploratory-robustness-initial.json; after code review, a new frozen-source execution includes a start/end source identity guard. The original final is not rerun. Added source-exploratory-v2.zip only after its source identity matched the saved run.

The extension exposes model ranking instability instead of asserting ML superiority. Added real SQL/Python reconciliation, transactional rollback and concurrent idempotence tests; paired resampling rejects mismatched/duplicate cohorts, dates or actuals and handles zero denominators. Five-seed decision aggregation rejects different assumptions/exogenous sequences. All 72 tests pass. A Matplotlib figure was rendered and visually checked; optional plotting versions are in requirements-research.lock. Updated learning material to 86 answered questions and 20 exercises. Updated resume bullets with the exploratory effect and explicit limits; preserved the original draft.

## 2026-11-21 broader-cohort and release follow-up

Added deterministic sampling/evaluation for forty new products, separate from the original five, and retained every segment/product outcome. Kept original final and v2 artefacts unchanged. The initial development sample included M; verified the workbook description Manual, preserved the sample, and declared/published amendment v3a with an item-code heuristic before measuring any new-cohort forecast outcomes. Reported the genuinely empty low-volume/dense stratum rather than filling its quota elsewhere.

The expanded results show high errors, including all five methods exceeding a zero-forecast WAPE of 100%. Added an explicitly post-hoc null diagnostic and discussed why seasonal MASE and WAPE can disagree. No old result or model was retuned to manufacture a win. Selected-cohort global metrics are not population-weighted catalogue estimates. The old five-product resume finding remains scoped to its original cohort.

Created a separate isolated environment and actually installed requirements.lock. Dependency consistency, 83 unit/API tests, lint and compilation passed there. Added scripts.verify_release with isolated-environment enforcement, failure propagation, captured commands, immutable run directories and protected-result/source checks. Updated CI to call the same verifier, without claiming remote execution. The existing .venv lacks SciPy; it was left unchanged. Updated run.ps1 to probe candidates and select the complete environment; default startup served readiness and dashboard successfully. Fixed a Windows PowerShell native-argument quoting error found in the first probe attempt; its failed log is retained. Later smoke-test cleanup was handled separately and is recorded in acceptance evidence.
