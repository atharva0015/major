"""Tests for the attempt ladder: cap, strategies, budgets, no-retry on genuine."""

from healing.orchestrator import HealerOrchestrator
from healing.policy.engine import load_config


def html_login() -> str:
    return (
        "<html><body><main>"
        '<button id="login-submit-v2" data-testid="login-submit" class="btn">Sign In</button>'
        '<button id="login-cancel" data-testid="login-cancel" class="btn">Cancel</button>'
        "</main></body></html>"
    )


def base_login() -> str:
    return (
        "<html><body><main>"
        '<button id="login-submit" data-testid="login-submit" class="btn">Sign In</button>'
        '<button id="login-cancel" data-testid="login-cancel" class="btn">Cancel</button>'
        "</main></body></html>"
    )


def test_ladder_heals_on_attempt_1_with_critic_pass() -> None:
    orch = HealerOrchestrator()
    out = orch.heal_case(
        "renamed_ids:/login",
        "t",
        "renamed_ids",
        html_login(),
        ' id="login-submit"',
        ["login-submit", "login-cancel"],
        "login-submit",
        baseline_html=base_login(),
        key_elements=("login-submit", "login-cancel"),
        purpose="submit",
    )
    assert out.healed == "login-submit"
    assert out.attempts and out.attempts[0]["strategy"] == "healenium_match"
    assert out.decision in ("heal_pr", "heal_unverified")


def test_cap_is_three_and_fourth_needs_flag() -> None:
    orch = HealerOrchestrator()
    assert orch.config.max_attempts == 3
    assert orch.config.allow_fourth_attempt is False
    # Force total failure: candidates with no correct element.
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
    assert len(out.attempts) <= 3
    assert out.healed is None


def test_no_retries_for_genuine_regressions() -> None:
    orch = HealerOrchestrator()
    html = "<html><body><!-- removed:primary-action --></body></html>"
    out = orch.heal_case(
        "removed_element:/login", "t", "removed_element", html, ' id="x"', ["a"], None
    )
    assert out.attempts == () and out.decision == "fail_escalate"


def test_strategies_differ_across_attempts() -> None:
    from healing.orchestrator import STRATEGIES

    assert STRATEGIES[0] != STRATEGIES[1]
    assert load_config().max_attempts == 3
