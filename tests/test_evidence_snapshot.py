"""The evidence snapshot must exercise every deterministic path and write JSON."""

from __future__ import annotations

import json

import pytest

from scripts import evidence_snapshot as snap


@pytest.fixture(scope="module")
def snapshot() -> dict[str, object]:
    return snap.build_snapshot()


def test_masking_and_narrative(snapshot: dict[str, object]) -> None:
    masking = snapshot["masking"]
    assert isinstance(masking, dict)
    assert all(masking["markers"].values())
    assert "@" not in str(masking["masked_text"])

    narrative = snapshot["narrative"]
    assert isinstance(narrative, dict)
    assert narrative["consistency"]["ok"] is True


def test_calibration_and_autonomy(snapshot: dict[str, object]) -> None:
    calibration = snapshot["calibration"]
    assert isinstance(calibration, dict)
    assert calibration["good_pairs_ece"] <= 0.15
    assert calibration["bad_alarm"][0] is True

    autonomy = snapshot["autonomy"]
    assert isinstance(autonomy, dict)
    assert autonomy["downgraded"] is True
    assert autonomy["effective_level"] == "L2"


def test_guard_metrics_and_gitops(snapshot: dict[str, object]) -> None:
    guard = {row["case"]: row["allowed"] for row in snapshot["assertion_guard"]}
    assert guard == {
        "removed_assertion": False,
        "weakened_assertion": False,
        "threshold_change": False,
        "safe_strengthening": True,
    }

    metrics = snapshot["metrics"]
    assert isinstance(metrics, dict)
    assert "heal_success_total" in metrics["prometheus_text"]

    gitops = snapshot["gitops"]
    assert isinstance(gitops, dict)
    assert gitops["pr_body_complete"] is True
    assert gitops["new_source_has_locator"] is True
    assert gitops["watch_now"] is True
    assert gitops["watch_old"] is False
    assert gitops["revert_record"]["revert_pr"] == 2
    assert gitops["alerts"]


def test_dedupe_and_survival(snapshot: dict[str, object]) -> None:
    dedupe = snapshot["dedupe"]
    assert isinstance(dedupe, dict)
    assert len(dedupe["plans"]) == 2

    survival = snapshot["survival"]
    assert isinstance(survival, dict)
    assert survival["30d"]["status"] == "insufficient_data"


def test_main_writes_json(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    out = tmp_path / "quality_snapshot.json"
    monkeypatch.setattr(snap, "OUT", str(out))
    snap.main()
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["label"] == "SIMULATED/IN-PROCESS"
    assert "gitops" in written


def test_local_repo_refuses_paths_outside_temp(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    fake_temp = tmp_path / "fake-temp"
    fake_temp.mkdir()
    monkeypatch.setattr(snap.tempfile, "gettempdir", lambda: str(fake_temp))
    snap._assert_under_temp(str(fake_temp / "r.git"))
    with pytest.raises(RuntimeError, match="outside temp"):
        snap._local_repo(str(tmp_path / "elsewhere"))
