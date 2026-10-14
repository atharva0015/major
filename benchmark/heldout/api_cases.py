"""Held-out API cases: new endpoint/mode/approval combos (11 cases).

Labels derived from the documented classifier rules before running:
401 with unchanged spec -> expired_credential (heal); breaking +
approved + rename-only -> approved_spec_change (heal); breaking otherwise
-> contract_change; stale payload data -> stale_data (heal); unchanged
spec with no credential/data cause -> unapproved_change (likely defect).
"""

from __future__ import annotations

from healing.nonui.pipeline import ApiCase

HELDOUT_API_CASES: list[ApiCase] = [
    ApiCase("heldout:renamed-unapproved", "renamed_field", "GET /api/products"),
    ApiCase("heldout:rename-cart-approved", "renamed_field", "POST /api/cart", approved=True),
    ApiCase("heldout:coupon-on-get", "new_required_field", "GET /api/products"),
    ApiCase("heldout:coupon-approved", "new_required_field", "POST /api/cart", approved=True),
    ApiCase("heldout:removed-products-view", "removed_endpoint", "GET /api/products"),
    ApiCase("heldout:token-cart", "expired_token", "GET /api/cart"),
    ApiCase("heldout:token-checkout", "expired_token", "POST /api/checkout"),
    ApiCase("heldout:stale-cart-view", "stale_seed", "GET /api/cart"),
    ApiCase("heldout:stale-checkout", "stale_seed", "POST /api/checkout"),
    ApiCase("heldout:type-cart", "type_change", "POST /api/cart"),
    ApiCase("heldout:pact-products", "none", "GET /api/products", pact=True),
]

HELDOUT_API_EXPECTED: dict[str, tuple[str, bool]] = {
    "heldout:renamed-unapproved": ("contract_change", False),
    "heldout:rename-cart-approved": ("approved_spec_change", True),
    "heldout:coupon-on-get": ("contract_change", False),
    "heldout:coupon-approved": ("contract_change", False),
    "heldout:removed-products-view": ("contract_change", False),
    "heldout:token-cart": ("expired_credential", True),
    "heldout:token-checkout": ("expired_credential", True),
    "heldout:stale-cart-view": ("unapproved_change", False),
    "heldout:stale-checkout": ("unapproved_change", False),
    "heldout:type-cart": ("contract_change", False),
    "heldout:pact-products": ("contract_change", False),
}
