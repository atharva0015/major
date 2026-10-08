"""API benchmark cases (deterministic, fixed seed)."""

from healing.nonui.pipeline import ApiCase

API_CASES: list[ApiCase] = [
    ApiCase("renamed_field:products", "renamed_field", "GET /api/products", approved=True),
    ApiCase("new_required_field:cart", "new_required_field", "POST /api/cart"),
    ApiCase("removed_endpoint:checkout", "removed_endpoint", "POST /api/checkout"),
    ApiCase("expired_token:products", "expired_token", "GET /api/products"),
    ApiCase("stale_seed:products", "stale_seed", "GET /api/products"),
    ApiCase("type_change:products", "type_change", "GET /api/products"),
    ApiCase("pact:cart", "none", "POST /api/cart", pact=True),
]

EXPECTED = {
    "renamed_field:products": ("approved_spec_change", True),
    "new_required_field:cart": ("contract_change", False),
    "removed_endpoint:checkout": ("contract_change", False),
    "expired_token:products": ("expired_credential", True),
    "stale_seed:products": ("stale_data", True),
    "type_change:products": ("contract_change", False),
    "pact:cart": ("contract_change", False),
}
