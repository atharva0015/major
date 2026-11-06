"""SBOM license normalization and allowlist enforcement."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import sbom


def test_normalize_license_handles_common_forms() -> None:
    cases = {
        "MIT": "MIT",
        "MIT License": "MIT",
        "MIT-0": "MIT-0",
        "Apache 2.0": "Apache-2.0",
        "Apache-2.0 OR BSD-3-Clause": "Apache-2.0 OR BSD-3-Clause",
        "Apache-2.0 AND BSD-2-Clause": "Apache-2.0 AND BSD-2-Clause",
        "BSD License": "BSD-3-Clause",
        "MPL-2.0": "MPL-2.0",
        "GNU Library or Lesser General Public License (LGPL)": "LGPL-3.0-only",
        "TBD": "UNKNOWN",
        "": "UNKNOWN",
    }
    for raw, expected in cases.items():
        assert sbom.normalize_license(raw) == expected

    long_text = (
        "All contributions are MIT licensed. Some files are PSF licensed. "
        "Other files are Apache licensed. " + "x" * 300
    )
    normalized = sbom.normalize_license(long_text)
    assert normalized == "Apache-2.0 AND MIT AND PSF-2.0"
    assert sbom.license_allowed(normalized)


def test_license_allowed_uses_or_and_rules() -> None:
    assert sbom.license_allowed("MIT")
    assert sbom.license_allowed("MPL-2.0")
    assert sbom.license_allowed("LGPL-3.0-only")
    assert not sbom.license_allowed("GPL-3.0")
    assert not sbom.license_allowed("UNKNOWN")
    assert sbom.license_allowed("MIT OR GPL-3.0")
    assert not sbom.license_allowed("MIT AND GPL-3.0")


def test_check_components_reports_only_disallowed() -> None:
    components = [
        {"name": "a", "version": "1", "license": "MIT"},
        {"name": "b", "version": "1", "license": "MPL-2.0"},
        {"name": "c", "version": "1", "license": "GPL-3.0"},
        {"name": "d", "version": "1", "license": "UNKNOWN"},
    ]
    violations = sbom.check_components(components)
    assert [component["name"] for component in violations] == ["c", "d"]


def test_main_check_passes_and_writes_sbom(tmp_path, monkeypatch, capsys) -> None:
    out = tmp_path / "sbom.json"
    monkeypatch.setattr(sbom, "OUT", str(out))
    monkeypatch.setattr(
        sbom,
        "build_sbom",
        lambda: {
            "sbom_format": "test",
            "components": [{"name": "a", "version": "1", "license": "MIT"}],
        },
    )

    sbom.main(["--check"])
    text = capsys.readouterr().out
    assert "result: PASS" in text
    assert json.loads(out.read_text(encoding="utf-8"))["sbom_format"] == "test"


def test_main_check_fails_closed(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(sbom, "OUT", str(tmp_path / "sbom.json"))
    monkeypatch.setattr(
        sbom,
        "build_sbom",
        lambda: {
            "sbom_format": "test",
            "components": [{"name": "bad", "version": "1", "license": "GPL-3.0"}],
        },
    )

    with pytest.raises(SystemExit) as exc:
        sbom.main(["--check"])
    assert exc.value.code == 1
    text = capsys.readouterr().out
    assert "DISALLOWED bad 1: GPL-3.0" in text
    assert "result: FAIL" in text


def test_project_metadata_is_mit() -> None:
    root = Path(__file__).resolve().parents[1]
    license_text = (root / "LICENSE").read_text(encoding="utf-8")
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    decision = (root / "docs" / "LICENSE_DECISION.md").read_text(encoding="utf-8")
    assert license_text.startswith("MIT License")
    assert 'license = { text = "MIT" }' in pyproject
    assert "MIT" in decision
