# Architecture

Fail-closed self-healing loop for UI and API tests.

Flow: `adapters` detect failing tests → `classifier` labels the failure
(unknown → escalate) → `matching` proposes locator candidates (Healenium,
Apache 2.0) → `sandbox` replays up to 3 heals in isolation → `critic`
independently verifies → `xai` writes a structured explanation record →
`policy` gates (deterministic code; models only propose) → `alerts`
escalates to humans on failure → `gitops` delivers fixes as reviewed
GitHub pull requests.

Sidecars: `nonui` handles API/schema failures (never auto-heals contracts,
assertions, or perf thresholds); `quality` tracks benchmarks and flakes;
`security` enforces env-only secrets and PII masking before external calls.

Safety: scoring, policy, gating, and Git operations are plain code.
Low-confidence or conflicting results fail the test and escalate.
Every heal stores model, prompt, policy, and config versions for replay.
