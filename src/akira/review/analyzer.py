"""
Analyze detected stack information with Akira review rules.
"""

# Standard Libraries
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Callable

# Local Libraries
from akira.detect.models import StackInfo

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ReviewCategory(str, Enum):
    """
    Categories used to group stack review findings.
    """

    CONSISTENCY = "CONSISTENCY"

    SUGGESTION = "SUGGESTION"

    INCOMPATIBILITY = "INCOMPATIBILITY"

    MISSING = "MISSING"


@dataclass(frozen=True)
class StackChange:
    """
    A safe metadata-only change that Akira can apply to stack artifacts.
    """

    summary: str

    details: tuple[str, ...] = ()

    add_signals: tuple[tuple[str, str], ...] = ()

    remove_signals: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Rule:
    """
    A stack review rule.
    """

    id: str

    condition: Callable[[StackInfo], bool]

    category: ReviewCategory

    message: str

    migration: str | None = None

    safe_change: StackChange | None = None

    def evaluate(self, stack: StackInfo) -> bool:
        """
        Return whether this rule applies to the detected stack.
        """

        return self.condition(stack)


@dataclass(frozen=True)
class Finding:
    """
    A single rule result for a stack review.
    """

    rule_id: str

    category: ReviewCategory

    message: str

    migration: str | None = None

    safe_change: StackChange | None = None

    @property
    def can_apply_safely(self) -> bool:
        """
        Return whether Akira can update generated artifacts for this finding.
        """

        return self.safe_change is not None


@dataclass(frozen=True)
class ReviewResult:
    """
    All findings produced for a stack review.
    """

    stack: StackInfo

    findings: tuple[Finding, ...]

    @property
    def has_incompatibilities(self) -> bool:
        """
        Return whether strict mode should fail for this result.
        """

        return any(
            finding.category is ReviewCategory.INCOMPATIBILITY
            for finding in self.findings
        )

    def by_category(self, category: ReviewCategory) -> tuple[Finding, ...]:
        """
        Return findings for one review category.
        """

        return tuple(
            finding for finding in self.findings if finding.category is category
        )


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def analyze_stack(
    stack: StackInfo,
    rules: tuple[Rule, ...] | None = None,
) -> ReviewResult:
    """
    Apply review rules to a detected project stack.
    """

    active_rules = INITIAL_RULES if rules is None else rules

    findings = tuple(
        Finding(
            rule_id=rule.id,
            category=rule.category,
            message=rule.message,
            migration=rule.migration,
            safe_change=rule.safe_change,
        )
        for rule in active_rules
        if rule.evaluate(stack)
    )

    return ReviewResult(stack=stack, findings=findings)


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _python_version_at_least(stack: StackInfo, minimum: tuple[int, int]) -> bool:

    python_tools = stack.by_category("runtime")

    version = next(
        (
            tool.version
            for tool in python_tools
            if tool.name == "python" and tool.version
        ),
        None,
    )

    if version is None:

        return False

    parts = version.split(".")

    try:

        major = int(parts[0])

        minor = int(parts[1]) if len(parts) > 1 else 0

    except ValueError:

        return False

    return (major, minor) >= minimum


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

INITIAL_RULES: tuple[Rule, ...] = (
    Rule(
        id="pytest-over-unittest",
        condition=lambda stack: (
            stack.has("unittest", category="testing")
            and not stack.has("pytest", category="testing")
        ),
        category=ReviewCategory.SUGGESTION,
        message="unittest detected. Consider pytest for richer fixtures, plugins, and modern Python test ergonomics.",
        migration="testing/unittest-to-pytest",
        safe_change=StackChange(
            summary="Replace unittest stack metadata with pytest.",
            details=(
                "Remove the generated unittest skill.",
                "Add pytest to the accepted stack state.",
                "Regenerate the pytest testing skill.",
            ),
            add_signals=(("pytest", "testing"),),
            remove_signals=(("unittest", "testing"),),
        ),
    ),
    Rule(
        id="ruff-replaces-black-isort",
        condition=lambda stack: (
            stack.has("ruff", category="linting")
            and (
                stack.has("black", category="formatting")
                or stack.has("isort", category="formatting")
            )
        ),
        category=ReviewCategory.SUGGESTION,
        message="Ruff can handle formatting and import sorting, so black/isort may be redundant.",
        safe_change=StackChange(
            summary="Remove redundant black/isort stack metadata while keeping ruff.",
            details=(
                "Leave dependency files unchanged.",
                "Keep ruff as the generated formatting and linting guidance.",
            ),
            remove_signals=(("black", "formatting"), ("isort", "formatting")),
        ),
    ),
    Rule(
        id="alembic-needs-sqlalchemy",
        condition=lambda stack: (
            stack.has("alembic", category="database")
            and not stack.has("sqlalchemy", category="database")
        ),
        category=ReviewCategory.INCOMPATIBILITY,
        message="Alembic detected without SQLAlchemy. Add SQLAlchemy or remove the migration setup.",
    ),
    Rule(
        id="missing-type-checker",
        condition=lambda stack: (
            _python_version_at_least(stack, (3, 10))
            and not stack.has_any("mypy", "pyright", "pytype", category="type_checking")
        ),
        category=ReviewCategory.MISSING,
        message="No type checker detected for a modern Python project. Consider adding mypy or pyright.",
        safe_change=StackChange(
            summary="Add mypy to accepted stack metadata.",
            details=(
                "Leave dependency files unchanged.",
                "Generate the mypy skill so agents receive typing guidance.",
            ),
            add_signals=(("mypy", "type_checking"),),
        ),
    ),
    Rule(
        id="async-stack-consistency",
        condition=lambda stack: (
            stack.has("fastapi", category="web_framework")
            and stack.has_any("asyncpg", "psycopg3", category="database")
            and not stack.has("psycopg2", category="database")
        ),
        category=ReviewCategory.CONSISTENCY,
        message="FastAPI is paired with an async-friendly PostgreSQL driver.",
    ),
    Rule(
        id="async-stack-sync-driver",
        condition=lambda stack: (
            stack.has("fastapi", category="web_framework")
            and stack.has("psycopg2", category="database")
            and not stack.has_any("asyncpg", "psycopg3", category="database")
        ),
        category=ReviewCategory.SUGGESTION,
        message="FastAPI is async-first, but psycopg2 is synchronous. Consider asyncpg or psycopg3.",
    ),
)
