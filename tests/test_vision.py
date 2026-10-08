"""Tests for vision fingerprints, shortlist, and self-hosted fallback."""

from healing.matching.vision import (
    SelfHostedEmbedding,
    cosine,
    crop_features,
    shortlist,
)

HTML = (
    "<html><body><main>"
    '<button id="login-submit-v2" data-testid="login-submit"'
    ' class="btn btn-primary">Sign In</button>'
    '<button id="login-cancel" data-testid="login-cancel" class="btn">Cancel</button>'
    "</main></body></html>"
)


def test_fingerprints_deterministic() -> None:
    assert crop_features(HTML, "login-submit") == crop_features(HTML, "login-submit")
    assert len(crop_features(HTML, "login-submit")) == 16
    assert crop_features(HTML, "missing") != crop_features(HTML, "login-submit")


def test_cosine_self_is_one() -> None:
    v = crop_features(HTML, "login-submit")
    assert cosine(v, v) == 1.0


def test_shortlist_ranks_correct_first() -> None:
    target = crop_features(HTML, "login-submit")
    crops = {c: crop_features(HTML, c) for c in ("login-submit", "login-cancel")}
    ranked, _ = shortlist(target, crops, k=2, margin=0.0)
    assert ranked[0].candidate.element_id == "login-submit"


def test_ambiguity_flag_escalates() -> None:
    target = crop_features(HTML, "login-submit")
    crops = {c: crop_features(HTML, c) for c in ("login-submit", "login-cancel")}
    _, ambiguous = shortlist(target, crops, k=2, margin=1.0)
    assert ambiguous is True


def test_self_hosted_fails_closed() -> None:
    assert SelfHostedEmbedding(url="").embed(["x"]) is None
    assert SelfHostedEmbedding(url="http://127.0.0.1:1/nope", timeout_s=0.2).embed(["x"]) is None
