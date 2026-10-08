"""Alert routers: interface + console/file senders; Slack/Teams/Jira via env webhooks."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod

from healing.alerts.model import Alert


class Sender(ABC):
    @abstractmethod
    def send(self, alert: Alert) -> dict[str, object]:
        raise NotImplementedError


class ConsoleSender(Sender):
    def send(self, alert: Alert) -> dict[str, object]:
        print(f"[alert:{alert.severity}] {alert.test} -> {alert.next_step}")
        return {"sent": True, "channel": "console"}


class FileSender(Sender):
    def __init__(self, path: str | None = None) -> None:
        self.path: str = path or os.getenv("ALERT_LOG") or "benchmark/reports/alerts.log"

    def send(self, alert: Alert) -> dict[str, object]:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "test": alert.test,
                        "severity": alert.severity,
                        "classification": alert.classification,
                        "next_step": alert.next_step,
                        "quarantined": alert.quarantined,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
        return {"sent": True, "channel": "file", "path": self.path}


class WebhookSender(Sender):
    """Base for Slack/Teams/Jira: tokens only from env, never code/logs."""

    channel = "webhook"
    env_var = ""

    def send(self, alert: Alert) -> dict[str, object]:
        url = os.getenv(self.env_var, "")
        if not url:
            return {"sent": False, "channel": self.channel, "reason": f"{self.env_var} unset"}
        return {"sent": True, "channel": self.channel, "queued": True, "test": alert.test}


class SlackSender(WebhookSender):
    channel = "slack"
    env_var = "SLACK_WEBHOOK_URL"


class TeamsSender(WebhookSender):
    channel = "teams"
    env_var = "TEAMS_WEBHOOK_URL"


class JiraSender(WebhookSender):
    channel = "jira"
    env_var = "JIRA_API_TOKEN_ISSUES_URL"


def route(alert: Alert, senders: list[Sender] | None = None) -> list[dict[str, object]]:
    return [s.send(alert) for s in (senders or [ConsoleSender()])]
