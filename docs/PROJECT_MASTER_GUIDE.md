# StockFlow project mastery guide

Read this with the application open and `artifacts/development.json` beside you. These are implemented behaviors, not a proposed architecture. The original brief remains in CODEX_COMPLETION_PROMPT.md. INDEX.md links all cards and reports.

## 1. Business decision and boundaries

The user is a purchasing or inventory manager with a restricted procurement budget. The decision is which integer lots to buy, how much cash to commit, which requirements remain uncovered, and which service/cost trade-offs deserve human review. Alternatives are a fixed order-up-to rule, a frequently refreshed greedy allocation, and a static optimiser. A successful tool exposes feasibility, assumptions, timing, evidence and losses; it does not need to make an ML model win.

Measure recorded-sales forecast error separately from replay fill rate and scenario cost. The research question is whether lower prediction error translates into better decisions under identical purchasing conditions. It may not: an error on an expensive or constrained product matters differently from an error on an unconstrained one. Lower WAPE is not an economic objective. Do not claim realised savings, causal impact, recovered lost sales, authenticated purchasing or company deployment.

The application is a local single-user prototype. Sales, assumed inventory and simulated outcomes are distinct. A real sales source does not make its assumed supplier cost real. Cancellation rows are not automatically linked returns. Missing dates are zero recorded sales under an explicit coverage assumption; closure and missing capture cannot be distinguished.

## 2. Trace one request end to end

Start at `data/demo_transactions.csv` and its SHA-256 metadata. `data.validate` checks canonical columns and classifies positive sales, cancellations, adjustments and zero-price lines. `registry.preview` first separates malformed rows with reason codes. `registry.publish` writes a hidden version directory and atomically renames it into view. Customer fields remain only in the preserved original local workbook, not canonical data or API responses.

`main.dataset` selects the server-configured CSV and caches verified canonical frames. `forecasting.history` filters through the cutoff, selects one SKU and reindexes calendar days from first sale. `predict` produces the operational weekday-mean point forecast. `research.forecast` implements richer offline comparisons. In `POST /api/plans`, Pydantic validates assumptions, the server computes lead-plus-review forecast totals, and `planning.allocate` or `optimizer.optimize` chooses feasible lots.

`storage.db` starts a SQLite connection, creates version-one tables, yields it to the operation, commits on success, rolls back on failure and always closes it. `main.plan` snapshots exact assumptions, provenance, method and outputs; sorted JSON gets a SHA-256 identity. Idempotency keys prevent duplicate snapshots under concurrent retries of one operation. Saved proposal payloads are never updated by review.

The UI receives JSON through fetch, stores the active proposal/review token in explicit JavaScript variables and renders user/source values with textContent. It displays proposed spend, uncovered rounded targets and a saved-snapshot link. The history screen previews exact contents, receives a five-minute token, then sends its token and hash to `/api/confirm`. A BEGIN IMMEDIATE transaction compares current dataset and persisted-assumption hashes, verifies snapshot bytes and inserts one local review receipt while consuming the token.

Inventory replay is a separate route. `simulation.compare` crosses five forecast methods with three policies. `replay` advances daily inventory and cash under common exogenous sales and lead-time draws, rather than pretending the static plan predicts historical stockouts. The assistant reads a selected immutable plan; offline mode is explicitly local rules/no LLM. Optional Groq selects a subset of allowed claim IDs. Numerical text is rendered from typed saved fields, not trusted free-form model prose.

See ARCHITECTURE.md for the diagram. A forecast row is not an order; a saved proposal is not a review; a local review is not a purchase order.

## 3. Mathematical walkthrough

Let recorded daily units be y_t. The recent mean is the average of the last min(28,n) days. Weekday mean averages up to eight preceding observations of the same weekday across 56 days. Seasonal naive repeats y_(t-7), recursively repeating the last observed week. Missing values after first sale enter these formulas as zero recorded units by assumption.

Croston smooths nonzero transaction-day size z and the gap p between nonzero days: z <- z + .1*(observed-z), p <- p + .1*(gap-p). SBA predicts .95*z/p. Leading zeros enter the first gap. It is suited to intermittent patterns but cannot infer unseen demand. Research requires 28 calendar days since first sale; an unseen product is an explicit error.

Ridge fits squared prediction loss plus alpha*sum(coefficients squared), alpha=10. Inputs are preceding sales lag 1/7/14, mean of preceding seven days and weekday. StandardScaler learns feature means/scales inside the same training fold. Recursive forecasting appends each predicted value before making the next feature vector. A future realised lag would leak the answer.

Across product-days, AE = sum |forecast-actual|, WAPE = AE / sum actual, MAE = AE/N, signed bias = sum(forecast-actual). WAPE is null when actual total is zero, even if absolute error is nonzero. Global WAPE weights by volume; average product WAPE weights each eligible product equally and excludes/handles zero denominators separately. Both need their denominators disclosed.

