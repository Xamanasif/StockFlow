# Resume evidence — three draft bullets

Use these only after independently reproducing and explaining the project. Development was AI-assisted; do not imply unaided implementation, company deployment or realised financial impact.

- Developed an AI-assisted inventory decision workbench combining recorded-sales forecasts, constrained replenishment, scenario replay and human proposal review, helping managers inspect purchasing cash, uncovered requirements and service-versus-cost trade-offs under explicit assumptions.
- Benchmarked five temporal forecasting methods on a held-out seven-day period covering 2,132 recorded units; seasonal naive achieved 70.59% WAPE versus Ridge’s 81.58%, retaining the simpler model’s advantage and uncertainty limitations.
- Implemented immutable dataset provenance, reason-coded quarantine, transactional proposal snapshots and version-bound local review, with concurrency, leakage, conservation and browser checks supporting reproducible analysis and auditable purchasing proposals before human review.

## Evidence and limits, separate from bullets

Business system: `app/main.py`, `app/planning.py`, `app/optimizer.py`, `app/simulation.py`, `app/static/`, `artifacts/worked-proposal.json`, `artifacts/browser.json`. Local unauthenticated reviews do not establish reviewer identity or place external orders.

Comparison: `artifacts/real-final.json:evaluation.summary`, `docs/EVALUATION_PROTOCOL.md`, `docs/EVALUATION_REPORT.md`, and exclusive `artifacts/FINAL-<dataset-hash>.json`. Denominator is 2,132 observed sales units over 35 product-days across five development-selected products. These high errors do not establish production forecasting quality; final results were not used to tune models. Source bytes matching the recorded code hash are in `artifacts/source-at-final.zip`.

Engineering: `artifacts/test-results.json`, `artifacts/tests.txt`, `artifacts/browser.json`, `app/registry.py`, `app/storage.py`, `tests/test_completion.py`. Software checks are distinct from forecast/replay evidence. Raw UCI data was actually imported, but procurement costs, stock and lead times are assumed; no realised savings or live Groq accuracy is claimed. Remote CI, clean-environment installation and production deployment remain unverified.

Contribution: user provided specification and foundation; completion code, tests and documentation were AI-assisted/generated. The owner must personally trace/reproduce results and make tested changes before claiming independent mastery. See PROJECT_MASTER_GUIDE.md section 10.
