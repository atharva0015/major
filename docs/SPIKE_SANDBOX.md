# Spike B — Sandbox feasibility (docs-only analysis)

## Goal

Replay a failed benchmark test isolated: Docker Compose project with
network egress denied except the demo app and a WireMock stub service.

## Proposed shape (not executed in this task)

- Separate compose project (`heal-sandbox`), `internal: true` network plus
  explicit allowlist links only to `demo:8001` and `wiremock:8080`.
- No host networking, no volume mounts from repo, read-only test bundle,
  artifact capture (HTML diff, healed locator, score) to a reports volume.
- WireMock stands in for any third-party HTTP the page touches.

## What worked

- Static analysis: demo pages are server-rendered strings, so replay is
  deterministic (seed 42) without a browser; harness already re-renders per
  drift mode. Compose `config` validates with pinned images.

## What did not (not run)

- No containers were started here (docs-only scope): Selenoid browser
  image pull, Chrome/driver download, and egress-deny firewall rules were
  not exercised; timing flakes under isolation remain unmeasured.

## Recommendation

**Isolated staging** over a full per-test sandbox: one long-lived
egress-restricted staging stack (demo + WireMock + Selenoid) serving all
replays, rather than a fresh sandbox per heal attempt. Cheaper, auditable,
and sufficient since heals are locator-only. Reserve full per-attempt
sandbox for untrusted (non-Healenium) healers later.
