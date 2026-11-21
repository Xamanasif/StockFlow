# Build status and acceptance record

## Delivered foundation

See README for supported functionality and precise modelling assumptions. Run `python -m unittest discover -s tests -v` from the project root. Initial environment run: **25 tests passed**. They cover ingestion failures, cancellation handling, duplicate preservation, checksum mismatch, UCI aliases, temporal leakage perturbation, horizon alignment, zero-denominator WAPE, pack/MOQ constraints, budget/capacity invariants, deterministic planning, invalid inputs and saved API snapshots.

## Remaining half

1. Robust real-data import with preview/quarantine, atomic data+metadata publication and a dataset registry.
2. Predefined temporal evaluation protocol, simple baselines, ML challenger and uncertainty diagnostics.
3. Day-by-day inventory replay under explicit purchase/inventory assumptions, common exogenous sequences and timing rules.
4. Baseline purchasing policies and an optimisation challenger; fair comparisons and scenario sensitivity.
5. Business-facing UI with charts, error states, data lineage, assumptions and proposal review.
6. Read-only grounded Groq assistant, restricted tools, citation checks and honest fallback.
7. Version-bound human approval workflow, migrations and audit controls.
8. Integration/browser tests, CI, observability, reproducible artefacts and interview documentation.

## Not yet verified

- No original real UCI import was run here; importer logic is tested on tiny UCI-shaped frames.
- No model provider was called.
- No automated browser test or visual browser inspection was performed.
- No optimisation superiority, real savings, realised service improvements or production readiness is claimed.
- Dependency ranges are not a lockfile; completion should create a tested reproducible environment.
- Import publishes CSV then sidecar, not a single atomic manifest switch. A crash can leave a partial unpublished import.
- CSV reloading per API request is acceptable for demo scale only; real-data caching/storage is unfinished.
- No prediction intervals, demand-censoring correction, ML challenger, simulator or approval capability yet.

