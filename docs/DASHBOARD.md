# Read-only dashboard

`healing/dashboard/app.py` serves a local page showing:

- quality gates from `docs/TARGETS.md` and the report JSON files;
- the newest explanation records from the JSONL store;
- the latest saved Prometheus metrics transcript.

It is a viewer, not an operator console. It cannot heal, approve, revert,
open a PR, or write a file.

## Start

```powershell
.venv312/Scripts/python -m healing.dashboard.app
```

Or:

```powershell
.venv312/Scripts/python tasks.py dashboard
```

Open <http://127.0.0.1:8080>. Override the bind address or port with
`DASHBOARD_HOST` and `DASHBOARD_PORT`; keep the host on localhost unless
you put an authenticated proxy in front.

## Routes

| Route | Purpose |
|---|---|
| `GET /` | HTML dashboard |
| `GET /api/summary` | The same data as JSON |
| `GET /healthz` | Liveness and read-only flag |

There are no POST, PUT, PATCH, or DELETE routes. FastAPI docs endpoints are
disabled.

## Data sources

| Section | Source | Notes |
|---|---|---|
| Gates | `docs/TARGETS.md` + `benchmark/reports/*.json` | Recomputed with `scripts.check_gates.evaluate()`, including the alert subgate; cached for 30 seconds |
| Records | `RECORDS_PATH` (default `benchmark/reports/records.jsonl`) | Newest `DASHBOARD_RECORD_LIMIT` records (default 25, maximum 100); malformed lines are skipped and counted |
| Metrics | `DASHBOARD_METRICS_PATH`, or the newest `reports/evidence/*/quality_snapshot.json` | Displays the saved `metrics.prometheus_text`; it does **not** scrape a live process |

Every record is hash-checked with `verify_hash()` before display. A
mismatch is shown as a failure, not hidden.

## Safety properties

- **GET-only**: no route mutates state.
- **Masked and escaped**: displayed record text passes through
  `mask_pii()` and `html.escape()`, so PII is masked and HTML is inert.
- **Fail-closed display**: missing files, malformed records, and gate
  errors produce visible warnings or `UNVERIFIED` rows; the page does not
  invent success.
- **Localhost by default**: bind address is `127.0.0.1`.
- **Security headers**: `nosniff`, `no-referrer`, and a restrictive
  Content-Security-Policy.
- **No secrets**: credentials are never read or rendered.

## Limits

- The metrics section is a **saved snapshot**, not live monitoring.
- Gates are cached for 30 seconds and may lag a fresh report write.
- Records have no timestamp field; the page shows append order.
- There is no login, user management, or remote access control.
- This is not a replacement for Prometheus/Grafana, which remain
  undeployed (`TODO.md` P2.2).

## Evidence

- `tests/test_dashboard.py` covers data loading, masking/escaping,
  fail-closed display, GET-only routes, and the JSON summary.
- `tests/test_check_gates.py` covers the structured `evaluate()` path used
  by the dashboard.
- `reports/evidence/2026-11-06/dashboard.jpeg` is a browser screenshot;
  `dashboard_summary.json`, `dashboard.html`, and `dashboard.txt` are the
  captured page, API summary, and transcript.
