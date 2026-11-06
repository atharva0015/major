# Gate review (current run 2026-11-06, after the approved measurement correction)

Overall: **PASS (0 failing)**. The checker exits 0 in normal mode. No
benchmark report, measured value, or threshold was changed to make a gate
pass.

Current result: **11 PASS / 0 FAIL / 1 UNVERIFIED**. Evidence:
`reports/evidence/2026-11-06/gates.txt` and `gates-strict.txt`.

`heal_survival_rate` remains UNVERIFIED because there is no 30-day history.
Normal mode exits 0; `--strict` exits 1 until the survival data exists or a
human records a waiver.

## What changed on 2026-11-06

A human approved a measurement correction, not a threshold change:

- `false_heal_rate_adversarial` now reads the **shipped orchestrator path**
  from `benchmark/reports/e2e_live.json` (`adversarial_fhr = 0.0`). The raw
  matcher still heals 9/9 in `healenium_live.json`, but that is shown as a
  non-gating diagnostic.
- `latency_per_heal_ms` is replaced by `pipeline_latency_ms`, the mean
  orchestrator overhead from `e2e_live.json` rows (~19.99 ms). Browser time
  (1122.08 ms) remains a non-gating diagnostic.

Both raw values remain visible in `scripts.check_gates.diagnostics()`, the
dashboard's "Diagnostics (not gating)" section, and the evidence index. The
old 9 PASS / 2 FAIL / 1 UNVERIFIED run is retained as history in
`reports/evidence/2026-11-05/gates-after-golden-live.txt`.

## Passing gates

heal_accuracy 1.0 (derived live, historical 2026-10-08), overall false-heal
0.0, adversarial false-heal on the orchestrator path 0.0, Critic catch 1.0,
Critic false-reject 0.0, classification 1.0, genuine passed to heal 0,
contract healed 0, cost 1.0 <= 2.0, pipeline latency 19.99 ms <= 100 ms,
alert_completeness (test_alerts.py green). Survival UNVERIFIED (no history;
becomes a FAIL gate once data accrues).

## Diagnostics (not gates)

- **Raw matcher adversarial FHR:** 1.0 (9/9 healed) from
  `benchmark/reports/healenium_live.json`. Healenium alone is not safe; the
  classifier, Critic, and policy are what contain it.
- **Browser latency per heal:** 1122.08 ms from the same report. This is a
  browser-session cost, not orchestrator overhead.

## Caveats a reviewer must carry

- `heal_accuracy [live]` is **derived**, not freshly measured:
  `scripts/bench_golden_live.py` reads `benchmark/reports/e2e_live.json`
  from 2026-10-08 and writes `golden_live.json`. It refuses a source that
  is not marked `"live": true`, but it does not re-run Docker or the stack.
- The orchestrator adversarial and pipeline-latency values are from the same
  historical 2026-10-08 live report. Docker is unavailable, so they have not
  been re-measured in this environment.
- `python -m scripts.check_gates --strict` exits 1 on UNVERIFIED gates. The
  survival gate would therefore block a strict release check until it has
  history or a written human waiver.
- Nothing here weakens the golden `1.0/0.0` limits in `policy.yaml`.

## Human sign-off checklist

- [x] Decide the `false_heal_rate_adversarial` gate: measure the shipped
  orchestrator path, keep raw matcher output as a diagnostic (human: project
  owner, session approval, date: 2026-11-06).
- [x] Decide the `latency_per_heal_ms` gate: measure pipeline overhead, keep
  browser latency as a diagnostic (human: project owner, session approval,
  date: 2026-11-06).
- [ ] Approve each "proposed" target in docs/TARGETS.md (or tighten it).
- [ ] Accept the DROP verdict on vision/LLM or fund real screenshots.
- [ ] Activate the survival FAIL gate once 30-day history exists.
