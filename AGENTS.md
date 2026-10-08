# AGENTS.md

Rules for all agents working in this repo. Safety matters more than autonomy:
wrong heals can hide real defects, so the system must fail closed.

- Deterministic core, probabilistic edges: scoring, policy, gating, and Git operations are plain code; models only propose.
- Fail closed: unknown, low-confidence, or conflicting results fail the test and escalate to a human.
- Never auto-heal API contract changes, assertions, or performance thresholds.
- Every heal produces a structured explanation record before any narrative text.
- Every heal is replayable: store model, prompt, policy, and config versions.
- No secrets in code or logs; read credentials from environment variables; mask personal data before any external call.
- Healenium code is reused under Apache 2.0: keep license notices and add a NOTICE entry.
- Write tests with every change; do not claim a feature works unless its tests pass.
- Prefer small diffs; do not touch files outside the current task.
