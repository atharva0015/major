"""Tests for alerts: required fields, routing, SLA, quarantine."""

from healing.alerts.model import (
    build_alert,
    needs_escalation,
    quarantine_test,
    severity_for,
)
from healing.alerts.routers import ConsoleSender, FileSender, JiraSender, route


def alert():  # type: ignore[no-untyped-def]
    return build_alert(
        "login",
        "locator_drift",
        [{"n": 1, "strategy": "healenium_match", "verdict": True, "reason": "ok"}],
        {"before": "b.png", "after": "a.png", "candidate": "c.png"},
        "review PR",
        "sandbox://replay/1",
        severity="low",
    )


def test_every_required_field_present() -> None:
    a = alert()
    ok, missing = a.complete()
    assert ok and missing == []
    for f in (
        "test",
        "build",
        "environment",
        "classification",
        "attempts",
        "screenshots",
        "next_step",
        "replay_link",
    ):
        assert getattr(a, f)


def test_incomplete_alert_lists_missing() -> None:
    a = alert()
    a.screenshots.pop("before")
    ok, missing = a.complete()
    assert not ok and "screenshots.before" in missing


def test_severity_routing() -> None:
    assert severity_for("genuine_regression", {"genuine_regression": "high"}) == "high"
    assert severity_for("locator_drift") == "low"


def test_sla_escalation_only_when_unacknowledged() -> None:
    a = alert()
    assert needs_escalation(a, now=a.ack_deadline_s + 1) is True
    a.acknowledged = True
    assert needs_escalation(a, now=a.ack_deadline_s + 999) is False


def test_quarantine_is_visible_not_silent() -> None:
    a = quarantine_test(alert())
    assert a.quarantined is True


def test_routers_send_without_secrets(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    out = route(alert(), [ConsoleSender(), FileSender(str(tmp_path / "a.log")), JiraSender()])
    assert out[0]["sent"] and out[1]["sent"]
    assert out[2] == {"sent": False, "channel": "jira", "reason": "JIRA_API_TOKEN_ISSUES_URL unset"}
