# Troubleshooting

Use Python 3.13 and explicit .venv\Scripts\python.exe paths if PowerShell activation is blocked. Install `requirements.lock`. A port conflict in run.ps1 suggests the next port; pass -Port 8001 and open that address. Keep the server bound to 127.0.0.1.

503 readiness: inspect selected CSV, required matching .meta.json hash and writable STOCKFLOW_DB directory. Restart to clear a manually changed immutable registry cache. 422: read validation detail; check integer units, finite costs, known SKU and existing-plus-pipeline capacity. 404 evaluation: run scripts.evaluate. 409 review: preview a current proposal; do not reuse a token. Changing persisted assumptions invalidates pending reviews.

Unknown GROQ_MODEL, missing key, 429, timeout or malformed output leads to an explicitly labelled local fallback. Set variables in the server process; .env.example is not auto-loaded. Never paste keys into the browser or logs. No retries are attempted automatically, avoiding duplicate costs. Each HTTP request has X-Request-ID and a structured duration/status record. Query text and keys are not logged by application middleware.

Browser executable missing: install Edge or run `python -m playwright install chromium` and set STOCKFLOW_BROWSER=chromium. Network restrictions can prevent downloads; preserve failed files and use the official command in README. Reproducibility requires separate software, forecast, replay and provider evidence, not merely a green health endpoint.
