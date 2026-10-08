"""Tests for PII masking and the append-only audit log."""

from healing.security import audit
from healing.security.masking import mask_mapping, mask_pii


def test_email_masked() -> None:
    assert mask_pii("contact ada@example.com now") == "contact [email] now"


def test_phone_masked() -> None:
    out = mask_pii("call +1 555-123-4567 ok")
    assert "555" not in out and "[phone]" in out


def test_card_masked() -> None:
    out = mask_pii("card 4111 1111 1111 1111 charged")
    assert "4111" not in out and "[card]" in out


def test_token_masked() -> None:
    out = mask_pii("Authorization: Bearer abc123XYZ")
    assert "abc123" not in out and "[token]" in out


def test_configurable_pattern() -> None:
    out = mask_pii("order SECRET-999 here", [r"SECRET-\d+"])
    assert "SECRET-999" not in out and "[masked]" in out


def test_mapping_masks_values_only() -> None:
    assert mask_mapping({"a": "a@b.com", "n": 5}) == {"a": "[email]", "n": 5}


def test_audit_append_only(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("AUDIT_LOG", str(tmp_path / "audit.log"))
    e1 = audit.append("system", "heal", "c1", "heal_unverified")
    e2 = audit.append("user", "review", "c1", "approved")
    assert (e1["seq"], e2["seq"]) == (1, 2)
    assert e2["prev"] == e1["hash"]
    assert len(audit.read_all()) == 2
