"""SBOM generation and license allowlist enforcement (stdlib only).

`python -m scripts.sbom` writes `sbom.json` for the installed distributions.
`python -m scripts.sbom --check` additionally fails closed when a component
has an unknown or disallowed license.

The allowlist was approved by the project owner on 2026-11-06: permissive
licenses plus MPL-2.0 and LGPL-3.0 for the existing transitive dependencies.
See `docs/LICENSE_DECISION.md` and `docs/COMPLIANCE.md`.
"""

from __future__ import annotations

import json
import re
import sys
from importlib.metadata import Distribution, distributions

OUT = "sbom.json"

ALLOWLIST = (
    "MIT",
    "MIT-0",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "PSF-2.0",
    "MPL-2.0",
    "LGPL-3.0-only",
    "LGPL-3.0-or-later",
)

_ALIASES = {
    "MIT": "MIT",
    "MIT LICENSE": "MIT",
    "MIT-0": "MIT-0",
    "APACHE": "Apache-2.0",
    "APACHE 2.0": "Apache-2.0",
    "APACHE-2.0": "Apache-2.0",
    "APACHE SOFTWARE LICENSE": "Apache-2.0",
    "BSD": "BSD-3-Clause",
    "BSD LICENSE": "BSD-3-Clause",
    "BSD-2-CLAUSE": "BSD-2-Clause",
    "BSD-3-CLAUSE": "BSD-3-Clause",
    "ISC": "ISC",
    "ISC LICENSE": "ISC",
    "PSF": "PSF-2.0",
    "PSF-2.0": "PSF-2.0",
    "PYTHON SOFTWARE FOUNDATION LICENSE": "PSF-2.0",
    "MPL": "MPL-2.0",
    "MPL-2.0": "MPL-2.0",
    "MOZILLA PUBLIC LICENSE 2.0": "MPL-2.0",
    "MOZILLA PUBLIC LICENSE 2.0 (MPL 2.0)": "MPL-2.0",
    "LGPL": "LGPL-3.0-only",
    "LGPL-3.0": "LGPL-3.0-only",
    "LGPL-3.0-ONLY": "LGPL-3.0-only",
    "LGPL-3.0-OR-LATER": "LGPL-3.0-or-later",
    "GNU LIBRARY OR LESSER GENERAL PUBLIC LICENSE": "LGPL-3.0-only",
    "GNU LIBRARY OR LESSER GENERAL PUBLIC LICENSE (LGPL)": "LGPL-3.0-only",
}

_CLAUSE = re.compile(r"\s+(AND|OR)\s+", re.IGNORECASE)
_UNKNOWN = {"", "NONE", "NOASSERTION", "TBD", "UNKNOWN"}

_LONG_TEXT_KEYWORDS = (
    (re.compile(r"\bAGPL\b|\bAFFERO\b", re.IGNORECASE), "AGPL-3.0"),
    (re.compile(r"\bLGPL\b|\bLESSER GENERAL PUBLIC\b", re.IGNORECASE), "LGPL-3.0-only"),
    (re.compile(r"\bMPL\b|\bMOZILLA PUBLIC\b", re.IGNORECASE), "MPL-2.0"),
    (re.compile(r"\bAPACHE\b", re.IGNORECASE), "Apache-2.0"),
    (re.compile(r"\bPSF\b|PYTHON SOFTWARE FOUNDATION", re.IGNORECASE), "PSF-2.0"),
    (re.compile(r"\bMIT\b", re.IGNORECASE), "MIT"),
    (re.compile(r"\bBSD\b", re.IGNORECASE), "BSD-3-Clause"),
    (re.compile(r"\bISC\b", re.IGNORECASE), "ISC"),
    (re.compile(r"\bGPL\b|\bGENERAL PUBLIC LICENSE\b", re.IGNORECASE), "GPL-3.0"),
)


def _token(value: str) -> str:
    """Normalize one short license name to a canonical token."""
    token = " ".join(value.replace("(", " ").replace(")", " ").split()).strip(" ,")
    upper = token.upper()
    if upper in _UNKNOWN:
        return "UNKNOWN"
    if upper in _ALIASES:
        return _ALIASES[upper]
    if "/" in upper and " OR " not in upper:
        parts = [part.strip() for part in upper.split("/") if part.strip()]
        return " OR ".join(_token(part) for part in parts)
    return upper


