"""Replay command: reproduce a past heal from its stored record."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from healing.quality.registry import replay_heal
from healing.xai.records import ExplanationRecord


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m scripts.replay_heal <heal-id> [--html PATH] [--candidates a,b]")
        raise SystemExit(2)
    heal_id = sys.argv[1]
    html, cands = "", []
    if "--html" in sys.argv:
        with open(sys.argv[sys.argv.index("--html") + 1], encoding="utf-8") as f:
            html = f.read()
    if "--candidates" in sys.argv:
        cands = sys.argv[sys.argv.index("--candidates") + 1].split(",")
    from healing.xai.records import JsonlRecordStore

    found = [r for r in JsonlRecordStore().list() if r.heal_id == heal_id]
    if not found:
        print(f"no record for {heal_id}")
        raise SystemExit(1)
    rec: ExplanationRecord = found[-1]
    out = replay_heal(rec, html, cands)
    print(json.dumps(out, indent=2, sort_keys=True))
    if not out["matches_record"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
