"""Demo web app: 4 pages + REST API with injectable UI drift."""

from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from demo_app.api_drift import STALE_PRODUCTS, VALID_TOKEN, api_drift_mode, server_token
from demo_app.drift import DEFAULT_SEED, apply_drift
from demo_app.orders import (
    calculate_loyalty_tier,
    compute_tax_rate,
    generate_invoice_manifest,
    log_customer_event,
    match_promotions,
    save_receipt_audit,
)

PRODUCTS: list[dict[str, object]] = [
    {"id": 1, "name": "Widget Pro", "price": 9.99},
    {"id": 2, "name": "Gadget Max", "price": 14.99},
    {"id": 3, "name": "Doohickey Ultra", "price": 4.99},
]

CART: list[int] = []

app = FastAPI(title="demo_app", description="NovaMart E-Commerce Store & Order Analytics")


def drift_mode() -> str:
    return os.getenv("DRIFT_MODE", "none")


def render(html: str) -> str:
    return apply_drift(html, drift_mode(), DEFAULT_SEED)


class AddCart(BaseModel):
    product_id: int
    coupon: str | None = None


class TaxRequest(BaseModel):
    subtotal: float
    tax_amount: float


class PromoRequest(BaseModel):
    cart_items: list[str]
    active_promos: list[str]


class LoyaltyRequest(BaseModel):
    level: int


class InvoiceRequest(BaseModel):
    order_id: int
    items: list[dict[str, object]]


class EventRequest(BaseModel):
    event_name: str


def _server_token() -> str:
    return server_token()


def _check_auth() -> None:
    if os.getenv("TEST_TOKEN", VALID_TOKEN) != _server_token():
        raise HTTPException(status_code=401, detail="token expired")


@app.get("/login", response_class=HTMLResponse)
def login_page() -> str:
    return render(
        "<html><body><main>"
        "<h1>Sign In</h1>"
        '<form id="login-form" data-testid="login-form">'
        '<label for="username">Username</label>'
        '<input id="username" data-testid="username" name="username" />'
        '<label for="password">Password</label>'
        '<input id="password" data-testid="password" name="password" type="password" />'
        '<button id="login-submit" data-testid="login-submit" '
        'class="btn btn-primary">Sign In</button>'
        '<button id="login-cancel" data-testid="login-cancel" '
        'class="btn">Cancel</button>'
        "</form></main></body></html>"
    )


@app.get("/products", response_class=HTMLResponse)
def products_page() -> str:
    cards = "".join(
        f'<div class="product-card" data-testid="product-{p["id"]}">'
        f"<h2>{p['name']}</h2><span>${p['price']}</span>"
        f'<button id="add-cart-{p["id"]}" data-testid="add-cart-{p["id"]}" '
        'class="btn btn-primary">Buy Now</button></div>'
        for p in PRODUCTS
    )
    return render(f"<html><body><main><h1>Products</h1>{cards}</main></body></html>")


@app.get("/cart", response_class=HTMLResponse)
def cart_page() -> str:
    rows = (
        "".join(
            f'<div class="cart-item" data-testid="cart-item-{pid}">Item {pid}</div>' for pid in CART
        )
        or '<p data-testid="cart-empty">Cart is empty</p>'
    )
    return render(
        "<html><body><main><h1>Cart</h1>"
        f"{rows}"
        '<a id="cart-checkout" data-testid="cart-checkout" '
        'class="btn btn-primary" href="/checkout">Checkout</a>'
        "</main></body></html>"
    )


@app.get("/checkout", response_class=HTMLResponse)
def checkout_page() -> str:
    return render(
        "<html><body><main>"
        "<h1>Checkout</h1>"
        '<form id="checkout-form" data-testid="checkout-form">'
        '<button id="checkout-submit" data-testid="checkout-submit" '
        'class="btn btn-primary">Checkout</button>'
        '<button id="checkout-cancel" data-testid="checkout-cancel" '
        'class="btn">Cancel</button>'
        "</form></main></body></html>"
    )


@app.get("/api/products")
def api_products() -> list[dict[str, object]]:
    _check_auth()
    mode = api_drift_mode()
    if mode == "stale_seed":
        return [dict(p) for p in STALE_PRODUCTS]
    items = [dict(p) for p in PRODUCTS]
    if mode == "renamed_field":
        for p in items:
            p["amount"] = p.pop("price")
    elif mode == "type_change":
        for p in items:
            p["price"] = str(p["price"])
    return items


