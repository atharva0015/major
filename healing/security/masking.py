"""PII/secret masking for DOM, logs, payloads, screenshot metadata."""

from __future__ import annotations

import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d .()-]{7,}\d)(?!\d)")
CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
TOKEN_RE = re.compile(
    r"(?i)(bearer\s+[A-Za-z0-9._~-]+|api[_-]?key\s*[:=]\s*[A-Za-z0-9._~-]+"
    r"|token\s*[:=]\s*[A-Za-z0-9._~-]+|sk-[A-Za-z0-9]+)"
)


def _compile_extra(patterns: list[str] | tuple[str, ...]) -> list[re.Pattern[str]]:
    return [re.compile(p) for p in patterns]


def mask_pii(text: str, extra_patterns: list[str] | tuple[str, ...] | None = None) -> str:
    """Mask emails, phones, card numbers, tokens, plus configured patterns."""
    out = EMAIL_RE.sub("[email]", text)
    out = CARD_RE.sub("[card]", out)
    out = TOKEN_RE.sub("[token]", out)
    out = PHONE_RE.sub("[phone]", out)
    for pat in _compile_extra(list(extra_patterns or ())):
        out = pat.sub("[masked]", out)
    return out


def mask_mapping(
    payload: dict[str, object],
    extra_patterns: list[str] | tuple[str, ...] | None = None,
) -> dict[str, object]:
    return {
        k: (mask_pii(str(v), extra_patterns) if isinstance(v, str) else v)
        for k, v in payload.items()
    }
