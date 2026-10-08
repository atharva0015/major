"""Shadow run: record what would be done, open no PRs, compare to truth."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.cases import CASES
from benchmark.harness import candidates_from, page_html
from healing.orchestrator import HealerOrchestrator

REPORT_MD = os.path.join("benchmark", "reports", "shadow.md")
REPORT_JSON = os.path.join("benchmark", "reports", "shadow.json")

OPEN_PR_CALLS = 0  # would-be PR opens; must stay 0 in shadow mode


def main() -> None:
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    orch = HealerOrchestrator()
    assert orch.config.shadow_mode, "shadow report requires shadow_mode: true"
    rows: list[dict[str, object]] = []
    for case in CASES:
        html = page_html(case.page, case.drift_mode)
        out = orch.heal_case(
            case.case_id,
            case.case_id,
            case.drift_mode,
            html,
            case.locator,
            candidates_from(html),
            case.correct_element,
        )
        proposed = out.healed is not None
        should = case.should_heal
        escaped = (proposed and not should) or (not proposed and should)
        if case.should_heal:
            assert out.shadow_pr is not None, f"shadow artifact missing for {case.case_id}"
        rows.append(
            {
                "case_id": case.case_id,
                "proposed_heal": proposed,
                "ground_truth_heal": should,
                "escaped": escaped,
                "shadow_pr_built": out.shadow_pr is not None,
            }
        )

    escaped_n = sum(1 for r in rows if r["escaped"])
    md = [
        "# Shadow-mode report (no PRs opened)\n",
        f"- cases: {len(rows)}",
        f"- PRs opened: {OPEN_PR_CALLS}",
        f"- escaped defects (shadow vs ground truth): {escaped_n}",
        f"- wrong cases: {[r['case_id'] for r in rows if r['escaped']] or 'none'}\n",
        "Note: ground truth stands in for engineer actions (none recorded yet).\n",
        "## Per-case\n",
        "| case | proposed | truth | escaped |",
        "|---|---|---|---|",
    ]
    for r in rows:
        md.append(
            f"| {r['case_id']} | {r['proposed_heal']} | {r['ground_truth_heal']} | {r['escaped']} |"
        )
    text = "\n".join(md) + "\n"
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(text)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {"prs_opened": OPEN_PR_CALLS, "escaped": escaped_n, "rows": rows},
            f,
            indent=2,
            sort_keys=True,
        )
    print(text.strip())


if __name__ == "__main__":
    main()
