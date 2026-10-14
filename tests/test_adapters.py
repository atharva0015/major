"""Tests for the adapters/ package contract.

The package is currently a placeholder: UI/API runner interfaces live
here once implemented. These tests pin the contract (importable, explicit
exports, documented intent) so future logic lands with tests already green.
"""

import healing.adapters as adapters


def test_package_imports() -> None:
    assert adapters.__name__ == "healing.adapters"


def test_exports_are_explicit() -> None:
    assert isinstance(adapters.__all__, list)


def test_docstring_states_intent() -> None:
    doc = adapters.__doc__ or ""
    assert "UI" in doc and "API" in doc
