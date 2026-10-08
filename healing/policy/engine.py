"""Policy engine: deterministic gating from versioned config (plain code)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import yaml

POLICY_VERSION_FALLBACK = "policy-0.1.0"
VALID_LEVELS = ("L1", "L2", "L3", "L4")


@dataclass(frozen=True)
class PolicyConfig:
    policy_version: str = POLICY_VERSION_FALLBACK
    config_version: str = "config-0.1.0"
    autonomy_level: str = "L3"
    kill_switch: bool = False
    high: float = 0.8
    medium: float = 0.5
    ambiguity_margin: float = 0.1
    blocked_classes: tuple[str, ...] = (
        "genuine_regression",
        "environment_issue",
        "contract_change",
    )
    masking_extra_patterns: tuple[str, ...] = ()
    max_attempts: int = 3
    allow_fourth_attempt: bool = False
    per_heal_timeout_s: float = 30.0
    per_heal_cost_budget: float = 10.0
    ack_sla_s: int = 3600
    shadow_mode: bool = True
    watch_window_h: int = 24
    golden_min_accuracy: float = 1.0
    golden_max_false_heal_rate: float = 0.0
    max_false_heal_rate: float = 0.0
    max_calibration_ece: float = 0.15
    vision_enabled: bool = False
    vision_apps: tuple[str, ...] = ()
    vision_max_cost: float = 1.0
    llm_max_cost: float = 2.0
    llm_timeout_s: float = 10.0
    llm_max_dom_chars: int = 2000
    model_version: str = "rules-0.1.0"
    prompt_version: str = "n/a-template-0.1.0"
    raw: dict[str, object] = field(default_factory=dict, compare=False)


def default_config_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "policy.yaml")


def load_config(path: str | None = None) -> PolicyConfig:
    resolved: str = path or os.getenv("POLICY_PATH") or default_config_path()
    with open(resolved, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    thresholds = data.get("thresholds", {}) or {}
    level = str(data.get("autonomy_level", "L3"))
    if level not in VALID_LEVELS:
        level = "L3"
    blocked = tuple(str(c) for c in (data.get("blocked_classes") or ()))
    extra = tuple(str(p) for p in (data.get("masking_extra_patterns") or ()))
    severity = data.get("severity_routing", {}) or {}
    if not isinstance(severity, dict):
        severity = {}
    return PolicyConfig(
        policy_version=str(data.get("policy_version", POLICY_VERSION_FALLBACK)),
        config_version=str(data.get("config_version", "config-0.1.0")),
        autonomy_level=level,
        kill_switch=bool(data.get("kill_switch", False)),
        high=float(thresholds.get("high", 0.8)),
        medium=float(thresholds.get("medium", 0.5)),
        ambiguity_margin=float(data.get("ambiguity_margin", 0.1)),
        blocked_classes=blocked or ("genuine_regression", "environment_issue", "contract_change"),
        masking_extra_patterns=extra,
        max_attempts=max(1, int(data.get("max_attempts", 3))),
        allow_fourth_attempt=bool(data.get("allow_fourth_attempt", False)),
        per_heal_timeout_s=float(data.get("per_heal_timeout_s", 30.0)),
        per_heal_cost_budget=float(data.get("per_heal_cost_budget", 10.0)),
        ack_sla_s=int(data.get("ack_sla_s", 3600)),
        shadow_mode=bool(data.get("shadow_mode", True)),
        watch_window_h=int(data.get("watch_window_h", 24)),
        golden_min_accuracy=float(
            (data.get("quality_limits", {}) or {}).get("golden_min_accuracy", 1.0)
        ),
        golden_max_false_heal_rate=float(
            (data.get("quality_limits", {}) or {}).get("golden_max_false_heal_rate", 0.0)
        ),
        max_false_heal_rate=float(
            (data.get("quality_limits", {}) or {}).get("max_false_heal_rate", 0.0)
        ),
        max_calibration_ece=float(
            (data.get("quality_limits", {}) or {}).get("max_calibration_ece", 0.15)
        ),
        vision_enabled=bool((data.get("vision_llm", {}) or {}).get("enabled", False)),
        vision_apps=tuple(
            str(a) for a in ((data.get("vision_llm", {}) or {}).get("apps", []) or ())
        ),
        vision_max_cost=float((data.get("vision_llm", {}) or {}).get("vision_max_cost", 1.0)),
        llm_max_cost=float((data.get("vision_llm", {}) or {}).get("llm_max_cost", 2.0)),
        llm_timeout_s=float((data.get("vision_llm", {}) or {}).get("llm_timeout_s", 10.0)),
        llm_max_dom_chars=int((data.get("vision_llm", {}) or {}).get("llm_max_dom_chars", 2000)),
        model_version=str(data.get("model_version", "rules-0.1.0")),
        prompt_version=str(data.get("prompt_version", "n/a-template-0.1.0")),
        raw={k: v for k, v in data.items()},
    )


@dataclass(frozen=True)
class Decision:
    action: str  # heal_pr | heal_unverified | propose | fail_escalate
    reason: str
    confidence: float
    critic_pass: bool | None
    ambiguous: bool


def decide(
    failure_class: str,
    confidence: float,
    margin_gap: float,
    critic_pass: bool | None,
    config: PolicyConfig | None = None,
) -> Decision:
    """Decision table (deterministic). High + Critic pass -> heal+PR;
    medium (or unverified stub) -> heal marked unverified; low/Critic fail/
    ambiguity/blocked class/kill switch -> fail and escalate."""
    cfg = config or load_config()
    ambiguous = margin_gap < cfg.ambiguity_margin
    if cfg.kill_switch:
        return Decision("fail_escalate", "kill_switch_engaged", confidence, critic_pass, ambiguous)
    if failure_class in cfg.blocked_classes:
        return Decision(
            "fail_escalate", f"blocked_class:{failure_class}", confidence, critic_pass, ambiguous
        )
    if ambiguous:
        return Decision("fail_escalate", "ambiguous_candidates", confidence, critic_pass, True)
    if critic_pass is False:
        return Decision("fail_escalate", "critic_fail", confidence, critic_pass, ambiguous)
    if confidence >= cfg.high and critic_pass is True:
        action = "heal_pr" if cfg.autonomy_level in ("L3", "L4") else "propose"
        return Decision(action, "high_confidence_critic_pass", confidence, critic_pass, ambiguous)
    if confidence >= cfg.medium:
        # Medium confidence, or high with unverified (stub) Critic.
        action = "heal_unverified" if cfg.autonomy_level in ("L2", "L3", "L4") else "propose"
        return Decision(
            action, "medium_confidence_or_unverified", confidence, critic_pass, ambiguous
        )
    return Decision("fail_escalate", "low_confidence", confidence, critic_pass, ambiguous)
