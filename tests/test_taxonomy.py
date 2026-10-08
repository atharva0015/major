"""Tests for the failure taxonomy (AGENTS.md: fail closed, small diffs)."""

from benchmark.cases import CASES
from healing.classifier.taxonomy import LABELS, FailureClass, should_heal


def test_all_six_classes_exist() -> None:
    assert {c.value for c in FailureClass} == {
        "locator_drift",
        "data_issue",
        "timing_issue",
        "environment_issue",
        "genuine_regression",
        "contract_change",
    }


def test_only_locator_drift_heals() -> None:
    for fc in FailureClass:
        assert should_heal(fc) == (fc == FailureClass.LOCATOR_DRIFT)


def test_every_case_labeled() -> None:
    drift_modes = {c.drift_mode for c in CASES}
    assert set(LABELS) == drift_modes
    for c in CASES:
        assert c.true_class in {fc.value for fc in FailureClass}


def test_three_adversarial_no_heal() -> None:
    no_heal = {c.drift_mode for c in CASES if not c.should_heal}
    assert {"removed_element", "swapped_roles", "duplicate_buttons"} <= no_heal
    assert CASES and all(c.correct_element is None for c in CASES if not c.should_heal)
