# Held-out provenance: what was (and was not) read before authoring cases

## Files read before writing `benchmark/heldout/`

`benchmark/cases.py`, `benchmark/harness.py`, `demo_app/app.py`,
`demo_app/api_drift.py`, `benchmark/api/cases.py`,
`healing/classifier/taxonomy.py`, `healing/nonui/classifier.py`,
`healing/nonui/pipeline.py`, `scripts/bench_decision.py`,
`scripts/bench_verify.py`, `healing/quality/metrics.py` (signatures only),
`benchmark/wrong_heals.py` (signature only).

## Files NOT opened during held-out authoring

`healing/classifier/rules.py`, `healing/critic/checks.py`,
`healing/policy/policy.yaml` — no reads, no edits, in this step.

## Plain statement on independence

Independence **cannot be fully shown**. The authoring session reused the
public interfaces above, but the author had prior exposure to the frozen
files' behavior from earlier sessions: the Critic's same-stem allowance
was documented in `docs/GATE_REVIEW.md`, the orchestrator ladder and
`signals_for` markers were read while building `scripts/bench_e2e_live.py`,
and the API classifier rules in `healing/nonui/classifier.py` (not frozen)
were read directly to derive the API labels. True blindness would require
a second author with no repo history. Treat the held-out set as
*unseen inputs through a known pipeline*, not as a double-blind trial.

## Expected outcomes fixed before the first run

**Held-out:** yes. The UI and API expectations in
`benchmark/heldout/ui_cases.py` and `benchmark/heldout/api_cases.py`
(`HELDOUT_API_EXPECTED`) were written before `scripts/bench_heldout.py`
was run. `docs/HELDOUT.md` records: "Labels fixed before running. Nothing
tuned afterward: the one mismatch below stands as recorded."

**Demo:** yes. The original 12 expectations in
`benchmark/demo_cases/cases.yaml` were written before `scripts/demo.py`
existed and before any run. The 12 harder blind cases were added later,
with expectations fixed before their first run, as recorded in
`docs/DEMO_CASES.md`.

## Demo cases (companion record)

The demo cases have their own provenance file, `docs/DEMO_PROVENANCE.md`.
Summary: before authoring, the session read `demo_app/app.py`,
`demo_app/drift.py`, `benchmark/cases.py`, `benchmark/harness.py`
(signatures only), `benchmark/healenium_healer.py`, held-out headers,
`healing/orchestrator.py` (signature and `HealOutcome` fields only),
`healing/critic/checks.py` (signatures plus the deterministic
`disabled`/`aria-hidden` snippet only), alert constructors, `Makefile`,
and the live test's import pattern. It did not open
`healing/classifier/rules.py`, the remainder of `healing/critic/checks.py`,
or `healing/policy/policy.yaml` during that step. The same limitation
applies: the author was not blind, so treat demo results as *authored
probes through a known pipeline*, not a double-blind trial.

## Frozen hashes at held-out time (from `docs/FROZEN_HASHES.md`, verified current)

| File | SHA-256 (`git hash-object`) | Matches working tree |
|---|---|---|
| `healing/classifier/rules.py` | `979914fd77151753b62072c885ed3a764e5834f6` | yes (MEASURED) |
| `healing/critic/checks.py` | `b4967ea84dba703db4bc7b25df3122e9bd497818` | yes (MEASURED) |
| `healing/policy/policy.yaml` | `31cdbd25d75113f26628dea55fe2f2f43035be4e` | yes (MEASURED) |

No frozen file changed during this step (`git status` shows none of them
modified). No `CHANGELOG_FROZEN.md` entry was needed.
