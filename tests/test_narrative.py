"""Tests for template narrative + consistency check (no LLM)."""

from healing.xai.narrative import consistency_check, render_narrative
from healing.xai.records import make_record


def record():  # type: ignore[no-untyped-def]
    return make_record(
        heal_id="heal-1",
        test="login",
        step="s1",
        classification="locator_drift",
        selected="login-submit",
        thresholds_applied={"high": 0.8},
        critic_checks={"verdict": "unverified"},
        escalation_reason=None,
        model_version="m",
        prompt_version="p",
        policy_version="pol",
        config_version="cfg",
    )


def test_narrative_maps_to_record() -> None:
    r = record()
    text = render_narrative(r)
    assert text  # record came first, narrative second
    assert consistency_check(text, r)["ok"] is True


def test_tampered_text_fails_check() -> None:
    r = record()
    bad = render_narrative(r).replace("login-submit", "other-button")
    result = consistency_check(bad, r)
    assert result["ok"] is False
    assert result["missing"]
