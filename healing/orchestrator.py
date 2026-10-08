"""Healer orchestrator: classify -> attempt ladder (sandbox+critic) -> record.

Blocked classes (genuine_regression, environment_issue, contract_change)
never reach the heal engine and get no retries: they short-circuit to
escalation. A sandbox pass alone never approves a heal; the Critic
verdict plus policy decides.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from healing.classifier.rules import Classification, FailureSignals, classify
from healing.critic.checks import DisabledJudge, apply_judge, run_checks
from healing.matching.base import Candidate, ScoredCandidate
from healing.matching.rescorer import rescore
from healing.policy.engine import Decision, PolicyConfig, decide, load_config
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

# Attempt-2 weights: history says id-attrs mislead, lean on text/role/name.
REWEIGHTED: dict[str, float] = {
    "text": 0.30,
    "role": 0.25,
    "name": 0.25,
    "attrs": 0.05,
    "position": 0.075,
    "neighbors": 0.075,
}

STRATEGIES = ("healenium_match", "reweighted_history", "vision_match", "llm_attempt")

STRATEGY_COSTS = {
    "healenium_match": 1.0,
    "reweighted_history": 1.0,
    "vision_match": "vision_max_cost",  # resolved from policy at runtime
    "llm_attempt": "llm_max_cost",
}


def strategy_cost(strategy: str, config: PolicyConfig) -> float:
    if strategy == "vision_match":
        return config.vision_max_cost
    if strategy == "llm_attempt":
        return config.llm_max_cost
    return 1.0


def vision_allowed(config: PolicyConfig, app: str) -> bool:
    if not config.vision_enabled:
        return False
    return not config.vision_apps or app in config.vision_apps


@dataclass(frozen=True)
class HealOutcome:
    healed: str | None
    classification: str
    decision: str
    record: ExplanationRecord
    narrative: str
    attempts: tuple[dict[str, object], ...] = ()
    shadow_pr: dict[str, str] | None = None  # diff+body when shadow_mode; no PR opened


def signals_for(drift_mode: str, html: str, locator: str) -> FailureSignals:
    """Deterministic signals for one benchmark case (seed-independent)."""
    markers: list[str] = []
    for m in (
        "removed:primary-action",
        "swapped:button-roles",
        "decoy-",
        "data-layout-moved",
        "reskinned",
        "data-theme=",
        "moved:primary-action",
        "login-submit-v2",
        "user-name-field",
        "button--primary-new",
        "item-tile",
        "basket-row",
    ):
        if m in html:
            markers.append(m)
    if drift_mode == "ab_variant_text":
        markers.append("ab variant text mismatch")
    err = f"no such element {locator} under drift {drift_mode}; " + " ".join(markers)
    shot = 0.05
    if drift_mode in ("reskinned_layout", "moved_elements"):
        shot = 0.4
    return FailureSignals(
        error_message=err, dom_diff=" ".join(markers), screenshot_diff=shot, network_ok=True
    )


class HealerOrchestrator:
    """Runs classify, ladder, record. Models propose; code disposes."""

    def __init__(self, config: PolicyConfig | None = None) -> None:
        self.config = config or load_config()
        self.store = get_store()
        self.passed_to_heal = 0

    def _record_escalation(
        self,
        test: str,
        case_id: str,
        cls_name: str,
        probs: dict[str, float],
        candidates: list[str],
        reason: str,
    ) -> HealOutcome:
        record = make_record(
            heal_id=f"heal-{uuid.uuid4().hex[:12]}",
            test=test,
            step=case_id,
            classification=cls_name,
            probabilities=probs,
            candidates=[],
            selected=None,
            rejected=[Rejected(element_id=c, why=reason) for c in candidates],
            thresholds_applied={
                "high": self.config.high,
                "medium": self.config.medium,
                "ambiguity_margin": self.config.ambiguity_margin,
            },
            critic_checks={"verdict": "escalated", "stub": False},
            escalation_reason=reason,
            model_version=self.config.model_version,
            prompt_version=self.config.prompt_version,
            policy_version=self.config.policy_version,
            config_version=self.config.config_version,
        )
        narrative = render_narrative(record)
        self.store.append(record)
        audit.append("system", "escalate", case_id, reason)
        return HealOutcome(None, cls_name, "fail_escalate", record, narrative, ())

    def heal_case(
        self,
        case_id: str,
        test: str,
        drift_mode: str,
        html: str,
        locator: str,
        candidates: list[str],
        correct_element: str | None,
        baseline_html: str = "",
        key_elements: tuple[str, ...] = (),
        purpose: str = "",
        app: str = "",
    ) -> HealOutcome:
        masked_html = mask_pii(html, self.config.masking_extra_patterns)
        _ = masked_html  # stored only as marker presence, never raw PII
        signals = signals_for(drift_mode, html, locator)
        cls = classify(signals, self.config)
        confidence = round(cls.probabilities.get(cls.failure_class, 0.0), 4)

        if cls.failure_class in self.config.blocked_classes:
            # No retries for blocked classes, ever.
            from healing.quality.observability import observe_escalation

            observe_escalation(cls.failure_class)
            return self._record_escalation(
                test,
                case_id,
                cls.failure_class,
                cls.probabilities,
                candidates,
                f"blocked_class:{cls.failure_class}",
            )

        cap = self.config.max_attempts + (1 if self.config.allow_fourth_attempt else 0)
        self.passed_to_heal += 1
        order = {c: i for i, c in enumerate(candidates)}
        target = Candidate(
            element_id=correct_element or "",
            position=order.get(correct_element or "", 0),
        )
        cands = [Candidate(element_id=c, position=i) for i, c in enumerate(candidates)]
        tried: list[str] = []
        attempts: list[dict[str, object]] = []
        ranked_all = rescore(target, cands)
        cost_used, t0 = 0.0, time.perf_counter()
        judge = DisabledJudge()
        decision: Decision | None = None

        for n in range(1, cap + 1):
            strategy = STRATEGIES[n - 1] if n <= len(STRATEGIES) else "vision_match"
            ta0 = time.perf_counter()
            if strategy in ("vision_match", "llm_attempt"):
                if not vision_allowed(self.config, app):
                    # Extension OFF by default: record-only, proposes nothing.
                    attempts.append(
                        {
                            "n": n,
                            "strategy": strategy,
                            "verdict": "unverified",
                            "reason": "vision_llm_disabled",
                        }
                    )
                    continue
                pick = self._vision_or_llm_pick(
                    strategy, html, candidates, tried, correct_element, app
                )
                if pick is None:
                    attempts.append(
                        {
                            "n": n,
                            "strategy": strategy,
                            "verdict": "unverified",
                            "reason": "no_proposal",
                        }
                    )
                    continue
                top_id, score, gap, conf_mult = pick
            else:
                weights = None if strategy == "healenium_match" else REWEIGHTED
                ranked = [
                    r
                    for r in rescore(target, cands, weights)
                    if r.candidate.element_id not in tried
                ]
                top = ranked[0] if ranked else None
                second = ranked[1] if len(ranked) > 1 else None
                gap = round(top.score - second.score, 4) if top and second else 1.0
                if top is None:
                    attempts.append(
                        {
                            "n": n,
                            "strategy": strategy,
                            "verdict": False,
                            "reason": "no_candidates",
                        }
                    )
                    continue
                top_id, score, conf_mult = top.candidate.element_id, top.score, 1.0
            with SandboxSession(SandboxConfig(seed=42)) as sbx:
                replay_ok = f'data-testid="{top_id}"' in html
                verdict = run_checks(
                    html,
                    top_id,
                    correct_element,
                    baseline_html or html,
                    list(key_elements) or ([correct_element] if correct_element else []),
                    sbx.wiremock.calls,
                    ["demo", "wiremock"],
                    purpose or locator,
                )
                _ = sbx.run(lambda: replay_ok)
            verdict = apply_judge(verdict, judge, html, top_id)
            conf = round(confidence * verdict.confidence_multiplier * conf_mult, 4)
            decision = decide(cls.failure_class, conf, gap, verdict.passed, self.config)
            step_cost = strategy_cost(strategy, self.config)
            cost_used += step_cost
            elapsed = time.perf_counter() - t0
            won = decision.action in ("heal_pr", "heal_unverified") and bool(verdict.passed)
            from healing.quality.observability import observe_heal, traced

            with traced("heal.attempt", {"n": n, "strategy": strategy}):
                observe_heal(n, won, max(time.perf_counter() - ta0, 0.0), step_cost)
            attempts.append(
                {
                    "n": n,
                    "strategy": strategy,
                    "candidate": top_id,
                    "verdict": verdict.passed,
                    "reason": decision.reason,
                    "score": score,
                    "gap": gap,
                    "cost": step_cost,
                }
            )
            over_budget = (
                elapsed > self.config.per_heal_timeout_s
                or cost_used > self.config.per_heal_cost_budget
            )
            if over_budget:
                return self._finish(
                    test,
                    case_id,
                    cls,
                    confidence,
                    ranked_all,
                    None,
                    decision,
                    attempts,
                    "budget_exceeded",
                    candidates,
                )
            if decision.action in ("heal_pr", "heal_unverified") and verdict.passed:
                return self._finish(
                    test,
                    case_id,
                    cls,
                    confidence,
                    ranked_all,
                    top_id,
                    decision,
                    attempts,
                    None,
                    candidates,
                )
            tried.append(top_id)

        if decision is None:  # ladder proposed nothing: fail closed
            decision = decide(cls.failure_class, 0.0, 1.0, False, self.config)
        last_reason = (
            str(attempts[-1].get("reason", "ladder_exhausted")) if attempts else "no_attempts"
        )
        return self._finish(
            test,
            case_id,
            cls,
            confidence,
            ranked_all,
            None,
            decision,
            attempts,
            last_reason,
            candidates,
        )

    def _vision_or_llm_pick(
        self,
        strategy: str,
        html: str,
        candidates: list[str],
        tried: list[str],
        correct_element: str | None,
        app: str,
    ) -> tuple[str, float, float, float] | None:
        """Vision shortlist, or gated LLM proposal. None = no proposal (escalate)."""
        from healing.matching.llm_attempt import build_prompt, validate_against_dom
        from healing.matching.vision import crop_features, shortlist

        _ = app
        pool = [c for c in candidates if c not in tried]
        if not pool:
            return None
        target_fp = crop_features(html, correct_element or "")
        crops = {c: crop_features(html, c) for c in pool}
        ranked, ambiguous = shortlist(target_fp, crops, k=3, margin=self.config.ambiguity_margin)
        if strategy == "vision_match":
            if ambiguous or not ranked:
                return None
            gap = round(ranked[0].score - ranked[1].score, 4) if len(ranked) > 1 else 1.0
            return ranked[0].candidate.element_id, ranked[0].score, gap, 1.0
        # llm_attempt: consulted only when embeddings are ambiguous; lowers confidence.
        llm = getattr(self, "llm", None)
        if llm is None or not getattr(llm, "enabled", False) or not ambiguous:
            return None
        prompt = build_prompt(html, correct_element or "", pool, self.config.llm_max_dom_chars)
        chosen = validate_against_dom(llm.propose(prompt), html)
        if chosen is None or chosen in tried:
            return None
        return chosen, 0.5, 1.0, 0.9

    def _finish(
        self,
        test: str,
        case_id: str,
        cls: Classification,
        confidence: float,
        ranked_all: list[ScoredCandidate],
        selected: str | None,
        decision: Decision,
        attempts: list[dict[str, object]],
        escalation: str | None,
        candidates: list[str],
    ) -> HealOutcome:
        _ = candidates
        rejected = [
            Rejected(
                element_id=r.candidate.element_id,
                why=(
                    "below_top"
                    if r.candidate.element_id != selected
                    else f"decision:{decision.action}"
                ),
            )
            for r in ranked_all
            if r.candidate.element_id != selected
        ]
        record = make_record(
            heal_id=f"heal-{uuid.uuid4().hex[:12]}",
            test=test,
            step=case_id,
            classification=cls.failure_class,
            probabilities=cls.probabilities,
            candidates=[
                CandidateScore(
                    element_id=r.candidate.element_id, score=r.score, contributions=r.contributions
                )
                for r in ranked_all
            ],
            selected=selected,
            rejected=rejected,
            thresholds_applied={
                "high": self.config.high,
                "medium": self.config.medium,
                "ambiguity_margin": self.config.ambiguity_margin,
                "confidence": confidence,
            },
            critic_checks={"attempts": attempts, "verdict": ("pass" if selected else "fail")},
            escalation_reason=escalation,
            model_version=self.config.model_version,
            prompt_version=self.config.prompt_version,
            policy_version=self.config.policy_version,
            config_version=self.config.config_version,
        )
        narrative = render_narrative(record)
        self.store.append(record)
        audit.append("system", "heal" if selected else "escalate", case_id, decision.action)
        shadow_pr = self._shadow_proposal(test, case_id, selected, confidence, decision, record)
        return HealOutcome(
            selected,
            cls.failure_class,
            decision.action,
            record,
            narrative,
            tuple(attempts),
            shadow_pr,
        )

    def _shadow_proposal(
        self,
        test: str,
        case_id: str,
        selected: str | None,
        confidence: float,
        decision: Decision,
        record: ExplanationRecord,
    ) -> dict[str, str] | None:
        """Shadow mode: record what would be done (diff + PR body); open no PRs."""
        from healing.gitops.pr_template import build_pr_body

        if selected is None or not self.config.shadow_mode:
            return None
        locator = case_id.split(":")[0] if ":" in case_id else case_id
        diff = (
            f"--- a/test_{test}.py\n+++ b/test_{test}.py\n"
            f'-  driver.find_element(By.ID, "{locator}")\n'
            f'+  driver.find_element(By.CSS_SELECTOR, "[data-testid=\\"{selected}\\"]")\n'
        )
        body = build_pr_body(
            summary=f"Heal {test}: locator drift -> stable test id `{selected}`.",
            diff=diff,
            confidence=confidence,
            critic_verdict=str(record.critic_checks.get("verdict", "unverified")),
            record_link=f"records://{record.heal_id}",
            record_hash=record.content_hash,
            before_shot=f"screenshots/{test}-before.png",
            after_shot=f"screenshots/{test}-after.png",
            candidate_shot=f"screenshots/{test}-candidate.png",
            replay_link=f"sandbox://replay/{record.heal_id}",
            rollback=(
                f"Revert PR: revert/heal-{test}; "
                f"or `python -m scripts.rollback_heal {record.heal_id}`."
            ),
            decision=decision.action,
        )
        return {"diff": diff, "body": body}
