# TODO — feature inventory and open work

Snapshot: 2026-11-04 · branch `chore/baseline` · after the evidence audit.
Working tree contains the evidence, analysis, and wiring changes from this
session; see `git log` for the exact commit.

Legend: `[x]` completed and evidence-backed · `[~]` implemented but not fully
verified/shipped · `[ ]` not completed.
Evidence labels follow `PROJECT_STATUS.md`: **MEASURED**, **SIMULATED**,
**UNVERIFIED**.

At a glance: **62 done · 33 partial · 20 open** (was 72 / 13 / 31 before the
2026-11-04 audit; the P0 batch, P1.3, the demo tests, the quality snapshot,
the dashboard, and the operator runbook closed items).

> **Audit rule used here:** a `[x]` stays only if it has both (a) a passing
> automated test that exercises the behaviour and (b) a saved output artifact
> (a report, run log, or command transcript). Documentation-only items were
> downgraded even when the document is useful, because a document is not an
> executable check. Artifacts under `benchmark/reports/` are regenerated and
> gitignored; durable copies live in `reports/` and the tracked docs.

## 0. Result of the 2026-11-04 audit

- Reviewed **72** existing `[x]` markers.
- **40 kept** with a named test and a saved artifact.
- **32 downgraded** to `[~]`, each with a one-line reason in section 2.2.
- **1 open item closed** this session: bench scripts wired into
  `Makefile` / `tasks.py`, now backed by `tests/test_bench_wiring.py`. It was
  folded into the existing “Make targets” entry rather than added as a new
  marker, so the done count stays 40.
- **1 open item moved to partial**: `.github/CODEOWNERS` exists, but every
  handle is a placeholder.
- **4 duplicate open items merged** into their parent items (CI gates, session
  reuse, `observe()` coverage, vendor register) and **3 audit follow-ups
  added** (presentation rehearsal, evidence-index walkthrough, missing
  test/artifact debt).
- No sign-off box in `docs/HUMAN_SIGNOFF.md` was ticked or edited.
- **P0 batch (2026-11-04):** four of the five P0 items are closed — rehearsal
  logs, evidence-index walkthrough, README, and frozen held-out hashes with an
  automated check. P0.5 (live re-runs) stays open until Docker is available.
- **P1.3 (2026-11-05):** `scripts/bench_golden_live.py` now derives the
  gate-shaped `golden_live.json` from the measured live E2E report; the gate
  moves from UNVERIFIED to PASS (historical data), so the count becomes
  9 PASS / 2 FAIL / 1 UNVERIFIED.
- **Quality snapshot (2026-11-05):** one tested transcript now carries the
  masking, narrative, calibration, autonomy, metrics, guard, and GitOps
  artifacts that were previously test-only.
- **Operator runbook (2026-11-06):** `docs/OPERATOR_RUNBOOK.md` documents
  stack start/stop, secret rotation, failed-heal recovery, retention, and
  the unverified external integrations; `tests/test_operator_runbook.py`
  checks the procedures and commands against the repository.

## 1. Completed features (kept after audit)

### 1.1 Core healing pipeline

- [x] **Failure classifier** — six classes, policy-driven weights and priors
  (`healing/classifier/rules.py`). Evidence: `tests/test_rules.py`,
  `tests/test_taxonomy.py`; `benchmark/reports/decision.md` (accuracy 1.000)
  and `reports/run_logs/scripts.bench_decision.txt`.
- [x] **Fail-closed blocked classes** — genuine regressions, environment faults,
  and contract changes never reach the heal engine (`healing/orchestrator.py`,
  `healing/policy/policy.yaml`). Evidence: `tests/test_policy.py`,
  `tests/test_orchestrator.py`; `benchmark/reports/decision.json`
  (`genuine_passed_to_heal = 0`) and `reports/evidence/2026-11-04/check_gates.txt`.
