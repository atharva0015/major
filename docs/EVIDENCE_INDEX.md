# Evidence index (2026-11-04)

Every headline claim in `PROJECT_STATUS.md` with its exact command, output
artifact, date, provenance label, and the result of re-running it on
2026-11-04. Labels: **MEASURED** (real run), **SIMULATED** (simulator or
in-process replay), **UNVERIFIED** (not observed / input missing).

Environment: Windows host, `.venv312` (Python 3.12.10), `make` absent.
Commands shown as `python` were run as
`.venv312/Scripts/python.exe -m ...`; the full invocation is recorded at the
top of each log under `reports/evidence/2026-11-04/`. Docker was **not
running** (`npipe:////./pipe/dockerDesktopLinuxEngine` unavailable), so
live-stack commands could not be repeated.

## Artifact durability

`benchmark/reports/*.md|json|log|jsonl` are regenerated and gitignored by
design (`.gitignore` lines 23-28). To keep the evidence durable, this
session wrote the command output to `reports/evidence/2026-11-04/`, which
is committed. Tracked docs (`docs/HELDOUT.md`, `docs/LIVE_VS_SIM.md`,
`docs/E2E_LIVE.md`) also carry the historical summaries.

## Headline claims

| # | Claim | Exact command | Output artifact | Date | Label | Re-run 2026-11-04 |
|---|---|---|---|---|---|---|
| 1 | 175 tests pass | `python -m pytest -q` | `reports/evidence/2026-11-04/pytest.txt` | 2026-11-04 | MEASURED | **MATCH** — 175 passed in 15.12 s (count same; runtime varies) |
| 2 | Demo 24/24 match, exit 0 | `python tasks.py demo` | `reports/evidence/2026-11-04/demo.txt` (console table) | 2026-11-04 | SIMULATED | **MATCH** — 24 rows, all expected/pipeline pairs equal, exit 0 |
| 3 | Held-out UI 24/24, accuracy 1.000, FHR 0.000 | `python -m scripts.bench_heldout` | `benchmark/reports/heldout.json` + `.md` (ignored); `reports/evidence/2026-11-04/bench_heldout.txt`; tracked `docs/HELDOUT.md` | 2026-10-14; re-run 2026-11-04 | MEASURED | **MATCH** — report hash unchanged; `ui_accuracy=1.0`, `ui_false_heal_rate=0.0`, `ui_escaped=0` |
| 4 | Held-out API 10/11 | `python -m scripts.bench_heldout` | same as #3 | 2026-10-14; re-run 2026-11-04 | MEASURED | **MATCH** — still 10/11; `heldout:token-cart` remains the one miss |
| 5 | Healenium live: accuracy 1.000, FHR 0.375, adversarial 9/9, 1122 ms | `python -m scripts.bench_healenium_live` | `benchmark/reports/healenium_live.json` + `.md` (ignored); tracked summary `docs/LIVE_VS_SIM.md` | 2026-10-08 | MEASURED (historical) | **NOT RE-RUN** — Docker unavailable; the gate and index still read the unchanged 2026-10-08 report. **UNVERIFIED now.** |
| 6 | Critic catch rate 1.000 | `python -m scripts.bench_verify` | `benchmark/reports/verify.json` + `.md` (ignored); `reports/evidence/2026-11-04/bench_verify.txt` | 2026-10-14; re-run 2026-11-04 | SIMULATED | **MATCH** — report hash unchanged; `catch_rate=1.0`, `false_reject_rate=0.0`, `false_heal_rate=0.0` |
| 7 | Gate result 8 PASS / 2 FAIL / 2 UNVERIFIED | `python -m scripts.check_gates` | `reports/evidence/2026-11-04/check_gates.txt` | 2026-11-04 | MEASURED | **MATCH** — same statuses and values; exit 1 |
| 8 | Live E2E pipeline 24/24, 0 false heals, 0 escaped | `python -m scripts.bench_e2e_live` | `benchmark/reports/e2e_live.json` + `.md` (ignored); tracked summary `docs/E2E_LIVE.md` | 2026-10-08 | MEASURED (historical) | **NOT RE-RUN** — Docker unavailable; **UNVERIFIED now.** |

## Gate-by-gate evidence

The gate command is the same for every row: `python -m scripts.check_gates`.
The source column is the report the checker reads.

| Gate | Source artifact | Date | Label | Re-run result |
|---|---|---|---|---|
| `heal_accuracy` (`>= 0.95`) | `benchmark/reports/golden_live.json` — **missing** | — | UNVERIFIED | Still UNVERIFIED. **No script in the repo generates this file.** |
| `false_heal_rate_overall` (`= 0.0`) | `benchmark/reports/verify.json` | 2026-11-04 re-run | SIMULATED | PASS — 0.0; hash unchanged |
| `false_heal_rate_adversarial` (`= 0.0`) | `benchmark/reports/healenium_live.json` | 2026-10-08 | MEASURED | FAIL — 1.0; input unchanged, live re-run blocked |
| `critic_catch_rate` (`>= 0.9`) | `benchmark/reports/verify.json` | 2026-11-04 re-run | SIMULATED | PASS — 1.0; hash unchanged |
| `critic_false_reject_rate` (`<= 0.05`) | `benchmark/reports/verify.json` | 2026-11-04 re-run | SIMULATED | PASS — 0.0; hash unchanged |
| `classification_accuracy` (`>= 0.95`) | `benchmark/reports/decision.json` | 2026-11-04 re-run | SIMULATED | PASS — 1.0; hash unchanged |
| `genuine_passed_to_heal` (`= 0`) | `benchmark/reports/decision.json` | 2026-11-04 re-run | SIMULATED | PASS — 0; hash unchanged |
| `contract_healed` (`= 0`) | `benchmark/reports/api.json` | 2026-11-04 re-run | SIMULATED | PASS — 0; hash unchanged |
| `cost_per_heal` (`<= 2.0`) | `benchmark/reports/healenium_live.json` | 2026-10-08 | MEASURED | PASS — 1.0; input unchanged, live re-run blocked |
| `latency_per_heal_ms` (`<= 100`) | `benchmark/reports/healenium_live.json` | 2026-10-08 | MEASURED | FAIL — 1122.08; input unchanged, live re-run blocked |
| `alert_completeness` (`= 1.0`) | `tests/test_alerts.py` (subgate) | 2026-11-04 | MEASURED | PASS — tests green |
| `heal_survival_rate` (TBD) | none — `healing/quality/survival.py` reports `insufficient_data` | — | UNVERIFIED | Still UNVERIFIED. **No history and no command can produce it.** |

