from __future__ import annotations

from pathlib import Path

from akira.detect.models import Signal, StackInfo
from akira.review import ReviewCategory, analyze_stack


def stack_with(*signals: Signal) -> StackInfo:
    return StackInfo.from_signals(Path.cwd(), signals)


def signal(tool: str, category: str, version: str | None = None) -> Signal:
    return Signal(tool=tool, category=category, version=version, source="test")


def finding_ids(stack: StackInfo) -> set[str]:
    return {finding.rule_id for finding in analyze_stack(stack).findings}


def test_initial_rules_report_expected_findings() -> None:
    stack = stack_with(
        signal("python", "runtime", "3.12"),
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


def test_missing_type_checker_only_applies_to_modern_python() -> None:
    legacy_stack = stack_with(signal("python", "runtime", "3.9"))
    modern_stack = stack_with(signal("python", "runtime", "3.10"))
    typed_stack = stack_with(
        signal("python", "runtime", "3.12"),
        signal("mypy", "type_checking"),
    )

    assert "missing-type-checker" not in finding_ids(legacy_stack)
    assert "missing-type-checker" in finding_ids(modern_stack)
    assert "missing-type-checker" not in finding_ids(typed_stack)


def test_async_consistency_rule_reports_matching_async_stack() -> None:
    stack = stack_with(
        signal("python", "runtime", "3.12"),
        signal("fastapi", "web_framework"),
        signal("asyncpg", "database"),
        signal("mypy", "type_checking"),
    )

    result = analyze_stack(stack)

    assert result.by_category(ReviewCategory.CONSISTENCY)[0].rule_id == (
        "async-stack-consistency"
    )
    assert result.has_incompatibilities is False