- [x] **Matcher interface** — abstract `find_candidates` / `score` / `explain`
  seam (`healing/matching/base.py`). Evidence: `tests/test_matcher.py`;
  `benchmark/reports/heldout.md` (matcher results through the seam).
- [x] **Healenium adapter v0.2.0** — public backend API only; `data` key and
  string-encoded scores; transport/schema doubt yields no candidates
  (`healing/matching/healenium_adapter.py`). Evidence: `tests/test_matcher.py`,
  `tests/test_live_healenium.py`; `benchmark/reports/healenium_live.md`
  (2026-10-08, historical).
- [x] **Transparent rescorer** — six weighted features with per-feature
  contributions (`healing/matching/rescorer.py`). Evidence:
  `tests/test_golden.py` (degraded-rescore test); `benchmark/reports/golden.md`.
- [x] **Attempt ladder** — up to three attempts, optional fourth, attempt-2
  reweighting, tried-candidate dedupe, timeout/cost budget
  (`healing/orchestrator.py`). Evidence: `tests/test_ladder.py`,
  `tests/test_ladder_vision.py`; `benchmark/reports/verify.md` (by-attempt
  table) and `reports/evidence/2026-11-04/bench_verify.txt`.
- [x] **Sandbox replay** — in-process deterministic replay, egress allowlist,
  stubs, seeded reset, parity report (`healing/sandbox/runner.py`). Evidence:
  `tests/test_sandbox.py`; `benchmark/reports/demo_cases.md` (`pass:all-layers`
  on healed rows).
- [x] **Layered Critic** — deterministic, state, network, intent layers; sandbox
  pass alone never approves; optional LLM cannot override a failed check
  (`healing/critic/checks.py`). Evidence: `tests/test_critic.py`;
  `benchmark/reports/verify.md` (catch rate 1.000) and
  `reports/evidence/2026-11-04/bench_verify.txt`.
- [x] **Intent-exactness fix** — same-stem neighbor confusion addressed; catch
  rate moved 0.667 → 1.000 on the seeded wrong-heal set
  (`tests/test_intent_exactness.py`). Evidence: `reports/run_logs/scripts.bench_verify.txt`
  (0.667 before), `benchmark/reports/verify.md` (1.000 after), and
  `docs/GATE_REVIEW.md` (history).
- [x] **Policy engine** — thresholds, ambiguity margin, blocked classes, L3,
  kill switch, shadow mode, budgets, vision/LLM gating
  (`healing/policy/engine.py`, `policy.yaml`). Evidence: `tests/test_policy.py`;
  `benchmark/reports/decision.md` and `reports/evidence/2026-11-04/check_gates.txt`.
- [x] **Orchestrator** — classify → ladder → record → narrative; attempt trail,
  shadow-PR proposal, audit entry (`healing/orchestrator.py`). Evidence:
  `tests/test_orchestrator.py`; `benchmark/reports/demo_cases.md` and
  `reports/evidence/2026-11-04/demo.txt` (two full records).

### 1.2 Explainability and audit

- [x] **Structured explanation records first** — frozen schema, canonical
  payload hash, append-only JSONL (`healing/xai/records.py`). Evidence:
  `tests/test_records.py`; `benchmark/reports/records.jsonl` and
  `reports/evidence/2026-11-04/demo.txt` (content hashes).
- [x] **Version pinning and replay** — model, prompt, policy, and config
  versions per heal; registry plus replay (`healing/quality/registry.py`,
  `scripts/replay_heal.py`). Evidence: `tests/test_quality_ops.py`;
  `benchmark/reports/records.jsonl` (all four version fields). Replay is
  test-only; no saved replay transcript.
- [x] **Append-only audit log** (`healing/security/audit.py`). Evidence:
  `tests/test_masking.py`; `benchmark/reports/audit.log` (hash-chained rows).

### 1.3 Safety, security, and alerts