For an empirical 80% interval, collect absolute errors from three preceding seven-day calibration folds. Select the sorted residual at index ceil((n+1)*.8), capped at n. Radius q produces [max(0,prediction-q),prediction+q]. Calibration precedes development and final assessment. Temporal dependence and small n mean empirical coverage can fall below nominal coverage; always report covered/N and average width. A wide interval can cover well while being operationally unhelpful.

For item i, expected coverage F_i covers review R plus assumed lead L_i. Net requirement g_i=max(0,F_i-on_hand_i-on_order_i). Target order rounds g_i upward to pack multiples and, if positive, at least the minimum pack multiple satisfying MOQ. Feasibility requires sum cost_i*q_i <= budget and existing physical + on-order + sum q_i <= capacity. Money is integer pence; GBP display divides by 100 only at the presentation boundary.

Greedy scores the next feasible lot by priority-weighted marginal covered units / cash. Its first lot satisfies MOQ; later lots add one pack. A large efficient lot can crowd out a globally better combination. The MILP maximises sum priority_i*z_i with integer pack counts, binary activation and z_i bounded by both purchased units and uncovered forecast. It solves only that specified static objective. It does not optimise future stochastic demand or replay costs, and equal objective solutions can spend different amounts.

Replay timing: grant weekly purchasing cash; receive orders due today; fulfil the common observed-sales proxy; discard unmet proxy units; charge holding and shortfall costs; review weekly at day end; pay procurement and ordering charges; schedule arrivals no earlier than tomorrow. Initial stock is endowed. Procurement grants are separate from economic holding/shortfall charges. Cash_end = grants - purchases - ordering. Stock_end = initial + arrivals - fulfilled. Pipeline_end = placed - arrived. Scenario cost = procurement outlay + ordering + holding + shortfall; there is no salvage credit. Report terminal physical and paid pipeline stock so end effects remain visible.

## 4. Code map and failure cases

|Module / function|Inputs and outputs|Purpose and failure boundary|
|---|---|---|
|data.validate|Raw frame -> canonical classified frame, audit|Reject missing columns, malformed values, negative prices; duplicates flagged, not deleted|
|data.load_dataset|CSV path -> frame/audit/metadata|Requires provenance and matching bytes; rejects no eligible sales|
|registry.read_raw / preview|CSV/XLSX -> all sheets, clean/rejected/report|Reason-coded invalid rows; minimises customer fields|
|registry.publish / datasets|Source and provenance -> version path/list|Atomic visibility; explicit quarantine, never overwrite existing version|
|forecasting.history / predict / backtest|Frame, SKU, cutoff -> daily history/predictions/error folds|Operational starter baselines; first-sale calendar; explicit insufficient history|
|research.features / forecast|Past values and dates -> recursive predictions|Fold-local Ridge or named baseline; unknown method/horizon fails|
|research.metrics / radius / select_products / evaluate|Arrays/frame -> metrics/calibration/selection/folds|Null percentage errors; development-only selection and all-method reporting|
|planning.Item / PlanRequest|JSON -> validated assumptions|Bounds, no nonfinite numbers, unique SKUs, no unknown fields|
|planning.allocate|Request and forecast totals -> greedy rows|Integer packs/budget/capacity, iteration cap and uncovered reasons|
|optimizer.optimize|Same -> static solver allocation|MILP status/gap; explicit feasible greedy fallback|
|simulation.Scenario / replay / compare|Scenario, data and policy -> daily log/comparison|Bounds, conservation, common sequences, paid pipeline and Pareto status|
|storage.digest / db / save_assumptions|JSON/SQL operations -> hash/transaction/version|Sorted finite JSON; rollback and guaranteed close; persisted assumptions immutable by hash|
|storage.challenge / confirm|Plan IDs/hashes/token -> preview challenge/receipt|Expired/reused/stale/tampered requests rejected under write lock|
|main.public_metadata|Full provenance -> screen-sized lineage summary|Preserves audit totals while retaining detailed original product dictionaries in local evidence|
|main app routes|HTTP requests -> structured JSON/export|Validation 422, missing 404, review conflict 409, readiness 503|
|assistant.get_plan / render / answer|Selected plan and question -> cited claims|One validated tool, bounded provider requests; no action tools, local fallback|
|static/index.html / workbench.js|API state -> accessible DOM workbench|Labelled controls, focus, responsive tables/chart, safe text rendering, visible errors|
|scripts.import_uci / prepare_real|Local source -> preview/version/real import evidence|Explicit quarantine and reproducible development subset; original snapshot retained|
|scripts.evaluate|Dataset/protocol -> JSON evidence|Exclusive final receipt, backup old outputs, hashes/versions/commands|
|scripts.browser_test|Isolated server -> workflow evidence/screenshots|Headless Windows browser; owns and terminates only its own process|
|tests/test_foundation.py / test_completion.py|Constructed inputs -> assertions|Preserve original test intent and add semantic negative/invariant tests|

## 5. Actual worked evidence

Open `artifacts/worked-proposal.json` and `artifacts/worked-example.md` when present. They retain a real saved demo proposal, exact product rows and independently calculated daily history/forecast totals. These are constructed demo data and assumed purchasing inputs, not a real business order. Recompute row spend = order_units*unit_cost_pence and compare against plan spend. Add uncovered targets and compare the assistant's cited units.

