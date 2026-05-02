from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from akira.detect import Scanner, render_stack_markdown


def test_minimal_project_stack_markdown_has_frontmatter_and_runtime(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
requires-python = ">=3.12"
dependencies = []

[tool.uv]
dev-dependencies = []
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "uv.lock").write_text("", encoding="utf-8")

    content = render_stack_markdown(
        Scanner().scan(tmp_path),
        generated_at=datetime(2026, 5, 1, 15, 30, tzinfo=timezone.utc),
        akira_version="1.0.0",
    )
    frontmatter = _frontmatter(content)

    assert frontmatter["generated_at"] == "2026-05-01T15:30:00+00:00"
    assert frontmatter["akira_version"] == "1.0.0"
    assert frontmatter["project_name"] == tmp_path.name
    assert f"# Stack - {tmp_path.name}" in content
    assert "## Runtime" in content
    assert "- **Python**: Python 3.12" in content
    assert "- **Package manager**: uv" in content
    assert "## Framework" not in content
    assert "## Active Skills" in content
    assert "- `python.md`" in content


def test_fastapi_project_stack_markdown_renders_sections_and_active_skills(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
requires-python = ">=3.12"
dependencies = [
    "fastapi==0.115.0",
    "pytest==8.3.0",
    "sqlalchemy==2.0.36",
    "alembic==1.14.0",
]

[tool.ruff]
line-length = 88

[tool.mypy]
strict = true
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "uv.lock").write_text("", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "ci.yml").write_text("name: CI\n", encoding="utf-8")

    content = render_stack_markdown(
        Scanner().scan(tmp_path),
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
        "python.md",
        "web_framework/fastapi.md",
        "testing/pytest.md",
        "database/sqlalchemy.md",
        "database/alembic.md",
        "tooling/ruff.md",
        "tooling/mypy.md",
        "infra/docker.md",
        "ci_cd/github_actions.md",
    ):
        assert f"- `{skill}`" in content


def _frontmatter(content: str) -> dict[str, str]:
    _, raw_frontmatter, _ = content.split("---", 2)
    return yaml.safe_load(raw_frontmatter)
