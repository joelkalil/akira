"""
Tests for review analyzer.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Third-Party Libraries
from rich.console import Console

# Local Libraries
from akira.detect.models import Signal, StackInfo
from akira.review import ReviewCategory, analyze_stack, render_review

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def stack_with(*signals: Signal) -> StackInfo:
    """
    Return stack with result.
    """

    return StackInfo.from_signals(Path.cwd(), signals)


def signal(tool: str, category: str, *, version: str | None = None) -> Signal:
    """
    Return signal result.
    """

    return Signal(tool=tool, category=category, version=version, source="test")


def finding_ids(stack: StackInfo) -> set[str]:
    """
    Return finding ids result.
    """

    return {finding.rule_id for finding in analyze_stack(stack).findings}


class TestInitialRulesReportExpectedFindings:
    """
    Verify initial rules report expected findings cases.
    """

    def test_initial_rules_report_expected_findings(self) -> None:
        """
        Verify initial rules report expected findings behavior.
        """

        stack = stack_with(
            signal("python", "runtime", version="3.12"),
            signal("fastapi", "web_framework"),
            signal("unittest", "testing"),
            signal("ruff", "linting"),
            signal("black", "formatting"),
            signal("isort", "formatting"),
            signal("alembic", "database"),
            signal("psycopg2", "database"),
        )

        result = analyze_stack(stack)

        assert finding_ids(stack) == {
            "pytest-over-unittest",
            "ruff-replaces-black-isort",
            "alembic-needs-sqlalchemy",
            "missing-type-checker",
            "async-stack-sync-driver",
        }

        assert result.has_incompatibilities is True

        assert result.by_category(ReviewCategory.INCOMPATIBILITY)[0].rule_id == (
            "alembic-needs-sqlalchemy"
        )


class TestMissingTypeCheckerOnlyAppliesToModernPython:
    """
    Verify missing type checker only applies to modern python cases.
    """

    def test_missing_type_checker_only_applies_to_modern_python(self) -> None:
        """
        Verify missing type checker only applies to modern python behavior.
        """

        legacy_stack = stack_with(signal("python", "runtime", version="3.9"))

        modern_stack = stack_with(signal("python", "runtime", version="3.10"))

        typed_stack = stack_with(
            signal("python", "runtime", version="3.12"),
            signal("mypy", "type_checking"),
        )

        assert "missing-type-checker" not in finding_ids(legacy_stack)

        assert "missing-type-checker" in finding_ids(modern_stack)

        assert "missing-type-checker" not in finding_ids(typed_stack)


class TestAsyncConsistencyRuleReportsMatchingAsyncStack:
    """
    Verify async consistency rule reports matching async stack cases.
    """

    def test_async_consistency_rule_reports_matching_async_stack(self) -> None:
        """
        Verify async consistency rule reports matching async stack behavior.
        """

        stack = stack_with(
            signal("python", "runtime", version="3.12"),
            signal("fastapi", "web_framework"),
            signal("asyncpg", "database"),
            signal("mypy", "type_checking"),
        )

        result = analyze_stack(stack)

        assert result.by_category(ReviewCategory.CONSISTENCY)[0].rule_id == (
            "async-stack-consistency"
        )

        assert result.has_incompatibilities is False


class TestReviewReporterEscapesProjectNameMarkup:
    """
    Verify review reporter escapes project name markup cases.
    """

    def test_review_reporter_escapes_project_name_markup(self) -> None:
        """
        Verify review reporter escapes project name markup behavior.
        """

        stack = StackInfo.from_signals(Path("project[broken]").resolve(), [])

        console = Console(record=True, force_terminal=False, width=80)

        render_review(analyze_stack(stack), console=console)

        assert "project[broken]" in console.export_text()
