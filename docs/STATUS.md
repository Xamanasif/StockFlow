# Completion status and acceptance record

Implemented the eight completion phases as a local portfolio prototype. The folder remains **StockFlow**. The original handoff is preserved in CODEX_COMPLETION_PROMPT.md; original README/status are preserved in foundation copies. Read INDEX.md for the full documentation set.

## Observed acceptance

|Evidence type|Actual result|Evidence|
|---|---|---|
|Software unit/API|56 tests passed on Windows/Python 3.13|artifacts/test-results.json and tests.txt|
|Lint and import compilation|Ruff F checks and compileall passed|artifacts/engineering-checks.json|
|Browser integration|Headless installed Edge, 11 workflow/state/layout checks; zero JavaScript errors|artifacts/browser.json, desktop.png, mobile.png|
|Official real import|1,067,371 source rows; 1,067,366 retained for source accounting; five negative-price rows quarantined; canonical research restricted to five development-selected SKUs|artifacts/real-import.json, data/raw/uci-quarantine.csv|
|Real API integration|Overview, forecast, MILP proposal, exact snapshot retrieval, local confirmation and decision report passed|artifacts/real-api.json|
|Synthetic development research|All five methods, 70 product-days / 734 recorded units; all three policies and eight sensitivity regimes retained|artifacts/development.json|
|Real development research|All five methods, 70 product-days / 4,087 recorded units; crossed policies/sensitivities retained|artifacts/real-development.json|
|Real final research|One evaluation, 35 product-days / 2,132 recorded units; seasonal naive WAPE 70.59%, Ridge 81.58%|artifacts/real-final.json and FINAL receipt|
|Live Groq|Not run; optional adapter and provider mocks only|app/assistant.py and completion tests|

These evidence types are not interchangeable. High forecasting errors, selected-product bias, interval limitations and the assumption-dependent replay remain visible. No realised savings, external deployment, authenticated reviewer identity or production readiness is claimed.

## Phase coverage

1. Data: official source/schema/license verified; original archive/workbook retained, reason-coded preview/quarantine, customer-field minimisation, raw/source/canonical hashes, manifest directories, first-60-day product selection, calendar/entry audit and cached reads. Full-workbook entry/exit dictionaries remain in local import evidence rather than registry screen payloads.
2. Forecasting: protocol written before experiments, hash/version retention, fold-local recursive Ridge, recent/weekday/seasonal/intermittent baselines, denominator-aware global/product/segment errors, calibrated empirical intervals and one-use final receipt. Final metrics did not drive retuning.
3. Replay: specified daily events, integer units/cash, lost-sales semantics, common demand/lead-time sequences, separate random streams for variability and lead-time jitter, paid pipeline, weekly grants, terminal stock and conservation.
4. Policies: fixed-target, greedy and static MILP, specified coverage objective, status/gap/fallback, brute-force checks, forecast/policy crossing, Pareto and sensitivity evidence including losses.
5. Product: maintainable single-process HTML/CSS/JavaScript frontend, overview/provenance, product chart, assumptions, planning selector, scenario lab, history/local review, CSV/report exports, assistant, mobile/empty/error states and safe DOM text rendering.
6. Assistant: server-side model discovery and bounded read-only get_plan tool, typed cited numerical rendering, explicit local fallback, stale-source/assumption checks and provider mocks. General free-form grounded reasoning and live-provider accuracy are unverified; paid services are not required.
7. Controls: immutable snapshots, persisted assumption versions and per-field provenance, expiring one-use version-bound review, concurrency/idempotency, rollback/connection closure, schema version, redacted structured logs, health/readiness, port conflict check, dependency version lock and CI definition.
8. Evidence: original tests retained in intent, additional semantic/invariant/negative tests, actual browser flow, actual official import, real temporal development/final experiments, saved worked proposal, screenshots and complete learning documentation.

## Boundaries and verification scope

Remote CI has not run. Other operating systems and clean virtual-environment installation were not exercised here. The version lock records the installed tested environment, without wheel hashes. No live Groq calls or authenticated/tenant-isolated deployment were tested. Optional Docker, demand-censoring correction, dynamic stochastic optimisation and external purchasing remain outside this local scope.

