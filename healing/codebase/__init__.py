"""Codebase Auto-Healing and Optimality Framework.

Provides autonomous bug detection, verification, and healing for arbitrary
codebases, along with static and dynamic performance/complexity optimization.
"""

from __future__ import annotations

from healing.codebase.healer import CodebaseHealer
from healing.codebase.llm_client import LocalLLMClient
from healing.codebase.models import (
    BugReport,
    CodePatch,
    HealingResult,
    OptimizationOpportunity,
    OptimizationResult,
    ScanResult,
)
from healing.codebase.optimizer import CodebaseOptimizer
from healing.codebase.scanner import CodebaseScanner

__all__ = [
    "BugReport",
    "CodePatch",
    "CodebaseHealer",
    "CodebaseOptimizer",
    "CodebaseScanner",
    "HealingResult",
    "LocalLLMClient",
    "OptimizationOpportunity",
    "OptimizationResult",
    "ScanResult",
]
