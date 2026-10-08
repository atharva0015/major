"""Alert builder: every escalation carries evidence, never a bare ping."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

REQUIRED_FIELDS = (
    "test",
    "build",
    "environment",
    "classification",
    "attempts",
    "screenshots",
    "next_step",
    "replay_link",
    "severity",
)


@dataclass(frozen=True)
class AttemptSummary:
    n: int
    strategy: str
    verdict: str
    reason: str


@dataclass
class Alert:
    test: str
    build: str
    environment: str
    classification: str
    attempts: list[AttemptSummary] = field(default_factory=list)
    screenshots: dict[str, str] = field(default_factory=dict)
    next_step: str = ""
    replay_link: str = ""
    severity: str = "low"
    acknowledged: bool = False
    ack_deadline_s: float = 0.0
    quarantined: bool = False

    def complete(self) -> tuple[bool, list[str]]:
        missing = [
            f
            for f in ("test", "build", "environment", "classification", "next_step", "replay_link")
            if not getattr(self, f)
        ]
        if not self.attempts:
            missing.append("attempts")
        for s in ("before", "after", "candidate"):
            if s not in self.screenshots:
                missing.append(f"screenshots.{s}")
        return (not missing, missing)


def severity_for(failure_class: str, routing: dict[str, str] | None = None) -> str:
    table = routing or {}
    return table.get(failure_class, "medium" if failure_class != "locator_drift" else "low")


def build_alert(
    test: str,
    classification: str,
    attempts: list[dict[str, object]],
    screenshots: dict[str, str],
    next_step: str,
    replay_link: str,
    severity: str = "low",
) -> Alert:
    return Alert(
        test=test,
        build=os.getenv("BUILD_ID", "local"),
        environment=os.getenv("TEST_ENV", "staging"),
        classification=classification,
        attempts=[
            AttemptSummary(
                int(str(a.get("n", 0))),
                str(a.get("strategy", "")),
                str(a.get("verdict", "")),
                str(a.get("reason", "")),
            )
            for a in attempts
        ],
        screenshots=screenshots,
        next_step=next_step,
        replay_link=replay_link,
        severity=severity,
        ack_deadline_s=time.time() + 3600.0,
    )


def needs_escalation(alert: Alert, now: float | None = None) -> bool:
    return (not alert.acknowledged) and (time.time() if now is None else now) > alert.ack_deadline_s


def acknowledge(alert: Alert, at: float | None = None) -> Alert:
    """Mark acknowledged and record acknowledgement time for metrics."""
    from healing.quality.observability import observe_ack

    now = time.time() if at is None else at
    alert.acknowledged = True
    observe_ack(max(now - (alert.ack_deadline_s - 3600.0), 0.0))
    return alert


def quarantine_test(alert: Alert) -> Alert:
    """Quarantine (visible, tracked) — never a silent skip."""
    alert.quarantined = True
    return alert
