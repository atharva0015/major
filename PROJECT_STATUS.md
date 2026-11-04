# Project status (regenerated 2026-11-04)

Snapshot: branch `chore/baseline`, after the 2026-11-04 evidence audit
(HEAD moves with the evidence commit).

Labels: **MEASURED** = observed from a real run in a recorded session.
**SIMULATED** = produced by the Healenium simulator or in-process replay,
not the live stack. **UNVERIFIED** = not observed here (needs CI, Docker
rerun, or a missing input).

## Summary

The healing pipeline is implemented end-to-end: classify → match →
sandbox replay → layered Critic → policy gate → explanation record →
alert / shadow PR, with an API sidecar and quality tooling. **MEASURED
this session (2026-11-04, Python 3.12.10): 175 tests pass; lint and mypy
are clean; the 24-case demo matches 24/24; gates report 8 PASS, 2 FAIL,
2 UNVERIFIED (exit 1).** Both failures are the documented ones: the raw
live Healenium matcher heals 9/9 adversarial cases, and live latency is
1122 ms against a sim-era 100 ms target. The pipeline around the matcher
still escalates all 9 adversarial cases (MEASURED live, 2026-10-08).

The held-out set now exists and was measured (previous status said it was
absent): UI 24/24 correct with 0 false heals; API 10/11, with one
documented label/coverage miss that fails closed. `heal_accuracy [live]`
remains UNVERIFIED because `benchmark/reports/golden_live.json` has never
been produced. Survival remains UNVERIFIED by design (no history).

## Verification this session (MEASURED 2026-11-04)

| Check | Result |
|---|---|
| `pytest -q` | 175 passed in 15.12 s |
| `ruff check .` | clean |
| `ruff format --check .` | 162 files already formatted |
| `mypy healing` | no issues in 50 source files |
| `python tasks.py demo` | 24/24 cases match, exit 0 |
| `python -m scripts.check_gates` | 8 PASS / 2 FAIL / 2 UNVERIFIED, exit 1 |

Environment: Windows host, project venv `.venv312` (Python 3.12.10).
`make` is absent on this host, so Makefile-equivalent commands were run
directly. GitHub Actions results were not observed from here.

## Gate table (fresh `check_gates` run, MEASURED this session)

| Gate | Target | Value | Status |
|---|---|---|---|
| heal_accuracy | >= 0.95 | no live report | UNVERIFIED (needs `golden_live.json`) |
| false_heal_rate_overall | = 0.0 | 0.0 | PASS (SIMULATED) |
| false_heal_rate_adversarial | = 0.0 | 1.0 | FAIL (MEASURED live raw matcher) |
| critic_catch_rate | >= 0.9 | 1.0 | PASS (SIMULATED, post intent fix) |
| critic_false_reject_rate | <= 0.05 | 0.0 | PASS (SIMULATED) |
| classification_accuracy | >= 0.95 | 1.0 | PASS (SIMULATED) |
| genuine_passed_to_heal | = 0 | 0 | PASS (SIMULATED) |
| contract_healed | = 0 | 0 | PASS (SIMULATED) |
| cost_per_heal | <= 2.0 | 1.0 | PASS (live report, constant by construction) |
| latency_per_heal_ms | <= 100 | 1122.08 | FAIL (MEASURED live) |
| alert_completeness | = 1.0 | `tests/test_alerts.py` green | PASS (MEASURED) |
| heal_survival_rate | TBD | no history | UNVERIFIED by design |

Two gates fail and are not waived. Per `docs/KNOWN_RED_GATES.md`, a human
must decide fix / waive / change target for each; no box is ticked.

`docs/TARGETS.md` still lists the sim report for `heal_accuracy`, while
`scripts/check_gates.py` now looks for its live counterpart. The checker
output above is authoritative for this snapshot.

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
- The `gates` CI job will fail while the two red gates stand. That is
  expected until a human records the decisions.
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

1. `false_heal_rate_adversarial` red (1.0 live raw vs 0.0). Contained by
   the classifier + Critic in the shipped path, but the gate itself is
   undecided.
2. `latency_per_heal_ms` red (1122 ms vs 100 ms). The target was written
   for sim units; changing it now would be tuning to fit, so it stands
   until a human resets it deliberately.
3. `heal_accuracy [live]` UNVERIFIED — no `golden_live.json`.
4. `heal_survival_rate` UNVERIFIED — no 30-day history; becomes a FAIL
   gate once data accrues.
5. Held-out API is 10/11; the one miss is documented and fail-closed.
6. `healing/adapters/` is an empty placeholder: no real pytest/Selenium/API
   runner ingestion yet. Current evidence comes from the benchmark harness.
7. GitOps is tested only against a local bare repo; no real GitHub App PR
   or revert has been opened. Alerts have not been delivered to real
   Slack/Teams/Jira endpoints. Screenshot paths in alerts/PRs are
   placeholders.
8. Observability is in-process only: no Prometheus exporter, scrape
   config, or running Grafana; the dashboard JSON is unverified.
9. Live attempts 2–4 were never exercised; every live heal won on
   attempt 1. There is no session reuse, and the live latency stays high.
10. CI on 3.12 is unverified from this host. The `gates` job is red by
    design until the gate decisions land.
11. `README.md` is still a four-line scaffold; `PROJECT_STATUS.md` was
    stale and is regenerated here. `TODO.md` tracks the remaining work.

## Human sign-off

All items in `docs/HUMAN_SIGNOFF.md` remain unchecked. A release tag is
blocked on: live adversarial containment re-verified, held-out built and
measured (now done), survival gate activated or formally deferred, and CI
green on 3.12 observed.

## Changes since the previous status

- Tests: 166 → **175 passed**; lint/mypy re-verified on Python 3.12.10.
- Held-out set: previously "absent / UNVERIFIED" → **built and measured**
  (UI 24/24, API 10/11).
- Demo: one-command runner added; **24/24** cases match, both XAI records
  print, exit 0.
- Live provenance gates: `heal_accuracy` now requires a live report;
  adversarial and latency gates read live data.
- Worktree: previously "uncommitted work remains" → **clean** at
  `f4c8093`; live-stack fixes and later evidence/docs are committed.
- Known red gates corrected to the two that currently fail: adversarial
  false-heal rate and live latency (the earlier 166-test snapshot reported
  a different mix).
