# Demo-cases provenance: what was (and was not) open while authoring

## Files read before writing the 12 demo cases

`demo_app/app.py`, `demo_app/drift.py`, `benchmark/cases.py`,
`benchmark/harness.py` (signatures only), `benchmark/healenium_healer.py`,
`benchmark/heldout/` headers, `healing/orchestrator.py` (heal_case
signature and HealOutcome fields only), `healing/critic/checks.py`
(signatures plus the deterministic `disabled`/`aria-hidden` snippet only),
`healing/alerts/model.py` + `routers.py` (constructors only),
`Makefile`, `tests/test_live_healenium.py` (import pattern only).
Expectations in `cases.yaml` were written before `scripts/demo.py`
existed and before any run.

## Files NOT opened during demo-case authoring

`healing/classifier/rules.py`, the remainder of `healing/critic/checks.py`,
`healing/policy/policy.yaml` — no reads, no edits, in that step.

## Plain statement on independence

Independence **cannot be fully shown**, for the same reason recorded in
`docs/HELDOUT_PROVENANCE.md`: earlier sessions read all three frozen
files in full (rules during QA, checks during the intent fix, policy
across several sessions), and their behavior is additionally documented
in `docs/GATE_REVIEW.md` and prior run logs. The 12 harder cases below
were authored in a session that opened none of the three files, and
their expectations were fixed before any run — but the author is not
blind. Treat results as *authored probes through a known pipeline*,
graded against pre-registered expectations, not as a double-blind trial.

## Frozen hashes re-verified this session (read-only `git hash-object`)

- `healing/classifier/rules.py` → `979914fd77151753b62072c885ed3a764e5834f6` (matches)
- `healing/critic/checks.py` → `b4967ea84dba703db4bc7b25df3122e9bd497818` (matches)
- `healing/policy/policy.yaml` → `31cdbd25d75113f26628dea55fe2f2f43035be4e` (matches)

`git diff --stat baseline-v0` on the three files shows only the committed
intent-exactness change to `checks.py` (`ba97432`, which predates the
freeze record); no unlogged post-freeze changes. No `CHANGELOG_FROZEN.md`
entry was needed.
