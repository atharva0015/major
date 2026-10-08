"""Rules-based classifier: error message, DOM diff, screenshot delta, net status.

Pure deterministic rules; weights and priors come from policy.yaml.
Genuine regressions, environment faults, and contract changes must never
reach the heal engine (the orchestrator gates on the returned class).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from healing.policy.engine import PolicyConfig, load_config

CLASSES = (
    "locator_drift",
    "data_issue",
    "timing_issue",
    "environment_issue",
    "genuine_regression",
    "contract_change",
)


@dataclass(frozen=True)
class FailureSignals:
    error_message: str = ""
    dom_diff: str = ""
    screenshot_diff: float = 0.0
    network_ok: bool = True


@dataclass(frozen=True)
class Classification:
    failure_class: str
    probabilities: dict[str, float] = field(default_factory=dict)
    fired_rules: tuple[str, ...] = ()


def _hits(text: str, *needles: str) -> bool:
    low = text.lower()
    return any(n.lower() in low for n in needles)


def classify(signals: FailureSignals, config: PolicyConfig | None = None) -> Classification:
    cfg = config or load_config()
    raw = cfg.raw if isinstance(cfg.raw, dict) else {}
    raw_weights = raw.get("rule_weights", {}) or {}
    raw_priors = raw.get("class_priors", {}) or {}
    if not isinstance(raw_weights, dict) or not isinstance(raw_priors, dict):
        raw_weights, raw_priors = {}, {}
    weights = {k: float(raw_weights.get(k, 0.8)) for k in raw_weights}
    priors = {c: float(raw_priors.get(c, 0.0)) for c in CLASSES}

    err = signals.error_message or ""
    dom = signals.dom_diff or ""
    fired: list[tuple[str, str]] = []  # (rule, class)

    if _hits(
        err, "openapi", "schema mismatch", "contract", "version-mismatch", "breaking api change"
    ) or _hits(dom, "schema mismatch", "contract"):
        fired.append(("contract_marker", "contract_change"))
    if (not signals.network_ok) or _hits(
        err,
        "timeout",
        "timed out",
        "dns",
        "econn",
        "connection refused",
        "502",
        "503",
        "504",
        "network unreachable",
    ):
        fired.append(("network_fault", "environment_issue"))
    if _hits(dom, "removed:primary-action") or _hits(
        err, "no such element and no candidate", "element removed"
    ):
        fired.append(("removed_marker", "genuine_regression"))
    if _hits(dom, "swapped:button-roles"):
        fired.append(("swapped_marker", "genuine_regression"))
    if _hits(dom, "decoy-", "duplicate") or _hits(
        err, "multiple matching elements", "ambiguous locator"
    ):
        fired.append(("decoy_marker", "environment_issue"))
    if _hits(
        dom,
        "login-submit-v2",
        "user-name-field",
        "button--primary-new",
        "item-tile",
        "basket-row",
        "data-layout-moved",
        "reskinned",
        "moved:primary-action",
        "data-theme=",
    ) or _hits(err, "no such element", "stale element", "locator"):
        fired.append(("locator_marker", "locator_drift"))
    if _hits(dom, "log in", "purchase", "continue to checkout") or _hits(
        err, "text mismatch", "ab variant"
    ):
        fired.append(("text_only_change", "locator_drift"))

    scores = dict(priors)
    for rule, cls in fired:
        scores[cls] = scores.get(cls, 0.0) + weights.get(rule, 0.8)

    if not fired:
        # Unknown: fail closed toward environment_issue at low confidence.
        scores["environment_issue"] = scores.get("environment_issue", 0.0) + 0.3
        fired.append(("unknown_fallback", "environment_issue"))

    total = sum(scores.values()) or 1.0
    probs = {c: scores.get(c, 0.0) / total for c in CLASSES}
    rounded = {c: round(v, 4) for c, v in probs.items()}
    # Correct rounding drift so probabilities sum to exactly 1.0.
    drift = round(1.0 - sum(rounded.values()), 4)
    if drift:
        top = max(rounded, key=lambda c: rounded[c])
        rounded[top] = round(rounded[top] + drift, 4)
    probs = rounded
    # Severity order breaks ties deterministically (fail closed first).
    order = (
        "contract_change",
        "genuine_regression",
        "environment_issue",
        "locator_drift",
        "timing_issue",
        "data_issue",
    )
    best = max(order, key=lambda c: (probs[c], -order.index(c)))
    return Classification(best, probs, tuple(r for r, _ in fired))
