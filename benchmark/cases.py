"""Benchmark cases: every drift × representative page, labeled with truth."""

from __future__ import annotations

from dataclasses import dataclass

from healing.classifier.taxonomy import LABELS

DEFAULT_SEED = 42


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    drift_mode: str
    page: str
    locator: str
    correct_element: str | None
    true_class: str
    should_heal: bool


PAGES = ("/login", "/products", "/checkout")

# (page, naive locator that breaks under drift, stable correct element)
# Leading space prevents matching data-testid="..." (which ends in id="...").
TARGETS: dict[str, tuple[str, str]] = {
    "/login": (' id="login-submit"', "login-submit"),
    "/products": (' id="add-cart-1"', "add-cart-1"),
    "/checkout": (' id="checkout-submit"', "checkout-submit"),
}

DRIFTS = [
    "renamed_ids",
    "changed_classes",
    "moved_elements",
    "reskinned_layout",
    "duplicate_buttons",
    "removed_element",
    "swapped_roles",
    "ab_variant_text",
]


def build_cases(seed: int = DEFAULT_SEED) -> list[BenchmarkCase]:
    _ = seed  # fixed order = reproducible
    cases: list[BenchmarkCase] = []
    for drift in DRIFTS:
        label = LABELS[drift]
        for page in PAGES:
            locator, correct = TARGETS[page]
            cases.append(
                BenchmarkCase(
                    case_id=f"{drift}:{page}",
                    drift_mode=drift,
                    page=page,
                    locator=locator,
                    correct_element=None if not label.should_heal else correct,
                    true_class=label.true_class.value,
                    should_heal=label.should_heal,
                )
            )
    return cases


CASES: list[BenchmarkCase] = build_cases()
