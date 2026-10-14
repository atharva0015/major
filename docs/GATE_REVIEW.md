# Gate review (`make gates`, run locally 2026-10-08)

Overall: **FAIL (2 failing)**. Checker exits non-zero as designed. No
benchmark, report, or threshold was changed to make any gate pass.

## Failing gates

- **false_heal_rate_adversarial: 1.0 vs target 0.0.** The raw Healenium sim
  heals 6 of 9 must-not-heal cases (duplicate buttons, swapped roles). This
  measures the *unprotected* matcher: the orchestrator path that actually
  ships escalates all 9 (see decision.md confusion matrix) and is covered by
  its own 0.0 gate, which passes. Do not "fix" this by retuning the sim;
  fix it by keeping the classifier + Critic gates in front of every heal.
- **critic_catch_rate: 0.667 vs target 0.90.** 5 of 15 seeded wrong heals
  escape, all same-stem neighbor confusion (`add-cart-2` for `add-cart-1`).
  The Critic's intent layer cannot distinguish them. This is the correct
  FAIL: one in three wrong heals escaping is inadequate, and the bar was
  set from risk, not fitted to the 0.667 measurement.

## Passing gates

heal_accuracy 1.0, overall false-heal 0.0, false-reject 0.0,
classification 1.0, genuine passed to heal 0, contract healed 0,
cost 1.0 <= 2.0, latency ~0.02 ms <= 100 ms, alert_completeness
(test_alerts.py green). Survival UNVERIFIED (no history; becomes a FAIL
gate once data accrues).

## Caveats a reviewer must carry

- The Healenium numbers are **simulated** (`live: False` in healenium.md);
  cost/latency are in-process units, not production figures.
- Nothing here weakens the golden `1.0/0.0` limits in `policy.yaml`.

## Human sign-off checklist

- [ ] Approve each "proposed" target in docs/TARGETS.md (or tighten it).
- [ ] Accept the DROP verdict on vision/LLM or fund real screenshots.
- [ ] Decide: fix intent-exactness for neighbor confusion, or accept 0.667.
- [ ] Activate the survival FAIL gate once 30-day history exists.
