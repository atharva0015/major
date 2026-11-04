"""Derive `golden_live.json` from the measured live E2E report.

The `heal_accuracy [live]` gate expects
`benchmark/reports/golden_live.json` with `metrics.heal_accuracy`. The live
E2E bench (`bench_e2e_live.py`) writes `e2e_live.json`, not that shape. This
adapter reads the already-measured live report and writes the gate input.

It does **not** run Docker, a browser, or the stack, and it does not turn a
simulated report into a live one: the source must declare `"live": true` and
contain at least one row. Run `bench_e2e_live.py` first when the stack is up;
then run this adapter and `check_gates.py`.
"""

from __future__ import annotations

import json
import os

SOURCE = "benchmark/reports/e2e_live.json"
OUT = "benchmark/reports/golden_live.json"


def build_report(data: dict[str, object]) -> dict[str, object]:
    """Validate a live E2E report and return the gate-shaped golden report."""
    if data.get("live") is not True:
        raise ValueError("source is not a live report (live != true)")
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("source has no rows")
    accuracy = float(data["accuracy"])  # type: ignore[arg-type]
    if not 0.0 <= accuracy <= 1.0:
        raise ValueError(f"accuracy out of range: {accuracy}")
    false_heal_rate = float(data.get("false_heal_rate", 0.0))  # type: ignore[arg-type]
    if not 0.0 <= false_heal_rate <= 1.0:
        raise ValueError(f"false_heal_rate out of range: {false_heal_rate}")
    escaped = int(data.get("escaped", 0))  # type: ignore[arg-type]
    if escaped < 0:
        raise ValueError(f"escaped is negative: {escaped}")

    return {
        "metrics": {
            "heal_accuracy": accuracy,
            "false_heal_rate": false_heal_rate,
            "cases": len(rows),
            "escaped": escaped,
        },
        "source": SOURCE,
        "provenance": "live",
        "derivation": (
            "derived from the measured live E2E report; this adapter does not re-run the stack"
        ),
    }


def main() -> None:
    with open(SOURCE, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{SOURCE} is not a JSON object")
    report = build_report(data)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    metrics = report["metrics"]
    assert isinstance(metrics, dict)
    print(
        f"wrote {OUT}: heal_accuracy={metrics['heal_accuracy']} "
        f"cases={metrics['cases']} escaped={metrics['escaped']}"
    )


if __name__ == "__main__":
    main()
