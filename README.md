# StockFlow

Inventory and working-capital decision workbench. Choose replenishment lots within cash, capacity and supplier-lot constraints; inspect uncovered targets and compare forecast/policy trade-offs using clearly labelled scenario replay.

Local portfolio prototype: synthetic demo by default; official UCI historical subset available after import. Stock, procurement costs and lead times are scenario assumptions. No external purchasing, authenticated identity assurance or realised savings claim.

## Windows launch

From the repository root (the folder containing this README):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
powershell -ExecutionPolicy Bypass -File .\run.ps1 -Port 8000
```

Open http://127.0.0.1:8000 ; API docs: http://127.0.0.1:8000/docs . Stop with Ctrl+C. The launcher detects occupied ports and supports `-Port 8001`. It checks `.venv`, then `.venv-release-v3`, then the active Python for required dependencies. Bind only to loopback. No Node server, paid API or frontend build is required. A clean isolated installation was verified on Windows with Python 3.13; see the release evidence below for results. Remote CI status is available in this repository's Actions tab.

macOS/Linux equivalent: `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.lock`, `.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. These commands are supplied, not claimed as locally exercised.

## Implemented

- Reason-coded import preview/quarantine, immutable dataset registry, source/raw/canonical hashes, minimised customer fields, development-only five-product selection and cached canonical loads.
- Recent/weekday mean, seasonal naive, Croston SBA and recursive fold-local Ridge; temporal protocol, calibrated intervals, all-method/product/segment errors, guarded final evaluation.
- Integer-pack greedy and static SciPy MILP allocation; daily lost-sales replay with shared seeds/sequences, cash/inventory checks, forecast/policy crossing, Pareto marking and eight sensitivity regimes.
- Responsive browser workbench: data/quality/lineage, dated evidence chart, assumptions, planning, scenario lab, history, version-bound local review, CSV/report exports and cited evidence assistant.
- SQLite transactions, concurrent idempotent saves, stale/expired/reused-review rejection, health/readiness, structured request logs, locked versions and CI configuration.
- Server-side opt-in Groq adapter using verified account model discovery and one validated read-only evidence tool. Missing credentials use explicitly labelled local rules/no LLM. Numbers are deterministically rendered from saved records. Live Groq calls remain unverified.

