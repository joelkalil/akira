"""Collect Python source files for developer fingerprint extractors."""

from __future__ import annotations

import ast
import fnmatch
import os
import tokenize
from pathlib import Path
from typing import Iterable

from akira.fingerprint.models import FingerprintAnalysis, SourceFile

DEFAULT_EXCLUDED_DIRS = {
    ".akira",
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "env",
    "generated",
    "node_modules",
    "site-packages",
    "venv",
}

GENERATED_FILE_SUFFIXES = (
    "_pb2.py",
    "_pb2_grpc.py",
)


def analyze_project(
    project_root: Path,
    *,
    sample_size: int = 20,
    exclude: Iterable[str] = (),
) -> FingerprintAnalysis:
    """Return sampled Python files with raw text and AST parse results."""
    root = project_root.resolve()
    files = tuple(
        _read_source_file(path, root)
        for path in collect_python_files(root, sample_size=sample_size, exclude=exclude)
    )
    return FingerprintAnalysis(project_root=root, files=files)


def collect_python_files(
    project_root: Path,
    *,
    sample_size: int = 20,
    exclude: Iterable[str] = (),
) -> tuple[Path, ...]:
    """Select up to ``sample_size`` Python files from a project."""
    root = project_root.resolve()
    if sample_size <= 0 or not root.exists():
        return ()

    exclude_patterns = tuple(_normalize_exclude_pattern(pattern) for pattern in exclude)
    files: list[Path] = []

    for directory, dirnames, filenames in os.walk(root):
        current_dir = Path(directory)
        relative_dir = current_dir.relative_to(root)
        dirnames[:] = [
            dirname
            for dirname in sorted(dirnames)
            if not _is_skipped(relative_dir / dirname, exclude_patterns)
        ]

        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue

            path = current_dir / filename
            relative_path = path.relative_to(root)
            if _is_skipped(relative_path, exclude_patterns):
                continue

            files.append(path)
            if len(files) >= sample_size:
                return tuple(files)

    return tuple(files)


def _read_source_file(path: Path, project_root: Path) -> SourceFile:
    relative_path = path.relative_to(project_root)
    read_result = _read_python_text(path)
    if isinstance(read_result, OSError):
        return SourceFile(
            path=path,
            relative_path=relative_path,
            text="",
            parse_error=f"unreadable file: {read_result.strerror or read_result}",
        )

    text = read_result

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as error:
        return SourceFile(
            path=path,
            relative_path=relative_path,
            text=text,
            parse_error=_format_syntax_error(error),
        )

    return SourceFile(path=path, relative_path=relative_path, text=text, tree=tree)


def _read_python_text(path: Path) -> str | OSError:
    try:
        with tokenize.open(path) as file:
            return file.read()
    except (OSError, SyntaxError, UnicodeDecodeError) as primary_error:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError as fallback_error:
            if isinstance(primary_error, OSError):
                return primary_error
            return fallback_error


def _format_syntax_error(error: SyntaxError) -> str:
    location = f"line {error.lineno}" if error.lineno is not None else "unknown line"
    return f"{location}: {error.msg}"


def _is_skipped(relative_path: Path, exclude_patterns: tuple[str, ...]) -> bool:
    if relative_path == Path("."):
        return False

    parts = relative_path.parts
    if any(part in DEFAULT_EXCLUDED_DIRS for part in parts):
        return True

    name = relative_path.name
    if name.endswith(GENERATED_FILE_SUFFIXES):
        return True

    relative_posix = relative_path.as_posix()
    return any(_matches_exclude(relative_posix, pattern) for pattern in exclude_patterns)


def _matches_exclude(relative_posix: str, pattern: str) -> bool:
    if not pattern:
        return False

    if any(marker in pattern for marker in "*?[]"):
        return fnmatch.fnmatch(relative_posix, pattern)

    return relative_posix == pattern or relative_posix.startswith(f"{pattern}/")


def _normalize_exclude_pattern(pattern: str) -> str:
    return pattern.strip().replace("\\", "/").strip("/")
