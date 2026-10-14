# Known red gates (MEASURED via `make gates` equivalent, exit 1)

Two gates fail. Neither was tuned, waived, or edited around. A human must
decide, per gate: **fix** the underlying cause, **waive** with written
reason, or **change the target** with rationale. No box below is ticked.

## 1. `false_heal_rate_adversarial` — 1.0 vs target 0.0 (SIMULATED sim data)

- Why it fails: the raw Healenium simulator heals 6 of 9 must-not-heal
  cases (duplicate buttons, swapped roles). Live measurement is worse
  (9/9, `healenium_live.md`). The unprotected matcher cannot refuse.
- What a fix looks like: keep classifier + Critic gates in front of every
  heal (already the shipped path — its own 0.0 gate passes); optionally
  point this gate at live data when a live bench runs in CI.
- Decision:
  - [ ] Fix (human: ______, date: ______)
  - [ ] Waive with reason (human: ______, date: ______)
  - [ ] Change target with rationale (human: ______, date: ______)

## 2. `latency_per_heal_ms` — 1122.08 vs target 100.0 (MEASURED live)

- Why it fails: the 100 ms bar was set for in-process sim units (~0.02 ms);
  real browser sessions cost ~1.1 s per heal. The target, not the system,
  is mismatched to the live path — but changing it here would be tuning
  to fit, so it stands as a FAIL until a human resets it deliberately.
- What a fix looks like: session reuse across cases, or a latency budget
  split by path (sim vs live) with separate bars.
- Decision:
  - [ ] Fix (human: ______, date: ______)
  - [ ] Waive with reason (human: ______, date: ______)
  - [ ] Change target with rationale (human: ______, date: ______)