Exact source bytes matching the final experiment's recorded hash are archived in artifacts/source-at-final.zip. Later changes summarised registry API display metadata, synchronised browser response checks and expanded documentation; forecast/replay/solver code did not change after final evaluation. The final period was not rerun. See BUILD_LOG.md, KNOWN_LIMITATIONS.md and EVALUATION_REPORT.md.

## Launch

From the inner StockFlow directory containing README.md:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
powershell -ExecutionPolicy Bypass -File .\run.ps1 -Port 8000
```

Open http://127.0.0.1:8000 . The launcher can also use the currently installed Python when no .venv exists. Read TROUBLESHOOTING.md for port conflicts, dataset selection, browser binary installation and review conflicts.

## 2026-11-21 role-aligned extension acceptance

The earlier acceptance table records the original build. Latest unit/API acceptance is **72 passing tests** (artifacts/test-results-v2.json, tests-v2.txt). Fourteen SQL/statistical tests plus two concurrency/report checks extend the original 56. Ruff F checks and Python compilation also pass.

Added a separate SQL transaction/product/daily mart with unique source/cutoff identity, concurrent idempotent loading, CTE/window views, explicit calendars and pre-commit Python/SQL reconciliation. The actual real subset loaded 13,287 canonical rows and 306,947 positive-sale units through the development cutoff; 142 later canonical rows were excluded. Those are selected-subset counts, separate from the full original 1,067,371-row import audit.

Added 13 historical weekly folds covering 455 shared product-days and 32,660 recorded units. All five models are reported; weekday mean has 16.24% less absolute error than Ridge in this exploratory sample. Circular paired block resampling retains all products jointly and reports 1/2/3-week sensitivity and undefined-denominator handling. All 75 common-seed replay runs, including losses/ties, are retained. No original final metric, receipt, model parameter or static policy was changed.

The new study was specified after final inspection and is labelled exploratory throughout. Report/source/evidence: docs/EXPLORATORY_PROTOCOL_V2.md, docs/RESEARCH_EXTENSION_REPORT.md, artifacts/exploratory-robustness.json and artifacts/source-exploratory-v2.zip. The source snapshot matches the recorded run hash. The new SQL/research screens retain source identifiers and mismatch states. Latest browser outcomes are in artifacts/browser.json; read its actual checks rather than assuming remote CI ran.

Learning material now contains 86 interview answers and 20 exercises, plus role-specific independent defence tasks. Resume bullets are30–35 words each with evidence/limits separately attached. Live Groq, authenticated deployment, realised business savings, cloud delivery, independent external replication and PhD-level novelty remain unverified/unestablished.

Latest browser extension acceptance: **13 checks passed**, including reconciled SQL analytics and the mismatched-source exploratory report warning, with zero JavaScript errors. All five SQL example queries were actually executed. New evidence identities and original-final preservation are recorded in artifacts/acceptance-v2.json.

## Latest coverage/release acceptance — v3a

Latest machine-readable record: artifacts/acceptance-v3.json. The clean isolated environment installed the locked dependencies and passed dependency consistency, 83 unit/API tests, lint, compilation and 14 actual Edge browser checks. Normal PowerShell launch served readiness/dashboard and the owned smoke-test port was verified closed afterward. The existing .venv was left unchanged; launcher dependency probing selected the verified environment when SciPy was missing from the old one.

Forty new development-selected products, 13 weekly folds, 3,640 product-days and 10,417 recorded units per method; all 2,600 product/method/fold rows completed without failures. Five populated volume/density strata and the empty low/dense stratum are retained. An initial manual-code sampling issue was corrected through a published pre-evaluation amendment, preserving the first selection. Original final and v2 result files/receipts remain byte-identical. Matching evaluation source is archived in source-coverage-v3a.zip.

The wider cohort does not establish forecast suitability: all five frozen methods exceed 100% WAPE, worse than an always-zero arithmetic diagnostic. MASE values and every product/segment loss remain visible. This negative finding is explicitly documented and the old five-product result cannot be generalised. Coverage and reproducibility are stronger; live business impact, independent retailer replication, cloud deployment, external users and owner mastery remain unverified. See COVERAGE_AND_RELEASE_REPORT.md.
