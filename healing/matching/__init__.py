"""Matching: Healenium-based locator matching (Apache 2.0, see NOTICE)."""

from healing.matching.base import Candidate, Matcher, ScoredCandidate
from healing.matching.healenium_adapter import HealeniumAdapter
from healing.matching.llm_attempt import (
    DisabledLlm,
    LlmAttempt,
    LlmProposal,
    SelfHostedLlm,
    build_prompt,
    parse_proposal,
    validate_against_dom,
)
from healing.matching.rescorer import WEIGHTS, rescore
from healing.matching.vision import (
    SelfHostedEmbedding,
    cosine,
    crop_features,
    shortlist,
)

__all__: list[str] = [
    "Candidate",
    "DisabledLlm",
    "HealeniumAdapter",
    "LlmAttempt",
    "LlmProposal",
    "Matcher",
    "ScoredCandidate",
    "SelfHostedEmbedding",
    "SelfHostedLlm",
    "WEIGHTS",
    "build_prompt",
    "cosine",
    "crop_features",
    "parse_proposal",
    "rescore",
    "shortlist",
    "validate_against_dom",
]
