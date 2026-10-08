"""Locked golden set: known-correct heals; CI fails on regression.

The set is generated from a reviewed benchmark run and hash-pinned.
Changing expectations requires editing golden.json, which CI reviews.
Limits come from policy.yaml quality_limits (never loosened to pass).
"""

from __future__ import annotations

import hashlib
import json
import os

GOLDEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden.json")


def load_golden(path: str | None = None) -> dict[str, object]:
    with open(path or GOLDEN_PATH, encoding="utf-8") as f:
        data: dict[str, object] = json.load(f)
    payload = {k: v for k, v in data.items() if k != "sha256"}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    if digest != data.get("sha256"):
        raise ValueError("golden.json hash mismatch: expectations were edited without re-pinning")
    return dict(data)


def pin_golden(cases: list[dict[str, object]], path: str | None = None) -> None:
    payload: dict[str, object] = {"cases": cases}
    payload["sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    with open(path or GOLDEN_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
