"""The demo-case bench must cover all 24 pre-registered cases and fail closed."""

from __future__ import annotations

import json

from scripts import bench_demo_cases


def test_bench_covers_every_pre_registered_case() -> None:
    expected = bench_demo_cases.load_expected()
    case_ids = {c.id for c in bench_demo_cases.CASES} | {c.id for c in bench_demo_cases.HARD_CASES}
    assert len(expected) == 24
    assert case_ids == set(expected)


def test_main_writes_24_rows_with_no_false_heals_or_wrong_escalations(
    tmp_path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    md = tmp_path / "demo_cases.md"
    js = tmp_path / "demo_cases.json"
    monkeypatch.setattr(bench_demo_cases, "REPORT_MD", str(md))
    monkeypatch.setattr(bench_demo_cases, "REPORT_JSON", str(js))

    bench_demo_cases.main()

    report = json.loads(js.read_text(encoding="utf-8"))
    rows = report["rows"]
    assert len(rows) == 24
    assert report["pipeline_false_heals"] == 0
    assert report["pipeline_wrong_escalations"] == 0
    assert all(row["pipeline_ok"] is True for row in rows)
    assert md.read_text(encoding="utf-8").count("\n| ") >= 24
