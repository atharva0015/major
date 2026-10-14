"""Held-out UI cases: new elements, pages, and locators (24 cases).

Written independently from benchmark/cases.py: none of the original
targets (login-submit, add-cart-1, checkout-submit) appear here. Uses an
anchor-link layout (/cart), form inputs (/login), sibling buttons, and
neighbor products. True classes mirror the documented drift semantics:
locator-affecting drifts heal; removed/swapped/duplicate drifts escalate.
Labels were fixed before running anything.
"""

from __future__ import annotations

from benchmark.cases import BenchmarkCase

# mode -> (true_class, should_heal), same documented semantics as LABELS.
_HELDOUT_LABELS: dict[str, tuple[str, bool]] = {
    "renamed_ids": ("locator_drift", True),
    "changed_classes": ("locator_drift", True),
    "moved_elements": ("locator_drift", True),
    "reskinned_layout": ("locator_drift", True),
    "ab_variant_text": ("locator_drift", True),
    "removed_element": ("genuine_regression", False),
    "swapped_roles": ("genuine_regression", False),
    "duplicate_buttons": ("environment_issue", False),
}

# (drift, page, naive locator substring, correct testid or None)
# Elements are all different from the original benchmark targets.
_SPECS: list[tuple[str, str, str, str | None]] = [
    ("renamed_ids", "/login", ' id="username"', "username"),
    ("renamed_ids", "/login", ' id="password"', "password"),
    ("renamed_ids", "/cart", ' id="cart-checkout"', "cart-checkout"),
    ("changed_classes", "/login", ' id="login-cancel"', "login-cancel"),
    ("changed_classes", "/products", ' id="add-cart-2"', "add-cart-2"),
    ("changed_classes", "/checkout", ' id="checkout-cancel"', "checkout-cancel"),
    ("moved_elements", "/login", ' id="login-cancel"', "login-cancel"),
    ("moved_elements", "/products", ' id="add-cart-3"', "add-cart-3"),
    ("moved_elements", "/cart", ' id="cart-checkout"', "cart-checkout"),
    ("reskinned_layout", "/login", ' id="login-cancel"', "login-cancel"),
    ("reskinned_layout", "/products", ' id="add-cart-2"', "add-cart-2"),
    ("reskinned_layout", "/checkout", ' id="checkout-cancel"', "checkout-cancel"),
    ("duplicate_buttons", "/login", ' id="login-cancel"', None),
    ("duplicate_buttons", "/products", ' id="add-cart-2"', None),
    ("duplicate_buttons", "/checkout", ' id="checkout-cancel"', None),
    ("removed_element", "/login", ' id="login-cancel"', None),
    ("removed_element", "/products", ' id="add-cart-2"', None),
    ("removed_element", "/cart", ' id="cart-checkout"', None),
    ("swapped_roles", "/login", ' id="login-cancel"', None),
    ("swapped_roles", "/products", ' id="add-cart-2"', None),
    ("swapped_roles", "/checkout", ' id="checkout-cancel"', None),
    ("ab_variant_text", "/login", ' id="username"', "username"),
    ("ab_variant_text", "/products", ' id="add-cart-3"', "add-cart-3"),
    ("ab_variant_text", "/checkout", ' id="checkout-cancel"', "checkout-cancel"),
]


def build_heldout_ui_cases() -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    for drift, page, locator, correct in _SPECS:
        true_class, should_heal = _HELDOUT_LABELS[drift]
        cases.append(
            BenchmarkCase(
                case_id=f"heldout:{drift}:{page}:{locator.strip()}",
                drift_mode=drift,
                page=page,
                locator=locator,
                correct_element=correct if should_heal else None,
                true_class=true_class,
                should_heal=should_heal,
            )
        )
    return cases


HELDOUT_UI_CASES: list[BenchmarkCase] = build_heldout_ui_cases()
