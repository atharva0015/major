"""Tests for heal metrics (deterministic, plain-code scoring)."""

from healing.quality.metrics import RunResult, compute_metrics, to_json, to_markdown


def sample() -> list[RunResult]:
    return [
        RunResult("a", True, True, True, False, 1.0, 10.0),
        RunResult("b", True, False, False, True, 0.0, 0.0),
        RunResult("c", False, False, False, True, 0.0, 0.0),
        RunResult("d", False, True, False, False, 2.0, 20.0),
    ]


def test_metric_values() -> None:
    m = compute_metrics(sample())
    assert m.total == 4
    assert m.heal_accuracy == 0.5  # 1/2 should-heal correct
    assert m.false_heal_rate == 0.5  # 1 wrong / 2 healed
    assert m.escalation_rate == 0.5  # 2/4 escalated
    assert m.correct_escalation_rate == 0.5  # 1/2 correct escalations
    assert m.cost_per_heal == 1.5
    assert m.latency_per_heal_ms == 15.0


def test_empty_results_zeroed() -> None:
    m = compute_metrics([])
    assert m.total == 0
    assert m.heal_accuracy == 0.0
    assert m.false_heal_rate == 0.0


def test_json_and_markdown_shapes() -> None:
    m = compute_metrics(sample())
    j = to_json(m)
    assert '"heal_accuracy"' in j
    md = to_markdown(m)
    assert md.startswith("# ")
    assert "heal_accuracy" in md
