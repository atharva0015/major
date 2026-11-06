"""Tests for Codebase Auto-Healing & Optimization Studio REST API and Web App."""

from __future__ import annotations

import io
import zipfile

from fastapi import UploadFile

from healing.codebase.app import (
    download_codebase,
    get_status,
    heal_codebase_endpoint,
    load_demo_project,
    load_sample_project,
    optimize_codebase_endpoint,
    serve_studio_ui,
    upload_codebase,
)


def test_serve_studio_ui() -> None:
    res = serve_studio_ui()
    assert res.status_code == 200
    html = res.body.decode("utf-8")
    assert "Codebase Healing & Optimality Studio" in html
    assert "Autonomous Bug Healing" in html
    assert "Code Optimality Engine" in html


def test_get_status() -> None:
    data = get_status()
    assert "llm_status" in data
    assert "provider" in data["llm_status"]


def test_load_sample_project() -> None:
    data = load_sample_project()
    assert "workspace_id" in data
    assert "scan_result" in data
    scan = data["scan_result"]
    assert scan["total_files"] >= 2
    assert len(scan["bugs"]) > 0
    assert len(scan["optimizations"]) > 0


def test_load_demo_project() -> None:
    data = load_demo_project()
    assert "workspace_id" in data
    assert "scan_result" in data
    scan = data["scan_result"]
    assert scan["total_files"] >= 2
    assert len(scan["bugs"]) == 3
    assert len(scan["optimizations"]) >= 3


def test_heal_endpoint_workflow() -> None:
    # 1. Load sample project
    load_res = load_sample_project()
    ws_id = load_res["workspace_id"]

    # 2. Trigger heal
    data = heal_codebase_endpoint(ws_id)
    assert "healing_result" in data
    assert len(data["healing_result"]["patches"]) > 0
    # Check that diffs exist
    for p in data["healing_result"]["patches"]:
        assert "diff" in p
        assert p["applied"] is True or p["verification_status"] != "verified"


def test_optimize_endpoint_workflow() -> None:
    # 1. Load sample project
    load_res = load_sample_project()
    ws_id = load_res["workspace_id"]

    # 2. Trigger optimize
    data = optimize_codebase_endpoint(ws_id)
    assert "optimization_result" in data
    opt = data["optimization_result"]
    assert opt["verified_safe"] is True
    assert opt["overall_speedup"] >= 1.0


def test_download_endpoint() -> None:
    load_res = load_sample_project()
    ws_id = load_res["workspace_id"]

    dl_res = download_codebase(ws_id)
    assert dl_res.status_code == 200
    assert dl_res.media_type == "application/zip"

    # Verify that zip content is readable
    with zipfile.ZipFile(io.BytesIO(dl_res.body)) as z:
        names = z.namelist()
        assert any("calculator.py" in n for n in names)


def test_upload_zip_codebase() -> None:
    # Build sample zip in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("app.py", "def div(a, b): return a / 0\n")
    buf.seek(0)

    upload_file = UploadFile(filename="test_codebase.zip", file=buf)
    data = upload_codebase(upload_file)
    assert "workspace_id" in data
    assert len(data["scan_result"]["bugs"]) > 0
