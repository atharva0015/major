"""The one-command demo must run end-to-end and print both XAI records."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_demo_runs_and_prints_24_cases_and_both_records() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "scripts.demo"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "demo run: SIMULATED" in result.stdout

    case_rows = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("| ") and not line.startswith("| case ")
    ]
    assert len(case_rows) == 24, result.stdout

    assert "--- XAI record: heal (renamed_id) ---" in result.stdout
    assert "--- XAI record: escalation (lookalike_trap) ---" in result.stdout
    assert '"heal_id"' in result.stdout
