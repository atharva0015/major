"""Bench entrypoint: run baseline healer, write markdown + json reports."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.harness import run_all, summarize
from healing.policy.baseline import NoHealPolicy
from healing.quality.metrics import compute_metrics, to_markdown
from scripts.baseline_report import (
    estimated_manual_repairs,
    failures_by_class,
    locator_drift_share,
)

REPORT_MD = os.path.join("benchmark", "reports", "baseline.md")
REPORT_JSON = os.path.join("benchmark", "reports", "baseline.json")


def main() -> None:
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    results = run_all(NoHealPolicy(), seed=42)
    metrics = compute_metrics(results)
    summary = summarize(results)
    by_class = failures_by_class()
    share = locator_drift_share()
    repairs = estimated_manual_repairs()

    md = to_markdown(metrics, title="Baseline report (do-nothing healer)")
    md += f"\n- failures by class: {by_class}\n"
    md += f"- locator drift share: {share:.3f}\n"
    md += f"- estimated manual repairs: {repairs}\n"
    md += "- policy: baseline-0.1.0, seed: 42\n"
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    print(md.strip())


if __name__ == "__main__":
    main()
