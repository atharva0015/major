"""Comprehensive static and dynamic codebase scanner.

Detects syntax errors, static bugs, failing tests, resource leaks,
cyclomatic complexity bottlenecks, and performance anti-patterns.
"""

from __future__ import annotations

import ast
import math
import re
import subprocess
import sys
import uuid
from pathlib import Path

from healing.codebase.ingest import list_code_files
from healing.codebase.models import (
    BugReport,
    MetricsSnapshot,
    OptimizationOpportunity,
    ScanResult,
)


class CodebaseScanner:
    """Scans codebases for defects, failing tests, and optimization opportunities."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()

    def scan(self) -> ScanResult:
        """Execute full scan: syntax, static bugs, test suites, and performance profiling."""
        files = list_code_files(self.workspace)
        bugs: list[BugReport] = []
        optimizations: list[OptimizationOpportunity] = []
        total_lines = 0
        total_complexity = 0.0

        for file_path in files:
            if file_path.suffix == ".py":
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                file_lines = len(content.splitlines())
                total_lines += file_lines

                # 1. Syntax check
                tree = None
                try:
                    tree = ast.parse(content, filename=str(file_path))
                except SyntaxError as err:
                    bugs.append(
                        BugReport(
                            bug_id=f"bug-{uuid.uuid4().hex[:8]}",
                            file_path=str(file_path.relative_to(self.workspace)),
                            line_number=err.lineno,
                            bug_type="syntax_error",
                            severity="high",
                            description=f"SyntaxError: {err.msg}",
                            stack_trace=f"Line {err.lineno}, offset {err.offset}: {err.text or ''}",
                            culprit_code=err.text,
                        )
                    )
                    continue

                if tree:
                    # 2. Static bug analysis
                    file_bugs = self._analyze_ast_bugs(tree, file_path, content)
                    bugs.extend(file_bugs)

                    # 3. Optimality & performance analysis
                    file_opts, complexity = self._analyze_ast_optimizations(
                        tree, file_path, content
                    )
                    optimizations.extend(file_opts)
                    total_complexity += complexity

        # 4. Dynamic test suite run
        test_detected, passed, failed, test_bugs = self._run_test_suite()
        bugs.extend(test_bugs)

        # 5. Calculate maintainability index
        num_py_files = max(1, sum(1 for f in files if f.suffix == ".py"))
        avg_complexity = total_complexity / num_py_files
        maintainability = self._calc_maintainability_index(total_lines, avg_complexity)

        metrics = MetricsSnapshot(
            total_files=len(files),
            total_lines=total_lines,
            cyclomatic_complexity=round(avg_complexity, 2),
            maintainability_index=round(maintainability, 1),
            detected_smells=len(bugs) + len(optimizations),
        )

        return ScanResult(
            project_name=self.workspace.name,
            workspace_path=str(self.workspace),
            total_files=len(files),
            total_lines=total_lines,
            bugs=bugs,
            optimizations=optimizations,
            metrics=metrics,
            test_suite_detected=test_detected,
            tests_passed=passed,
            tests_failed=failed,
        )

    def _analyze_ast_bugs(self, tree: ast.AST, file_path: Path, content: str) -> list[BugReport]:
        """Detect static bugs, anti-patterns, and resource leaks via AST inspection."""
        bugs: list[BugReport] = []
        rel_path = str(file_path.relative_to(self.workspace))
        lines = content.splitlines()

        for node in ast.walk(tree):
            # A. Constant division by zero
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv)):
                if isinstance(node.right, ast.Constant) and node.right.value == 0:
                    lineno = getattr(node, "lineno", None)
                    code_snippet = lines[lineno - 1] if lineno and lineno <= len(lines) else None
                    bugs.append(
                        BugReport(
                            bug_id=f"bug-{uuid.uuid4().hex[:8]}",
                            file_path=rel_path,
                            line_number=lineno,
                            bug_type="runtime_error",
                            severity="high",
                            description="ZeroDivisionError: Division by constant zero",
                            culprit_code=code_snippet,
                        )
                    )

            # B. Mutable default arguments in function definitions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults + node.args.kw_defaults:
                    if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        lineno = getattr(node, "lineno", None)
                        bugs.append(
                            BugReport(
                                bug_id=f"bug-{uuid.uuid4().hex[:8]}",
                                file_path=rel_path,
                                line_number=lineno,
                                bug_type="logic_error",
                                severity="medium",
                                description=(
                                    f"Mutable default '{ast.unparse(default)}' in "
                                    f"function '{node.name}' retains state"
                                ),
                                culprit_code=lines[lineno - 1]
                                if lineno and lineno <= len(lines)
                                else None,
                            )
                        )

            # C. Bare except clauses catching BaseException (including KeyboardInterrupt)
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    lineno = getattr(node, "lineno", None)
                    bugs.append(
                        BugReport(
                            bug_id=f"bug-{uuid.uuid4().hex[:8]}",
                            file_path=rel_path,
                            line_number=lineno,
                            bug_type="logic_error",
                            severity="medium",
                            description=(
                                "Bare 'except:' catches system exceptions; use "
                                "'except Exception:' instead"
                            ),
                            culprit_code=lines[lineno - 1]
                            if lineno and lineno <= len(lines)
                            else None,
                        )
                    )

            # D. Unclosed file handles: assignment `f = open(...)` without context manager
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                    if node.value.func.id == "open":
                        lineno = getattr(node, "lineno", None)
                        bugs.append(
                            BugReport(
                                bug_id=f"bug-{uuid.uuid4().hex[:8]}",
                                file_path=rel_path,
                                line_number=lineno,
                                bug_type="resource_leak",
                                severity="medium",
                                description=(
                                    "Unclosed file descriptor: Use 'with open(...) as' "
                                    "context manager"
                                ),
                                culprit_code=lines[lineno - 1]
                                if lineno and lineno <= len(lines)
                                else None,
                            )
                        )

            # E. Dead code detection: statements after return/raise in same block
            if hasattr(node, "body") and isinstance(getattr(node, "body"), list):
                body = getattr(node, "body")
                for i, stmt in enumerate(body):
                    if isinstance(stmt, (ast.Return, ast.Raise)) and i < len(body) - 1:
                        next_stmt = body[i + 1]
                        lineno = getattr(next_stmt, "lineno", None)
                        bugs.append(
                            BugReport(
                                bug_id=f"bug-{uuid.uuid4().hex[:8]}",
                                file_path=rel_path,
                                line_number=lineno,
                                bug_type="logic_error",
                                severity="low",
                                description="Dead code: Unreachable statement after return/raise",
                                culprit_code=lines[lineno - 1]
                                if lineno and lineno <= len(lines)
                                else None,
                            )
                        )
                        break

        return bugs

    def _analyze_ast_optimizations(
        self, tree: ast.AST, file_path: Path, content: str
    ) -> tuple[list[OptimizationOpportunity], float]:
        """Detect algorithmic complexity bottlenecks and inefficient structures."""
        opts: list[OptimizationOpportunity] = []
        rel_path = str(file_path.relative_to(self.workspace))
        lines = content.splitlines()
        file_complexity = 1.0

        for node in ast.walk(tree):
            # Calculate cyclomatic complexity contribution
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With)):
                file_complexity += 1.0
            if isinstance(node, ast.BoolOp):
                file_complexity += len(node.values) - 1

            # A. Inefficient linear membership check inside loop (O(N) -> O(1))
            if isinstance(node, (ast.For, ast.While)):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Compare):
                        for op, comparator in zip(sub.ops, sub.comparators, strict=False):
                            if isinstance(op, ast.In) and isinstance(comparator, ast.Name):
                                lineno = getattr(sub, "lineno", getattr(node, "lineno", 1))
                                opts.append(
                                    OptimizationOpportunity(
                                        opt_id=f"opt-{uuid.uuid4().hex[:8]}",
                                        file_path=rel_path,
                                        line_start=lineno,
                                        line_end=lineno,
                                        category="inefficient_lookup",
                                        current_complexity="O(N) linear search per loop iteration",
                                        projected_complexity="O(1) hash lookup via precomputed set",
                                        description=(
                                            f"Linear membership check '{ast.unparse(sub)}' in loop."
                                        ),
                                        suggested_improvement=(
                                            f"Precompute set({comparator.id}) outside the loop."
                                        ),
                                        estimated_speedup="5x - 50x depending on collection size",
                                        code_snippet=lines[lineno - 1]
                                        if lineno <= len(lines)
                                        else None,
                                    )
                                )

            # B. Nested loops (O(N^2) or worse)
            if isinstance(node, (ast.For, ast.While)):
                for sub in node.body:
                    if isinstance(sub, (ast.For, ast.While)):
                        lineno = getattr(node, "lineno", 1)
                        end_lineno = getattr(sub, "end_lineno", lineno + 5)
                        opts.append(
                            OptimizationOpportunity(
                                opt_id=f"opt-{uuid.uuid4().hex[:8]}",
                                file_path=rel_path,
                                line_start=lineno,
                                line_end=end_lineno,
                                category="algorithmic_complexity",
                                current_complexity="O(N^2) quadratic time",
                                projected_complexity="O(N) or O(N log N)",
                                description=(
                                    "Nested loops detected. Iterating over collections inside "
                                    "another loop causes quadratic time scaling."
                                ),
                                suggested_improvement=(
                                    "Refactor using hash maps, sets, or vectorized operations."
                                ),
                                estimated_speedup="10x - 100x on larger datasets",
                                code_snippet="\n".join(
                                    lines[lineno - 1 : min(end_lineno, len(lines))]
                                ),
                            )
                        )
                        break

            # C. Inefficient string concatenation in loop (O(N^2) reallocation)
            if isinstance(node, (ast.For, ast.While)):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.AugAssign) and isinstance(sub.op, ast.Add):
                        lineno = getattr(sub, "lineno", 1)
                        opts.append(
                            OptimizationOpportunity(
                                opt_id=f"opt-{uuid.uuid4().hex[:8]}",
                                file_path=rel_path,
                                line_start=lineno,
                                line_end=lineno,
                                category="string_concat",
                                current_complexity="O(N^2) memory reallocation",
                                projected_complexity="O(N) linear buffer",
                                description=(
                                    "String concatenation '+=' inside a loop allocates new strings "
                                    "on every iteration."
                                ),
                                suggested_improvement=(
                                    "Collect parts into a list and combine with ''.join()."
                                ),
                                estimated_speedup="3x - 15x on large loops",
                                code_snippet=lines[lineno - 1] if lineno <= len(lines) else None,
                            )
                        )

            # D. Pure recursive function without memoization
            if isinstance(node, ast.FunctionDef):
                calls_self = any(
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Name)
                    and call.func.id == node.name
                    for call in ast.walk(node)
                )
                has_decorator = any("cache" in ast.unparse(d).lower() for d in node.decorator_list)
                if calls_self and not has_decorator:
                    lineno = getattr(node, "lineno", 1)
                    opts.append(
                        OptimizationOpportunity(
                            opt_id=f"opt-{uuid.uuid4().hex[:8]}",
                            file_path=rel_path,
                            line_start=lineno,
                            line_end=getattr(node, "end_lineno", lineno + 5),
                            category="redundant_computation",
                            current_complexity="O(2^N) exponential tree recursion",
                            projected_complexity="O(N) linear with memoization",
                            description=(
                                f"Recursive function '{node.name}' has no caching decorator."
                            ),
                            suggested_improvement=(
                                "Add @functools.lru_cache to eliminate recomputing subproblems."
                            ),
                            estimated_speedup="100x - 10000x for overlapping inputs",
                            code_snippet=lines[lineno - 1] if lineno <= len(lines) else None,
                        )
                    )

        return opts, file_complexity

    def _run_test_suite(self) -> tuple[bool, int, int, list[BugReport]]:
        """Run pytest in workspace if test files exist, returning pass/fail and failures."""
        test_files = list(self.workspace.glob("**/test_*.py")) + list(
            self.workspace.glob("**/*_test.py")
        )
        if not test_files:
            return False, 0, 0, []

        try:
            cmd = [sys.executable, "-m", "pytest", "-q", "--tb=short"]
            proc = subprocess.run(
                cmd,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=25,
            )
            output = proc.stdout + "\n" + proc.stderr
            return self._parse_pytest_output(output, proc.returncode)
        except subprocess.TimeoutExpired:
            return (
                True,
                0,
                1,
                [
                    BugReport(
                        bug_id=f"bug-{uuid.uuid4().hex[:8]}",
                        file_path="tests",
                        bug_type="test_failure",
                        severity="high",
                        description="Pytest execution timed out (exceeded 25s limit)",
                    )
                ],
            )
        except Exception as exc:
            return (
                True,
                0,
                0,
                [
                    BugReport(
                        bug_id=f"bug-{uuid.uuid4().hex[:8]}",
                        file_path="tests",
                        bug_type="test_failure",
                        severity="medium",
                        description=f"Could not execute pytest: {exc}",
                    )
                ],
            )

    def _parse_pytest_output(
        self, output: str, returncode: int
    ) -> tuple[bool, int, int, list[BugReport]]:
        """Extract pass/fail numbers and specific failure traces from pytest output."""
        passed = 0
        failed = 0
        bugs: list[BugReport] = []

        passed_match = re.search(r"(\d+)\s+passed", output)
        if passed_match:
            passed = int(passed_match.group(1))

        failed_match = re.search(r"(\d+)\s+failed", output)
        if failed_match:
            failed = int(failed_match.group(1))

        # Parse individual failures
        pat = r"FAILED\s+([^\s:]+)(?:::([^\s]+))?\s*-\s*(.*?)(?=\nFAILED|\n===|\Z)"
        failure_blocks = re.findall(pat, output, re.DOTALL)
        for path_match, test_name, reason in failure_blocks:
            line_no = None
            line_match = re.search(r":(\d+):", reason)
            if line_match:
                line_no = int(line_match.group(1))
            desc = f"Test failure in {test_name or path_match}: {reason.strip()[:120]}"
            bugs.append(
                BugReport(
                    bug_id=f"bug-{uuid.uuid4().hex[:8]}",
                    file_path=path_match.strip(),
                    line_number=line_no,
                    bug_type="test_failure",
                    severity="high",
                    description=desc,
                    stack_trace=reason.strip(),
                    failing_test=test_name,
                )
            )

        if returncode != 0 and not bugs and failed > 0:
            bugs.append(
                BugReport(
                    bug_id=f"bug-{uuid.uuid4().hex[:8]}",
                    file_path="tests",
                    bug_type="test_failure",
                    severity="high",
                    description="Test suite exited with failures",
                    stack_trace=output[-1000:],
                )
            )

        return True, passed, failed, bugs

    def _calc_maintainability_index(self, total_lines: int, avg_complexity: float) -> float:
        """Standard Maintainability Index calculation (0 to 100)."""
        if total_lines <= 0:
            return 100.0
        # Formula: max(0, (171 - 5.2*ln(vol) - 0.23*comp - 16.2*ln(lines)) * 100 / 171)
        volume = max(1.0, total_lines * 4.0)
        raw_mi = (
            171.0
            - 5.2 * math.log(volume)
            - 0.23 * avg_complexity
            - 16.2 * math.log(max(1.0, float(total_lines)))
        )
        normalized = max(0.0, min(100.0, raw_mi * 100.0 / 171.0))
        return normalized
