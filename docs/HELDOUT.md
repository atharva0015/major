# Held-out report (frozen pipeline, unseen cases, seed 42)

36 cases written independently from new elements, pages, locators, and
endpoint combos. Labels fixed before running. Nothing tuned afterward:
the one mismatch below stands as recorded.

## UI (24 cases, MEASURED)

- classification accuracy: 1.000
- critic catch rate: 1.000 (15/15 injected)
- critic false-reject rate: 0.000
- false-heal rate: 0.000
- escaped defects: 0
- wrong cases: none

New vs original: cancel/username/password inputs, neighbor products
(add-cart-2/3), anchor-link layout (/cart cart-checkout) instead of only
submit buttons. All 8 drift modes covered, including look-alike decoys,
A/B text variants, swapped roles, and removed elements.

## API (11 cases, MEASURED)

- class+heal match: 10/11
- auto-healed contract changes: 0 (must be 0)
- false-heal rate: 0.000
- wrong cases: ['heldout:token-cart']

## The one failure (reported, not fixed)

`heldout:token-cart` (expired_token on GET /api/cart): labeled
expired_credential/heal, observed unapproved_change/escalate. Cause is in
my label, compounded by a real coverage gap — `observe()` only handles
three endpoints, so GET /api/cart falls into the "unknown endpoint"
branch and escalates as a likely defect. Fail-closed and safe (nothing
healed), but imprecise: an expired credential on the cart view is
reported as an unapproved change. Fixing either the label or the
endpoint coverage is explicitly out of scope for this step.

## Per-case UI (MEASURED)

| case | true | predicted | decision | healed | heal_ok |
|---|---|---|---|---|---|---|
| heldout:renamed_ids:/login:id="username" | locator_drift | locator_drift | heal_unverified | username | True |
| heldout:renamed_ids:/login:id="password" | locator_drift | locator_drift | heal_unverified | password | True |
| heldout:renamed_ids:/cart:id="cart-checkout" | locator_drift | locator_drift | heal_unverified | cart-checkout | True |
| heldout:changed_classes:/login:id="login-cancel" | locator_drift | locator_drift | heal_unverified | login-cancel | True |
| heldout:changed_classes:/products:id="add-cart-2" | locator_drift | locator_drift | heal_unverified | add-cart-2 | True |
| heldout:changed_classes:/checkout:id="checkout-cancel" | locator_drift | locator_drift | heal_unverified | checkout-cancel | True |
| heldout:moved_elements:/login:id="login-cancel" | locator_drift | locator_drift | heal_unverified | login-cancel | True |
| heldout:moved_elements:/products:id="add-cart-3" | locator_drift | locator_drift | heal_unverified | add-cart-3 | True |
| heldout:moved_elements:/cart:id="cart-checkout" | locator_drift | locator_drift | heal_unverified | cart-checkout | True |
| heldout:reskinned_layout:/login:id="login-cancel" | locator_drift | locator_drift | heal_unverified | login-cancel | True |
| heldout:reskinned_layout:/products:id="add-cart-2" | locator_drift | locator_drift | heal_unverified | add-cart-2 | True |
| heldout:reskinned_layout:/checkout:id="checkout-cancel" | locator_drift | locator_drift | heal_unverified | checkout-cancel | True |
| heldout:duplicate_buttons:/login:id="login-cancel" | environment_issue | environment_issue | fail_escalate | None | True |
| heldout:duplicate_buttons:/products:id="add-cart-2" | environment_issue | environment_issue | fail_escalate | None | True |
| heldout:duplicate_buttons:/checkout:id="checkout-cancel" | environment_issue | environment_issue | fail_escalate | None | True |
| heldout:removed_element:/login:id="login-cancel" | genuine_regression | genuine_regression | fail_escalate | None | True |
| heldout:removed_element:/products:id="add-cart-2" | genuine_regression | genuine_regression | fail_escalate | None | True |
| heldout:removed_element:/cart:id="cart-checkout" | genuine_regression | genuine_regression | fail_escalate | None | True |
| heldout:swapped_roles:/login:id="login-cancel" | genuine_regression | genuine_regression | fail_escalate | None | True |
| heldout:swapped_roles:/products:id="add-cart-2" | genuine_regression | genuine_regression | fail_escalate | None | True |
| heldout:swapped_roles:/checkout:id="checkout-cancel" | genuine_regression | genuine_regression | fail_escalate | None | True |
| heldout:ab_variant_text:/login:id="username" | locator_drift | locator_drift | heal_unverified | username | True |
| heldout:ab_variant_text:/products:id="add-cart-3" | locator_drift | locator_drift | heal_unverified | add-cart-3 | True |
| heldout:ab_variant_text:/checkout:id="checkout-cancel" | locator_drift | locator_drift | heal_unverified | checkout-cancel | True |

## Per-case API (MEASURED)

| case | class | action | healed | heal_ok |
|---|---|---|---|---|
| heldout:renamed-unapproved | contract_change | escalate | False | True |
| heldout:rename-cart-approved | approved_spec_change | propose_test_update | True | True |
| heldout:coupon-on-get | contract_change | escalate | False | True |
| heldout:coupon-approved | contract_change | escalate | False | True |
| heldout:removed-products-view | contract_change | escalate | False | True |
| heldout:token-cart | unapproved_change | escalate | False | False |
| heldout:token-checkout | expired_credential | refresh_token | True | True |
| heldout:stale-cart-view | unapproved_change | escalate | False | True |
| heldout:stale-checkout | unapproved_change | escalate | False | True |
| heldout:type-cart | contract_change | escalate | False | True |
| heldout:pact-products | contract_change | escalate | False | True |
