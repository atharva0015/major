"""Dedupe: one shared page-object fix, one PR, for many failing tests."""

from __future__ import annotations


def group_by_locator(failures: list[dict[str, str]]) -> dict[str, list[str]]:
    """Group failing test ids by their shared broken locator/page object."""
    groups: dict[str, list[str]] = {}
    for f in failures:
        groups.setdefault(f["locator"], []).append(f["test"])
    return groups


def plan_prs(groups: dict[str, list[str]]) -> list[dict[str, object]]:
    """One PR per shared locator (fix the page object once)."""
    return [
        {"branch": f"heal/shared-{i}", "locator": loc, "tests": sorted(tests)}
        for i, (loc, tests) in enumerate(sorted(groups.items()))
    ]
