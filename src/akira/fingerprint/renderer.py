"""
Render fingerprint analysis into durable project artifacts.
"""

# Standard Libraries
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Third-Party Libraries
from jinja2 import Environment, PackageLoader, StrictUndefined

# Local Libraries
from akira.fingerprint.models import FingerprintAnalysis, StylePattern

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class FingerprintLine:
    """
    A readable fingerprint assertion derived from a style pattern.
    """

    label: str

    value: str

    confidence: float

    samples: int


@dataclass(frozen=True)
class FingerprintSection:
    """
    A rendered fingerprint.md section.
    """

    title: str

    lines: tuple[FingerprintLine, ...]


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

SECTION_ORDER = (
    (
        "spacing",
        "Spacing",
        ("top_level_definitions", "methods", "logical_blocks", "after_imports"),
    ),
    (
        "comments",
        "Comments",
        ("section_separators", "inline_comment_frequency", "language", "todo_format"),
    ),
    (
        "structure",
        "Control Flow",
        ("early_returns", "guard_clauses", "nesting_depth", "ternary_usage"),
    ),
    (
        "naming",
        "Naming",
        (
            "functions",
            "variables",
            "classes",
            "constants",
            "private_helpers",
            "boolean_prefixes",
        ),
    ),
    (
        "imports",
        "Imports",
        (
            "grouping_order",
            "alphabetical_order",
            "one_import_per_line",
            "wildcard_usage",
            "relative_imports",
        ),
    ),
    (
        "typing",
        "Type Hints",
        (
            "signature_coverage",
            "return_hints",
            "optional_syntax",
            "complex_type_imports",
        ),
    ),
    (
        "docstrings",
        "Docstrings",
        (
            "docstring_style",
            "public_docstrings",
            "class_docstrings",
            "function_docstrings",
            "private_docstring_behavior",
        ),
    ),
    (
        "error_handling",
        "Error Handling",
        ("exception_specificity", "logging_on_catch", "reraising"),
    ),
    (
        "organization",
        "Organization",
        ("module_order", "helper_placement", "class_member_order", "main_block"),
    ),
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
    "function_docstrings": "Functions",
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
    "sparse": "Sparse",
    "specific_exceptions": "Specific exceptions",
    "snake_case": "snake_case",
    "triple_double": 'Triple double quotes `"""`',
    "under_30_lines": "Prefers functions under 30 lines",
    "UPPER_SNAKE_CASE": "UPPER_SNAKE_CASE",
    "uses_ternary": "Uses ternary expressions",
    "logs_caught_exceptions": "Logs caught exceptions",
    "reraises_after_catch": "Re-raises after catch",
}


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def render_fingerprint_markdown(
    analysis: FingerprintAnalysis,
    *,
    generated_at: datetime | None = None,
    sample_size: int | None = None,
) -> str:
    """
    Render fingerprint.md content for a fingerprint analysis.

    Parameters
    ----------
    analysis : FingerprintAnalysis
        The analysis value.
    generated_at : datetime | None
        The generated at value.
    sample_size : int | None
        The sample size value.

    Returns
    -------
    str
        The result of the operation.
    """

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
    """
    Create the output directory and write fingerprint.md into it.

    Parameters
    ----------
    output_dir : Path
        The output dir value.
    analysis : FingerprintAnalysis
        The analysis value.
    sample_size : int | None
        The sample size value.

    Returns
    -------
    Path
        The result of the operation.
    """

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
    """
    Build all v1.0 fingerprint sections in a stable order.

    Parameters
    ----------
    patterns : tuple[StylePattern, ...]
        The patterns value.

    Returns
    -------
    tuple[FingerprintSection, ...]
        The result of the operation.
    """

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


def format_fingerprint_value(value: Any) -> str:
    """
    Format a structured fingerprint value for human-readable Markdown.

    Parameters
    ----------
    value : Any
        The value value.

    Returns
    -------
    str
        The result of the operation.
    """

    if isinstance(value, tuple):
        return " -> ".join(format_fingerprint_value(item) for item in value)

    if isinstance(value, list):
        return ", ".join(format_fingerprint_value(item) for item in value)

    if isinstance(value, bool):
        return "yes" if value else "no"

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        return f"{value:.2f}"

    text = str(value)

    return VALUE_LABELS.get(text, text)


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _line_for_pattern(pattern: StylePattern) -> FingerprintLine:
    """
    Convert a style pattern into a rendered fingerprint line.

    Parameters
    ----------
    pattern : StylePattern
        The pattern value.

    Returns
    -------
    FingerprintLine
        The result of the operation.
    """

    return FingerprintLine(
        label=PATTERN_LABELS.get(pattern.name, _humanize_label(pattern.name)),
        value=_format_value(pattern),
        confidence=pattern.confidence,
        samples=pattern.samples,
    )


def _format_value(pattern: StylePattern) -> str:
    """
    Format a style pattern value for human-readable output.

    Parameters
    ----------
    pattern : StylePattern
        The pattern value.

    Returns
    -------
    str
        The result of the operation.
    """

    if isinstance(pattern.value, int) and pattern.dimension == "spacing":
        noun = "blank line" if pattern.value == 1 else "blank lines"

        return f"{pattern.value} {noun}"

    if pattern.name == "nesting_depth" and isinstance(pattern.value, int):
        noun = "level" if pattern.value == 1 else "levels"

        return f"{pattern.value} {noun}"

    return _format_raw_value(pattern.value)


def _format_raw_value(value: Any) -> str:
    """
    Format a raw fingerprint value for display.

    Parameters
    ----------
    value : Any
        The value value.

    Returns
    -------
    str
        The result of the operation.
    """

    return format_fingerprint_value(value)


def _humanize_label(value: str) -> str:
    """
    Convert an internal pattern name into a display label.

    Parameters
    ----------
    value : str
        The value value.

    Returns
    -------
    str
        The result of the operation.
    """

    return value.replace("_", " ").replace("-", " ").title()
