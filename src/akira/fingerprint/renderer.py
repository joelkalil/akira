"""Render fingerprint analysis into durable project artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, StrictUndefined

from akira.fingerprint.models import FingerprintAnalysis, StylePattern


@dataclass(frozen=True)
class FingerprintLine:
    """A readable fingerprint assertion derived from a style pattern."""

    label: str
    value: str
    confidence: float
    samples: int


@dataclass(frozen=True)
class FingerprintSection:
    """A rendered fingerprint.md section."""

    title: str
    lines: tuple[FingerprintLine, ...]


SECTION_ORDER = (
    ("spacing", "Spacing", ("top_level_definitions", "methods", "logical_blocks", "after_imports")),
    ("comments", "Comments", ("section_separators", "inline_comment_frequency", "language", "todo_format")),
    ("structure", "Control Flow", ("early_returns", "guard_clauses", "nesting_depth", "ternary_usage")),
    ("naming", "Naming", ("functions", "variables", "classes", "constants", "private_helpers", "boolean_prefixes")),
    ("imports", "Imports", ("grouping_order", "alphabetical_order", "one_import_per_line", "wildcard_usage", "relative_imports")),
    ("typing", "Type Hints", ("signature_coverage", "return_hints", "optional_syntax", "complex_type_imports")),
    ("docstrings", "Docstrings", ("docstring_style", "public_docstrings", "class_docstrings", "private_docstring_behavior")),
    ("error_handling", "Error Handling", ("exception_specificity", "logging_on_catch", "reraising")),
    ("organization", "Organization", ("module_order", "helper_placement", "class_member_order", "main_block")),
    ("strings", "Strings", ("quote_style", "interpolation_style", "multiline_strings")),
    ("general", "General Patterns", ("function_length",)),
)

PATTERN_LABELS = {
    "after_imports": "After imports section",
    "alphabetical_order": "Alphabetical order",
    "boolean_prefixes": "Boolean variables",
    "class_docstrings": "Classes",
    "class_member_order": "Class member order",
    "classes": "Classes",
    "complex_type_imports": "Complex type imports",
    "docstring_style": "Style",
    "early_returns": "Early returns",
    "exception_specificity": "Exceptions",
    "function_length": "Function length",
    "functions": "Functions",
    "grouping_order": "Order",
    "guard_clauses": "Guard clauses",
    "helper_placement": "Helper placement",
    "inline_comment_frequency": "Inline comments",
    "interpolation_style": "Interpolation",
    "language": "Language",
    "logging_on_catch": "Logging on catch",
    "logical_blocks": "Inside functions",
    "main_block": "Main block",
    "methods": "Between methods",
    "module_order": "Module order",
    "multiline_strings": "Multi-line strings",
    "nesting_depth": "Max nesting",
    "one_import_per_line": "Style",
    "optional_syntax": "Optional style",
    "private_docstring_behavior": "Private methods",
    "private_helpers": "Private helpers",
    "public_docstrings": "Public functions",
    "quote_style": "Quotes",
    "relative_imports": "Relative imports",
    "reraising": "Re-raising",
    "return_hints": "Return types",
    "section_separators": "Section separators",
    "signature_coverage": "Coverage",
    "ternary_usage": "Ternary",
    "todo_format": "TODO format",
    "top_level_definitions": "Between top-level definitions",
    "variables": "Variables",
    "wildcard_usage": "Wildcard imports",
}

VALUE_LABELS = {
    "avoid_relative_imports": "Avoid relative imports",
    "avoid_wildcards": "Avoid wildcard imports",
    "avoids_ternary": "Avoids ternary expressions",
    "double": 'Double quotes `"`',
    "documented": "Documented",
    "f_strings": "f-strings",
    "full_signature_hints": "Full function signature hints",
    "google": "Google style",
    "hash_dash_section_separator": "`# --- Section ---`",
    "mixed_or_other": "Mixed or other",
    "low": "Low",
    "omit_private_docstrings": "Omit private docstrings",
    "PascalCase": "PascalCase",
    "pipe_union_none": "`X | None`",
    "preferred": "Preferred",
    "present": "Present",
    "rare": "Rare",
    "single": "Single quotes `'`",
    "single_leading_underscore": "Single leading underscore",
    "snake_case": "snake_case",
    "triple_double": 'Triple double quotes `"""`',
    "under_30_lines": "Prefers functions under 30 lines",
    "UPPER_SNAKE_CASE": "UPPER_SNAKE_CASE",
    "uses_ternary": "Uses ternary expressions",
}


def render_fingerprint_markdown(
    analysis: FingerprintAnalysis,
    *,
    generated_at: datetime | None = None,
    sample_size: int | None = None,
) -> str:
    """Render fingerprint.md content for a fingerprint analysis."""
    timestamp = generated_at or datetime.now(timezone.utc)
    env = Environment(
        loader=PackageLoader("akira.fingerprint", "templates"),
        autoescape=False,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,
    )
    template = env.get_template("fingerprint.md.j2")

    return template.render(
        generated_at=timestamp.replace(microsecond=0).isoformat(),
        sample_size=sample_size if sample_size is not None else len(analysis.files),
        files_analyzed=tuple(file.relative_path.as_posix() for file in analysis.files),
        confidence=analysis.confidence,
        sections=build_fingerprint_sections(analysis.patterns),
    )


def write_fingerprint_markdown(
    output_dir: Path,
    analysis: FingerprintAnalysis,
    *,
    sample_size: int | None = None,
) -> Path:
    """Create the output directory and write fingerprint.md into it."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "fingerprint.md"
    path.write_text(
        render_fingerprint_markdown(analysis, sample_size=sample_size),
        encoding="utf-8",
    )
    return path


def build_fingerprint_sections(
    patterns: tuple[StylePattern, ...],
) -> tuple[FingerprintSection, ...]:
    """Build all v1.0 fingerprint sections in a stable order."""
    by_dimension_and_name = {
        (pattern.dimension, pattern.name): pattern for pattern in patterns
    }
    sections: list[FingerprintSection] = []

    for dimension, title, names in SECTION_ORDER:
        lines: list[FingerprintLine] = []
        for name in names:
            pattern = by_dimension_and_name.get((dimension, name))
            if pattern is None and dimension == "general":
                pattern = by_dimension_and_name.get(("structure", name))
            if pattern is None:
                continue
            lines.append(_line_for_pattern(pattern))
        sections.append(FingerprintSection(title=title, lines=tuple(lines)))

    return tuple(sections)


def _line_for_pattern(pattern: StylePattern) -> FingerprintLine:
    return FingerprintLine(
        label=PATTERN_LABELS.get(pattern.name, _humanize(pattern.name)),
        value=_format_value(pattern.value),
        confidence=pattern.confidence,
        samples=pattern.samples,
    )


def _format_value(value: Any) -> str:
    if isinstance(value, tuple):
        return " -> ".join(_format_value(item) for item in value)
    if isinstance(value, list):
        return ", ".join(_format_value(item) for item in value)
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        noun = "blank line" if value == 1 else "blank lines"
        return f"{value} {noun}"
    if isinstance(value, float):
        return f"{value:.2f}"

    text = str(value)
    return VALUE_LABELS.get(text, _humanize(text))


def _humanize(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()