The saved demo development experiment predicts 734 recorded units over 70 product-days. Weekday mean AE=131.625 and WAPE=131.625/734=17.9326%; Ridge AE=146.9787557 and WAPE=20.0244%. Weekday mean's signed error is +38.125 units and its empirical interval covers 47/70=67.14%, below the nominal 80%. These exact values establish a baseline win and interval failure on this synthetic sample. See EVALUATION_REPORT.md for the real-data table, separate final results and policy outcomes. Do not substitute these demo values for real UCI findings.

Read every forecast/policy row before selecting a demo story. Compare a method's WAPE ranking to its replay cost and fill-rate ranking; use the same scenario and forecast family before attributing a difference to the allocator. Sensitivity changes one assumption at a time, retaining regimes that weaken the preferred result. No single metric proves the central research question universally.

## 6. Technology explanations

Python hosts validation, numerical models, solver and API, reducing deployment complexity. pandas supports tabular validation, groupby aggregation and explicit date reindexing; SQL stores versioned transactional decisions. A CSV is portable but has no transaction semantics, which is why registry publication uses staging. SQLite supplies atomic local writes without a separate server; BEGIN IMMEDIATE serialises competing reviewers before they read mutable receipt state.

FastAPI maps HTTP paths/methods to typed Python handlers. Pydantic validates request shape before business logic, returning 422 for invalid bounded inputs. A GET reads evidence; POST creates a proposal, changes a local selected dataset or records a review. The local APIs are unauthenticated and must remain on loopback. A 409 means current state conflicts with a requested review/version, rather than a malformed JSON body. A readiness endpoint checks data and database; liveness alone does not establish either.

The frontend uses native HTML/CSS/JavaScript to avoid a second build/server toolchain. State is selected product, assumption JSON, active proposal and review token. Fetch failures become visible status text. Source strings are placed with textContent and option/DOM APIs, never interpolated as unsafe HTML. Tables scroll on mobile; evidence panels have bounded height; SVG labels specify recorded units/dates. This is maintainable small-app scope, not a claim that a large React application has been built.

Scikit-learn pipelines encapsulate training-only transformations and regularised linear fitting. SciPy/HiGHS solves the small integer static coverage problem; a solver status is part of the evidence, not a cosmetic implementation detail. HTTPX supplies server-side Groq requests with timeouts. The adapter checks account model availability at /models, allows one get_plan tool call, validates its arguments, then requests allowed claim IDs. It permits at most two chat requests plus model discovery, no automatic retries, and never exposes filesystem/network/SQL/order tools to the model. A missing key is a working local mode with honest labeling, not simulated Groq output.

Dependency versions are in requirements.lock; this is a tested installed-version snapshot, not hashed wheel provenance or proof of clean installation on every system. CI defines Windows and Linux checks but is not remotely verified in this unpushed folder. Source content hashes stand in for a Git commit because the supplied directory has no Git history.

## 7. Trade-offs and contribution account

Rejected for this scope: random time-row splits, sale-price procurement costs, silent duplicate removal, retrospective stockout claims, a mandatory paid assistant, a second frontend server, and dynamic optimiser superiority claims. A simple baseline remains valuable if it wins. Atomic local manifests are sufficient for a small local tool; a multi-tenant deployment would need authentication, authorization, isolation, durable migrations and operational review.

The user supplied the project goals and foundation. The completion code, tests and learning material were AI-assisted/generated in this session. Do not claim that the owner independently designed, implemented or validated all of it. Before using resume bullets, the owner should reproduce the launch, trace one raw SKU to one saved decision, manually verify one forecast/error formula, demonstrate stale/concurrent review rejection, explain the negative model result and change a module while keeping relevant tests passing. Independent comprehension must be earned by reproduction, not inferred from possession of this folder.

The following answers describe current implementation, including its limitations. Interview practice should include explaining a failure and proposing a measured next experiment.

## 8. Interview cross-questions and answers

