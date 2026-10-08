"""Demo web app: 4 pages + REST API with injectable UI drift."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from demo_app.api_drift import STALE_PRODUCTS, VALID_TOKEN, api_drift_mode, server_token
from demo_app.drift import DEFAULT_SEED, apply_drift

PRODUCTS: list[dict[str, object]] = [
    {"id": 1, "name": "Widget", "price": 9.99},
    {"id": 2, "name": "Gadget", "price": 14.99},
    {"id": 3, "name": "Doohickey", "price": 4.99},
]

CART: list[int] = []

app = FastAPI(title="demo_app")


def drift_mode() -> str:
    return os.getenv("DRIFT_MODE", "none")


def render(html: str) -> str:
    return apply_drift(html, drift_mode(), DEFAULT_SEED)


class AddCart(BaseModel):
    product_id: int
    coupon: str | None = None


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


def main() -> None:
    print("demo_app ok")


if __name__ == "__main__":
    main()
