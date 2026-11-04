"""Every file listed in docs/FROZEN_HASHES.md must match its recorded hash.

Fail closed: a missing manifest, a missing entry for a required frozen file, a
listed file that no longer exists, or a hash mismatch all fail the test. Run
`git hash-object` rather than hashing bytes in Python so the test matches the
manifest's recorded algorithm exactly.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "FROZEN_HASHES.md"

# The table rows we care about: | `path` | `40-hex git blob id` |
ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{40})`\s*\|", re.MULTILINE)

REQUIRED = {
    "healing/classifier/rules.py",
    "healing/critic/checks.py",
    "healing/policy/policy.yaml",
    "benchmark/cases.py",
    "benchmark/api/cases.py",
    "benchmark/heldout/ui_cases.py",
    "benchmark/heldout/api_cases.py",
}


def listed_hashes() -> dict[str, str]:
    text = MANIFEST.read_text(encoding="utf-8")
    found: dict[str, str] = {}
    for path, digest in ROW.findall(text):
        if path in found and found[path] != digest:
            raise AssertionError(f"conflicting hashes recorded for {path}")
        found[path] = digest
    assert found, "no frozen hashes parsed from docs/FROZEN_HASHES.md"
    return found


def git_hash(path: str) -> str:
    result = subprocess.run(
        ["git", "hash-object", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def test_manifest_lists_every_required_frozen_file() -> None:
    found = listed_hashes()
    missing = sorted(REQUIRED - found.keys())
    assert not missing, f"frozen files missing from manifest: {missing}"


def test_listed_hashes_match_working_tree() -> None:
    found = listed_hashes()
    mismatches: list[str] = []
    for path, expected in sorted(found.items()):
        full = ROOT / path
        assert full.is_file(), f"frozen file listed but missing on disk: {path}"
        actual = git_hash(path)
        if actual != expected:
            mismatches.append(f"{path}: manifest={expected} actual={actual}")
    assert not mismatches, "frozen hash mismatches:\n" + "\n".join(mismatches)
