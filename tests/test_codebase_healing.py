"""Tests for the Codebase Auto-Healing and Optimization framework."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from healing.codebase.healer import CodebaseHealer
from healing.codebase.ingest import (
    cleanup_workspace,
    create_temp_workspace,
    create_workspace_zip,
    extract_zip,
)
from healing.codebase.optimizer import CodebaseOptimizer
from healing.codebase.scanner import CodebaseScanner


@pytest.fixture
def sample_broken_codebase(tmp_path: Path) -> Path:
    """Create a temporary codebase with known defects and optimization opportunities."""
    ws = tmp_path / "sample_project"
    ws.mkdir()

    # File 1: Syntax Error
    (ws / "broken_syntax.py").write_text("def faulty(\n    return 42\n", encoding="utf-8")

    # File 2: Runtime Bug (division by zero) + Mutable Default
    (ws / "calc.py").write_text(
        "def compute_ratio(a, b):\n"
        "    if b == 0:\n"
        "        pass\n"
        "    return a / 0\n\n"
        "def append_item(x, items=[]):\n"
        "    items.append(x)\n"
        "    return items\n",
        encoding="utf-8",
    )

    # File 3: Algorithmic Inefficiency (linear lookup in loop)
    (ws / "search.py").write_text(
        "def find_matches(candidates, targets):\n"
        "    matches = []\n"
        "    for c in candidates:\n"
        "        if c in targets:\n"
        "            matches.append(c)\n"
        "    return matches\n",
        encoding="utf-8",
    )

    # File 4: Test file
    tests_dir = ws / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_calc.py").write_text(
        "from calc import append_item\n\n"
        "def test_append():\n"
        "    res = append_item(1, [])\n"
        "    assert res == [1]\n",
        encoding="utf-8",
    )

    return ws


def test_scanner_detects_bugs_and_optimizations(sample_broken_codebase: Path) -> None:
    scanner = CodebaseScanner(sample_broken_codebase)
    result = scanner.scan()

    assert result.total_files >= 3
    assert len(result.bugs) > 0
    # Checks for syntax error detection
    bug_types = [b.bug_type for b in result.bugs]
    assert "syntax_error" in bug_types
    assert "runtime_error" in bug_types

    # Checks for optimization opportunities
    assert len(result.optimizations) > 0
    categories = [o.category for o in result.optimizations]
    assert "inefficient_lookup" in categories


def test_healer_repairs_defects(sample_broken_codebase: Path) -> None:
    scanner = CodebaseScanner(sample_broken_codebase)
    scan_result = scanner.scan()

    healer = CodebaseHealer(sample_broken_codebase)
    healing_result = healer.heal_codebase(scan_result)

    assert len(healing_result.patches) > 0
    # Check that patches have unified diffs
    for p in healing_result.patches:
        assert p.diff != ""
        assert p.file_path in ["calc.py", "broken_syntax.py", "search.py"]


def test_optimizer_applies_safe_transformations(sample_broken_codebase: Path) -> None:
    scanner = CodebaseScanner(sample_broken_codebase)
    scan_result = scanner.scan()

    optimizer = CodebaseOptimizer(sample_broken_codebase)
    opt_result = optimizer.optimize_codebase(scan_result)

    assert opt_result.verified_safe is True
    assert opt_result.overall_speedup >= 1.0


def test_zip_ingest_and_archive(tmp_path: Path) -> None:
    # Build sample in-memory zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("app/main.py", "print('hello world')\n")
        z.writestr("app/utils.py", "def add(a, b): return a + b\n")

    ws = create_temp_workspace(prefix="test_zip_")
    try:
        extracted = extract_zip(buf.getvalue(), ws)
        assert len(extracted) == 2
        assert (ws / "app" / "main.py").exists()

        zip_bytes = create_workspace_zip(ws)
        assert len(zip_bytes) > 0

        # Unpack generated zip and verify
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as check_z:
            names = check_z.namelist()
            assert any("main.py" in n for n in names)
    finally:
        cleanup_workspace(ws)
