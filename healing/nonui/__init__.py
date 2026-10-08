"""NonUI: non-UI (API/schema) failure handling; never auto-heal contracts."""

from healing.nonui.assert_guard import guard_diff
from healing.nonui.classifier import API_CLASSES, ApiClassification, ApiFailure, classify_api
from healing.nonui.healers import ALLOWED_ACTIONS, ApiHeal, escalate_with_diff, heal_api
from healing.nonui.pipeline import ApiCase, ApiOutcome, check_contract, heal_api_case
from healing.nonui.schema_diff import SchemaDiff, SpecChange, diff_specs

__all__: list[str] = [
    "ALLOWED_ACTIONS",
    "API_CLASSES",
    "ApiCase",
    "ApiClassification",
    "ApiFailure",
    "ApiHeal",
    "ApiOutcome",
    "SchemaDiff",
    "SpecChange",
    "check_contract",
    "classify_api",
    "diff_specs",
    "escalate_with_diff",
    "guard_diff",
    "heal_api",
    "heal_api_case",
]
