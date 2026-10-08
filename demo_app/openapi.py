"""Hand-written minimal OpenAPI-ish specs: the source of truth.

Small deterministic dicts versioned in the repo (not generated), so the
classifier can diff base vs drifted contract without a running server.
"""

from __future__ import annotations

BASE_SPEC: dict[str, object] = {
    "openapi": "3.0.0",
    "paths": {
        "/api/products": {
            "get": {
                "responses": {"200": {"fields": {"id": "int", "name": "str", "price": "float"}}}
            }
        },
        "/api/cart": {
            "get": {"responses": {"200": {"fields": {"items": "list[int]"}}}},
            "post": {
                "required": ["product_id"],
                "responses": {"200": {"fields": {"items": "list[int]"}}},
            },
        },
        "/api/checkout": {"post": {"responses": {"200": {"fields": {"status": "str"}}}}},
    },
    "auth": {"scheme": "bearer", "header": "Authorization"},
}


def spec_for(mode: str) -> dict[str, object]:
    """Drifted spec for an API_DRIFT_MODE (deep-copied, deterministic)."""
    import copy

    spec = copy.deepcopy(BASE_SPEC)
    paths = spec["paths"]
    assert isinstance(paths, dict)
    if mode == "renamed_field":
        fields = paths["/api/products"]["get"]["responses"]["200"]["fields"]
        assert isinstance(fields, dict)
        fields["amount"] = fields.pop("price")
    elif mode == "new_required_field":
        required = paths["/api/cart"]["post"]["required"]
        assert isinstance(required, list)
        required.append("coupon")
    elif mode == "removed_endpoint":
        paths.pop("/api/checkout", None)
    elif mode == "type_change":
        fields = paths["/api/products"]["get"]["responses"]["200"]["fields"]
        assert isinstance(fields, dict)
        fields["price"] = "str"
    return spec
