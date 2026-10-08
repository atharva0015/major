"""Selenium-style suite for demo_app (hybrid: real WebDriver if present).

Runs headless-browser-free by default via direct view calls + locator
helpers so `make bench` stays deterministic without chromedriver. If
selenium + a driver are available, `test_selenium_driver_present`
exercises it.
"""

from __future__ import annotations

import os

import pytest

from demo_app.app import (
    AddCart,
    api_add_cart,
    api_cart,
    api_checkout,
    api_products,
    cart_page,
    checkout_page,
    login_page,
    products_page,
)
from demo_app.drift import DRIFT_MODES, apply_drift


def get_html(page: str, drift: str = "none") -> str:
    os.environ["DRIFT_MODE"] = drift
    try:
        if page == "/login":
            return login_page()
        if page == "/products":
            return products_page()
        if page == "/cart":
            return cart_page()
        if page == "/checkout":
            return checkout_page()
        raise ValueError(f"unknown page: {page}")
    finally:
        os.environ["DRIFT_MODE"] = "none"


def has_id(html: str, element_id: str) -> bool:
    return f' id="{element_id}"' in html


def has_testid(html: str, testid: str) -> bool:
    return f'data-testid="{testid}"' in html


def test_login_form_present() -> None:
    assert has_testid(get_html("/login"), "login-form")


def test_login_submit_id_baseline() -> None:
    assert has_id(get_html("/login"), "login-submit")


def test_login_cancel_present() -> None:
    assert has_testid(get_html("/login"), "login-cancel")


def test_login_semantic_main() -> None:
    assert "<main>" in get_html("/login")


def test_products_page_lists_three() -> None:
    html = get_html("/products")
    assert html.count("product-") >= 3


def test_products_add_buttons() -> None:
    html = get_html("/products")
    assert has_id(html, "add-cart-1")
    assert has_id(html, "add-cart-2")


def test_cart_page_empty_state() -> None:
    from demo_app.app import CART

    CART.clear()
    assert has_testid(get_html("/cart"), "cart-empty")


def test_cart_checkout_link() -> None:
    assert has_id(get_html("/cart"), "cart-checkout")


def test_checkout_form_present() -> None:
    assert has_testid(get_html("/checkout"), "checkout-form")


def test_checkout_submit_baseline() -> None:
    assert has_id(get_html("/checkout"), "checkout-submit")


def test_api_products() -> None:
    assert len(api_products()) == 3


def test_api_cart_add_and_read() -> None:
    from demo_app.app import CART

    CART.clear()
    api_add_cart(AddCart(product_id=1))
    assert api_cart() == {"items": [1]}
    CART.clear()


def test_api_checkout_clears_cart() -> None:
    from demo_app.app import CART

    CART.clear()
    api_add_cart(AddCart(product_id=2))
    assert api_checkout() == {"status": "ordered"}
    assert api_cart() == {"items": []}


def test_drift_modes_enumerated() -> None:
    assert set(DRIFT_MODES) == {
        "none",
        "renamed_ids",
        "changed_classes",
        "moved_elements",
        "reskinned_layout",
        "duplicate_buttons",
        "removed_element",
        "swapped_roles",
        "ab_variant_text",
    }


def test_renamed_ids_breaks_naive_locator() -> None:
    assert not has_id(get_html("/login", "renamed_ids"), "login-submit")
    assert has_testid(get_html("/login", "renamed_ids"), "login-submit")


def test_changed_classes_breaks_class_locator() -> None:
    assert "btn btn-primary" not in get_html("/login", "changed_classes")


def test_moved_elements_marks_layout() -> None:
    assert "data-layout-moved" in get_html("/login", "moved_elements")


def test_reskinned_layout_marks_theme() -> None:
    assert "reskinned" in get_html("/login", "reskinned_layout")


def test_duplicate_buttons_adds_decoy() -> None:
    assert "decoy-buy" in get_html("/products", "duplicate_buttons")


def test_duplicate_buttons_decoy_on_all_pages() -> None:
    for page in ("/login", "/products", "/checkout"):
        assert "decoy-" in get_html(page, "duplicate_buttons")


def test_removed_element_drops_primary() -> None:
    assert not has_testid(get_html("/login", "removed_element"), "login-submit")


def test_swapped_roles_marks_concept_drift() -> None:
    assert "swapped:button-roles" in get_html("/login", "swapped_roles")


def test_ab_variant_changes_text() -> None:
    assert "Purchase" in get_html("/products", "ab_variant_text")


def test_drift_deterministic_fixed_seed() -> None:
    html = get_html("/login")
    assert apply_drift(html, "renamed_ids", 42) == apply_drift(html, "renamed_ids", 42)


def test_selenium_driver_if_present() -> None:
    pytest.importorskip("selenium")
    from selenium import webdriver  # type: ignore[import-not-found]

    try:
        driver = webdriver.Chrome()
    except Exception as exc:  # no driver in CI: documented skip
        pytest.skip(f"no browser driver: {exc}")
    driver.quit()
