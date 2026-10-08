"""Bench Healenium attempt-1: per-case results vs baseline + adversarial slice."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.cases import CASES
from benchmark.harness import run_all, summarize
from benchmark.healenium_healer import SIM_VERSION, HealeniumSimHealer
from healing.quality.metrics import compute_metrics, to_markdown

REPORT_MD = os.path.join("benchmark", "reports", "healenium.md")
REPORT_JSON = os.path.join("benchmark", "reports", "healenium.json")
BASELINE_JSON = os.path.join("benchmark", "reports", "baseline.json")


def adversarial_block(results: list[object]) -> str:
    adv = [r for r in results if not getattr(r, "should_heal")]
    healed = [r for r in adv if getattr(r, "healed")]
    wrong = [r for r in healed if not getattr(r, "correct")]
    rate = (len(wrong) / len(healed)) if healed else 0.0
    lines = [
        "## Adversarial cases (must NOT heal)",
        f"- adversarial total: {len(adv)}",
        f"- adversarial healed: {len(healed)}",
        f"- adversarial false heals: {len(wrong)}",
        f"- adversarial false-heal rate: {rate:.3f}",
        "",
        "| case | healed | escalated |",
        "|---|---|---|",
    ]
    for r in adv:
        lines.append(
            f"| {getattr(r, 'case_id')} | {getattr(r, 'healed')} | {getattr(r, 'escalated')} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    live = os.getenv("HEALENIUM_LIVE", "0") == "1"
    healer = HealeniumSimHealer()
    results = run_all(healer, seed=42)
    metrics = compute_metrics(results)
    summary = summarize(results)
    baseline: dict[str, object] = {}
    if os.path.exists(BASELINE_JSON):
        with open(BASELINE_JSON, encoding="utf-8") as f:
            baseline = json.load(f).get("metrics", {})

    md = to_markdown(metrics, title="Healenium attempt-1 report (sim)")
    md += f"\n- policy: {SIM_VERSION}, seed: 42, live: {live}\n"
    md += f"- baseline heal_accuracy: {baseline.get('heal_accuracy', 'n/a')}\n"
    md += f"- baseline escalation_rate: {baseline.get('escalation_rate', 'n/a')}\n"
    md += "\n" + adversarial_block(results)
    md += "\n## Per-case results\n\n| case | should_heal | healed | correct |\n"
    md += "|---|---|---|---|\n"
    for r in results:
        md += f"| {r.case_id} | {r.should_heal} | {r.healed} | {r.correct} |\n"
    md += f"\nExpected: {len(CASES)} cases.\n"
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    print(md.strip())


if __name__ == "__main__":
    main()
