"""Retention job: dry-run by default; --apply required to delete anything."""

from __future__ import annotations

import os
import time

RETENTION_DAYS = {
    "records.jsonl": 365,
    "audit.log": 365,
    "alerts.log": 180,
    "screenshots": 90,
}


def plan_deletions(reports_dir: str, now: float | None = None) -> list[dict[str, object]]:
    now = time.time() if now is None else now
    plan: list[dict[str, object]] = []
    for name, days in RETENTION_DAYS.items():
        path = os.path.join(reports_dir, name)
        if not os.path.exists(path):
            continue
        age_days = (now - os.path.getmtime(path)) / 86400.0
        if age_days > days:
            plan.append(
                {
                    "path": path,
                    "age_days": round(age_days, 1),
                    "retention_days": days,
                    "action": "delete",
                }
            )
    return plan


def run(reports_dir: str, apply: bool = False) -> dict[str, object]:
    """Dry-run unless apply=True. Returns what would be (or was) deleted."""
    plan = plan_deletions(reports_dir)
    if apply:
        for item in plan:
            path = str(item["path"])
            if os.path.isdir(path):
                import shutil

                shutil.rmtree(path)
            else:
                os.remove(path)
    return {"dry_run": not apply, "deletions": plan}
