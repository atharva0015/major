# Project status (regenerated 2026-11-06)

Snapshot: branch `chore/baseline`, after the 2026-11-04 evidence audit, the
2026-11-05 live-golden derivation, and the 2026-11-06 gate measurement
correction approved by the project owner (HEAD moves with the evidence
commit).

Labels: **MEASURED** = observed from a real run in a recorded session.
**SIMULATED** = produced by the Healenium simulator or in-process replay,
not the live stack. **UNVERIFIED** = not observed here (needs CI, Docker
rerun, or a missing input).

## Summary

The healing pipeline is implemented end-to-end: classify → match →
sandbox replay → layered Critic → policy gate → explanation record →
alert / shadow PR, with an API sidecar, a read-only local dashboard, and
quality tooling. **MEASURED this session (2026-11-06, Python 3.12.10):
204 tests pass; lint and mypy are clean; the 24-case demo matches 24/24;
gates report 11 PASS, 0 FAIL, 1 UNVERIFIED (normal mode exit 0; strict
mode exit 1 on the survival gate).** The 2026-11-06 measurement correction
was explicitly approved by the project owner: the adversarial gate now
measures the shipped orchestrator path (0.0, all 9 cases escalate), and the
latency gate measures pipeline overhead (19.99 ms). The raw matcher's 9/9
adversarial heals and the 1122 ms browser time remain visible as
non-gating diagnostics; no report value or threshold was changed.

The held-out set now exists and was measured (previous status said it was
absent): UI 24/24 correct with 0 false heals; API 10/11, with one
documented label/coverage miss that fails closed. `heal_accuracy [live]`
now **PASSES** at 1.0, but from `golden_live.json` derived from the
historical 2026-10-08 live E2E report; the stack was not re-run. Survival
remains UNVERIFIED by design (no history).

## Verification this session (MEASURED 2026-11-06)

| Check | Result |
|---|---|
| `pytest -q` | 204 passed in 24.96 s |
| `ruff check .` | clean |
| `ruff format --check .` | 177 files already formatted |
| `mypy healing` | no issues in 52 source files |
| `python tasks.py demo` | 24/24 cases match, exit 0 |
| `python -m scripts.bench_demo_cases` | 24/24, 0 false heals, 0 wrong escalations |
| `python tasks.py evidence-snapshot` | in-process quality transcript, exit 0 |
| `python tasks.py dashboard` | local read-only page, HTTP 200; 11/0/1 plus diagnostics; screenshot saved |
| `python -m scripts.bench_golden_live` | 24 cases, heal_accuracy 1.0 |
| `python -m scripts.check_gates` | 11 PASS / 0 FAIL / 1 UNVERIFIED, exit 0 |
| `python -m scripts.check_gates --strict` | same gate counts, exit 1 on the UNVERIFIED survival gate |

Environment: Windows host, project venv `.venv312` (Python 3.12.10).
`make` is absent on this host, so Makefile-equivalent commands were run
directly. GitHub Actions results were not observed from here.

## Gate table (fresh `check_gates` run, MEASURED this session)

| Gate | Target | Value | Status |
|---|---|---|---|
| heal_accuracy | >= 0.95 | 1.0 (derived, historical 2026-10-08) | PASS (MEASURED live, derived; not re-run) |
| false_heal_rate_overall | = 0.0 | 0.0 | PASS (SIMULATED) |
| false_heal_rate_adversarial | = 0.0 | 0.0 (orchestrator path) | PASS (MEASURED live, historical; raw matcher 1.0 is a diagnostic) |
| critic_catch_rate | >= 0.9 | 1.0 | PASS (SIMULATED, post intent fix) |
| critic_false_reject_rate | <= 0.05 | 0.0 | PASS (SIMULATED) |
| classification_accuracy | >= 0.95 | 1.0 | PASS (SIMULATED) |
| genuine_passed_to_heal | = 0 | 0 | PASS (SIMULATED) |
| contract_healed | = 0 | 0 | PASS (SIMULATED) |
| cost_per_heal | <= 2.0 | 1.0 | PASS (live report, constant by construction) |
| pipeline_latency_ms | <= 100 | 19.99 ms (mean pipeline overhead) | PASS (MEASURED live, historical; browser 1122.08 ms is a diagnostic) |
| alert_completeness | = 1.0 | `tests/test_alerts.py` green | PASS (MEASURED) |
| heal_survival_rate | TBD | no history | UNVERIFIED by design |

The two former red gates were resolved by a human-approved measurement
correction on 2026-11-06, not by changing a report value or threshold. The
raw diagnostics stay visible:

- raw matcher adversarial FHR: **1.0 (9/9)**;
- browser latency per heal: **1122.08 ms**.

Normal `check_gates` exits 0. `check_gates --strict` exits 1 because
`heal_survival_rate` is UNVERIFIED; a human must activate it once history
exists or record a formal deferral.