## Verify and study

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m ruff check app scripts tests --select F
.\.venv\Scripts\python.exe -m scripts.browser_test
```

Browser test uses installed Edge on Windows. Alternative: `.\.venv\Scripts\python.exe -m playwright install chromium`, then `$env:STOCKFLOW_BROWSER='chromium'`. The browser harness starts its own isolated server/database. Exact observed checks and limitations: [current status](docs/STATUS.md), [evaluation report](docs/EVALUATION_REPORT.md), [evidence artifacts](artifacts/).

Study [project mastery guide](docs/PROJECT_MASTER_GUIDE.md), [architecture](docs/ARCHITECTURE.md), [demo walkthrough](docs/DEMO_WALKTHROUGH.md), and [docs index](docs/INDEX.md). Original README/status are preserved as foundation copies.

## Public repository contents

Source, tests, dependency locks, documentation, synthetic demo data, screenshots and historical research evidence are included. The demo runs after installation without downloading the UCI workbook. Raw customer records, local dataset registries, SQLite databases, virtual environments and credentials are excluded. Import the attributed official source below to reproduce real-data experiments; recorded absolute paths identify the original local run and are not portable input paths. Preserve existing final-evaluation receipts and use new output filenames for exploratory studies.

## Official UCI import

Source/license verified: [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii), Chen, D. (2012), DOI 10.24432/C5CG6D; [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Preserve attribution with source/derived data. The original workbook includes customer identifiers; keep raw snapshots local. Canonical and quarantine tables omit those fields.

```powershell
New-Item -ItemType Directory -Force data/raw | Out-Null
Invoke-WebRequest 'https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip' -OutFile data/raw/online-retail-ii.zip
.\.venv\Scripts\python.exe -m scripts.prepare_real --quarantine
```

The completion run actually downloaded and imported this source. `artifacts/real-import.json` records the source rows, rejected reasons, hashes and canonical subset path. The helper preserves original dates and selects products using only the first 60 days; it never selects them by final accuracy. The latest research day is excluded as potentially partial.

For another CSV/XLSX (all sheets; legacy XLS must be converted):

```powershell
.\.venv\Scripts\python.exe -m scripts.import_uci 'data/raw/source.xlsx' --preview
.\.venv\Scripts\python.exe -m scripts.import_uci 'data/raw/source.xlsx' --quarantine --source-url 'actual source URL' --license 'actual license'
```

Select a published version in the workbench for the current single-process session, or set `$env:STOCKFLOW_CSV=(Resolve-Path 'data/registry/<version>/transactions.csv').Path` before launching. Restart without STOCKFLOW_CSV to return to demo. No arbitrary server path can be submitted through the browser.

## Reproduce research

Read [the protocol](docs/EVALUATION_PROTOCOL.md) first. Development reruns preserve earlier outputs:

```powershell
.\.venv\Scripts\python.exe -m scripts.evaluate --sensitivity
.\.venv\Scripts\python.exe -m scripts.evaluate --data 'data/registry/<version>/transactions.csv' --output artifacts/real-development.json --sensitivity
```

Final evaluation additionally requires `--final --output artifacts/<distinct-final-name>.json` and refuses a second attempt for the same dataset hash. Do not delete receipts or silently retune after final inspection. Saved final results can be read without rerunning. Software tests, recorded-sales accuracy, replay outcomes and live-provider evaluations are distinct kinds of evidence.

## Assistant configuration and boundaries

Set GROQ_API_KEY and GROQ_MODEL only in the backend process environment if you explicitly choose to enable provider calls. `.env.example` is a reference and is not auto-loaded. Model availability is checked using the current official [Groq API](https://console.groq.com/docs/api-reference); no key is needed for the local workbench. No paid/live calls were performed for this completion.

All outputs are proposals and scenario evidence. Missing sales days do not prove zero demand; source sales do not reveal stockouts, supplier costs or lost sales. Static optimisation is not dynamic cost optimality. Read [known limitations](docs/KNOWN_LIMITATIONS.md) before using the results or resume bullets. The folder remains named **StockFlow**.

## Research and SQL extension (2026-11-21)

The project now includes a transactional SQL analytics mart and a wider exploratory study. Read [role alignment](docs/ROLE_ALIGNMENT.md), [research extension report](docs/RESEARCH_EXTENSION_REPORT.md), [SQL examples](docs/ANALYTICS_QUERIES.sql) and [the new protocol](docs/EXPLORATORY_PROTOCOL_V2.md). The mastery guide contains 86 answered questions and 20 exercises. The original final evaluation and receipt remain unchanged.

Build demo SQL evidence, or pass --data for a registered canonical subset. Choose new output filenames when preserving existing artefacts:

```powershell
.\.venv\Scripts\python.exe -m scripts.build_analytics --output artifacts/my-demo-analytics.json
.\.venv\Scripts\python.exe -m scripts.build_analytics --data 'data/registry/<version>/transactions.csv' --output artifacts/my-real-analytics.json
.\.venv\Scripts\python.exe -m scripts.robustness --data 'data/registry/<version>/transactions.csv' --output artifacts/my-exploratory-study.json
```

The SQL mart defaults to data/analytics.db and is read through /api/analytics; STOCKFLOW_ANALYTICS can override that server-side path. The workbench also exposes the saved exploratory report at /api/research/robustness and marks mismatched datasets. It does not execute arbitrary SQL.

Optional scientific report figure dependencies and regeneration:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-research.lock
.\.venv\Scripts\python.exe -m scripts.report_robustness
```

The thirteen-fold extension is explicitly exploratory after original final inspection; it does not replace or rerun that final. The five-seed replay varies supplier timing, not independent customer demand. Neither provides causal savings or a research-novelty claim. Updated evidence and exactly three resume bullets are in docs/RESUME_EVIDENCE.md.

## Broader coverage and isolated verification (v3a)

The project now includes a separate forty-product cohort excluding all five original research products. Selection uses only first-sixty-day volume and recorded-sales density, with an explicit item-code heuristic and retained empty stratum. The study covers thirteen weeks and 3,640 product-days per method. Read [the coverage/release report](docs/COVERAGE_AND_RELEASE_REPORT.md), [the amended protocol](docs/COVERAGE_PROTOCOL_V3A.md) and [the original v3 protocol](docs/COVERAGE_PROTOCOL_V3.md). Existing final and v2 results are unchanged.

The broadened cohort exposes weak forecast performance: all five methods exceed 100% WAPE there. The post-hoc zero-forecast diagnostic and the different interpretation of seasonal MASE are documented explicitly; the earlier five-product comparison must not be generalised to this cohort. This is an exploratory decision prototype, not a validated automatic replenishment policy.

An actual clean isolated dependency installation has been performed in `.venv-release-v3`, without changing your existing `.venv`. The launcher checks required modules, tries `.venv`, then `.venv-release-v3`, then active Python, and prints its selected interpreter. A specific interpreter can be requested with `-PythonPath`.

```powershell
.\.venv-release-v3\Scripts\python.exe -m scripts.verify_release --require-isolated --browser
powershell -ExecutionPolicy Bypass -File .\run.ps1 -Port 8000
```

The verifier runs dependency consistency, unit/API tests, lint, compilation and optional browser acceptance; each run writes actual command outcomes into a new timestamped `artifacts/releases/` directory. It refuses to call a global interpreter isolated, and failed commands stay failed. See artifacts/acceptance-v3.json for the observed release and source identities. Remote CI now calls the same verifier but remains unverified until observed remotely.
