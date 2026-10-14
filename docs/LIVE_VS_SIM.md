# LIVE_VS_SIM: measured Healenium vs simulator (2026-10-08)

Stack: hlm-backend 3.5.1, hlm-proxy 2.2.1, selector-imitator 1.6,
postgres 15.5-alpine, Selenium Grid hub + node-chromium, demo app.
Seed 42, 24 UI cases, green warmup pass first (the tool needs stored
references). Numbers below are MEASURED live except where marked SIMULATED.

## Headline numbers

| Metric | SIMULATED (healenium.md) | MEASURED live (healenium_live.md) |
|---|---|---|
| heal accuracy | 1.000 | 1.000 |
| false-heal rate, overall | 0.286 | **0.375** |
| adversarial false-heal (9 cases) | 1.000 (6/9) | **1.000 (9/9)** |
| escalation rate | 0.125 | **0.000** |
| correct-escalation rate | 0.333 | **0.000** |
| latency per heal | 0.021 ms (in-process units) | **1122 ms** |
| cost per heal | 1.000 | 1.000 (constant by construction) |

## What the simulator got wrong

1. **Removed elements.** SIMULATED: correctly escalated (3/3). MEASURED: the
   live proxy *healed all three* (`removed_element` → `via: healed`,
   wrong element). The sim's escalate-on-removed rule was backwards: live
   Healenium invents a match for deleted elements instead of failing.
2. **Duplicate/swapped drifts.** SIMULATED: decoy/cancel picks (active false
   heals). MEASURED: naive `By.ID` lookups still resolve, so the proxy
   passes them through untouched — no healing event, but the real defect
   (ambiguous buttons, swapped roles) sails through silently. Counted as
   false heals under fail-closed accounting: a masked defect is a masked
   defect, whether the proxy acted or not.
3. **Only `renamed_ids` triggers real healing** (`/login`, `/checkout`;
   `/products` ids are untouched by that drift → passthrough). The sim
   treated every drift as a healing event; live, most drifts never reach
   the matcher at all.
4. **Latency.** SIMULATED microseconds are meaningless; MEASURED ~1.1 s per
   healed lookup (fresh browser session each). Cost units are identical
   only because both sides record a constant.
5. **Report dedupe.** Live backend 3.5.1 writes one row per locator and
   reuses it on repeat healings (`score` string-encoded, e.g. `"0.97"`,
   under a `data` key — not the guessed `items`/numeric shape). The
   adapter was narrowed to exactly this shape (v0.2.0).

## Safety verdict: Healenium alone is NOT safe

MEASURED live adversarial false-heal rate is **1.000 (9/9)** with an
escalation rate of **0.000** — the proxy never declines. Worst of all, it
heals genuinely removed elements. Every live heal must stay behind the
classifier (which blocks all 9 adversarial classes before matching), the
layered Critic, and policy gating. The sim understated the danger on
removed elements and overstated it on duplicates; both directions confirm
the same conclusion: never trust the raw matcher.
