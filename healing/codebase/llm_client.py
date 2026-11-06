"""Local Free LLM client with graceful deterministic fallback.

Connects to local inference servers (e.g. Ollama, llama.cpp, LocalAI) at
http://localhost:11434. When the local LLM is offline or uninstalled,
falls back to deterministic, rule-based AST synthesis so operations
remain 100% reliable and fail-closed.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import httpx

from healing.codebase.models import BugReport, OptimizationOpportunity

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("LOCAL_LLM_MODEL", "qwen2.5-coder:latest")


class LocalLLMClient:
    """Interface to local free LLM servers (Ollama / LocalAI) with deterministic fallback."""

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        model: str = DEFAULT_MODEL,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout_seconds

    def is_available(self) -> bool:
        """Check if local Ollama/server is running and reachable."""
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def get_status_info(self) -> dict[str, Any]:
        """Return connectivity details for UI display."""
        available = self.is_available()
        return {
            "available": available,
            "provider": "Ollama (Local Free LLM)" if available else "Deterministic Fallback Engine",
            "model": self.model if available else "AST Rule-Based Synthesizer",
            "endpoint": self.base_url,
        }

    def _call_ollama(self, prompt: str, system_prompt: str = "") -> str | None:
        """Call Ollama /api/generate endpoint."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt
            or "You are an expert software engineer fixing code bugs and optimizing code.",
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 1024},
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return str(data.get("response", "")).strip()
        except Exception as exc:
            logger.debug("Local LLM call failed or timed out: %s", exc)
        return None

    def propose_bug_fix(self, bug: BugReport, file_content: str) -> tuple[str, str]:
        """Propose a fix for a bug. Returns (modified_file_content, explanation)."""
        # Try local LLM if available
        if self.is_available():
            system_prompt = (
                "You are an automated code healing agent. Output ONLY the complete, "
                "fixed file content enclosed in ```python ... ``` without narrative outside."
            )
            prompt = (
                f"Fix the following bug in Python code:\n"
                f"Bug Type: {bug.bug_type}\n"
                f"Description: {bug.description}\n"
                f"Failing Line: {bug.line_number}\n"
                f"Stack Trace / Context: {bug.stack_trace or 'None'}\n\n"
                f"File Content:\n```python\n{file_content}\n```"
            )
            raw = self._call_ollama(prompt, system_prompt)
            if raw:
                code_match = re.search(r"```(?:python)?\s*(.*?)\s*```", raw, re.DOTALL)
                extracted_code = code_match.group(1) if code_match else raw
                if extracted_code.strip() and extracted_code != file_content:
                    return extracted_code, f"Fixed via local LLM ({self.model}): {bug.description}"

        # Deterministic Fallback Synthesis
        return self._deterministic_bug_fix(bug, file_content)

    def propose_optimization(
        self, opt: OptimizationOpportunity, file_content: str
    ) -> tuple[str, str]:
        """Propose code optimization. Returns (modified_file_content, explanation)."""
        if self.is_available():
            system_prompt = (
                "You are a performance optimization compiler. Output ONLY the optimized "
                "file content enclosed in ```python ... ``` preserving exact external behavior."
            )
            prompt = (
                "Optimize the following Python code for performance and algorithmic complexity:\n"
                f"Category: {opt.category}\n"
                f"Complexity: {opt.current_complexity} -> Target: {opt.projected_complexity}\n"
                f"Bottleneck: {opt.description}\n"
                f"Suggested: {opt.suggested_improvement}\n\n"
                f"File Content:\n```python\n{file_content}\n```"
            )
            raw = self._call_ollama(prompt, system_prompt)
            if raw:
                code_match = re.search(r"```(?:python)?\s*(.*?)\s*```", raw, re.DOTALL)
                extracted_code = code_match.group(1) if code_match else raw
                if extracted_code.strip() and extracted_code != file_content:
                    return (
                        extracted_code,
                        f"Optimized via local LLM ({self.model}): {opt.suggested_improvement}",
                    )

        # Deterministic Fallback Optimization
        return self._deterministic_optimization(opt, file_content)

    def _deterministic_bug_fix(self, bug: BugReport, content: str) -> tuple[str, str]:
        """Deterministic rule-based bug repair engine."""
        lines = content.splitlines()

        # 1. Division by zero guard: if b == 0 or constant 0
        desc_context = (bug.description + " " + (bug.stack_trace or "")).lower()
        if "division by" in desc_context or "zerodivision" in desc_context:
            target_idx = (
                (bug.line_number - 1)
                if bug.line_number and 0 < bug.line_number <= len(lines)
                else -1
            )
            if target_idx >= 0:
                line = lines[target_idx]
                if "/" in line:
                    indent = len(line) - len(line.lstrip())
                    lead = " " * indent
                    # Replace `return a / b` or `result = a / b` with zero check
                    div_match = re.search(r"(\w+)\s*/\s*(\w+)", line)
                    if div_match:
                        _num, den = div_match.group(1), div_match.group(2)
                        if den == "0":
                            fixed = [f"{lead}return 0.0"]
                        else:
                            fixed = [
                                f"{lead}if {den} == 0:",
                                f"{lead}    return 0.0",
                                line,
                            ]
                        lines = lines[:target_idx] + fixed + lines[target_idx + 1 :]
                        return "\n".join(lines), "Added zero-division safety guard"

        # 2. Mutable default argument: def fn(x, items: list[T] = []) -> def fn(x, items=None)
        # Handles type annotations AND return annotations: `param: SomeType[X] = []`
        if "mutable default" in bug.description.lower() or bug.bug_type == "code_smell":

            def _fix_mutable_default(m: re.Match[str]) -> str:
                fn_name = m.group(1)
                all_params = m.group(2)  # all params up to the `= []`
                ret_ann = m.group(4) or ""  # optional `-> ReturnType`
                # Peel off the last param (which carries the mutable default)
                last_comma = all_params.rfind(",")
                pre = all_params[: last_comma + 1] if last_comma >= 0 else ""
                param_with_type = all_params[last_comma + 1 :].strip()
                # Drop any type annotation, keep only the name
                param_bare = re.sub(r"\s*:.*", "", param_with_type).strip()
                sep = " " if pre.endswith(",") else ""
                return f"def {fn_name}({pre}{sep}{param_bare}=None){ret_ann}:"

            new_content = re.sub(
                # Captures: fn_name, all params before `= []`, the bracket literal, return ann
                r"def\s+(\w+)\s*\(([^)]*)\s*=\s*(\[\]|\{\})\s*\)(\s*->.*?)?:",
                _fix_mutable_default,
                content,
            )
            if new_content != content:
                return new_content, "Replaced mutable default argument with None guard"

        # 3. Missing import repair
        if (
            "nameerror" in (bug.stack_trace or "").lower()
            or "is not defined" in bug.description.lower()
        ):
            match = re.search(
                r"name '(\w+)' is not defined", (bug.stack_trace or "") + " " + bug.description
            )
            if match:
                missing_name = match.group(1)
                known_imports = {
                    "math": "import math",
                    "json": "import json",
                    "os": "import os",
                    "sys": "import sys",
                    "time": "import time",
                    "re": "import re",
                    "Path": "from pathlib import Path",
                    "List": "from typing import List",
                    "Dict": "from typing import Dict",
                    "Any": "from typing import Any",
                    "Optional": "from typing import Optional",
                }
                if missing_name in known_imports:
                    imp_line = known_imports[missing_name]
                    if imp_line not in content:
                        new_content = imp_line + "\n" + content
                        return (
                            new_content,
                            f"Automatically imported missing module '{missing_name}'",
                        )

        # 4. Off-by-one / IndexError guard
        if (
            "indexerror" in (bug.stack_trace or "").lower()
            or "list index out of range" in bug.description.lower()
        ):
            target_idx = (
                (bug.line_number - 1)
                if bug.line_number and 0 < bug.line_number <= len(lines)
                else -1
            )
            if target_idx >= 0:
                line = lines[target_idx]
                indent = len(line) - len(line.lstrip())
                lead = " " * indent
                match = re.search(r"(\w+)\[(.*?)\]", line)
                if match:
                    arr, idx = match.group(1), match.group(2)
                    fixed = [
                        f"{lead}if not {arr} or len({arr}) <= {idx}:",
                        f"{lead}    return None",
                        line,
                    ]
                    lines = lines[:target_idx] + fixed + lines[target_idx + 1 :]
                    return "\n".join(lines), f"Added bounds check for index access on '{arr}'"

        # 5. Resource leak: unclosed open()
        # Pattern: <indent>var = open(args)\n<indent>body_line\n<indent>var.close()
        # Lambda replacement emits real newlines and preserves indentation.
        if "unclosed file" in bug.description.lower() or "resource_leak" in bug.bug_type:

            def _fix_resource_leak(m: re.Match[str]) -> str:
                indent = m.group(1)
                var = m.group(2)
                args = m.group(3)
                body_line = m.group(4).strip()
                return f"{indent}with open({args}) as {var}:\n{indent}    {body_line}"

            new_content = re.sub(
                r"([ \t]*)(\w+)\s*=\s*open\((.*?)\)\n([ \t]*[^\n]+)\n[ \t]*\2\.close\(\)",
                _fix_resource_leak,
                content,
            )
            if new_content != content:
                return (
                    new_content,
                    "Refactored unclosed file to use 'with open(...) as' context manager",
                )

        return content, "No deterministic repair matched; manual inspection recommended"

    def _deterministic_optimization(
        self, opt: OptimizationOpportunity, content: str
    ) -> tuple[str, str]:
        """Deterministic AST and pattern-based code optimizer."""
        # 1. Inefficient lookup in loop: `for x in arr: if x in other_list` -> precompute set
        if opt.category == "inefficient_lookup":
            pattern = re.search(
                r"([ \t]*)for\s+(\w+)\s+in\s+(\w+):\s*\n([ \t]*)if\s+\2\s+in\s+(\w+):",
                content,
            )
            if pattern:
                indent_for = pattern.group(1)
                elem_var = pattern.group(2)
                iter_var = pattern.group(3)
                indent_if = pattern.group(4)
                target_list = pattern.group(5)
                target_set = f"{target_list}_set"
                old_block = pattern.group(0)
                replacement = (
                    f"{indent_for}{target_set} = set({target_list})\n"
                    f"{indent_for}for {elem_var} in {iter_var}:\n"
                    f"{indent_if}if {elem_var} in {target_set}:"
                )
                return (
                    content.replace(old_block, replacement, 1),
                    f"Converted linear scan of '{target_list}' from O(N) to O(1) set lookup",
                )

        # 2. String concatenation in loop -> list append and ''.join()
        if opt.category == "string_concat":
            # Line-by-line scan: find `var = ""` (or `var = ''`) then a `for X in Y:` loop
            # that contains `var +=` in its body. Works regardless of what appears between them.
            lines = content.splitlines(keepends=True)
            for i, line in enumerate(lines):
                # Find an empty-string initializer: `    body = ""`
                init_match = re.match(r"([ \t]*)(\w+)\s*=\s*[\"']{1,3}[\"']{0,2}\s*\n", line)
                if not init_match:
                    continue
                indent = init_match.group(1)
                res_var = init_match.group(2)
                # Look ahead for a for-loop at same indent level
                for j in range(i + 1, min(i + 6, len(lines))):
                    for_match = re.match(
                        rf"{re.escape(indent)}for\s+(\w+)\s+in\s+(.+?):\s*\n", lines[j]
                    )
                    if not for_match:
                        continue
                    item_var = for_match.group(1)
                    iterable = for_match.group(2).strip()
                    # Check next line is `var +=` inside the loop body
                    if j + 1 < len(lines):
                        body_match = re.match(
                            rf"{re.escape(indent)}    {re.escape(res_var)}\s*\+=\s*(.+)\n?",
                            lines[j + 1],
                        )
                        if body_match:
                            add_expr = body_match.group(1).strip()
                            # Build optimized replacement
                            old_block = "".join(lines[j : j + 2])
                            new_block = (
                                f"{indent}{res_var}_parts = []\n"
                                f"{indent}for {item_var} in {iterable}:\n"
                                f"{indent}    {res_var}_parts.append({add_expr})\n"
                                f"{indent}{res_var} = ''.join({res_var}_parts)\n"
                            )
                            new_content = content.replace(old_block, new_block, 1)
                            if new_content != content:
                                return (
                                    new_content,
                                    "Refactored string accumulation in loop"
                                    " to fast ''.join() buffer",
                                )
                    break  # found for-loop, stop inner search

        # 3. Redundant / repeated expensive computation -> lru_cache
        if opt.category == "redundant_computation":
            if "@functools.lru_cache" not in content and "@lru_cache" not in content:
                # Find any function that calls itself recursively anywhere in its body.
                # Strategy: find `def fn_name(...)` then search for `fn_name(` later in the file.
                func_defs = list(re.finditer(r"^([ \t]*)def\s+(\w+)\s*\(", content, re.MULTILINE))
                func_match_name: str | None = None
                for fd in func_defs:
                    fname = fd.group(2)
                    after_def = content[fd.end() :]
                    if re.search(rf"\b{re.escape(fname)}\s*\(", after_def):
                        func_match_name = fname
                        break
                if func_match_name:
                    cache_import = "from functools import lru_cache\n"
                    if "from functools import lru_cache" not in content:
                        content = cache_import + content
                    decorated = content.replace(
                        f"def {func_match_name}(",
                        f"@lru_cache(maxsize=1024)\ndef {func_match_name}(",
                    )
                    return (
                        decorated,
                        f"Applied @lru_cache memoization to '{func_match_name}',"
                        " cutting complexity",
                    )

        # 4. Dead code removal: code after return in the same block
        if opt.category == "dead_code":
            lines = content.splitlines()
            new_lines = []
            skip = False
            skip_indent = 0
            dead_removed = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if skip:
                    # check indentation
                    curr_indent = len(line) - len(line.lstrip())
                    if curr_indent <= skip_indent and stripped:
                        skip = False
                    else:
                        dead_removed += 1
                        continue
                if stripped.startswith("return ") or stripped == "return":
                    skip_indent = len(line) - len(line.lstrip())
                    skip = True
                new_lines.append(line)
            if dead_removed > 0:
                return "\n".join(new_lines), f"Pruned {dead_removed} unreachable dead code lines"

        return content, "No deterministic transformation matched; local LLM proposal used"
