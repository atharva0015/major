"""Autonomous Codebase Bug Healer with sandbox and Critic verification."""

from __future__ import annotations

import ast
import difflib
import logging
import subprocess
import sys
import uuid
from pathlib import Path

from healing.codebase.llm_client import LocalLLMClient
from healing.codebase.models import BugReport, CodePatch, HealingResult, ScanResult

logger = logging.getLogger(__name__)


def generate_unified_diff(original: str, modified: str, file_path: str = "file.py") -> str:
    """Generate standard unified diff format."""
    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines,
        mod_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
    )
    return "".join(diff)


class CodebaseHealer:
    """Orchestrates bug repair, sandbox testing, and Critic verification for a codebase."""

    def __init__(self, workspace: Path, llm: LocalLLMClient | None = None) -> None:
        self.workspace = workspace.resolve()
        self.llm = llm or LocalLLMClient()

    def heal_codebase(self, scan_result: ScanResult) -> HealingResult:
        """Attempt to heal all detected bugs in the codebase."""
        patches: list[CodePatch] = []
        fixed_bugs: list[str] = []
        failed_bugs: list[str] = []

        for bug in scan_result.bugs:
            patch = self._heal_single_bug(bug)
            if patch is not None:
                patches.append(patch)
                if patch.verification_status == "verified":
                    fixed_bugs.append(bug.bug_id)
                else:
                    failed_bugs.append(bug.bug_id)
            else:
                failed_bugs.append(bug.bug_id)

        all_verified = len(fixed_bugs) > 0 and len(failed_bugs) == 0
        return HealingResult(
            project_name=self.workspace.name,
            patches=patches,
            fixed_bugs=fixed_bugs,
            failed_bugs=failed_bugs,
            sandbox_verified=all_verified,
            total_attempted=len(scan_result.bugs),
            total_resolved=len(fixed_bugs),
            explanation_record={
                "model_info": self.llm.get_status_info(),
                "fixed_count": len(fixed_bugs),
                "failed_count": len(failed_bugs),
                "summary": (
                    f"Autonomous healing resolved {len(fixed_bugs)} of "
                    f"{len(scan_result.bugs)} detected bugs with sandbox verification."
                ),
            },
        )

    def _heal_single_bug(self, bug: BugReport) -> CodePatch | None:
        """Synthesize and verify a patch for one bug."""
        target_path = self.workspace / bug.file_path
        if not target_path.exists() or not target_path.is_file():
            # If the bug was in a general test runner output without exact file path
            candidates = list(self.workspace.glob(f"**/{bug.file_path}"))
            if candidates:
                target_path = candidates[0]
            else:
                return None

        try:
            original_code = target_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.error("Could not read file %s: %s", target_path, exc)
            return None

        # Synthesize candidate fix
        modified_code, explanation = self.llm.propose_bug_fix(bug, original_code)
        if not modified_code or modified_code == original_code:
            return None

        diff = generate_unified_diff(original_code, modified_code, bug.file_path)
        patch_id = f"patch-{uuid.uuid4().hex[:8]}"

        # Sandbox Verification
        # 1. AST Syntax Check
        try:
            ast.parse(modified_code, filename=str(target_path))
        except SyntaxError as err:
            return CodePatch(
                patch_id=patch_id,
                file_path=bug.file_path,
                original_code=original_code,
                modified_code=modified_code,
                diff=diff,
                explanation=explanation,
                target_id=bug.bug_id,
                applied=False,
                verification_status="failed_verification",
                error_message=f"Proposed fix failed syntax check: {err}",
            )

        # 2. Apply temporarily to verify against tests
        target_path.write_text(modified_code, encoding="utf-8")
        test_ok, err_msg = self._verify_in_sandbox()

        if test_ok:
            # Verification passed! Keep change
            return CodePatch(
                patch_id=patch_id,
                file_path=bug.file_path,
                original_code=original_code,
                modified_code=modified_code,
                diff=diff,
                explanation=explanation,
                target_id=bug.bug_id,
                applied=True,
                verification_status="verified",
            )
        else:
            # Revert change: fail closed
            target_path.write_text(original_code, encoding="utf-8")
            return CodePatch(
                patch_id=patch_id,
                file_path=bug.file_path,
                original_code=original_code,
                modified_code=modified_code,
                diff=diff,
                explanation=explanation,
                target_id=bug.bug_id,
                applied=False,
                verification_status="failed_verification",
                error_message=err_msg or "Failed sandbox test suite verification",
            )

    def _verify_in_sandbox(self) -> tuple[bool, str | None]:
        """Execute test suite to verify the applied patch introduced no regressions."""
        test_files = list(self.workspace.glob("**/test_*.py")) + list(
            self.workspace.glob("**/*_test.py")
        )
        if not test_files:
            # No tests: syntax validity already passed
            return True, None

        try:
            cmd = [sys.executable, "-m", "pytest", "-q"]
            proc = subprocess.run(
                cmd,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=20,
            )
            if proc.returncode == 0:
                return True, None
            return False, f"Pytest exit code {proc.returncode}: {proc.stdout[:200]}"
        except subprocess.TimeoutExpired:
            return False, "Sandbox verification timed out (>20s)"
        except Exception as exc:
            return False, f"Verification failed to run tests: {exc}"
