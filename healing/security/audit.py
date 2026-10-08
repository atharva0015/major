"""Append-only audit log for system, user, and chatbot actions."""

from __future__ import annotations

import hashlib
import json
import os
import time


def audit_path() -> str:
    return os.getenv("AUDIT_LOG", os.path.join("benchmark", "reports", "audit.log"))


def _chain_hash(prev: str, entry: str) -> str:
    return hashlib.sha256((prev + entry).encode("utf-8")).hexdigest()


def append(actor: str, action: str, target: str, result: str) -> dict[str, object]:
    """Append one entry; returns the entry (seq is monotonic, hash-chained)."""
    path = audit_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    prev, seq = "GENESIS", 0
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            lines = [ln for ln in f if ln.strip()]
        if lines:
            last = json.loads(lines[-1])
            prev, seq = str(last.get("hash", prev)), int(last.get("seq", 0))
    entry = {
        "seq": seq + 1,
        "ts": time.time(),
        "actor": actor,
        "action": action,
        "target": target,
        "result": result,
        "prev": prev,
    }
    entry["hash"] = _chain_hash(prev, json.dumps(entry, sort_keys=True))
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def read_all() -> list[dict[str, object]]:
    path = audit_path()
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(ln) for ln in f if ln.strip()]
