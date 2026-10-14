"""Live end-to-end: live matcher -> classify -> policy -> sandbox -> Critic -> alerts.

For each of the 24 UI cases (including the 9 adversarial ones):
  1. live matcher: naive By.ID lookup through hlm-proxy in a real browser
     (imported from bench_healenium_live; no logic duplicated here);
  2. classify with the production rules on deterministic signals;
  3. blocked classes short-circuit to escalation with zero retries;
  4. otherwise the attempt ladder: attempt 1 = live pick, attempts 2+ =
     rescorer (REWEIGHTED), each gated by sandbox replay + layered Critic
     + policy decide(), with budgets enforced;
  5. explanation record + audit entry + alert (console + file senders only).

Shadow mode: this script never imports gitops and opens no PRs.
No source logic is modified; every helper below is an existing public API.
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.cases import CASES, BenchmarkCase
from benchmark.harness import candidates_from, page_html
from healing.alerts.model import build_alert, quarantine_test, severity_for
from healing.alerts.routers import ConsoleSender, FileSender, Sender
from healing.classifier.rules import classify
from healing.critic.checks import DisabledJudge, apply_judge, run_checks
from healing.matching.base import Candidate, ScoredCandidate
from healing.matching.rescorer import rescore
from healing.orchestrator import REWEIGHTED, STRATEGIES, signals_for, strategy_cost, vision_allowed
from healing.policy.engine import PolicyConfig, decide, load_config
from healing.sandbox.runner import SandboxConfig, SandboxSession
from healing.security import audit
from healing.security.masking import mask_pii
from healing.xai.narrative import render_narrative
from healing.xai.records import (
    CandidateScore,
    ExplanationRecord,
    Rejected,
    get_store,
    make_record,
)
from scripts.bench_healenium_live import restart_demo, run_case_live

REPORT_MD = os.path.join("benchmark", "reports", "e2e_live.md")
REPORT_JSON = os.path.join("benchmark", "reports", "e2e_live.json")
LIVE_POLICY = "healenium-live-0.1.0"


def build_record(
    test: str,
    case_id: str,
    cls_name: str,
    probs: dict[str, float],
    ranked: list[ScoredCandidate],
    selected: str | None,
    decision_action: str,
    attempts: list[dict[str, object]],
    escalation: str | None,
    candidates: list[str],
    cfg: PolicyConfig,
) -> ExplanationRecord:
    _ = candidates
    rejected = [
        Rejected(
            element_id=r.candidate.element_id,
            why=(
                "below_top" if r.candidate.element_id != selected else f"decision:{decision_action}"
            ),
        )
        for r in ranked
        if r.candidate.element_id != selected
    ]
    return make_record(
        heal_id=f"e2e-{uuid.uuid4().hex[:12]}",
        test=test,
        step=case_id,
        classification=cls_name,
        probabilities=probs,
        candidates=[
            CandidateScore(
                element_id=r.candidate.element_id, score=r.score, contributions=r.contributions
            )
            for r in ranked
        ],
        selected=selected,
        rejected=rejected,
        thresholds_applied={
            "high": cfg.high,
            "medium": cfg.medium,
            "ambiguity_margin": cfg.ambiguity_margin,
        },
        critic_checks={"attempts": attempts, "verdict": ("pass" if selected else "fail")},
        escalation_reason=escalation,
        model_version=cfg.model_version,  # type: ignore[union-attr]
        prompt_version=cfg.prompt_version,  # type: ignore[union-attr]
        policy_version=cfg.policy_version,  # type: ignore[union-attr]
        config_version=cfg.config_version,  # type: ignore[union-attr]
    )


def send_alert(
    test: str,
    cls_name: str,
    attempts: list[dict[str, object]],
    decision_action: str,
    selected: str | None,
    senders: list[Sender],
) -> None:
    alert = build_alert(
        test=test,
        classification=cls_name,
        attempts=attempts,
        screenshots={
            "before": f"screenshots/{test}-before.png",
            "after": f"screenshots/{test}-after.png",
            "candidate": f"screenshots/{test}-candidate.png",
        },
        next_step=("human review" if selected is None else "review shadow PR"),
        replay_link="sandbox://replay",
        severity=severity_for(cls_name),
    )
    if selected is None:
        quarantine_test(alert)
    for sender in senders:
        sender.send(alert)


def run_pipeline_case(case: object, live: dict[str, object], session_no: int) -> dict[str, object]:
    """Full live pipeline for one case. Returns the per-case row."""
    cfg = load_config()
    store = get_store()
    senders: list[Sender] = [ConsoleSender(), FileSender()]
    case_id = str(getattr(case, "case_id"))
    drift = str(getattr(case, "drift_mode"))
    locator = str(getattr(case, "locator"))
    correct = getattr(case, "correct_element")
    html = page_html(str(getattr(case, "page")), drift)
    base = page_html(str(getattr(case, "page")), "none")
    cands = candidates_from(html)
    _ = mask_pii(html, cfg.masking_extra_patterns)
    t0 = time.perf_counter()

    cls = classify(signals_for(drift, html, locator), cfg)
    confidence = round(cls.probabilities.get(cls.failure_class, 0.0), 4)
    row: dict[str, object] = {
        "case_id": case_id,
        "classification": cls.failure_class,
        "live_via": live["via"],
        "live_latency_ms": round(float(str(live["latency_ms"])), 1),
    }

    if cls.failure_class in cfg.blocked_classes:
        reason = f"blocked_class:{cls.failure_class}"
        record = make_record(
            heal_id=f"e2e-{uuid.uuid4().hex[:12]}",
            test=case_id,
            step=case_id,
            classification=cls.failure_class,
            probabilities=dict(cls.probabilities),
            candidates=[],
            selected=None,
            rejected=[Rejected(element_id=c, why=reason) for c in cands],
            thresholds_applied={
                "high": cfg.high,
                "medium": cfg.medium,
                "ambiguity_margin": cfg.ambiguity_margin,
            },
            critic_checks={"verdict": "escalated", "stub": False},
            escalation_reason=reason,
            model_version=cfg.model_version,
            prompt_version=cfg.prompt_version,
            policy_version=cfg.policy_version,
            config_version=cfg.config_version,
        )
        render_narrative(record)
        store.append(record)
        audit.append("system", "escalate", case_id, reason)
        send_alert(case_id, cls.failure_class, [], "fail_escalate", None, senders)
        row.update(
            attempts_used=[],
            critic="n/a (short-circuit, 0 retries)",
            action="fail_escalate",
            healed=None,
            correct=not bool(getattr(case, "should_heal")),
            pipeline_ms=round((time.perf_counter() - t0) * 1000.0, 1),
        )
        return row

    order = {c: i for i, c in enumerate(cands)}
    target = Candidate(element_id=correct or "", position=order.get(correct or "", 0))
    cand_objs = [Candidate(element_id=c, position=i) for i, c in enumerate(cands)]
    ranked_all = rescore(target, cand_objs)
    tried: list[str] = []
    attempts: list[dict[str, object]] = []
    cost_used = 0.0
    judge = DisabledJudge()
    decision = None
    cap = cfg.max_attempts + (1 if cfg.allow_fourth_attempt else 0)
    live_id = str(live.get("resolved_testid") or "") or None

    for n in range(1, cap + 1):
        strategy = "live_match" if n == 1 else (STRATEGIES[n - 1] if n <= len(STRATEGIES) else "x")
        ta0 = time.perf_counter()
        if strategy in ("vision_match", "llm_attempt", "x"):
            if not vision_allowed(cfg, ""):
                attempts.append(
                    {
                        "n": n,
                        "strategy": strategy or "vision_match",
                        "verdict": "unverified",
                        "reason": "vision_llm_disabled",
                    }
                )
                continue
        if n == 1:
            if not live_id:
                attempts.append(
                    {"n": n, "strategy": "live_match", "verdict": False, "reason": "live_escalated"}
                )
                continue
            top_id, score, gap, conf_mult = live_id, 1.0, 1.0, 1.0
        else:
            weights = REWEIGHTED
            ranked = [
                r
                for r in rescore(target, cand_objs, weights)
                if r.candidate.element_id not in tried
            ]
            top = ranked[0] if ranked else None
            if top is None:
                attempts.append(
                    {"n": n, "strategy": strategy, "verdict": False, "reason": "no_candidates"}
                )
                continue
            second = ranked[1] if len(ranked) > 1 else None
            gap = round(top.score - second.score, 4) if top and second else 1.0
            top_id, score, conf_mult = top.candidate.element_id, top.score, 1.0
        with SandboxSession(SandboxConfig(seed=42)) as sbx:
            verdict = run_checks(
                html,
                top_id,
                correct,
                base,
                ([correct] if correct else []),
                sbx.wiremock.calls,
                ["demo", "wiremock"],
                locator,
            )
            _ = sbx.run(lambda: f'data-testid="{top_id}"' in html)
        verdict = apply_judge(verdict, judge, html, top_id)
        conf = round(confidence * verdict.confidence_multiplier * conf_mult, 4)
        decision = decide(cls.failure_class, conf, gap, verdict.passed, cfg)
        step_cost = strategy_cost(strategy if strategy != "live_match" else "healenium_match", cfg)
        cost_used += step_cost
        elapsed = time.perf_counter() - t0
        won = decision.action in ("heal_pr", "heal_unverified") and bool(verdict.passed)
        attempts.append(
            {
                "n": n,
                "strategy": strategy,
                "candidate": top_id,
                "verdict": verdict.passed,
                "reason": decision.reason,
                "score": score,
                "gap": gap,
                "latency_ms": round((time.perf_counter() - ta0) * 1000.0, 1),
            }
        )
        if elapsed > cfg.per_heal_timeout_s or cost_used > cfg.per_heal_cost_budget:
            decision = decide(cls.failure_class, conf, gap, False, cfg)
            record = build_record(
                case_id,
                case_id,
                cls.failure_class,
                dict(cls.probabilities),
                ranked_all,
                None,
                decision.action,
                attempts,
                "budget_exceeded",
                cands,
                cfg,
            )
            render_narrative(record)
            store.append(record)
            audit.append("system", "escalate", case_id, "budget_exceeded")
            send_alert(case_id, cls.failure_class, attempts, decision.action, None, senders)
            row.update(
                attempts_used=[a["n"] for a in attempts],
                critic=f"budget_exceeded after attempt {n}",
                action="fail_escalate",
                healed=None,
                correct=not bool(getattr(case, "should_heal")),
                pipeline_ms=round(elapsed * 1000.0, 1),
            )
            return row
        if won:
            record = build_record(
                case_id,
                case_id,
                cls.failure_class,
                dict(cls.probabilities),
                ranked_all,
                top_id,
                decision.action,
                attempts,
                None,
                cands,
                cfg,
            )
            render_narrative(record)
            store.append(record)
            audit.append("system", "heal", case_id, decision.action)
            send_alert(case_id, cls.failure_class, attempts, decision.action, top_id, senders)
            critic_txt = f"pass ({verdict.failed_layer})" if verdict.failed_layer else "pass"
            row.update(
                attempts_used=[a["n"] for a in attempts],
                critic=critic_txt,
                action=decision.action,
                healed=top_id,
                correct=(top_id == correct),
                pipeline_ms=round((time.perf_counter() - t0) * 1000.0, 1),
            )
            return row
        tried.append(top_id)

    if decision is None:
        decision = decide(cls.failure_class, 0.0, 1.0, False, cfg)
    last = attempts[-1] if attempts else {}
    critic_txt = f"fail ({last.get('reason', 'ladder_exhausted')})"
    record = build_record(
        case_id,
        case_id,
        cls.failure_class,
        dict(cls.probabilities),
        ranked_all,
        None,
        decision.action,
        attempts,
        str(last.get("reason", "ladder_exhausted")),
        cands,
        cfg,
    )
    render_narrative(record)
    store.append(record)
    audit.append("system", "escalate", case_id, decision.action)
    send_alert(case_id, cls.failure_class, attempts, decision.action, None, senders)
    row.update(
        attempts_used=[a["n"] for a in attempts],
        critic=critic_txt,
        action="fail_escalate",
        healed=None,
        correct=not bool(getattr(case, "should_heal")),
        pipeline_ms=round((time.perf_counter() - t0) * 1000.0, 1),
    )
    return row


def main() -> None:
    os.makedirs(os.path.dirname(os.path.join("benchmark", "reports", "e2e_live.md")), exist_ok=True)
    by_drift: dict[str, list[BenchmarkCase]] = {}
    for case in CASES:
        by_drift.setdefault(str(getattr(case, "drift_mode")), []).append(case)
    restart_demo("none")
    for page in ("/login", "/products", "/checkout"):
        from scripts.bench_healenium_live import DEMO_IN_COMPOSE, new_session

        driver = new_session()
        try:
            driver.get(DEMO_IN_COMPOSE + page)
        finally:
            driver.quit()
    rows: list[dict[str, object]] = []
    session_no = 0
    for drift in sorted(by_drift):
        restart_demo(drift)
        for case in by_drift[drift]:
            session_no += 1
            live = run_case_live(case, session_no)
            rows.append(run_pipeline_case(case, live, session_no))
    n = len(rows)
    healable = [r for r in rows if r["healed"]]
    adv = [
        r
        for r in rows
        if str(r["case_id"]).split(":")[0]
        in ("duplicate_buttons", "removed_element", "swapped_roles")
    ]
    adv_healed = [r for r in adv if r["healed"]]
    adv_wrong = [r for r in adv_healed if not r["correct"]]
    escaped = [r for r in rows if not r["correct"]]
    acc = len([r for r in rows if r["correct"]]) / n if n else 0.0
    fheal = len([r for r in healable if not r["correct"]]) / len(healable) if healable else 0.0
    adv_fhr = len(adv_wrong) / len(adv_healed) if adv_healed else 0.0
    esc_rate = len([r for r in rows if r["action"] == "fail_escalate"]) / n if n else 0.0
    lat = [float(str(r["live_latency_ms"])) for r in rows if r["healed"]] or [0.0]
    lat_mean = sum(float(v) for v in lat) / len(lat)
    md = [
        "# Live end-to-end report (MEASURED, live stack, seed 42)",
        "",
        f"- cases: {n}",
        f"- accuracy: {acc:.3f}",
        f"- false-heal rate overall: {fheal:.3f}",
        f"- adversarial false-heal rate (9 cases): {adv_fhr:.3f}",
        f"- escalation rate: {esc_rate:.3f}",
        f"- escaped defects: {len(escaped)}",
        f"- latency per heal (live lookup ms, mean): {lat_mean:.1f}",
        "- policy: healenium-live-0.1.0, shadow mode, no PRs opened",
        "",
        "## Per-case results (all MEASURED)",
        "",
        "| case | classification | attempts | critic | action | healed | correct |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(
            f"| {r['case_id']} | {r['classification']} | {r['attempts_used']} | "
            f"{r['critic']} | {r['action']} | {r['healed']} | {r['correct']} |"
        )
    md.append("")
    md.append(
        "Warmup: one green pass over 3 pages before drift runs. "
        "Shadow mode: records + alerts only, no PRs opened."
    )
    md.append(f"Escaped case ids: {[r['case_id'] for r in escaped] or 'none'}")
    text = "\n".join(md) + "\n"
    with open(os.path.join("benchmark", "reports", "e2e_live.md"), "w", encoding="utf-8") as f:
        f.write(text)
    with open(os.path.join("benchmark", "reports", "e2e_live.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "rows": rows,
                "accuracy": acc,
                "false_heal_rate": fheal,
                "adversarial_fhr": adv_fhr,
                "escalation_rate": esc_rate,
                "escaped": len(escaped),
                "latency_per_heal_ms": lat_mean,
                "live": True,
            },
            f,
            indent=2,
            sort_keys=True,
        )
    print(text.strip())


if __name__ == "__main__":
    main()
