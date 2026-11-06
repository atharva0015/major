# Operator runbook

This is the human procedure for running the self-healing stack, rotating its
credentials, recovering from a bad heal, and applying retention. It describes
the commands that exist in this repository; it does not add automation or
approve any action.

> **Status in this environment:** Docker was unavailable on 2026-11-06, so
> the compose start/stop and live-benches below are **UNVERIFIED** here. The
> real GitHub, Slack, Teams, and Jira calls are also **UNVERIFIED**. Do not
> treat a green unit test as proof that those external integrations work.

## 1. Preconditions

- Work from the repository root.
- Use the project interpreter: `.venv312/Scripts/python` on Windows, or
  `python` inside the activated virtual environment.
- Read `docs/TARGETS.md`, `docs/HUMAN_SIGNOFF.md`, and `TODO.md` before
  changing thresholds or approving a merge.
- Keep secrets in environment variables or a secret manager. Never put a
  token, webhook URL, private key, or password in a tracked file, command
  history, alert, record, or screenshot.

Environment variables used by the code:

| Variable | Used for |
|---|---|
| `GITHUB_APP_ID`, `GITHUB_PRIVATE_KEY_PATH`, `GITHUB_INSTALLATION_ID`, `GITHUB_REPO` | GitHub App PR/revert client (`healing/gitops/app.py`) |
| `SLACK_WEBHOOK_URL`, `TEAMS_WEBHOOK_URL`, `JIRA_API_TOKEN_ISSUES_URL` | Alert delivery (`healing/alerts/routers.py`) |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Compose Postgres credentials |
| `RECORDS_PATH`, `RECORD_STORE`, `DATABASE_URL` | Explanation-record store |
| `AUDIT_LOG`, `ALERT_LOG` | Audit and alert log paths |
| `POLICY_PATH` | Override for `healing/policy/policy.yaml` |
| `DASHBOARD_HOST`, `DASHBOARD_PORT`, `DASHBOARD_METRICS_PATH`, `DASHBOARD_RECORD_LIMIT` | Read-only dashboard |
| `HEALENIUM_URL`, `HEALENIUM_PROXY_URL`, `DEMO_URL`, `DEMO_IN_COMPOSE_URL` | Live Healenium checks and benches |
| `VISION_LLM_URL`, `VISION_EMBEDDING_URL` | Optional vision/embedding adapters; disabled by default |

## 2. Start and stop the stack

Validate the compose file first, then start it:

```powershell
docker compose --project-directory infra -f infra/docker-compose.yml config
docker compose --project-directory infra -f infra/docker-compose.yml up -d
docker compose --project-directory infra -f infra/docker-compose.yml ps
```

Expected services: `postgres-db`, `healenium`, `selector-imitator`,
`hlm-proxy`, `selenium-hub`, `node-chrome`, and `demo-app`.

Check the local endpoints:

```powershell
Invoke-WebRequest http://localhost:7878/healenium/report/data
Invoke-WebRequest http://localhost:8001/
Invoke-WebRequest http://localhost:4444/status
```

Run the live check and, if a full measurement is intended, the live bench:

```powershell
.venv312/Scripts/python -m scripts.live_healenium_check
.venv312/Scripts/python -m scripts.bench_healenium_live
```

The dashboard is separate from compose and binds to localhost:

```powershell
.venv312/Scripts/python -m healing.dashboard.app
```

Open <http://127.0.0.1:8080>. It is read-only and has no authentication.

Stop the stack with:

```powershell
docker compose --project-directory infra -f infra/docker-compose.yml stop
docker compose --project-directory infra -f infra/docker-compose.yml down
```

**Data warning:** the compose file does not mount a named volume for the
Postgres data directory, so `down` removes the containers and their writable
layers. Back up first if the reference selectors, heal history, or reports
must survive:

```powershell
docker exec -t postgres-db pg_dump -U healenium_user -d healenium -f /tmp/healenium.sql
docker cp postgres-db:/tmp/healenium.sql .\healenium-backup.sql
```

Never run `down -v` unless deleting all named volumes is the intended action.

## 3. Rotate secrets

Rotate on a schedule, after a suspected exposure, and when an owner leaves.
Record the rotation date and owner outside the repository.

### GitHub App private key

1. In the GitHub App settings, generate a new private key.
2. Store the PEM outside the repository and restrict its file permissions.
3. Point `GITHUB_PRIVATE_KEY_PATH` at the new file and restart the process
   that opens PRs.
4. Verify the App can read the repository and open a draft/test PR through
   the normal review process. A real GitHub call is still **UNVERIFIED** in
   this repository's evidence.
5. Revoke the old key in GitHub only after the new key is verified.

Do not commit the PEM, paste it into a log, or put it in a compose file.

### Slack, Teams, and Jira

1. Create a new webhook or API token in the provider.
2. Update `SLACK_WEBHOOK_URL`, `TEAMS_WEBHOOK_URL`, or
   `JIRA_API_TOKEN_ISSUES_URL` in the process environment or secret manager.
