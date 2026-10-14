"""Healenium adapter: implements Matcher by reading backend public API.

No Healenium source modified. Fail closed: any transport/schema doubt
returns no candidates so policy escalates.
"""

from __future__ import annotations

import os
from html.parser import HTMLParser

import httpx

from healing.matching.base import Candidate, Matcher, ScoredCandidate

ADAPTER_VERSION = "healenium-adapter-0.2.0"
BACKEND_IMAGE = "healenium/hlm-backend:3.5.1"
PROXY_IMAGE = "healenium/hlm-proxy:2.2.1"
DEFAULT_SCORE_CAP = 0.6


class _TestIdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.out: list[Candidate] = []
        self._current: dict[str, str] | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = {k: (v or "") for k, v in attrs}
        if "data-testid" in d:
            self._current = d
            self._current["_tag"] = tag
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._current is not None:
            self._text.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if self._current is not None and self._current.get("_tag") == tag:
            tid = self._current.get("data-testid", "")
            self.out.append(
                Candidate(
                    element_id=tid,
                    text=" ".join(t for t in self._text if t),
                    role=tag,
                    name=self._current.get("aria-label", tid),
                    attrs={k: v for k, v in self._current.items() if not k.startswith("_")},
                    position=len(self.out),
                )
            )
            self._current = None
            self._text = []


def parse_candidates(html: str) -> list[Candidate]:
    p = _TestIdParser()
    p.feed(html)
    return p.out


def best_score_for_locator(payload: object, locator: str) -> float | None:
    """Best valid unit score among entries mentioning locator (pure)."""
    import json

    items = payload.get("data", []) if isinstance(payload, dict) else []
    if not isinstance(items, list):
        return None
    best: float | None = None
    for it in items:
        if not isinstance(it, dict):
            continue
        if locator not in json.dumps(it):
            continue
        v = it.get("score")
        if isinstance(v, bool):
            continue
        if isinstance(v, str):
            v = float(v) if v.replace(".", "", 1).isdigit() else None
        if isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0:
            f = float(v)
            best = f if best is None else max(best, f)
    return best


class HealeniumAdapter(Matcher):
    """Thin client over hlm-backend public endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        score_cap: float = DEFAULT_SCORE_CAP,
        timeout_s: float = 2.0,
    ) -> None:
        self.base_url = base_url or os.getenv("HEALENIUM_URL", "http://localhost:7878")
        self.score_cap = score_cap
        self.timeout_s = timeout_s
        self.version = ADAPTER_VERSION

    def find_candidates(self, html: str) -> list[Candidate]:
        return parse_candidates(html)

    def _backend_score(self, locator: str) -> float | None:
        """Best valid score for entries mentioning locator, else None.

        Verified live against hlm-backend 3.5.1: GET /healenium/report/data
        returns {"data": [...], ...}; each entry carries "score" as a
        "0.97"-style string. No query params (the backend ignores them);
        filtering is client-side. Anything else -> None (fail closed).
        """
        try:
            r = httpx.get(
                f"{self.base_url}/healenium/report/data",
                timeout=self.timeout_s,
            )
            if r.status_code != 200:
                return None
            return best_score_for_locator(r.json(), locator)
        except Exception:
            return None

    def score(self, target: str, candidates: list[Candidate]) -> list[ScoredCandidate]:
        out: list[ScoredCandidate] = []
        for c in candidates:
            s = self._backend_score(target)
            if s is None:
                continue  # fail closed: skip unscored candidates
            if s < self.score_cap:
                continue
            out.append(ScoredCandidate(candidate=c, score=s, contributions={"healenium_score": s}))
        return sorted(out, key=lambda x: x.score, reverse=True)

    def explain(self, choice: ScoredCandidate | None) -> dict[str, object]:
        return {
            "matcher": "healenium",
            "adapter_version": self.version,
            "backend_image": BACKEND_IMAGE,
            "proxy_image": PROXY_IMAGE,
            "score_cap": self.score_cap,
            "base_url": self.base_url,
            "choice": None
            if choice is None
            else {
                "element_id": choice.candidate.element_id,
                "score": choice.score,
                "contributions": choice.contributions,
            },
        }
