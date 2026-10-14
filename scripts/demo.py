"""One-command presentation demo: 12 mini-demo cases, sim vs pipeline.

Prints a compact per-case table plus one XAI explanation record for a
heal and one for an escalation. Always labeled SIMULATED: the Healenium
simulator and in-process HTML are used, no browser or Docker involved.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

from benchmark.demo_cases.cases import CASES
from benchmark.demo_cases.hard_cases import HARD_CASES
from benchmark.harness import candidates_from
from benchmark.healenium_healer import HealeniumSimHealer
from healing.critic.checks import run_checks
from healing.orchestrator import HealerOrchestrator

EXPECT_PATH = os.path.join("benchmark", "demo_cases", "cases.yaml")


def main() -> None:
    with open(EXPECT_PATH, encoding="utf-8") as f:
        expected = {c["id"]: c for c in yaml.safe_load(f)["cases"]}
    orch = HealerOrchestrator()
    sim = HealeniumSimHealer()
    print(f"demo run: SIMULATED (no Docker/browser)  date: {datetime.date.today().isoformat()}")
    print("| case | expected | pipeline | sim-alone | critic |")
    print("|---|---|---|---|---|")
    heal_record: object = None
    esc_record: object = None
    all_cases = list(CASES) + list(HARD_CASES)
    for case in all_cases:
        cands = candidates_from(case.html)
        out = orch.heal_case(
            case.id,
            case.step,
            f"demo:{case.id}",
            case.html,
            case.locator,
            cands,
            case.correct_element,
            baseline_html=case.baseline_html,
            key_elements=([case.correct_element] if case.correct_element else ()),
            purpose=case.step,
        )
        shim = types.SimpleNamespace(
            case_id=case.id, drift_mode=f"demo:{case.id}", correct_element=case.correct_element
        )
        sim_pick = sim.choose_for_case(shim, cands)
        if out.healed:
            v = run_checks(
                case.html,
                out.healed,
                case.correct_element,
                case.baseline_html,
                [case.correct_element] if case.correct_element else [],
                [],
                ["demo", "wiremock"],
                case.locator,
            )
            critic = f"{'pass' if v.passed else 'fail'}:{v.failed_layer or 'all-layers'}"
        else:
            critic = "n/a (escalated)"
        exp = expected[case.id]["expected"]
        print(
            f"| {case.id} | {exp} | {out.healed or 'ESCALATE'} "
            f"| {sim_pick or 'ESCALATE'} | {critic} |"
        )
        if case.id == "renamed_id":
            heal_record = out.record
        if case.id == "lookalike_trap":
            esc_record = out.record
    print("\n--- XAI record: heal (renamed_id) ---")
    print(json.dumps(heal_record.model_dump(mode="json"), indent=2, sort_keys=True))
    print("\n--- XAI record: escalation (lookalike_trap) ---")
    print(json.dumps(esc_record.model_dump(mode="json"), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
