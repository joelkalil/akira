"""
Data models for the fingerprint analysis pipeline.
"""

# Standard Libraries
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceFile:
    """
    A Python source file prepared for style extractors.
    """

    path: Path

    relative_path: Path

    text: str

    tree: ast.AST | None = None

    parse_error: str | None = None

    @property
    def parsed(self) -> bool:
        """
        Return whether the file was parsed successfully.

        Returns
        -------
        bool
            The result of the operation.
        """

        return self.tree is not None and self.parse_error is None


@dataclass(frozen=True)
class StylePattern:
    """
    A structured style signal extracted from sampled source files.
    """

    dimension: str

    name: str

    value: object

    confidence: float

    samples: int

    description: str

    evidence: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class FingerprintAnalysis:
    """
    The source sample that later fingerprint extractors consume.
    """

    project_root: Path

    files: tuple[SourceFile, ...]

    patterns: tuple[StylePattern, ...] = ()

    @property
    def parsed_files(self) -> tuple[SourceFile, ...]:
        """
        Return files with a usable AST.

        Returns
        -------
        tuple[SourceFile, ...]
            The result of the operation.
        """

        return tuple(file for file in self.files if file.parsed)

    @property
    def failed_files(self) -> tuple[SourceFile, ...]:
        """
        Return files that could not be parsed as Python.

        Returns
        -------
        tuple[SourceFile, ...]
            The result of the operation.
        """

        return tuple(file for file in self.files if file.parse_error is not None)

    @property
    def confidence(self) -> float:
        """
        Return the average confidence across extracted patterns.

        Returns
        -------
        float
            The result of the operation.
        """

        if not self.patterns:
            return 0.0

        return round(
            sum(pattern.confidence for pattern in self.patterns) / len(self.patterns),
            2,
        )
