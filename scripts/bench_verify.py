"""Bench verify: critic catch/false-reject rates + success by attempt."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.cases import CASES
from benchmark.harness import candidates_from, page_html
from benchmark.wrong_heals import wrong_candidate
from healing.critic.checks import run_checks
from healing.orchestrator import HealerOrchestrator

REPORT_MD = os.path.join("benchmark", "reports", "verify.md")
REPORT_JSON = os.path.join("benchmark", "reports", "verify.json")


def main() -> None:
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    orch = HealerOrchestrator()
    by_attempt = {1: [0, 0], 2: [0, 0], 3: [0, 0]}  # n -> [success, total_healable]
    wrong_injected, wrong_caught = 0, 0
    correct_proposed, correct_rejected = 0, 0
    false_heals = 0
    for case in CASES:
        if not case.should_heal:
            continue
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
        won_at = next(
            (
                a["n"]
                for a in out.attempts
                if a.get("candidate") == out.healed and a.get("verdict") is True
            ),
            None,
        )
        for n in by_attempt:
            by_attempt[n][1] += 1
        if won_at in by_attempt and out.healed:
            by_attempt[won_at][0] += 1
        if out.healed and out.healed != case.correct_element:
            false_heals += 1
        # Wrong-heal injection: would the Critic catch it?
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
        # False-reject probe: does the Critic accept the right answer?
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

    catch = wrong_caught / wrong_injected if wrong_injected else 0.0
    freject = correct_rejected / correct_proposed if correct_proposed else 0.0
    fheal = false_heals / len([c for c in CASES if c.should_heal])
    md = [
        "# Verify-before-it-matters report (sandbox + layered Critic)\n",
        f"- wrong heals injected: {wrong_injected}",
        f"- critic catch rate: {catch:.3f}",
        f"- critic false-reject rate: {freject:.3f}",
        f"- orchestrator false-heal rate: {fheal:.3f}\n",
        "## Heal success by attempt\n",
        "| attempt | success | total | rate |",
        "|---|---|---|---|",
    ]
    for n in (1, 2, 3):
        s, t = by_attempt[n]
        md.append(f"| {n} | {s} | {t} | {(s / t if t else 0.0):.3f} |")
    text = "\n".join(md) + "\n"
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(text)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {
                "catch_rate": catch,
                "false_reject_rate": freject,
                "false_heal_rate": fheal,
                "by_attempt": {str(k): v for k, v in by_attempt.items()},
            },
            f,
            indent=2,
            sort_keys=True,
        )
    print(text.strip())


if __name__ == "__main__":
    main()