1. **Who makes the decision?** A purchasing manager reviews feasible SKU lots and their uncovered requirements in `main.plan`; the system saves proposals and local review receipts, not external orders.
2. **What is the central research question?** Whether forecast accuracy improves inventory decisions under common constraints. Compare `research.evaluate` to `simulation.compare`, not WAPE alone.
3. **Why cannot you claim realised savings?** Replay uses assumed stock/costs and recorded-sales proxies. There is no actual intervention, measured counterfactual or deployment outcome.
4. **Are sales demand?** They are observed transactions limited by unknown availability. DATA_CARD.md explicitly avoids recovering unobserved lost sales.
5. **Why exclude cancellations?** C-prefixed invoices are separately flagged in `data.validate`; blindly counting negative quantities as future demand or return arrivals misstates timing.
6. **Do identical rows get removed?** No. The duplicate audit flags repeated canonical lines because legitimate invoices can contain identical entries. Source audit retains their count.
7. **Why preserve raw snapshots?** They permit independent reinspection of transformation and quarantine. `registry.publish` stores local raw bytes and hashes, while the canonical frame drops customer fields.
8. **Does a checksum establish trustworthy data?** It establishes byte identity relative to a recorded hash. Incorrect or maliciously supplied source bytes can still match their own hash.
9. **What does quarantine mean?** Invalid required records are separated with reason codes by `registry.preview`; `--quarantine` explicitly permits publication of retained rows. Accounting is input=retained+rejected.
10. **Can reason counts sum above rejected rows?** Yes. One row can have both missing identifier and invalid date. `reason_codes` retains multiple causes; row accounting uses distinct rows.
11. **How is publication atomic?** All files are written in `.stage-UUID`, then the directory is renamed on the same filesystem. `datasets` ignores hidden staging directories.
12. **What does atomic publication not guarantee?** It does not make disk writes power-loss durable, prevent privileged file modification, or create a cross-host transactional registry. See ARCHITECTURE.md.
13. **How are products selected?** `select_products` ranks first-60-day sales volume, requiring entry by day 14, and returns up to five. Final-period performance does not select SKUs.
14. **Why is the subset biased?** It favors established higher-volume products. A conclusion on these SKUs may fail on rare, new, discontinued or seasonal products.
15. **Why exclude the latest day?** Source capture may end partway through it. Research conservatively uses max_date-1; it cannot verify the completeness of all other days.
16. **Why zero-fill missing days?** Baselines need a calendar series. `history` assumes zero recorded units after first sale; missing capture and closure remain unresolved alternatives.
17. **What happens to a new product?** Research raises an insufficient-history error below 28 days, rather than inventing a confident zero forecast. Operational starter minimum is 14 days.
18. **How does weekday mean differ from seasonal naive?** Weekday mean averages matching weekdays over 56 days; seasonal naive repeats the last observed week recursively. Both are in `research.forecast`.
19. **Why use Croston SBA?** It separates nonzero sale size and interarrival gaps for intermittent patterns. It remains an empirical sales baseline and can lose on regular demand.
20. **What makes Ridge ML here?** It fits coefficients to lagged training examples with regularisation in `research.forecast`. The mean and seasonal rules do not fit those coefficients.
21. **Why scale inside each fold?** Global means/scales would use later observations. StandardScaler is fitted with Ridge using only the history available at the current cutoff.
22. **What is recursive forecasting?** A predicted value is appended to the lag history for the next step. It avoids future actual lags but can compound forecast error.
23. **Which features are known in advance?** Calendar weekday is known, while future realised sales are not. The model uses past lags and a preceding seven-day mean only.
24. **How is leakage tested beyond code inspection?** Completion tests perturb future quantities dramatically and assert identical predictions for all methods, including the fold-local Ridge pipeline.
25. **What is WAPE's denominator?** Total actual recorded units across evaluated product-days. Demo development uses 734 units; numerator is absolute error, not average percentage error.
26. **Why return null for zero-demand WAPE?** Division by zero is undefined, even if predictions are perfect. `metrics` retains MAE, absolute error and signed error to describe behavior.
27. **What does positive signed error mean?** Sum(forecast-actual)>0 means aggregate overforecasting. Errors can cancel, so bias cannot replace absolute-error metrics.
28. **Why can global and mean SKU WAPE disagree?** Global WAPE weights large unit denominators more. Small products can dominate equal-weight per-SKU averages; zero denominators need explicit treatment.
29. **How are intervals calibrated?** `radius` takes a finite-sample adjusted quantile of absolute residuals from earlier calibration folds, separately by method/SKU.
30. **Is 80% coverage guaranteed?** No. Time dependence, sample size and distribution shift violate simple exchangeability assumptions. Demo weekday intervals cover 47/70, an explicit failure against nominal coverage.
31. **Why report interval width?** Broad intervals can obtain coverage with little decision value. `evaluate` records both covered observations and total width.
32. **What prevents final tuning?** `scripts.evaluate --final` requires a distinct output and exclusively creates a dataset receipt before accessing final metrics. Development runs do not evaluate final actuals.
33. **Can a user bypass the final guard?** A local file owner can delete receipts or inspect CSVs. It is a procedural accidental-rerun guard, not enforced secret holdout storage.
34. **Did ML win the demo?** No. Saved development WAPE is 20.02% for Ridge versus 17.93% for weekday mean. Retaining this loss is part of honest evaluation.
35. **Why not switch the live plan automatically to the final winner?** Final-based switching contaminates final assessment. The operational plan retains the interpretable weekday baseline; selection belongs to development.
36. **How is replenishment target formed?** Forecast lead-plus-review units, subtract physical and pipeline stock, clamp at zero and round to pack/MOQ constraints in `planning.allocate`.
37. **Why use integer pence?** Exact integer budget accounting avoids floating-point overspend. Display conversion to GBP happens after calculation.
38. **What if MOQ is not a pack multiple?** Minimum first order is ceil(MOQ/pack)*pack. For MOQ 6 and pack 4 it is 8 units, as tested in foundation tests.
39. **Can capacity include outstanding orders?** Yes. Both planning and replay reserve physical plus pipeline units; this is conservative aggregate capacity, not warehouse volume.
40. **What does greedy optimise?** Each step selects marginal priority-weighted covered units per penny. Local ratio choices do not guarantee the globally best combination.
41. **Give a greedy counterexample.** A(cost1,MOQ6,target6,priority1.1) and B(cost1,MOQ5,target10,priority1), with pack1, stock0 and budget/capacity10: greedy takes A6 then cannot buy B5, objective6.6; B10 yields10. Verify with `allocate` and `optimize`; costs are illustrative integer pence, not source prices.
42. **What is actually optimal in the MILP?** Weighted covered units for one static review with the stated integer-lot/budget/capacity constraints. `objective_covered_units`, status and gap report that narrow result.
43. **Why use binary activation variables?** They allow either zero order or at least the first MOQ-compliant pack count. Without activation, a linear minimum could force orders for every SKU.
44. **What happens on solver timeout or failure?** `optimize` returns feasible greedy output with explicit fallback and no optimality claim. The test mocks an unsuccessful solve; it is not evidence of observed production timeouts.
45. **How was optimiser correctness checked?** Tiny feasible combinations are enumerated and their best objective compared to SciPy MILP. This validates constructed cases, not every numerical/scale regime.
46. **Why may the MILP lose in replay cost?** Its static covered-unit objective omits dynamic holding, shortages, timing and salvage. Better static coverage does not imply lower total scenario cost.
47. **What is fixed policy?** A frozen initial order-up-to target reviewed weekly. Greedy/MILP refresh forecasts at review dates; this deliberate difference must be stated when interpreting comparisons.
48. **What is the simulator event order?** Cash grant, arrivals, proxy fulfilment/lost units, costs, review, paid orders and future arrivals. `replay` never allows same-day arrival.
49. **Why lost sales rather than backlog?** Recorded invoices do not reveal backorder demand. Explicit lost-sales semantics avoid silently carrying unobserved customer obligations into later days.
50. **How are returns handled?** They are not replayed. Cancellation/adjustment records remain audit evidence; their relation to original orders and return availability is unknown.
51. **How are policies made comparable?** They share SKU set, initial inventory, scenario seed, demand sequence and lead-time jitter. `exogenous_sha256` verifies the identical exogenous inputs per regime.
52. **Which conservation identities matter?** Initial+arrivals-fulfilled=physical stock; placed-arrived=pipeline; grants-purchases-order fees=cash. Daily assertions and tests verify these within constructed scenarios.
53. **Are holding and shortage charges cash commitments?** They are economic scenario penalties. They do not debit the procurement-grant balance; purchase and order fees do. DECISION_POLICY_CARD.md separates these ledgers.
54. **How do you treat terminal inventory?** Report physical and paid pipeline stock/value without a salvage credit. This makes horizon effects visible; it still affects policy cost ranking.
55. **What is fill rate here?** Fulfilled proxy units divided by all observed-sales proxy units. It is not the fraction of customer orders delivered on time and is null for zero proxy demand.
56. **What does Pareto mean?** A row is nondominated if no compared row has both no greater scenario cost and no greater unmet units, with one strict improvement. It does not identify a universally best policy.
57. **Why sensitivity analysis?** Procurement decisions depend heavily on assumed costs, budget, lead time and starting stock. `sensitivity` retains eight regimes, including synthetic volatility, without suppressing losses.
58. **What did the SQLite bug teach?** A SQLite connection's context manager commits or rolls back but does not close it. `storage.db` now closes explicitly, fixing Windows file-lock cleanup without weakening tests.
59. **How do concurrent retries avoid duplicate saves?** Idempotency-Key is bound to an input/dataset/policy fingerprint inside BEGIN IMMEDIATE. Same fingerprint returns one run; different inputs with the key return 409.
60. **How do concurrent approvals avoid duplicates?** Write locking, a primary key on review run_id, expiry checks and transactionally consumed tokens allow one receipt. The two-thread test expects one 200 and one 409.
61. **How does a review become stale?** Current data, latest persisted assumptions or expected snapshot hash changes. Expired/used tokens and tampered saved payloads also fail in `storage.confirm`.
62. **Is local confirmation authenticated approval?** No. It records a human review gesture on a loopback app with no identity assurance. A database owner can modify receipts; there is no tamper-proof audit claim.
63. **How is prompt injection constrained?** No source instructions can add tools. The provider has only validated get_plan and can select only enumerated claim IDs. Output values/citations come from deterministic saved fields.
64. **Why is numeric string matching insufficient?** A model can quote the right number with the wrong currency, sign or interpretation. This adapter renders typed fields in fixed semantic templates instead of approving arbitrary prose because digits match.
65. **What do Groq mocks establish?** Model discovery, tool validation, allowed claim selection, fallback and key non-disclosure behavior. They do not establish live answer relevance, availability, accuracy or cost.
66. **What happens without provider credentials?** `answer` emits an explicitly labelled local rules/no LLM summary. Missing credentials do not block importing, research, planning or review.
67. **Why not expose SQL to the assistant?** Arbitrary SQL can reveal/change records or bypass scope. get_plan accepts only the selected immutable run ID; no filesystem, network, import or order tools are model-accessible.
68. **How are frontend injection risks reduced?** Dynamic values use textContent/DOM APIs and CSV cells with dangerous spreadsheet prefixes are escaped. Tests are limited boundaries, not comprehensive security certification.
69. **How is provenance exported?** CSV rows include run, snapshot and dataset hashes; the self-contained report includes assumptions, provenance, policy results and limitations. A bare screenshot cannot replace the saved artifact.
70. **What should the owner claim personally?** The specification and any work they independently reproduce/modify. The contribution account states AI assistance; possession of generated code is not evidence of independent mastery.