- [x] **Retention job** — per-artifact windows, dry-run by default, `--apply`
  (`healing/security/retention.py`, `scripts/retention.py`). Evidence:
  `tests/test_quality_ops.py`; `reports/run_logs/scripts.retention.txt`
  (dry run, 0 deletions).
- [x] **Alert model with evidence completeness** — required fields, severity
  routing, acknowledgement deadline, quarantine helper
  (`healing/alerts/model.py`). Evidence: `tests/test_alerts.py`;
  `benchmark/reports/alerts.log`.
- [x] **Alert senders** — console, file, Slack, Teams, Jira webhook senders;
  env-only secrets (`healing/alerts/routers.py`). Evidence:
  `tests/test_alerts.py`; `benchmark/reports/alerts.log` (console/file path
  exercised; webhook delivery itself is still unproven — see 2.1).

### 1.4 GitOps delivery

- [x] **Shadow mode** — records the diff/PR body it would produce and opens no
  PRs (`healing/orchestrator.py`). Evidence: `tests/test_shadow.py`;
  `benchmark/reports/shadow.md` (0 PRs, 0 escaped).

### 1.5 Non-UI / API sidecar

- [x] **API failure classifier** with API-specific classes
  (`healing/nonui/classifier.py`). Evidence: `tests/test_api_classifier.py`;
  `benchmark/reports/api.md` and `reports/evidence/2026-11-04/bench_api.txt`.
- [x] **Allowlisted API actions only** — `refresh_token`,
  `regenerate_fixtures`, `propose_test_update`; everything else escalates
  (`healing/nonui/healers.py`). Evidence: `tests/test_api_healers.py`;
  `benchmark/reports/api.md` (only those actions taken).
- [x] **Contract checks and schema diff** — shape, endpoint presence, required
  fields, type changes; Pact always escalates (`healing/nonui/schema_diff.py`,
  `healing/nonui/pipeline.py`). Evidence: `tests/test_schema_diff.py`,
  `tests/test_api_e2e.py`; `benchmark/reports/api.md` (0 contract heals).
- [x] **API shadow PR body + audit + explanation record**
  (`healing/nonui/pipeline.py`). Evidence: `tests/test_api_e2e.py` exercises
  the path; `benchmark/reports/api.json`, `records.jsonl`, and `audit.log`.
  Body content is not separately asserted; see 2.2.

### 1.6 Quality, metrics, and observability

- [x] **Benchmark metrics and reports** — accuracy, false-heal rate, confusion
  matrix, JSON + Markdown (`healing/quality/metrics.py`). Evidence:
  `tests/test_bench.py`, `tests/test_metrics.py`; `benchmark/reports/baseline.md`
  and `reports/run_logs/make-bench.txt`.
- [x] **Hash-pinned golden set** — CI fails if expectations are edited without
  re-pinning; limits from policy (`healing/quality/golden_set.py`). Evidence:
  `tests/test_golden.py`; `benchmark/reports/golden.md` (PASS).

### 1.7 Optional vision/LLM extension

- [x] **Deterministic visual fingerprints** — cosine-similarity shortlist from
  DOM-derived features (`healing/matching/vision.py`). Evidence:
  `tests/test_vision.py`; `benchmark/reports/vision.md`.
- [x] **Gated LLM proposal** — structured JSON only, masking before external
  calls, selector re-validated, default off (`healing/matching/llm_attempt.py`,
  `policy.yaml vision_llm`). Evidence: `tests/test_llm_attempt.py`;
  `benchmark/reports/vision.md` (“LLM disabled abstains: True”).
- [x] **Benchmark and verdict** — 15/15 vision top-1 but 15/15 ambiguous;
  attempts 3–4 add zero marginal heals; verdict DROP, left disabled
  (`docs/EXTENSION_VISION_LLM.md`). Evidence: `tests/test_ladder_vision.py`;
  `benchmark/reports/vision.md`.

### 1.8 Benchmarks, demo, and evidence

