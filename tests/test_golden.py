"""Tests for the golden gate: degraded matcher fails, normal passes."""

import json

import pytest

from healing.quality.golden_set import load_golden


def test_golden_loads_and_hash_pins() -> None:
    data = load_golden()
    assert len(data["cases"]) == 24
    assert data["sha256"]


def test_golden_tamper_detected(tmp_path) -> None:
    from healing.quality.golden_set import pin_golden

    pin_golden([{"case_id": "x"}], str(tmp_path / "g.json"))
    payload = json.loads(open(str(tmp_path / "g.json")).read())
    payload["cases"].append({"case_id": "y"})
    with open(str(tmp_path / "g.json"), "w") as f:
        json.dump(payload, f)
    with pytest.raises(ValueError):
        load_golden(str(tmp_path / "g.json"))


def test_degraded_scorer_breaks_accuracy() -> None:
    """Swapping rescore to always-first must drop accuracy below the limit."""
    import healing.orchestrator as orch_module
    from benchmark.cases import CASES
    from benchmark.harness import candidates_from, page_html
    from healing.orchestrator import HealerOrchestrator
    from healing.policy.engine import load_config

    def bad_rescore(target, cands, weights=None):  # type: ignore[no-untyped-def]
        _ = (target, cands, weights)
        return []  # degraded: matcher proposes nothing

    orch_module.rescore = bad_rescore  # type: ignore[method-assign]
    try:
        orch = HealerOrchestrator()
        correct = 0
        for case in CASES:
            if not case.should_heal:
                continue
            html = page_html(case.page, case.drift_mode)
            out = orch.heal_case(
                case.case_id,
                case.case_id,
                case.drift_mode,
                html,
                case.locator,
                candidates_from(html),
                case.correct_element,
            )
            if out.healed == case.correct_element:
                correct += 1
    finally:
        from healing.matching.rescorer import rescore as real

        orch_module.rescore = real  # type: ignore[method-assign]
    cfg = load_config()
    assert correct / 15 < cfg.golden_min_accuracy  # gate would FAIL


def test_normal_matcher_passes_gate() -> None:
    from scripts import bench_golden as bg

    bg.main()  # exits 1 on failure; raises SystemExit otherwise
    data = json.loads(open("benchmark/reports/golden.json").read())
    assert data["pass"] is True