## 9. Hands-on exercises with checks and solutions

Run from the directory containing README.md. Work in a copy when changing code. `python -m unittest discover -s tests -v` is the broad regression check; the targeted commands below help isolate the concept. Never remove a final receipt merely to practice rerunning a holdout.

1. **Trace one real saved demo decision.** Open `artifacts/worked-proposal.json`, select its first row, multiply quantity by unit_cost_pence and sum all row spends. Check that the sum equals spent_pence and budget minus spend equals remaining_budget_pence. Solution: the worked-example artifact prints the source dates, forecast sum, target and allocation; compare to `main.plan` and `planning.allocate`. Test: `python -m unittest discover -s tests -p test_foundation.py -v` includes snapshot persistence and arithmetic invariants.
2. **Prove future leakage is absent.** In a scratch script load the demo, choose cutoff=max_date-20, multiply all later quantities by 10,000 and compare all five seven-day forecasts. Solution: outputs must be identical because history and fold fitting stop at cutoff. Check: `python -m unittest discover -s tests -p test_completion.py -k ignore_future -v`.
3. **Recompute WAPE manually.** Add actual and predicted errors from all weekday_mean rows in development.json. Solution: sum AE / sum actual = 131.625/734 on the demo; MAE divides by 70 product-days. Check also signed bias=38.125, and compare against the saved summary. Changing denominator to the number of SKUs is incorrect.
4. **Handle a zero denominator.** Call `metrics([0,0],[1,2])`. Solution: wape=None, absolute_error=3, mae=1.5, signed_error=3. Add a negative-bias case to a scratch test and explain why percentage error remains undefined. Check: completion test `zero_denominator`.
5. **Create a quarantined CSV.** Copy two canonical rows, replace one's date with 'bad' and add a CustomerID column. Run importer --preview, then publish only with --quarantine into a temporary registry. Solution: input2=retained1+rejected1, invalid_date reason, no customer field in canonical/rejected files; original snapshot remains local. Check: `-k csv_roundtrip` and `-k private_fields` completion tests.
6. **Show the first MOQ-compliant lot.** Use Item(sku='A',unit_cost_pence=125,on_hand=0,pack=4,moq=6). With budget=1000 and target20, first order is8 and costs1000. Solution: ceil(6/4)*4=8; budget999 produces zero. Check: foundation `budget_and_capacity`; add the 999 edge manually without weakening original assertions.
7. **Construct a greedy loss.** Use the valid A/B example in question41. Solution: greedy buys A6, objective6.6; MILP buys B10, objective10 under ten units/pence capacity/budget. Verify objective=sum(priority*min(order_units,target gap)), not total unweighted order units. Check: `-k bruteforce`; extend its enumeration to this example.
8. **Demonstrate arrival timing.** Replay SKU-001 for three days with initial_stock0, lead_days2 and daily proxy5. Solution: first two days fulfil0; any first arrival is day index2 or3 due common jitter. Read orders' arrival indexes and check terminal stock/pipeline. Check: completion `arrival_conservation_and_terminal`.
9. **Reconcile cash and cost.** From one replay row, subtract purchase and order fees from grants; separately sum purchase+ordering+holding+shortfall. Solution: first equals cash_remaining, second equals scenario_cost. Holding penalties are not procurement cash debits. Check: replay log assertions; vary shortfall_pence and observe cash stays unchanged for policies whose allocation ignores the penalty.
10. **Reject stale and duplicate review.** Create a proposal, preview it, save different assumptions and attempt confirmation; then create/preview a fresh one and issue two identical confirmations concurrently. Solution: stale request409; concurrent fresh results200/409. Check: completion `stale_assumptions`, `concurrent_confirmation` and `concurrent_idempotent_save`.
11. **Attack assistant scope safely.** Ask it to execute SQL, invent negative dollar costs or use another run ID. Solution: no action tools exist; offline rendering stays in GBP with the actual record hash, and `get_plan` rejects contradictory IDs. Mock provider429 to see local fallback. Check: completion `prompt_injection`, `contradictory_records`, `provider_rate_limit`.
12. **Evaluate interval failure honestly.** Divide covered by interval_observations in the weekday demo summary, then compare width to recent mean. Solution: 47/70 is67.14%, below80%; the narrower width is not a guaranteed improvement. Propose a new protocol version with longer calibration and assess on new development periods; do not tune based on an already inspected final result. Check: completion `uncertainty_edges`.
13. **Run a complete browser flow.** Execute `python -m scripts.browser_test` with Edge installed, or set STOCKFLOW_BROWSER=chromium after installing its binary. Solution: browser.json lists selection, quality, chart, proposal, policy comparison, review, history, assistant, validation and mobile checks, with zero JavaScript errors. Inspect desktop/mobile PNGs. A test process starts an isolated database and owns its own server cleanup.
14. **Explain a policy loss.** Select two comparison rows under one scenario, inspect daily stock, unmet units and terminal pipeline, then alter shortfall_pence in a scratch scenario. Solution: costs can reorder without any forecast changing because the objective and cost ratio differ. Preserve both rows, common exogenous hash, seed and assumptions; do not describe the difference as causal financial savings.