@app.get("/api/cart")
def api_cart() -> dict[str, list[int]]:
    _check_auth()
    return {"items": list(CART)}


@app.post("/api/cart")
def api_add_cart(item: AddCart) -> dict[str, list[int]]:
    _check_auth()
    if api_drift_mode() == "new_required_field" and not item.coupon:
        raise HTTPException(status_code=422, detail="missing required field: coupon")
    CART.append(item.product_id)
    return {"items": list(CART)}


@app.post("/api/checkout")
def api_checkout() -> dict[str, str]:
    _check_auth()
    if api_drift_mode() == "removed_endpoint":
        raise HTTPException(status_code=404, detail="endpoint removed")
    CART.clear()
    return {"status": "ordered"}


# ============================================================================
# Order & Analytics Interactive Endpoints (Exercising demo_app/orders.py)
# ============================================================================


@app.post("/api/orders/tax")
def api_compute_tax(req: TaxRequest) -> dict[str, object]:
    """Calculates tax rate using demo_app.orders.compute_tax_rate."""
    try:
        rate = compute_tax_rate(req.subtotal, req.tax_amount)
        return {"success": True, "effective_tax_rate": rate}
    except ZeroDivisionError as exc:
        return {
            "success": False,
            "error": f"ZeroDivisionError: {exc}",
            "bug_detected": True,
            "hint": "This bug is automatically repaired by the Codebase Healing Studio!",
        }


@app.post("/api/orders/event")
def api_log_event(req: EventRequest) -> dict[str, object]:
    """Logs customer activity using demo_app.orders.log_customer_event."""
    history = log_customer_event(req.event_name)
    return {
        "success": True,
        "event_logged": req.event_name,
        "event_history": history,
        "history_count": len(history),
    }


@app.post("/api/orders/match-promos")
def api_match_promos(req: PromoRequest) -> dict[str, object]:
    """Matches promotion codes using demo_app.orders.match_promotions."""
    t0 = time.perf_counter()
    matched = match_promotions(req.cart_items, req.active_promos)
    duration_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "success": True,
        "matched_promotions": matched,
        "match_count": len(matched),
        "execution_time_ms": round(duration_ms, 3),
    }


@app.post("/api/orders/loyalty")
def api_calc_loyalty(req: LoyaltyRequest) -> dict[str, object]:
    """Calculates tiered multiplier using demo_app.orders.calculate_loyalty_tier."""
    if req.level > 32:
        raise HTTPException(status_code=400, detail="Level capped at 32 for CPU protection")
    t0 = time.perf_counter()
    multiplier = calculate_loyalty_tier(req.level)
    duration_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "success": True,
        "level": req.level,
        "points_multiplier": multiplier,
        "execution_time_ms": round(duration_ms, 3),
    }


@app.post("/api/orders/invoice")
def api_generate_invoice(req: InvoiceRequest) -> dict[str, object]:
    """Generates invoice and audits receipt using demo_app.orders."""
    t0 = time.perf_counter()
    manifest = generate_invoice_manifest(req.order_id, req.items)
    save_receipt_audit(req.order_id, manifest)
    duration_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "success": True,
        "order_id": req.order_id,
        "manifest": manifest,
        "audit_file": f"receipt_audit_{req.order_id}.log",
        "execution_time_ms": round(duration_ms, 3),
    }


# ============================================================================
# Modern E-Commerce Storefront UI
# ============================================================================

STOREFRONT_PATH = Path(__file__).parent / "storefront.html"


@app.get("/", response_class=HTMLResponse)
def index_storefront() -> HTMLResponse:
    """Renders the NovaMart E-Commerce Store & Order Analytics Live Console."""
    if STOREFRONT_PATH.exists():
        return HTMLResponse(STOREFRONT_PATH.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>NovaMart Demo Storefront</h1>")


def main() -> None:
    import uvicorn

    host = os.getenv("DEMO_APP_HOST", "127.0.0.1")
    port = int(os.getenv("DEMO_APP_PORT", "8082"))
    print(f"Starting Demo E-Commerce App on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
