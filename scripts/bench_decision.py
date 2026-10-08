"""Bench decision layer: classification accuracy + heal-engine gate proof."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.cases import CASES
from benchmark.harness import candidates_from, page_html
from healing.orchestrator import HealerOrchestrator

REPORT_MD = os.path.join("benchmark", "reports", "decision.md")
REPORT_JSON = os.path.join("benchmark", "reports", "decision.json")


def main() -> None:
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    orch = HealerOrchestrator()
    rows: list[dict[str, object]] = []
    for case in CASES:
        html = page_html(case.page, case.drift_mode)
        cands = candidates_from(html)
        out = orch.heal_case(
            case.case_id,
            case.case_id,
            case.drift_mode,
            html,
            case.locator,
            cands,
            case.correct_element,
        )
        rows.append(
            {
                "case_id": case.case_id,
                "true_class": case.true_class,
                "predicted": out.classification,
                "correct": out.classification == case.true_class,
                "decision": out.decision,
                "healed": out.healed,
            }
        )

    classes = sorted({r["true_class"] for r in rows} | {r["predicted"] for r in rows})
    matrix = {t: {p: 0 for p in classes} for t in classes}
    for r in rows:
        matrix[str(r["true_class"])][str(r["predicted"])] += 1
    acc = sum(1 for r in rows if r["correct"]) / len(rows) if rows else 0.0
    genuine_passed = sum(1 for r in rows if r["true_class"] == "genuine_regression" and r["healed"])
    wrong = [r["case_id"] for r in rows if not r["correct"]]

    md = [
        "# Decision-layer report (classify -> match -> policy -> record)\n",
        f"- cases: {len(rows)}",
        f"- classification accuracy: {acc:.3f}",
        f"- genuine_regression passed to heal engine: {genuine_passed}",
        f"- wrong cases: {wrong or 'none'}\n",
        "## Confusion matrix (true x predicted)\n",
        "| true \\ predicted | " + " | ".join(classes) + " |",
        "|" + "---|" * (len(classes) + 1),
    ]
    for t in classes:
        md.append("| " + t + " | " + " | ".join(str(matrix[t][p]) for p in classes) + " |")
    md += [
        "\n## Per-case results\n",
        "| case | true | predicted | decision | healed |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(
            f"| {r['case_id']} | {r['true_class']} | {r['predicted']} "
            f"| {r['decision']} | {r['healed']} |"
        )
    text = "\n".join(md) + "\n"
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(text)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {
                "accuracy": acc,
                "genuine_passed_to_heal": genuine_passed,
                "matrix": matrix,
                "rows": rows,
            },
            f,
            indent=2,
            sort_keys=True,
        )
    print(text.strip())


if __name__ == "__main__":
    main()