## 10. Personal mastery checkpoint

Independently reproduce launch and tests; manually calculate one forecast, uncertainty quantile, pack/MOQ target and budget-feasible allocation; show a greedy counterexample; explain a real method loss; demonstrate stale/concurrent review rejection; modify a model or policy with a new protocol and meaningful tests. Record which tasks you completed yourself. Resume wording in RESUME_EVIDENCE.md is conditional on your ability to demonstrate and explain the system, and must retain its AI-assisted provenance when asked.

Final real-period follow-up: seasonal naive WAPE=70.59%, Ridge=81.58% over 2,132 recorded units/35 product-days. This reverses the development ranking and was not used to retune. Read the full final table in EVALUATION_REPORT.md.

## 11. SQL and statistical extension (2026-11-21)

The role-alignment work added app/analytics.py, app/statistics.py and the build_analytics, robustness and report_robustness scripts. Read ROLE_ALIGNMENT.md, ANALYTICS_QUERIES.sql, EXPLORATORY_PROTOCOL_V2.md and RESEARCH_EXTENSION_REPORT.md alongside this section. The original final period was preserved; the new analysis is explicitly exploratory because it was specified after the original final result was known.

### Additional interview questions

71. **Why add a separate analytics mart?** Proposal storage answers “what decision was saved?” The mart answers “what recorded sales and source-quality evidence support analysis?” Its transaction, product and daily tables make SQL skills and reconciliation inspectable without mixing assumed procurement data with observed sales.
72. **What is its grain?** fact_transaction has one canonical-row ordinal per source/cutoff run; dim_product has one positive-sale product per run; fact_daily_sales has one calendar day per product after first sale. Canonical ordinals are not original Excel row numbers.
73. **What ensures idempotent ETL?** A unique dataset-hash/cutoff identity and BEGIN IMMEDIATE serialize concurrent loads. Repeating the same verified source/cutoff returns the existing run instead of duplicating facts.
74. **Where does rollback apply?** All run, dimension, line-fact and daily-fact writes commit together after reconciliation. A constructed failing trigger demonstrates that an interrupted load leaves no partial run/facts. Schema creation may remain; incomplete data does not.
75. **What is reconciled?** Loaded line count equals Python's cutoff-filtered rows; positive-sale quantity sum equals Python's independently computed sum; daily-calendar quantity sum equals the SQL line sum. The real development subset has 13,287 loaded canonical lines and 306,947 recorded positive-sale units.
76. **Why does ROWS mean days here?** The mart explicitly materializes the calendar after first sale. Without those zero-filled rows, seven preceding rows could be seven irregular sale days rather than seven calendar days.
77. **Why end the window at 1 PRECEDING?** The target day's actual sales must not enter its lag feature. A fixture with day-eight value 8 expects the preceding sum 1+...+7=28, excluding8.
78. **What does ABC classify?** First-sixty-day recorded unit volume within the selected subset. It is not full-catalogue importance, observed margin, procurement priority or a profitability label.
79. **Why are source million-row counts different from SQL counts?** The official importer audited the full workbook; research and SQL intentionally use five development-selected products and exclude later dates. A million-row SQL performance claim would be false.
80. **Why extend evaluation across thirteen weeks?** The original final had only 35 product-days. More historical folds reveal ranking instability, but because the extension followed final inspection, they are exploratory and do not create a new independent confirmation.
81. **What is a paired comparison?** Every alternative and baseline uses identical SKU/cutoff keys, actual vectors, target dates and observation counts. Missing, duplicate or contradictory pairs are rejected before resampling.
82. **Why resample weeks jointly across products?** Product sales can move together and days within a week can depend on one another. Sampling individual product-day errors would exaggerate independent information. Weekly blocks preserve those relationships within each selected block.
83. **Why circular blocks and length sensitivity?** Fixed-length consecutive-week blocks wrap at the ends so starts are equally eligible; wrap-around is artificial. Length1/2/3 sensitivity exposes the impact of dependence assumptions instead of selecting a favorable interval.
84. **How is a WAPE bootstrap replicate calculated?** Resample the paired blocks, sum each method's absolute errors and the resampled actual denominator, then compute100*(alternative_AE-baseline_AE)/actual_units. It is a ratio of resampled totals, not an average of per-row percentage errors.
85. **How do the original final and wider exploratory findings differ?** Seasonal naive won the original seven-day final. The thirteen-week exploratory comparison favors weekday mean over Ridge. Different periods and post-final exploration limit generalisation; neither licenses hidden retuning or a claim of universal superiority.
86. **What do five seeds establish?** Limited sensitivity to shared lead-time jitter under the same observed-sales proxy, starting stock and costs. They are not five independent retailer histories or proof of causal savings. Fairness checks reject changed assumptions within or across the paired design.

