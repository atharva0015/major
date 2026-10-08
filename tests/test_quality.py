"""Tests for calibration curves, survival math, and autonomy downgrade."""

from healing.policy.engine import load_config
from healing.quality.autonomy_guard import evaluate
from healing.quality.calibration import (
    alarm_if_diverged,
    expected_calibration_error,
    reliability_curve,
)
from healing.quality.survival import (
    fingerprint_freshness,
    override_rate,
    revert_rate,
    survival_rate,
)


def test_perfect_calibration_zero_ece() -> None:
    pairs = [(0.9, True)] * 9 + [(0.1, False)] * 9
    assert expected_calibration_error(pairs) < 0.15
    assert reliability_curve(pairs)[9]["n"] == 9


def test_miscalibration_alarms() -> None:
    pairs = [(0.95, False)] * 10
    ece = expected_calibration_error(pairs)
    assert ece > 0.5
    alarmed, _ = alarm_if_diverged(ece, load_config().max_calibration_ece)
    assert alarmed


def test_no_alarm_when_calibrated() -> None:
    alarmed, _ = alarm_if_diverged(0.05, load_config().max_calibration_ece)
    assert not alarmed


def test_survival_insufficient_data() -> None:
    assert survival_rate([], 30)["status"] == "insufficient_data"
    assert revert_rate([])["status"] == "insufficient_data"
    assert override_rate([])["status"] == "insufficient_data"


def test_survival_rates_seeded() -> None:
    now = 200 * 86400.0
    heals = [
        {"merged_at": 0.0},
        {"merged_at": 0.0, "reverted": True},
        {"merged_at": 0.0, "overridden": True},
    ]
    assert survival_rate(heals, 30, now)["rate"] == round(1 / 3, 4)
    assert revert_rate(heals)["rate"] == round(1 / 3, 4)
    assert override_rate(heals)["rate"] == round(1 / 3, 4)
    assert fingerprint_freshness(10.0)["fresh"] is True
    assert fingerprint_freshness(100 * 86400.0)["status"] == "stale"


def test_guard_downgrades_l3_to_l2_on_breach() -> None:
    cfg = load_config()
    assert cfg.autonomy_level == "L3"
    v = evaluate(0.5, 0.0, cfg)
    assert (v.effective_level, v.downgraded) == ("L2", True)
    assert v.alert and v.alert["severity"] == "high"


def test_guard_downgrades_on_ece_breach() -> None:
    v = evaluate(0.0, 0.9)
    assert v.downgraded and v.effective_level == "L2"


def test_guard_holds_when_healthy_and_never_rewrites_config() -> None:
    before = open("healing/policy/policy.yaml").read()
    v = evaluate(0.0, 0.0)
    assert (v.downgraded, v.effective_level) == (False, "L3")
    assert open("healing/policy/policy.yaml").read() == before
