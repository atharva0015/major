"""OpenTelemetry traces + Prometheus metrics (thin observe() calls)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from prometheus_client import Counter, Histogram

try:
    trace.get_tracer(__name__)
except Exception:  # pragma: no cover - provider setup is best-effort
    trace.set_tracer_provider(TracerProvider())

TRACER = trace.get_tracer("healing")

HEAL_LATENCY = Histogram("heal_latency_seconds", "Heal latency by attempt", ["attempt"])
HEAL_COST = Counter("heal_cost_total", "Heal cost by attempt", ["attempt"])
HEAL_SUCCESS = Counter(
    "heal_success_total", "Heal success by attempt number", ["attempt", "result"]
)
ESCALATIONS = Counter("heal_escalations_total", "Escalations by class", ["classification"])
ALERT_ACK_TIME = Histogram("alert_ack_seconds", "Alert acknowledgement time")


@contextmanager
def traced(
    name: str, attributes: dict[str, str | int | float | bool] | None = None
) -> Iterator[None]:
    with TRACER.start_as_current_span(name, attributes=attributes or {}):
        yield


def observe_heal(attempt: int, success: bool, latency_s: float, cost: float) -> None:
    HEAL_LATENCY.labels(attempt=str(attempt)).observe(latency_s)
    HEAL_COST.labels(attempt=str(attempt)).inc(cost)
    HEAL_SUCCESS.labels(attempt=str(attempt), result="success" if success else "fail").inc()


def observe_escalation(classification: str) -> None:
    ESCALATIONS.labels(classification=classification).inc()


def observe_ack(seconds: float) -> None:
    ALERT_ACK_TIME.observe(seconds)
