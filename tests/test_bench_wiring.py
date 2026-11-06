"""Every bench script must be reachable from Makefile and tasks.py."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import tasks

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def target_for(stem: str) -> str:
    if stem == "bench":
        return "bench"
    return "bench-" + stem.removeprefix("bench_").replace("_", "-")


def test_every_bench_script_is_wired() -> None:
    bench_scripts = sorted(p.stem for p in SCRIPTS.glob("bench*.py") if p.name != "__init__.py")
    assert bench_scripts, "no bench scripts found"

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for stem in bench_scripts:
        target = target_for(stem)
        assert re.search(rf"^{re.escape(target)}:", makefile, re.MULTILINE), (
            f"{stem} has no Makefile target {target}"
        )
        assert f"scripts.{stem}" in makefile, f"{stem} is not invoked by the Makefile"
        assert target in tasks.TASKS, f"{stem} has no tasks.py target {target}"
        command = " ".join(tasks.TASKS[target][0])
        assert f"scripts.{stem}" in command, f"{stem} is not invoked by tasks.py"


def test_tasks_mirror_makefile_targets() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in tasks.TASKS:
        assert re.search(rf"^{re.escape(target)}:", makefile, re.MULTILINE), (
            f"tasks.py target {target} is missing from the Makefile"
        )


def test_tasks_use_the_current_interpreter() -> None:
    for target, commands in tasks.TASKS.items():
        for command in commands:
            assert command[0] == sys.executable, (
                f"{target} would run {command[0]!r} from PATH instead of the active venv"
            )
