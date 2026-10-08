"""Tests for API classifier: 5-way decision, spec-as-truth, Pact."""

from healing.nonui.classifier import ApiFailure, classify_api


def test_expired_token_healable() -> None:
    c = classify_api(ApiFailure(401, "token expired"))
    assert (c.api_class, c.healable) == ("expired_credential", True)


def test_stale_data_healable() -> None:
    c = classify_api(ApiFailure(200, "ids mismatch", data_fresh=False))
    assert (c.api_class, c.healable) == ("stale_data", True)


def test_approved_rename_healable() -> None:
    c = classify_api(ApiFailure(200, "", True, True, True, True))
    assert (c.api_class, c.healable) == ("approved_spec_change", True)


def test_unapproved_breaking_is_contract() -> None:
    c = classify_api(ApiFailure(200, "", True, True, False))
    assert (c.api_class, c.healable) == ("contract_change", False)


def test_spec_unchanged_is_likely_defect() -> None:
    c = classify_api(ApiFailure(500, "weird boom"))
    assert c.api_class == "unapproved_change" and not c.healable


def test_pact_always_escalates() -> None:
    c = classify_api(ApiFailure(200, "", True, False, True, pact=True))
    assert (c.api_class, c.healable) == ("contract_change", False)
