# `healing/adapters/` — placeholder, intentionally documented

Status: **empty placeholder, do not delete.**

`healing/adapters/__init__.py` is imported by `tests/test_adapters.py`, and
the package is the agreed home for UI/API runner adapters. There is no
runner ingestion code yet; the pipeline is currently driven by the
benchmark harness (`benchmark/harness.py`, `scripts/bench_*.py`).

## What belongs here

Adapters should normalize failures from real test runners into the
framework's inputs without changing their semantics:

- UI: pytest/Selenium failures → `FailureSignals` (error message, DOM
  snapshot, screenshot delta, network status) plus the page URL.
- API: pytest/httpx/Pact failures → `ApiFailure` (status, error,
  spec/breaking/approved/rename flags, auth/data freshness, Pact flag).
- Shared: runner metadata (test id, build, environment, retry count) for
  alerts and explanation records.

## Contract to preserve

- Adapters only **detect and normalize**; classification, matching,
  policy, and Git operations stay deterministic and outside this package.
- Unknown or malformed runner output must fail closed (escalate), never
  guess a heal.
- No secrets in logs; mask PII before any external call.
- Tests must accompany the first real adapter.

The contract is currently pinned by `tests/test_adapters.py`. Replace the
placeholder when a real runner integration is implemented; do not remove
the package while that test imports it.
