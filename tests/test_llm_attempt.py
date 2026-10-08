"""Tests for the LLM attempt: masking, caps, JSON validation, DOM gate."""

from healing.matching.llm_attempt import (
    DisabledLlm,
    SelfHostedLlm,
    build_prompt,
    parse_proposal,
    validate_against_dom,
)

HTML = '<button data-testid="buy" class="btn">Buy ada@example.com</button>'


def test_disabled_abstains() -> None:
    assert DisabledLlm().propose("anything").abstained is True


def test_prompt_masked_and_capped() -> None:
    prompt = build_prompt(HTML + "x" * 5000, "buy", ["buy"], max_dom_chars=100)
    assert "ada@example.com" not in prompt
    assert "[email]" in prompt
    assert "truncated" in prompt


def test_parse_requires_selector_plus_evidence() -> None:
    assert parse_proposal("not json").abstained is True
    assert parse_proposal('{"selector": ""}').abstained is True
    assert parse_proposal('{"selector": "buy"}').abstained is True
    good = parse_proposal('{"selector": "buy", "evidence": ["text match"]}')
    assert (good.abstained, good.selector) == (False, "buy")


def test_dom_gate_refuses_ghost_selector() -> None:
    good = parse_proposal('{"selector": "buy", "evidence": ["e"]}')
    assert validate_against_dom(good, HTML) == "buy"
    ghost = parse_proposal('{"selector": "ghost", "evidence": ["e"]}')
    assert validate_against_dom(ghost, HTML) is None


def test_self_hosted_fails_closed() -> None:
    llm = SelfHostedLlm(url="")
    assert llm.propose("p").abstained is True
    down = SelfHostedLlm(url="http://127.0.0.1:1/nope", timeout_s=0.2)
    assert down.propose("p").abstained is True