3. Restart the alert worker.
4. Send one masked test alert and confirm delivery. Unit tests do not prove
   real delivery; TODO P1.9 remains open until a human observes it.
5. Revoke the old webhook or token.

### Postgres

1. Back up the database as shown above.
2. Change the role password in Postgres, for example:
   `docker exec -it postgres-db psql -U healenium_user -d healenium -c "ALTER USER healenium_user WITH PASSWORD '<new-password>';"`
3. Update `POSTGRES_PASSWORD` in the environment or secret manager and
   restart the dependent services.
4. A throwaway local stack can instead be recreated, but that destroys its
   data. Do not recreate a stack that holds evidence.

### Demo token and optional model URLs

`TEST_TOKEN` is a demo/test credential, not a repository secret. Rotate it in
the demo app and the test runner together, and never print it. If
`VISION_LLM_URL` or `VISION_EMBEDDING_URL` embeds a credential, rotate it at
the provider and update the environment; the vision/LLM path is disabled by
default.

After any rotation, run the routine checks in section 6 and confirm the
dashboard has no warnings.

## 4. Recover from a failed or suspect heal

1. **Stop new heals.** Set `kill_switch: true` in
   `healing/policy/policy.yaml` (or in the file named by `POLICY_PATH`), then
   restart the process that calls the orchestrator. The policy returns
   `fail_escalate` with `kill_switch_engaged`; rollback is not blocked by the
   switch.
2. **Preserve evidence.** Copy `benchmark/reports/records.jsonl`,
   `benchmark/reports/audit.log`, and `benchmark/reports/alerts.log` to a
   safe location. Do not edit records in place; the store is append-only.
3. **Find the record.** Use the dashboard's recent-record table or the
   `heal_id` from the alert. A non-zero hash mismatch is a red flag: preserve
   the file and escalate rather than trusting the row.
4. **Replay the decision.**
   `.venv312/Scripts/python -m scripts.replay_heal <heal-id> --html <snapshot.html> --candidates a,b`
   The command exits 1 when the reproduced selection does not match the
   record. Use the stored inputs where available; a replay with invented
   inputs proves nothing.
5. **Roll back.**
   `.venv312/Scripts/python -m scripts.rollback_heal <heal-id|branch> --reason "post-merge failure"`
   This script is currently a **dry run**: it prints the revert branch/PR it
   would reference and does not open a PR. A human must execute the revert
   through the reviewed GitOps process. Do not describe the dry run as a
   completed rollback.
6. **Fix forward only after review.** For the known `token-cart` observer gap,
   do not change code without the approval required by TODO P1.4. For a
   regression or contract change, the correct outcome is escalation, not a
   heal.
7. **Re-enable.** Re-run the tests and gates, confirm the dashboard is clean,
   and get human approval before setting `kill_switch` back to `false`.

## 5. Retention and deletion

Retention is dry-run by default:

```powershell
.venv312/Scripts/python -m scripts.retention
```

Inspect the JSON `deletions` list. Only then apply it:

```powershell
.venv312/Scripts/python -m scripts.retention --apply
```

The current schedule is:

| Artifact | Retention |
|---|---|
| `records.jsonl` | 365 days |
| `audit.log` | 365 days |
| `alerts.log` | 180 days |
| `benchmark/reports/screenshots/` (when present) | 90 days |

The job compares file modification time with the current time; it does not
read a record timestamp. It deletes the whole file or directory and has no
undo. Export anything needed for an investigation first. Do not run `--apply`
as part of a routine health check. Real screenshot capture is still open
(TODO P1.6); the compose stack's `infra/screenshots/` bind mount is not the
path this retention job scans.

## 6. Routine checks

```powershell
.venv312/Scripts/python -m pytest -q
.venv312/Scripts/python -m ruff check .
.venv312/Scripts/python -m ruff format --check .
.venv312/Scripts/python -m mypy healing
.venv312/Scripts/python -m scripts.check_gates
.venv312/Scripts/python -m scripts.evidence_snapshot
```

The gate command exits 1 while the documented red gates remain
(`false_heal_rate_adversarial` and `latency_per_heal_ms`). Do not loosen a
safety target to make it green; a human must fix, waive, or re-baseline it.
`heal_survival_rate` stays UNVERIFIED until history exists.

## 7. Known gaps and stop conditions

- Docker and the live stack are **UNVERIFIED** in this environment.
- Real GitHub PRs, Slack/Teams/Jira delivery, and before/after screenshots
  have not been observed.
- `scripts/rollback_heal.py` is a dry run, not a live revert.
- The dashboard is local-only, unauthenticated, and reads saved metrics; it
  is not Prometheus/Grafana.
- The SBOM license allowlist is not enforced in CI (TODO P1.12), and the
  project license is still TBD.
- Retention is irreversible after `--apply`.

Stop and ask a human owner if any of these are true: a record hash mismatch,
an unexplained heal of a regression/contract change, a failed revert, a
credential exposure, or a gate that would need a safety threshold loosened.
