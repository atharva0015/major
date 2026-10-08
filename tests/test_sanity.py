"""Sanity tests: package imports and layout exist."""

import importlib


def test_healing_imports() -> None:
    mod = importlib.import_module("healing")
    assert mod.__version__ == "0.1.0"


def test_subpackages_import() -> None:
    subs = [
        "adapters",
        "classifier",
        "matching",
        "sandbox",
        "critic",
        "policy",
        "xai",
        "alerts",
        "gitops",
        "nonui",
        "quality",
        "security",
    ]
    for name in subs:
        assert importlib.import_module(f"healing.{name}") is not None
