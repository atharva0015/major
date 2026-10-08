"""Tests for ladder attempts 3/4: wiring, budgets, disabled-by-default."""

from dataclasses import replace

from healing.orchestrator import HealerOrchestrator, strategy_cost
from healing.policy.engine import load_config


def html_login() -> str:
    return (
        "<html><body><main>"
        '<button id="login-submit-v2" data-testid="login-submit" class="btn">Sign In</button>'
        '<button id="login-cancel" data-testid="login-cancel" class="btn">Cancel</button>'
        "</main></body></html>"
    )


def base_login() -> str:
    return html_login().replace('login-submit-v2"', 'login-submit"')


def test_vision_off_by_default() -> None:
    cfg = load_config()
    assert cfg.vision_enabled is False
    assert cfg.vision_apps == ()


def test_strategy_costs_from_policy() -> None:
    cfg = load_config()
    assert strategy_cost("healenium_match", cfg) == 1.0
    assert strategy_cost("vision_match", cfg) == cfg.vision_max_cost
    assert strategy_cost("llm_attempt", cfg) == cfg.llm_max_cost


def test_disabled_vision_records_only() -> None:
    orch = HealerOrchestrator()
    out = orch.heal_case(
        "renamed_ids:/login",
        "t",
        "renamed_ids",
        html_login(),
        ' id="login-submit"',
        ["nope-a", "nope-b"],
        "login-submit",
        baseline_html=base_login(),
        purpose="submit",
    )
    assert out.healed is None
    assert out.attempts[-1]["strategy"] == "vision_match"
    assert out.attempts[-1]["reason"] == "vision_llm_disabled"


def test_vision_enabled_shortlists_but_ambiguity_escalates() -> None:
    cfg = replace(load_config(), vision_enabled=True)
    orch = HealerOrchestrator(cfg)
    out = orch.heal_case(
        "renamed_ids:/login",
        "t",
        "renamed_ids",
        html_login(),
        ' id="login-submit"',
        ["nope-a", "nope-b"],
        "login-submit",
        baseline_html=base_login(),
        purpose="submit",
    )
    strategies = [a["strategy"] for a in out.attempts]
    assert "vision_match" in strategies
    assert out.healed is None  # ambiguous fingerprints -> no pick, fail closed


def test_fourth_attempt_needs_flag_and_llm_abstains() -> None:
    cfg = replace(load_config(), vision_enabled=True, allow_fourth_attempt=True)
    orch = HealerOrchestrator(cfg)
    out = orch.heal_case(
        "renamed_ids:/login",
        "t",
        "renamed_ids",
        html_login(),
        ' id="login-submit"',
        ["nope-a", "nope-b"],
        "login-submit",
        baseline_html=base_login(),
        purpose="submit",
    )
    assert [a["strategy"] for a in out.attempts][-1] == "llm_attempt"
    assert len(out.attempts) <= 4
