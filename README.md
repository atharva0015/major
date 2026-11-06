# Self-Healing Test Framework

Fail-closed self-healing for UI and API test failures, built as a reference
MVP in Python 3.12. The deterministic core classifies, scores, gates, and
performs Git operations; models only propose candidates. Unknown,
low-confidence, conflicting, or contract-changing results fail the test and
escalate to a human.

The current evidence set is in [`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md).
It labels every number **MEASURED**, **SIMULATED**, or **UNVERIFIED** and
links the command and artifact behind it. The open-work backlog is
[`TODO.md`](TODO.md), split into P0/P1/P2.

New to the project? Start with
[`docs/PROJECT_EXPLAINED.md`](docs/PROJECT_EXPLAINED.md), a plain-English
guide to how it works, what is real, and what the end user experiences.

## Quickstart

Requires Python 3.12. No Docker, browser, or network is needed for the
tests or the one-command demo.

Windows:

```powershell
py -3.12 -m venv .venv312
.venv312\Scripts\python -m pip install -e ".[dev]"
.venv312\Scripts\python tasks.py test
.venv312\Scripts\python tasks.py demo
.venv312\Scripts\python tasks.py dashboard
```

Unix:

```bash
python3.12 -m venv .venv312
.venv312/bin/python -m pip install -e ".[dev]"
.venv312/bin/python tasks.py test
.venv312/bin/python tasks.py demo
.venv312/bin/python tasks.py dashboard
```

Open <http://127.0.0.1:8080> for the read-only dashboard. `tasks.py gates`
is optional in the quickstart: it currently exits 0 with **11 PASS / 0 FAIL
/ 1 UNVERIFIED**. `tasks.py gates-strict` exits 1 until the survival gate
has history or a written waiver, so release checks cannot ignore missing
evidence.

If `make` is installed, the same targets are available as `make test` and
`make demo`. `tasks.py` is the Windows-friendly equivalent of every Makefile
target and always runs through the active interpreter.

## What the demo shows

`tasks.py demo` runs 24 pre-registered drift scenarios through the full
in-process pipeline and prints the pipeline choice, the Healenium simulator
alone, and the layered Critic verdict. It ends with two complete structured
explanation records: one heal and one escalation.

Everything in the demo is **SIMULATED** (in-process HTML plus the simulator).
It is designed to show the decision path, not to claim live-browser results.
The demo takes seconds.

## Commands

| Command | What it runs |
|---|---|
| `python tasks.py test` | Full pytest suite |
| `python tasks.py lint` | ruff check, ruff format check, mypy |
| `python tasks.py demo` | 24-case presenter demo, two XAI records |
| `python tasks.py gates` | Quality gates from the saved reports (currently 11/0/1, exit 0) |
| `python tasks.py gates-strict` | Quality gates; UNVERIFIED also exits 1 |
| `python tasks.py bench` | Baseline benchmark plus Critic verify |
| `python tasks.py bench-heldout` | Held-out UI + API cases |
| `python tasks.py bench-demo-cases` | External mini-demo cases |
| `python tasks.py bench-decision` | Classification accuracy + fail-closed gate proof |
| `python tasks.py bench-golden` | Hash-pinned golden set |
| `python tasks.py bench-golden-live` | Derive live `golden_live.json` from a measured live E2E report |
| `python tasks.py bench-api` | API sidecar, zero contract heals |
| `python tasks.py bench-healenium` | Healenium simulator |
| `python tasks.py bench-healenium-live` | Live Healenium (Docker required) |
| `python tasks.py bench-e2e-live` | Live end-to-end pipeline (Docker required) |
| `python tasks.py bench-shadow` | Shadow-mode report |
| `python tasks.py bench-vision` | Vision/LLM extension benchmark |
| `python tasks.py evidence-snapshot` | Deterministic quality transcript (masking, narrative, calibration, guard, GitOps) |
| `python tasks.py dashboard` | Local read-only dashboard (gates, records, metrics) at http://127.0.0.1:8080 |
| `python tasks.py studio` | Modern Web UI for uploading, auto-healing, and optimizing any codebase at http://127.0.0.1:8081 |

## Codebase Healing & Optimality Studio

`python tasks.py studio` serves the interactive modern Web Studio at <http://127.0.0.1:8081>.
It enables developers and QA engineers to:
- **Upload any codebase** as a `.zip` file or run instant one-click analysis using the built-in demo project.
- **Autonomous Bug Healing**: Scans for syntax errors, runtime crashes, mutable default parameters, unclosed file descriptors, and failing tests. It synthesizes optimal patches (using local free LLMs via Ollama or deterministic rule-based AST synthesis), verifies them in an isolated sandbox, and presents interactive unified split diffs.
- **Code Optimality Engine**: Detects algorithmic complexity bottlenecks ($O(N^2) \rightarrow O(N)$), linear collection searches, string concatenation in loops, and unmemoized recursion; measures before/after execution speedups; and enforces strict Critic regression guards.
- **Download Optimized Codebase**: One-click export of the clean, repaired, and benchmark-optimized codebase as a `.zip` archive.

## Read-only dashboard

`python tasks.py dashboard` serves a local page showing the quality gates,
the newest 25 explanation records, and the latest saved metrics snapshot.
It is GET-only, masks PII, escapes displayed text, and never heals or
writes. It has no authentication, so bind it to localhost only. See
`docs/DASHBOARD.md` for routes, data sources, and limits.

## How it works

```text
failing test
  -> adapters        normalize runner output (UI signals / API failure)
  -> classifier      deterministic class + probabilities
  -> matching        Healenium candidates, transparent rescorer
  -> sandbox         in-process replay of up to three attempts
  -> critic          deterministic, state, network, intent checks
  -> policy          confidence, ambiguity margin, blocked classes, budgets
  -> xai             structured explanation record first, narrative second
  -> alerts/gitops   escalation or shadow/reviewed PR
```

Safety invariants:

- Genuine regressions, environment faults, contract changes, removed or
  weakened assertions, and performance thresholds never reach the heal engine.
- A sandbox pass alone never approves a heal; the layered Critic must also
  pass, and an optional LLM cannot override a failed deterministic check.
- Every heal stores model, prompt, policy, and config versions for replay.
- Secrets come from environment variables; PII is masked before any external
  call.
- Unknown or malformed input escalates; it never guesses.

## Current limits (say these out loud)

- The **raw live Healenium matcher** still heals all 9 adversarial cases.
  That is a **non-gating diagnostic**: the gate measures the shipped
  orchestrator path, which escalates all 9 (`adversarial_fhr = 0.0`).
- **Browser latency** is 1122 ms per heal. That is also a diagnostic; the
  gate measures orchestrator overhead (`pipeline_latency_ms`, ~20 ms).
- `heal_accuracy [live]` **PASSES** at 1.0 only because
  `scripts/bench_golden_live.py` derives `benchmark/reports/golden_live.json`
  from the historical 2026-10-08 live E2E report. It does not re-run the
  stack; treat it as measured-but-stale until Docker is available.
- Held-out API is **10/11**; `heldout:token-cart` misses because `observe()`
  lacks a `GET /api/cart` dispatch. Root cause and proposed fix:
  [`docs/TOKEN_CART_ANALYSIS.md`](docs/TOKEN_CART_ANALYSIS.md).
- `healing/adapters/` is a documented placeholder; there is no real runner
  ingestion yet.
- Real GitHub App PRs, Slack/Teams/Jira delivery, screenshot capture, and
  Prometheus/Grafana deployment have **not** been observed.
- Live benches need Docker; when it is unavailable they are historical and
  must be labelled that way.
- The project license is **TBD**; the package is not distributable until a
  human chooses one.

## Repository map

| Path | Contents |
|---|---|
| `healing/` | Classifier, matcher, sandbox, Critic, policy, XAI, alerts, GitOps, API sidecar, quality tooling |
| `benchmark/` | Core 24-case benchmark, held-out cases, demo cases, wrong-heal set |
| `demo_app/` | FastAPI demo app with UI and API drift injection |
| `scripts/` | Benchmarks, gates, demo, replay, retention, SBOM |
| `tests/` | Pytest suite, including evidence-integrity checks |
| `docs/` | Architecture, ADRs, targets, evidence index, provenance, sign-off |
| `reports/` | Committed run logs and dated evidence transcripts |

## Documentation

- [`docs/PROJECT_EXPLAINED.md`](docs/PROJECT_EXPLAINED.md) — plain-English project guide, including the end-user view.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — components and flow.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — ADRs, including fail-closed rules.
- [`docs/TARGETS.md`](docs/TARGETS.md) — quality targets and rationale.
- [`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md) — claim → command → artifact.
- [`docs/HUMAN_SIGNOFF.md`](docs/HUMAN_SIGNOFF.md) — decisions reserved for humans.
- [`docs/OPERATOR_RUNBOOK.md`](docs/OPERATOR_RUNBOOK.md) — start/stop, secret rotation, recovery, retention.
- [`TODO.md`](TODO.md) — P0/P1/P2 open work with effort estimates.

Apache-2.0 notices for reused Healenium code are in [`NOTICE`](NOTICE) and
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
