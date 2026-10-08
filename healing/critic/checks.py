"""Layered Critic: deterministic -> state -> network -> intent.

A sandbox pass alone never approves a heal; this verdict plus policy
decides. The pluggable LLM judge is disabled by default and may only
lower confidence, never override a failed deterministic check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

CRITIC_VERSION = "critic-0.1.0"


@dataclass(frozen=True)
class CriticVerdict:
    passed: bool | None  # None = unverified (stub path)
    failed_layer: str | None = None
    details: dict[str, object] = field(default_factory=dict)
    confidence_multiplier: float = 1.0


class LlmJudge(Protocol):
    enabled: bool

    def review(self, html: str, chosen: str) -> float:
        """Return a confidence multiplier in (0, 1]."""
        raise NotImplementedError


class DisabledJudge:
    enabled = False

    def review(self, html: str, chosen: str) -> float:
        _ = (html, chosen)
        return 1.0


def _tag_of(html: str, testid: str) -> str | None:
    idx = html.find(f'data-testid="{testid}"')
    if idx == -1:
        return None
    open_tag = html.rfind("<", 0, idx)
    space = html.find(" ", open_tag)
    end = html.find(">", open_tag)
    return html[open_tag + 1 : min(space if space != -1 else end, end)]


def check_deterministic(html: str, chosen: str) -> tuple[bool, str]:
    """Unique, visible, enabled, expected type, actionable without force."""
    if html.count(f'data-testid="{chosen}"') != 1:
        return False, "element_not_unique"
    tag = _tag_of(html, chosen)
    if tag is None:
        return False, "element_absent"
    snippet = html[
        max(0, html.find(f'data-testid="{chosen}"') - 200) : html.find(f'data-testid="{chosen}"')
    ]
    if "disabled" in snippet or 'aria-hidden="true"' in snippet or "display:none" in snippet:
        return False, "element_not_actionable"
    if tag not in ("button", "a", "input"):
        return False, f"unexpected_type:{tag}"
    return True, ""


def check_state(html: str, baseline_html: str, key_elements: list[str]) -> tuple[bool, str]:
    """Next page/URL/key elements match the recorded baseline."""
    missing = [k for k in key_elements if f'data-testid="{k}"' not in html]
    if missing:
        return False, f"state_mismatch:missing={missing}"
    extra_form = html.count("<form") != baseline_html.count("<form")
    if extra_form:
        return False, "state_mismatch:forms"
    return True, ""


def check_network(calls: list[str], expected_hosts: list[str]) -> tuple[bool, str]:
    """Expected requests/shapes only; no new errors or hosts."""
    for url in calls:
        if not any(h in url for h in expected_hosts):
            return False, f"unexpected_host:{url}"
        if "error" in url or "500" in url:
            return False, f"network_error:{url}"
    return True, ""


def check_intent(chosen: str, correct: str | None, purpose: str) -> tuple[bool, str]:
    """The step's recorded purpose still matches the chosen role/name."""
    if correct is None:
        return False, "no_correct_element"
    if chosen == correct:
        return True, ""
    # Same-purpose tokens share a stem (submit/add/checkout/buy); else mismatch.
    stems = ("submit", "add-cart", "checkout", "buy", "purchase")
    chosen_stem = next((s for s in stems if s in chosen), chosen)
    correct_stem = next((s for s in stems if s in correct), correct)
    if chosen_stem != correct_stem:
        return False, f"intent_mismatch:{purpose}:{chosen}!={correct}"
    return True, ""


def run_checks(
    html: str,
    chosen: str | None,
    correct: str | None,
    baseline_html: str,
    key_elements: list[str],
    network_calls: list[str],
    expected_hosts: list[str],
    purpose: str,
) -> CriticVerdict:
    if chosen is None:
        return CriticVerdict(False, "no_candidate", {"reason": "nothing_to_verify"})
    ok, why = check_deterministic(html, chosen)
    if not ok:
        return CriticVerdict(False, "deterministic", {"reason": why})
    ok, why = check_state(html, baseline_html, key_elements)
    if not ok:
        return CriticVerdict(False, "state", {"reason": why})
    ok, why = check_network(network_calls, expected_hosts)
    if not ok:
        return CriticVerdict(False, "network", {"reason": why})
    ok, why = check_intent(chosen, correct, purpose)
    if not ok:
        return CriticVerdict(False, "intent", {"reason": why})
    return CriticVerdict(True, None, {"layers": ["deterministic", "state", "network", "intent"]})


def apply_judge(
    verdict: CriticVerdict, judge: LlmJudge | None, html: str = "", chosen: str = ""
) -> CriticVerdict:
    """An enabled judge may only lower confidence, never revive a failure."""
    if judge is None or not judge.enabled:
        return verdict
    factor = max(0.0, min(1.0, judge.review(html, chosen)))
    if verdict.passed is False:
        # Failed deterministic (or any) layer stays failed.
        return verdict
    return CriticVerdict(
        verdict.passed,
        verdict.failed_layer,
        dict(verdict.details),
        verdict.confidence_multiplier * factor,
    )
