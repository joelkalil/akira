"""Shared helpers for fingerprint extractor implementations."""

from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, TypeVar

from akira.fingerprint.models import StylePattern

T = TypeVar("T")

SNAKE_CASE_RE = re.compile(r"^_?[a-z][a-z0-9_]*_?$|^__$")
PASCAL_CASE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
UPPER_SNAKE_CASE_RE = re.compile(r"^_?[A-Z][A-Z0-9_]*_?$")
BOOLEAN_PREFIXES = ("is_", "has_", "can_", "should_", "use_", "enable_")


def clamp_confidence(value: float) -> float:
    """Keep confidence values stable and renderer-friendly."""
    return round(max(0.0, min(1.0, value)), 2)


def modal_pattern(values: Iterable[T]) -> tuple[T | None, float, int]:
    """Return the dominant value, its share, and the number of observations."""
    items = list(values)
    if not items:
        return None, 0.0, 0

    counter = Counter(items)
    value, count = sorted(counter.items(), key=lambda item: (-item[1], str(item[0])))[0]
    return value, count / len(items), len(items)


def make_pattern(
    *,
    dimension: str,
    name: str,
    value: object,
    confidence: float,
    samples: int,
    description: str,
    evidence: dict[str, object] | None = None,
) -> StylePattern:
    """Create a normalized style pattern result."""
    return StylePattern(
        dimension=dimension,
        name=name,
        value=value,
        confidence=clamp_confidence(confidence),
        samples=samples,
        description=description,
        evidence=evidence or {},
    )


def blank_lines_before(lines: list[str], line_number: int) -> int:
    """Count blank lines immediately before a 1-based line number."""
    index = line_number - 2
    count = 0
    while index >= 0 and not lines[index].strip():
        count += 1
        index -= 1
    return count


def blank_lines_between(lines: list[str], start_line: int, end_line: int) -> int:
    """Count blank physical lines between two 1-based source positions."""
    if end_line <= start_line:
        return 0
    return sum(1 for line in lines[start_line:end_line - 1] if not line.strip())


def iter_function_defs(tree: ast.AST) -> Iterable[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Yield all function definitions in deterministic AST order."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            yield node


def module_name_from_path(relative_path: Path) -> str:
    """Infer the most useful local import root from a project-relative path."""
    parts = relative_path.with_suffix("").parts
    if "src" in parts:
        src_index = parts.index("src")
        if src_index + 1 < len(parts):
            return parts[src_index + 1]
    return parts[0] if parts else ""