def normalize_license(value: object) -> str:
    """Return a canonical SPDX-style expression, or `UNKNOWN`.

    Handles PEP 639 `License-Expression`, short `License` fields, license
    classifiers, and long license texts that name several licenses.
    """
    text = " ".join(str(value).split())
    if text.upper() in _UNKNOWN:
        return "UNKNOWN"

    # Long free-text license fields often contain the full text of every
    # license that applies. Treat all named licenses as an AND expression.
    if len(text) > 200:
        found = {license_id for pattern, license_id in _LONG_TEXT_KEYWORDS if pattern.search(text)}
        if not found:
            return "UNKNOWN"
        if "LGPL-3.0-only" in found or "AGPL-3.0" in found:
            found.discard("GPL-3.0")
        return " AND ".join(sorted(found))

    # Fold common multi-word names before splitting on AND/OR. Single-word
    # aliases are handled by `_token` so they cannot match inside an
    # already-normalized SPDX token (for example MIT inside MIT-0).
    folded = text
    multi_word = (alias for alias in _ALIASES if " " in alias)
    for alias in sorted(multi_word, key=len, reverse=True):
        folded = re.sub(rf"\b{re.escape(alias)}\b", _ALIASES[alias], folded, flags=re.IGNORECASE)
    folded = re.sub(r"\([^)]*\)", " ", folded)

    parts = _CLAUSE.split(folded)
    tokens = [part for part in parts if part.upper() not in {"AND", "OR"}]
    operators = [part.upper() for part in parts if part.upper() in {"AND", "OR"}]
    if not tokens:
        return "UNKNOWN"
    normalized = [_token(token) for token in tokens]
    if not operators:
        return normalized[0]
    if len(operators) != len(normalized) - 1:
        return "UNKNOWN"
    result = normalized[0]
    for operator, token in zip(operators, normalized[1:], strict=True):
        result = f"{result} {operator} {token}"
    return result


def _allowed_and(expression: str, allowed: set[str]) -> bool:
    return all(part in allowed for part in expression.split(" AND "))


def license_allowed(expression: str, allowlist: tuple[str, ...] = ALLOWLIST) -> bool:
    """An OR expression is allowed when one branch is allowed; AND needs all."""
    allowed = set(allowlist)
    return any(_allowed_and(part, allowed) for part in expression.split(" OR "))


def _license_for(dist: Distribution) -> tuple[str, str]:
    expression = dist.metadata.get("License-Expression")
    if expression:
        return expression, "License-Expression"
    license_field = dist.metadata.get("License")
    if license_field and license_field.strip().upper() not in _UNKNOWN:
        return license_field, "License"
    classifiers = [
        item
        for item in (dist.metadata.get_all("Classifier") or [])
        if item.startswith("License ::")
    ]
    if classifiers:
        classifier = classifiers[0].split("::")[-1].strip()
        classifier = re.sub(r"\([^)]*\)", "", classifier).strip()
        return classifier, "Classifier"
    return "UNKNOWN", "missing"


def build_sbom() -> dict[str, object]:
    components = []
    seen: set[tuple[str, str]] = set()
    for dist in distributions():
        name = str(dist.metadata.get("Name", "unknown"))
        version = str(dist.version)
        key = (name.lower(), version)
        if key in seen:
            continue
        seen.add(key)
        raw, source = _license_for(dist)
        components.append(
            {
                "name": name,
                "version": dist.version,
                "license": normalize_license(raw),
                "license_source": source,
            }
        )
    components.sort(key=lambda component: str(component["name"]).lower())
    return {"sbom_format": "healing-sbom-0.2.0", "components": components}


def check_components(
    components: list[dict[str, object]], allowlist: tuple[str, ...] = ALLOWLIST
) -> list[dict[str, object]]:
    """Return components whose license is unknown or outside the allowlist."""
    violations = []
    for component in components:
        expression = str(component.get("license", "UNKNOWN"))
        if not license_allowed(expression, allowlist):
            violations.append(component)
    return violations


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    sbom = build_sbom()
    components = sbom["components"]
    assert isinstance(components, list)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(sbom, handle, indent=2, sort_keys=True)

    violations = check_components(components)
    print(f"wrote {OUT} with {len(components)} components")
    print(
        f"license allowlist: {len(components) - len(violations)} allowed, "
        f"{len(violations)} disallowed"
    )
    for component in violations:
        print(
            f"DISALLOWED {component['name']} {component['version']}: "
            f"{component['license']} ({component.get('license_source', 'unknown')})"
        )
    if "--check" in args:
        if violations:
            print("result: FAIL")
            raise SystemExit(1)
        print("result: PASS")


if __name__ == "__main__":
    main()
