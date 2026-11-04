# TODO — feature inventory and open work

Snapshot: 2026-11-04 · branch `chore/baseline` · HEAD `f4c8093` · working tree clean.

Legend: `[x]` completed · `[~]` implemented but not fully verified/shipped · `[ ]` not completed.
Evidence labels follow `PROJECT_STATUS.md`: **MEASURED**, **SIMULATED**, **UNVERIFIED**.

At a glance: **72 done · 13 partial · 31 open**.

> Note on "partial": these are working features whose end-to-end proof is
> incomplete (real integration, live repeat run, or CI observation), not
> half-written code.

## 1. Completed features

### 1.1 Core healing pipeline

- [x] **Failure classifier** — six classes (`locator_drift`, `data_issue`,
  `timing_issue`, `environment_issue`, `genuine_regression`, `contract_change`),
  policy-driven rule weights and class priors (`healing/classifier/rules.py`).
- [x] **Fail-closed blocked classes** — genuine regressions, environment faults,
  and contract changes never reach the heal engine and get zero retries
  (`healing/orchestrator.py`, `healing/policy/policy.yaml`).
- [x] **Matcher interface** — abstract `find_candidates` / `score` / `explain`
  seam so the pipeline does not depend on a concrete matcher
  (`healing/matching/base.py`).
- [x] **Healenium adapter v0.2.0** — reads only Healenium's public backend API;
  narrowed to the observed live `data` key and string-encoded score shape;
  any transport or schema doubt yields no candidates
  (`healing/matching/healenium_adapter.py`).
- [x] **Transparent rescorer** — six weighted features (text, role, accessible
  name, attributes, position, neighbors) with per-feature contributions
  (`healing/matching/rescorer.py`).
- [x] **Attempt ladder** — up to three attempts, optional fourth, attempt-2
  reweighting toward text/role/name, tried-candidate dedupe, per-heal timeout
  and cost budget, hard stop on budget overrun (`healing/orchestrator.py`).
- [x] **Sandbox replay** — in-process deterministic replay, egress allowlist,
  WireMock-style stubs, seeded reset, sandbox/staging parity report
  (`healing/sandbox/runner.py`).
- [x] **Layered Critic** — deterministic, state, network, and intent layers;
  sandbox pass alone never approves a heal; optional LLM judge is disabled by
  default and cannot override a failed deterministic check
  (`healing/critic/checks.py`).
- [x] **Intent-exactness fix** — same-stem neighbor confusion addressed;
  Critic catch rate moved 0.667 → 1.000 on the seeded wrong-heal set
  (`tests/test_intent_exactness.py`).
- [x] **Policy engine** — high/medium thresholds, ambiguity margin, blocked
  classes, autonomy level L3, kill switch, shadow mode, per-heal budgets,
  vision/LLM gating (`healing/policy/engine.py`, `policy.yaml`).
- [x] **Orchestrator** — classify → ladder → record → narrative; returns
  attempt trail and shadow-PR proposal, writes audit entry (`healing/orchestrator.py`).

### 1.2 Explainability and audit

- [x] **Structured explanation records first** — frozen Pydantic schema,
  canonical payload hash, append-only JSONL store
  (`healing/xai/records.py`).
- [x] **Narrative renderer** — human-readable explanation generated from the
  structured record, never instead of it (`healing/xai/narrative.py`).
- [x] **Version pinning and replay** — model, prompt, policy, and config
  versions stored per heal; registry plus replay script
  (`healing/quality/registry.py`, `scripts/replay_heal.py`).
- [x] **Append-only audit log** (`healing/security/audit.py`).

### 1.3 Safety, security, and alerts

- [x] **PII/secret masking** — emails, phones, card numbers, bearer/API tokens,
  plus configurable extra patterns (`healing/security/masking.py`).
- [x] **Retention job** — per-artifact retention windows, dry-run by default,
  `--apply` to delete (`healing/security/retention.py`, `scripts/retention.py`).
- [x] **Alert model with evidence completeness** — required test/build/
  environment/classification/attempts/screenshots/next-step/replay fields,
  severity routing, acknowledgement deadline, quarantine helper
  (`healing/alerts/model.py`).
