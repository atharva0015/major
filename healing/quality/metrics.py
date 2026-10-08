"""Metrics: heal accuracy, false-heal/escalation rates, cost, latency."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RunResult:
    case_id: str
    should_heal: bool
    healed: bool
    correct: bool
    escalated: bool
    cost: float = 0.0
    latency_ms: float = 0.0


@dataclass(frozen=True)
class HealMetrics:
    total: int
    heal_accuracy: float
    false_heal_rate: float
    escalation_rate: float
    correct_escalation_rate: float
    cost_per_heal: float
    latency_per_heal_ms: float


def compute_metrics(results: list[RunResult]) -> HealMetrics:
    total = len(results)
    if total == 0:
        return HealMetrics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    should_heal = [r for r in results if r.should_heal]
    should_not = [r for r in results if not r.should_heal]
    healed = [r for r in results if r.healed]
    correct_heals = [r for r in should_heal if r.healed and r.correct]
    wrong_heals = [r for r in healed if not r.correct]
    escalated = [r for r in results if r.escalated]
    correct_esc = [r for r in should_not if r.escalated and not r.healed]

    heal_accuracy = len(correct_heals) / len(should_heal) if should_heal else 0.0
    false_heal_rate = len(wrong_heals) / len(healed) if healed else 0.0
    escalation_rate = len(escalated) / total
    correct_esc_rate = len(correct_esc) / len(should_not) if should_not else 0.0
    cost_per_heal = sum(r.cost for r in healed) / len(healed) if healed else 0.0
    latency = sum(r.latency_ms for r in healed) / len(healed) if healed else 0.0
    return HealMetrics(
        total,
        heal_accuracy,
        false_heal_rate,
        escalation_rate,
        correct_esc_rate,
        cost_per_heal,
        latency,
    )


def to_json(m: HealMetrics) -> str:
    return json.dumps(asdict(m), indent=2, sort_keys=True)


def to_markdown(m: HealMetrics, title: str = "Baseline report") -> str:
    return (
        f"# {title}\n\n"
        f"- total: {m.total}\n"
        f"- heal_accuracy: {m.heal_accuracy:.3f}\n"
        f"- false_heal_rate: {m.false_heal_rate:.3f}\n"
        f"- escalation_rate: {m.escalation_rate:.3f}\n"
        f"- correct_escalation_rate: {m.correct_escalation_rate:.3f}\n"
        f"- cost_per_heal: {m.cost_per_heal:.3f}\n"
        f"- latency_per_heal_ms: {m.latency_per_heal_ms:.3f}\n"
    )


def write_report(m: HealMetrics, path: str, title: str = "Baseline report") -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(to_markdown(m, title))
