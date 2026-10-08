"""Template narrative from a record + automated consistency check (no LLM)."""

from __future__ import annotations

from healing.xai.records import ExplanationRecord


def render_narrative(record: ExplanationRecord) -> str:
    """Record first, narrative second: every claim below maps to a field."""
    lines = [
        f"Heal {record.heal_id} on test {record.test} step {record.step}.",
        f"Classification {record.classification} "
        f"(policy {record.policy_version}, config {record.config_version}).",
        f"Selected {record.selected} with thresholds {record.thresholds_applied}.",
        f"Critic {record.critic_checks}; escalation {record.escalation_reason}.",
        f"Versions model {record.model_version} prompt {record.prompt_version}.",
    ]
    return " ".join(lines)


def consistency_check(text: str, record: ExplanationRecord) -> dict[str, object]:
    """Every claim in the text must map to a record field value."""
    required = [
        record.heal_id,
        record.test,
        record.classification,
        str(record.policy_version),
        str(record.config_version),
        str(record.model_version),
        str(record.prompt_version),
        str(record.selected),
        str(record.escalation_reason),
    ]
    missing = [r for r in required if r and r not in text]
    for key, val in record.thresholds_applied.items():
        if str(key) not in text or str(val) not in text:
            missing.append(f"threshold:{key}={val}")
    return {"ok": not missing, "missing": missing}
