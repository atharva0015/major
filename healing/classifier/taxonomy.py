"""Failure taxonomy: every benchmark case carries its true class (fail closed)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FailureClass(str, Enum):  # noqa: UP042
    LOCATOR_DRIFT = "locator_drift"
    DATA_ISSUE = "data_issue"
    TIMING_ISSUE = "timing_issue"
    ENVIRONMENT_ISSUE = "environment_issue"
    GENUINE_REGRESSION = "genuine_regression"
    CONTRACT_CHANGE = "contract_change"


@dataclass(frozen=True)
class BenchmarkLabel:
    case_id: str
    true_class: FailureClass
    should_heal: bool


def should_heal(fc: FailureClass) -> bool:
    """Only locator drift may be healed; everything else escalates."""
    return fc == FailureClass.LOCATOR_DRIFT


# Adversarial cases (must NOT heal): removed_element, swapped_roles,
# duplicate_buttons. All other drifts are healable locator drift.
LABELS: dict[str, BenchmarkLabel] = {
    "renamed_ids": BenchmarkLabel("renamed_ids", FailureClass.LOCATOR_DRIFT, True),
    "changed_classes": BenchmarkLabel("changed_classes", FailureClass.LOCATOR_DRIFT, True),
    "moved_elements": BenchmarkLabel("moved_elements", FailureClass.LOCATOR_DRIFT, True),
    "reskinned_layout": BenchmarkLabel("reskinned_layout", FailureClass.LOCATOR_DRIFT, True),
    "ab_variant_text": BenchmarkLabel("ab_variant_text", FailureClass.LOCATOR_DRIFT, True),
    "removed_element": BenchmarkLabel("removed_element", FailureClass.GENUINE_REGRESSION, False),
    "swapped_roles": BenchmarkLabel("swapped_roles", FailureClass.GENUINE_REGRESSION, False),
    "duplicate_buttons": BenchmarkLabel("duplicate_buttons", FailureClass.ENVIRONMENT_ISSUE, False),
}
