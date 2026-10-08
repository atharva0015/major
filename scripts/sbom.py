"""SBOM generation from installed distribution metadata (stdlib only)."""

from __future__ import annotations

import json
import os
from importlib.metadata import distributions

OUT = os.path.join("sbom.json")
ALLOWLIST = ("MIT", "Apache-2.0", "BSD", "ISC", "PSF", "Apache Software License")


def build_sbom() -> dict[str, object]:
    components = []
    for dist in distributions():
        name = dist.metadata.get("Name", "unknown")
        components.append(
            {
                "name": name,
                "version": dist.version,
                "license": dist.metadata.get("License", "unknown"),
            }
        )
    components.sort(key=lambda c: str(c["name"]).lower())
    return {"sbom_format": "healing-sbom-0.1.0", "components": components}


def main() -> None:
    sbom = build_sbom()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2, sort_keys=True)
    print(f"wrote {OUT} with {len(sbom['components'])} components")


if __name__ == "__main__":
    main()
