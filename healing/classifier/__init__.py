"""Classifier: label failures; unknown maps to escalate (fail closed)."""

from healing.classifier.rules import (
    CLASSES,
    Classification,
    FailureSignals,
    classify,
)

__all__: list[str] = ["CLASSES", "Classification", "FailureSignals", "classify"]
