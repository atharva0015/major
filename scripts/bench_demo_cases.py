"""Bench external mini-demo: frozen pipeline + sim-alone on 12 drift scenarios.

Method mirrors bench_heldout.py: orchestrator.heal_case per case, Critic
re-run on the healed choice, HealeniumSimHealer alone for comparison.
Custom drift names ("demo:*") hit no stock-drift branch in the sim, so the
sim heals iff the stable testid survives — documented, not tuned.
Writes benchmark/reports/demo_cases.md + demo_cases.json. Docker is down
in this environment, so all results below are SIMULATED (no live runs).
"""

from __future__ import annotations

import json
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

from benchmark.demo_cases.cases import CASES
from benchmark.harness import candidates_from
from benchmark.healenium_healer import HealeniumSimHealer
from healing.critic.checks import run_checks
from healing.orchestrator import HealerOrchestrator

REPORT_MD = os.path.join("benchmark", "reports", "demo_cases.md")
REPORT_JSON = os.path.join("benchmark", "reports", "demo_cases.json")
EXPECT_PATH = os.path.join("benchmark", "demo_cases", "cases.yaml")


def load_expected() -> dict[str, dict[str, object]]:
    with open(EXPECT_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {c["id"]: c for c in data["cases"]}


def sim_shim(case_id: str, drift_mode: str, correct: str | None) -> types.SimpleNamespace:
    # Custom "demo:*" modes match no stock branch in the sim: it then heals
    # iff the stable testid is present. Reported as-is.
    return types.SimpleNamespace(case_id=case_id, drift_mode=drift_mode, correct_element=correct)


def main() -> None:
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    expected = load_expected()
    orch = HealerOrchestrator()
    sim = HealeniumSimHealer()
    rows: list[dict[str, object]] = []
    for case in CASES:
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
            critic = "n/a (escalated, nothing to verify)"
        sim_pick = sim.choose_for_case(
            sim_shim(case.id, f"demo:{case.id}", case.correct_element), cands
        )
        exp = expected[case.id]
        exp_heal = exp["expected"] == "HEAL"
        if exp_heal:
            pipe_ok = out.healed == exp["heals_to"]
        else:
            pipe_ok = out.healed is None
        sim_ok = (sim_pick == exp["heals_to"]) if exp_heal else (sim_pick is None)
        rows.append(
            {
                "case_id": case.id,
                "expected": exp["expected"],
                "needs_review": exp["needs_review"],
                "pipeline": out.healed if out.healed else "ESCALATE",
                "pipeline_ok": pipe_ok,
                "sim_alone": sim_pick if sim_pick else "ESCALATE",
                "sim_ok": sim_ok,
                "critic": critic,
                "decision": out.decision,
                "classification": out.classification,
                "attempts": [(a.get("n"), a.get("strategy")) for a in out.attempts],
            }
        )

    n_heal = sum(1 for r in rows if r["expected"] == "HEAL")
    n_esc = len(rows) - n_heal
    pipe_fh = sum(1 for r in rows if r["expected"] == "ESCALATE" and r["pipeline"] != "ESCALATE")
    pipe_we = sum(1 for r in rows if r["expected"] == "HEAL" and r["pipeline"] == "ESCALATE")
    sim_fh = sum(1 for r in rows if r["expected"] == "ESCALATE" and r["sim_alone"] != "ESCALATE")
    sim_we = sum(1 for r in rows if r["expected"] == "HEAL" and r["sim_alone"] == "ESCALATE")
    md = [
        "# Demo-cases report (SIMULATED — Docker down, no live runs)\n",
        f"- cases: {len(rows)} (expected HEAL: {n_heal}, expected ESCALATE: {n_esc})",
        f"- pipeline false heals: {pipe_fh}",
        f"- pipeline wrong escalations: {pipe_we}",
        f"- sim-alone false heals: {sim_fh}",
        f"- sim-alone wrong escalations: {sim_we}\n",
        "## Per-case results\n",
        "| case | expected | pipeline | ok | sim-alone | sim ok | critic | decision |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(
            f"| {r['case_id']} | {r['expected']} | {r['pipeline']} | {r['pipeline_ok']} "
            f"| {r['sim_alone']} | {r['sim_ok']} | {r['critic']} | {r['decision']} |"
        )
    text = "\n".join(md) + "\n"
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(text)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {
                "pipeline_false_heals": pipe_fh,
                "pipeline_wrong_escalations": pipe_we,
                "sim_false_heals": sim_fh,
                "sim_wrong_escalations": sim_we,
                "rows": rows,
            },
            f,
            indent=2,
            sort_keys=True,
        )
    print(text.strip())


if __name__ == "__main__":
    main()
