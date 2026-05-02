"""Generate Agent Skills from detected Akira stack information."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from jinja2 import Environment, PackageLoader, StrictUndefined

from akira.detect.categories import normalize_skill_category
from akira.detect.models import StackInfo, ToolInfo


@dataclass(frozen=True)
class SkillTemplate:
    """Mapping from a detected tool to a rendered skill artifact."""

    category: str
    tool: str
    template_path: str
    output_path: str
    reason: str


@dataclass(frozen=True)
class GeneratedSkill:
    """A generated skill file."""

    path: Path
    template_path: str


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

_TEMPLATE_BY_SIGNAL = {
    (item.category, item.tool): item for item in SKILL_TEMPLATES
}
_MANAGED_OUTPUTS = {
    Path("SKILL.md"),
    *(Path(item.output_path) for item in SKILL_TEMPLATES),
}


class SkillGenerator:
    """Render the detected Python skill tree for a project."""

    def __init__(self) -> None:
        self.env = Environment(
            loader=PackageLoader("akira.skills", "templates"),
            autoescape=False,
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )

    def generate(self, stack: StackInfo, output_dir: Path) -> tuple[GeneratedSkill, ...]:
        """Generate Python skills under output_dir/skills/python."""
        python_dir = output_dir / "skills" / "python"
        python_dir.mkdir(parents=True, exist_ok=True)

        selected = self.select_templates(stack)
        self._remove_stale_skills(python_dir, selected)

        context = build_template_context(stack, selected)
        generated = [
            self._render_to_file(
                "python/python.md.j2",
                python_dir / "SKILL.md",
                context,
            )
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
        """Return skill templates relevant to the detected stack."""
        selected: list[SkillTemplate] = []

        for signal in stack.signals:
            category = normalize_skill_category(signal.category)
            skill_template = _TEMPLATE_BY_SIGNAL.get((category, signal.tool))
            if skill_template and skill_template not in selected:
                selected.append(skill_template)

        return tuple(selected)

    def _remove_stale_skills(
        self,
        python_dir: Path,
        selected: tuple[SkillTemplate, ...],
    ) -> None:
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
        for directory in sorted(managed_dirs, key=lambda path: len(path.parts), reverse=True):
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
        output_path.parent.mkdir(parents=True, exist_ok=True)
        content = self.env.get_template(template_path).render(**context)
        output_path.write_text(content, encoding="utf-8")
        return GeneratedSkill(path=output_path, template_path=template_path)


def generate_skills(stack: StackInfo, output_dir: Path) -> tuple[GeneratedSkill, ...]:
    """Generate Akira skills for a detected stack."""
    return SkillGenerator().generate(stack, output_dir)


def build_template_context(
    stack: StackInfo,
    selected: tuple[SkillTemplate, ...] = (),
) -> dict[str, Any]:
    """Build the shared Jinja context for all skill templates."""
    tools = {tool.name: tool for category in stack.categories for tool in category.tools}
    context: dict[str, Any] = {
        "project_name": stack.project_name,
        "project_root": stack.project_root,
        "stack": stack,
        "signals": stack.signals,
        "metadata": _merged_metadata(stack),
        "active_skills": [
            {"path": item.output_path, "reason": item.reason} for item in selected
        ],
        "python_version": _version(tools, "python"),
        "package_manager": _first_tool_name(stack, "package_manager"),
        "source_layout": _source_layout(stack.project_root),
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

def _version_context(tools: Mapping[str, ToolInfo]) -> dict[str, str | None]:
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
    is_async_app = stack.has_any("asyncpg", category="database")
    async_stack = "async SQLAlchemy" if is_async_app and stack.has("sqlalchemy") else None
    return {
        "api_layer": "Django REST Framework" if stack.has("djangorestframework") else None,
        "async_stack": async_stack,
        "is_async_app": is_async_app,
        "uses_drf": stack.has("djangorestframework"),
        "uses_pydantic_v2": _uses_pydantic_v2(tools),
    }


def _testing_context(stack: StackInfo) -> dict[str, Any]:
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
    postgres_driver = _first_present_tool(stack, ("asyncpg", "psycopg3", "psycopg2"))
    return {
        "database_engine": "postgres" if stack.has("postgres", category="database") else None,
        "migration_path": "alembic/versions"
        if (stack.project_root / "alembic").is_dir()
        else None,
        "orm": "SQLAlchemy" if stack.has("sqlalchemy", category="database") else None,
        "postgres_driver": postgres_driver,
        "session_style": "async" if postgres_driver == "asyncpg" else None,
    }


def _tooling_context(
    stack: StackInfo,
    tools: Mapping[str, ToolInfo],
) -> dict[str, Any]:
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
        "project_file": "pyproject.toml"
        if (stack.project_root / "pyproject.toml").exists()
        else None,
    }


def _infra_context(stack: StackInfo, tools: Mapping[str, ToolInfo]) -> dict[str, Any]:
    compose = tools.get("docker-compose")
    return {
        "compose_file": compose.sources[0] if compose and compose.sources else None,
        "dockerfile_path": "Dockerfile"
        if (stack.project_root / "Dockerfile").exists()
        else None,
        "gcp_config_files": _existing_joined(
            stack.project_root,
            ("app.yaml", "cloudbuild.yaml", "cloudbuild.yml"),
        ),
    }


def _ci_context(stack: StackInfo) -> dict[str, str | None]:
    github_actions = _tool(stack, "github-actions")
    workflow_files = (
        github_actions.metadata.get("workflow_files") if github_actions else None
    )
    return {
        "workflow_path": ".github/workflows"
        if (stack.project_root / ".github" / "workflows").is_dir()
        else None,
        "python_versions": None,
        "workflow_files": ", ".join(workflow_files) if workflow_files else None,
    }


def _merged_metadata(stack: StackInfo) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for signal in stack.signals:
        metadata.update(signal.metadata)
    return metadata


def _source_layout(project_root: Path) -> str | None:
    return "src" if (project_root / "src").is_dir() else None


def _version(tools: Mapping[str, ToolInfo], tool_name: str) -> str | None:
    tool = tools.get(tool_name)
    return tool.version if tool else None


def _tool(stack: StackInfo, tool_name: str) -> ToolInfo | None:
    for category in stack.categories:
        for tool in category.tools:
            if tool.name == tool_name:
                return tool
    return None


def _first_tool_name(stack: StackInfo, category: str) -> str | None:
    tools = stack.by_category(category)
    return tools[0].name if tools else None


def _first_present_tool(stack: StackInfo, tool_names: tuple[str, ...]) -> str | None:
    for tool_name in tool_names:
        if stack.has(tool_name):
            return tool_name
    return None


def _first_existing(project_root: Path, filenames: tuple[str, ...]) -> str | None:
    for filename in filenames:
        if (project_root / filename).exists():
            return filename
    return None


def _existing_joined(project_root: Path, filenames: tuple[str, ...]) -> str | None:
    existing = [filename for filename in filenames if (project_root / filename).exists()]
    return ", ".join(existing) if existing else None


def _uses_pydantic_v2(tools: Mapping[str, ToolInfo]) -> bool:
    pydantic = tools.get("pydantic")
    if pydantic is None or pydantic.version is None:
        return True
    return pydantic.version.split(".", 1)[0] == "2"
