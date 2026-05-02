from __future__ import annotations

from pathlib import Path

import yaml

from akira.detect import scan_project
from akira.detect.models import Signal, StackInfo
from akira.skills.generator import generate_skills


def test_detected_tools_generate_expected_skill_paths(
    fixtures_dir: Path,
    tmp_path: Path,
) -> None:
    stack = scan_project(fixtures_dir / "fastapi_project")

    generated = generate_skills(stack, tmp_path)

    generated_paths = {path.path.relative_to(tmp_path).as_posix() for path in generated}
    assert generated_paths == {
        "skills/SKILL.md",
        "skills/python/SKILL.md",
        "skills/python/ci_cd/github_actions.md",
        "skills/python/database/alembic.md",
        "skills/python/database/postgres.md",
        "skills/python/database/sqlalchemy.md",
        "skills/python/infra/docker.md",
        "skills/python/testing/pytest.md",
        "skills/python/tooling/mypy.md",
        "skills/python/tooling/ruff.md",
        "skills/python/tooling/uv.md",
        "skills/python/web_framework/fastapi.md",
    }


def test_undetected_tools_do_not_generate_stray_skill_files(
    fixtures_dir: Path,
    tmp_path: Path,
) -> None:
    stack = scan_project(fixtures_dir / "minimal_project")

    generate_skills(stack, tmp_path)

    assert (tmp_path / "skills" / "SKILL.md").exists()
    python_dir = tmp_path / "skills" / "python"
    assert (python_dir / "SKILL.md").exists()
    assert (python_dir / "tooling" / "uv.md").exists()
    assert not (python_dir / "web_framework" / "fastapi.md").exists()
    assert not (python_dir / "testing" / "pytest.md").exists()
    assert not (python_dir / "database" / "sqlalchemy.md").exists()


def test_repeated_generation_removes_stale_managed_skill_files(tmp_path: Path) -> None:
    project = tmp_path / "project"
    output = tmp_path / ".akira"
    project.mkdir()
    rich_stack = StackInfo.from_signals(
        project,
        [
            Signal("python", "runtime", version="3.12", source="test"),
            Signal("fastapi", "web_framework", version="0.115", source="test"),
            Signal("pytest", "testing", version="8.0", source="test"),
        ],
    )
    minimal_stack = StackInfo.from_signals(
        project,
        [Signal("python", "runtime", version="3.12", source="test")],
    )

    generate_skills(rich_stack, output)
    generate_skills(minimal_stack, output)

    assert (output / "skills" / "SKILL.md").exists()
    python_dir = output / "skills" / "python"
    assert (python_dir / "SKILL.md").exists()
    assert not (python_dir / "web_framework" / "fastapi.md").exists()
    assert not (python_dir / "testing" / "pytest.md").exists()


def test_generated_skill_files_have_valid_frontmatter_and_body(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    stack = StackInfo.from_signals(
        project,
        [
            Signal("python", "runtime", version="3.12", source="test"),
            Signal("sqlalchemy", "database", version="2.0", source="test"),
            Signal("postgres", "database", source="test"),
            Signal("mypy", "type_checking", source="test"),
        ],
    )

    generated = generate_skills(stack, tmp_path / ".akira")

    for skill in generated:
        content = skill.path.read_text(encoding="utf-8")
        frontmatter = _frontmatter(content)

        assert isinstance(frontmatter["name"], str)
        assert frontmatter["name"].startswith("akira")
        assert isinstance(frontmatter["description"], str)
        assert frontmatter["description"].strip()
        assert frontmatter["user-invocable"] is False
        assert content.split("---", 2)[2].strip()


def test_root_router_references_project_files_and_active_sub_skills(
    tmp_path: Path,
) -> None:
    project = tmp_path / "portfolio-service"
    project.mkdir()
    stack = StackInfo.from_signals(
        project,
        [
            Signal("python", "runtime", version="3.12", source="test"),
            Signal("fastapi", "web_framework", version="0.115", source="test"),
            Signal("pytest", "testing", version="8.0", source="test"),
            Signal("ruff", "linting", source="test"),
        ],
    )

    generate_skills(stack, tmp_path / ".akira")

    router = (tmp_path / ".akira" / "skills" / "SKILL.md").read_text(
        encoding="utf-8",
    )
    frontmatter = _frontmatter(router)

    assert frontmatter["name"] == "akira"
    assert "portfolio-service" in frontmatter["description"]
    assert "FastAPI + pytest + ruff" in frontmatter["description"]
    assert "`../stack.md`" in router
    assert "`../fingerprint.md`" in router
    assert "Read `python/SKILL.md` when working with Python modules" in router
    assert (
        "Read `python/web_framework/fastapi.md` when working with FastAPI endpoints"
        in router
    )
    assert "Read `python/testing/pytest.md` when working with pytest tests" in router
    assert "Read `python/tooling/ruff.md` when working with Ruff linting" in router


def test_root_router_uses_fingerprint_placeholder_when_missing(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    stack = StackInfo.from_signals(
        project,
        [Signal("python", "runtime", version="3.12", source="test")],
    )

    generate_skills(stack, tmp_path / ".akira")

    router = (tmp_path / ".akira" / "skills" / "SKILL.md").read_text(
        encoding="utf-8",
    )
    assert "`fingerprint.md` may not exist yet" in router
    assert "preserve the" in router
    assert "conventions already present in nearby files" in router


def test_root_router_changes_active_sub_skills_for_different_stacks(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    flask_stack = StackInfo.from_signals(
        project,
        [
            Signal("python", "runtime", version="3.12", source="test"),
            Signal("flask", "web_framework", source="test"),
            Signal("unittest", "testing", source="test"),
        ],
    )
    django_stack = StackInfo.from_signals(
        project,
        [
            Signal("python", "runtime", version="3.12", source="test"),
            Signal("django", "web_framework", source="test"),
            Signal("pytest", "testing", source="test"),
        ],
    )

    generate_skills(flask_stack, tmp_path / "flask")
    generate_skills(django_stack, tmp_path / "django")

    flask_router = (tmp_path / "flask" / "skills" / "SKILL.md").read_text(
        encoding="utf-8",
    )
    django_router = (tmp_path / "django" / "skills" / "SKILL.md").read_text(
        encoding="utf-8",
    )

    assert "python/web_framework/flask.md" in flask_router
    assert "python/testing/unittest.md" in flask_router
    assert "python/web_framework/django.md" not in flask_router
    assert "python/web_framework/django.md" in django_router
    assert "python/testing/pytest.md" in django_router
    assert "python/web_framework/flask.md" not in django_router


def test_root_router_output_is_deterministic_for_signal_order(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    signals = [
        Signal("python", "runtime", version="3.12", source="test"),
        Signal("pytest", "testing", version="8.0", source="test"),
        Signal("fastapi", "web_framework", version="0.115", source="test"),
        Signal("ruff", "linting", source="test"),
    ]

    generate_skills(StackInfo.from_signals(project, signals), tmp_path / "first")
    generate_skills(
        StackInfo.from_signals(project, list(reversed(signals))),
        tmp_path / "second",
    )

    first_router = (tmp_path / "first" / "skills" / "SKILL.md").read_text(
        encoding="utf-8",
    )
    second_router = (tmp_path / "second" / "skills" / "SKILL.md").read_text(
        encoding="utf-8",
    )
    assert first_router == second_router


def _frontmatter(content: str) -> dict[str, object]:
    assert content.startswith("---\n")
    _, raw_frontmatter, _ = content.split("---", 2)
    loaded = yaml.safe_load(raw_frontmatter)
    assert isinstance(loaded, dict)
    return loaded
