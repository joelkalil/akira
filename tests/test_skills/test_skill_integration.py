"""
Tests for skill integration.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path
from shutil import copytree

# Third-Party Libraries
import yaml

# Local Libraries
from akira.detect import scan_project
from akira.skills.generator import generate_skills
from akira.skills.installer import install_claude_skills

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


class TestDetectGenerateAndInstallClaudeSkillsForRepresentativeStack:
    """
    Verify detect generate and install claude skills for representative stack cases.
    """

    def test_detect_generate_and_install_claude_skills_for_representative_stack(
        self,
        fixtures_dir: Path,
        tmp_path: Path,
    ) -> None:
        """
        Verify detect generate and install claude skills for representative.

        stack behavior.
        """

        source_project = fixtures_dir / "fastapi_project"

        project = tmp_path / "fastapi_project"

        output = tmp_path / ".akira"

        copytree(source_project, project, ignore=_ignore_generated_cache_dirs)

        stack = scan_project(project)

        expected_tools = {
            ("fastapi", "web_framework"),
            ("pytest", "testing"),
            ("sqlalchemy", "database"),
            ("alembic", "database"),
            ("postgres", "database"),
            ("docker", "infrastructure"),
            ("github-actions", "ci_cd"),
        }

        for tool, category in expected_tools:

            assert stack.has(tool, category=category)

        generated = generate_skills(stack, output)

        generated_paths = {
            path.path.relative_to(output).as_posix() for path in generated
        }

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
            "skills/python/tooling/pre_commit.md",
            "skills/python/tooling/ruff.md",
            "skills/python/tooling/uv.md",
            "skills/python/web_framework/fastapi.md",
        }

        for skill in generated:

            frontmatter = _frontmatter(skill.path.read_text(encoding="utf-8"))

            assert isinstance(frontmatter["name"], str)

            assert isinstance(frontmatter["description"], str)

            assert frontmatter["user-invocable"] is False

        router = (output / "skills" / "SKILL.md").read_text(encoding="utf-8")

        assert "Read `python/web_framework/fastapi.md`" in router

        assert "Read `python/testing/pytest.md`" in router

        assert "Read `python/database/sqlalchemy.md`" in router

        assert "Read `python/database/alembic.md`" in router

        assert "Read `python/database/postgres.md`" in router

        assert "Read `python/infra/docker.md`" in router

        assert "Read `python/ci_cd/github_actions.md`" in router

        (output / "stack.md").write_text("# Stack\n", encoding="utf-8")

        (output / "fingerprint.md").write_text("# Fingerprint\n", encoding="utf-8")

        installed = install_claude_skills(project, output)

        install_root = project / ".claude" / "skills" / "akira"

        installed_paths = {
            item.path.relative_to(install_root).as_posix() for item in installed
        }

        assert "SKILL.md" in installed_paths

        assert "stack.md" in installed_paths

        assert "fingerprint.md" in installed_paths

        assert "python/web_framework/fastapi.md" in installed_paths

        assert "python/testing/pytest.md" in installed_paths

        assert all(
            _is_relative_to(item.path.resolve(), install_root.resolve())
            for item in installed
        )

        assert not (source_project / ".claude").exists()

        installed_router = (install_root / "SKILL.md").read_text(encoding="utf-8")

        assert "`stack.md`" in installed_router

        assert "`fingerprint.md`" in installed_router

        assert "`../stack.md`" not in installed_router

        assert "`../fingerprint.md`" not in installed_router


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _ignore_generated_cache_dirs(
    directory: str,
    names: list[str],
) -> set[str]:
    """
    Return generated cache directory names that should be ignored.
    """

    return {name for name in names if name in {".ruff_cache", "__pycache__"}}


def _frontmatter(content: str) -> dict[str, object]:
    """
    Parse rendered skill frontmatter.
    """

    assert content.startswith("---\n")

    _, raw_frontmatter, _ = content.split("---", 2)

    loaded = yaml.safe_load(raw_frontmatter)

    assert isinstance(loaded, dict)

    return loaded


def _is_relative_to(path: Path, parent: Path) -> bool:
    """
    Return whether a path is relative to a parent directory.
    """

    try:

        path.relative_to(parent)

    except ValueError:

        return False

    return True
