"""Transparent rescorer: weighted per-feature contributions (plain code)."""

from __future__ import annotations

from healing.matching.base import Candidate, ScoredCandidate

RESCORER_VERSION = "rescorer-0.1.0"

WEIGHTS: dict[str, float] = {
    "text": 0.25,
    "role": 0.20,
    "name": 0.20,
    "attrs": 0.15,
    "position": 0.10,
    "neighbors": 0.10,
}


def _sim(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a.lower() in b.lower() or b.lower() in a.lower():
        return 0.5
    return 0.0


def feature_scores(target: Candidate, cand: Candidate) -> dict[str, float]:
    attr_hit = 1.0 if target.element_id == cand.element_id else 0.0
    neigh = 1.0 if set(target.neighbors) & set(cand.neighbors) else 0.0
    pos = 1.0 if target.position == cand.position else 0.0
    return {
        "text": _sim(target.text, cand.text),
        "role": _sim(target.role, cand.role),
        "name": _sim(target.name, cand.name),
        "attrs": attr_hit,
        "position": pos,
        "neighbors": neigh,
    }


def rescore(
    target: Candidate,
    candidates: list[Candidate],
    weights: dict[str, float] | None = None,
) -> list[ScoredCandidate]:
    w = weights or WEIGHTS
    out: list[ScoredCandidate] = []
    for c in candidates:
        feats = feature_scores(target, c)
        total = sum(feats[k] * w[k] for k in w)
        contrib = {k: round(feats[k] * w[k], 4) for k in w}
        out.append(ScoredCandidate(candidate=c, score=round(total, 4), contributions=contrib))
    return sorted(out, key=lambda x: x.score, reverse=True)
