# Quality targets (all "proposed, needs human sign-off")

Bars are set from risk, not from current results. Safety metrics
(false heals, escaped defects, contract heals) are absolute and must
never be loosened to fit measured numbers.

| Metric | Target | Rationale | Measured by |
|---|---|---|---|
| heal accuracy | >= 0.95 | Flake allowance; golden separately pins 1.0 | golden.json, decision.json |
| false-heal rate, overall (orchestrator) | = 0.0 | Any wrong heal can hide a defect | verify.json, golden.json |
| false-heal rate, adversarial (orchestrator path) | = 0.0 | Willful-misheal cases must all escalate | healenium.json adversarial slice, decision.json |
| Critic catch rate | >= 0.90 | 1-in-3 escapes today is inadequate | verify.json |
| Critic false-reject rate | <= 0.05 | Waste, not danger; lenient bound | verify.json |
| classification accuracy | >= 0.95 | Misroutes can expose adversarial cases to the healer | decision.json |
| genuine regressions passed to heal engine | = 0 | Defect-masking is the top risk | decision.json |
| auto-healed contract changes | = 0 | Absolute per AGENTS.md | api.json |
| cost per heal | <= 2.0 units | 2x current 1.0; tripwire for runaway model/API spend | healenium.json |
| latency per heal | <= 100 ms | Far above in-process ~0.02 ms; headroom for CI variance | healenium.json |
| alert completeness | = 1.0 | Every escalation must carry evidence | tests/test_alerts.py (subgate) |
| heal survival rate | TBD, pending data | No history yet; becomes a FAIL gate once data accrues | UNVERIFIED by design |

```yaml targets
- metric: heal_accuracy
  op: ">="
  value: 0.95
  source: benchmark/reports/golden.json
  key: accuracy
- metric: false_heal_rate_overall
  op: "=="
  value: 0.0
  source: benchmark/reports/verify.json
  key: false_heal_rate
- metric: false_heal_rate_adversarial
  op: "=="
  value: 0.0
  source: benchmark/reports/healenium.json
  key: "results[computed: wrong_heals/healed among should_heal=false]"
- metric: critic_catch_rate
  op: ">="
  value: 0.9
  source: benchmark/reports/verify.json
  key: catch_rate
- metric: critic_false_reject_rate
  op: "<="
  value: 0.05
  source: benchmark/reports/verify.json
  key: false_reject_rate
- metric: classification_accuracy
  op: ">="
  value: 0.95
  source: benchmark/reports/decision.json
  key: accuracy
- metric: genuine_passed_to_heal
  op: "=="
  value: 0
  source: benchmark/reports/decision.json
  key: genuine_passed_to_heal
- metric: contract_healed
  op: "=="
  value: 0
  source: benchmark/reports/api.json
  key: contract_healed
- metric: cost_per_heal
  op: "<="
  value: 2.0
  source: benchmark/reports/healenium.json
  key: metrics.cost_per_heal
- metric: latency_per_heal_ms
  op: "<="
  value: 100.0
  source: benchmark/reports/healenium.json
  key: metrics.latency_per_heal_ms
```
