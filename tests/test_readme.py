"""README must stay useful: quickstart, demo, evidence, and honest limits."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def test_readme_has_quickstart_demo_evidence_and_limits() -> None:
    text = README.read_text(encoding="utf-8")
    for needle in (
        "## Quickstart",
        "python tasks.py demo",
        "## Current limits",
        "docs/EVIDENCE_INDEX.md",
        "docs/PROJECT_EXPLAINED.md",
        "TODO.md",
        "docs/TOKEN_CART_ANALYSIS.md",
        "NOTICE",
    ):
        assert needle in text, f"README is missing {needle!r}"

    for target in (
        "docs/EVIDENCE_INDEX.md",
        "docs/PROJECT_EXPLAINED.md",
        "TODO.md",
        "docs/TOKEN_CART_ANALYSIS.md",
        "docs/ARCHITECTURE.md",
        "docs/DECISIONS.md",
        "docs/TARGETS.md",
        "docs/HUMAN_SIGNOFF.md",
        "docs/OPERATOR_RUNBOOK.md",
        "NOTICE",
        "THIRD_PARTY_NOTICES.md",
    ):
        assert (ROOT / target).is_file(), f"README links to missing file {target}"
