"""Tests for demo_app order processing and analytics."""

from __future__ import annotations

from demo_app.orders import (
    calculate_loyalty_tier,
    generate_invoice_manifest,
    log_customer_event,
    match_promotions,
)


def test_log_customer_event_isolated() -> None:
    res = log_customer_event("checkout_started", [])
    assert res == ["checkout_started"]


def test_match_promotions() -> None:
    cart = ["item-1", "item-2", "item-3"]
    promos = ["item-2", "item-4"]
    matches = match_promotions(cart, promos)
    assert matches == ["item-2"]


def test_generate_invoice_manifest() -> None:
    items: list[dict[str, object]] = [{"name": "Widget", "price": 9.99}]
    manifest = generate_invoice_manifest(101, items)
    assert "INVOICE #101" in manifest
    assert "Widget" in manifest


def test_calculate_loyalty_tier() -> None:
    res = calculate_loyalty_tier(4)
    assert res == 5
