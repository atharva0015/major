"""Bench held-out set: frozen pipeline measured on unseen cases.

Mirrors bench_decision.py / bench_verify.py / bench_api.py line-for-line in
method; only the case set differs. Writes benchmark/reports/heldout.md +
heldout.json, kept separate from the original benchmark. No tuning here:
failures are reported, not fixed.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.harness import candidates_from, page_html
from benchmark.heldout.api_cases import HELDOUT_API_CASES, HELDOUT_API_EXPECTED
from benchmark.heldout.ui_cases import HELDOUT_UI_CASES
from benchmark.wrong_heals import wrong_candidate
from demo_app.app import CART
from healing.critic.checks import run_checks
from healing.nonui.pipeline import heal_api_case
from healing.orchestrator import HealerOrchestrator

REPORT_MD = os.path.join("benchmark", "reports", "heldout.md")
REPORT_JSON = os.path.join("benchmark", "reports", "heldout.json")


def run_ui() -> dict[str, object]:
    CART.clear()
    orch = HealerOrchestrator()
    rows: list[dict[str, object]] = []
    wrong_injected, wrong_caught = 0, 0
    correct_proposed, correct_rejected = 0, 0
    for case in HELDOUT_UI_CASES:
        html = page_html(case.page, case.drift_mode)
        base = page_html(case.page, "none")
        cands = candidates_from(html)
        out = orch.heal_case(
            case.case_id,
            case.case_id,
            case.drift_mode,
            html,
            case.locator,
            cands,
            case.correct_element,
            baseline_html=base,
            key_elements=(tuple([case.correct_element]) if case.correct_element else ()),
            purpose=case.locator,
        )
        rows.append(
            {
                "case_id": case.case_id,
                "true_class": case.true_class,
                "predicted": out.classification,
                "correct": out.classification == case.true_class,
                "decision": out.decision,
                "healed": out.healed,
                "expected_healed": case.should_heal,
                "heal_ok": bool(out.healed) == case.should_heal
                and (not case.should_heal or out.healed == case.correct_element),
            }
        )
        if not case.should_heal:
            continue
        wrong = wrong_candidate(case, cands)
        if wrong and wrong != case.correct_element:
            wrong_injected += 1
            v = run_checks(
                html,
                wrong,
                case.correct_element,
                base,
                [case.correct_element] if case.correct_element else [],
                [],
                ["demo", "wiremock"],
                case.locator,
            )
            if not v.passed:
                wrong_caught += 1
        if case.correct_element and case.correct_element in cands:
            correct_proposed += 1
            v = run_checks(
                html,
                case.correct_element,
                case.correct_element,
                base,
                [case.correct_element],
                [],
                ["demo", "wiremock"],
                case.locator,
            )
            if not v.passed:
                correct_rejected += 1
    return {
        "rows": rows,
        "wrong_injected": wrong_injected,
        "wrong_caught": wrong_caught,
        "correct_proposed": correct_proposed,
        "correct_rejected": correct_rejected,
    }


def run_api() -> list[dict[str, object]]:
    CART.clear()
    rows: list[dict[str, object]] = []
    for case in HELDOUT_API_CASES:
        out = heal_api_case(case)
        exp_class, exp_healed = HELDOUT_API_EXPECTED[case.case_id]
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
    return rows


def main() -> None:
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    ui = run_ui()
    ui_rows = ui["rows"]
    assert isinstance(ui_rows, list)
    acc = sum(1 for r in ui_rows if r["correct"]) / len(ui_rows) if ui_rows else 0.0
    false_heals = sum(1 for r in ui_rows if r["healed"] and not r["heal_ok"])
    healed_total = sum(1 for r in ui_rows if r["healed"])
    fheal = false_heals / healed_total if healed_total else 0.0
    escaped = [r["case_id"] for r in ui_rows if not r["heal_ok"]]
    wi_raw, wc_raw, cp_raw, cr_raw = (
        ui["wrong_injected"],
        ui["wrong_caught"],
        ui["correct_proposed"],
        ui["correct_rejected"],
    )
    assert isinstance(wi_raw, int) and isinstance(wc_raw, int)
    assert isinstance(cp_raw, int) and isinstance(cr_raw, int)
    wi, wc, cp, cr = wi_raw, wc_raw, cp_raw, cr_raw
    catch = wc / wi if wi else 0.0
    freject = cr / cp if cp else 0.0

    api_rows = run_api()
    api_wrong = [r["case_id"] for r in api_rows if not (r["class_ok"] and r["heal_ok"])]
    api_healed = sum(1 for r in api_rows if r["healed"])
    api_fheal = (
        sum(1 for r in api_rows if r["healed"] and not r["expected_healed"]) / api_healed
        if api_healed
        else 0.0
    )
    api_contract = sum(1 for r in api_rows if r["api_class"] == "contract_change" and r["healed"])

    md = [
        "# Held-out report (frozen pipeline, unseen cases, seed 42)\n",
        "## UI (24 cases)",
        f"- classification accuracy: {acc:.3f}",
        f"- critic catch rate: {catch:.3f} ({ui['wrong_caught']}/{wi} injected)",
        f"- critic false-reject rate: {freject:.3f}",
        f"- false-heal rate: {fheal:.3f}",
        f"- escaped defects: {len(escaped)}",
        f"- wrong cases: {escaped or 'none'}\n",
        "## API (11 cases)",
        f"- class+heal match: {len(api_rows) - len(api_wrong)}/{len(api_rows)}",
        f"- auto-healed contract changes: {api_contract} (must be 0)",
        f"- false-heal rate: {api_fheal:.3f}",
        f"- wrong cases: {api_wrong or 'none'}\n",
        "## Per-case UI\n",
        "| case | true | predicted | decision | healed | heal_ok |",
        "|---|---|---|---|---|---|",
    ]
    for r in ui_rows:
        md.append(
            f"| {r['case_id']} | {r['true_class']} | {r['predicted']} "
            f"| {r['decision']} | {r['healed']} | {r['heal_ok']} |"
        )
    md += [
        "",
        "## Per-case API",
        "| case | class | action | healed | heal_ok |",
        "|---|---|---|---|---|",
    ]
    for r in api_rows:
        md.append(
            f"| {r['case_id']} | {r['api_class']} | {r['action']} "
            f"| {r['healed']} | {r['heal_ok']} |"
        )
    text = "\n".join(md) + "\n"
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(text)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {
                "ui_accuracy": acc,
                "ui_catch_rate": catch,
                "ui_false_reject_rate": freject,
                "ui_false_heal_rate": fheal,
                "ui_escaped": len(escaped),
                "api_wrong": len(api_wrong),
                "api_contract_healed": api_contract,
                "api_false_heal_rate": api_fheal,
                "ui_rows": ui_rows,
                "api_rows": api_rows,
            },
            f,
            indent=2,
            sort_keys=True,
        )
    print(text.strip())


if __name__ == "__main__":
    main()
