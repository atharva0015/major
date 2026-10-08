"""Survival: 30/60/90-day heal survival, revert/override rates, freshness.

Real stores have no 90-day history yet: with insufficient data the
functions report pending status instead of inventing numbers. Tests use
seeded synthetic histories.
"""

from __future__ import annotations

import time

DAY = 86400.0


def survival_rate(
    heals: list[dict[str, object]], days: int, now: float | None = None
) -> dict[str, object]:
    """Share of heals still standing (no revert/override) after `days`."""
    now = time.time() if now is None else now
    matured = [h for h in heals if now - float(str(h.get("merged_at", now))) >= days * DAY]
    if not matured:
        return {"days": days, "status": "insufficient_data", "n": 0}
    alive = [h for h in matured if not h.get("reverted") and not h.get("overridden")]
    return {
        "days": days,
        "status": "ok",
        "rate": round(len(alive) / len(matured), 4),
        "n": len(matured),
    }


def revert_rate(heals: list[dict[str, object]]) -> dict[str, object]:
    if not heals:
        return {"status": "insufficient_data", "rate": 0.0, "n": 0}
    n = sum(1 for h in heals if h.get("reverted"))
    return {"status": "ok", "rate": round(n / len(heals), 4), "n": len(heals)}


def override_rate(heals: list[dict[str, object]]) -> dict[str, object]:
    if not heals:
        return {"status": "insufficient_data", "rate": 0.0, "n": 0}
    n = sum(1 for h in heals if h.get("overridden"))
    return {"status": "ok", "rate": round(n / len(heals), 4), "n": len(heals)}


def fingerprint_freshness(last_seen_s: float, max_age_s: float = 90 * DAY) -> dict[str, object]:
    fresh = last_seen_s <= max_age_s
    return {
        "fresh": fresh,
        "age_s": last_seen_s,
        "max_age_s": max_age_s,
        "status": "ok" if fresh else "stale",
    }
