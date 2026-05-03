"""
Generate Agent Skills from detected Akira stack information.
"""

# Standard Libraries
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

# Third-Party Libraries
from jinja2 import Environment, PackageLoader, StrictUndefined

# Local Libraries
from akira.detect.categories import normalize_skill_category
from akira.detect.models import StackInfo, ToolInfo
from akira.fingerprint import format_fingerprint_value
from akira.fingerprint.models import FingerprintAnalysis, StylePattern

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class SkillTemplate:
    """
    Mapping from a detected tool to a rendered skill artifact.
    """

    category: str

    tool: str

    template_path: str

    output_path: str

    reason: str


@dataclass(frozen=True)
class GeneratedSkill:
    """
    A generated skill file.
    """

    path: Path

    template_path: str


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

SKILL_TEMPLATES: tuple[SkillTemplate, ...] = (
    SkillTemplate(
        "package_manager",
        "uv",
        "python/tooling/uv.md.j2",
        "tooling/uv.md",
        "Python package and environment work",
    ),
    SkillTemplate(
        "web_framework",
        "fastapi",
        "python/web_framework/fastapi.md.j2",
        "web_framework/fastapi.md",
        "FastAPI endpoints, routers, dependencies, or middleware",
    ),
    SkillTemplate(
        "web_framework",
        "flask",
        "python/web_framework/flask.md.j2",
        "web_framework/flask.md",
        "Flask apps, blueprints, requests, or extensions",
    ),
    SkillTemplate(
        "web_framework",
        "django",
        "python/web_framework/django.md.j2",
        "web_framework/django.md",
        "Django apps, settings, models, views, or migrations",
    ),
    SkillTemplate(
        "testing",
        "pytest",
        "python/testing/pytest.md.j2",
        "testing/pytest.md",
        "pytest tests, fixtures, parametrization, or test configuration",
    ),
    SkillTemplate(
        "testing",
        "unittest",
        "python/testing/unittest.md.j2",
        "testing/unittest.md",
        "unittest suites, cases, assertions, or test runners",
    ),
    SkillTemplate(
        "database",
        "sqlalchemy",
        "python/database/sqlalchemy.md.j2",
        "database/sqlalchemy.md",
        "SQLAlchemy models, sessions, queries, or persistence code",
    ),
    SkillTemplate(
        "database",
        "alembic",
        "python/database/alembic.md.j2",
        "database/alembic.md",
        "Alembic migrations or database schema changes",
    ),
    SkillTemplate(
        "database",
        "postgres",
        "python/database/postgres.md.j2",
        "database/postgres.md",
        "PostgreSQL schema, queries, drivers, or database behavior",
    ),
    SkillTemplate(
        "tooling",
        "ruff",
        "python/tooling/ruff.md.j2",
        "tooling/ruff.md",
        "Ruff linting, formatting, or import organization",
    ),
    SkillTemplate(
        "tooling",
        "mypy",
        "python/tooling/mypy.md.j2",
        "tooling/mypy.md",
        "mypy typing, annotations, or static analysis",
    ),
    SkillTemplate(
        "infrastructure",
        "docker",
        "python/infra/docker.md.j2",
        "infra/docker.md",
        "Dockerfiles, images, containers, or compose integration",
    ),
    SkillTemplate(
        "infrastructure",
        "gcp",
        "python/infra/gcp.md.j2",
        "infra/gcp.md",
        "Google Cloud deployment, runtime, or service configuration",
    ),
    SkillTemplate(
        "ci_cd",
        "github-actions",
        "python/ci_cd/github_actions.md.j2",
        "ci_cd/github_actions.md",
        "GitHub Actions workflows or CI/CD automation",
    ),
)

_MANAGED_OUTPUTS = {
    Path("SKILL.md"),
    *(Path(item.output_path) for item in SKILL_TEMPLATES),
}

_ROOT_ROUTER_OUTPUT = Path("SKILL.md")

