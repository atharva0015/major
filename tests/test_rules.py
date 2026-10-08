"""Tests for rules classifier: every signal class + never-heal gate."""

from healing.classifier.rules import FailureSignals, classify
from healing.policy.engine import load_config


def cfg():  # type: ignore[no-untyped-def]
    return load_config()


def test_locator_drift_markers() -> None:
    c = classify(FailureSignals("no such element id=x", "login-submit-v2", 0.05, True), cfg())
    assert c.failure_class == "locator_drift"
    assert "locator_marker" in c.fired_rules
    assert abs(sum(c.probabilities.values()) - 1.0) < 1e-6


def test_removed_is_genuine_regression() -> None:
    c = classify(FailureSignals("no such element", "removed:primary-action", 0.1, True), cfg())
    assert c.failure_class == "genuine_regression"


def test_swapped_is_genuine_regression() -> None:
    c = classify(FailureSignals("click went somewhere", "swapped:button-roles", 0.2, True), cfg())
    assert c.failure_class == "genuine_regression"


def test_decoy_is_environment_issue() -> None:
    c = classify(
        FailureSignals("multiple matching elements", "decoy-buy duplicate", 0.1, True),
        cfg(),
    )
    assert c.failure_class == "environment_issue"


def test_network_fault_is_environment_issue() -> None:
    c = classify(FailureSignals("timeout waiting for element", "", 0.0, False), cfg())
    assert c.failure_class == "environment_issue"


def test_contract_change_never_heals() -> None:
    from healing.policy.engine import decide

    c = classify(FailureSignals("schema mismatch v2", "contract openapi", 0.0, True), cfg())
    assert c.failure_class == "contract_change"
    d = decide(c.failure_class, 0.99, 1.0, True, cfg())
    assert d.action == "fail_escalate"


def test_unknown_fails_closed() -> None:
    c = classify(FailureSignals("", "", 0.0, True), cfg())
    assert c.failure_class == "environment_issue"
