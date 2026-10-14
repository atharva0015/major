"""Intent-exactness: the 5 known same-stem escapes plus new look-alikes.

Each case below PASSED the old stem allowance (same stem on both sides)
and must now FAIL closed. None of these weaken existing tests.
"""

from healing.critic.checks import check_intent, run_checks

# The 5 measured escapes: wrong_candidate() picks add-cart-2 for add-cart-1
# on every healable products-page drift; all share stem "add-cart".
KNOWN_ESCAPES = [
    ("add-cart-2", "add-cart-1", "renamed_ids:/products"),
    ("add-cart-2", "add-cart-1", "changed_classes:/products"),
    ("add-cart-2", "add-cart-1", "moved_elements:/products"),
    ("add-cart-2", "add-cart-1", "reskinned_layout:/products"),
    ("add-cart-2", "add-cart-1", "ab_variant_text:/products"),
]

# New look-alikes I wrote: renamed ids, cancel siblings, prefix traps,
# text-identical decoys. Every pair shares a stem or visible text.
NEW_LOOK_ALIKES = [
    ("login-submit-v2", "login-submit", "renamed id text"),
    ("checkout-cancel", "checkout-submit", "cancel sibling"),
    ("user-name-field", "username", "renamed field"),
    ("cart-checkout-v2", "cart-checkout", "renamed link"),
    ("add-cart-10", "add-cart-1", "numeric prefix trap"),
    ("decoy-buy", "add-cart-1", "text-identical decoy"),
    ("login-cancel", "login-submit", "cancel sibling login"),
]


def test_known_escapes_now_fail() -> None:
    assert len(KNOWN_ESCAPES) == 5
    for chosen, correct, purpose in KNOWN_ESCAPES:
        ok, why = check_intent(chosen, correct, purpose)
        assert ok is False, f"{chosen} vs {correct} must fail"
        assert why.startswith("intent_mismatch")


def test_new_look_alikes_fail_closed() -> None:
    for chosen, correct, purpose in NEW_LOOK_ALIKES:
        ok, why = check_intent(chosen, correct, purpose)
        assert ok is False, f"{chosen} vs {correct} must fail"
        assert f"{chosen}!={correct}" in why


def test_exact_identity_still_passes() -> None:
    for element in ("login-submit", "add-cart-1", "cart-checkout", "username"):
        assert check_intent(element, element, "p") == (True, "")


def test_layer_attribution_is_intent() -> None:
    html = (
        "<html><body><main>"
        '<button id="a2" data-testid="add-cart-2" class="btn">Buy</button>'
        '<button id="a1" data-testid="add-cart-1" class="btn">Buy</button>'
        "</main></body></html>"
    )
    v = run_checks(
        html,
        "add-cart-2",
        "add-cart-1",
        html,
        ["add-cart-1", "add-cart-2"],
        [],
        ["demo", "wiremock"],
        "buy",
    )
    assert v.passed is False and v.failed_layer == "intent"


def test_unknown_correct_still_fails_closed() -> None:
    assert check_intent("anything", None, "p") == (False, "no_correct_element")
