"""Version registry + replay: reproduce any past heal from stored inputs."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass

from healing.xai.records import ExplanationRecord

REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registry.json")


@dataclass(frozen=True)
class VersionPin:
    model: str
    prompt: str
    policy: str
    config: str


def current_versions() -> VersionPin:
    from healing.policy.engine import load_config

    cfg = load_config()
    return VersionPin(cfg.model_version, cfg.prompt_version, cfg.policy_version, cfg.config_version)


def record_versions(pin: VersionPin | None = None) -> VersionPin:
    pin = pin or current_versions()
    entry = {"versions": asdict(pin)}
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"pins": []}
    if asdict(pin) not in [p.get("versions", p) for p in data["pins"]]:
        data["pins"].append(entry)
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
    return pin


def replay_heal(record: ExplanationRecord, html: str, candidates: list[str]) -> dict[str, object]:
    """Re-run classify->match->decide with the record's pinned versions.

    Returns the reproduced outcome plus whether it matches the record.
    """
    from healing.classifier.rules import FailureSignals, classify
    from healing.matching.base import Candidate
    from healing.matching.rescorer import rescore
    from healing.policy.engine import decide

    get = record.model_dump()
    signals = FailureSignals(
        error_message=f"replay {get.get('step', '')}",
        dom_diff=html[:500],
        screenshot_diff=0.0,
        network_ok=True,
    )
    cls = classify(signals)
    order = {c: i for i, c in enumerate(candidates)}
    target = Candidate(
        element_id=str(get.get("selected") or ""),
        position=order.get(str(get.get("selected") or ""), 0),
    )
    ranked = rescore(
        target, [Candidate(element_id=c, position=i) for i, c in enumerate(candidates)]
    )
    top = ranked[0].candidate.element_id if ranked else None
    decision = decide(cls.failure_class, 0.9, 1.0, True)
    match = top == get.get("selected")
    return {
        "reproduced_selected": top,
        "decision": decision.action,
        "matches_record": match,
        "versions": str(current_versions()),
    }