### Additional independent exercises with solutions

15. **Run and reconcile SQL.** Build a temporary mart with `python -m scripts.build_analytics --data <canonical CSV> --database <new DB> --output <new JSON>`. Execute the first query in ANALYTICS_QUERIES.sql using its run_id. Solution: expected/actual row counts and Python/SQL unit totals match. The real saved evidence is real-analytics-v2.json. Tests: `python -m unittest discover -s tests -p test_analytics_research.py -k reconciles -v`.
16. **Test transactional failure and concurrency.** Run `-k midload_failure` and `-k concurrent_loads` in the extension test file. Solution: a failing insert leaves all four data tables empty; two concurrent successful loads produce one created version and one existing version. Explain why schema existence is different from partially published data.
17. **Prove a lag excludes its target.** Inspect the preceding-window fixture query. Solution: day-eight sales8, lag sum28. Change the window end to CURRENT ROW in a scratch query and observe36. Explain why the schema needs an explicit calendar before interpreting seven rows as seven days. Test: `-k preceding_window`.
18. **Reject unfair paired inference.** Remove one product/fold or change one method's actual vector in a copy of the paired_rows fixture. Solution: paired_block_comparison raises ValueError rather than silently comparing different cohorts. Test: `-k unpaired_duplicate`.
19. **Derive a resampling effect.** The synthetic fixture has baseline prediction2 and alternative1 with actual1 every day. Solution: baseline WAPE 100%, alternative 0%, difference−100 percentage points; constant blocks produce interval[−100,−100]. With all actuals 0, WAPE stays undefined in every replicate while MAE differences remain defined. Tests: `-k constant_effect`, `-k zero_denominator`.
20. **Explain the strongest finding without exaggeration.** From exploratory-robustness.json compute1−weekday_AE/Ridge_AE. Solution: about 16.24% less absolute error on 32,660 recorded units, 455 product-days and 13 historical weekly folds. State post-final exploratory status, the five-product selection bias and unchanged original final. Then contrast it with the earlier seasonal-naive final win and explain why neither result proves general superiority.

