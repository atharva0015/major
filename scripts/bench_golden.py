"""Bench golden: re-run locked set; fail CI on accuracy drop / false-heal rise."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.cases import CASES
from benchmark.harness import candidates_from, page_html
from healing.orchestrator import HealerOrchestrator
from healing.policy.engine import load_config
from healing.quality.golden_set import load_golden

REPORT_MD = os.path.join("benchmark", "reports", "golden.md")
REPORT_JSON = os.path.join("benchmark", "reports", "golden.json")


def main() -> None:
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    golden = load_golden()
    expected = {c["case_id"]: c for c in golden["cases"]}  # type: ignore[index]
    cfg = load_config()
    orch = HealerOrchestrator(cfg)
    mismatches: list[str] = []
    healed_correct, healed_total, false_heals, healed_n = 0, 0, 0, 0
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
        exp = expected.get(case.case_id, {})
        if out.healed != exp.get("healed") or out.classification != exp.get("classification"):
            mismatches.append(case.case_id)
        if case.should_heal:
            healed_total += 1
            if out.healed == case.correct_element:
                healed_correct += 1
        if out.healed is not None:
            healed_n += 1
            if not case.should_heal or out.healed != case.correct_element:
                false_heals += 1
    accuracy = healed_correct / healed_total if healed_total else 0.0
    fhr = false_heals / healed_n if healed_n else 0.0
    ok = (
        not mismatches
        and accuracy >= cfg.golden_min_accuracy
        and fhr <= cfg.golden_max_false_heal_rate
    )
    md = (
        "# Golden-set report\n\n"
        f"- cases: {len(CASES)}, mismatches: {mismatches or 'none'}\n"
        f"- accuracy: {accuracy:.3f} (min {cfg.golden_min_accuracy})\n"
        f"- false-heal rate: {fhr:.3f} (max {cfg.golden_max_false_heal_rate})\n"
        f"- verdict: {'PASS' if ok else 'FAIL'}\n"
    )
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {"accuracy": accuracy, "false_heal_rate": fhr, "mismatches": mismatches, "pass": ok},
            f,
            indent=2,
            sort_keys=True,
        )
    print(md.strip())
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