`docs/TARGETS.md` still lists the sim report for `heal_accuracy`, while
`scripts/check_gates.py` reads its live counterpart. The checker output
above is authoritative for this snapshot. The live value is **derived**
from `e2e_live.json` by `scripts/bench_golden_live.py`; refresh it with a
new live run when Docker is available.

## Benchmarks and evidence

| Benchmark | Cases | Result | Provenance |
|---|---|---|---|
| Core decision | 24 | classification 1.000, 0 genuine passed, 0 wrong | SIMULATED |
| Critic verify | 15 injected | catch 1.000, false-reject 0.000, FHR 0.000 | SIMULATED |
| Golden set | 24 | accuracy 1.000, FHR 0.000, PASS | SIMULATED |
| API | 7 | 0 contract heals, FHR 0.000, 0 wrong | SIMULATED |
| Healenium sim | 24 | accuracy 1.000, FHR 0.286, adversarial 6/9 | SIMULATED |
| Healenium live | 24 | accuracy 1.000, FHR 0.375, adversarial 9/9, 1122 ms | MEASURED 2026-10-08 |
| Live E2E pipeline | 24 | accuracy 1.000, FHR 0.000, adversarial 0.000, escaped 0, 1464.7 ms lookup | MEASURED 2026-10-08 |
| Golden live (derived) | 24 | accuracy 1.000, FHR 0.000, escaped 0 | DERIVED from live E2E 2026-10-08; generated 2026-11-05 |
| Held-out UI | 24 | accuracy 1.000, catch 1.000, FHR 0.000, escaped 0 | MEASURED 2026-10-14 |
| Held-out API | 11 | 10/11, contract heals 0, FHR 0.000 | MEASURED 2026-10-14 |
| Demo cases | 24 | 24/24 match pre-registered expectations | SIMULATED 2026-11-04 |
| Shadow mode | 24 | 0 PRs opened, 0 escaped defects | SIMULATED |
| Vision/LLM | 24 | 15/15 top-1, 15/15 ambiguous, wins: 1st=15, 2nd–4th=0; verdict DROP | SIMULATED |

## Live vs simulated

- Raw live Healenium heals **9/9** adversarial cases; the simulator heals
  6/9. The sim understated removed-element danger and overstated
  duplicate-button danger. Verdict from both sources: **Healenium alone
  is not safe** (`docs/LIVE_VS_SIM.md`).
- The live pipeline still records **0.000** adversarial false heals because
  the classifier short-circuits all 9 blocked cases before matching. This
  is containment by the pipeline, not by the matcher
  (`docs/E2E_LIVE.md`).
- Live latency is roughly three orders of magnitude above the sim number:
  1122 ms/heal measured on the raw matcher, 1464.7 ms per live lookup in
  the E2E run vs in-process microseconds.
- Adapter v0.2.0 is narrowed to the observed backend shape (`data` key,
  string-encoded score). The earlier `items`/numeric/`?locator=` simulator
  assumptions are retired (`docs/HEALENIUM.md`).

## Held-out generalization (MEASURED 2026-10-14)

`benchmark/heldout/` now exists: 24 unseen UI cases and 11 unseen API
cases, labels fixed before running.

- UI: classification 1.000, Critic catch 1.000 (15/15 injected),
  false-reject 0.000, false-heal 0.000, escaped defects 0.
- API: class+heal match 10/11, auto-healed contract changes 0,
  false-heal 0.000.
- The one miss is `heldout:token-cart`: labeled
  `expired_credential`/heal, observed `unapproved_change`/escalate. The
  label and the three-endpoint `observe()` coverage are both implicated;
  the case fails closed (nothing healed). It is deliberately left
  unfixed for a separate change.
- Independence caveat: the author had prior exposure to the pipeline, so
  this is *unseen inputs through a known pipeline*, not a double-blind
  trial (`docs/HELDOUT_PROVENANCE.md`).

## Critic status (MEASURED)

Intent exactness landed in `healing/critic/checks.py` with
`tests/test_intent_exactness.py` (5 known escapes + 7 new look-alikes).
Catch rate is 1.000 on the original 15 seeded wrong heals (0.667 before
the fix). Held-out confirmation: 15/15 caught. The Critic remains one
layer behind deterministic/state/network checks; the optional LLM judge
is disabled by default.

## CI and compliance

- **CI workflows authored**: `ci.yml` runs lint-test, golden, compliance,
  and gates on Python 3.12; `heal-pr.yml` runs unit tests, staging verify,
  a five-run stability loop, a negative check, a grep secret scan, and a
  policy check. **UNVERIFIED** in GitHub Actions (no runs observed here).
- The `gates` CI job now passes locally (11/0/1, exit 0), but the real
  GitHub Actions run is still unobserved. The strict release check exits 1
  until the survival gate has history or a written deferral.
- The `compliance` job currently runs SBOM generation and a retention
  dry-run only. `scripts/sbom.py` defines a license allowlist but never
  checks it; docs claim license enforcement that the workflow does not
  perform.
