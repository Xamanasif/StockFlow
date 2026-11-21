# Demo walkthrough

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