## Broader product coverage and seasonal MASE

app/coverage.py defines deterministic volume/sparsity sampling and product/segment evaluation. scripts/prepare_coverage.py publishes selection before evaluating it. The initial v3 sample included manual code M; the original workbook's description was verified as Manual. That sample remains preserved, and protocol v3a excludes manual/service-like identifiers using a declared five-digit-plus-suffix heuristic before any new-cohort outcomes were measured. This remains an imperfect semantic eligibility rule.

The amended cohort has 40 new products, excluding the original five, selected from 2,673 eligible candidates. Five strata contain eight products each; low-volume/dense has none under the declared definition. The resulting 13-fold study has 3,640 product-days and 10,417 recorded units per method. Failures are retained; incomplete method/product coverage blocks paired inference. Existing forecast algorithms and settings are unchanged.

Seasonal MASE divides product-fold MAE by mean absolute seven-day training differences; zero scales are undefined. It weights defined product-folds equally and does not replace unit-weighted WAPE. In this actual cohort weekday mean has mean MASE around 0.779 but WAPE around 127.95%. That discrepancy is interpretable weighting/scaling, not a reason to suppress the worse metric. Always-zero forecasts have 100% WAPE for positive nonnegative actual totals; that post-hoc arithmetic diagnostic beats every tested method on this cohort. It is not an appropriate purchasing policy by itself, because decision costs and service risks differ from absolute prediction error.

Personal exercise 21: reproduce a single product's seasonal scaling denominator from training dates only, then alter future records and verify the scale/prediction stays fixed. Explain why the product's WAPE can be undefined while its MAE or MASE is defined. Relevant tests: test_coverage_release.py seasonal-scale and final-actual perturbation cases.

Personal exercise 22: compare the old five-product report with all forty new product/segment rows in COVERAGE_AND_RELEASE_REPORT.md. Identify a method/segment loss and show why “weekday beats Ridge everywhere” would be false. Do not mix cohorts or denominators.

Personal exercise 23: run `python -m scripts.verify_release --require-isolated --browser` using the isolated interpreter. Read the actual timestamped report, dependency consistency output and browser checks. Demonstrate that a failed command cannot be reported as passed and that using global Python cannot claim isolated acceptance. Review the normal launcher dependency probing and its printed interpreter choice.
