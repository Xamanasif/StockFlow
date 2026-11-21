# StockFlow

Inventory & Working-Capital Decision Engine — working foundation, not a finished product.

Business question: with a limited purchase budget, which products should we replenish and what remains uncovered?

## Run on Windows PowerShell

Extract the ZIP, open the **StockFlow** folder containing this README in VS Code, and open its terminal.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 and API docs at http://127.0.0.1:8000/docs. Stop with Ctrl+C.
Activation is optional: explicit interpreter paths avoid PowerShell execution-policy problems.
After installing, `powershell -ExecutionPolicy Bypass -File .\run.ps1 -Port 8001` is an alternative launch command.

On macOS/Linux: `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, `.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.

## What is implemented

- Seeded, clearly labelled synthetic demo: five products and 120 calendar days.
- Invoice-line validation, UCI column aliases, cancellation/adjustment/zero-price classification, duplicate warnings and SHA-256 provenance.
- Two baselines: 28-day mean and weekday average over the preceding 56 days.
- Three seven-day temporal backtest folds reporting error totals, WAPE and signed error; no claim of a selected ML champion.
- Deterministic greedy allocation with integer-pence accounting, budget, aggregate capacity, existing inventory, on-order, packs, MOQ and explicit uncovered targets.
- Proposal snapshots in SQLite, including inputs, data hash and calculation outputs.
- FastAPI and a functional browser workbench; no Node toolchain or paid API required.
- 25 passing offline unit/API tests in the build environment. Browser behaviour has NOT been automatically exercised.

This is the first half by scope, not a claim of exactly 50% of implementation effort. The challenging decision simulation and honest evaluation remain for the next phase.

## Import real UCI data

Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii

Download the original data yourself, retain its attribution/license, and place its XLSX file in `data/raw/`. No real UCI file is bundled or downloaded in this starter. The importer accepts CSV or XLSX (all sheets); legacy XLS must first be converted to XLSX.

```powershell
.\.venv\Scripts\python.exe -m scripts.import_uci "data\raw\online_retail_II.xlsx" --output "data\imported.csv"
$env:STOCKFLOW_CSV = (Resolve-Path "data\imported.csv").Path
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The import validates the entire input before writing, drops customer fields, refuses existing output paths and creates a checksum sidecar. It labels a user-supplied UCI-format file, not independently authenticated data. Invalid required rows currently stop import; quarantine preview is a completion task. Forecasting an entire large dataset is not performance-validated; begin with an explicitly documented subset. Do not mix demo and real records.

To return to the demo: `Remove-Item Env:STOCKFLOW_CSV` and restart.

## Interpret outputs correctly

- Sales are observed transactions, not latent/unconstrained demand. Unobserved lost sales are not recoverable here.
- Missing invoice days are assumed zero recorded sales for the baseline. They are not proven opening days or complete observation days.
- Latest transaction date is the cutoff, not today's date. Original historical dates are preserved.
- Replenishment covers the forecast over review horizon plus assumed lead time; it is an aggregate target calculation, not a timed availability simulation.
- Stock, purchasing costs, lead times, packs and minimum orders are editable assumptions. Sale price is never silently used as procurement cost.
- Capacity counts all current/on-order units plus proposed orders. This is conservative aggregate accounting, not warehouse volume or arrival timing.
- Priority-weighted coverage is a heuristic objective, not profit. The greedy allocator has no optimality guarantee.
- The data-quality report preserves cancellations separately. It does not automatically link cancellation lines to original orders or infer return dates.
- Saved rows are proposals, not approvals or purchase orders. There is no live purchasing integration.

## Completion handoff

Open `docs/CODEX_COMPLETION_PROMPT.md`. Give Codex that entire prompt, or ask it:

> Read README.md, docs/STATUS.md, docs/FOUNDATION_GUIDE.md and docs/CODEX_COMPLETION_PROMPT.md. Complete the project as instructed, retaining truthful provenance and a working local launch. Start with a code audit and then implement the remaining phases.

No live Groq integration exists yet. `.env.example` is a future configuration template; the starter does not load it or make model calls.

## Local-only scope

Bind to `127.0.0.1`. This prototype has no user authentication or production hardening. Dataset selection is server-side through environment configuration; the browser cannot read arbitrary local paths.