- [x] **Core 24-case UI benchmark** — 15 healable + 9 adversarial
  (`benchmark/cases.py`, `benchmark/wrong_heals.py`). Evidence:
  `tests/test_bench.py`; `benchmark/reports/baseline.md`.
- [x] **Healenium simulator benchmark** (`scripts/bench_healenium.py`).
  Evidence: `tests/test_bench_healenium.py`; `benchmark/reports/healenium.md`.
- [x] **Live Healenium benchmark** — pinned stack, 24 cases, live report.
  Evidence: `tests/test_live_healenium.py`; `benchmark/reports/healenium_live.md`
  (2026-10-08, historical; not re-run on 2026-11-04 because Docker was down).
- [x] **Golden-set benchmark** — 24 cases, accuracy 1.000, false-heal 0.000,
  PASS. Evidence: `tests/test_golden.py`; `benchmark/reports/golden.md`.
- [x] **API benchmark** — 7 cases, 0 auto-healed contract changes, 0 false
  heals. Evidence: `tests/test_api_e2e.py`; `benchmark/reports/api.md`.
- [x] **Held-out benchmark** — 35 unseen cases (24 UI + 11 API), labels fixed
  before running (`docs/HELDOUT.md`, `benchmark/heldout/`). Evidence:
  `tests/test_heldout.py`; `benchmark/reports/heldout.md` and
  `reports/evidence/2026-11-04/bench_heldout.txt`.
- [x] **Shadow-mode report** — 0 PRs opened, 0 escaped defects. Evidence:
  `tests/test_shadow.py`; `benchmark/reports/shadow.md`.
- [x] **Vision/LLM benchmark**. Evidence: `tests/test_vision.py`,
  `tests/test_ladder_vision.py`; `benchmark/reports/vision.md`.
- [x] **Demo app with UI and API drift modes** (`demo_app/app.py`,
  `demo_app/drift.py`, `demo_app/api_drift.py`). Evidence:
  `benchmark/test_demo.py`, `tests/test_api_e2e.py`;
  `reports/evidence/2026-11-04/demo.txt`.

### 1.9 Infrastructure and tooling

- [x] **Pinned Docker Compose stack** — Postgres, Healenium backend/proxy,
  selector-imitator, Selenium hub + Chrome node, demo app
  (`infra/docker-compose.yml`). Evidence: `tests/test_live_healenium.py`
  (compose assertions); `benchmark/reports/healenium_live.md`.
- [x] **Make targets and Windows equivalents** — test, lint, every bench,
  gates, demo (`Makefile`, `tasks.py`). Evidence: `tests/test_bench_wiring.py`;
  `reports/run_logs/make-*.txt` and `reports/evidence/2026-11-04/*`.
- [x] **Demo-case benchmark covers all 24 pre-registered cases** — the bench
  runs the 12 base cases plus the 12 hard cases against `cases.yaml`.
  `tests/test_demo_cases_bench.py` asserts 24 rows, 0 pipeline false heals,
  and 0 wrong escalations. Evidence:
  `reports/evidence/2026-11-05/demo_cases.txt` (24/24).
- [x] **One-command presentation demo** — `scripts/demo.py` / `tasks.py demo`.
  `tests/test_demo_script.py` runs it as a subprocess and asserts 24 case
  rows plus both XAI records. Evidence:
  `reports/evidence/2026-11-05/demo.txt` (24/24, exit 0).
- [x] **Read-only operator dashboard** — `healing/dashboard/app.py` renders
  quality gates, the newest explanation records, and the latest saved
  metrics snapshot. It is GET-only, masks/escapes displayed text, hash-checks
  records, and binds to localhost. Evidence: `tests/test_dashboard.py`;
  `reports/evidence/2026-11-06/dashboard.jpeg` and `dashboard.txt`
  (11 PASS / 0 FAIL / 1 UNVERIFIED plus two diagnostics; 25 of 7996
  records).

### 1.10 Tests and documentation

