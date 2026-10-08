"""Tests for explanation records: hashing, immutability, append-only."""

import pytest

from healing.xai.records import JsonlRecordStore, make_record, verify_hash


def sample(**kw: object):  # type: ignore[no-untyped-def]
    base: dict[str, object] = {
        "heal_id": "heal-abc",
        "test": "t",
        "classification": "locator_drift",
    }
    base.update(kw)
    return make_record(**base)


def test_hash_stable_and_verified() -> None:
    r1 = sample()
    r2 = sample()
    assert r1.content_hash == r2.content_hash
    assert verify_hash(r1)
    assert len(r1.content_hash) == 64


def test_hash_changes_with_content() -> None:
    assert sample(test="a").content_hash != sample(test="b").content_hash


def test_tamper_detected() -> None:
    r = sample()
    tampered = r.model_copy(update={"classification": "data_issue"})
    assert not verify_hash(tampered)


def test_frozen_immutable() -> None:
    r = sample()
    with pytest.raises(Exception):
        r.classification = "x"  # type: ignore[misc]


def test_jsonl_append_only(tmp_path) -> None:  # type: ignore[no-untyped-def]
    store = JsonlRecordStore(str(tmp_path / "r.jsonl"))
    store.append(sample(test="one"))
    store.append(sample(test="two"))
    assert [r.test for r in store.list()] == ["one", "two"]
