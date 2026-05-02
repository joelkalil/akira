from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from akira.detect import Scanner, render_stack_markdown
from akira.detect.models import Signal, StackInfo, ToolInfo
from akira.detect.renderer import SKILL_HINTS, tool_label, tool_value
from akira.skills.generator import SKILL_TEMPLATES


def test_minimal_project_stack_markdown_has_frontmatter_and_runtime(
    fixtures_dir: Path,
) -> None:
    project_root = fixtures_dir / "minimal_project"

    content = render_stack_markdown(
        Scanner().scan(project_root),
        generated_at=datetime(2026, 5, 1, 15, 30, tzinfo=timezone.utc),
        akira_version="1.0.0",
    )
    frontmatter = _frontmatter(content)

    assert frontmatter["generated_at"] == "2026-05-01T15:30:00+00:00"
    assert frontmatter["akira_version"] == "1.0.0"
    assert frontmatter["project_name"] == "minimal_project"
    assert "# Stack - minimal_project" in content
    assert "## Runtime" in content
    assert "- **Python**: Python 3.12" in content
    assert "- **Package manager**: uv" in content
    assert "## Framework" not in content
    assert "## Active Skills" in content
    assert "- `python/SKILL.md`" in content
    assert "- `python/tooling/uv.md`" in content


def test_fastapi_project_stack_markdown_renders_sections_and_active_skills(
    fixtures_dir: Path,
) -> None:
    project_root = fixtures_dir / "fastapi_project"

    content = render_stack_markdown(
        Scanner().scan(project_root),
        generated_at=datetime(2026, 5, 1, 15, 30, tzinfo=timezone.utc),
        akira_version="1.0.0",
    )

    for section in (
        "## Runtime",
        "## Framework",
        "## Database",
        "## Testing",
        "## Tooling",
        "## Infrastructure",
        "## Active Skills",
    ):
        assert section in content

    assert "- **Web**: FastAPI 0.115.0" in content
    assert "- **Framework**: pytest 8.3.0" in content
    assert "- **ORM**: SQLAlchemy 2.0.36" in content
    assert "- **Migrations**: Alembic 1.14.0" in content
    assert "- **Linter/Formatter**: ruff" in content
    assert "- **Type checker**: mypy" in content
    assert "- **Container**: Docker" in content
    assert "- **CI/CD**: GitHub Actions" in content

    for skill in (
        "python/SKILL.md",
        "python/tooling/uv.md",
        "python/web_framework/fastapi.md",
        "python/testing/pytest.md",
        "python/database/sqlalchemy.md",
        "python/database/alembic.md",
        "python/tooling/ruff.md",
        "python/tooling/mypy.md",
        "python/infra/docker.md",
        "python/ci_cd/github_actions.md",
    ):
        assert f"- `{skill}`" in content

    assert "- `python/infra/docker.md`" in content
    assert "- `python/infra/docker-compose.md`" not in content


def _frontmatter(content: str) -> dict[str, str]:
    _, raw_frontmatter, _ = content.split("---", 2)
    return yaml.safe_load(raw_frontmatter)


def test_unknown_tool_label_uses_tool_name_not_category() -> None:
    tool = ToolInfo(name="psycopg2-binary", category="database")

    assert tool_label(tool) == "Psycopg2 Binary"


def test_pre_commit_value_ignores_version_for_boolean_presence() -> None:
    tool = ToolInfo(name="pre-commit", category="pre_commit", version="3.8.0")

    assert tool_value(tool) == "yes"


def test_stack_markdown_renders_new_infra_ci_and_database_tools(
    tmp_path: Path,
) -> None:
    stack = StackInfo.from_signals(
        tmp_path,
        [
            Signal(tool="gitlab-ci", category="ci_cd", source=".gitlab-ci.yml"),
            Signal(tool="gcp", category="infrastructure", source="cloud hints"),
            Signal(tool="aws", category="infrastructure", source="cloud hints"),
            Signal(tool="terraform", category="infrastructure", source="infra/main.tf"),
            Signal(tool="psycopg3", category="database", version="3.2.3"),
            Signal(tool="redis", category="database"),
        ],
    )

    content = render_stack_markdown(
        stack,
        generated_at=datetime(2026, 5, 1, 15, 30, tzinfo=timezone.utc),
        akira_version="1.0.0",
    )

    for row in (
        "- **CI/CD**: GitLab CI",
        "- **Cloud**: GCP",
        "- **Cloud**: AWS",
        "- **Infrastructure as code**: Terraform",
        "- **Driver**: psycopg3 3.2.3",
        "- **Cache**: Redis",
    ):
        assert row in content

    assert "- `python/infra/gcp.md`" in content
    assert "- `python/ci_cd/gitlab_ci.md`" not in content
    assert "- `python/infra/aws.md`" not in content
    assert "- `python/infra/terraform.md`" not in content
    assert "- `python/database/redis.md`" not in content


def test_active_skill_hints_match_generated_skill_outputs() -> None:
    generated_paths = {"python/SKILL.md"}
    generated_paths.update(f"python/{template.output_path}" for template in SKILL_TEMPLATES)

    assert set(SKILL_HINTS.values()) <= generated_paths
