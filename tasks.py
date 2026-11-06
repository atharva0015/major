"""Windows-friendly equivalents of every Makefile target.

Usage: python tasks.py <target>  (targets mirror the Makefile 1:1)
Uses sys.executable so the 3.12 venv is honored on Windows without make.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

TASKS: dict[str, list[list[str]]] = {
    "test": [[sys.executable, "-m", "pytest", "-q"]],
    "lint": [
        [sys.executable, "-m", "ruff", "check", "."],
        [sys.executable, "-m", "ruff", "format", "--check", "."],
        [sys.executable, "-m", "mypy", "healing"],
    ],
    "bench": [
        [sys.executable, "-m", "scripts.bench"],
        [sys.executable, "-m", "scripts.bench_verify"],
    ],
    "bench-verify": [[sys.executable, "-m", "scripts.bench_verify"]],
    "bench-decision": [[sys.executable, "-m", "scripts.bench_decision"]],
    "bench-heldout": [[sys.executable, "-m", "scripts.bench_heldout"]],
    "bench-demo-cases": [[sys.executable, "-m", "scripts.bench_demo_cases"]],
    "bench-e2e-live": [[sys.executable, "-m", "scripts.bench_e2e_live"]],
    "bench-healenium": [[sys.executable, "-m", "scripts.bench_healenium"]],
    "bench-healenium-live": [[sys.executable, "-m", "scripts.bench_healenium_live"]],
    "bench-shadow": [[sys.executable, "-m", "scripts.shadow_report"]],
    "bench-api": [[sys.executable, "-m", "scripts.bench_api"]],
    "bench-golden": [[sys.executable, "-m", "scripts.bench_golden"]],
    "bench-golden-live": [[sys.executable, "-m", "scripts.bench_golden_live"]],
    "bench-vision": [[sys.executable, "-m", "scripts.bench_vision"]],
    "evidence-snapshot": [[sys.executable, "-m", "scripts.evidence_snapshot"]],
    "gates": [[sys.executable, "-m", "scripts.check_gates"]],
    "gates-strict": [[sys.executable, "-m", "scripts.check_gates", "--strict"]],
    "demo": [[sys.executable, "-m", "scripts.demo"]],
    "dashboard": [[sys.executable, "-m", "healing.dashboard.app"]],
    "studio": [[sys.executable, "-m", "healing.codebase.app"]],
    "demo-ui": [[sys.executable, "-m", "demo_app.app"]],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Makefile-equivalent task")
    parser.add_argument("target", choices=sorted(TASKS))
    args = parser.parse_args()
    for cmd in TASKS[args.target]:
        print(f"+ {' '.join(cmd)}", flush=True)
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