- [x] **Alert senders** — console, file, Slack, Teams, and Jira webhook senders;
  secrets read from environment only (`healing/alerts/routers.py`).

### 1.4 GitOps delivery

- [x] **GitHub App client** — branch, commit, PR, label, comment, and revert
  operations; protected-branch refusal; env-only credentials; local bare-repo
  client for tests (`healing/gitops/app.py`).
- [x] **AST locator edits** — LibCST rewrite of exactly one failing locator,
  unified diff, stable-locator ranking, refusal on ambiguous matches
  (`healing/gitops/ast_edit.py`).
- [x] **PR template** — summary, diff, confidence, Critic verdict, record link
  and hash, screenshots, sandbox replay link, rollback instructions
  (`healing/gitops/pr_template.py`).
- [x] **Shared-locator dedupe** — one PR per broken page object/locator
  (`healing/gitops/dedupe.py`).
- [x] **Post-merge watcher** — revert PR + alert when a healed test fails inside
  the watch window (`healing/gitops/watch.py`).
- [x] **Shadow mode** — records the diff/PR body it would produce and opens no
  PRs; live/shadow runs made 0 PRs (`healing/orchestrator.py`).

### 1.5 Non-UI / API sidecar

- [x] **API failure classifier** with API-specific classes
  (`healing/nonui/classifier.py`).
- [x] **Allowlisted API actions only** — `refresh_token`,
  `regenerate_fixtures`, `propose_test_update`; everything else escalates
  (`healing/nonui/healers.py`).
- [x] **Contract checks and schema diff** — response shape, endpoint presence,
  required fields, type changes; Pact failures always escalate
  (`healing/nonui/schema_diff.py`, `healing/nonui/pipeline.py`).
- [x] **Assertion/threshold guard** — refuses removed or weakened assertions,
  performance thresholds, and SLAs without explicit human sign-off
  (`healing/nonui/assert_guard.py`).
- [x] **API shadow PR body + audit + explanation record**
  (`healing/nonui/pipeline.py`).

### 1.6 Quality, metrics, and observability

- [x] **Benchmark metrics and reports** — accuracy, false-heal rate, confusion
  matrix, JSON + Markdown output (`healing/quality/metrics.py`).
- [x] **Calibration** — reliability curve and expected calibration error
  (`healing/quality/calibration.py`).
- [x] **Hash-pinned golden set** — CI fails if expectations are edited without
  re-pinning; limits come from policy (`healing/quality/golden_set.py`).
- [x] **Autonomy guard** — runtime L3→L2 downgrade on false-heal/calibration
  breach; never rewrites policy on disk (`healing/quality/autonomy_guard.py`).
- [x] **Survival metrics** — 30/60/90-day survival, revert rate, override rate,
  fingerprint freshness; reports `insufficient_data` instead of inventing
  numbers (`healing/quality/survival.py`).
- [x] **OpenTelemetry traces and Prometheus metrics** — heal latency, cost,
  success, escalations, alert acknowledgement (`healing/quality/observability.py`).

### 1.7 Optional vision/LLM extension

- [x] **Deterministic visual fingerprints** — cosine-similarity shortlist from
  DOM-derived visual features (`healing/matching/vision.py`).
- [x] **Gated LLM proposal** — structured JSON only, masking before external
  calls, selector re-validated against the real DOM, default off per app
  (`healing/matching/llm_attempt.py`, `policy.yaml vision_llm`).
- [x] **Benchmark and verdict** — 15/15 vision top-1 but 15/15 ambiguous;
  attempts 3–4 add zero marginal heals; documented verdict **DROP**, left
  disabled (`docs/EXTENSION_VISION_LLM.md`, `benchmark/reports/vision.md`).

### 1.8 Benchmarks, demo, and evidence

- [x] **Core 24-case UI benchmark** — 15 healable + 9 adversarial, wrong-heal
  injection set (`benchmark/cases.py`, `benchmark/wrong_heals.py`).
