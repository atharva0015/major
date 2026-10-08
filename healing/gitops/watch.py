"""Post-merge watcher: revert PR + alert if the healed test fails in-window."""

from __future__ import annotations

import time
from collections.abc import Callable

from healing.gitops.app import GitHubClient, PullRequest


def should_watch(merged_at: float, window_h: float, now: float | None = None) -> bool:
    return (time.time() if now is None else now) - merged_at <= window_h * 3600.0


def on_failure(
    test: str,
    pr: PullRequest,
    reason: str,
    client: GitHubClient,
    alerter: Callable[[str], None] | None = None,
) -> dict[str, object]:
    """Open a revert PR and alert. Returns the revert record."""
    revert = client.open_revert_pr(pr, reason)
    if alerter is not None:
        alerter(f"healed test {test} failed post-merge; revert #{revert.number}: {reason}")
    return {"test": test, "revert_pr": revert.number, "reason": reason}
