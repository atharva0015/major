"""Visual similarity via deterministic DOM-derived fingerprints (stdlib only).

No real screenshots exist in this benchmark (server-rendered strings), so a
"crop" is a visual descriptor of the element: tag, class tokens, text
shape, siblings, position. Fingerprints are deterministic, versioned, and
the only thing the ladder may use. A self-hosted embedding model can be
plugged in behind the same interface via configuration; unreachable or
misconfigured endpoints fail closed to local fingerprints.
"""

from __future__ import annotations

import hashlib
import math
import os

import httpx

from healing.matching.base import Candidate, ScoredCandidate

VISION_VERSION = "vision-0.1.0"
DIM = 16


def crop_features(html: str, testid: str) -> tuple[float, ...]:
    """Deterministic visual fingerprint of one element. Pure function."""
    idx = html.find(f'data-testid="{testid}"')
    if idx == -1:
        return tuple(0.0 for _ in range(DIM))
    open_tag = html.rfind("<", 0, idx)
    tag_end = html.find(">", open_tag)
    tag_text = html[open_tag + 1 : tag_end]
    tag = tag_text.split(" ")[0] if tag_text else ""
    close = html.find(f"</{tag}>", tag_end) if tag else -1
    inner = html[tag_end + 1 : close] if close != -1 else ""
    words = inner.split()
    text_len = len(inner.strip())
    vec = [
        float(len(tag)),
        float(sum(ord(c) for c in tag) % 64) / 64.0,
        float(tag_text.count("class=")),
        float(tag_text.count("btn")),
        float(tag_text.count("primary")),
        float(text_len) / 64.0,
        float(len(words)) / 8.0,
        float(sum(1 for w in words if w and w[0].isupper())) / 4.0,
        float(html.count("<button")) / 8.0,
        float(html.count("<a ")) / 8.0,
        float(html.count("<div")) / 16.0,
        float(idx) / max(len(html), 1),
        float(tag_text.count("data-testid=")),
        float(sum(ord(c) for c in testid) % 64) / 64.0,
        float(len(testid)) / 32.0,
        float(hashlib.sha256(testid.encode()).digest()[0]) / 255.0,
    ]
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return tuple(round(v / norm, 6) for v in vec)


def cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    denom = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if not denom:
        return 0.0
    return round(sum(x * y for x, y in zip(a, b)) / denom, 6)


def shortlist(
    target: tuple[float, ...],
    crops: dict[str, tuple[float, ...]],
    k: int = 3,
    margin: float = 0.05,
) -> tuple[list[ScoredCandidate], bool]:
    """Rank crops by similarity. Returns (ranked, ambiguous)."""
    ranked = sorted(crops.items(), key=lambda kv: cosine(target, kv[1]), reverse=True)
    out = [
        ScoredCandidate(Candidate(element_id=tid), cosine(target, vec), {"visual": 0.0})
        for tid, vec in ranked[:k]
    ]
    for sc in out:
        sc.contributions["visual"] = sc.score
    ambiguous = len(out) > 1 and (out[0].score - out[1].score) < margin
    return out, ambiguous


class SelfHostedEmbedding:
    """Optional self-hosted embedding model (httpx). Masked payloads only."""

    def __init__(self, url: str | None = None, timeout_s: float = 10.0) -> None:
        self.url = url or os.getenv("VISION_EMBEDDING_URL", "")
        self.timeout_s = timeout_s

    def embed(self, descriptors: list[str]) -> list[tuple[float, ...]] | None:
        """Return vectors, or None on any failure (fail closed to local)."""
        if not self.url:
            return None
        try:
            from healing.security.masking import mask_pii

            r = httpx.post(
                self.url,
                json={"inputs": [mask_pii(d) for d in descriptors]},
                timeout=self.timeout_s,
            )
            if r.status_code != 200:
                return None
            data = r.json()
            vecs = data.get("vectors", [])
            if not vecs or not all(len(v) == len(vecs[0]) for v in vecs):
                return None
            return [tuple(float(x) for x in v) for v in vecs]
        except Exception:
            return None
