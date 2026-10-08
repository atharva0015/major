"""Tests for allowed healers and the assertion guard."""

import os

from healing.nonui.assert_guard import guard_diff
from healing.nonui.healers import heal_api


def test_refresh_token_sets_env() -> None:
    os.environ.pop("TEST_TOKEN", None)
    os.environ["API_DRIFT_MODE"] = "expired_token"
    try:
        h = heal_api("expired_credential")
        assert h.action == "refresh_token"
        from demo_app.api_drift import server_token

        assert os.getenv("TEST_TOKEN") == server_token()
    finally:
        os.environ["API_DRIFT_MODE"] = "none"
        os.environ.pop("TEST_TOKEN", None)


def test_only_three_actions_heal() -> None:
    assert heal_api("stale_data").action == "regenerate_fixtures"
    p = heal_api("approved_spec_change", old_field="price", new_field="amount", test_path="t.py")
    assert p.action == "propose_test_update" and "amount" in p.diff
    for blocked in ("contract_change", "unapproved_change"):
        assert heal_api(blocked).action == "escalate"


def test_guard_blocks_removed_assertion() -> None:
    diff = "--- a/t.py\n+++ b/t.py\n-    assert resp['price'] == 9.99\n"
    allowed, why = guard_diff(diff)
    assert not allowed and "removes" in why


def test_guard_blocks_weakened_assertion() -> None:
    diff = (
        "--- a/t.py\n+++ b/t.py\n-    assert resp['price'] == 9.99\n"
        "+    assert resp['price'] is not None\n"
    )
    # Removal dominates: still refused without sign-off.
    assert guard_diff(diff)[0] is False
    assert guard_diff(diff, human_signoff="ada")[0] is True


def test_guard_blocks_threshold_change() -> None:
    diff = "--- a/t.py\n+++ b/t.py\n+    timeout: 5\n"
    assert guard_diff(diff)[0] is False
    assert guard_diff(diff, human_signoff="ada")[0] is True


def test_guard_allows_field_rename_proposal() -> None:
    diff = '--- a/test_api.py\n+++ b/test_api.py\n-  response["price"]\n+  response["amount"]\n'
    assert guard_diff(diff) == (True, "ok: no assertions touched")
