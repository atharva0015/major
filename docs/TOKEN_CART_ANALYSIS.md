# `heldout:token-cart` analysis (2026-11-04)

Status: **root cause identified; no code changed; proposed fix needs human
approval.**

## The miss

`heldout:token-cart` is the single API miss in the held-out run:
expected `expired_credential` / heal, observed `unapproved_change` /
escalate (`benchmark/reports/heldout.json`, `ui`/`api` report in
`docs/HELDOUT.md`). The case still **fails closed**: nothing was healed,
no contract was touched, and the test result is an escalation.

## Reproduction probe

Command output saved at
`reports/evidence/2026-11-04/token_cart_probe.txt`.

```text
observe() -> ApiFailure(status=500, error='unknown endpoint GET /api/cart',
    spec_changed=False, breaking=False, approved=False, rename_only=False,
    auth_ok=True, data_fresh=True, pact=False)
classify(observe()) -> ApiClassification(api_class='unapproved_change',
    fired_rules=('spec_unchanged_likely_defect',), healable=False)

direct api_cart() -> 401 'token expired'
classify(direct 401) -> ApiClassification(api_class='expired_credential',
    fired_rules=('auth_401_spec_unchanged',), healable=True)
```

The real endpoint behaves exactly as the label expects. The pipeline never
asks it.

## Root cause

`healing/nonui/pipeline.py::observe()` hard-codes three endpoints:

```text
GET /api/products
POST /api/cart
POST /api/checkout
```

`GET /api/cart` is not one of them, so `observe()` returns a synthetic
`ApiFailure(500, "unknown endpoint GET /api/cart", ...)` with every flag at
its default. `classify_api()` then applies its last-resort rule:
spec unchanged, no breaking diff, data fresh, no auth marker →
`unapproved_change` / not healable. `heal_api_case()` escalates before the
healer, Critic, or policy gate is reached.

The label is **not** the cause. The observer's endpoint coverage is. The
earlier note in `docs/HELDOUT.md` that "the cause is in my label" is
superseded by this probe.

## Which component failed

| Component | Verdict |
|---|---|
| Observer (`healing/nonui/pipeline.py::observe`) | **FAILED** — missing dispatch for `GET /api/cart`; returns a synthetic 500 instead of the real 401 |
| API classifier (`healing/nonui/classifier.py`) | Correct on the input it received; the last-resort rule is behaving as designed |
| Healer (`healing/nonui/healers.py`) | Never invoked; no wrong action taken |
| Critic | Not involved on the API path; no safety failure |
| Policy gate | Not involved; the API path escalates on `healable=False` |

## General fix vs case-specific fix

A general fix exists. Both parts should be treated as one proposal.

1. **General observation** — replace the hard-coded endpoint chain with a
   registry or a `fastapi.testclient.TestClient` call keyed by
   `case.endpoint`, so new endpoints do not silently become "unknown".
   This is the durable fix and would also cover future held-out cases.
2. **Distinguish observer gaps from API defects** — add an
   `observer_error` / `unknown_endpoint` field to `ApiFailure` and make
   `classify_api()` escalate with that explicit reason. Today an observer
   bug is misreported as an `unapproved_change`, which is misleading even
   though it is safe.

A one-line case-specific fix (`elif case.endpoint == "GET /api/cart":
payload = app_module.api_cart()`) would make this case pass, but it leaves
the same trap for every future endpoint. It is **not recommended** as the
only change.

## Proposed change (needs human approval)

- **Needs human approval:** yes.
- **Files that would change:** `healing/nonui/pipeline.py`,
  `healing/nonui/classifier.py`, `tests/test_api_e2e.py` /
  `tests/test_api_classifier.py`.
- **Safety constraints:** keep contract changes and Pact failures
  escalating; do not auto-heal any newly covered endpoint; preserve the
  existing env save/restore behavior; add no network calls beyond the
  in-process demo app.
- **Acceptance:** held-out API returns **11/11**, and the unknown-endpoint
  signal is a distinct escalation reason rather than `unapproved_change`.

## Fresh cases needed to test the fix

Add these before changing code, and label them before the first run:

| New case | Expected class/action | Why |
|---|---|---|
| `GET /api/cart` + `expired_token` | `expired_credential` / heal | Exact regression for this bug; real endpoint returns 401 `token expired` |
| `GET /api/cart` + `none` | no failure / no heal | Proves the observer calls the real endpoint and gets 200 |
| `GET /api/cart` + `stale_seed` | `unapproved_change` / escalate | Preserves the existing label; currently passes for the wrong "unknown endpoint" reason |
| `GET /api/cart` + `expired_token` + `renamed_field` | `contract_change` / escalate | Auth plus spec change must outrank `expired_credential` |
| `GET /api/does-not-exist` | explicit observer-gap escalation (new reason) | Proves unknown endpoints are no longer mislabeled as API defects |
| `POST /api/cart` + `expired_token` | `expired_credential` / heal | Existing covered path; guards against regression in the general dispatch |
| `POST /api/checkout` + `stale_seed` | existing expected class | Existing covered path; guards against regression |

Do not tick any sign-off box for this proposal; a human owner must approve
the change and the refreshed held-out rerun.
