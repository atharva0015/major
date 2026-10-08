"""API drift injection for the demo app (deterministic, fixed seed).

Separate API_DRIFT_MODE so UI and API drifts compose independently.
"""

from __future__ import annotations

import os

API_DRIFT_MODES: list[str] = [
    "none",
    "renamed_field",
    "new_required_field",
    "removed_endpoint",
    "expired_token",
    "stale_seed",
    "type_change",
]

DEFAULT_SEED = 42
VALID_TOKEN = "test-token-42"
STALE_PRODUCTS: list[dict[str, object]] = [
    {"id": 101, "name": "StaleWidget", "price": 1.99},
]


def api_drift_mode() -> str:
    return os.getenv("API_DRIFT_MODE", "none")


def server_token() -> str:
    """Token the server currently accepts (rotated under expired_token drift)."""
    if api_drift_mode() == "expired_token":
        return "rotated-token-99"
    return VALID_TOKEN