- [x] **Healenium simulator benchmark** (`scripts/bench_healenium.py`).
- [x] **Live Healenium benchmark** — pinned stack, 24 cases, live report
  (`benchmark/reports/healenium_live.md`).
- [x] **Live end-to-end pipeline run** — 24/24 correct, 0 pipeline false heals,
  0 escaped defects (`docs/E2E_LIVE.md`).
- [x] **Golden-set benchmark** — 24 cases, accuracy 1.000, false-heal 0.000,
  PASS (`benchmark/reports/golden.md`).
- [x] **API benchmark** — 7 cases, 0 auto-healed contract changes, 0 false
  heals (`benchmark/reports/api.md`).
- [x] **Held-out benchmark** — 35 unseen cases (24 UI + 11 API), labels fixed
  before running (`docs/HELDOUT.md`, `benchmark/heldout/`).
- [x] **Demo-case benchmark** — 24 external mini-demo scenarios, pre-registered
  expectations, 24/24 match (`docs/DEMO_CASES.md`, `benchmark/demo_cases/`).
- [x] **One-command demo** — `make demo` / `python tasks.py demo`; prints the
  result table plus two full XAI records (`scripts/demo.py`, `docs/DEMO_SCRIPT.md`).
- [x] **Shadow-mode report** — 0 PRs opened, 0 escaped defects
  (`benchmark/reports/shadow.md`).
- [x] **Vision/LLM benchmark** (`benchmark/reports/vision.md`).
- [x] **Demo app with UI drift modes and API drift modes**
  (`demo_app/app.py`, `demo_app/drift.py`, `demo_app/api_drift.py`).
- [x] **Committed run logs** for the baseline commands (`reports/run_logs/`).

### 1.9 Infrastructure and tooling

- [x] **Pinned Docker Compose stack** — Postgres, Healenium backend/proxy,
  selector-imitator, Selenium hub + Chrome node, demo app
  (`infra/docker-compose.yml`).
- [x] **Sandbox overlay documentation** (`infra/sandbox.overlay.yml`).
- [x] **SBOM generator** and committed `sbom.json` (`scripts/sbom.py`).
- [x] **CI workflows authored** — lint/test, golden, compliance, gates, plus
  heal-PR jobs (unit tests, staging verify, stability, negative check, secret
  scan, policy check) (`.github/workflows/ci.yml`, `heal-pr.yml`).
- [x] **Pre-commit hooks** — ruff, ruff-format, mypy, whitespace/EOF/YAML checks
  (`.pre-commit-config.yaml`).
- [x] **Make targets and Windows equivalents** — test, lint, bench, bench-api,
  bench-golden, bench-shadow, bench-vision, gates, demo
  (`Makefile`, `tasks.py`).
- [x] **Apache-2.0 notices for Healenium reuse** (`NOTICE`,
  `THIRD_PARTY_NOTICES.md`).

### 1.10 Tests and documentation

- [x] **173 tests passing** on Python 3.12.10, including dedicated coverage for
  classifier, matcher, Critic, policy, orchestrator, sandbox, XAI, alerts,
  GitOps, API sidecar, held-out set, gates, and metrics (**MEASURED 2026-11-04**).
- [x] **Lint/type checks clean** — ruff check, ruff format (157 files), mypy
  (50 source files) (**MEASURED 2026-11-04**).
- [x] **Architecture and ADRs** — deterministic core, fail closed, never heal
  contracts/assertions/thresholds, structured explanation, Healenium reuse
  (`docs/ARCHITECTURE.md`, `docs/DECISIONS.md`).
- [x] **Quality targets** with risk-based rationale (`docs/TARGETS.md`).
- [x] **Gate review, known red gates, and live-vs-sim comparison**
  (`docs/GATE_REVIEW.md`, `docs/KNOWN_RED_GATES.md`, `docs/LIVE_VS_SIM.md`).
- [x] **Healenium setup and live runbook** (`docs/HEALENIUM.md`).
- [x] **Provenance records** for held-out and demo cases, including the honest
  non-blindness statement (`docs/HELDOUT_PROVENANCE.md`,
  `docs/DEMO_PROVENANCE.md`).