- [x] **204 tests passing** on Python 3.12.10, including classifier, matcher,
  Critic, policy, orchestrator, sandbox, XAI, alerts, GitOps, API sidecar,
  held-out set, gates, dashboard, runbook, and metrics (**MEASURED
  2026-11-06**). Evidence: the suite itself;
  `reports/evidence/2026-11-06/pytest.txt` (204 passed, exit 0).
- [x] **Lint/type checks clean** — ruff check, ruff format, mypy (**MEASURED
  2026-11-04**). Evidence: `reports/evidence/2026-11-04/lint.txt` (exit 0/0/0).

### 1.11 Quality evidence snapshot (2026-11-05)

`scripts/evidence_snapshot.py` (tested by `tests/test_evidence_snapshot.py`)
writes one reproducible in-process transcript. Artifacts:
`reports/evidence/2026-11-05/quality_snapshot.json` and
`quality_snapshot.txt`. GitOps uses a temporary local bare repo; no network,
Docker, or real GitHub credentials are involved.

- [x] **PII/secret masking** — email, phone, card, and token markers in the
  saved transcript (`tests/test_masking.py`).
- [x] **GitHub App client** — branch, commit, PR, labels, and comments from a
  recorded local bare-repo run (not a real GitHub call).
- [x] **AST locator edits** — saved unified diff and edited source
  (`tests/test_ast_edit.py`).
- [x] **PR template** — rendered PR body with all required sections
  (`tests/test_pr_dedupe_watch.py`).
- [x] **Shared-locator dedupe** — grouped failures and one-PR-per-locator plan.
- [x] **Post-merge watcher** — revert PR record plus alert transcript.
- [x] **Assertion/threshold guard** — blocked removed/weakened/threshold diffs
  and an allowed strengthening (`tests/test_api_healers.py`).
- [x] **Narrative renderer** — rendered text plus consistency check
  (`tests/test_narrative.py`).
- [x] **Calibration** — reliability curve, good/bad ECE, and alarm decision
  (`tests/test_quality.py`).
- [x] **Autonomy guard** — L3 to L2 downgrade with alert payload
  (`tests/test_quality.py`).
- [x] **OpenTelemetry/Prometheus** — exported healing metric samples
  (`tests/test_quality_ops.py`).

## 2. Implemented but not fully verified/shipped (33)

### 2.1 Existing partials (13)

- [~] **Live adversarial containment** — pipeline escalates all 9 adversarial
  cases, but the raw live matcher heals 9/9; proven on one 24-case, single-seed
  run and attempts 2+ were never exercised live (`docs/E2E_LIVE.md`).
- [~] **Live Healenium validation** — measured once on the pinned stack; no
  repeat run after host/Docker changes; latency target is still sim-era 100 ms.
- [~] **GitOps end-to-end** — tested against a local bare repo only; no real
  GitHub App install, live heal PR, or live revert PR.
- [~] **Alert delivery** — senders implemented; only console/file exercised;
  no real Slack/Teams/Jira delivery.
- [~] **Observability deployment** — OTel/Prometheus instrumentation exists;
  no exporter, scrape config, or running Grafana; dashboard JSON is unverified.
- [~] **Screenshot evidence** — alert/PR screenshot fields hold placeholder
  paths; no screenshots are captured anywhere.
- [~] **API endpoint coverage** — `observe()` handles three endpoints;
  `GET /api/cart` falls into the unknown-endpoint branch. Root cause in
  `docs/TOKEN_CART_ANALYSIS.md`; fix needs human approval.
- [~] **Sandbox isolation** — in-process replay and staging overlay exist, but
  no egress-restricted container ran in CI.
- [~] **Held-out independence** — expectations were fixed before running, but
  the author had prior pipeline exposure; not double-blind
  (`docs/HELDOUT_PROVENANCE.md`).
- [~] **CI verification** — workflows authored; GitHub Actions results were
  never observed from this machine. The local `gates` run now passes
  (11/0/1), but real CI remains unobserved.
