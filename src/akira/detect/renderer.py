"""Render detected stack information into durable project artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, PackageLoader, StrictUndefined

from akira import __version__
from akira.detect.categories import normalize_skill_category
from akira.detect.models import StackInfo, ToolInfo


@dataclass(frozen=True)
class StackSection:
    """A rendered stack.md section."""

    title: str
    rows: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ActiveSkill:
    """A skill hint derived from a detected tool."""

    path: str


TOOL_LABELS = {
    "alembic": "Migrations",
    "asyncpg": "Driver",
    "aws": "Cloud",
    "black": "Formatter",
    "click": "CLI",
    "django": "Web",
    "docker": "Container",
    "docker-compose": "Compose",
    "fastapi": "Web",
    "flake8": "Linter",
    "flask": "Web",
    "gcp": "Cloud",
    "github-actions": "CI/CD",
    "gitlab-ci": "CI/CD",
    "isort": "Import sorter",
    "mypy": "Type checker",
    "pip": "Package manager",
    "poetry": "Package manager",
    "postgres": "Engine",
    "psycopg2": "Driver",
    "psycopg3": "Driver",
    "pre-commit": "Pre-commit",
    "pytest": "Framework",
    "pytest-asyncio": "Plugin",
    "pytest-cov": "Plugin",
    "pyright": "Type checker",
    "pytype": "Type checker",
    "python": "Python",
    "redis": "Cache",
    "ruff": "Linter/Formatter",
    "sqlalchemy": "ORM",
    "streamlit": "Web",
    "terraform": "Infrastructure as code",
    "tox": "Runner",
    "typer": "CLI",
    "uv": "Package manager",
    "unittest": "Framework",
}

SECTION_CATEGORIES = {
    "Runtime": ("runtime", "package_manager"),
    "Framework": ("web_framework", "cli_framework"),
    "Database": ("database",),
    "Testing": ("testing",),
    "Tooling": ("linting", "formatting", "type_checking", "pre_commit"),
    "Infrastructure": ("infrastructure", "ci_cd"),
}

SKILL_HINTS = {
    ("runtime", "python"): "python/SKILL.md",
    ("package_manager", "uv"): "python/tooling/uv.md",
    ("web_framework", "fastapi"): "python/web_framework/fastapi.md",
    ("web_framework", "flask"): "python/web_framework/flask.md",
    ("web_framework", "django"): "python/web_framework/django.md",
    ("testing", "pytest"): "python/testing/pytest.md",
    ("testing", "unittest"): "python/testing/unittest.md",
    ("database", "sqlalchemy"): "python/database/sqlalchemy.md",
    ("database", "alembic"): "python/database/alembic.md",
    ("database", "postgres"): "python/database/postgres.md",
    ("tooling", "ruff"): "python/tooling/ruff.md",
    ("tooling", "mypy"): "python/tooling/mypy.md",
    ("infrastructure", "docker"): "python/infra/docker.md",
    ("infrastructure", "docker-compose"): "python/infra/docker.md",
    ("infrastructure", "gcp"): "python/infra/gcp.md",
    ("ci_cd", "github-actions"): "python/ci_cd/github_actions.md",
}

def render_stack_markdown(
    stack: StackInfo,
    *,
    generated_at: datetime | None = None,
    akira_version: str = __version__,
) -> str:
    """Render stack.md content for detected project stack."""
    timestamp = generated_at or datetime.now(timezone.utc)
    env = Environment(
        loader=PackageLoader("akira.detect", "templates"),
        autoescape=False,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,
    )
    template = env.get_template("stack.md.j2")

    return template.render(
        generated_at=timestamp.replace(microsecond=0).isoformat(),
        akira_version=akira_version,
        project_name=stack.project_name,
        sections=build_stack_sections(stack),
        active_skills=build_active_skills(stack),
    )


def write_stack_markdown(output_dir: Path, stack: StackInfo) -> Path:
    """Create the output directory and write stack.md into it."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "stack.md"
    path.write_text(render_stack_markdown(stack), encoding="utf-8")
    return path


def build_stack_sections(stack: StackInfo) -> tuple[StackSection, ...]:
    """Build readable stack sections from normalized categories."""
    sections: list[StackSection] = []
    for title, categories in SECTION_CATEGORIES.items():
        rows = tuple(
            (tool_label(tool), tool_value(tool))
            for category in categories
            for tool in stack.by_category(category)
        )
        if rows:
            sections.append(StackSection(title=title, rows=rows))

    return tuple(sections)


def build_active_skills(stack: StackInfo) -> tuple[ActiveSkill, ...]:
    """Derive active skill hints from detected tools."""
    paths: list[str] = []
    for signal in stack.signals:
        category = normalize_skill_category(signal.category)
        path = SKILL_HINTS.get((category, signal.tool))
        if path and path not in paths:
            paths.append(path)

    return tuple(ActiveSkill(path=path) for path in paths)


def _humanize_tool_name(name: str) -> str:
    """Return a readable label derived from a tool name."""
    return name.replace("-", " ").replace("_", " ").title()


def tool_label(tool: ToolInfo) -> str:
    """Return the display label for a detected tool."""
    return TOOL_LABELS.get(tool.name, _humanize_tool_name(tool.name))


def tool_value(tool: ToolInfo) -> str:
    """Return the display value for a detected tool."""
    name = tool.name.replace("-", " ").title()
    if tool.name in {"mypy", "pip", "pytest", "ruff", "uv"}:
        name = tool.name
    elif tool.name == "fastapi":
        name = "FastAPI"
    elif tool.name == "github-actions":
        name = "GitHub Actions"
    elif tool.name == "gitlab-ci":
        name = "GitLab CI"
    elif tool.name == "pre-commit":
        return "yes"
    elif tool.name == "sqlalchemy":
        name = "SQLAlchemy"
    elif tool.name == "docker-compose":
        name = "Docker Compose"
    elif tool.name == "gcp":
        name = "GCP"
    elif tool.name == "aws":
        name = "AWS"
    elif tool.name == "psycopg3":
        name = "psycopg3"

    return f"{name} {tool.version}" if tool.version else name
