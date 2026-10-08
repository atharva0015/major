"""XAI: structured explanation records before narrative text."""

from healing.xai.narrative import consistency_check, render_narrative
from healing.xai.records import (
    ExplanationRecord,
    JsonlRecordStore,
    PostgresRecordStore,
    compute_hash,
    get_store,
    make_record,
    verify_hash,
)

__all__: list[str] = [
    "ExplanationRecord",
    "JsonlRecordStore",
    "PostgresRecordStore",
    "compute_hash",
    "consistency_check",
    "get_store",
    "make_record",
    "render_narrative",
    "verify_hash",
]