- [~] **Compliance tooling** — SBOM, retention, masking, and audit exist, but
  the SBOM license allowlist is unused and no CI step enforces it.
- [~] **Vision/LLM extension** — code and benchmark complete; verdict is DROP
  because there are no real screenshots and attempts 1–2 already win.
- [~] **Documentation surface** — docs are extensive and `README.md` now has
  quickstart, architecture, commands, evidence links, and limits, but most
  docs still have no executable check.

### 2.2 Downgraded by the 2026-11-04 audit (19)

Each item is implemented and/or tested, but lacks one of the two required
proofs. The reason names the missing half.

- [~] **Survival metrics** — tested (`tests/test_quality.py`), but the gate
  remains UNVERIFIED (`insufficient_data`); the snapshot records the status
  without inventing history.
- [~] **Live end-to-end pipeline run** — artifact exists
  (`benchmark/reports/e2e_live.md`), but no pytest test covers the live
  pipeline.
- [~] **Committed run logs** — logs exist under `reports/run_logs/`, but this
  is a documentation claim, not an executable check.
- [~] **Sandbox overlay documentation** — `infra/sandbox.overlay.yml` is
  documented, but no test or run uses the overlay.
- [~] **SBOM generator and committed `sbom.json`** — generator tested and
  output saved (`reports/run_logs/scripts.sbom.txt`), but `sbom.json` is
  gitignored (`.gitignore` line 29), so it is **not committed** as claimed.
- [~] **CI workflows authored** — workflow YAML exists, but no CI run was
  observed and no local test executes the workflows.
- [~] **Pre-commit hooks** — config exists, but the hooks were never executed
  here and no artifact records a run.
- [~] **Apache-2.0 notices** — `NOTICE` / `THIRD_PARTY_NOTICES.md` exist, but
  no test or artifact verifies their contents.
- [~] **Architecture and ADRs** — documentation only; no executable check.
- [~] **Quality targets** — documentation only; target values live in prose
  and `policy.yaml`, with no test that pins every documented value.
- [~] **Gate review, known red gates, live-vs-sim docs** — analysis docs only;
  the underlying gate transcript exists but no test asserts the docs match it.
- [~] **Healenium setup and live runbook** — documentation only; no test.
- [~] **Provenance records** — documentation only; independence is a statement,
  not an executable check.
- [~] **Frozen-file hash manifest and changelog** — the manifest is now
  automated by `tests/test_frozen_hashes.py`; `CHANGELOG_FROZEN.md` is still
  documentation-only and has no executable check.
- [~] **Compliance evidence, license options, branch protection, sign-off
  checklist** — documentation/human-decision items; no executable check and
  no boxes ticked.
- [~] **Spike reports** — documentation only; no executable check.
- [~] **Deferral record for chatbot/MCP** — documentation only; no code.
- [~] **Regenerated `PROJECT_STATUS.md`** — documentation only; no test.
- [~] **This `TODO.md`** — documentation only; no test.

### 2.3 New partial from this session (1)

- [~] **CODEOWNERS** — `.github/CODEOWNERS` added, but every `@your-org/...`
  handle is a placeholder and required review is not enabled. Needs a human
  owner decision before branch protection can rely on it.

## 3. Open work by priority

Effort scale: **S** < 1 day · **M** 2–5 days · **L** 1–2 weeks · **XL** > 2
weeks. Human-only decisions are marked; no sign-off box is ticked here.

### P0 — before the presentation (4 done, 1 open)

- [x] **P0.1 Rehearse the demo and gates** — run `python tasks.py demo`,
  `python -m scripts.check_gates`, and the held-out bench; save fresh logs
  under `reports/evidence/2026-11-04/`. Evidence: `p0-demo.txt` (24/24, exit
  0), `p0-gates.txt` (8 PASS / 2 FAIL / 2 UNVERIFIED, exit 1 expected),
  `p0-heldout.txt` (UI 24/24, API 10/11), `p0-verify.txt` (catch 1.0), and
  `p0-pytest.txt` (178 passed). Repeat on the presentation machine if it is
  not this host. **S**.