- Apache-2.0 notices for Healenium reuse are present (`NOTICE`,
  `THIRD_PARTY_NOTICES.md`); SBOM is committed.
- **LICENSE is still a placeholder**, `pyproject.toml` says `TBD`, the
  vendor register is blank, legal review is outstanding, and all 12
  target sign-offs and release boxes in `docs/HUMAN_SIGNOFF.md` are
  unchecked.

## Open gates and risks

1. **Resolved 2026-11-06 by human-approved measurement correction:**
   `false_heal_rate_adversarial` now gates the shipped orchestrator path
   (0.0); raw matcher FHR 1.0 is a diagnostic. `latency_per_heal_ms` was
   replaced by `pipeline_latency_ms` (19.99 ms); browser latency 1122.08 ms
   is a diagnostic. No threshold or report value changed.
2. `heal_accuracy [live]` PASSES only from a **derived historical** report;
   a fresh stack run is still needed to confirm it.
3. `heal_survival_rate` UNVERIFIED — no 30-day history; becomes a FAIL
   gate once data accrues, and `--strict` already exits 1.
4. Held-out API is 10/11; the one miss is documented and fail-closed.
5. `healing/adapters/` is an empty placeholder: no real pytest/Selenium/API
   runner ingestion yet. Current evidence comes from the benchmark harness.
6. GitOps is tested only against a local bare repo; no real GitHub App PR
   or revert has been opened. Alerts have not been delivered to real
   Slack/Teams/Jira endpoints. Screenshot paths in alerts/PRs are
   placeholders.
7. Observability is in-process only: no Prometheus exporter, scrape
   config, or running Grafana; the dashboard JSON is unverified as a live
   observability feed.
8. Live attempts 2–4 were never exercised; every live heal won on
   attempt 1. There is no session reuse, and browser latency stays high.
9. CI on 3.12 is unverified from this host; the local gate run is green.
10. `README.md` now covers quickstart, architecture, commands, evidence,
    and limits; most other docs still lack an executable check. `TODO.md`
    tracks the remaining work.

## Human sign-off

All items in `docs/HUMAN_SIGNOFF.md` remain unchecked. A release tag is
blocked on: live adversarial containment re-verified, held-out built and
measured (now done), survival gate activated or formally deferred, and CI
green on 3.12 observed.

## Changes since the previous status

- **2026-11-06:** project owner approved the gate measurement correction:
  adversarial FHR gates the orchestrator path (0.0), latency gates pipeline
  overhead (19.99 ms), and the raw matcher/browser numbers remain
  diagnostics. Gates are now **11 PASS / 0 FAIL / 1 UNVERIFIED**; normal
  mode exits 0 and strict mode exits 1 on the survival UNVERIFIED.
- Tests: 166 → **204 passed**; lint/mypy re-verified on Python 3.12.10.
- Onboarding: `tasks.py` now runs pytest, ruff, and mypy through
  `sys.executable`, so a fresh venv cannot silently fall back to a PATH
  interpreter. A clean temp venv installed with `pip install -e ".[dev]"`,
  passed 204 tests, ran the 24-case demo, and served the dashboard.
- Dashboard: added a GET-only local page for gates, recent explanation
  records, and the latest saved metrics snapshot. Records are
  hash-checked, PII-masked, and HTML-escaped; there is no authentication,
  so it binds to `127.0.0.1`.
- Operator runbook: added `docs/OPERATOR_RUNBOOK.md` for stack start/stop,
  secret rotation, failed-heal recovery, and retention. Its test checks the
  commands and safety notes against the repository; it records the dry-run
  rollback and the Docker/external-service gaps as **UNVERIFIED**.
- Demo debt: `bench_demo_cases` now runs all **24** pre-registered cases
  (it previously ran only the 12 base cases); new tests cover the bench and
  the one-command demo.
- Quality evidence: `scripts/evidence_snapshot.py` now saves masking,
  narrative, calibration, autonomy, Prometheus, guard, dedupe, PR, and
  revert artifacts in one transcript. The local bare repo is not a real
  GitHub run.
- `heal_accuracy [live]`: UNVERIFIED → **PASS** from
  `scripts/bench_golden_live.py`; that intermediate run was 9 PASS / 2 FAIL
  / 1 UNVERIFIED before the 2026-11-06 measurement correction.
- Held-out set: previously "absent / UNVERIFIED" → **built and measured**
  (UI 24/24, API 10/11).
- Demo: one-command runner added; **24/24** cases match, both XAI records
  print, exit 0.
- Live provenance gates: `heal_accuracy` now requires a live report;
  adversarial and latency gates read live data.
- Worktree: clean after the P0 evidence commit (`dfbbf1e`); the P1.3
  adapter and docs changes land in the following commit.
- Known red gates at the 2026-11-05 snapshot: adversarial false-heal rate
  and live latency. **Superseded 2026-11-06** by the approved measurement
  correction (see the first bullet in this section).
