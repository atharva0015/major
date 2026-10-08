"""Baseline healer: does nothing; every failure stays a failure (fail closed)."""

from __future__ import annotations

POLICY_VERSION = "baseline-0.1.0"


class NoHealPolicy:
    """Do-nothing policy used to measure the starting point."""

    version = POLICY_VERSION

    def choose(self, candidates: list[str]) -> str | None:  # noqa: ARG002
        return None

    def should_escalate(self) -> bool:
        return True
