"""Immutable explanation records: schema, hashing, append-only stores."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class CandidateScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    element_id: str
    score: float
    contributions: dict[str, float] = Field(default_factory=dict)


class Rejected(BaseModel):
    model_config = ConfigDict(frozen=True)

    element_id: str
    why: str


class ExplanationRecord(BaseModel):
    """Frozen record. Created via make_record(); corrections append anew."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    heal_id: str
    test: str
    step: str = ""
    classification: str = ""
    probabilities: dict[str, float] = Field(default_factory=dict)
    candidates: list[CandidateScore] = Field(default_factory=list)
    selected: str | None = None
    rejected: list[Rejected] = Field(default_factory=list)
    thresholds_applied: dict[str, float] = Field(default_factory=dict)
    critic_checks: dict[str, object] = Field(default_factory=dict)
    escalation_reason: str | None = None
    model_version: str = ""
    prompt_version: str = ""
    policy_version: str = ""
    config_version: str = ""
    content_hash: str = ""


def canonical_payload(record: ExplanationRecord) -> str:
    data = record.model_dump(exclude={"content_hash"}, mode="json")
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def compute_hash(record: ExplanationRecord) -> str:
    return hashlib.sha256(canonical_payload(record).encode("utf-8")).hexdigest()


def make_record(**fields: Any) -> ExplanationRecord:
    """Build an immutable record with its content hash stamped at creation."""
    bare = ExplanationRecord(**fields)
    return bare.model_copy(update={"content_hash": compute_hash(bare)})


def verify_hash(record: ExplanationRecord) -> bool:
    return record.content_hash == compute_hash(record)


class RecordStore(Protocol):
    def append(self, record: ExplanationRecord) -> None:
        raise NotImplementedError

    def list(self) -> list[ExplanationRecord]:
        raise NotImplementedError


class JsonlRecordStore:
    """Append-only JSONL fallback (Postgres unavailable locally)."""

    def __init__(self, path: str | None = None) -> None:
        default = os.path.join("benchmark", "reports", "records.jsonl")
        self.path: str = path or os.getenv("RECORDS_PATH") or default

    def append(self, record: ExplanationRecord) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")

    def list(self) -> list[ExplanationRecord]:
        if not os.path.exists(self.path):
            return []
        out: list[ExplanationRecord] = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    out.append(ExplanationRecord.model_validate_json(line))
        return out


class PostgresRecordStore:
    """Append-only Postgres store (INSERT only, never UPDATE)."""

    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or os.getenv("DATABASE_URL", "")

    def _connect(self):  # type: ignore[no-untyped-def]
        try:
            import psycopg  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "psycopg not installed; set RECORD_STORE=jsonl or install it"
            ) from exc
        return psycopg.connect(self.dsn)

    def append(self, record: ExplanationRecord) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO explanation_records (heal_id, content_hash, payload)"
                " VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (record.heal_id, record.content_hash, record.model_dump_json()),
            )

    def list(self) -> list[ExplanationRecord]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT payload FROM explanation_records ORDER BY id")
            return [ExplanationRecord.model_validate_json(row[0]) for row in cur]


def get_store() -> RecordStore:
    if os.getenv("RECORD_STORE", "jsonl") == "postgres":
        return PostgresRecordStore()
    return JsonlRecordStore()
