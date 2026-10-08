"""Quality: benchmarks, flake detection, and heal metrics."""

from healing.quality.autonomy_guard import GuardVerdict, evaluate
from healing.quality.calibration import (
    alarm_if_diverged,
    expected_calibration_error,
    reliability_curve,
)
from healing.quality.golden_set import load_golden, pin_golden
from healing.quality.observability import (
    observe_ack,
    observe_escalation,
    observe_heal,
    traced,
)
from healing.quality.registry import current_versions, record_versions, replay_heal
from healing.quality.survival import (
    fingerprint_freshness,
    override_rate,
    revert_rate,
    survival_rate,
)

__all__: list[str] = [
    "GuardVerdict",
    "alarm_if_diverged",
    "current_versions",
    "evaluate",
    "expected_calibration_error",
    "fingerprint_freshness",
    "load_golden",
    "observe_ack",
    "observe_escalation",
    "observe_heal",
    "override_rate",
    "pin_golden",
    "record_versions",
    "reliability_curve",
    "replay_heal",
    "revert_rate",
    "survival_rate",
    "traced",
]
