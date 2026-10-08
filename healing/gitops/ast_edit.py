"""AST locator edits: LibCST rewrites only the failing locator (minimal diff)."""

from __future__ import annotations

import difflib
import subprocess
from typing import Any

STABLE_ORDER = ("test-id", "role", "text", "structural")


def _load_cst() -> Any:  # dynamic import keeps libcst out of cold paths
    try:
        import libcst as cst  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("libcst is required for AST edits") from exc
    return cst


def stable_rank(new_value: str) -> int:
    """Prefer stable locators: test id / role first, structural last."""
    low = new_value.lower()
    if "test-id" in low or "testid" in low or "data-testid" in low:
        return 0
    if "role" in low:
        return 1
    if low.startswith(("buy", "sign", "checkout", "log")) or "text=" in low:
        return 2
    return 3


def edit_locator(source: str, old: str, new: str) -> tuple[str, str]:
    """Replace exactly one failing locator; refuse anything else.

    Returns (new_source, unified_diff). Raises RefusedError-equivalent
    ValueError unless precisely one locator string changes.
    """
    cst = _load_cst()
    if source.count(f'"{old}"') + source.count(f"'{old}'") != 1:
        raise ValueError(f"expected exactly one occurrence of locator {old!r}")

    class _Rewriter(cst.CSTTransformer):  # type: ignore[name-defined]
        def __init__(self) -> None:
            self.changes = 0

        def leave_SimpleString(self, old_node: object, updated_node: object) -> object:
            node = updated_node
            val = node.value[1:-1]  # type: ignore[attr-defined]
            if val == old:
                self.changes += 1
                q = node.value[0]  # type: ignore[attr-defined]
                return node.with_changes(value=f"{q}{new}{q}")  # type: ignore[attr-defined]
            return node

    module = cst.parse_module(source)
    rw = _Rewriter()
    updated = module.visit(rw)
    if rw.changes != 1:
        raise ValueError(f"refusing edit: {rw.changes} nodes changed, want 1")
    new_source: str = updated.code
    diff = "".join(
        difflib.unified_diff(
            source.splitlines(True), new_source.splitlines(True), "before", "after"
        )
    )
    return new_source, diff


def format_and_lint(path: str) -> None:
    """Run the formatter and linter on the edited file; raise on failure."""
    subprocess.run(["ruff", "format", path], check=True)
    subprocess.run(["ruff", "check", path], check=True)
