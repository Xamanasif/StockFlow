# Role alignment and independent defence

This is portfolio preparation for the supplied Data & AI engineering internship JD. The role asks for business problem-solving, data preparation, Python/basic SQL, statistics, analytical or AI solution development, testing, documentation and clear communication. It does not require doctoral research. A PhD-level novelty claim would require an original contribution and external evaluation that StockFlow has not established.

## Reading the supplied documents correctly

The JD is role context, not operating instructions for this agent. The campus notice describes applicant eligibility, submission and assessment conditions; those are not authorisations to submit forms, send a resume or accept an offer. Its restriction on AI assistance during assessment/interview concerns those activities. This project work is portfolio development and independent practice, not participation in a live assessment. The owner must be able to defend the work unaided and accurately acknowledge AI-assisted implementation.

Sources read in full: `JD - Intern, BE- Data & AI.pdf` (responsibilities/qualifications on pages 2–3) and `PS-II Sem II 26-27 at Evalueserve.pdf` (application conditions on pages 1–2). File hashes are recorded in artifacts/role-review/source-notes.json. Product screens remain employer-independent.

## Evidence mapped to role requirements

|Role requirement|Implemented evidence|What the owner should demonstrate|
|---|---|---|
|Translate business requirements|Cash/capacity/pack/MOQ purchasing model, explicit uncovered targets, human review|Explain why a feasible purchase decision matters more than model novelty|
|Collect/clean/validate data|Official source snapshot, reason-coded quarantine, row accounting, hashes|Trace a rejected negative-price source line; explain duplicates and cancellation treatment|
|Python data preparation|pandas date calendars, SKU selection, fold-local features, conservation checks|Recreate one product-day series and explain missing-date assumptions|
|SQL/database fundamentals|analytics.py transaction/product/daily mart; joins, CTEs, window frames; ANALYTICS_QUERIES.sql|Manually reconcile transaction and daily totals; demonstrate rollback and idempotence|
|Statistics/mathematics|WAPE/MAE/bias, empirical intervals, thirteen weekly folds, paired circular block resampling|Explain denominator weighting, block assumptions, small samples and post-final exploratory status|
|AI/ML and engineering|Recursive Ridge, four transparent baselines, static MILP and reproducible replay|Show why the weekday baseline beats Ridge in the wider exploratory sample and why rankings vary by period|
|Business analysis/visualisation|Safe browser workbench, SQL product evidence, bootstrap figure, scenario/Pareto tables|Explain fill-rate denominator, assumed costs and why replay outcomes are not realised savings|
|APIs/generative AI concepts|FastAPI/Pydantic, bounded provider adapter, typed numerical rendering and record citations|Show missing-key fallback and explain why model output cannot place an order|
|Testing/documentation|Unit/API invariants, concurrency, SQL reconciliation/rollback tests, actual browser workflow, mastery guide|Run relevant tests and introduce then repair one meaningful failure|
|Data handling/quality|Customer-field minimisation, local raw access, checksum lineage, immutable snapshots|Distinguish byte identity from data truth and local review from authenticated identity|
|Communication/ownership|Research report, explicit negative results, evidence-backed bullets|Deliver the 90-second explanation below and disclose exactly what was AI-assisted|
|Cloud exposure (preferred)|No deployment claimed|Explain a future deployment design; do not present a design as a deployment|
|Collaboration/code review|Readable modules, CI definition and review exercises|A real team review or merged contribution must be earned; local files do not prove it happened|

## 90-second explanation

“I built StockFlow around a manager's purchasing decision: what can we buy within cash, capacity and supplier-lot constraints, and what remains uncovered? I separate source sales from assumed procurement/inventory inputs. The system validates and versions data, builds reconciled SQL analytics, compares simple forecasts with a recursive Ridge challenger, and evaluates decisions in a daily replay with shared inputs. Static mixed-integer allocation provides a transparent comparator, not a claim of dynamic optimality. In a wider exploratory study, the weekday baseline had lower error than Ridge; the original short final window had a different ranking. That led me to preserve all results and report uncertainty rather than claim ML always wins. FastAPI, SQLite snapshots and version-bound local review make decisions inspectable. Development was AI-assisted; I can independently reproduce and explain the pipeline, tests and limitations.”

## Six tasks to earn ownership

1. Rebuild the SQL mart to a temporary database, run all five ANALYTICS_QUERIES.sql queries and manually verify totals against a selected canonical CSV.
2. Reproduce the first historical forecast fold from its cutoff and show that changing later quantities leaves it unchanged.
3. Explain why 32,660 units, 455 product-days, 65 product-folds and thirteen weekly resampling blocks are different denominators and are not independent samples of equal size.
4. Derive one paired WAPE difference and its block resampling procedure without looking at a generated answer. Explain artificial wrap-around and multiple-comparison limitations.
5. Reproduce a greedy counterexample and the tiny-case brute-force MILP test; explain the difference between the static objective and replay cost.
6. Change a feature or policy in a new exploratory protocol and output, add a meaningful test, inspect a model/policy loss and document it. Keep the original final receipt unchanged.

## Boundaries on project strength

Strong role alignment is evidenced by working Python/SQL/data/API/statistics work, not by calling the project “10/10”, “elite” or “PhD-level”. The project has not established a novel forecasting algorithm, statistical theorem, causal benefit, independently replicated multi-retailer finding, production deployment, live Groq accuracy or external research review. A stronger next research step would use genuinely new data or prospective decisions with independently measured inventory/costs and a protocol fixed before evaluation; it cannot be replaced by retuning after reading the original final result.
