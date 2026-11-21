# Known limitations and unverified paths

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

Exploratory extension: the thirteen-week historical study and SQL analytics now use separate fixed queries and bounded reports. New rows do not update existing decisions or retune the original models. Statistical block resampling, extra scenario seeds and broader temporal coverage improve evidence depth; they do not establish independent replication, model novelty or a causal business result. See RESEARCH_EXTENSION_REPORT.md and ROLE_ALIGNMENT.md.

## Updated boundaries after coverage extension

The forty-product v3a cohort broadens cross-product evidence but still comes from the same retailer; it is not independent external replication. The initial five-product finding cannot be generalised to it. All five frozen methods exceed 100% WAPE on the broader cohort, so portfolio-wide forecast suitability is not established. Seasonal MASE below 1 does not erase that finding. Sampling uses an item-identifier heuristic and equal stratum quotas, not verified supplier catalogue eligibility or population weights. The one low-volume/dense empty stratum is retained.

A clean isolated installation and actual Windows verification are now evidenced separately under artifacts/releases/ and acceptance-v3.json; the earlier statement that no clean installation was exercised refers to the original build. Remote CI, other OS execution, external users, cloud deployment, live Groq accuracy, real procurement costs, causal savings and independent owner mastery remain unverified.
