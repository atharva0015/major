"""Gate checker: re-judge every gate against docs/TARGETS.md. Exit 1 on any FAIL.

Reads report JSON only (plus the alert unit tests as a subgate). Never
imports healing/ or benchmark/ code, so a broken pipeline cannot mask a
red gate. Missing or malformed reports FAIL closed.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TARGETS_MD = os.path.join("docs", "TARGETS.md")


def load_targets(path: str | None = None) -> list[dict[str, object]]:
    with open(path or TARGETS_MD, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"```yaml targets\n(.*?)```", text, re.DOTALL)
    if not m:
        raise ValueError("TARGETS.md has no ```yaml targets block")
    import yaml

    data = yaml.safe_load(m.group(1))
    if not isinstance(data, list) or not data:
        raise ValueError("TARGETS.md targets block is empty or malformed")
    return data


def read_json(path: str) -> dict[str, object]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def adversarial_fhr(path: str) -> float:
    rows = read_json(path).get("results", [])
    assert isinstance(rows, list)
    adv = [r for r in rows if isinstance(r, dict) and not r.get("should_heal")]
    healed = [r for r in adv if r.get("healed")]
    if not healed:
        return 0.0
    wrong = [r for r in healed if not r.get("correct")]
    return len(wrong) / len(healed)


def metric_value(name: str, source: str) -> float:
    if name == "false_heal_rate_adversarial":
        return adversarial_fhr(source)
    data = read_json(source)
    if name in ("cost_per_heal", "latency_per_heal_ms"):
        metrics = data.get("metrics", {})
        assert isinstance(metrics, dict)
        return float(metrics[name])
    key = {
        "heal_accuracy": "accuracy",
        "false_heal_rate_overall": "false_heal_rate",
        "critic_catch_rate": "catch_rate",
        "critic_false_reject_rate": "false_reject_rate",
        "classification_accuracy": "accuracy",
        "genuine_passed_to_heal": "genuine_passed_to_heal",
        "contract_healed": "contract_healed",
    }[name]
    return float(data[key])  # type: ignore[arg-type]


OPS = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
}


def check_alerts() -> tuple[str, str]:
    """Alert-completeness subgate: the alert unit tests must pass unmodified."""
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_alerts.py", "-q"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
    except Exception as exc:
        return "FAIL", f"could not run alert tests: {exc}"
    if r.returncode == 0:
        return "PASS", "tests/test_alerts.py green (builder enforces all fields)"
    return "FAIL", "tests/test_alerts.py red"


def main() -> None:
    try:
        targets = load_targets()
    except (OSError, ValueError) as exc:
        print(f"FAIL targets_block: {exc}")
        raise SystemExit(1)
    failed = 0
    for t in targets:
        name, op, value, source = (
            str(t["metric"]),
            str(t["op"]),
            float(t["value"]),
            str(t["source"]),
        )
        try:
            actual = metric_value(name, source)
        except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
            print(f"FAIL {name}: cannot read {source} ({exc})")
            failed += 1
            continue
        if OPS[op](actual, value):
            print(f"PASS {name}: {actual} {op} {value}")
        else:
            print(f"FAIL {name}: {actual} {op} {value} (from {source})")
            failed += 1
    status, detail = check_alerts()
    print(f"{status} alert_completeness: {detail}")
    failed += status != "PASS"
    print(
        "UNVERIFIED heal_survival_rate: no history yet (survival.py reports "
        "insufficient_data); becomes a FAIL gate once data accrues"
    )
    print(f"result: {'FAIL' if failed else 'PASS'} ({failed} failing)")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
