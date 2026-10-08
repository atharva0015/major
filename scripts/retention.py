"""Retention CLI: dry-run by default; --apply deletes."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from healing.security.retention import run


def main() -> None:
    reports = os.path.join("benchmark", "reports")
    result = run(reports, apply="--apply" in sys.argv)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
