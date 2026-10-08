"""Autonomy guard: downgrade L3->L2 on quality breach (runtime-only).

Never rewrites policy.yaml: the downgrade is effective for the running
process and recorded in the returned alert payload; a human applies the
config change. Limits come from policy.yaml quality_limits.
"""

from __future__ import annotations

from dataclasses import dataclass

from healing.policy.engine import PolicyConfig, load_config


@dataclass(frozen=True)
class GuardVerdict:
    effective_level: str
    downgraded: bool
    reasons: tuple[str, ...] = ()
    alert: dict[str, object] | None = None


def evaluate(
    false_heal_rate: float, calibration_ece: float, config: PolicyConfig | None = None
) -> GuardVerdict:
    cfg = config or load_config()
    reasons: list[str] = []
    if false_heal_rate > cfg.max_false_heal_rate:
        reasons.append(f"false_heal_rate {false_heal_rate} > {cfg.max_false_heal_rate}")
    if calibration_ece > cfg.max_calibration_ece:
        reasons.append(f"calibration_ece {calibration_ece} > {cfg.max_calibration_ece}")
    if not reasons or cfg.autonomy_level not in ("L3", "L4"):
        return GuardVerdict(cfg.autonomy_level, False, tuple(reasons))
    return GuardVerdict(
        "L2",
        True,
        tuple(reasons),
        {
            "severity": "high",
            "owners": "healing-owners",
            "text": f"Autonomy downgraded {cfg.autonomy_level}->L2: " + "; ".join(reasons),
            "ack_sla_s": cfg.ack_sla_s,
        },
    )
