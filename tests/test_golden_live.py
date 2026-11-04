"""Tests for the live golden-report adapter (no Docker, no live run)."""

from __future__ import annotations

import json

import pytest

from scripts.bench_golden_live import build_report


def live_data() -> dict[str, object]:
    return {
        "live": True,
        "accuracy": 1.0,
        "false_heal_rate": 0.0,
        "escaped": 0,
        "rows": [{"case_id": "a", "correct": True}, {"case_id": "b", "correct": True}],
    }


def test_build_report_maps_metrics() -> None:
    report = build_report(live_data())
    metrics = report["metrics"]
    assert isinstance(metrics, dict)
    assert metrics["heal_accuracy"] == 1.0
    assert metrics["false_heal_rate"] == 0.0
    assert metrics["cases"] == 2
    assert metrics["escaped"] == 0
    assert report["provenance"] == "live"


def test_build_report_rejects_simulated_source() -> None:
    data = live_data()
    data["live"] = False
    with pytest.raises(ValueError, match="not a live report"):
        build_report(data)


def test_build_report_rejects_empty_or_bad_values() -> None:
    data = live_data()
    data["rows"] = []
    with pytest.raises(ValueError, match="no rows"):
        build_report(data)

    data = live_data()
    data["accuracy"] = 1.5
    with pytest.raises(ValueError, match="accuracy out of range"):
        build_report(data)


def test_written_report_is_gate_shaped(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    source = tmp_path / "e2e_live.json"
    out = tmp_path / "golden_live.json"
    source.write_text(json.dumps(live_data()), encoding="utf-8")

    from scripts import bench_golden_live as mod

    monkeypatch.setattr(mod, "SOURCE", str(source))
    monkeypatch.setattr(mod, "OUT", str(out))
    mod.main()

    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["metrics"]["heal_accuracy"] == 1.0
    assert written["metrics"]["cases"] == 2
