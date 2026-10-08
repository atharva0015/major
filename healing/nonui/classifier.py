"""API failure classifier: spec is the source of truth.

Decides among expired_credential | stale_data | approved_spec_change |
unapproved_change | contract_change. If the spec did not change, the
failure is a likely defect -> escalate. Pact/consumer-driven failures
always escalate. Pure deterministic rules.
"""

from __future__ import annotations

from dataclasses import dataclass

API_CLASSES = (
    "expired_credential",
    "stale_data",
    "approved_spec_change",
    "unapproved_change",
    "contract_change",
)


@dataclass(frozen=True)
class ApiFailure:
    status: int = 200
    error: str = ""
    spec_changed: bool = False
    breaking: bool = False
    approved: bool = False
    rename_only: bool = False
    auth_ok: bool = True
    data_fresh: bool = True
    pact: bool = False


@dataclass(frozen=True)
class ApiClassification:
    api_class: str
    fired_rules: tuple[str, ...] = ()
    healable: bool = False


def classify_api(failure: ApiFailure) -> ApiClassification:
    if failure.pact:
        return ApiClassification("contract_change", ("pact_always_escalates",), False)
    if (
        failure.status == 401
        or "token expired" in failure.error.lower()
        or "unauthorized" in failure.error.lower()
    ):
        if not failure.spec_changed:
            return ApiClassification("expired_credential", ("auth_401_spec_unchanged",), True)
        return ApiClassification("contract_change", ("auth_scheme_changed",), False)
    if failure.breaking:
        if failure.approved and failure.rename_only:
            return ApiClassification("approved_spec_change", ("approved_rename_in_spec",), True)
        return ApiClassification("contract_change", ("breaking_spec_diff",), False)
    if failure.spec_changed and failure.approved:
        return ApiClassification("approved_spec_change", ("approved_non_breaking",), True)
    if failure.spec_changed and not failure.approved:
        return ApiClassification("unapproved_change", ("unapproved_diff_likely_defect",), False)
    if not failure.data_fresh:
        return ApiClassification("stale_data", ("stale_fixture",), True)
    # Spec did not change and no credential/data cause: likely defect.
    return ApiClassification("unapproved_change", ("spec_unchanged_likely_defect",), False)
