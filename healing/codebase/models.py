"""Data models for codebase scanning, bug healing, and optimization."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BugReport(BaseModel):
    """Details of a detected bug or defect in the codebase."""

    bug_id: str
    file_path: str
    line_number: int | None = None
    bug_type: (
        str  # syntax_error, runtime_error, test_failure, type_error, logic_error, resource_leak
    )
    severity: str = "high"  # high, medium, low
    description: str
    stack_trace: str | None = None
    failing_test: str | None = None
    culprit_code: str | None = None


class OptimizationOpportunity(BaseModel):
    """Details of an identified performance or complexity bottleneck."""

    opt_id: str
    file_path: str
    line_start: int
    line_end: int
    # algorithmic_complexity, inefficient_lookup, redundant_computation,
    # dead_code, string_concat, resource_management
    category: str
    current_complexity: str = "O(N^2)"
    projected_complexity: str = "O(N)"
    description: str
    suggested_improvement: str
    estimated_speedup: str = "2x - 10x"
    code_snippet: str | None = None


class CodePatch(BaseModel):
    """Unified code patch representing a bug fix or optimization transformation."""

    patch_id: str
    file_path: str
    original_code: str
    modified_code: str
    diff: str
    explanation: str
    target_id: str  # bug_id or opt_id
    applied: bool = False
    verification_status: str = "unverified"  # verified, failed_verification, unverified
    error_message: str | None = None


class MetricsSnapshot(BaseModel):
    """Quantitative code quality and complexity metrics."""

    total_files: int = 0
    total_lines: int = 0
    cyclomatic_complexity: float = 0.0
    maintainability_index: float = 100.0
    detected_smells: int = 0


class ScanResult(BaseModel):
    """Overall outcome of scanning a codebase."""

    project_name: str
    workspace_path: str
    total_files: int
    total_lines: int
    bugs: list[BugReport] = Field(default_factory=list)
    optimizations: list[OptimizationOpportunity] = Field(default_factory=list)
    metrics: MetricsSnapshot = Field(default_factory=MetricsSnapshot)
    test_suite_detected: bool = False
    tests_passed: int = 0
    tests_failed: int = 0


class HealingResult(BaseModel):
    """Outcome of attempting to auto-heal detected bugs."""

    project_name: str
    patches: list[CodePatch] = Field(default_factory=list)
    fixed_bugs: list[str] = Field(default_factory=list)
    failed_bugs: list[str] = Field(default_factory=list)
    sandbox_verified: bool = False
    total_attempted: int = 0
    total_resolved: int = 0
    explanation_record: dict[str, Any] = Field(default_factory=dict)


class BenchmarkComparison(BaseModel):
    """Execution timing and resource profiling comparison."""

    benchmark_name: str
    before_ms: float
    after_ms: float
    speedup_factor: float
    memory_before_kb: float = 0.0
    memory_after_kb: float = 0.0
    memory_reduction_pct: float = 0.0


class OptimizationResult(BaseModel):
    """Outcome of running the code optimization engine."""

    project_name: str
    patches: list[CodePatch] = Field(default_factory=list)
    applied_count: int = 0
    benchmarks: list[BenchmarkComparison] = Field(default_factory=list)
    overall_speedup: float = 1.0
    overall_memory_reduction_pct: float = 0.0
    complexity_before: float = 0.0
    complexity_after: float = 0.0
    verified_safe: bool = True
    explanation: str = ""
