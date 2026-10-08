"""Isolated sandbox replay: ephemeral handle, egress denied, mocked sides.

Follows docs/SPIKE_SANDBOX.md: one egress-restricted shape (demo + WireMock
only). Replays are in-process and deterministic so `make bench` needs no
Docker; infra/sandbox.overlay.yml documents the real staging equivalent.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

SANDBOX_VERSION = "sandbox-0.1.0"
ALLOWED_HOSTS = ("demo", "wiremock", "localhost", "127.0.0.1")


class EgressBlocked(Exception):
    """Raised when replay touches anything outside the allowlist."""


@dataclass(frozen=True)
class SandboxConfig:
    seed: int = 42
    allowed_hosts: tuple[str, ...] = ALLOWED_HOSTS
    egress_denied: bool = True
    reset_data: bool = True
    app_version: str = "demo-0.1.0"
    policy_version: str = "policy-0.1.0"


@dataclass(frozen=True)
class ParityReport:
    match: bool
    drift: tuple[str, ...] = ()


def check_parity(
    sandbox_versions: dict[str, str], staging_versions: dict[str, str]
) -> ParityReport:
    """Compare sandbox vs staging versions/config; report every drift field."""
    drift = tuple(
        k
        for k in set(sandbox_versions) | set(staging_versions)
        if sandbox_versions.get(k) != staging_versions.get(k)
    )
    return ParityReport(match=not drift, drift=drift)


class WireMockStubs:
    """In-process stand-in for third-party HTTP (seeded, resettable)."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.calls: list[str] = []
        self.stubs: dict[str, object] = {
            "wiremock/products": [{"id": 1}, {"id": 2}, {"id": 3}],
        }

    def get(self, url: str) -> object:
        self.calls.append(url)
        return self.stubs.get(url, {"stub": True, "seed": self.seed})

    def reset(self) -> None:
        self.calls = []


class SandboxSession:
    """Ephemeral isolated replay handle (context manager, auto-teardown)."""

    def __init__(self, config: SandboxConfig | None = None) -> None:
        self.config = config or SandboxConfig()
        self.wiremock = WireMockStubs(self.config.seed)
        self._saved_env: dict[str, str] = {}
        self.active = False
        self.version = SANDBOX_VERSION

    def __enter__(self) -> SandboxSession:
        self._saved_env = dict(os.environ)
        os.environ["SANDBOX_ACTIVE"] = "1"
        os.environ["SEED"] = str(self.config.seed)
        self.active = True
        return self

    def __exit__(self, *exc: object) -> None:
        _ = exc
        self.teardown()

    def teardown(self) -> None:
        """Reset seeded data and restore env (automatic)."""
        try:
            from demo_app.app import CART

            if self.config.reset_data:
                CART.clear()
        finally:
            os.environ.clear()
            os.environ.update(self._saved_env)
            self.wiremock.reset()
            self.active = False

    def _guard(self, url: str) -> None:
        if not self.config.egress_denied:
            return
        if not any(h in url for h in self.config.allowed_hosts):
            raise EgressBlocked(f"egress denied for {url!r}; sandbox never touches real systems")

    def http_get(self, url: str) -> object:
        self._guard(url)
        if "wiremock" in url:
            return self.wiremock.get(url)
        return {"page": "demo", "seed": self.config.seed}

    def http_post(self, url: str, payload: object = None) -> object:
        _ = payload
        self._guard(url)
        return {"ok": True, "seed": self.config.seed}

    def run(self, fn: object, *args: object) -> object:
        """Replay a callable inside the sandbox."""
        assert self.active, "session not active"
        assert callable(fn)
        return fn(*args)  # type: ignore[operator]


@dataclass
class AttemptLog:
    strategy: str
    verdict: str = "unverified"
    reason: str = ""
    cost: float = 0.0
    latency_ms: float = 0.0
    _items: list[dict[str, object]] = field(default_factory=list)

    def record(
        self, strategy: str, verdict: str, reason: str, cost: float = 0.0, latency_ms: float = 0.0
    ) -> None:
        self._items.append(
            {
                "strategy": strategy,
                "verdict": verdict,
                "reason": reason,
                "cost": cost,
                "latency_ms": latency_ms,
            }
        )

    def items(self) -> list[dict[str, object]]:
        return list(self._items)
