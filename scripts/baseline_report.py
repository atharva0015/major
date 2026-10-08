"""Maintenance-style numbers from benchmark cases + baseline results."""

from __future__ import annotations

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.cases import CASES


def failures_by_class() -> dict[str, int]:
    return dict(Counter(c.true_class for c in CASES))


def locator_drift_share() -> float:
    if not CASES:
        return 0.0
    n = sum(1 for c in CASES if c.true_class == "locator_drift")
    return n / len(CASES)


def estimated_manual_repairs() -> int:
    """Baseline heals nothing, so every should-heal case needs a manual fix."""
    return sum(1 for c in CASES if c.should_heal)


def main() -> None:
    by_class = failures_by_class()
    share = locator_drift_share()
    repairs = estimated_manual_repairs()
    print(f"failures by class: {by_class}")
    print(f"locator drift share: {share:.3f}")
    print(f"estimated manual repairs: {repairs}")


if __name__ == "__main__":
    main()
