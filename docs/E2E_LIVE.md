# Live end-to-end report (all numbers MEASURED on the live stack, seed 42)

Pipeline per case: live matcher (naive `By.ID` through hlm-proxy 2.2.1 in
real Chrome via Selenium Grid) -> rules classifier -> policy gate ->
sandbox replay -> layered Critic -> explanation record + alert.
Shadow mode: records + console/file alerts only; **no PRs opened**.
Stack: hlm-backend 3.5.1, postgres 15.5-alpine, node-chromium, demo app.
Green warmup over 3 pages first (Healenium needs stored references).

## Summary (MEASURED)

- cases: 24 (15 healable locator_drift, 9 adversarial)
- accuracy: **1.000** (24/24 correct)
- false-heal rate overall: **0.000**
- adversarial false-heal rate (9 cases): **0.000** — all 9 escalated
- escalation rate: 0.375 (9/24, exactly the adversarial set)
- escaped defects: **0**
- latency per heal, live lookup mean: **1464.7 ms** (fresh browser session
  per case; pipeline overhead excluded)
- decisions: 15 × `heal_unverified` (attempt 1, Critic pass), 9 ×
  `fail_escalate` (classifier short-circuit, 0 attempts, 0 retries)

## Per-case results (all MEASURED)

| case | classification | attempts | critic | action | healed | correct |
|---|---|---|---|---|---|---|
| ab_variant_text:/login | locator_drift | [1] | pass | heal_unverified | login-submit | True |
| ab_variant_text:/products | locator_drift | [1] | pass | heal_unverified | add-cart-1 | True |
| ab_variant_text:/checkout | locator_drift | [1] | pass | heal_unverified | checkout-submit | True |
| changed_classes:/login | locator_drift | [1] | pass | heal_unverified | login-submit | True |
| changed_classes:/products | locator_drift | [1] | pass | heal_unverified | add-cart-1 | True |
| changed_classes:/checkout | locator_drift | [1] | pass | heal_unverified | checkout-submit | True |
| duplicate_buttons:/login | environment_issue | [] | n/a (short-circuit, 0 retries) | fail_escalate | None | True |
| duplicate_buttons:/products | environment_issue | [] | n/a (short-circuit, 0 retries) | fail_escalate | None | True |
| duplicate_buttons:/checkout | environment_issue | [] | n/a (short-circuit, 0 retries) | fail_escalate | None | True |
| moved_elements:/login | locator_drift | [1] | pass | heal_unverified | login-submit | True |
| moved_elements:/products | locator_drift | [1] | pass | heal_unverified | add-cart-1 | True |
| moved_elements:/checkout | locator_drift | [1] | pass | heal_unverified | checkout-submit | True |
| removed_element:/login | genuine_regression | [] | n/a (short-circuit, 0 retries) | fail_escalate | None | True |
| removed_element:/products | genuine_regression | [] | n/a (short-circuit, 0 retries) | fail_escalate | None | True |
| removed_element:/checkout | genuine_regression | [] | n/a (short-circuit, 0 retries) | fail_escalate | None | True |
| renamed_ids:/login | locator_drift | [1] | pass | heal_unverified | login-submit | True |
| renamed_ids:/products | locator_drift | [1] | pass | heal_unverified | add-cart-1 | True |
| renamed_ids:/checkout | locator_drift | [1] | pass | heal_unverified | checkout-submit | True |
| reskinned_layout:/login | locator_drift | [1] | pass | heal_unverified | login-submit | True |
| reskinned_layout:/products | locator_drift | [1] | pass | heal_unverified | add-cart-1 | True |
| reskinned_layout:/checkout | locator_drift | [1] | pass | heal_unverified | checkout-submit | True |
| swapped_roles:/login | genuine_regression | [] | n/a (short-circuit, 0 retries) | fail_escalate | None | True |
| swapped_roles:/products | genuine_regression | [] | n/a (short-circuit, 0 retries) | fail_escalate | None | True |
| swapped_roles:/checkout | genuine_regression | [] | n/a (short-circuit, 0 retries) | fail_escalate | None | True |

## Honest caveats

- The 0.000 adversarial rate is earned by the **classifier gate**, not the
  matcher: all 9 adversarial cases short-circuited before any healing was
  attempted. The raw live matcher alone heals 9/9 adversarial
  (see `healenium_live.md`, MEASURED FHR 1.000) — **Healenium alone is not
  safe**; the pipeline around it is what holds.
- Every healable case won at attempt 1, so attempts 2+ remain unexercised
  live; the ladder beyond attempt 1 is covered only by unit tests.
- Alert screenshots are placeholder paths (no screenshots captured);
  records + audit entries were written to the standard stores.
- No thresholds, targets, golden files, or benchmark logic were changed;
  no failures occurred, so nothing was tuned or hidden.
