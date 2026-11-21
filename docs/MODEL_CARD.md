# Forecast model card

Task: predict nonnegative daily recorded units for a selected SKU. `forecasting.py` preserves the starter operational weekday and recent-mean baselines and 14-day minimum. `research.py` imposes a 28-day since-first-sale minimum, with explicit failures. Unknown products fail rather than silently becoming zero-demand products.

Research methods: recent 28-day mean; weekday means over 56 days; last-week seasonal naive; Croston SBA with alpha=.1 and correction .95; Ridge alpha=10 with fold-local StandardScaler. Ridge features are preceding lag 1/7/14, preceding seven-day average, and known weekday. Multi-step forecasts append predicted values so future lags never use realised future sales. It is a linear ML challenger, not a demand-censoring model.

`EVALUATION_PROTOCOL.md` predates the saved experiments in this build. Its hash is in every research artifact. No random row splits or final-period product selection. Prior residuals calibrate empirical 80% intervals; chronological dependence and small samples undermine nominal guarantees. Report coverage and width together, including undercoverage. Calibration is not fitted on evaluation actuals.

Operational plans keep the interpretable weekday baseline. Development candidates are ranked by WAPE, while the operational proposal deliberately retains its transparent weekday baseline; no final-based switching. Review `EVALUATION_REPORT.md` before claiming any accuracy advantage. Seasonal change, closures, incomplete source capture, intermittent/new products, outliers and wholesale baskets limit transferability. Sales are censored by unknown availability; these models do not recover unconstrained demand.
