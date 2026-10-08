"""Assertion guard: reject weakened assertions / thresholds / SLAs.

Any proposed test change that removes or weakens an assertion, or edits a
performance threshold or SLA, is refused unless a human reviewer has
explicitly signed off (sign-off token). Deterministic, plain code.
"""

from __future__ import annotations

import re

WEAKEN_PATTERNS = (
    re.compile(r"^\s*-\s*assert\b"),  # removed assertion line
    re.compile(r"assert\s+\S+\s+is\s+not\s+None\s*(#|$)"),  # == weakened to existence
    re.compile(r"assert\s+True\b"),  # vacuous assertion
    re.compile(r"(?i)\b(timeout|threshold|sla|latency_ms|max_ms)\b\s*[:=]"),
)

STRENGTHENING_PREFIX = "+"


def guard_diff(diff: str, human_signoff: str | None = None) -> tuple[bool, str]:
    """Return (allowed, reason). Weakening without sign-off is refused."""
    added_asserts = [
        ln for ln in diff.splitlines() if ln.startswith(STRENGTHENING_PREFIX) and "assert" in ln
    ]
    removed_asserts = [
        ln
        for ln in diff.splitlines()
        if ln.startswith("-") and not ln.startswith("---") and "assert" in ln
    ]
    weakened = [
        ln
        for ln in diff.splitlines()
        if ln.startswith(STRENGTHENING_PREFIX) and WEAKEN_PATTERNS[1].search(ln)
    ]
    if WEAKEN_PATTERNS[0].search(diff) or removed_asserts:
        if human_signoff:
            return True, f"assertion_removed_with_signoff:{human_signoff}"
        return False, "refused: removes an assertion"
    if weakened or WEAKEN_PATTERNS[2].search(diff):
        if human_signoff:
            return True, f"assertion_weakened_with_signoff:{human_signoff}"
        return False, "refused: weakens an assertion"
    for ln in diff.splitlines():
        if ln.startswith(STRENGTHENING_PREFIX) and WEAKEN_PATTERNS[3].search(ln):
            if human_signoff:
                return True, f"threshold_changed_with_signoff:{human_signoff}"
            return False, "refused: changes a performance threshold or SLA"
    if added_asserts or "assert" in diff:
        return True, "ok: assertions preserved or strengthened"
    return True, "ok: no assertions touched"
