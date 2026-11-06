"""Workspace ingestion and archive management."""

from __future__ import annotations

import io
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

IGNORE_DIRS = {
    ".git",
    ".github",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    ".venv312",
    "venv",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "self_healing_framework.egg-info",
}

IGNORE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".exe",
    ".png",
    ".jpg",
    ".jpeg",
    ".zip",
    ".tar",
    ".gz",
}


def create_temp_workspace(prefix: str = "healing_ws_") -> Path:
    """Create an isolated temporary directory for scanning and healing."""
    temp_dir = tempfile.mkdtemp(prefix=prefix)
    return Path(temp_dir)


def extract_zip(zip_bytes: bytes, target_dir: Path) -> list[str]:
    """Extract in-memory zip bytes into target directory safely."""
    extracted_files: list[str] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for member in z.namelist():
            # Security: guard against Zip Slip directory traversal
            norm = os.path.normpath(member)
            if norm.startswith("..") or os.path.isabs(norm):
                continue
            z.extract(member, target_dir)
            extracted_files.append(member)
    return extracted_files


def copy_folder_to_workspace(source_dir: Path, target_dir: Path) -> list[str]:
    """Copy an existing local folder to an isolated workspace, filtering ignore dirs."""
    copied_files: list[str] = []
    source_dir = source_dir.resolve()
    for root, dirs, files in os.walk(source_dir):
        # Prune ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        rel_root = Path(root).relative_to(source_dir)
        dest_root = target_dir / rel_root
        dest_root.mkdir(parents=True, exist_ok=True)
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in IGNORE_EXTENSIONS:
                continue
            src_file = Path(root) / f
            dest_file = dest_root / f
            shutil.copy2(src_file, dest_file)
            copied_files.append(str(rel_root / f))
    return copied_files


def list_code_files(workspace: Path) -> list[Path]:
    """Return all source code files in the workspace (Python first)."""
    files: list[Path] = []
    for root, dirs, filenames in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext in {".py", ".json", ".yaml", ".yml", ".md", ".toml"}:
                files.append(Path(root) / f)
    return sorted(files)


def create_workspace_zip(workspace: Path) -> bytes:
    """Pack the modified workspace into an in-memory zip archive for download."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(workspace):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(workspace)
                z.write(full_path, arcname=str(rel_path))
    buf.seek(0)
    return buf.getvalue()


def cleanup_workspace(workspace: Path) -> None:
    """Safely remove a temporary workspace."""
    if workspace.exists() and workspace.is_dir():
        shutil.rmtree(workspace, ignore_errors=True)
