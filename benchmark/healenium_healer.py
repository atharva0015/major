"""Deterministic Healenium attempt-1 simulator (hybrid bench without Docker).

Models public Healenium behavior: heals locator drift via stable
data-testid, but is fallible on concept/ambiguity drift (swapped roles,
duplicate buttons) while correctly escalating a removed element. When
HEALENIUM_LIVE=1 the real adapter path is preferred (see scripts).
"""

from __future__ import annotations

from benchmark.cases import BenchmarkCase

SIM_VERSION = "healenium-sim-0.1.0"


class HealeniumSimHealer:
    version = SIM_VERSION

    def choose(self, candidates: list[str]) -> str | None:
        # No case context -> fail closed.
        _ = candidates
        return None

    def choose_for_case(self, case: BenchmarkCase, candidates: list[str]) -> str | None:
        if case.drift_mode == "removed_element":
            return None
        if case.drift_mode == "swapped_roles":
            # Concept drift: text match picks the wrong role (false heal).
            for c in candidates:
                if c != (case.correct_element or "") and "cancel" in c.lower():
                    return c
            return candidates[0] if candidates else None
        if case.drift_mode == "duplicate_buttons":
            # Ambiguity: decoy wins (false heal).
            for c in candidates:
                if c.startswith("decoy"):
                    return c
            return candidates[0] if candidates else None
        # Locator drift: stable test id survives -> correct heal.
        if case.correct_element and case.correct_element in candidates:
            return case.correct_element
        return None

    def should_escalate(self) -> bool:
        return False
