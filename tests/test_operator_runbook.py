"""The operator runbook must stay aligned with the commands and limits it names."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "docs" / "OPERATOR_RUNBOOK.md"


def test_runbook_has_required_procedures() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    for heading in (
        "## 2. Start and stop the stack",
        "## 3. Rotate secrets",
        "## 4. Recover from a failed or suspect heal",
        "## 5. Retention and deletion",
        "## 6. Routine checks",
        "## 7. Known gaps and stop conditions",
    ):
        assert heading in text, f"runbook is missing {heading!r}"

    for command in (
        "docker compose --project-directory infra -f infra/docker-compose.yml up -d",
        "docker compose --project-directory infra -f infra/docker-compose.yml down",
        ".venv312/Scripts/python -m scripts.live_healenium_check",
        ".venv312/Scripts/python -m healing.dashboard.app",
        ".venv312/Scripts/python -m scripts.retention",
        ".venv312/Scripts/python -m scripts.retention --apply",
        ".venv312/Scripts/python -m scripts.rollback_heal",
        ".venv312/Scripts/python -m scripts.replay_heal",
        ".venv312/Scripts/python -m scripts.check_gates",
    ):
        assert command in text, f"runbook is missing command {command!r}"

    for env_var in (
        "GITHUB_PRIVATE_KEY_PATH",
        "SLACK_WEBHOOK_URL",
        "TEAMS_WEBHOOK_URL",
        "JIRA_API_TOKEN_ISSUES_URL",
        "POSTGRES_PASSWORD",
        "POLICY_PATH",
        "RECORDS_PATH",
    ):
        assert env_var in text, f"runbook is missing environment variable {env_var!r}"

    for fact in (
        "kill_switch: true",
        "365 days",
        "180 days",
        "90 days",
        "benchmark/reports/screenshots",
        "dry run",
        "UNVERIFIED",
    ):
        assert fact in text, f"runbook is missing operational fact {fact!r}"


def test_readme_links_to_runbook() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/OPERATOR_RUNBOOK.md" in readme
    assert RUNBOOK.is_file()
