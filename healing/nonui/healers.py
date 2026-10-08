"""Allowed API auto-actions (only three). Everything else escalates with the diff."""

from __future__ import annotations

import os
from dataclasses import dataclass

from demo_app.api_drift import server_token

ALLOWED_ACTIONS = ("refresh_token", "regenerate_fixtures", "propose_test_update")


@dataclass(frozen=True)
class ApiHeal:
    action: str  # one of ALLOWED_ACTIONS, or "escalate"
    detail: str
    diff: str = ""


def refresh_token() -> ApiHeal:
    """Refresh the expired test-environment credential (env only, masked in logs)."""
    os.environ["TEST_TOKEN"] = server_token()
    return ApiHeal("refresh_token", "TEST_TOKEN refreshed in test env")


def regenerate_fixtures() -> ApiHeal:
    """Regenerate stale sandbox fixtures (seeded reset)."""
    from demo_app.app import CART, PRODUCTS

    CART.clear()
    if not any(p.get("id") == 1 for p in PRODUCTS):
        PRODUCTS.extend([{"id": 1, "name": "Widget", "price": 9.99}])
    return ApiHeal("regenerate_fixtures", "sandbox fixtures reseeded")


def propose_test_update(old_field: str, new_field: str, test_path: str) -> ApiHeal:
    """Propose (never silently apply) a test update for an approved rename."""
    diff = (
        f"--- a/{test_path}\n+++ b/{test_path}\n"
        f'-  response["{old_field}"]\n+  response["{new_field}"]\n'
    )
    return ApiHeal("propose_test_update", f"approved rename {old_field}->{new_field}", diff)


def escalate_with_diff(reason: str, diff_text: str) -> ApiHeal:
    return ApiHeal("escalate", reason, diff_text)


def heal_api(api_class: str, **kwargs: object) -> ApiHeal:
    """Dispatch: only the three allowed actions heal; rest escalate."""
    if api_class == "expired_credential":
        return refresh_token()
    if api_class == "stale_data":
        return regenerate_fixtures()
    if api_class == "approved_spec_change":
        old = str(kwargs.get("old_field", ""))
        new = str(kwargs.get("new_field", ""))
        path = str(kwargs.get("test_path", "test_api.py"))
        if old and new:
            return propose_test_update(old, new, path)
        return escalate_with_diff("approved rename lacks field mapping", "")
    return escalate_with_diff(
        f"{api_class} is not auto-healable", str(kwargs.get("schema_diff", ""))
    )
