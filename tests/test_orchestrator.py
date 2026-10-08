"""Tests for the orchestrator pipeline order and fail-closed gates."""

from healing.orchestrator import HealerOrchestrator


def test_blocked_class_short_circuits_before_heal() -> None:
    orch = HealerOrchestrator()
    html = "<html><body><!-- removed:primary-action --></body></html>"
    out = orch.heal_case(
        "removed_element:/login", "t", "removed_element", html, ' id="x"', ["a", "b"], None
    )
    assert out.healed is None
    assert out.decision == "fail_escalate"
    assert out.classification == "genuine_regression"
    assert orch.passed_to_heal == 0
    # Record exists before narrative; narrative matches record.
    assert out.record.heal_id in out.narrative


def test_locator_drift_flows_to_unverified_heal() -> None:
    orch = HealerOrchestrator()
    html = '<button id="login-submit-v2" data-testid="login-submit">x</button>'
    out = orch.heal_case(
        "renamed_ids:/login",
        "t",
        "renamed_ids",
        html,
        ' id="login-submit"',
        ["login-submit", "other"],
        "login-submit",
    )
    assert out.classification == "locator_drift"
    assert out.decision == "heal_unverified"  # stub Critic returns unverified
    assert out.healed == "login-submit"
