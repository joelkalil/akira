"""Data models for the fingerprint analysis pipeline."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceFile:
    """A Python source file prepared for style extractors."""

    path: Path
    relative_path: Path
    text: str
    tree: ast.AST | None = None
    parse_error: str | None = None

    @property
    def parsed(self) -> bool:
        """Return whether the file was parsed successfully."""
        return self.tree is not None and self.parse_error is None


@dataclass(frozen=True)
class FingerprintAnalysis:
    """The source sample that later fingerprint extractors consume."""

    project_root: Path
    files: tuple[SourceFile, ...]

    @property
    def parsed_files(self) -> tuple[SourceFile, ...]:
        """Return files with a usable AST."""
        return tuple(file for file in self.files if file.parsed)

    @property
    def failed_files(self) -> tuple[SourceFile, ...]:
        """Return files that could not be parsed as Python."""
        return tuple(file for file in self.files if file.parse_error is not None)
