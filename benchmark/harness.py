"""Harness: run each drift case, record failures, score healer choices."""

from __future__ import annotations

import os
import time

from benchmark.cases import BenchmarkCase, build_cases
from demo_app.app import cart_page, checkout_page, login_page, products_page
from healing.quality.metrics import RunResult, compute_metrics


def page_html(page: str, drift_mode: str) -> str:
    """Render a page directly (no HTTP/TestClient) for determinism."""
    os.environ["DRIFT_MODE"] = drift_mode
    try:
        if page == "/login":
            return login_page()
        if page == "/products":
            return products_page()
        if page == "/cart":
            return cart_page()
        if page == "/checkout":
            return checkout_page()
        raise ValueError(f"unknown page: {page}")
    finally:
        os.environ["DRIFT_MODE"] = "none"


def candidates_from(html: str) -> list[str]:
    """Stable candidates: data-testid values in order (deterministic)."""
    out: list[str] = []
    idx = 0
    while True:
        idx = html.find('data-testid="', idx)
        if idx == -1:
            return out
        start = idx + len('data-testid="')
        end = html.find('"', start)
        out.append(html[start:end])
        idx = end


def run_case(case: BenchmarkCase, healer: object) -> RunResult:
    start = time.perf_counter()
    html = page_html(case.page, case.drift_mode)
    naive_ok = case.locator in html
    # Every drift case counts as a failure to score (deterministic benchmark);
    # naive_ok is recorded for diagnostics but the healer is always attempted.
    _ = naive_ok
    chosen: str | None = None
    if case.drift_mode != "none":
        cands = candidates_from(html)
        choose_case = getattr(healer, "choose_for_case", None)
        if callable(choose_case):
            chosen = choose_case(case, cands)  # type: ignore[no-untyped-call]
        else:
            choose = getattr(healer, "choose", None)
            if callable(choose):
                chosen = choose(cands)  # type: ignore[no-untyped-call]
    latency_ms = (time.perf_counter() - start) * 1000.0
    healed = chosen is not None
    if case.should_heal:
        correct = healed and chosen == case.correct_element
        escalated = not healed
    else:
        # Adversarial: any heal is wrong; correct action is to escalate.
        correct = False
        escalated = not healed
    cost = 0.0 if not healed else 1.0
    return RunResult(
        case_id=case.case_id,
        should_heal=case.should_heal,
        healed=healed,
        correct=bool(correct),
        escalated=escalated,
        cost=cost,
        latency_ms=latency_ms,
    )


def run_all(healer: object, seed: int = 42) -> list[RunResult]:
    _ = seed
    return [run_case(c, healer) for c in build_cases()]


def summarize(results: list[RunResult]) -> dict[str, object]:
    m = compute_metrics(results)
    return {
        "metrics": {
            "total": m.total,
            "heal_accuracy": m.heal_accuracy,
            "false_heal_rate": m.false_heal_rate,
            "escalation_rate": m.escalation_rate,
            "correct_escalation_rate": m.correct_escalation_rate,
            "cost_per_heal": m.cost_per_heal,
            "latency_per_heal_ms": m.latency_per_heal_ms,
        },
        "results": [
            {
                "case_id": r.case_id,
                "should_heal": r.should_heal,
                "healed": r.healed,
                "correct": r.correct,
                "escalated": r.escalated,
            }
            for r in results
        ],
    }