- [x] **Frozen-file hash manifest and changelog**
  (`docs/FROZEN_HASHES.md`, `docs/CHANGELOG_FROZEN.md`).
- [x] **Compliance evidence, license options, branch-protection requirements,
  human sign-off checklist** (`docs/COMPLIANCE.md`, `LICENSE_DECISION.md`,
  `BRANCH_PROTECTION.md`, `HUMAN_SIGNOFF.md`).
- [x] **Spike reports** for Healenium explainability and sandbox feasibility
  (`docs/SPIKE_EXPLAINABILITY.md`, `docs/SPIKE_SANDBOX.md`).
- [x] **Deferral record for the chatbot/MCP extension**
  (`docs/EXTENSION_CHATBOT.md`).

## 2. Implemented but not fully verified/shipped

- [~] **Live adversarial containment** — the pipeline escalates all 9 adversarial
  cases (classifier short-circuit), but the raw live matcher heals 9/9. The
  protection is proven on one 24-case, single-seed run; attempts 2+ were never
  exercised live (`docs/E2E_LIVE.md`, `docs/LIVE_VS_SIM.md`).
- [~] **Live Healenium validation** — 24 cases measured once on the pinned stack;
  no repeat run after host/Docker changes; latency target is still the sim-era
  100 ms.
- [~] **GitOps end-to-end** — fully implemented and tested against a local bare
  repo, but no real GitHub App install, no live heal PR, no live revert PR.
- [~] **Alert delivery** — all senders implemented; only console/file exercised
  in benchmarks; no real Slack/Teams/Jira delivery smoke test.
- [~] **Observability deployment** — OTel/Prometheus instrumentation exists in
  code, but no Prometheus exporter, scrape config, or running Grafana; the
  dashboard JSON is an unverified artifact.
- [~] **Screenshot evidence** — alert and PR screenshot fields are populated with
  placeholder paths; no screenshots are captured anywhere.
- [~] **API endpoint coverage** — `observe()` handles only three endpoints; the
  held-out `GET /api/cart` case falls into the unknown-endpoint branch and is
  reported as `unapproved_change` instead of `expired_credential`.
- [~] **Sandbox isolation** — in-process replay and the staging overlay are
  implemented, but no egress-restricted container actually ran in CI.
- [~] **Held-out independence** — expectations were fixed before running, but
  the author had prior exposure to the pipeline; not a double-blind trial.
- [~] **CI verification** — workflows are authored; GitHub Actions results were
  never observed from this machine. The `gates` job will fail until the two red
  gates are decided.
- [~] **Compliance tooling** — SBOM, retention, masking, and audit exist, but the
  SBOM license allowlist is defined and unused, and no CI step enforces it.
- [~] **Vision/LLM extension** — code and benchmark are complete; verdict is DROP
  because there are no real screenshots and attempts 1–2 already win.
- [~] **Documentation surface** — docs are extensive, but `README.md` is still a
  four-line scaffold and `PROJECT_STATUS.md` was stale until this change.

## 3. Not completed

### 3.1 Quality gates and verification

- [ ] **Resolve `false_heal_rate_adversarial`** — 1.0 vs target 0.0 on raw live
  Healenium data. Human must choose: fix, waive with reason, or change target.
- [ ] **Resolve `latency_per_heal_ms`** — 1122 ms vs target 100 ms. Either add
  session reuse / split sim-vs-live budgets, or formally re-baseline.
- [ ] **Produce `benchmark/reports/golden_live.json`** so `heal_accuracy [live]`
  is verified instead of UNVERIFIED.
- [ ] **Activate or formally defer `heal_survival_rate`** once 30 days of heal
  history exists (or record the deferral decision).
- [ ] **Fix the held-out API miss** — correct the `heldout:token-cart` label
  and/or extend `observe()` coverage, then rerun to target 11/11.
- [ ] **Re-verify frozen hashes and add a CHANGELOG_FROZEN entry** after any
  change to `rules.py`, `checks.py`, or `policy.yaml`.
