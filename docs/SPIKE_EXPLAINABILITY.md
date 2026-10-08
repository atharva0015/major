# Spike A — Healenium explainability

## What Healenium exposes (verified against public interfaces)

- HTML report at `GET /healenium/report/` per session: failed locator value,
  healed locator value, screenshot, correct/not-correct toggle, **single
  final healing score**.
- JSON: `GET /healenium/report/data`, `GET /healenium/report/data/{uid}`,
  `GET /healenium/selector/all`, `POST /healenium/healing/success`
  (confirmed via healenium.io report + MCP tool docs).
- Postgres stores reference selectors and healing rows, but per-feature
  weights (text vs role vs attributes vs structure) are **not exposed**
  through any public endpoint.

## Conclusion

Only a final opaque score is available. That is insufficient for the
AGENTS.md rule "structured explanation record before narrative" and for
fail-closed gating on adversarial cases.

## Recommendation

Keep Healenium score as one signal behind `SCORE_CAP=.6`; re-score its top
candidates with `healing/matching/rescorer.py`: transparent weights
(text .25, role .20, accessible name .20, attributes .15, position .10,
neighbors .10) returning per-feature contributions. Gate: below threshold
or conflicting top candidates → escalate, never auto-heal.
