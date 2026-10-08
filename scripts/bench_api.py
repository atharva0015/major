"""Bench API: conservative healing metrics with zero-tolerance contract gate."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.api.cases import API_CASES, EXPECTED
from healing.nonui.pipeline import heal_api_case

REPORT_MD = os.path.join("benchmark", "reports", "api.md")
REPORT_JSON = os.path.join("benchmark", "reports", "api.json")


def main() -> None:
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    rows: list[dict[str, object]] = []
    for case in API_CASES:
        out = heal_api_case(case)
        exp_class, exp_healed = EXPECTED[case.case_id]
        rows.append(
            {
                "case_id": case.case_id,
                "api_class": out.api_class,
                "expected_class": exp_class,
                "class_ok": out.api_class == exp_class,
                "healed": out.healed,
                "expected_healed": exp_healed,
                "heal_ok": out.healed == exp_healed,
                "action": out.action,
                "reason": out.reason,
            }
        )

    contract_healed = sum(1 for r in rows if r["api_class"] == "contract_change" and r["healed"])
    wrong = [r["case_id"] for r in rows if not (r["class_ok"] and r["heal_ok"])]
    healed_total = sum(1 for r in rows if r["healed"])
    false_heals = sum(1 for r in rows if r["healed"] and not r["expected_healed"])
    fheal = false_heals / healed_total if healed_total else 0.0
    md = [
        "# API benchmark report (conservative healing)\n",
        f"- cases: {len(rows)}",
        f"- auto-healed contract changes: {contract_healed} (must be 0)",
        f"- false-heal rate: {fheal:.3f}",
        f"- wrong cases: {wrong or 'none'}\n",
        "## Per-case (healed / escalated and why)\n",
        "| case | class | action | healed | reason |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(
            f"| {r['case_id']} | {r['api_class']} | {r['action']} | {r['healed']} | {r['reason']} |"
        )
    text = "\n".join(md) + "\n"
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(text)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {"contract_healed": contract_healed, "false_heal_rate": fheal, "rows": rows},
            f,
            indent=2,
            sort_keys=True,
        )
    print(text.strip())


if __name__ == "__main__":
    main()