_CORE_RULE_PRIORITY = (
    ("structure", "early_returns"),
    ("structure", "guard_clauses"),
    ("comments", "section_separators"),
    ("comments", "inline_comment_frequency"),
    ("spacing", "logical_blocks"),
    ("typing", "signature_coverage"),
    ("typing", "optional_syntax"),
    ("structure", "nesting_depth"),
    ("imports", "grouping_order"),
    ("imports", "relative_imports"),
    ("imports", "wildcard_usage"),
    ("docstrings", "docstring_style"),
    ("docstrings", "public_docstrings"),
    ("docstrings", "private_docstring_behavior"),
    ("strings", "quote_style"),
    ("strings", "interpolation_style"),
    ("structure", "function_length"),
)


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class SkillGenerator:
    """
    Render the detected Python skill tree for a project.
    """

    def __init__(self) -> None:
        """Return init helper result."""

        self.env = Environment(
            loader=PackageLoader("akira.skills", "templates"),
            autoescape=False,
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )

    def generate(
        self,
        stack: StackInfo,
        output_dir: Path,
        *,
        fingerprint: FingerprintAnalysis | None = None,
    ) -> tuple[GeneratedSkill, ...]:
        """
        Generate the Akira router and Python skills under output_dir/skills.

        Parameters
        ----------
        stack : StackInfo
            The stack value.
        output_dir : Path
            The output dir value.
        fingerprint : FingerprintAnalysis | None
            The fingerprint value.

        Returns
        -------
        tuple[GeneratedSkill, ...]
            The result of the operation.
        """

        skills_dir = output_dir / "skills"

        python_dir = output_dir / "skills" / "python"

        skills_dir.mkdir(parents=True, exist_ok=True)

        python_dir.mkdir(parents=True, exist_ok=True)

        selected = self.select_templates(stack)

        self._remove_stale_skills(python_dir, selected)

        fingerprint_path = output_dir / "fingerprint.md"

        fingerprint_file_exists = fingerprint_path.exists()

        context = build_template_context(
            stack,
            selected=selected,
            fingerprint_exists=fingerprint_file_exists,
            fingerprint=fingerprint,
        )

        generated = [
            self._render_to_file(
                "base.md.j2",
                skills_dir / _ROOT_ROUTER_OUTPUT,
                context,
            ),
            self._render_to_file(
                "python/python.md.j2",
                python_dir / "SKILL.md",
                context,
            ),
        ]

        for skill_template in selected:
            generated.append(
                self._render_to_file(
                    skill_template.template_path,
                    python_dir / skill_template.output_path,
                    context,
                )
            )

        return tuple(generated)

    def select_templates(self, stack: StackInfo) -> tuple[SkillTemplate, ...]:
        """
        Return skill templates relevant to the detected stack.

        Parameters
        ----------
        stack : StackInfo
            The stack value.

        Returns
        -------
        tuple[SkillTemplate, ...]
            The result of the operation.
        """

        detected = {
            (normalize_skill_category(signal.category), signal.tool)
            for signal in stack.signals
        }

        return tuple(
            skill_template
            for skill_template in SKILL_TEMPLATES
            if (skill_template.category, skill_template.tool) in detected
        )

    def _remove_stale_skills(
        self,
        python_dir: Path,
        selected: tuple[SkillTemplate, ...],
    ) -> None:
        """
        Remove managed skill files that are no longer selected.

        Parameters
        ----------
        python_dir : Path
            The python dir value.
        selected : tuple[SkillTemplate, ...]
            The selected value.
        """

        active_outputs = {Path("SKILL.md")}

        active_outputs.update(Path(item.output_path) for item in selected)

        for relative_path in sorted(_MANAGED_OUTPUTS - active_outputs):
            path = python_dir / relative_path

            if path.exists():
                path.unlink()

        managed_dirs = {
            python_dir / relative_path.parent
            for relative_path in _MANAGED_OUTPUTS
            if relative_path.parent != Path(".")
        }

        for directory in sorted(
            managed_dirs, key=lambda path: len(path.parts), reverse=True
        ):
            try:
                directory.rmdir()

            except OSError:
                continue

    def _render_to_file(
        self,
        template_path: str,
        output_path: Path,
        context: Mapping[str, Any],
    ) -> GeneratedSkill:
        """
        Render a skill template to disk.

        Parameters
        ----------
        template_path : str
            The template path value.
        output_path : Path
            The output path value.
        context : Mapping[str, Any]
            The context value.

        Returns
        -------
        GeneratedSkill
            The result of the operation.
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self.env.get_template(template_path).render(**context)

        output_path.write_text(content, encoding="utf-8")

        return GeneratedSkill(path=output_path, template_path=template_path)


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def generate_skills(
    stack: StackInfo,
    output_dir: Path,
    *,
    fingerprint: FingerprintAnalysis | None = None,
) -> tuple[GeneratedSkill, ...]:
    """
    Generate Akira skills for a detected stack.

    Parameters
    ----------
    stack : StackInfo
        The stack value.
    output_dir : Path
        The output dir value.
    fingerprint : FingerprintAnalysis | None
        The fingerprint value.

    Returns
    -------
    tuple[GeneratedSkill, ...]
        The result of the operation.
    """

    return SkillGenerator().generate(stack, output_dir, fingerprint=fingerprint)


def build_template_context(
    stack: StackInfo,
    *,
    selected: tuple[SkillTemplate, ...] = (),
    fingerprint_exists: bool = False,
    fingerprint: FingerprintAnalysis | None = None,
) -> dict[str, Any]:
    """
    Build the shared Jinja context for all skill templates.

    Parameters
    ----------
    stack : StackInfo
        The stack value.
    selected : tuple[SkillTemplate, ...]
        The selected value.
    fingerprint_exists : bool
        The fingerprint exists value.
    fingerprint : FingerprintAnalysis | None
        The fingerprint value.

    Returns
    -------
    dict[str, Any]
        The result of the operation.
    """

    tools = {
        tool.name: tool for category in stack.categories for tool in category.tools
    }

    active_skills = [
        {"path": item.output_path, "reason": item.reason} for item in selected
    ]

    context: dict[str, Any] = {
        "project_name": stack.project_name,
        "project_root": stack.project_root,
        "stack": stack,
        "signals": stack.signals,
        "metadata": _merged_metadata(stack),
        "active_skills": active_skills,
        "fingerprint_exists": fingerprint_exists,
        "fingerprint_core_rules": select_fingerprint_core_rules(fingerprint),
        "python_version": _version(tools, "python"),
        "package_manager": _first_tool_name(stack, "package_manager"),
        "root_active_skills": _root_active_skills(active_skills),
        "source_layout": _source_layout(stack.project_root),
        "stack_summary": _stack_summary(stack),
        "uses_docker": stack.has("docker", category="infrastructure"),
    }

    context.update(_version_context(tools))

    context.update(_framework_context(stack, tools))

    context.update(_testing_context(stack))

    context.update(_database_context(stack, tools))

    context.update(_tooling_context(stack, tools))

    context.update(_infra_context(stack, tools))

    context.update(_ci_context(stack))

    return {key: value for key, value in context.items() if value is not None}


def select_fingerprint_core_rules(
    fingerprint: FingerprintAnalysis | None,
    *,
    limit: int = 5,
    minimum_confidence: float = 0.7,
) -> tuple[str, ...]:
    """
    Select concise router rules from high-confidence fingerprint patterns.

    Parameters
    ----------
    fingerprint : FingerprintAnalysis | None
        The fingerprint value.
    limit : int
        The limit value.
    minimum_confidence : float
        The minimum confidence value.

    Returns
    -------
    tuple[str, ...]
        The result of the operation.
    """

    if fingerprint is None:
        return ()

    by_key = {
        (pattern.dimension, pattern.name): pattern
        for pattern in fingerprint.patterns
        if pattern.confidence >= minimum_confidence and pattern.samples > 0
    }

    rules: list[str] = []

    for dimension, name in _CORE_RULE_PRIORITY:
        pattern = by_key.get((dimension, name))

        if pattern is None:
            continue

        rule = _core_rule_for_pattern(pattern)

        if rule and rule not in rules:
            rules.append(rule)

        if len(rules) >= limit:
            break

    return tuple(rules)


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _core_rule_for_pattern(pattern: StylePattern) -> str | None:
    """
    Convert a fingerprint pattern into a concise router rule.

    Parameters
    ----------
    pattern : StylePattern
        The pattern value.

    Returns
    -------
    str | None
        The result of the operation.
    """

    key = (pattern.dimension, pattern.name)

    value = pattern.value

    if key == ("structure", "early_returns") and value == "preferred":
        return "Prefer early returns over deeply nested branches."

    if key == ("structure", "guard_clauses") and value == "preferred":
        return "Put guard clauses near the top of functions."

    if key == ("structure", "nesting_depth") and isinstance(value, int):
        if value == 0:
            return "Avoid nested control flow where possible."

        return (
            f"Keep control-flow nesting to {value} {_plural('level', value)} or less."
        )

    if key == ("comments", "section_separators"):
        return f"Use {format_fingerprint_value(value)} comments as section separators."

    if key == ("comments", "inline_comment_frequency") and value in {"low", "rare"}:
        return "Keep inline comments rare; prefer self-documenting code."

    if key == ("spacing", "logical_blocks") and isinstance(value, int):
        return (
            f"Use {value} {_plural('blank line', value)} between logical blocks "
            "inside functions."
        )

    if key == ("typing", "signature_coverage") and value == "full_signature_hints":
        return "Use full type hints on function signatures."

    if key == ("typing", "optional_syntax"):
        return f"Use {format_fingerprint_value(value)} syntax for optional values."

    if key == ("imports", "grouping_order"):
        return f"Keep imports grouped in this order: {format_fingerprint_value(value)}."

    if key == ("imports", "relative_imports") and value == "avoid_relative_imports":
        return "Prefer absolute imports over relative imports."

    if key == ("imports", "wildcard_usage") and value == "avoid_wildcards":
        return "Avoid wildcard imports."

    if key == ("docstrings", "docstring_style"):
        return f"Write {format_fingerprint_value(value)} docstrings."

    if key == ("docstrings", "public_docstrings") and value == "documented":
        return "Document public functions and classes."

    if (
        key == ("docstrings", "private_docstring_behavior")
        and value == "omit_private_docstrings"
    ):
        return "Omit docstrings on private helpers when names are descriptive."

    if key == ("strings", "quote_style"):
        return f"Use {format_fingerprint_value(value)} for string literals."

    if key == ("strings", "interpolation_style") and value == "f_strings":
        return "Prefer f-strings for string interpolation."

    if key == ("structure", "function_length") and value == "under_30_lines":
        return "Prefer functions under 30 lines."

    return None


def _plural(noun: str, count: int) -> str:
    """
    Return a pluralized noun for the provided count.

    Parameters
    ----------
    noun : str
        The noun value.
    count : int
        The count value.

    Returns
    -------
    str
        The result of the operation.
    """

    return noun if count == 1 else f"{noun}s"


def _version_context(tools: Mapping[str, ToolInfo]) -> dict[str, str | None]:
    """
    Build template context values for detected tool versions.

    Parameters
    ----------
    tools : Mapping[str, ToolInfo]
        The tools value.

    Returns
    -------
    dict[str, str | None]
        The result of the operation.
    """

    return {
        "alembic_version": _version(tools, "alembic"),
        "django_version": _version(tools, "django"),
        "fastapi_version": _version(tools, "fastapi"),
        "flask_version": _version(tools, "flask"),
        "mypy_version": _version(tools, "mypy"),
        "postgres_version": _version(tools, "postgres"),
        "pytest_version": _version(tools, "pytest"),
        "ruff_version": _version(tools, "ruff"),
        "sqlalchemy_version": _version(tools, "sqlalchemy"),
    }


def _framework_context(
    stack: StackInfo,
    tools: Mapping[str, ToolInfo],
) -> dict[str, Any]:
    """
    Build template context values for detected web frameworks.

    Parameters
    ----------
    stack : StackInfo
        The stack value.
    tools : Mapping[str, ToolInfo]
        The tools value.

    Returns
    -------
    dict[str, Any]
        The result of the operation.
    """

    is_async_app = stack.has_any("asyncpg", category="database")

    async_stack = (
        "async SQLAlchemy" if is_async_app and stack.has("sqlalchemy") else None
    )

    return {
        "api_layer": (
            "Django REST Framework" if stack.has("djangorestframework") else None
        ),
        "async_stack": async_stack,
        "is_async_app": is_async_app,
        "uses_drf": stack.has("djangorestframework"),
        "uses_pydantic_v2": _uses_pydantic_v2(tools),
    }


def _testing_context(stack: StackInfo) -> dict[str, Any]:
    """
    Build template context values for detected testing tools.

    Parameters
    ----------
    stack : StackInfo
        The stack value.

    Returns
    -------
    dict[str, Any]
        The result of the operation.
    """

    return {
        "async_tests": stack.has("pytest-asyncio", category="testing")
        or stack.has("asyncpg", category="database"),
        "test_path": "tests" if (stack.project_root / "tests").is_dir() else None,
        "test_runner": "pytest" if stack.has("pytest", category="testing") else None,
    }


def _database_context(
    stack: StackInfo,
    tools: Mapping[str, ToolInfo],
) -> dict[str, str | None]:
    """
    Build template context values for detected database tools.

    Parameters
    ----------
    stack : StackInfo
        The stack value.
    tools : Mapping[str, ToolInfo]
        The tools value.

    Returns
    -------
    dict[str, str | None]
        The result of the operation.
    """

    postgres_driver = _first_present_tool(stack, ("asyncpg", "psycopg3", "psycopg2"))

    return {
        "database_engine": (
            "postgres" if stack.has("postgres", category="database") else None
        ),
        "migration_path": (
            "alembic/versions" if (stack.project_root / "alembic").is_dir() else None
        ),
        "orm": "SQLAlchemy" if stack.has("sqlalchemy", category="database") else None,
        "postgres_driver": postgres_driver,
        "session_style": "async" if postgres_driver == "asyncpg" else None,
    }


def _tooling_context(
    stack: StackInfo,
    tools: Mapping[str, ToolInfo],
) -> dict[str, Any]:
    """
    Build template context values for detected development tooling.

    Parameters
    ----------
    stack : StackInfo
        The stack value.
    tools : Mapping[str, ToolInfo]
        The tools value.

    Returns
    -------
    dict[str, Any]
        The result of the operation.
    """

    ruff = tools.get("ruff")

    mypy = tools.get("mypy")

    return {
        "config_file": _first_existing(
            stack.project_root,
            ("pyproject.toml", "ruff.toml", "mypy.ini", "setup.cfg"),
        ),
        "line_length": ruff.metadata.get("line_length") if ruff else None,
        "mypy_strictness": mypy.metadata.get("strictness") if mypy else None,
        "lock_file": "uv.lock" if (stack.project_root / "uv.lock").exists() else None,
        "project_file": (
            "pyproject.toml"
            if (stack.project_root / "pyproject.toml").exists()
            else None
        ),
    }


def _infra_context(stack: StackInfo, tools: Mapping[str, ToolInfo]) -> dict[str, Any]:
    """
    Build template context values for detected infrastructure tools.

    Parameters
    ----------
    stack : StackInfo
        The stack value.
    tools : Mapping[str, ToolInfo]
        The tools value.

    Returns
    -------
    dict[str, Any]
        The result of the operation.
    """

    compose = tools.get("docker-compose")

    return {
        "compose_file": compose.sources[0] if compose and compose.sources else None,
        "dockerfile_path": (
            "Dockerfile" if (stack.project_root / "Dockerfile").exists() else None
        ),
        "gcp_config_files": _existing_joined(
            stack.project_root,
            ("app.yaml", "cloudbuild.yaml", "cloudbuild.yml"),
        ),
    }


def _ci_context(stack: StackInfo) -> dict[str, str | None]:
    """
    Build template context values for detected CI tools.

    Parameters
    ----------
    stack : StackInfo
        The stack value.

    Returns
    -------
    dict[str, str | None]
        The result of the operation.
    """

    github_actions = _tool(stack, "github-actions")

    workflow_files = (
        github_actions.metadata.get("workflow_files") if github_actions else None
    )

    return {
        "workflow_path": (
            ".github/workflows"
            if (stack.project_root / ".github" / "workflows").is_dir()
            else None
        ),
        "python_versions": None,
        "workflow_files": ", ".join(workflow_files) if workflow_files else None,
    }


def _merged_metadata(stack: StackInfo) -> dict[str, Any]:
    """
    Merge stack signal metadata into one template context mapping.

    Parameters
    ----------
    stack : StackInfo
        The stack value.

    Returns
    -------
    dict[str, Any]
        The result of the operation.
    """

    metadata: dict[str, Any] = {}

    for signal in stack.signals:
        metadata.update(signal.metadata)

    return metadata


def _root_active_skills(
    active_skills: list[dict[str, str]],
) -> list[dict[str, str]]:
    """
    Build root router entries for active generated skills.

    Parameters
    ----------
    active_skills : list[dict[str, str]]
        The active skills value.

    Returns
    -------
    list[dict[str, str]]
        The result of the operation.
    """

    return [
        {
            "path": "python/SKILL.md",
            "reason": "Python modules, imports, typing, or shared code",
        },
        *(
            {"path": f"python/{skill['path']}", "reason": skill["reason"]}
            for skill in active_skills
        ),
    ]


def _stack_summary(stack: StackInfo) -> str:
    """
    Render a compact summary of the detected stack.

    Parameters
    ----------
    stack : StackInfo
        The stack value.

    Returns
    -------
    str
        The result of the operation.
    """

    priority = (
        ("web_framework", ("fastapi", "django", "flask")),
        ("database", ("sqlalchemy", "postgres", "alembic")),
        ("testing", ("pytest", "unittest")),
        ("tooling", ("ruff", "mypy")),
        ("package_manager", ("uv", "poetry", "pip")),
        ("infrastructure", ("docker", "gcp")),
        ("ci_cd", ("github-actions",)),
    )

    labels = {
        "django": "Django",
        "fastapi": "FastAPI",
        "flask": "Flask",
        "github-actions": "GitHub Actions",
        "gcp": "GCP",
        "mypy": "mypy",
        "postgres": "PostgreSQL",
        "pytest": "pytest",
        "ruff": "ruff",
        "sqlalchemy": "SQLAlchemy",
        "unittest": "unittest",
        "uv": "uv",
    }

    selected: list[str] = []

    for category, tools in priority:
        for tool in tools:
            if _has_skill_tool(stack, tool, category=category):
                selected.append(labels.get(tool, tool.title()))

    if not selected:
        return "Python"

    return " + ".join(dict.fromkeys(selected))


def _has_skill_tool(stack: StackInfo, tool: str, category: str) -> bool:
    """
    Return whether a normalized skill signal exists for a tool.

    Parameters
    ----------
    stack : StackInfo
        The stack value.
    tool : str
        The tool value.
    category : str
        The category value.

    Returns
    -------
    bool
        The result of the operation.
    """

    return any(
        signal.tool == tool and normalize_skill_category(signal.category) == category
        for signal in stack.signals
    )


def _source_layout(project_root: Path) -> str | None:
    """
    Return the detected Python source layout.

    Parameters
    ----------
    project_root : Path
        The project root value.

    Returns
    -------
    str | None
        The result of the operation.
    """

    return "src" if (project_root / "src").is_dir() else None


def _version(tools: Mapping[str, ToolInfo], tool_name: str) -> str | None:
    """
    Return the detected version for a tool.

    Parameters
    ----------
    tools : Mapping[str, ToolInfo]
        The tools value.
    tool_name : str
        The tool name value.

    Returns
    -------
    str | None
        The result of the operation.
    """

    tool = tools.get(tool_name)

    return tool.version if tool else None


def _tool(stack: StackInfo, tool_name: str) -> ToolInfo | None:
    """
    Return the first detected tool with the requested name.

    Parameters
    ----------
    stack : StackInfo
        The stack value.
    tool_name : str
        The tool name value.

    Returns
    -------
    ToolInfo | None
        The result of the operation.
    """

    for category in stack.categories:
        for tool in category.tools:
            if tool.name == tool_name:
                return tool

    return None


def _first_tool_name(stack: StackInfo, category: str) -> str | None:
    """
    Return the first detected tool name in a category.

    Parameters
    ----------
    stack : StackInfo
        The stack value.
    category : str
        The category value.

    Returns
    -------
    str | None
        The result of the operation.
    """

    tools = stack.by_category(category)

    return tools[0].name if tools else None


def _first_present_tool(stack: StackInfo, tool_names: tuple[str, ...]) -> str | None:
    """
    Return the first requested tool present in the stack.

    Parameters
    ----------
    stack : StackInfo
        The stack value.
    tool_names : tuple[str, ...]
        The tool names value.

    Returns
    -------
    str | None
        The result of the operation.
    """

    for tool_name in tool_names:
        if stack.has(tool_name):
            return tool_name

    return None


def _first_existing(project_root: Path, filenames: tuple[str, ...]) -> str | None:
    """
    Return the first filename that exists under the project root.

    Parameters
    ----------
    project_root : Path
        The project root value.
    filenames : tuple[str, ...]
        The filenames value.

    Returns
    -------
    str | None
        The result of the operation.
    """

    for filename in filenames:
        if (project_root / filename).exists():
            return filename

    return None


def _existing_joined(project_root: Path, filenames: tuple[str, ...]) -> str | None:
    """
    Return existing filenames joined for template display.

    Parameters
    ----------
    project_root : Path
        The project root value.
    filenames : tuple[str, ...]
        The filenames value.

    Returns
    -------
    str | None
        The result of the operation.
    """

    existing = [
        filename for filename in filenames if (project_root / filename).exists()
    ]

    return ", ".join(existing) if existing else None


def _uses_pydantic_v2(tools: Mapping[str, ToolInfo]) -> bool:
    """
    Return whether generated FastAPI guidance should assume Pydantic v2.

    Parameters
    ----------
    tools : Mapping[str, ToolInfo]
        The tools value.

    Returns
    -------
    bool
        The result of the operation.
    """

    pydantic = tools.get("pydantic")

    if pydantic is None or pydantic.version is None:
        return True

    return pydantic.version.split(".", 1)[0] == "2"
