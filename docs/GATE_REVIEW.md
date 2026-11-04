# Gate review (current run 2026-11-05, after the live-golden derivation)

Overall: **FAIL (2 failing)**. Checker exits non-zero as designed. No
benchmark, report, or threshold was changed to make any gate pass.

Current result: **9 PASS / 2 FAIL / 1 UNVERIFIED**. Evidence:
`reports/evidence/2026-11-05/gates-after-golden-live.txt`.

This file supersedes the stale 2026-10-08 review that reported a
`critic_catch_rate` failure; that issue was fixed and the gate now passes.

## Failing gates

- **false_heal_rate_adversarial: 1.0 vs target 0.0.** The gate reads the
  live Healenium report. The raw matcher heals all 9 must-not-heal cases
  (duplicate buttons, swapped roles). This measures the *unprotected*
  matcher: the orchestrator path that actually ships escalates all 9 (see
  the decision confusion matrix) and is covered by its own 0.0 gate, which
  passes. Do not "fix" this by retuning the matcher; fix it by keeping the
  classifier + Critic gates in front of every heal, or have a human waive
  or re-baseline this gate in writing.
- **latency_per_heal_ms: 1122.08 ms vs target 100 ms.** The 100 ms bar was
  set for in-process sim units (~0.02 ms); real browser sessions cost about
  1.1 s per heal. The target, not the system, is mismatched to the live
  path — but changing it here would be tuning to fit, so it stands as a
  FAIL until a human resets it deliberately.

## Passing gates

heal_accuracy 1.0 (derived live, historical 2026-10-08), overall false-heal
0.0, false-reject 0.0, classification 1.0, genuine passed to heal 0,
contract healed 0, cost 1.0 <= 2.0, alert_completeness (test_alerts.py
green). Survival UNVERIFIED (no history; becomes a FAIL gate once data
accrues).

## Caveats a reviewer must carry

- `heal_accuracy [live]` is **derived**, not freshly measured:
  `scripts/bench_golden_live.py` reads `benchmark/reports/e2e_live.json`
  from 2026-10-08 and writes `golden_live.json`. It refuses a source that
  is not marked `"live": true`, but it does not re-run Docker or the stack.
- The Healenium adversarial and latency values are live measurements from
  2026-10-08 and have not been re-run since Docker became unavailable.
- Nothing here weakens the golden `1.0/0.0` limits in `policy.yaml`.

## Human sign-off checklist

- [ ] Approve each "proposed" target in docs/TARGETS.md (or tighten it).
- [ ] Decide the `false_heal_rate_adversarial` gate: contain, waive, or
  re-baseline (see `docs/KNOWN_RED_GATES.md`).
- [ ] Decide the `latency_per_heal_ms` gate: session reuse, split
  sim/live budgets, or formally re-baseline.
- [ ] Accept the DROP verdict on vision/LLM or fund real screenshots.
- [ ] Activate the survival FAIL gate once 30-day history exists.
