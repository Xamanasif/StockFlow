# Codex completion brief — StockFlow

You are continuing StockFlow, an inventory and working-capital decision engine. Finish the project to a polished, reproducible portfolio standard, and teach its owner to explain it deeply. The owner wants a strong business-oriented Data & AI project, not an application-specific demo. Do not mention Evalueserve or any job description in the product.

## Business purpose

Help a manager choose replenishment quantities under a limited purchasing budget, understand unmet requirements and compare availability/cash/cost trade-offs. The central research question is: does improved forecast accuracy produce better inventory decisions under identical constraints?

## Starting procedure

Read README.md, docs/STATUS.md and docs/FOUNDATION_GUIDE.md, inspect every module, run the existing tests and list concrete implementation defects. Preserve the working launch and original starter test intent. The foundation is not authoritative: fix errors and explain why. Do not inflate a failing assertion into a pass by weakening the check. No existing customer data or source history may be deleted without preserving a backup.

Work through all phases below autonomously. Maintain an implementation log, and clearly distinguish done, unverified and deferred. Finish the implementation, not merely a plan. Use free libraries and local execution; no paid services. Ask only for truly blocking user-specific information, such as unavailable credentials. Missing credentials must not block the other phases.

## Phase 1 — trustworthy real data

- Support the original UCI Online Retail II XLSX/CSV, verify current official source, license and schema, download from the official source if available and permitted, otherwise provide a precise manual command. Never claim a real-data run without actually performing it.
- Make an import-preview screen/report: required columns, invalid dates, missing identifiers, quantities, zero/negative prices, invoice cancellations, adjustment lines and possible duplicates. Allow explicit quarantine with reason codes rather than silently deleting rows. Customer IDs are unnecessary; minimise retained personal information.
- Preserve raw snapshots, source URL, download time, license, hashes, row accounting and dataset version. Imported data and metadata should be published atomically using a manifest/registry. Never overwrite demo or an existing dataset silently. Show provenance on every relevant screen/export.
- Do not assume transactions reveal inventory levels, supplier lead times, costs, opening days or unobserved demand. Maintain versioned scenario assumptions separately, with per-field provenance and currency. Audit partial latest days, missing calendar days and product entry/exit. Use zero-filling only under an explicit coverage assumption. Handle intermittent demand and minimum-history failures visibly.
- Restrict to a documented, manageable subset selected on development data; avoid using final-period performance to choose products. Cache/store canonical data efficiently instead of re-reading a million-row file on every request.

## Phase 2 — forecast evaluation before tuning

- Write EVALUATION_PROTOCOL.md before experiments: eligibility, cutoffs, development/tuning/calibration/final windows, feature availability, baselines, metrics and failure reporting. Hash it and retain subsequent changes visibly; do not backdate pre-registration.
- Include simple recent-mean, seasonal-naive and appropriate intermittent-demand baselines; add one practical tree/linear ML challenger. Use preceding-sales features only; fit transforms inside each temporal fold. Recursively forecast when future lags are unavailable. No random splitting of time rows. Do not use future sales, realised future promotions or product-selection information.
- Report global WAPE with denominator, MAE, signed bias and product/segment breakdowns. Zero actual totals require undefined percentage errors, not fake perfect scores. Report all evaluated eligible products, not only wins.
- Add a defensible uncertainty method calibrated on prior data. Evaluate empirical coverage and interval width; do not label intervals guaranteed. Reserve an untouched final period, prevent accidental reaccess and distinguish development reruns from final evaluation.
- Keep model losses. A validated simple baseline may remain champion. Do not manufacture lift or choose metrics after seeing the holdout.

## Phase 3 — day-by-day inventory simulator

