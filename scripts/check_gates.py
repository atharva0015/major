"""Gate checker: re-judge every gate against docs/TARGETS.md. Exit 1 on any FAIL.

Reads report JSON only (plus the alert unit tests as a subgate). Never
imports healing/ or benchmark/ code, so a broken pipeline cannot mask a
red gate. Missing or malformed reports FAIL closed — except gates that
declare live provenance: with no live report they are UNVERIFIED, never
graded on simulated data.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TARGETS_MD = os.path.join("docs", "TARGETS.md")
RAW_MATCHER_LIVE = os.path.join("benchmark", "reports", "healenium_live.json")


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
    """False-heal rate on should_heal=false rows.

    Fail closed: an empty, malformed, or non-adversarial report cannot prove
    a zero rate. It raises instead of returning 0.0, so a live gate becomes
    UNVERIFIED and a sim gate becomes FAIL.
    """
    data = read_json(path)
    rows = data.get("results", data.get("vias"))
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path} has no result rows")

    checked: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{path} row {index} is not an object")
        for field in ("should_heal", "healed"):
            if not isinstance(row.get(field), bool):
                raise ValueError(f"{path} row {index} lacks boolean {field}")
        if row["healed"] is True and not isinstance(row.get("correct"), bool):
            raise ValueError(f"{path} row {index} healed without boolean correct")
        checked.append(row)

    adv = [r for r in checked if r["should_heal"] is False]
    if not adv:
        raise ValueError(f"{path} has no should_heal=false rows")
    healed = [r for r in adv if r["healed"] is True]
    if not healed:
        return 0.0
    wrong = [r for r in healed if r["correct"] is not True]
    return len(wrong) / len(healed)


def live_source_for(source: str) -> str:
    """Live counterpart of a sim report path (healenium.json -> healenium_live.json)."""
    root, ext = os.path.splitext(source)
    if root.endswith("_live"):
        return source
    return root + "_live" + ext


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} is not a number")
    return float(value)


def _pipeline_latency(data: dict[str, object]) -> float:
    """Mean per-case orchestrator overhead from e2e_live.json rows."""
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("report has no rows")
    total = 0.0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"row {index} is not an object")
        total += _number(row.get("pipeline_ms"), f"row {index} pipeline_ms")
    return total / len(rows)


def metric_value(name: str, source: str, live: bool = False) -> float:
    if name == "false_heal_rate_adversarial":
        data = read_json(source)
        if "adversarial_fhr" in data:
            rows = data.get("rows")
            if not isinstance(rows, list) or not rows:
                raise ValueError(f"{source} has no rows")
            return _number(data["adversarial_fhr"], f"{source} adversarial_fhr")
        return adversarial_fhr(source)
    data = read_json(source)
    if name == "pipeline_latency_ms":
        return _pipeline_latency(data)
    if name in ("cost_per_heal", "latency_per_heal_ms"):
        metrics = data.get("metrics", {})
        assert isinstance(metrics, dict)
        return float(metrics[name])
    if live and name == "heal_accuracy":
        # Live reports nest accuracy under metrics; sim golden.json is flat.
        metrics = data.get("metrics", {})
        assert isinstance(metrics, dict)
        return float(metrics["heal_accuracy"])
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


def evaluate(run_alerts: bool = True) -> list[dict[str, object]]:
    """Return every gate as a structured row; never prints and never exits."""
    rows: list[dict[str, object]] = []

    def add(
        metric: str,
        op: str,
        target: float | None,
        provenance: str,
        status: str,
        actual: float | None,
        message: str,
        source: str,
    ) -> None:
        rows.append(
            {
                "metric": metric,
                "op": op,
                "target": target,
                "provenance": provenance,
                "status": status,
                "actual": actual,
                "message": message,
                "source": source,
            }
        )

    for t in load_targets():
        name, op, value, source = (
            str(t["metric"]),
            str(t["op"]),
            float(str(t["value"])),
            str(t["source"]),
        )
        provenance = str(t.get("provenance", "sim"))
        if provenance == "live":
            live_path = live_source_for(source)
            try:
                actual = metric_value(name, live_path, live=True)
            except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
                add(
                    name,
                    op,
                    value,
                    provenance,
                    "UNVERIFIED",
                    None,
                    f"UNVERIFIED {name} [live]: no live report at {live_path} "
                    f"({exc}); sim data must not stand in",
                    live_path,
                )
                continue
            ok = OPS[op](actual, value)
            status = "PASS" if ok else "FAIL"
            message = f"{status} {name} [live]: {actual} {op} {value}"
            if not ok:
                message += f" (from {live_path})"
            add(name, op, value, provenance, status, actual, message, live_path)
            continue
        try:
            actual = metric_value(name, source)
        except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
            add(
                name,
                op,
                value,
                provenance,
                "FAIL",
                None,
                f"FAIL {name}: cannot read {source} ({exc})",
                source,
            )
            continue
        ok = OPS[op](actual, value)
        status = "PASS" if ok else "FAIL"
        message = f"{status} {name} [sim]: {actual} {op} {value}"
        if not ok:
            message += f" (from {source})"
        add(name, op, value, provenance, status, actual, message, source)

    if run_alerts:
        status, detail = check_alerts()
        add(
            "alert_completeness",
            "==",
            1.0,
            "test",
            status,
            1.0 if status == "PASS" else 0.0,
            f"{status} alert_completeness: {detail}",
            "tests/test_alerts.py",
        )
    add(
        "heal_survival_rate",
        "TBD",
        None,
        "history",
        "UNVERIFIED",
        None,
        "UNVERIFIED heal_survival_rate: no history yet (survival.py reports "
        "insufficient_data); becomes a FAIL gate once data accrues",
        "healing/quality/survival.py",
    )
    return rows


def diagnostics(source: str = RAW_MATCHER_LIVE) -> list[dict[str, object]]:
    """Return non-gating raw-matcher and browser-latency diagnostics.

    These numbers explain why the shipped orchestrator path exists, but they
    do not decide pass/fail. A missing or malformed report is shown as
    unavailable instead of being treated as a zero.
    """
    rows: list[dict[str, object]] = []

    def add(metric: str, actual: float | None, message: str) -> None:
        rows.append(
            {
                "metric": metric,
                "op": "n/a",
                "target": None,
                "provenance": "live (non-gating)",
                "status": "DIAGNOSTIC",
                "actual": actual,
                "message": message,
                "source": source,
            }
        )

    try:
        raw = adversarial_fhr(source)
        add(
            "raw_matcher_adversarial_fhr",
            raw,
            f"DIAGNOSTIC raw_matcher_adversarial_fhr: {raw} (not gated; "
            "the orchestrator path is the gate)",
        )
    except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
        add(
            "raw_matcher_adversarial_fhr",
            None,
            f"DIAGNOSTIC raw_matcher_adversarial_fhr: unavailable ({exc})",
        )

    try:
        browser = metric_value("latency_per_heal_ms", source)
        add(
            "browser_latency_per_heal_ms",
            browser,
            f"DIAGNOSTIC browser_latency_per_heal_ms: {browser} (not gated; "
            "pipeline overhead is the gate)",
        )
    except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
        add(
            "browser_latency_per_heal_ms",
            None,
            f"DIAGNOSTIC browser_latency_per_heal_ms: unavailable ({exc})",
        )
    return rows


def main(strict: bool = False) -> None:
    """Print gate results; exit 1 on FAIL, or on UNVERIFIED when strict."""
    try:
        rows = evaluate()
    except (OSError, ValueError) as exc:
        print(f"FAIL targets_block: {exc}")
        raise SystemExit(1)
    for row in rows:
        print(row["message"])
    for row in diagnostics():
        print(row["message"])
    passed = sum(1 for row in rows if row["status"] == "PASS")
    failed = sum(1 for row in rows if row["status"] == "FAIL")
    unverified = sum(1 for row in rows if row["status"] == "UNVERIFIED")
    print(f"MEASURED PASS {passed} / FAIL {failed} / UNVERIFIED {unverified}")
    blocked = failed > 0 or (strict and unverified > 0)
    reason = f"{failed} failing"
    if strict:
        reason += f", {unverified} unverified in strict mode"
    print(f"result: {'FAIL' if blocked else 'PASS'} ({reason})")
    if blocked:
        raise SystemExit(1)


if __name__ == "__main__":
    main(strict="--strict" in sys.argv[1:])
