# Decisions

Architecture Decision Records.

## ADR-001: Deterministic core, probabilistic edges

Scoring, policy, gating, and Git operations are plain code; models only
propose candidates. Rationale: auditability and fail-closed safety.

## ADR-002: Fail closed on unknown / low-confidence / conflict

Unknown, low-confidence, or conflicting results fail the test and escalate
to a human rather than guessing. Rationale: wrong heals hide real defects.

## ADR-003: Never auto-heal contracts, assertions, or perf thresholds

API contract changes, assertion changes, and performance thresholds require
human review. Rationale: these encode product intent.

## ADR-004: Structured explanation before narrative; full replayability

Every heal emits a structured explanation record first, then narrative.
Store model, prompt, policy, and config versions. Rationale: debugging
and audit.

## ADR-005: Reuse Healenium under Apache 2.0

Reuse Healenium for locator matching; keep license notices and a NOTICE
entry (see `THIRD_PARTY_NOTICES.md`). Rationale: avoid reinventing
matching; respect upstream license.
