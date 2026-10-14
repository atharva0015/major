# License decision (no license specified anywhere — LICENSE left untouched)

Evidence: `LICENSE` is a placeholder TODO, `pyproject.toml` declares
`license = { text = "TBD" }`, and no ADR or doc names a project license.
Per instruction, this file lists options instead of choosing. A human owner
must decide; swapping the text into `LICENSE` + `pyproject.toml` is a
one-commit follow-up.

## Constraints from the repo (MEASURED, from files on disk)

- Healenium is reused under **Apache-2.0** (`THIRD_PARTY_NOTICES.md`,
  `NOTICE`, ADR-005). Any choice must be Apache-2.0-compatible.
- Selenium Grid images are Apache-2.0. No GPL/copyleft dependencies are
  vendored; the SBOM license scan enforces an allowlist
  (`MIT, Apache-2.0, BSD, ISC, PSF`).
- The project aspires to commercial SaaS use (alerting, GitHub App
  delivery), so copyleft licenses would endanger adoption.

## Options

| License | Fits constraints | Notes for the decider |
|---|---|---|
| **MIT** (recommended) | Yes | Shortest, most permissive; pairs cleanly with Apache-2.0 Healenium reuse; standard for test tooling |
| **Apache-2.0** | Yes | Matches Healenium exactly; adds explicit patent grant; slightly longer text |
| **BSD-3-Clause** | Yes | Equivalent permissiveness; less common for new Python projects |
| ~~GPL/AGPL~~ | No | Rejected: copyleft conflicts with SaaS use and the SBOM allowlist |

## What the decision unlocks

Until a human picks: `LICENSE` stays a placeholder, `pyproject.toml`
stays `TBD`, and the package is undistributable. Nothing else is blocked.