- [x] **P0.2 Walk `docs/EVIDENCE_INDEX.md` line by line** — every number was
  re-checked against its command/artifact; red gates and UNVERIFIED items
  remain visible; the frozen table and rehearsal section were refreshed.
  Evidence: `docs/EVIDENCE_INDEX.md`. **S**.
- [x] **P0.3 Expand `README.md`** — quickstart, architecture flow, command
  table, evidence pointers, and current limits. Evidence:
  `tests/test_readme.py` (checks required sections and links) and the README
  itself. **S**.
- [x] **P0.4 Freeze the held-out case files and automate the hash check** —
  `benchmark/heldout/ui_cases.py` and `api_cases.py` are in
  `docs/FROZEN_HASHES.md`; `tests/test_frozen_hashes.py` recomputes every
  listed hash and fails closed. Evidence:
  `reports/evidence/2026-11-04/frozen-hashes.txt` (7/7 MATCH) and the test.
  **S**.
- [ ] **P0.5 Re-run the live Healenium and live E2E benches if Docker is
  available** — otherwise present the 2026-10-08 results explicitly as
  historical/UNVERIFIED, not as fresh measurements. **M**.

### P1 — before merge to main (14 open, 4 done)

- [x] **P1.1 Resolve `false_heal_rate_adversarial`** — human-approved
  2026-11-06: gate the shipped orchestrator path from `e2e_live.json`
  (`adversarial_fhr = 0.0`; all 9 adversarial cases escalate). Raw matcher FHR
  1.0 stays visible as a non-gating diagnostic. Evidence:
  `reports/evidence/2026-11-06/gates.txt` (11/0/1, exit 0),
  `gates-strict.txt`, and `tests/test_check_gates.py`. **M**.
- [x] **P1.2 Resolve `latency_per_heal_ms`** — human-approved 2026-11-06:
  gate `pipeline_latency_ms` (mean `pipeline_ms` = 19.99 ms, target 100 ms).
  Browser latency 1122.08 ms stays visible as a non-gating diagnostic.
  Evidence: same artifacts; `docs/TARGETS.md` and `docs/GATE_REVIEW.md`
  record the measurement correction. **M**.
- [x] **P1.3 Produce `benchmark/reports/golden_live.json`** so
  `heal_accuracy [live]` is verified instead of UNVERIFIED.
  `scripts/bench_golden_live.py` derives it from the measured live E2E report
  and refuses a source that is not marked `"live": true`; `tests/test_golden_live.py`
  covers the mapping and rejects simulated/empty/bad input. Evidence:
  `reports/evidence/2026-11-05/bench_golden_live.txt` and `golden_live.json`
  (24 cases, accuracy 1.0), `gates-after-golden-live.txt` (9 PASS / 2 FAIL /
  1 UNVERIFIED). The accuracy is from the **historical 2026-10-08** run, not
  a fresh stack run. **M**.
- [ ] **P1.4 Fix the `token-cart` observer gap generally** — registry or
  TestClient dispatch in `observe()`, plus an explicit observer-gap escalation
  reason; add the seven fresh cases in `docs/TOKEN_CART_ANALYSIS.md`; target
  held-out API 11/11. **Needs human approval.** **M**.
- [ ] **P1.5 Exercise live attempts 2–4** — every live heal so far won on
  attempt 1; build cases that force the ladder. **M**.
- [ ] **P1.6 Capture real before/after/candidate screenshots** and feed them
  into alerts, PRs, and retention instead of placeholder paths. **M**.
- [ ] **P1.7 Observe CI green on Python 3.12** for `lint-test`, `golden`,
  `compliance`, and `gates`; the local `gates` run now passes after
  P1.1/P1.2, but the real GitHub Actions run remains unobserved. **M**.
