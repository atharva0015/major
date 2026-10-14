# Demo script for presenters (one command)

## Commands

- Unix: `make demo`
- Windows: `python tasks.py demo` (or `.venv312/Scripts/python -m scripts.demo`)

Both print the same output. Runtime is seconds; no Docker, browser, or
network needed.

## What each output row means

| column | meaning |
|---|---|
| case | Drift scenario id from `benchmark/demo_cases/cases.yaml` |
| expected | Pre-registered expectation (HEAL or ESCALATE), fixed before any run |
| pipeline | What the full pipeline chose: a testid (healed) or ESCALATE |
| sim-alone | What the Healenium simulator alone chose (same two outcomes) |
| critic | Layered Critic verdict on the healed choice, or n/a when escalated |

After the table, two full XAI explanation records print: one heal
(`renamed_id`) showing candidates with per-feature contributions,
thresholds, and Critic checks; one escalation (`lookalike_trap`) showing
rejected alternatives and the escalation reason.

The header line states the run label and date.

## Known limits (say these out loud)

- Cases are team-written fixtures, not production traffic.
- Everything shown is SIMULATED: the sim healer plus in-process HTML.
  No live Healenium, browser, or Docker is involved; see
  `docs/LIVE_VS_SIM.md` for the live numbers, which are worse.
- The sim-alone column is weak by construction on custom drift names
  (documented in `docs/DEMO_CASES.md`); the pipeline column is the claim.
- Session 1 (12/12 match, zero Critic/policy failures) required no fix,
  so there is deliberately no fix proposal in this session.
