"""Multimodal LLM attempt: masked, size-limited, JSON-validated, DOM-gated.

Consulted only when embeddings are ambiguous. Like LlmJudge, it may only
lower confidence or abstain -- never revive a Critic failure. Disabled by
default; self-hosted endpoint via configuration. All payloads masked.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import httpx

LLM_ATTEMPT_VERSION = "llm-attempt-0.1.0"


@dataclass(frozen=True)
class LlmProposal:
    selector: str
    evidence: tuple[str, ...] = ()
    abstained: bool = False


class LlmAttempt:
    enabled: bool = False
    version: str = LLM_ATTEMPT_VERSION

    def propose(self, prompt: str) -> LlmProposal:
        _ = prompt
        return LlmProposal("", (), abstained=True)


class DisabledLlm(LlmAttempt):
    enabled = False


class SelfHostedLlm(LlmAttempt):
    enabled = True

    def __init__(
        self,
        url: str | None = None,
        timeout_s: float = 10.0,
        max_dom_chars: int = 2000,
    ) -> None:
        self.url = url or os.getenv("VISION_LLM_URL", "")
        self.timeout_s = timeout_s
        self.max_dom_chars = max_dom_chars

    def propose(self, prompt: str) -> LlmProposal:
        if not self.url:
            return LlmProposal("", (), abstained=True)
        try:
            r = httpx.post(self.url, json={"prompt": prompt}, timeout=self.timeout_s)
            if r.status_code != 200:
                return LlmProposal("", (), abstained=True)
            return parse_proposal(r.text)
        except Exception:
            return LlmProposal("", (), abstained=True)


def build_prompt(html: str, testid: str, candidates: list[str], max_dom_chars: int = 2000) -> str:
    """Masked, size-limited DOM slice plus crop descriptors. No raw PII."""
    from healing.security.masking import mask_pii

    masked = mask_pii(html)
    head = masked[:max_dom_chars]
    if len(masked) > max_dom_chars:
        head += f"\n<!-- truncated {len(masked) - max_dom_chars} chars -->"
    return (
        f"Failing element testid: {testid}\n"
        f"Candidates: {', '.join(candidates)}\n"
        f"DOM slice:\n{head}\n"
        'Reply with JSON only: {"selector": "<data-testid>", "evidence": ["..."]}.'
    )


def parse_proposal(text: str) -> LlmProposal:
    """Require structured JSON with selector plus evidence."""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return LlmProposal("", (), abstained=True)
    if not isinstance(data, dict):
        return LlmProposal("", (), abstained=True)
    selector = data.get("selector", "")
    evidence = data.get("evidence", [])
    if not isinstance(selector, str) or not selector:
        return LlmProposal("", (), abstained=True)
    if (
        not isinstance(evidence, list)
        or not evidence
        or not all(isinstance(e, str) and e for e in evidence)
    ):
        return LlmProposal("", (), abstained=True)
    return LlmProposal(selector, tuple(evidence), abstained=False)


def validate_against_dom(proposal: LlmProposal, html: str) -> str | None:
    """The selector must resolve in the real DOM before use. Else refuse."""
    if proposal.abstained:
        return None
    if f'data-testid="{proposal.selector}"' in html:
        return proposal.selector
    return None