- Specify event order in writing: outstanding orders/arrivals, observed-sales proxy, fulfilment, unmet proxy demand, returns if modelled, inventory costs, review, orders and future arrivals. Avoid same-day arrival for nonzero lead time.
- Keep integer units, pack/MOQ logic and integer minor currency units. Define lost-sales versus backlog semantics. Account for pipeline inventory, outstanding spending commitments, budget replenishment cadence, terminal inventory and capacity timing.
- Track inventory conservation and cash/cost conservation. Cost inputs are assumed procurement/holding/order/shortfall costs. Do not confuse gross sales revenue, margin, profit and cash. Never use sale price as procurement cost without an explicitly declared scenario.
- Historical sales are a proxy, not the counterfactual demand that would occur with unlimited inventory. Call outputs scenario replay/simulation and never historical realised savings. Synthetic perturbations and starting stock must be labelled. Separate real-sales replay from fully synthetic robustness experiments.
- Use common scenario seeds, starting inventories, exogenous demand sequences and lead-time draws across policies. Store all assumptions and seeds.

## Phase 4 — decision policies and business comparisons

- Implement transparent fixed/reorder-point or order-up-to baselines. Retain the starter greedy policy as a comparator. Add an optimiser only where its objective and constraints are specified and testable; SciPy MILP or another free solver is acceptable.
- State what is optimal (e.g. a static period problem), solver status/gap/timeout and what remains heuristic. Test optimised outputs against brute-force tiny cases. Feasible fallback on timeout must be explicit; do not invent optimality.
- Compare inventory costs, fill rate definition/denominator, unmet proxy units, average stock/capital and cash commitments under identical conditions. Show a Pareto trade-off instead of promising universal improvement.
- Include forecast-versus-policy cross-comparisons so forecasting lift and decision improvement are not conflated. Run sensitivity to cost ratios, lead times, budget, demand variability and stock assumptions; retain regimes where the proposal loses.

## Phase 5 — product experience

- Create a polished responsive React/TypeScript interface or equivalently strong maintainable frontend; keep a single clear local launch script that starts necessary processes and handles port conflicts. Do not force needless infrastructure.
- Screens: overview/action queue, data quality and provenance, product evidence/forecast chart, assumptions editor, budget/capacity planning, policy comparison/scenario lab, proposal detail/history and assistant.
- Lead with the business decision: what to buy, what cannot fit, why, required cash and uncertainty. Charts need dates, currency, units, legends and loading/error/empty states. Show real vs synthetic vs assumed labels persistently.
- Support CSV exports and a self-contained decision report containing input versions, assumptions, method, results and limitations. No fake testimonials, fabricated ROI or employer branding.
- Accessibility: keyboard navigation, labelled inputs, visible focus, readable contrast and mobile-safe tables. Render user/source text as text, not unsafe HTML.

## Phase 6 — grounded Groq assistant

- Implement server-side provider adapter using the current official Groq API documentation. Model name is configurable; verify availability rather than assuming an old model works. Keep keys in environment variables, never frontend code, logs or committed files.
- Restrict tools to validated read-only functions such as get_product_evidence, get_forecast, get_plan, compare_policies, get_assumptions and get_evaluation. No arbitrary SQL/Python/filesystem/network tools. No purchasing, confirmation or data import tool.
- Bound tool loops, output size, timeout and retries. Handle rate limits and missing keys explicitly. Offline mode must be labelled local rules/no LLM, never presented as Groq.
- Cite actual run/product/record evidence IDs. Numerical answers must use tool outputs, with currencies, units and dates. Test contradictory sources, missing evidence, sign/unit errors, stale plans and instructions hidden in descriptions. Never assume lexical numeric matching proves correct reasoning.
- Document whether live calls were actually run. Provider mocks test software behaviour, not LLM accuracy. If key absent, finish mocks and evaluation harness and mark the live benchmark unverified.

## Phase 7 — review and engineering controls

