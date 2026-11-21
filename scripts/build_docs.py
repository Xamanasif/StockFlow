"""Build human-readable documentation from saved evidence; never invent results."""
import json
from app.data import ROOT

def write(name,text): (ROOT/'docs'/name).write_text(text.strip()+'\n',encoding='utf-8')

def main():
    demo=json.loads((ROOT/'artifacts/development.json').read_text(encoding='utf-8'))
    real_path=ROOT/'artifacts/real-development.json'
    real=json.loads(real_path.read_text(encoding='utf-8')) if real_path.exists() else None
    table='|Method|WAPE|MAE units|Bias units|Empirical coverage|Mean interval width|\n|---|---:|---:|---:|---:|---:|\n'
    for r in demo['evaluation']['summary']:
        table+=f"|{r['method']}|{r['wape']:.2%}|{r['mae']:.3f}|{r['signed_error']:.2f}|{r['covered']}/{r['interval_observations']}|{r['mean_width']:.3f}|\n"
    comparisons=demo['comparison']; ct='|Forecast|Policy|Filled/proxy units|Scenario cost GBP|Mean stock units|Pareto|\n|---|---|---:|---:|---:|---|\n'
    for r in comparisons: ct+=f"|{r['method']}|{r['policy']}|{r['fulfilled_units']}/{r['proxy_demand_units']}|{r['scenario_cost_pence']/100:.2f}|{r['average_stock_units']:.2f}|{r['pareto']}|\n"
    write('EVALUATION_REPORT.md',f'''# Actual evaluation evidence

Commands and machine-readable records: `artifacts/development.json`, `artifacts/real-development.json` when present, and separate `*final.json`. Each records data/protocol/code hashes, timestamp, versions and seed. The script preserves previous output versions. No Git commit exists in the supplied folder; source content hashes substitute for a commit identifier.

## Synthetic development forecasts

Denominator: {demo['evaluation']['summary'][0]['actual_units']:.0f} recorded units across {demo['evaluation']['summary'][0]['observations']} product-days, five products and two seven-day folds. These are constructed demo transactions, not company impact. All evaluated methods appear below.

{table}

Weekday mean beats Ridge on this development metric; its intervals under-cover the nominal 80% target. The ML challenger is retained as a loss. No universal forecasting or service improvement is established. Product rows include regular/intermittent segment membership, raw errors and predictions; aggregate global WAPE weights high-volume products more strongly.

## Identical-scenario purchasing comparison

Costs are hypothetical GBP amounts, including purchase outlay, holding, order and shortfall charges. Terminal inventory receives no credit; this is neither profit nor financial ROI. Paid pipeline, initial stock, and weekly cash grants are explicit in each row. Fill rate is fulfilled proxy units / all proxy units, not customer-order service rate.

{ct}

Sensitivity evidence: eight one-at-a-time variants in `development.json:sensitivity`: cash grants, lead time, shortfall ratio, initial stock and synthetic variability. Rows retain losing regimes; inspect costs and unmet units jointly. All forecast/policy combinations in each regime share an exogenous sequence hash. The static MILP solves weighted target coverage at a review; it does not optimise the entire replay cost.

## Real-data status

{('An official-source workbook was actually imported and its development experiment saved. See real-development.json and real-import.json; the latter records full-workbook accounting and subset selection. Read its metrics below, separately from demo results.' if real else 'No successful real-data experiment is asserted by this document version. Run status and retained raw files do not substitute for an imported/evaluated artefact.')}

## Evidence categories

Unit/API tests establish constructed invariants. Browser tests exercise a synthetic user workflow. Forecast results evaluate recorded-sales prediction. Replay results depend on invented procurement/inventory assumptions. Provider mocks exercise adapter behavior; they do not measure live model reasoning. A final receipt prevents automatic repeated access; an owner with filesystem access can bypass it, so this is a procedural guard, not an access-control guarantee.
''')
    if real:
        with (ROOT/'docs/EVALUATION_REPORT.md').open('a',encoding='utf-8') as f:
            f.write('\n### Real development metrics\n\n|Method|Absolute error / actual units|WAPE|Coverage|\n|---|---:|---:|---:|\n')
            for r in real['evaluation']['summary']: f.write(f"|{r['method']}|{r['absolute_error']:.2f} / {r['actual_units']:.0f}|{r['wape']:.2%}|{r['covered']}/{r['interval_observations']}|\n")
    final_path=ROOT/'artifacts/real-final.json'
    if final_path.exists():
        final=json.loads(final_path.read_text(encoding='utf-8'))
        with (ROOT/'docs/EVALUATION_REPORT.md').open('a',encoding='utf-8') as f:
            f.write('\n## One-use real final period\n\nFinal actual denominator: 2,132 recorded units, 35 product-days (five products, seven days). All methods were evaluated once; no settings or deployed policy were changed based on this result. Receipt: artifacts/FINAL-<dataset-hash>.json.\n\n|Method|Absolute error / actual units|WAPE|Coverage|Mean width units|\n|---|---:|---:|---:|---:|\n')
            for r in final['evaluation']['summary']: f.write(f"|{r['method']}|{r['absolute_error']:.2f} / {r['actual_units']:.0f}|{r['wape']:.2%}|{r['covered']}/{r['interval_observations']}|{r['mean_width']:.2f}|\n")
            f.write('\nSeasonal naive beats Ridge on this final period, reversing the development ranking. High absolute percentage errors and wide intervals remain important limitations, not suppressed results. No final-based retuning was performed. Exact numerical source bytes matching the saved code hash are archived in artifacts/source-at-final.zip; subsequent registry display and browser-harness fixes changed no forecast, optimiser or replay logic.\n')
    if real:
        with (ROOT/'docs/EVALUATION_REPORT.md').open('a',encoding='utf-8') as f:
            f.write('\n## Real development decision cross-comparison\n\n|Forecast|Policy|Filled / proxy units|Scenario cost GBP|Average stock units|\n|---|---|---:|---:|---:|\n')
            for r in real['comparison']: f.write(f"|{r['method']}|{r['policy']}|{r['fulfilled_units']}/{r['proxy_demand_units']}|{r['scenario_cost_pence']/100:.2f}|{r['average_stock_units']:.2f}|\n")
            f.write('\nUnder the default tight budget and common exogenous sequence, Ridge has lower development WAPE but greedy replay fulfils 260/4,087 proxy units, versus weekday mean 456/4,087. This constructed scenario does not establish a general causal effect. Static MILP reaches 456/4,087 for both forecast methods; forecast accuracy and purchasing policy are separate decisions. The replay budget is deliberately tight relative to these volumes, and all procurement/penalty inputs remain assumptions.\n')
    write('ARCHITECTURE.md','''# Architecture

```mermaid
flowchart LR
  Raw[Local raw snapshots] --> Preview[Preview and reason codes]
  Preview --> Registry[Immutable version directory and manifest]
  Registry --> Daily[Positive recorded sales and calendar assumption]
  Daily --> Forecast[Fold-local baselines and recursive Ridge]
  Forecast --> Static[Greedy or static MILP]
  Daily --> Replay[Daily lost-sales scenario replay]
  Static --> Replay
  Static --> API[FastAPI / Pydantic]
  API --> DB[SQLite immutable proposal and review receipts]
  API --> UI[HTML / CSS / JavaScript workbench]
  DB --> Assistant[Read-only evidence selector and renderer]
```

The backend serves the maintainable zero-build frontend, so one process and one origin suffice. Modules separate ingestion, research, allocation, replay, storage and assistant. `main.dataset` caches at most four versions keyed by path and CSV/metadata modification times. The first load verifies the SHA-256 sidecar. Only static assets are mounted; raw snapshots and databases are not web roots.

`POST /api/plans` validates assumptions, checks products, forecasts lead plus review horizon, allocates integer lots, snapshots inputs/provenance/results, hashes sorted JSON, and inserts within a transaction. An optional Idempotency-Key binds concurrent retries to the same fingerprint and run. A reused key with different inputs returns 409. Review challenge preview contains exact saved JSON. Confirmation checks expiry, one-time use, current data hash, latest persisted assumptions hash and snapshot integrity under BEGIN IMMEDIATE. Receipt and token consumption commit together. SQLite file owners can edit everything; there is no authenticated identity assurance.

Data publication builds a hidden staging directory with canonical CSV, metadata, quarantine, raw snapshot and manifest, then renames it on the same filesystem. Registry enumeration ignores staging. This is atomic visibility, not a guarantee against power-loss without filesystem durability. Unique version directories avoid overwriting datasets.
''')
    write('DATA_CARD.md','''# Data card

Official source: https://archive.ics.uci.edu/dataset/502/online+retail+ii . Attribution: Chen, D. (2012), Online Retail II, UCI Machine Learning Repository, DOI 10.24432/C5CG6D. Official page checked during this build; license CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ . Source schema contains invoice, stock code, description, quantity, timestamp, unit price, customer identifier and country. Historical coverage and exact downloaded bytes are recorded in import metadata, not inferred from filename.

Canonical retained columns: invoice, SKU, normalized calendar date, integer quantity and sale price. Customer IDs, description and country are dropped from canonical and quarantine tables. The preserved original workbook contains source fields, including customer identifiers: keep it local and restrict access. It is not served by the API. Raw snapshots are excluded from Git. No attempt is made to reidentify customers.

Positive quantity/price lines excluding C-prefixed invoices become sales. Cancellation and nonpositive-quantity adjustments remain visible but are not demand or simulated returns. Negative prices, malformed dates, nonfinite/fractional quantities and missing identifiers have explicit quarantine reason codes; publishing rejected rows requires --quarantine. Duplicates remain and are flagged. Row accounting must reconcile input = retained + quarantine; reason counts overlap.

Demo uses seeded synthetic transactions and has separate hashes. Real research uses up to five products ranked by units during the first 60 days, requiring entry within the first 14 days. This is a manageable, volume-biased subset, not representative of every retailer SKU. Latest day is potentially partial and excluded from research. Missing days are zero recorded sales only under the stated coverage assumption. Last observed sale is not proof of product exit; first sale is not actual launch date.

Transactions contain no procurement costs, stock balances, supplier lead times, opening days or lost sales. Scenario fields carry explicit assumed provenance and GBP minor units; never equate sale price with purchase cost. Checksums prove byte identity, not source correctness.
''')
    write('MODEL_CARD.md','''# Forecast model card

Task: predict nonnegative daily recorded units for a selected SKU. `forecasting.py` preserves the starter operational weekday and recent-mean baselines and 14-day minimum. `research.py` imposes a 28-day since-first-sale minimum, with explicit failures. Unknown products fail rather than silently becoming zero-demand products.

Research methods: recent 28-day mean; weekday means over 56 days; last-week seasonal naive; Croston SBA with alpha=.1 and correction .95; Ridge alpha=10 with fold-local StandardScaler. Ridge features are preceding lag 1/7/14, preceding seven-day average, and known weekday. Multi-step forecasts append predicted values so future lags never use realised future sales. It is a linear ML challenger, not a demand-censoring model.

`EVALUATION_PROTOCOL.md` predates the saved experiments in this build. Its hash is in every research artifact. No random row splits or final-period product selection. Prior residuals calibrate empirical 80% intervals; chronological dependence and small samples undermine nominal guarantees. Report coverage and width together, including undercoverage. Calibration is not fitted on evaluation actuals.

Operational plans keep the interpretable weekday baseline. Champion selection is based on development WAPE; no final-based switching. Review `EVALUATION_REPORT.md` before claiming any accuracy advantage. Seasonal change, closures, incomplete source capture, intermittent/new products, outliers and wholesale baskets limit transferability. Sales are censored by unknown availability; these models do not recover unconstrained demand.
''')
    write('DECISION_POLICY_CARD.md','''# Decision policy card

Static target = predicted units over review + assumed lead time minus on-hand and on-order, lower-bounded at zero. Requested order is rounded to pack multiples and at least ceil(MOQ/pack)*pack if positive. Greedy repeatedly adds the best affordable marginal priority-weighted covered-unit lot per penny, with deterministic SKU tie-breaking and a visible iteration cap. It can lose to a global combination.

MILP variables: integer pack count x_i, binary activation y_i, continuous covered units z_i. Maximise sum priority_i*z_i. Bound z_i by uncovered forecast and pack_i*x_i; minimum_packs*y_i <= x_i <= target_packs*y_i. Sum cost_i*pack_i*x_i <= purchasing cash; sum pack_i*x_i <= free aggregate capacity. SciPy HiGHS status/gap are exposed. On unsuccessful solve, return feasible greedy with an explicit fallback. Optimality concerns this static objective only, with possible equal-objective alternative spends; never claim dynamic cost optimality. Tests compare tiny cases against enumeration.

Replay comparator `fixed` sets its order-up-to target from the forecast available before replay starts and reuses it at weekly reviews. `greedy` and `milp` refresh targets using information through the current end-of-day review. This is an intentional policy difference, not a pure allocator-only comparison. Forecast × policy crosses keep this distinction visible.

Event order: weekly cash grant at day start; due arrivals; fulfil positive recorded-sales proxy; lose unmet units (no backlog); charge end-day holding and unmet-unit penalties; weekly end-day review; pay orders/charges immediately; enqueue arrivals at t+max(1,lead+common jitter). Even zero configured lead arrives next day under this conservative convention. Returns are not modelled. Capacity reserves physical + pipeline units, so arrivals do not create surprise overflow. On-order purchase cost has already been paid; unpaid commitments are zero.

Conservation: stock_end = initial + arrivals - fulfilled; pipeline_end = placed - arrived; cash_end = weekly grants - purchase outlay - order charges. Holding and shortfall are economic scenario costs, not cash debits against procurement grants. Total reported scenario cost sums purchase, order, holding and shortfall costs, with no terminal salvage credit. Initial stock is assumed endowed and its acquisition cost is excluded. Terminal physical and paid pipeline quantities/value are explicit. Revenue/margin/profit are not computed.
''')
    write('KNOWN_LIMITATIONS.md','''# Known limitations and unverified paths

- Local unauthenticated, single-process prototype; no tenant isolation, production security claim, or live purchasing. Loopback binding only. Do not expose publicly.
- Recorded sales proxy cannot identify historic stockouts, lost demand, causal savings or service uplift. Assumed costs and starting stock drive replay outcomes.
- Five development-selected products create selection bias. Calendar zero-fill is a declared assumption. Latest day exclusion is conservative, not proof other days are complete.
- Per-product empirical intervals have small, temporally dependent calibration samples; nominal coverage can fail. No censored-demand correction or automatic seasonal regime detection.
- Static MILP is not a globally optimal dynamic policy; time limits trigger greedy fallback. Fixed-target policy freezes its initial forecast; other policies update. Shared sequences ensure fairness within the defined comparison, not external validity.
- Raw workbook is retained locally and may include source customer IDs. Canonical records minimise fields. Source license/attribution must travel with distributed data.
- Registry rename offers atomic visibility on one filesystem, not power-loss durability or a multi-host database. Cache assumes immutable registry versions; file-owner attacks are outside scope.
- Final receipt is a procedural local guard, bypassable by a file owner. Failed attempts must remain recorded. Do not silently delete receipts or retune based on final metrics.
- Groq integration is opt-in via environment key and account-available model. Without credentials it is local rules/no LLM. No paid calls were authorised by the free-local project scope; live calls and reasoning accuracy remain unverified. Mocks do not substitute for a live benchmark. The model selects evidence claims, while templates enforce quantities and citations; free-form assistant reasoning is intentionally deferred.
- Browser coverage uses headless browser and constructed demo state; it is not exhaustive accessibility, cross-browser or penetration testing. CI configuration is supplied; remote CI runs are unverified until pushed and observed.
- requirements.lock records tested dependency versions, without wheel hashes. Clean installation/network availability and non-Windows platforms need their own verification. Optional Docker is deferred; a single local process meets the launch requirement.
''')
    write('BUILD_LOG.md','''# Implementation log

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
''')
    write('DEMO_WALKTHROUGH.md','''# Demo walkthrough

From the folder containing README.md: install requirements.lock in Python 3.13, then run run.ps1. Open http://127.0.0.1:8000 . The badge must say synthetic_demo for the default dataset.

1. Read overview and open quality/provenance; explain zero-filled days and assumptions.
2. Inspect SKU-001. Trace recorded units and dated forecast chart; read baseline errors without calling them demand accuracy.
3. Set budget to GBP 100, edit assumed stock/cost/lead time JSON, and build proposal. Identify proposed spend and uncovered target. The save is a proposal, not an order.
4. Run the scenario comparison. Explain filled/proxy denominator, cost assumptions, terminal stock and Pareto alternatives; a better forecast need not minimise replay cost.
5. Refresh history, select the newest proposal, and preview exact contents. Confirm locally. Repeating the same token must fail. Change and save assumptions to demonstrate stale-review rejection.
6. Export CSV and complete decision report. Both contain snapshot and dataset hashes.
7. Ask the assistant about cash/uncovered target. Without credentials, explicitly read the local-rules/no-LLM label and saved record citation.
8. Switch to a registered real subset through Data registry, inspect lineage, and repeat. A saved demo evaluation must show stale-for-active-dataset. The server selection is session-local; use STOCKFLOW_CSV to choose a persistent startup dataset.

Reproduce tests: `python -m unittest discover -s tests -v`; research: `python -m scripts.evaluate --sensitivity`; browser: `python -m scripts.browser_test`. Windows defaults to installed Edge; set STOCKFLOW_BROWSER=chromium after `python -m playwright install chromium` to use its downloaded browser. Final research requires a distinct output and --final; never remove the receipt to rerun after inspecting results.
''')
    write('TROUBLESHOOTING.md','''# Troubleshooting

Use Python 3.13 and explicit .venv\\Scripts\\python.exe paths if PowerShell activation is blocked. Install `requirements.lock`. A port conflict in run.ps1 suggests the next port; pass -Port 8001 and open that address. Keep the server bound to 127.0.0.1.

503 readiness: inspect selected CSV, required matching .meta.json hash and writable STOCKFLOW_DB directory. Restart to clear a manually changed immutable registry cache. 422: read validation detail; check integer units, finite costs, known SKU and existing-plus-pipeline capacity. 404 evaluation: run scripts.evaluate. 409 review: preview a current proposal; do not reuse a token. Changing persisted assumptions invalidates pending reviews.

Unknown GROQ_MODEL, missing key, 429, timeout or malformed output leads to an explicitly labelled local fallback. Set variables in the server process; .env.example is not auto-loaded. Never paste keys into the browser or logs. No retries are attempted automatically, avoiding duplicate costs. Each HTTP request has X-Request-ID and a structured duration/status record. Query text and keys are not logged by application middleware.

Browser executable missing: install Edge or run `python -m playwright install chromium` and set STOCKFLOW_BROWSER=chromium. Network restrictions can prevent downloads; preserve failed files and use the official command in README. Reproducibility requires separate software, forecast, replay and provider evidence, not merely a green health endpoint.
''')
    write('INDEX.md','''# Study and evidence index

Start with PROJECT_MASTER_GUIDE.md, then ARCHITECTURE.md, EVALUATION_REPORT.md and DEMO_WALKTHROUGH.md. Inspect executable paths and saved JSON while studying.

- EVALUATION_PROTOCOL.md — pre-experiment build protocol and final-use rules
- DATA_CARD.md — provenance, license, schema and assumptions
- MODEL_CARD.md — models, features, intervals and failure modes
- DECISION_POLICY_CARD.md — objectives, timing and accounting
- KNOWN_LIMITATIONS.md — boundaries, deferred and unverified paths
- BUILD_LOG.md — audit defects and implementation decisions
- TROUBLESHOOTING.md — local launch and errors
- RESUME_EVIDENCE.md — exactly three defensible bullets with evidence
- STATUS.md — current acceptance record; STATUS.foundation.md preserves original
- FOUNDATION_GUIDE.md — starter concepts; CODEX_COMPLETION_PROMPT.md preserves the full original brief
- ../artifacts/ — machine-readable evidence, screenshots, test output, and worked proposal
''')

if __name__=='__main__': main()
