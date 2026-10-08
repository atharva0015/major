"""Tests for OpenAPI spec diff: breaking vs non-breaking."""

from demo_app.openapi import BASE_SPEC, spec_for
from healing.nonui.schema_diff import diff_specs


def test_renamed_field_is_breaking() -> None:
    d = diff_specs(BASE_SPEC, spec_for("renamed_field"))
    assert d.has_breaking
    assert any(c.kind == "renamed_field" for c in d.changes)


def test_new_required_is_breaking() -> None:
    d = diff_specs(BASE_SPEC, spec_for("new_required_field"))
    assert any(c.kind == "new_required" and c.breaking for c in d.changes)


def test_removed_endpoint_is_breaking() -> None:
    d = diff_specs(BASE_SPEC, spec_for("removed_endpoint"))
    assert any(c.kind == "removed_endpoint" for c in d.breaking)


def test_type_change_is_breaking() -> None:
    d = diff_specs(BASE_SPEC, spec_for("type_change"))
    assert any(c.kind == "type_change" for c in d.changes)


def test_identical_specs_have_no_changes() -> None:
    d = diff_specs(BASE_SPEC, spec_for("none"))
    assert d.changes == () and not d.has_breaking


def test_added_optional_is_non_breaking() -> None:
    import copy

    head = copy.deepcopy(BASE_SPEC)
    head["paths"]["/api/products"]["get"]["responses"]["200"]["fields"]["nick"] = "str"
    d = diff_specs(BASE_SPEC, head)
    assert not d.has_breaking
    assert any(c.kind == "added_optional" for c in d.changes)