- Implement a genuine human proposal-review workflow. Preview exact contents; approvals reference an immutable version and fresh evidence/assumptions hash. Reject stale, expired and reused requests. Prevent duplicate saves under concurrency; rollback incomplete transactions. No automatic external orders.
- Local unauthenticated confirmation is not identity assurance; label it appropriately. Add real authentication/tenant isolation only if scope requires it, with meaningful negative tests. Do not claim production security without evidence.
- Add structured logs with request/run IDs, durations, data/method versions and error categories; redact keys and source-sensitive content. Provide local health/readiness checks and a concise troubleshooting guide. Avoid unneeded telemetry services.
- Add dependency lock, lint/type checks as useful, reproducible launch on Windows, CI workflow and optional Docker packaging. Run builds/checks actually supported by the environment; do not claim Windows verification from a Linux-only run.

## Phase 8 — tests and actual evidence

- Extend unit and API coverage with a real importer round trip and bad inputs, temporal leakage perturbation, fold-local preprocessing, zero/intermittent products and uncertainty edge cases.
- Test budget/capacity/MOQ/pack invariants, nonfinite inputs, very large requests, conservation, arrival timing, terminal stock, solver infeasibility and fair policy seeds.
- Browser-test a complete path: choose data, inspect quality, configure assumptions, run plan, compare policies, review/confirm, revisit saved history and read an assistant answer. Test error/empty/mobile states and security boundaries as applicable.
- Separate constructed scenario assertions, real-data forecast evaluation, simulated business outcomes, live LLM evaluations and software tests. None substitutes for another.
- Save machine-readable results with denominators, data hashes, code commit/hash, timestamps, seeds, protocol version and exact commands. Never fabricate savings/accuracy, make a hidden final-test rerun or turn an observed association into causal business impact.

## Required learning deliverables

Create docs/PROJECT_MASTER_GUIDE.md with:
1. Business user, decision, alternatives, success criteria and boundaries.
2. Architecture and a traced request from invoice through forecast, policy, simulator, API, database and UI.
3. Mathematical walkthrough of forecasts, WAPE/bias, uncertainty, reorder logic, budget constraints, cost accounting and optimiser objective.
4. Code walkthrough naming each important module/function, purpose, inputs, outputs, failure cases and why it exists.
5. Worked examples using actual saved project rows and results; mark illustrative numbers as illustrative.
6. Technology explanations: Python/pandas/SQL, FastAPI/Pydantic, frontend state, persistence, transactions, HTTP/API errors, model training, solver and Groq tool calls.
7. Trade-offs and rejected alternatives; baseline losses and unresolved limitations.
8. At least 60 interview cross-questions with answers tied to code or saved results, including leakage, demand censoring, counterfactuals, costs, optimisers, concurrency and hallucinations.
9. At least 12 hands-on exercises with tests/solutions so the owner can independently inspect and change the project.
10. Honest contribution account: user specification versus AI-generated code, what the owner must reproduce and personally verify before claiming it.

Also create ARCHITECTURE.md, DATA_CARD.md, MODEL_CARD.md, DECISION_POLICY_CARD.md, EVALUATION_REPORT.md, KNOWN_LIMITATIONS.md, BUILD_LOG.md, DEMO_WALKTHROUGH.md and RESUME_EVIDENCE.md. Keep a docs index. Use diagrams where useful, without burying the beginner in jargon.

## Resume evidence, last step only

Produce exactly three concise resume bullets, approximately 25–35 words each: business system, strongest actual comparison/finding, and trustworthy engineering. Prefer one meaningful metric comparison across the three bullets; do not fill every sentence with test counts or dataset sizes. Include denominator and benchmark context where needed. Attach evidence paths and limitations separately. Do not describe real company deployment, realised financial savings, live Groq testing or independent personal work without evidence.

## Final response

Report completed features, exact launch commands, actual test/experiment outcomes, files to study first, remaining limitations and any live paths not exercised. Confirm the folder remains named StockFlow. Deliver the functioning project and all documentation; do not stop after scaffolding or planning. Success is a trustworthy decision tool with defensible findings, not a claim of a perfect model or guaranteed business impact.
