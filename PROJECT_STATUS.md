# Project status (regenerated; every number labeled by provenance)

Labels: **MEASURED** = observed from a real run in a recorded session.
**SIMULATED** = produced by the Healenium sim, not the live stack.
**UNVERIFIED** = not observed here (needs CI, Docker rerun, or missing input).

## Summary

The framework is code-complete through Phase 8 plus the VISION_LLM
extension (verdict DROP, left disabled). MEASURED this session on
Python 3.10: 166 tests pass; gates FAIL on 1 of 12 (sim adversarial
false-heals). The Critic intent-exactness fix moved MEASURED catch rate
0.667 → 1.000. Live Healenium numbers exist on disk
(`healenium_live.md`, MEASURED 2026-10-08: adversarial false-heals 9/9,
latency ~1122 ms/heal). The held-out set was never built
(`benchmark/heldout/` absent), so generalization is UNVERIFIED. Two
commits since `baseline-v0` are in; uncommitted work remains.

## Gate table (fresh `check_gates` run, MEASURED this session)

| Gate | Target | Value | Status |
|---|---|---|---|
| heal_accuracy | >= 0.95 | 1.0 | PASS (MEASURED) |
| false_heal_rate_overall | = 0.0 | 0.0 | PASS (MEASURED) |
| false_heal_rate_adversarial | = 0.0 | 1.0, SIMULATED sim | FAIL (MEASURED checker run) |
| critic_catch_rate | >= 0.9 | 1.0 | PASS (MEASURED, post intent fix) |
| critic_false_reject_rate | <= 0.05 | 0.0 | PASS (MEASURED) |
| classification_accuracy | >= 0.95 | 1.0 | PASS (MEASURED) |
| genuine_passed_to_heal | = 0 | 0 | PASS (MEASURED) |
| contract_healed | = 0 | 0 | PASS (MEASURED) |
| cost_per_heal | <= 2.0 | 1.0 | PASS (SIMULATED units) |
| latency_per_heal_ms | <= 100 | ~0.02 | PASS (SIMULATED units) |
| alert_completeness | = 1.0 | test_alerts green | PASS (MEASURED) |
| heal_survival_rate | TBD | no history | UNVERIFIED by design |

## Live vs simulated (MEASURED live 2026-10-08 vs SIMULATED)

- Live adversarial false-heals: 9/9 (escalation 0.000) — worse than the
  sim's 6/9; the sim understated removed-element danger and overstated
  duplicate-button danger. Verdict, both sources: Healenium alone is NOT safe.
- Live latency ~1122 ms/heal vs SIMULATED ~0.02 ms (in-process units).
- Live adapter v0.2.0 narrowed to the observed `data`-key, string-encoded
  score shape; simulator assumptions (`items`, numeric score, `?locator=`
  filtering) were wrong and are retired.

## Held-out generalization: BLOCKED (no data)

`benchmark/heldout/` does not exist; the plan session produced only a plan.
Classification accuracy, Critic catch/false-reject, false-heal rate, and
escaped defects on unseen cases are all UNVERIFIED. Do not claim
generalization.

## Critic fix status (MEASURED)

Intent-exactness landed in `healing/critic/checks.py` with
`tests/test_intent_exactness.py` (5 known escapes + 7 new look-alikes).
Catch rate MEASURED 1.000 on the original 15 seeded wrong heals
(vs 0.667 pre-fix). Held-out confirmation pending (see above).

## CI on 3.12

- Local clean 3.12 venv (prior session, MEASURED): lint clean, tests
  passed, golden PASS, SBOM + retention ran.
- GitHub Actions runs on 3.12 (`lint-test`, `golden`, `compliance`,
  `gates` jobs): UNVERIFIED from here (no Actions results observed).
- Windows host runs 3.10; `make` absent (equivalents used); Selenium
  optional test skips without the package.

## Open gates and risks

1. Sim adversarial gate red (1.0 vs 0.0) — by design; live numbers are
   worse (9/9), contained only by classifier+Critic gating.
2. Survival gate UNVERIFIED (no history).
3. Uncommitted tree: live-stack fixes committed (`cc0bb3c`); targets
   session + chatbot/license/adapters/intent-test files uncommitted.
4. COMPLIANCE vendor register blank, LICENSE undecided, legal review
   outstanding — see `docs/HUMAN_SIGNOFF.md` (all boxes unchecked).
