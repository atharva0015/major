# Project Explained in Simple English

**Self-Healing Test Framework - a plain-language guide**

This document explains what the project does, how it works, what is already
built, what is still missing, and how to run it. It avoids deep technical
jargon where possible and explains the important terms along the way.

---

## Contents

1. [What is this project?](#1-what-is-this-project)
2. [The problem it solves](#2-the-problem-it-solves)
3. [The big idea: careful, not clever](#3-the-big-idea-careful-not-clever)
4. [How it works, step by step](#4-how-it-works-step-by-step)
   - [4.1 What the end user actually experiences](#41-what-the-end-user-actually-experiences)
5. [A concrete example](#5-a-concrete-example)
6. [What happens when it is not safe](#6-what-happens-when-it-is-not-safe)
7. [The main parts of the system](#7-the-main-parts-of-the-system)
8. [What is already built](#8-what-is-already-built)
9. [What is real, simulated, or unverified](#9-what-is-real-simulated-or-unverified)
10. [Current status and known limits](#10-current-status-and-known-limits)
11. [How to run the demo](#11-how-to-run-the-demo)
12. [The read-only dashboard](#12-the-read-only-dashboard)
13. [Repository map](#13-repository-map)
14. [Glossary](#14-glossary)
15. [What is still pending](#15-what-is-still-pending)
16. [The one-sentence summary](#16-the-one-sentence-summary)

---

## 1. What is this project?

This is a **self-healing layer for automated tests**.

Automated tests often fail for a boring reason: the website changed a small
detail, but the feature still works. For example, a test says:

> "Click the element with ID `login-btn`."

A developer renames the ID to `login-submit`. The button is still there and
still works, but the test fails because it is looking for the old name.

This project tries to repair that kind of **safe** breakage automatically.
It also tries very hard **not** to hide real bugs.

> In one sentence: it is a careful assistant that can repair a broken test
> locator, but refuses to guess when the failure might be a real problem.

The project is written in Python 3.12. It is currently a reference MVP: the
core pipeline works and is tested in-process, but some live and external
integrations are still unverified.

> If you want the user's view first, jump to
> [4.1 What the end user actually experiences](#41-what-the-end-user-actually-experiences).

---

## 2. The problem it solves

When a UI or API test fails, teams usually have three bad options:

1. **Fix the test by hand** every time the UI changes. This is slow and boring.
2. **Let a tool blindly "fix" the test.** This can hide a real bug.
3. **Disable the test.** This loses coverage and lets defects through.

This project offers a fourth option:

> **Heal only when it is safe, and escalate to a human when it is not.**

"Escalate" means: stop, keep the test failing, and send a clear explanation
to a person. The project would rather ask for help than make a dangerous
change.

---

## 3. The big idea: careful, not clever

The most important design rule is:

> **Models may suggest. Plain code decides.**

- The classifier, scoring, policy, gating, and Git operations are
  deterministic code.
- An optional LLM can propose a candidate, but it cannot override a failed
  deterministic check.
- If the system is unsure, it stops and asks a human.

This is called **fail closed**. "Fail closed" means: when in doubt, do not
heal; escalate. A wrong heal can hide a real defect, so the system must fail
in the safe direction.

Other safety rules:

- Never auto-heal API contract changes.
- Never auto-heal removed or weakened assertions.
- Never auto-heal performance threshold changes.
- Never weaken a test just to make it pass.
- Store a structured explanation before writing any human-readable text.
- Keep secrets in environment variables, never in code or logs.
- Mask personal data before any external call.

---

## 4. How it works, step by step

The pipeline looks like this:

```text
failing test
   -> adapter         capture the failure
   -> classifier      decide what kind of failure it is
   -> matcher         find candidate elements
   -> rescorer        rank the candidates
   -> sandbox         replay the step safely
   -> critic          independently verify the result
   -> policy          decide: heal, propose, or escalate
   -> xai             write the structured explanation first
   -> alerts/gitops   tell a human or prepare a reviewed PR
```

### Step 1 - Detect

An adapter captures the failure: the error message, the page HTML, the
network status, and the locator that failed.

> **Current limit:** the real runner adapters are not implemented yet.
> `healing/adapters/` is a documented placeholder. The demo uses benchmark
> cases instead of a real pytest/Selenium failure.

### Step 2 - Classify

The classifier puts the failure into one of six classes:

| Class | Simple meaning | Safe to heal? |
|---|---|---|
| `locator_drift` | The element moved or was renamed | Usually yes |
| `data_issue` | The test data looks wrong | Maybe |
| `timing_issue` | The page or element was not ready | Maybe |
| `environment_issue` | Network, DNS, or service problem | No |
| `genuine_regression` | A real product bug | No |
| `contract_change` | An API contract changed | No |

The last three are **blocked classes**. They never reach the heal engine.
The system escalates them.

### Step 3 - Find candidates

The matcher looks for elements that could be the same element under a new
name. It can use the Healenium backend (reused under Apache 2.0) or another
matcher implementation.

A **candidate** is a possible replacement locator, such as
`login-submit`, `submit`, or `login-button`.

### Step 4 - Score

The rescorer ranks candidates using six weighted features, for example:

- Does the element ID look similar?
- Do the text, role, and name match?
- Is it in the same place on the page?
- Is it the same kind of element?

The score is transparent: each feature's contribution is recorded. The
system also checks the **gap** between the top two candidates. If they are
too close, the result is ambiguous and the system escalates.

### Step 5 - Replay in a sandbox

The sandbox replays the step in a safe, isolated environment. It uses a
seeded reset, an egress allowlist, and stubs. A sandbox pass alone is **not**
enough to approve a heal.

### Step 6 - Verify with the Critic

The Critic is an independent checker. It has four layers:

- **Deterministic:** basic checks on the candidate.
- **State:** is the page still in a valid state?
- **Network:** were the network calls sane?
- **Intent:** does the candidate represent the same user action?

The Critic must pass. An optional LLM cannot override a failed deterministic
check.

### Step 7 - Decide with policy

The policy engine uses confidence thresholds:

- **High confidence** (0.8 or more) plus a Critic pass: normal heal.
- **Medium confidence** (0.5 or more): heal marked "unverified" and needs
  review.
- **Low confidence:** escalate.
- **Ambiguous candidates:** escalate.

The default policy is **L3 in shadow mode**. That means the system can decide
to heal, but it records what it would do and does **not** open a real pull
request. A human reviews the proposal.

### Step 8 - Explain first

Before any narrative text, the system writes a structured **XAI record**
(explainable AI record). It stores:

- the failure class and probabilities,
- the candidates and their scores,
- the selected candidate and rejected ones,
- the thresholds that were applied,
- the Critic checks,
- the escalation reason, if any,
- the model, prompt, policy, and config versions.

This makes every heal replayable and auditable.

### Step 9 - Deliver or escalate

- If the decision is a heal: the system prepares a diff, a PR body, and an
  audit entry. In shadow mode it opens no PR.
- If the decision is an escalation: the system creates an alert with evidence
  and a severity level.

### Step 10 - Audit

An append-only, hash-chained audit log records security-relevant events. A
retention job can clean up old artifacts; it is dry-run by default.

### 4.1 What the end user actually experiences

This section looks at the same pipeline from the other side: what the person
using it sees, does, and decides.

#### Who the end user is

The main user is a test automation engineer, QA engineer, or developer who
owns a failing UI or API test. A second user is the reviewer, team lead, or
manager who reads the dashboard and the explanation records.

If you are a reviewer or manager, you mostly use the dashboard and the XAI
records. You check what was healed, what was escalated, and whether the
evidence is convincing.

The user's real question is simple:

> "Is this failure a real bug, or did the UI change in a harmless way?"

The software exists to answer that question safely.

#### Today: what you can actually do

The current reference MVP is demonstrated with benchmark cases, not with a
real test runner. Today you can:

1. Install the project and run `tasks.py demo`.
2. Watch 24 pre-registered cases go through the pipeline.
3. Compare three views: the full pipeline, the Healenium simulator alone, and
   the Critic.
4. Read two complete XAI records: one heal and one escalation.
5. Open the dashboard and inspect the gates, recent records, and metrics.
6. Run `tasks.py gates` and see the current 9 PASS / 2 FAIL / 1 UNVERIFIED
   status.

What you cannot do today: point the framework at your own pytest/Selenium
suite. `healing/adapters/` is a documented placeholder. That is the main gap
between the reference MVP and a usable MVP.

#### The intended everyday flow

Once the pytest adapter is connected, the user experience should look like
this. This is the target flow, not a claim that it is fully wired today.

1. **You run your normal test suite.** No special rewrite of every test is
   required; the adapter captures failures through a fixture or plugin.
2. **A test fails.** For example: `NoSuchElementException: #login-btn`.
3. **The adapter captures context.** It records the error, the current page
   HTML, the failing locator, the network status, and the test metadata.
4. **The framework classifies the failure.** You see the class and the
   confidence, for example `locator_drift` at 0.93.
5. **It proposes candidates.** You see the ranked list, for example
   `login-submit` (0.91), `submit` (0.69), and `login-button` (0.64).
6. **It replays the step in the sandbox.** You see whether the replay passed.
7. **The Critic verifies the result.** You see the layer results:
   deterministic, state, network, and intent.
8. **The policy decides.** You see one of four outcomes:
   - `heal_pr`: high confidence and a Critic pass.
   - `heal_unverified`: medium confidence; the heal needs review.
   - `propose`: the system proposes but does not act.
   - `fail_escalate`: the system refuses to heal and asks for a human.
9. **The XAI record is written first.** The explanation exists before any
   narrative text or PR.
10. **You review the proposal.** In shadow mode, you see the PR body and diff
    the system would use, but no real PR is opened. If the team enables real
    PRs, you review the PR like any other code change.
11. **You merge or reject.** The decision is yours. The system does not merge
    its own change in the default configuration.
12. **The system watches the result.** After merge, the post-merge watcher can
    create a revert PR and an alert if the heal does not survive.
13. **If the decision is escalate, you get an alert.** It contains the class,
    the reason, the evidence, and the suggested next step. You decide whether
    to fix the product, fix the test, or fix the environment.

#### What you see in the console

The demo prints a compact table. An illustrative pair of rows looks like
this:

| Case | Expected | Pipeline | Healenium alone | Critic |
|---|---|---|---|---|
| `renamed_id` | HEAL | `submit-order` | `submit-order` | `pass:all-layers` |
| `lookalike_trap` | ESCALATE | `ESCALATE` | a plausible wrong pick | `n/a (escalated)` |

The real demo prints 24 rows plus two full XAI records. The point of the table
is to show where the pipeline and the raw matcher disagree. The
`lookalike_trap` row is the important one: the raw matcher can pick a
plausible but wrong element, while the pipeline escalates.

#### What you see in an XAI record

A record is structured data, not a paragraph. A simplified excerpt looks like
this:

```text
classification: locator_drift
probabilities: locator_drift 0.93, others lower
selected: login-submit (0.91)
rejected: submit (0.69, below_top), login-button (0.64, below_top)
thresholds: high 0.8, medium 0.5, ambiguity margin 0.1
critic: pass
decision: heal_unverified
versions: rules-0.1.0 / policy-0.1.0 / config-0.1.0
content_hash: <sha256>
```

The real record is JSON and includes per-feature score contributions, every
attempt, the Critic checks, and the escalation reason. The `content_hash`
lets the dashboard detect tampering.

#### What you see in the dashboard

The dashboard is the user's cockpit. It shows:

- **Gates:** PASS, FAIL, or UNVERIFIED; the actual value, the target, and the
  source report.
- **Recent records:** the newest 25 explanation records, including the class,
  selected candidate, confidence, Critic verdict, escalation reason, and hash.
- **Metrics snapshot:** the latest saved quality metrics.
- **Integrity check:** if a record hash does not match, the dashboard flags it.

The dashboard is read-only. There is no "heal now" button. It is a window into
the records, not a control panel. It binds to localhost and has no login, so
it is for local use only.

#### What you are asked to decide

The software does not remove the human from the loop. It moves the human to
the right place. You are asked to decide:

- **For a heal proposal:** Is the new locator the same element and the same
  user intent? Merge or reject.
- **For an escalation:** Is this a real bug, an environment problem, a
  contract change, or bad test data? The alert gives you the evidence.
- **For an API contract change:** Do you approve the new contract? The system
  never auto-heals it.
- **For low confidence:** Can you provide a better locator, a clearer test, or
  a more stable page?
- **For a red gate:** Do you fix the system, waive the gate with a written
  reason, or re-baseline the target? This is a human decision.

#### What the software will not do

- It will not fix a real product bug.
- It will not change an assertion, a performance threshold, or an API
  contract.
- It will not open a real pull request in the default shadow mode.
- It will not heal when it is unsure.
- It will not replace human review.
- It will not claim a live result without a fresh live run.

#### A day in the life

A test engineer starts the day with a red CI run. The login test failed.
The framework classifies it as `locator_drift`, proposes `login-submit`, the
Critic passes, and a shadow PR appears. The engineer reviews the old and new
locators, checks the evidence, and merges.

Later, the checkout test fails. The framework classifies it as
`genuine_regression`: the checkout button was removed. It escalates instead
of inventing a new locator. The engineer files a product bug. The test stays
red, which is correct.

At the end of the day, the dashboard shows one heal and one escalation. The
engineer can explain both decisions because each one has a structured record.

That is the intended experience. The missing piece today is the adapter that
turns a real pytest failure into this flow. Until it exists, the demo uses
benchmark cases to show the same decision path.

#### What the end user needs to provide

- A test runner (pytest with Selenium, Playwright, or an API suite).
- Access to the page DOM/HTML and network status at failure time.
- A baseline DOM or a stored selector history, so the system can infer intent.
- A policy configuration: thresholds, blocked classes, shadow mode, budgets.
- For real PRs: GitHub App credentials and a repository.
- For alerts: webhook URLs from environment variables.
- For the live browser path: the Docker Compose stack.

#### What the end user gets back

- A clear decision, not a silent edit.
- A structured explanation record before any narrative.
- A safe default: shadow mode, no real PRs.
- A reviewable diff and PR body when a heal is proposed.
- An evidence-rich alert when escalation is the right answer.
- An audit trail and replayable versions for every heal.

This is the user's side of the system: the software does the repetitive
detective work, but the human keeps the judgment call.

---

## 5. A concrete example

Imagine a test that clicks the login button:

```python
page.click("#login-btn")
```

The page changes the button's ID to `login-submit`. The test fails with:

```text
no such element: #login-btn
```

Here is what the system does:

1. **Detect:** the adapter captures the error and the current page HTML.
2. **Classify:** the classifier says `locator_drift` with 0.93 confidence.
3. **Find candidates:** the matcher proposes `login-submit`, `submit`, and
   `login-button`.
4. **Score:** `login-submit` ranks first with 0.91; the gap to second place is
   0.22.
5. **Sandbox:** replaying the click on `login-submit` works.
6. **Critic:** the intent check says it is still the login action; the page
   state and network look normal.
7. **Policy:** high confidence plus a Critic pass means "heal."
8. **Explain:** the XAI record is written first.
9. **Deliver:** in shadow mode, the system records the PR body it would use
   and opens nothing.
10. **Review:** a human can approve the change.

If the button had been **removed** instead of renamed, the classifier would
say `genuine_regression`, and the system would escalate. That is the correct
behavior: a missing button may be a real bug.

---

## 6. What happens when it is not safe

The system escalates in all of these cases:

- The failure looks like a real product bug.
- The network or environment is unhealthy.
- An API contract changed.
- An assertion was removed or weakened.
- A performance threshold changed.
- Confidence is too low.
- Two candidates are too close to call.
- The input is unknown or malformed.

Escalation is not a failure of the system. It is the system doing its job.
The goal is not "heal everything." The goal is "heal safely, and never hide a
real defect."

---

## 7. The main parts of the system

| Folder | What it does in simple terms |
|---|---|
| `healing/classifier/` | Decides what kind of failure it is |
| `healing/matching/` | Finds candidate elements and ranks them |
| `healing/sandbox/` | Replays the step in a safe environment |
| `healing/critic/` | Independently verifies the result |
| `healing/policy/` | The rulebook for heal vs escalate |
| `healing/orchestrator/` | Runs the whole pipeline |
| `healing/xai/` | Writes structured explanation records |
| `healing/alerts/` | Tells humans when something needs attention |
| `healing/gitops/` | Prepares branches, commits, and pull requests |
| `healing/nonui/` | Handles API/schema failures |
| `healing/quality/` | Metrics, gates, calibration, observability |
| `healing/dashboard/` | Read-only local dashboard |
| `healing/adapters/` | Planned real runner input (currently a placeholder) |
| `healing/security/` | Masking, audit log, retention |
| `benchmark/` | Test cases and saved benchmark reports |
| `demo_app/` | A small FastAPI app with UI and API drift modes |
| `scripts/` | Commands for benchmarks, gates, demo, replay, retention |
| `tests/` | The pytest test suite |
| `docs/` | Architecture, targets, evidence, decisions, runbook |
| `reports/` | Saved evidence and run logs |

### The API sidecar

The project also handles API test failures. It classifies them separately:

- `expired_credential`
- `stale_data`
- `approved_spec_change`
- `unapproved_change`
- `contract_change`

It can take only three allowlisted actions:

- `refresh_token`
- `regenerate_fixtures`
- `propose_test_update`

Everything else escalates. API contract changes are **never** auto-healed.

### The dashboard

The dashboard is a read-only local web page. It shows:

- the quality gates,
- the newest explanation records,
- the latest saved metrics snapshot.

It is GET-only, binds to localhost, masks personal data, escapes displayed
text, and hash-checks the records. It has no login, so it must not be exposed
to the internet.

---

## 8. What is already built

The core reference MVP is largely complete:

- **Core healing pipeline:** classifier, fail-closed blocked classes, matcher
  interface, Healenium adapter, transparent rescorer, attempt ladder,
  sandbox replay, layered Critic, policy engine, orchestrator.
- **Explainability and audit:** structured XAI records, version pinning and
  replay, append-only audit log, retention job.
- **Safety and alerts:** alert model with evidence completeness, console/file
  and webhook senders, shadow mode, assertion/threshold guard, PII masking,
  autonomy guard.
- **API sidecar:** API classifier, allowlisted actions, contract checks,
  schema diff, API shadow PR, audit, and explanation record.
- **GitOps:** GitHub App client, AST locator edits, PR template,
  shared-locator dedupe, post-merge watcher. (Tested against a local bare
  repository, not real GitHub.)
- **Quality and observability:** metrics and reports, hash-pinned golden set,
  calibration, OpenTelemetry/Prometheus metric samples.
- **Benchmarks and demo:** 24 UI cases, 24 demo cases, 7 API cases, 35
  held-out cases, shadow report, vision benchmark, Healenium simulator,
  historical live reports, one-command demo.
- **Dashboard:** read-only operator dashboard.
- **Tests and docs:** 204 passing tests, clean lint/type checks, README,
  operator runbook, evidence index, architecture docs.

The project backlog currently tracks:

- **60 done**
- **33 partial**
- **22 open**

"Partial" means the feature exists, but it is missing a live, external, or
executable proof. It is not the same as "not built."

---

## 9. What is real, simulated, or unverified

The project uses clear evidence labels. This is important because a demo can
look real even when it is simulated.

| Label | Meaning |
|---|---|
| **MEASURED** | Actually run, with a command, artifact, and date |
| **SIMULATED** | Run in-process with fake or deterministic inputs |
| **UNVERIFIED** | Not observed or not proven |
| **MEASURED (historical)** | Measured once, but not re-run recently |

### What is measured now

- The 204-test suite.
- The 24-case demo.
- The in-process benchmarks.
- The quality gates.
- The read-only dashboard.
- The fresh-venv quickstart.

### What is measured but historical

- The live Healenium benchmark.
- The live end-to-end pipeline.
- Both are from **2026-10-08** and have not been re-run because Docker is not
  available on this machine.

### What is simulated

- The demo cases.
- The Healenium simulator.
- The API benchmark.
- The vision/LLM benchmark.

### What is unverified

- A fresh live stack run.
- Real GitHub App pull requests and reverts.
- Real Slack, Teams, or Jira delivery.
- Real before/after/candidate screenshots.
- Prometheus scraping and Grafana deployment.
- 30 days of heal survival history.

A reviewer should treat simulated results as evidence about the decision
path, not as proof of live browser or production behavior.

---

## 10. Current status and known limits

### Test and gate status

- **204 tests passed** on Python 3.12.10.
- Lint and type checks are clean.
- The fresh-venv quickstart was verified.
- Quality gates: **9 PASS / 2 FAIL / 1 UNVERIFIED**.
- `tasks.py gates` exits with code 1 while the two red gates remain. This is
  intentional.

### The two red gates

**1. `false_heal_rate_adversarial`**

- The **raw live matcher** heals all 9 must-not-heal cases. That is a
  false-heal rate of 1.0.
- The **shipped orchestrator path** escalates all 9 cases. Its false-heal
  rate is 0.0.
- The target text says "orchestrator path," but the current gate reads the
  raw matcher report.
- This is a measurement-definition question. A human must decide whether the
  gate should measure the raw matcher or the shipped orchestrator. Either way,
  the raw matcher number should stay visible.

**2. `latency_per_heal_ms`**

- The live browser measurement is about **1122 ms** per heal.
- The target is **100 ms**.
- The 100 ms target was written for in-process work, which takes about
  0.02 ms in the simulator and about 20 ms of pipeline overhead in the live
  end-to-end report.
- The current gate reads browser latency, not in-process latency.
- This is also a measurement-definition question. A human must decide whether
  the target is for orchestrator overhead or end-to-end browser time.

These are not being hidden or tuned away. The raw numbers remain in the
reports, and the decision is reserved for a human.

### Other known limits

- **Real runner ingestion is missing.** `healing/adapters/` is a placeholder.
  The demo is driven by benchmark cases, not by a real pytest or Selenium
  failure.
- **The live stack has not been re-run.** Docker is unavailable.
- **The API held-out set is 10/11.** The `token-cart` case misses because
  `observe()` does not handle `GET /api/cart`.
- **Real GitHub is not tested.** The GitOps path uses a local bare repository.
- **Real Slack/Teams/Jira is not tested.** Only console/file delivery has
  been exercised.
- **Screenshots are placeholders.** No real before/after/candidate images
  have been captured.
- **Prometheus/Grafana is not deployed.** The project exports metric samples
  in-process, but there is no running scrape or dashboard.
- **The project license is TBD.** The package is not distributable until a
  human chooses a license.
- **The SBOM license allowlist is not enforced.** `scripts/sbom.py` defines
  an allowlist, but no CI step checks it.
- **The secret scan is still grep-based.** It should be replaced before
  distribution.
- **The survival gate has no history.** It reports `insufficient_data` until
  30 days of heal history exists.
- **Vision/LLM is a DROP.** The code and benchmark exist, but there are no
  real screenshots, and attempts 1-2 already win. It stays disabled.
- **The raw matcher is not safe alone.** Healenium alone heals adversarial
  cases; the classifier and Critic are what make the shipped path safe.

---

## 11. How to run the demo

### Setup (Windows)

```powershell
py -3.12 -m venv .venv312
.venv312\Scripts\python -m pip install -e ".[dev]"
```

### Setup (macOS/Linux)

```bash
python3.12 -m venv .venv312
.venv312/bin/python -m pip install -e ".[dev]"
```

### Run the tests

```powershell
.venv312\Scripts\python tasks.py test
```

Expected result: **204 passed**.

### Run the presentation demo

```powershell
.venv312\Scripts\python tasks.py demo
```

This runs 24 pre-registered drift scenarios through the full in-process
pipeline. It prints the pipeline choice, the Healenium simulator alone, and
the layered Critic verdict. It ends with two complete XAI records: one heal
and one escalation.

Everything in this demo is **SIMULATED**. It shows the decision path, not a
live browser result.

### Run the quality gates

```powershell
.venv312\Scripts\python tasks.py gates
```

Expected result: **9 PASS / 2 FAIL / 1 UNVERIFIED**, exit code 1.

The exit code is 1 because two gates are still red. The dashboard shows the
same status.

### Open the dashboard

```powershell
.venv312\Scripts\python tasks.py dashboard
```

Then open <http://127.0.0.1:8080>.

The dashboard is read-only. It binds to localhost and has no authentication,
so do not expose it to the internet.

### Other useful commands

| Command | What it does |
|---|---|
| `python tasks.py lint` | Run ruff and mypy |
| `python tasks.py bench` | Baseline benchmark and Critic verify |
| `python tasks.py bench-heldout` | Held-out UI and API cases |
| `python tasks.py bench-api` | API sidecar with zero contract heals |
| `python tasks.py bench-shadow` | Shadow-mode report |
| `python tasks.py bench-vision` | Vision/LLM benchmark |
| `python tasks.py bench-healenium-live` | Live Healenium (Docker required) |
| `python tasks.py bench-e2e-live` | Live end-to-end pipeline (Docker required) |
| `python tasks.py evidence-snapshot` | Deterministic quality transcript |

The live benchmarks need Docker. When Docker is unavailable, the reports are
historical and must be labelled that way.

---

## 12. The read-only dashboard

The dashboard is a small local web app. It answers three questions:

1. **Are the quality gates passing?**
2. **What did the system decide recently?**
3. **What do the latest saved metrics say?**

It does not scrape live metrics, and it does not heal anything. It reads
saved reports and records.

Safety properties:

- GET-only: it has no write endpoints.
- Localhost-bound: it is not a public service.
- PII-masked: personal data is masked before display.
- HTML-escaped: displayed text cannot inject scripts.
- Hash-checked: explanation records are checked for tampering.
- Unauthenticated: suitable for a local demo only.

Current evidence: **9 PASS / 2 FAIL / 1 UNVERIFIED**, 25 newest records,
0 hash mismatches.

---

## 13. Repository map

| Path | Contents |
|---|---|
| `healing/` | Classifier, matcher, sandbox, Critic, policy, XAI, alerts, GitOps, API sidecar, quality tooling, dashboard |
| `benchmark/` | Core 24-case benchmark, held-out cases, demo cases, wrong-heal set, saved reports |
| `demo_app/` | FastAPI demo app with UI and API drift injection |
| `scripts/` | Benchmarks, gates, demo, replay, retention, SBOM |
| `tests/` | Pytest suite, including evidence-integrity checks |
| `docs/` | Architecture, ADRs, targets, evidence index, provenance, sign-off, runbook |
| `reports/` | Committed run logs and dated evidence transcripts |
| `infra/` | Docker Compose stack for the live Healenium path |
| `tasks.py` | Windows-friendly task runner |
| `Makefile` | Unix-friendly task runner |

Key documents:

- `README.md` - quickstart and current limits.
- `docs/ARCHITECTURE.md` - the pipeline and components.
- `docs/DECISIONS.md` - architecture decisions, including fail-closed rules.
- `docs/TARGETS.md` - the quality targets and why they exist.
- `docs/EVIDENCE_INDEX.md` - claim -> command -> artifact.
- `docs/HUMAN_SIGNOFF.md` - decisions reserved for humans.
- `docs/OPERATOR_RUNBOOK.md` - start/stop, secret rotation, recovery, retention.
- `TODO.md` - the P0/P1/P2 backlog.

---

## 14. Glossary

| Term | Simple meaning |
|---|---|
| **Locator** | How a test finds an element, such as an ID, CSS selector, or text |
| **Locator drift** | The element still exists, but its locator changed |
| **Heal** | Propose and verify a new locator for a failing test |
| **Escalate** | Stop and ask a human; do not heal |
| **Candidate** | A possible replacement locator |
| **Confidence** | How sure the classifier or scorer is |
| **Ambiguity margin** | The required gap between the top two candidates; if too close, escalate |
| **Sandbox** | A safe, isolated replay environment |
| **Critic** | An independent checker that must pass before a heal is accepted |
| **XAI record** | A structured explanation of a decision |
| **Gate** | A quality rule that must pass before release |
| **Shadow mode** | Record what the system would do, but do not open a real PR |
| **Pull request (PR)** | A proposed code change for human review |
| **Revert** | A change that undoes a previous change |
| **L3** | An autonomy level where the system may heal, but PRs still need review |
| **PII** | Personal information, such as email, phone, or card data |
| **SBOM** | Software bill of materials: a list of dependencies and licenses |
| **Survival rate** | The share of heals that still work after some time |
| **Fail closed** | When unsure, stop and escalate instead of guessing |

---

## 15. What is still pending

The backlog has three priority levels.

### P0 - before the presentation

- Re-run the live Healenium and live end-to-end benchmarks when Docker is
  available.

### P1 - before merge and release

- Resolve the two red gates.
- Fix the `token-cart` observer gap.
- Exercise live attempts 2-4.
- Capture real before/after/candidate screenshots.
- Observe CI green on Python 3.12.
- Install the real GitHub App and open one heal PR and one revert PR.
- Smoke-test real Slack/Teams/Jira delivery.
- Close the missing test/artifact debt.
- Enforce the SBOM license allowlist in CI.
- Replace the grep-based secret scan.
- Activate the survival gate or record a formal deferral.
- Choose the project license.
- Complete legal review and the vendor/subprocessor register.
- Approve the 12 quality targets.
- Confirm release blockers and cut the next tag.

### P2 - production

- Implement full runner adapters for real pytest/Selenium/API suites.
- Deploy Prometheus scraping and the Grafana dashboard.
- Schedule the retention job and alert on failure.
- Revisit vision/LLM with real screenshots.
- Revisit the chatbot/MCP assistant (currently deferred).

### The biggest missing feature for a usable MVP

The project can demonstrate the full decision path, but it cannot yet ingest
a **real** failing test from a real test runner. `healing/adapters/` is a
placeholder.

Adding one real pytest adapter would turn the demo into a tool a team could
try on its own test suite. That is the main feature gap between the current
reference MVP and a usable MVP.

Why it is not a small wrapper: the current orchestrator entry point uses
benchmark-only fields (`drift_mode` and `correct_element`). A production
adapter must derive the failure signals from the real error and DOM diff, and
derive the intended target from the baseline DOM and the failing locator. That
is a real design task, not just plumbing.

---

## 16. The one-sentence summary

> This is a fail-closed self-healing layer for UI and API tests: it repairs
> safe locator drift automatically, explains every decision, and escalates to
> a human whenever the failure might be a real bug, a contract change, or an
> environment problem.

---

## A final note on honesty

This project deliberately separates:

- what has been **measured**,
- what has been **simulated**,
- and what is still **unverified**.

That is why some numbers are labelled historical, why some gates are still
red, and why some features are marked partial. The goal is not to look
finished. The goal is to be trustworthy.

No sign-off box in `docs/HUMAN_SIGNOFF.md` has been ticked. Decisions about
the project license, legal review, quality targets, and the two red gates are
reserved for a human.