- [ ] **Observe CI green on Python 3.12** for `lint-test`, `golden`, `compliance`,
  and `gates` in GitHub Actions.
- [ ] **Make the `gates` CI job pass** once the red-gate decisions are recorded.
- [ ] **Exercise live attempts 2–4** — every live heal so far won on attempt 1.
- [ ] **Add session reuse / a live latency budget** so the live path has a
  meaningful bar instead of a sim-era number.
- [ ] **Capture real before/after/candidate screenshots** and feed them into
  alerts, PRs, and retention.
- [ ] **Re-run the live E2E bench** after stack or host changes and record the
  evidence.

### 3.2 Integrations and operations

- [ ] **Implement runner adapters** — `healing/adapters/` is an empty placeholder;
  the system has no ingestion path for real pytest, Selenium, or API-suite
  failures yet.
- [ ] **Install the GitHub App and open a real heal PR** — set `GITHUB_APP_ID`,
  `GITHUB_PRIVATE_KEY_PATH`, `GITHUB_INSTALLATION_ID`, and `GITHUB_REPO`; verify
  branch protection, required checks, and CODEOWNERS.
- [ ] **Smoke-test Slack/Teams/Jira alert delivery** with real webhook URLs from
  environment variables.
- [ ] **Deploy Prometheus scraping and the Grafana dashboard** — today only the
  in-process metrics and an unverified dashboard JSON exist.
- [ ] **Schedule the retention job** (cron/CI schedule) and alert on job failure;
  it currently runs manually/dry-run only.
- [ ] **Enforce the SBOM license allowlist in CI** — `scripts/sbom.py` defines an
  allowlist but never checks it; CI does not run `pip-licenses`.
- [ ] **Replace the grep-based secret scan** with a real scanner
  (gitleaks/trufflehog) if the project will be distributed.
- [ ] **Wire `bench-heldout`, `bench-e2e-live`, and `bench-decision` into
  `Makefile` / `tasks.py`** — the scripts exist but are not one-command targets.
- [ ] **Add a CODEOWNERS file** — `docs/BRANCH_PROTECTION.md` requires review for
  `healing/**`, but no CODEOWNERS file exists.
- [ ] **Write the operator runbook** — stack start/stop, secret rotation, failed
  heal recovery, and retention/apply procedure.
- [ ] **Expand API `observe()` endpoint coverage** beyond the three hand-written
  endpoints (also blocks the held-out API fix above).

### 3.3 Product extensions

- [ ] **Vision/LLM revisit** — rerun only with real screenshots and a benchmark
  where attempts 1–2 demonstrably fail; the current verdict is DROP/disabled.
- [ ] **Chatbot/MCP assistant** — **DEFERRED**; revisit only when the four
  criteria in `docs/EXTENSION_CHATBOT.md` hold. No code exists.

### 3.4 Compliance, legal, and release

- [ ] **Choose the project license** — MIT recommended; update `LICENSE` and
  `pyproject.toml` (`license = "TBD"` today). Package is undistributable until
  this is done.
- [ ] **Legal review of `docs/COMPLIANCE.md`** — data handling, DPAs, vendor
  terms.
- [ ] **Complete the vendor/subprocessor register** — region, DPA status, and
  owner are TBD for GitHub, Docker Hub, PyPI, Slack, Teams, Jira, and the
  self-hosted stack.
- [ ] **Approve the 12 quality targets** in `docs/HUMAN_SIGNOFF.md` (all boxes
  unchecked; agents may not tick them).
- [ ] **Confirm release blockers and cut the next tag** — live adversarial
  containment re-verified, held-out built and measured, survival gate activated
  or deferred, CI green on 3.12 observed.
- [ ] **Expand `README.md`** from scaffold to usage, architecture summary, and
  quickstart commands.

### 3.5 Documentation debt closed by this change

- [x] **Regenerate `PROJECT_STATUS.md`** with current test, gate, held-out,
  demo, and live numbers (2026-11-04).
- [x] **Add this `TODO.md`** feature inventory with completed/open markers.
