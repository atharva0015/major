"""Held-out set structural checks (no outcome assertions; outcomes are measured)."""

from benchmark.heldout.api_cases import HELDOUT_API_CASES, HELDOUT_API_EXPECTED
from benchmark.heldout.ui_cases import HELDOUT_UI_CASES, build_heldout_ui_cases
from healing.classifier.taxonomy import FailureClass
from healing.nonui.classifier import API_CLASSES


def test_ui_count_and_unique_ids() -> None:
    assert len(HELDOUT_UI_CASES) >= 20
    ids = [c.case_id for c in HELDOUT_UI_CASES]
    assert len(set(ids)) == len(ids)
    assert all(i.startswith("heldout:") for i in ids)


def test_ui_labels_valid_and_deterministic() -> None:
    valid = {c.value for c in FailureClass}
    for c in HELDOUT_UI_CASES:
        assert c.true_class in valid
        if not c.should_heal:
            assert c.correct_element is None
    again = build_heldout_ui_cases()
    assert [(c.case_id, c.true_class) for c in again] == [
        (c.case_id, c.true_class) for c in HELDOUT_UI_CASES
    ]


def test_ui_elements_differ_from_original() -> None:
    for c in HELDOUT_UI_CASES:
        assert "login-submit" not in c.locator
        assert "add-cart-1" not in c.locator
        assert "checkout-submit" not in c.locator


def test_api_count_labels_and_expected() -> None:
    assert len(HELDOUT_API_CASES) >= 10
    ids = [c.case_id for c in HELDOUT_API_CASES]
    assert len(set(ids)) == len(ids)
    for c in HELDOUT_API_CASES:
        assert c.case_id in HELDOUT_API_EXPECTED
        exp_class, _ = HELDOUT_API_EXPECTED[c.case_id]
        assert exp_class in API_CLASSES
