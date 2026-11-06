"""Modern Web UI and REST API for Autonomous Codebase Auto-Healing and Optimization.

Allows users to upload any codebase (ZIP or local folder path), inspect detected
defects and bottlenecks, execute verified auto-healing with sandbox replay,
run performance optimization with benchmarking, and download the optimized codebase.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from healing.codebase.healer import CodebaseHealer
from healing.codebase.ingest import (
    cleanup_workspace,
    create_temp_workspace,
    create_workspace_zip,
    extract_zip,
)
from healing.codebase.llm_client import LocalLLMClient
from healing.codebase.models import HealingResult, OptimizationResult, ScanResult
from healing.codebase.optimizer import CodebaseOptimizer
from healing.codebase.scanner import CodebaseScanner

app = FastAPI(
    title="Codebase Auto-Healing & Optimization Studio",
    description="Autonomous bug healing and performance optimization for any codebase.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active session workspaces in memory
_ACTIVE_WORKSPACES: dict[str, Path] = {}
_ACTIVE_SCANS: dict[str, ScanResult] = {}
_ACTIVE_HEALS: dict[str, HealingResult] = {}
_ACTIVE_OPTS: dict[str, OptimizationResult] = {}

llm_client = LocalLLMClient()


class FolderPathRequest(BaseModel):
    folder_path: str


@app.get("/api/status")
def get_status() -> dict[str, Any]:
    """Return local LLM status and active session info."""
    return {
        "llm_status": llm_client.get_status_info(),
        "active_workspaces": len(_ACTIVE_WORKSPACES),
    }


@app.post("/api/upload")
def upload_codebase(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload a zipped codebase, unpack into isolated sandbox, and run initial scan."""
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported for upload")

    contents = file.file.read()
    workspace_id = f"ws-{uuid.uuid4().hex[:8]}"
    ws_dir = create_temp_workspace(prefix=f"{workspace_id}_")

    try:
        extract_zip(contents, ws_dir)
        scanner = CodebaseScanner(ws_dir)
        scan_result = scanner.scan()

        _ACTIVE_WORKSPACES[workspace_id] = ws_dir
        _ACTIVE_SCANS[workspace_id] = scan_result

        return {
            "workspace_id": workspace_id,
            "project_name": file.filename.replace(".zip", ""),
            "scan_result": scan_result.model_dump(),
        }
    except Exception as exc:
        cleanup_workspace(ws_dir)
        raise HTTPException(status_code=500, detail=f"Failed to process archive: {exc}") from exc


@app.post("/api/load-sample")
def load_sample_project() -> dict[str, Any]:
    """Create a sample testbed project with realistic bugs and optimization bottlenecks."""
    workspace_id = f"ws-{uuid.uuid4().hex[:8]}"
    ws_dir = create_temp_workspace(prefix=f"{workspace_id}_sample_")

    # Sample File 1: Math Calculator with zero division & mutable default
    (ws_dir / "calculator.py").write_text(
        '"""Financial ratio calculator."""\n\n'
        "def compute_quick_ratio(assets, liabilities):\n"
        "    # Bug: Division by zero when liabilities is 0\n"
        "    if liabilities == 0:\n"
        "        pass\n"
        "    return assets / liabilities\n\n"
        "def record_transaction(tx_id, log=[]):\n"
        "    # Bug: Mutable default argument retains state\n"
        "    log.append(tx_id)\n"
        "    return log\n",
        encoding="utf-8",
    )

    # Sample File 2: Inefficient search & string concatenation
    (ws_dir / "analytics.py").write_text(
        '"""Analytics reporting engine."""\n\n'
        "def find_priority_customers(all_customers, flagged_ids):\n"
        "    # Bottleneck: Linear search inside loop: O(N*M)\n"
        "    priorities = []\n"
        "    for cust in all_customers:\n"
        "        if cust in flagged_ids:\n"
        "            priorities.append(cust)\n"
        "    return priorities\n\n"
        "def format_audit_log(events):\n"
        "    # Bottleneck: String concatenation in loop\n"
        '    header = "AUDIT LOG:\\n"\n'
        '    log_str = ""\n'
        "    for ev in events:\n"
        '        log_str += f"- {ev}\\n"\n'
        "    return header + log_str\n\n"
        "def recursive_fib(n):\n"
        "    # Bottleneck: Exponential tree recursion without memoization\n"
        "    if n <= 1:\n"
        "        return n\n"
        "    return recursive_fib(n - 1) + recursive_fib(n - 2)\n",
        encoding="utf-8",
    )

    # Sample File 3: Unit tests
    tests_dir = ws_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_calculator.py").write_text(
        "from calculator import record_transaction\n\n"
        "def test_record_isolated():\n"
        '    res = record_transaction("tx-1", [])\n'
        '    assert res == ["tx-1"]\n',
        encoding="utf-8",
    )

    scanner = CodebaseScanner(ws_dir)
    scan_result = scanner.scan()

    _ACTIVE_WORKSPACES[workspace_id] = ws_dir
    _ACTIVE_SCANS[workspace_id] = scan_result

    return {
        "workspace_id": workspace_id,
        "project_name": "Sample Financial & Analytics Codebase",
        "scan_result": scan_result.model_dump(),
    }