- [ ] **P1.8 Install the GitHub App and open one real heal PR and one revert
  PR** — verify branch protection, required checks, and replace the CODEOWNERS
  placeholders with real teams. **L**.
- [ ] **P1.9 Smoke-test Slack/Teams/Jira delivery** with real webhook URLs from
  environment variables. **S**.
- [ ] **P1.10 Close the missing test/artifact debt from section 2.2** —
  remaining minimum: live E2E, survival history, and the frozen changelog;
  the deterministic artifact debt is covered by
  `scripts/evidence_snapshot.py`. **M**.
- [x] **P1.11 Write the operator runbook** — stack start/stop, secret rotation,
  failed-heal recovery, retention/apply. `docs/OPERATOR_RUNBOOK.md` states
  the dry-run rollback, the Postgres data-loss warning, the retention
  schedule, and the unverified external integrations. Evidence:
  `tests/test_operator_runbook.py`; `reports/evidence/2026-11-06/runbook.txt`.
  **M**.
- [ ] **P1.12 Enforce the SBOM license allowlist in CI** — `scripts/sbom.py`
  defines it but never checks it; add `pip-licenses` or equivalent. **S**.
- [ ] **P1.13 Replace the grep-based secret scan** with gitleaks/trufflehog if
  the project will be distributed. **S**.
- [ ] **P1.14 Activate the survival gate or record a formal deferral** once 30
  days of heal history exists (today it reports `insufficient_data`). **S**.
- [ ] **P1.15 Choose the project license** — MIT recommended; update `LICENSE`
  and `pyproject.toml` (`license = "TBD"` today). **Human decision. S**.
- [ ] **P1.16 Complete legal review and the vendor/subprocessor register** —
  data handling, DPAs, regions/owners for GitHub, Docker Hub, PyPI, Slack,
  Teams, Jira, and the self-hosted stack. **Human decision. M**.
- [ ] **P1.17 Approve the 12 quality targets** in `docs/HUMAN_SIGNOFF.md` —
  all boxes remain unchecked; agents may not tick them. **Human decision. S**.
- [ ] **P1.18 Confirm release blockers and cut the next tag** — live
  containment re-verified, held-out measured, survival decided, CI green
  observed. **S** after P1.1–P1.7.

### P2 — production (5)

- [ ] **P2.1 Implement runner adapters** — ingest real pytest/Selenium/API-suite
  failures into `FailureSignals` / `ApiFailure`; `healing/adapters/` is still a
  documented placeholder. **XL**.
- [ ] **P2.2 Deploy Prometheus scraping and the Grafana dashboard** — today
  only in-process metrics and an unverified dashboard JSON exist. **M**.
- [ ] **P2.3 Schedule the retention job** (cron/CI) and alert on job failure;
  it currently runs manually/dry-run only. **S**.
- [ ] **P2.4 Vision/LLM revisit** — only with real screenshots and a benchmark
  where attempts 1–2 demonstrably fail; current verdict is DROP/disabled. **L**.
- [ ] **P2.5 Chatbot/MCP assistant** — **DEFERRED**; revisit only when the four
  criteria in `docs/EXTENSION_CHATBOT.md` hold. No code exists. **XL if
  revived**.

## 4. Delivered by the 2026-11-04/05 evidence sessions

These are process/documentation deliverables, listed without `[x]` markers so
they do not inflate the verified-feature count:

- `docs/EVIDENCE_INDEX.md` with command, artifact, date, and label per claim.
- `docs/TOKEN_CART_ANALYSIS.md` plus the probe transcript.
- `docs/HELDOUT_PROVENANCE.md` augmentation (expectations-before-run and demo
  provenance).
- `docs/FROZEN_HASHES.md` re-verification section and evidence hash log.
- Bench wiring (`Makefile`, `tasks.py`, `tests/test_bench_wiring.py`) — this
  one **is** counted as `[x]` in section 1.9.
- `healing/adapters/README.md` and `.github/CODEOWNERS` (placeholders).
