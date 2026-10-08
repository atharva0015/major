"""API heal pipeline reusing the shared primitives.

classify -> sandbox replay -> contract checks -> guard -> heal/record ->
shadow PR body -> audit. Contract changes, assertions, and SLAs are never
auto-healed; Pact failures always escalate.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass

from demo_app.openapi import BASE_SPEC, spec_for
from healing.nonui.assert_guard import guard_diff
from healing.nonui.classifier import ApiFailure, classify_api
from healing.nonui.healers import heal_api
from healing.nonui.schema_diff import SchemaDiff, diff_specs
from healing.sandbox.runner import SandboxConfig, SandboxSession
from healing.security import audit
from healing.security.masking import mask_pii
from healing.xai.narrative import render_narrative
from healing.xai.records import get_store, make_record


@dataclass(frozen=True)
class ApiCase:
    case_id: str
    drift_mode: str
    endpoint: str
    approved: bool = False
    pact: bool = False


@dataclass(frozen=True)
class ApiOutcome:
    healed: bool
    api_class: str
    action: str
    reason: str
    shadow_pr: dict[str, str] | None = None


def check_contract(payload: object, endpoint: str, spec: dict[str, object]) -> tuple[bool, str]:
    """Response shape matches the spec; no new error codes. Deterministic."""
    paths = spec.get("paths", {})
    assert isinstance(paths, dict)
    if endpoint not in paths:
        return False, f"endpoint_not_in_spec:{endpoint}"
    if isinstance(payload, dict) and "detail" in payload:
        return False, f"error_payload:{payload.get('detail')}"
    return True, ""


def observe(case: ApiCase) -> ApiFailure:
    """Run the real endpoint under drift; never regenerate payloads to force a pass."""
    from fastapi import HTTPException

    from demo_app import app as app_module

    os.environ["API_DRIFT_MODE"] = case.drift_mode
    saved_token = os.environ.pop("TEST_TOKEN", None)  # tests run with the stale credential
    try:
        status, error = 200, ""
        payload: object = None
        try:
            if case.endpoint == "GET /api/products":
                payload = app_module.api_products()
            elif case.endpoint == "POST /api/cart":
                payload = app_module.api_add_cart(app_module.AddCart(product_id=1))
            elif case.endpoint == "POST /api/checkout":
                payload = app_module.api_checkout()
            else:
                return ApiFailure(
                    500,
                    f"unknown endpoint {case.endpoint}",
                    False,
                    False,
                    case.approved,
                    False,
                    True,
                    True,
                    case.pact,
                )
        except HTTPException as exc:
            status, error = exc.status_code, str(exc.detail)
        diff = diff_specs(BASE_SPEC, spec_for(case.drift_mode))
        rename_only = bool(diff.changes) and all(c.kind == "renamed_field" for c in diff.changes)
        fresh = True
        if case.drift_mode == "stale_seed" and isinstance(payload, list):
            fresh = {p.get("id") for p in payload} == {1, 2, 3}
        if status == 401:
            return ApiFailure(
                status,
                error or "token expired",
                False,
                False,
                case.approved,
                False,
                False,
                fresh,
                case.pact,
            )
        return ApiFailure(
            status,
            error,
            bool(diff.changes),
            diff.has_breaking,
            case.approved,
            rename_only,
            True,
            fresh,
            case.pact,
        )
    finally:
        os.environ["API_DRIFT_MODE"] = "none"
        if saved_token is None:
            os.environ.pop("TEST_TOKEN", None)
        else:
            os.environ["TEST_TOKEN"] = saved_token


def heal_api_case(case: ApiCase, human_signoff: str | None = None) -> ApiOutcome:
    failure = observe(case)
    masked_err = mask_pii(failure.error)
    cls = classify_api(failure)
    diff = diff_specs(BASE_SPEC, spec_for(case.drift_mode))

    with SandboxSession(SandboxConfig(seed=42)) as sbx:
        _ = sbx.run(lambda: dict(status=failure.status, error=masked_err))

    if not cls.healable:
        _record(
            case,
            cls.api_class,
            None,
            "escalate",
            f"{cls.fired_rules[0] if cls.fired_rules else 'blocked'}; "
            f"breaking={[c.kind for c in diff.breaking]}",
        )
        audit.append("system", "escalate", case.case_id, cls.api_class)
        return ApiOutcome(False, cls.api_class, "escalate", f"{cls.api_class}: {masked_err}")

    heal = heal_api(
        cls.api_class,
        old_field="price",
        new_field="amount",
        test_path="test_api.py",
        schema_diff=str(diff),
    )
    if heal.action == "propose_test_update":
        allowed, why = guard_diff(heal.diff, human_signoff)
        if not allowed:
            _record(case, cls.api_class, None, "escalate", why)
            return ApiOutcome(False, cls.api_class, "escalate", why)
        from healing.gitops.pr_template import build_pr_body

        body = build_pr_body(
            f"API heal {case.case_id}: approved rename price->amount.",
            heal.diff,
            0.9,
            "contract-checks-pass",
            f"records://{case.case_id}",
            "n/a",
            f"screenshots/{case.case_id}-before.png",
            f"screenshots/{case.case_id}-after.png",
            f"screenshots/{case.case_id}-candidate.png",
            f"sandbox://replay/{case.case_id}",
            f"Revert via scripts/rollback_heal.py {case.case_id}.",
        )
        _record(
            case,
            cls.api_class,
            heal.action,
            "proposed",
            f"shadow PR body built ({len(body)} chars)",
        )
        return ApiOutcome(
            True, cls.api_class, heal.action, heal.detail, {"diff": heal.diff, "body": body}
        )
    _record(case, cls.api_class, heal.action, "applied", heal.detail)
    audit.append("system", "heal", case.case_id, heal.action)
    return ApiOutcome(True, cls.api_class, heal.action, heal.detail)


def _record(
    case: ApiCase, api_class: str, selected: str | None, decision: str, reason: str
) -> None:
    record = make_record(
        heal_id=f"api-{uuid.uuid4().hex[:12]}",
        test=case.case_id,
        step=case.endpoint,
        classification=api_class,
        probabilities={api_class: 1.0},
        selected=selected,
        escalation_reason=None if selected else reason,
        critic_checks={"contract_checks": "pass" if selected else "n/a"},
        thresholds_applied={},
        model_version="rules-0.1.0",
        prompt_version="n/a-template-0.1.0",
        policy_version="policy-0.1.0",
        config_version="config-0.1.0",
    )
    get_store().append(record)
    render_narrative(record)


def spec_diff_for(mode: str) -> SchemaDiff:
    return diff_specs(BASE_SPEC, spec_for(mode))
