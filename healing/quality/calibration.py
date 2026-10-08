"""Calibration: confidence vs actual correctness (reliability curve + ECE)."""

from __future__ import annotations


def reliability_curve(pairs: list[tuple[float, bool]], bins: int = 10) -> list[dict[str, float]]:
    """Bucket confidences; per-bin mean confidence vs empirical accuracy."""
    curve: list[dict[str, float]] = []
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        in_bin = [c for p, c in pairs if (p >= lo and (p < hi or (hi == 1.0 and p <= hi)))]
        if not in_bin:
            curve.append({"bin": round(lo, 2), "confidence": 0.0, "accuracy": 0.0, "n": 0})
            continue
        probs = [p for p, _ in pairs if (p >= lo and (p < hi or (hi == 1.0 and p <= hi)))]
        curve.append(
            {
                "bin": round(lo, 2),
                "confidence": round(sum(probs) / len(probs), 4),
                "accuracy": round(sum(in_bin) / len(in_bin), 4),
                "n": len(in_bin),
            }
        )
    return curve


def expected_calibration_error(pairs: list[tuple[float, bool]], bins: int = 10) -> float:
    if not pairs:
        return 0.0
    ece = 0.0
    for row in reliability_curve(pairs, bins):
        if row["n"]:
            ece += (row["n"] / len(pairs)) * abs(row["confidence"] - row["accuracy"])
    return round(ece, 4)


def alarm_if_diverged(ece: float, limit: float) -> tuple[bool, str]:
    if ece > limit:
        return True, f"calibration diverged: ECE {ece} > limit {limit}"
    return False, ""
