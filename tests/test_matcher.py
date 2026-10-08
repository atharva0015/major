"""Tests for Matcher seam, adapter fail-closed, and rescorer transparency."""

from healing.matching.base import Candidate, Matcher
from healing.matching.healenium_adapter import HealeniumAdapter
from healing.matching.rescorer import WEIGHTS, rescore


def test_weights_sum_to_one() -> None:
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9
    assert set(WEIGHTS) == {"text", "role", "name", "attrs", "position", "neighbors"}


def test_rescore_prefers_exact_and_explains() -> None:
    target = Candidate("buy", text="Buy Now", role="button", name="buy")
    good = Candidate("buy", text="Buy Now", role="button", name="buy")
    bad = Candidate("x", text="Cancel", role="link", name="x")
    ranked = rescore(target, [bad, good])
    assert ranked[0].candidate.element_id == "buy"
    assert abs(sum(ranked[0].contributions.values()) - ranked[0].score) < 1e-9


def test_adapter_fail_closed_without_backend() -> None:
    ad = HealeniumAdapter(base_url="http://127.0.0.1:1", timeout_s=0.2)
    assert isinstance(ad, Matcher)
    cands = [Candidate("a", text="Buy Now")]
    assert ad.score("id=x", cands) == []
    rec = ad.explain(None)
    assert rec["matcher"] == "healenium"
    assert "score_cap" in rec


def test_adapter_finds_testids() -> None:
    ad = HealeniumAdapter()
    html = '<button data-testid="buy" aria-label="Buy">Buy Now</button>'
    cands = ad.find_candidates(html)
    assert [c.element_id for c in cands] == ["buy"]
