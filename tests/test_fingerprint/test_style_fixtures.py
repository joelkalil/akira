# Standard Libraries
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path

# Third-Party Libraries

# Local Libraries
from akira.detect.models import Signal, StackInfo
from akira.fingerprint import (
    analyze_project,
    fingerprint_project,
    render_fingerprint_markdown,
)
from akira.fingerprint.extractors import (
    comments,
    docstrings,
    error_handling,
    imports,
    naming,
    organization,
    spacing,
    strings,
    structure,
    typing,
)
from akira.fingerprint.models import StylePattern
from akira.skills.generator import generate_skills

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def test_style_fixtures_cover_major_fingerprint_dimensions(fixtures_dir: Path) -> None:
    analysis = fingerprint_project(fixtures_dir / "style_projects" / "consistent")

    dimensions = {pattern.dimension for pattern in analysis.patterns}

    assert dimensions >= {
        "spacing",
        "naming",
        "imports",
        "comments",
        "typing",
        "structure",
        "docstrings",
        "organization",
        "error_handling",
        "strings",
    }


def test_individual_extractors_report_expected_fixture_patterns(
    fixtures_dir: Path,
) -> None:
    analysis = analyze_project(fixtures_dir / "style_projects" / "consistent")

    expected_names_by_extractor = {
        spacing.extract: {"top_level_definitions", "methods", "logical_blocks"},
        naming.extract: {"functions", "classes", "private_helpers"},
        imports.extract: {"grouping_order", "wildcard_usage", "relative_imports"},
        comments.extract: {"section_separators", "inline_comment_frequency"},
        typing.extract: {"signature_coverage", "optional_syntax"},
        structure.extract: {"early_returns", "guard_clauses", "function_length"},
        docstrings.extract: {"docstring_style", "public_docstrings"},
        organization.extract: {"module_order", "helper_placement"},
        error_handling.extract: {
            "exception_specificity",
            "logging_on_catch",
            "reraising",
        },
        strings.extract: {"quote_style", "interpolation_style", "multiline_strings"},
    }

    for extractor, expected_names in expected_names_by_extractor.items():
        patterns = extractor(analysis)

        actual_names = {pattern.name for pattern in patterns}

        assert actual_names >= expected_names


def test_consistent_style_fixture_has_high_confidence_patterns(
    fixtures_dir: Path,
) -> None:
    patterns = _patterns_by_name(
        fingerprint_project(fixtures_dir / "style_projects" / "consistent").patterns
    )

    assert patterns["logical_blocks"].value == 1

    assert patterns["logical_blocks"].confidence == 1.0

    assert patterns["variables"].value == "snake_case"

    assert patterns["variables"].confidence == 1.0

    assert patterns["signature_coverage"].value == "full_signature_hints"

    assert patterns["signature_coverage"].confidence == 1.0

    assert patterns["optional_syntax"].value == "pipe_union_none"

    assert patterns["exception_specificity"].confidence == 1.0

    assert patterns["logging_on_catch"].confidence == 1.0

    assert patterns["reraising"].confidence == 1.0


def test_mixed_style_fixture_lowers_aggregate_and_dimension_confidence(
    fixtures_dir: Path,
) -> None:
    consistent = fingerprint_project(fixtures_dir / "style_projects" / "consistent")

    mixed = fingerprint_project(fixtures_dir / "style_projects" / "mixed")

    consistent_patterns = _patterns_by_name(consistent.patterns)

    mixed_patterns = _patterns_by_name(mixed.patterns)

    assert mixed.confidence < consistent.confidence

    assert (
        mixed_patterns["functions"].confidence
        < consistent_patterns["functions"].confidence
    )

    assert (
        mixed_patterns["grouping_order"].confidence
        < consistent_patterns["grouping_order"].confidence
    )

    assert (
        mixed_patterns["signature_coverage"].confidence
        < consistent_patterns["signature_coverage"].confidence
    )

    assert (
        mixed_patterns["public_docstrings"].confidence
        < consistent_patterns["public_docstrings"].confidence
    )


def test_syntax_error_fixture_is_represented_without_blocking_patterns(
    fixtures_dir: Path,
) -> None:
    analysis = fingerprint_project(
        fixtures_dir / "style_projects" / "with_syntax_error"
    )

    patterns = _patterns_by_name(analysis.patterns)

    assert [file.relative_path.as_posix() for file in analysis.failed_files] == [
        "src/style_app/broken.py"
    ]

    assert "line 1" in analysis.failed_files[0].parse_error

    assert [file.relative_path.as_posix() for file in analysis.parsed_files] == [
        "src/style_app/valid.py"
    ]

    assert patterns["signature_coverage"].value == "full_signature_hints"

    assert patterns["early_returns"].value == "preferred"


def test_fixture_rendered_fingerprint_markdown_is_verified(
    fixtures_dir: Path,
) -> None:
    analysis = fingerprint_project(fixtures_dir / "style_projects" / "consistent")

    content = render_fingerprint_markdown(
        analysis,
        generated_at=datetime(2026, 5, 2, 12, 30, tzinfo=timezone.utc),
        sample_size=20,
    )

    assert 'generated_at: "2026-05-02T12:30:00+00:00"' in content

    assert '  - "src/style_app/helpers.py"' in content

    assert '  - "src/style_app/service.py"' in content

    assert "- **Inside functions**: 1 blank line" in content

    assert "- **Variables**: snake_case" in content

    assert "- **Coverage**: Full function signature hints" in content

    assert "- **Optional style**: `X | None`" in content

    assert "- **Logging on catch**: Logs caught exceptions" in content

    assert "## Organization" in content

    assert "## Strings" in content


def test_fingerprint_core_rules_are_included_in_generated_router(
    fixtures_dir: Path,
    tmp_path: Path,
) -> None:
    project = fixtures_dir / "style_projects" / "consistent"

    output = tmp_path / ".akira"

    stack = StackInfo.from_signals(
        project,
        (
            Signal(tool="pytest", category="testing", source="fixture"),
            Signal(tool="ruff", category="tooling", source="fixture"),
        ),
    )

    analysis = fingerprint_project(project)

    generate_skills(stack, output, fingerprint=analysis)

    router = (output / "skills" / "SKILL.md").read_text(encoding="utf-8")

    assert "Read `python/testing/pytest.md`" in router

    assert "Use 1 blank line between logical blocks inside functions." in router

    assert "Use full type hints on function signatures." in router

    assert "Use `X | None` syntax for optional values." in router

    assert "Prefer the conventions already present in the repository." in router


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _patterns_by_name(patterns: tuple[StylePattern, ...]) -> dict[str, StylePattern]:
    return {pattern.name: pattern for pattern in patterns}
