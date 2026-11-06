"""Dashboard tests: read-only routes, latest data, masking, and fail-closed display."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from healing.dashboard import app as dashboard
from healing.xai.records import make_record

GATES = [
    {
        "metric": "heal_accuracy",
        "op": ">=",
        "target": 0.95,
        "provenance": "live",
        "status": "PASS",
        "actual": 1.0,
        "message": "PASS heal_accuracy [live]: 1.0 >= 0.95",
        "source": "benchmark/reports/golden_live.json",
    },
    {
        "metric": "latency_per_heal_ms",
        "op": "<=",
        "target": 100.0,
        "provenance": "live",
        "status": "FAIL",
        "actual": 1122.0,
        "message": "FAIL latency_per_heal_ms [live]: 1122.0 <= 100.0",
        "source": "benchmark/reports/healenium_live.json",
    },
    {
        "metric": "heal_survival_rate",
        "op": "TBD",
        "target": None,
        "provenance": "history",
        "status": "UNVERIFIED",
        "actual": None,
        "message": "UNVERIFIED heal_survival_rate: insufficient_data",
        "source": "healing/quality/survival.py",
    },
]


def _record(heal_id: str, test: str, selected: str | None = None, step: str = "s1"):  # type: ignore[no-untyped-def]
    return make_record(
        heal_id=heal_id,
        test=test,
        step=step,
        classification="locator_drift" if selected else "genuine_regression",
        selected=selected,
        escalation_reason=None if selected else "blocked_class:genuine_regression",
        critic_checks={"verdict": "pass" if selected else "unverified"},
    )


def _write_records(path, records) -> None:  # type: ignore[no-untyped-def]
    path.write_text(
        "\n".join(record.model_dump_json() for record in records) + "\n",
        encoding="utf-8",
    )


def _write_metrics(path) -> None:  # type: ignore[no-untyped-def]
    text = "\n".join(
        [
            'heal_success_total{attempt="1",result="success"} 2.0',
            'heal_success_total{attempt="1",result="fail"} 1.0',
            'heal_escalations_total{classification="locator_drift"} 3.0',
            'heal_cost_total{attempt="1"} 1.5',
            'heal_latency_seconds_count{attempt="1"} 4.0',
            'heal_latency_seconds_sum{attempt="1"} 0.2',
            "alert_ack_seconds_count 2.0",
            "alert_ack_seconds_sum 6.0",
        ]
    )
    path.write_text(
        json.dumps(
            {
                "label": "SIMULATED/IN-PROCESS",
                "metrics": {"prometheus_text": text},
            }
        ),
        encoding="utf-8",
    )


@pytest.fixture
def client(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    records = tmp_path / "records.jsonl"
    _write_records(
        records, [_record("heal-old", "login"), _record("heal-new", "cart", "add-cart-1")]
    )
    metrics = tmp_path / "quality_snapshot.json"
    _write_metrics(metrics)
    monkeypatch.setenv("RECORDS_PATH", str(records))
    monkeypatch.setenv("DASHBOARD_METRICS_PATH", str(metrics))
    monkeypatch.setattr(dashboard, "_gate_rows", lambda: GATES)
    return TestClient(dashboard.app)


def test_load_records_reads_latest_and_skips_bad_lines(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "records.jsonl"
    _write_records(path, [_record("h1", "a"), _record("h2", "b", "x")])
    with open(path, "a", encoding="utf-8") as f:
        f.write("{not json}\n")

    result = dashboard.load_records(str(path), limit=2)
    assert result["available"] is True
    assert result["seen"] == 3
    assert result["invalid"] == 1
    assert [row["heal_id"] for row in result["records"]] == ["h2"]


def test_load_metrics_totals_saved_snapshot(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "quality_snapshot.json"
    _write_metrics(path)

    result = dashboard.load_metrics(str(path))
    assert result["available"] is True
    assert result["totals"]["heal_success"] == 2.0
    assert result["totals"]["heal_fail"] == 1.0
    assert result["totals"]["escalations"] == 3.0
    assert result["totals"]["cost"] == 1.5
    assert result["totals"]["latency_count"] == 4.0
    assert result["totals"]["avg_latency_ms"] == 50.0
    assert result["totals"]["avg_ack_s"] == 3.0


def test_index_renders_gates_records_and_metrics(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert "READ-ONLY" in body
    assert "heal_accuracy" in body
    assert "latency_per_heal_ms" in body
    assert "heal-new" in body
    assert "add-cart-1" in body
    assert "Successful heals" in body
    assert "50.00 ms" in body
    assert response.headers["x-content-type-options"] == "nosniff"


def test_api_summary_is_json(client) -> None:  # type: ignore[no-untyped-def]
    data = client.get("/api/summary").json()
    assert data["read_only"] is True
    assert data["gate_counts"] == {"pass": 1, "fail": 1, "unverified": 1}
    assert data["record_counts"] == {"heals": 1, "escalations": 1, "hash_mismatch": 0}
    assert data["metrics"]["totals"]["heal_success"] == 2.0
    assert data["records"]["records"][0]["heal_id"] == "heal-new"


def test_index_masks_and_escapes_record_text(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    records = tmp_path / "records.jsonl"
    _write_records(
        records,
        [
            _record(
                "heal-xss",
                "<script>alert(1)</script> ada@example.com",
                step="<img src=x onerror=alert(1)>",
            )
        ],
    )
    monkeypatch.setenv("RECORDS_PATH", str(records))
    monkeypatch.setenv("DASHBOARD_METRICS_PATH", str(tmp_path / "missing.json"))
    monkeypatch.setattr(dashboard, "_gate_rows", lambda: GATES)

    body = TestClient(dashboard.app).get("/").text
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in body
    assert "&lt;img src=x onerror=alert(1)&gt;" in body
    assert "[email]" in body


def test_missing_data_is_shown_not_crashed(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("RECORDS_PATH", str(tmp_path / "missing.jsonl"))
    monkeypatch.setenv("DASHBOARD_METRICS_PATH", str(tmp_path / "missing.json"))
    monkeypatch.setattr(dashboard, "_gate_rows", lambda: [])

    response = TestClient(dashboard.app).get("/")
    assert response.status_code == 200
    assert "Records file not found" in response.text
    assert "Metrics snapshot unavailable" in response.text


def test_dashboard_is_get_only() -> None:
    methods = set()
    for route in dashboard.app.routes:
        methods.update(getattr(route, "methods", set()) or set())
    assert methods <= {"GET", "HEAD"}
    assert dashboard.app.openapi_url is None


def test_healthz(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "read_only": True}
