"""Tests for bench-healenium wiring and adversarial reporting."""

import os

from benchmark.harness import run_all
from benchmark.healenium_healer import HealeniumSimHealer
from healing.quality.metrics import compute_metrics


def test_sim_heals_drift_escalates_removed() -> None:
    from benchmark.cases import BenchmarkCase

    h = HealeniumSimHealer()
    drift = BenchmarkCase(
        "renamed_ids:/login",
        "renamed_ids",
        "/login",
        ' id="x"',
        "login-submit",
        "locator_drift",
        True,
    )
    assert h.choose_for_case(drift, ["login-submit", "other"]) == "login-submit"
    gone = BenchmarkCase(
        "removed_element:/login",
        "removed_element",
        "/login",
        ' id="x"',
        None,
        "genuine_regression",
        False,
    )
    assert h.choose_for_case(gone, ["other"]) is None
    assert h.choose(["a"]) is None  # no context -> fail closed


def test_healenium_metrics_and_adversarial_slice() -> None:
    results = run_all(HealeniumSimHealer(), seed=42)
    assert len(results) == 24
    m = compute_metrics(results)
    assert m.heal_accuracy == 1.0  # all 15 locator drifts healed
    assert m.false_heal_rate > 0.0  # swapped + duplicate false-heal
    adv = [r for r in results if not r.should_heal]
    assert len(adv) == 9
    assert any(r.healed for r in adv)


def test_bench_healenium_writes_report(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from scripts import bench_healenium as bh

    md = os.path.join(str(tmp_path), "healenium.md")
    js = os.path.join(str(tmp_path), "healenium.json")
    monkeypatch.setattr(bh, "REPORT_MD", md)
    monkeypatch.setattr(bh, "REPORT_JSON", js)
    monkeypatch.setattr(bh, "BASELINE_JSON", os.path.join(str(tmp_path), "missing.json"))
    bh.main()
    assert os.path.exists(md)
    with open(md, encoding="utf-8") as f:
        text = f.read()
    assert "Adversarial cases" in text
    assert "Per-case results" in text
