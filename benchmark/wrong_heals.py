"""Seeded wrong heals: plausible but incorrect candidates (fixed seed)."""

from __future__ import annotations

import random

from benchmark.cases import BenchmarkCase

SEED = 42

# Plausible confusions: same form / neighbor product / same prefix.
WRONG_MAP = {
    "login-submit": "login-cancel",
    "checkout-submit": "checkout-cancel",
    "add-cart-1": "add-cart-2",
}


def wrong_candidate(case: BenchmarkCase, candidates: list[str], seed: int = SEED) -> str | None:
    """Deterministic wrong pick: mapped confusion if present, else seeded draw."""
    rng = random.Random(seed)
    if case.correct_element and WRONG_MAP.get(case.correct_element) in candidates:
        return WRONG_MAP[case.correct_element]
    pool = [c for c in candidates if c != (case.correct_element or "")]
    if not pool:
        return None
    return rng.choice(sorted(pool))
