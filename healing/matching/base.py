"""Matcher interface: the only seam the rest of the system may depend on."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Candidate:
    element_id: str
    text: str = ""
    role: str = ""
    name: str = ""
    attrs: dict[str, str] = field(default_factory=dict)
    position: int = 0
    neighbors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScoredCandidate:
    candidate: Candidate
    score: float
    contributions: dict[str, float] = field(default_factory=dict)


class Matcher(ABC):
    """Attempt-1 matcher. Implementations only propose; policy gates."""

    @abstractmethod
    def find_candidates(self, html: str) -> list[Candidate]:
        raise NotImplementedError

    @abstractmethod
    def score(self, target: str, candidates: list[Candidate]) -> list[ScoredCandidate]:
        raise NotImplementedError

    @abstractmethod
    def explain(self, choice: ScoredCandidate | None) -> dict[str, object]:
        """Structured explanation record (must come before any narrative)."""
        raise NotImplementedError
