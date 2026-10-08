"""Rollback a heal: open a revert PR (kill switch does not block rollbacks)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m scripts.rollback_heal <heal-id|branch> [--reason TEXT]")
        raise SystemExit(2)
    target = sys.argv[1]
    reason = "manual rollback"
    if "--reason" in sys.argv:
        reason = sys.argv[sys.argv.index("--reason") + 1]
    # Rollback stays available even under kill switch (it undoes, not heals).
    print(f"rollback prepared for {target}: revert PR would reference '{reason}'")
    print("dry-run: no PR opened (wire a GitHubClient to execute)")


if __name__ == "__main__":
    main()
