# Known red gates (none as of 2026-11-06)

Current run: **11 PASS / 0 FAIL / 1 UNVERIFIED**. Evidence:
`reports/evidence/2026-11-06/gates.txt` (normal mode, exit 0) and
`reports/evidence/2026-11-06/gates-strict.txt` (strict mode, exit 1 because
`heal_survival_rate` is UNVERIFIED).

The two former red gates were resolved by a human-approved measurement
correction on 2026-11-06. No report value or threshold was edited. The raw
values remain visible as non-gating diagnostics.

## Resolved: `false_heal_rate_adversarial` (was 1.0 vs target 0.0)

- **Old measurement:** raw live Healenium matcher on the 9 must-not-heal
  cases. It healed 9/9, so the rate was 1.0.
- **New gate:** the shipped orchestrator path in
  `benchmark/reports/e2e_live.json`; all 9 cases escalate, so
  `adversarial_fhr = 0.0`.
- **Still visible:** raw matcher FHR 1.0 in the diagnostics section. The
  raw matcher is deliberately protected by the classifier, Critic, and
  policy; it is not safe alone.
- **Evidence:** `benchmark/reports/e2e_live.json`,
  `benchmark/reports/healenium_live.json`, and `docs/E2E_LIVE.md`.

## Resolved: `latency_per_heal_ms` (was 1122.08 vs target 100 ms)

- **Old measurement:** live browser session time per heal (1122.08 ms).
- **New gate:** `pipeline_latency_ms`, the mean orchestrator overhead from
  `e2e_live.json` rows (19.99 ms), against the same 100 ms bar.
- **Still visible:** browser latency 1122.08 ms in the diagnostics section.
- **Evidence:** `benchmark/reports/e2e_live.json` and
  `reports/evidence/2026-11-06/gates.txt`.

## Remaining strict blocker

`heal_survival_rate` is **UNVERIFIED** because no 30-day heal history
exists. Normal `check_gates` exits 0 with one UNVERIFIED row;
`check_gates --strict` exits 1 by design. A human must activate the gate
once history exists or record a formal deferral.

## History

The pre-correction run is retained unchanged:
`reports/evidence/2026-11-05/gates-after-golden-live.txt` records
9 PASS / 2 FAIL / 1 UNVERIFIED. Do not rewrite dated transcripts when a
measurement definition changes.