## Supporting benchmark re-runs

| Benchmark | Exact command | Artifact | Re-run result |
|---|---|---|---|
| Baseline healer | `python -m scripts.bench` | `benchmark/reports/baseline.json` + `.md` | MATCH — hash unchanged |
| Decision layer | `python -m scripts.bench_decision` | `benchmark/reports/decision.json` + `.md` | MATCH — hash unchanged; accuracy 1.0 |
| Critic verify | `python -m scripts.bench_verify` | `benchmark/reports/verify.json` + `.md` | MATCH — hash unchanged; catch 1.0 |
| API benchmark | `python -m scripts.bench_api` | `benchmark/reports/api.json` + `.md` | MATCH — hash unchanged; 0 contract heals |
| Golden set | `python -m scripts.bench_golden` | `benchmark/reports/golden.json` + `.md` | MATCH — hash unchanged; PASS |
| Healenium simulator | `python -m scripts.bench_healenium` | `benchmark/reports/healenium.json` + `.md` | MATCH on headline numbers; hash changed only the sub-ms latency field (0.0283 ms) |
| Held-out | `python -m scripts.bench_heldout` | `benchmark/reports/heldout.json` + `.md` | MATCH — hash unchanged |
| Demo cases | `python -m scripts.bench_demo_cases` | `benchmark/reports/demo_cases.json` + `.md` | MATCH — hash unchanged; 24/24 |
| Vision/LLM | `python -m scripts.bench_vision` | `benchmark/reports/vision.json` + `.md` | MATCH on verdict/counts; hash changed only vision latency (0.225 ms vs 0.100 ms) |
| Shadow mode | `python -m scripts.shadow_report` | `benchmark/reports/shadow.json` + `.md` | MATCH — hash unchanged; 0 PRs, 0 escaped |
| Live Healenium | `python -m scripts.bench_healenium_live` | `benchmark/reports/healenium_live.json` + `.md` | **BLOCKED** — Docker daemon unavailable |
| Live E2E | `python -m scripts.bench_e2e_live` | `benchmark/reports/e2e_live.json` + `.md` | **BLOCKED** — Docker daemon unavailable |

Every command above was run from the repo root with
`.venv312/Scripts/python.exe`. Gate and pytest stdout is saved under
`reports/evidence/2026-11-04/`; bench stdout is also saved there for the
rows that were re-run.

## Frozen-file check (2026-11-04)

Command: `git hash-object <file>` for each frozen file. Full output:
`reports/evidence/2026-11-04/frozen-hashes.txt`.

| File | Recomputed hash | Matches `docs/FROZEN_HASHES.md`? |
|---|---|---|
| `healing/classifier/rules.py` | `979914fd77151753b62072c885ed3a764e5834f6` | YES |
| `healing/critic/checks.py` | `b4967ea84dba703db4bc7b25df3122e9bd497818` | YES |
| `healing/policy/policy.yaml` | `31cdbd25d75113f26628dea55fe2f2f43035be4e` | YES |
| `benchmark/cases.py` | `d387369429e4fa0d18a47cbda7576c3252d16220` | YES |
| `benchmark/api/cases.py` | `0588789ac15f7385d26d3360f2da279ed047b276` | YES |

**No differences.** Two documentation gaps remain, flagged not fixed:

1. `docs/FROZEN_HASHES.md` still says "No `benchmark/heldout/` exists yet"
   (line 17), although the directory was added on 2026-10-14. The held-out
   case files are not listed or hash-pinned.
2. The freeze record says "166 passed" (line 4); the current suite is 175.

## Claims with no reproducible command

These are flagged as **UNVERIFIED** or procedural; do not cite them as
measured:

- `heal_accuracy [live]` — the checker consumes `golden_live.json`, but no
  script produces it. The only live-looking accuracy command is
  `bench_e2e_live`, which writes a different report and requires Docker.
- `heal_survival_rate` — no history store and no command; the code reports
  `insufficient_data`.
- Held-out and demo **independence** — the provenance docs are statements
  about authoring, not executable checks. The reps cannot prove blindness
  (`docs/HELDOUT_PROVENANCE.md`, `docs/DEMO_PROVENANCE.md`).
- Real GitHub App PR/revert, real Slack/Teams/Jira delivery, real screenshot
  capture, and Prometheus/Grafana deployment — no command or artifact
  exists; these are roadmap items, not measured claims.
- Human sign-offs and license/DPA decisions — human decisions, not
  commands; all boxes in `docs/HUMAN_SIGNOFF.md` remain unchecked.
