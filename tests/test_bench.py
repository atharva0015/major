"""Tests for bench wiring and maintenance numbers."""

import os

from benchmark.cases import CASES
from scripts.baseline_report import (
    estimated_manual_repairs,
    failures_by_class,
    locator_drift_share,
)


def test_failures_by_class_covers_adversarial() -> None:
    by_class = failures_by_class()
    assert by_class["locator_drift"] == 15  # 5 drifts x 3 pages
    assert by_class["genuine_regression"] == 6  # 2 drifts x 3 pages
    assert sum(by_class.values()) == len(CASES) == 24


def test_locator_share_and_repairs() -> None:
    assert locator_drift_share() == 15 / 24
    assert estimated_manual_repairs() == 15


def test_bench_writes_baseline_md(tmp_path: object) -> None:
    from scripts import bench

    md = os.path.join(str(tmp_path), "baseline.md")
    orig = bench.REPORT_MD
    bench.REPORT_MD = md  # type: ignore[assignment]
    orig_json = bench.REPORT_JSON
    bench.REPORT_JSON = os.path.join(str(tmp_path), "baseline.json")
    try:
        bench.main()
        assert os.path.exists(md)
        with open(md, encoding="utf-8") as f:
            text = f.read()
        assert "Baseline report" in text
        assert "locator drift share" in text
    finally:
        bench.REPORT_MD = orig  # type: ignore[assignment]
        bench.REPORT_JSON = orig_json
