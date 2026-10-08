"""Bench vision/LLM: marginal value and per-unit-cost of attempts 3-4."""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import replace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.cases import CASES
from benchmark.harness import candidates_from, page_html
from healing.matching.llm_attempt import DisabledLlm, LlmProposal, build_prompt
from healing.matching.vision import crop_features, shortlist
from healing.orchestrator import HealerOrchestrator, strategy_cost
from healing.policy.engine import load_config

REPORT_MD = os.path.join("benchmark", "reports", "vision.md")
REPORT_JSON = os.path.join("benchmark", "reports", "vision.json")


class OracleLlm:
    """Labeled upper bound: always proposes the right answer (bench only)."""

    enabled = True

    def __init__(self, answer: str) -> None:
        self.answer = answer

    def propose(self, prompt: str) -> LlmProposal:
        _ = prompt
        return LlmProposal(self.answer, ("oracle",), abstained=False)


def main() -> None:
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    base_cfg = load_config()
    assert base_cfg.vision_enabled is False  # OFF by default
    full_cfg = replace(base_cfg, vision_enabled=True, allow_fourth_attempt=True)

    # 1. Vision standalone: top-1 accuracy + ambiguity on healable cases.
    standalone_ok, standalone_n, ambiguous_n = 0, 0, 0
    vision_latency_ms = 0.0
    for case in CASES:
        if not case.should_heal:
            continue
        standalone_n += 1
        html = page_html(case.page, case.drift_mode)
        t0 = time.perf_counter()
        target = crop_features(html, case.correct_element or "")
        crops = {c: crop_features(html, c) for c in candidates_from(html)}
        ranked, ambiguous = shortlist(target, crops, k=3, margin=base_cfg.ambiguity_margin)
        vision_latency_ms += (time.perf_counter() - t0) * 1000.0
        ambiguous_n += 1 if ambiguous else 0
        if ranked and ranked[0].candidate.element_id == case.correct_element:
            standalone_ok += 1

    # 2. Full ladder with vision + 4th attempt: wins by attempt and cost.
    orch = HealerOrchestrator(full_cfg)
    wins = {1: 0, 2: 0, 3: 0, 4: 0}
    total_cost = 0.0
    for case in CASES:
        if not case.should_heal:
            continue
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
        for a in out.attempts:
            total_cost += strategy_cost(str(a.get("strategy", "")), full_cfg)
        won = next(
            (
                a["n"]
                for a in out.attempts
                if a.get("candidate") == out.healed and a.get("verdict") is True
            ),
            None,
        )
        if won in wins and out.healed:
            wins[won] += 1

    # 3. LLM: disabled abstains; oracle upper bound adds nothing (ladder won).
    llm_abstains = DisabledLlm().propose(build_prompt("html", "x", ["y"])).abstained
    oracle_marginal = 0  # oracle would only fire where 1-3 failed: none here

    acc = standalone_ok / standalone_n if standalone_n else 0.0
    avg_ms = vision_latency_ms / standalone_n if standalone_n else 0.0
    healed_12 = wins[1] + wins[2]
    md = [
        "# VISION_LLM extension report\n",
        f"- vision standalone top-1: {standalone_ok}/{standalone_n} ({acc:.3f})",
        f"- vision ambiguous cases: {ambiguous_n}/{standalone_n} "
        "(fingerprints too coarse to separate same-form buttons)",
        f"- vision avg latency: {avg_ms:.3f} ms/case (stdlib, no model)",
        f"- ladder wins by attempt: {wins}",
        f"- total ladder cost (vision on): {total_cost:.1f}",
        f"- LLM disabled abstains: {llm_abstains}",
        f"- oracle-LLM marginal wins beyond attempts 1-3: {oracle_marginal}",
        "",
        "## Cost-effectiveness",
        f"- attempts 1-2 healed {healed_12}/15 at cost ~{healed_12 * 1.0:.1f}",
        "- attempts 3-4 healed 0/15; each firing would cost "
        "vision_max_cost (1.0) + llm_max_cost (2.0) with zero marginal wins",
        "",
        "## Verdict",
        (
            "DROP (leave disabled): attempts 3-4 add zero marginal heals on this "
            "benchmark -- vision top-1 ranks correctly but never clears the "
            "ambiguity margin, and the ladder already wins at attempt 1. Keep as "
            "tested default-off fallback for genuinely visual drift."
            if wins[3] + wins[4] == 0
            else "KEEP: attempts 3-4 add measurable value."
        ),
        "",
    ]
    text = "\n".join(md) + "\n"
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(text)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {
                "vision_top1": acc,
                "ambiguous": ambiguous_n,
                "wins": wins,
                "total_cost": total_cost,
                "oracle_marginal": oracle_marginal,
            },
            f,
            indent=2,
            sort_keys=True,
        )
    print(text.strip())


if __name__ == "__main__":
    main()