@app.post("/api/load-demo")
def load_demo_project() -> dict[str, Any]:
    """Load the demo_app codebase (pre-seeded with bugs + bottlenecks) for live presentation."""
    demo_dir = Path(__file__).parent.parent.parent / "demo_app"
    if not demo_dir.exists():
        raise HTTPException(status_code=404, detail="demo_app folder not found in repository root")

    workspace_id = f"ws-{uuid.uuid4().hex[:8]}"
    ws_dir = create_temp_workspace(prefix=f"{workspace_id}_demo_")

    # Copy demo_app contents into isolated workspace
    import shutil

    for item in demo_dir.iterdir():
        dest = ws_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    scanner = CodebaseScanner(ws_dir)
    scan_result = scanner.scan()

    _ACTIVE_WORKSPACES[workspace_id] = ws_dir
    _ACTIVE_SCANS[workspace_id] = scan_result

    return {
        "workspace_id": workspace_id,
        "project_name": "Demo App — Order Processing & Analytics",
        "scan_result": scan_result.model_dump(),
    }


@app.post("/api/heal/{workspace_id}")
def heal_codebase_endpoint(workspace_id: str) -> dict[str, Any]:
    """Execute autonomous bug healing with sandbox and Critic verification."""
    ws_dir = _ACTIVE_WORKSPACES.get(workspace_id)
    scan_result = _ACTIVE_SCANS.get(workspace_id)

    if not ws_dir or not scan_result:
        raise HTTPException(status_code=404, detail="Workspace not found")

    healer = CodebaseHealer(ws_dir, llm=llm_client)
    healing_result = healer.heal_codebase(scan_result)
    _ACTIVE_HEALS[workspace_id] = healing_result

    # Rescan after healing to update metrics
    scanner = CodebaseScanner(ws_dir)
    updated_scan = scanner.scan()
    _ACTIVE_SCANS[workspace_id] = updated_scan

    return {
        "healing_result": healing_result.model_dump(),
        "updated_scan": updated_scan.model_dump(),
    }


@app.post("/api/optimize/{workspace_id}")
def optimize_codebase_endpoint(workspace_id: str) -> dict[str, Any]:
    """Execute code performance and complexity optimization with regression guard."""
    ws_dir = _ACTIVE_WORKSPACES.get(workspace_id)
    scan_result = _ACTIVE_SCANS.get(workspace_id)

    if not ws_dir or not scan_result:
        raise HTTPException(status_code=404, detail="Workspace not found")

    optimizer = CodebaseOptimizer(ws_dir, llm=llm_client)
    opt_result = optimizer.optimize_codebase(scan_result)
    _ACTIVE_OPTS[workspace_id] = opt_result

    # Rescan after optimization to update metrics
    scanner = CodebaseScanner(ws_dir)
    updated_scan = scanner.scan()
    _ACTIVE_SCANS[workspace_id] = updated_scan

    return {
        "optimization_result": opt_result.model_dump(),
        "updated_scan": updated_scan.model_dump(),
    }


@app.get("/api/download/{workspace_id}")
def download_codebase(workspace_id: str) -> Response:
    """Download the modified, healed, and optimized codebase as a ZIP file."""
    ws_dir = _ACTIVE_WORKSPACES.get(workspace_id)
    if not ws_dir or not ws_dir.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")

    zip_bytes = create_workspace_zip(ws_dir)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={workspace_id}_optimized.zip"},
    )


STUDIO_HTML_PATH = Path(__file__).parent / "studio.html"


@app.get("/", response_class=HTMLResponse)
def serve_studio_ui() -> HTMLResponse:
    """Render the Modern Single-Page Web UI."""
    content = STUDIO_HTML_PATH.read_text(encoding="utf-8")
    return HTMLResponse(content)


def main() -> None:
    import uvicorn

    host = os.getenv("STUDIO_HOST", "127.0.0.1")
    port = int(os.getenv("STUDIO_PORT", "8081"))
    print(f"Starting Codebase Auto-Healing & Optimality Studio on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
