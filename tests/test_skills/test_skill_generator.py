"""
Tests for skill generator.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Third-Party Libraries
import yaml

# Local Libraries
from akira.detect import scan_project
from akira.detect.models import Signal, StackInfo
from akira.fingerprint import fingerprint_project
from akira.skills.generator import generate_skills

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


class TestDetectedToolsGenerateExpectedSkillPaths:
    """
    Verify detected tools generate expected skill paths cases.
    """

    def test_detected_tools_generate_expected_skill_paths(
        self,
        fixtures_dir: Path,
        tmp_path: Path,
    ) -> None:
        """
        Verify detected tools generate expected skill paths behavior.
        """

        stack = scan_project(fixtures_dir / "fastapi_project")

        generated = generate_skills(stack, tmp_path)

        generated_paths = {
            path.path.relative_to(tmp_path).as_posix() for path in generated
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
            "skills/python/tooling/ruff.md",
            "skills/python/tooling/uv.md",
            "skills/python/web_framework/fastapi.md",
        }


class TestUndetectedToolsDoNotGenerateStraySkillFiles:
    """
    Verify undetected tools do not generate stray skill files cases.
    """

    def test_undetected_tools_do_not_generate_stray_skill_files(
        self,
        fixtures_dir: Path,
        tmp_path: Path,
    ) -> None:
        """
        Verify undetected tools do not generate stray skill files behavior.
        """

        stack = scan_project(fixtures_dir / "minimal_project")

        generate_skills(stack, tmp_path)

        assert (tmp_path / "skills" / "SKILL.md").exists()

        python_dir = tmp_path / "skills" / "python"

        assert (python_dir / "SKILL.md").exists()

        assert (python_dir / "tooling" / "uv.md").exists()

        assert not (python_dir / "web_framework" / "fastapi.md").exists()

        assert not (python_dir / "testing" / "pytest.md").exists()

        assert not (python_dir / "database" / "sqlalchemy.md").exists()


class TestRepeatedGenerationRemovesStaleManagedSkillFiles:
    """
    Verify repeated generation removes stale managed skill files cases.
    """

    def test_repeated_generation_removes_stale_managed_skill_files(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify repeated generation removes stale managed skill files behavior.
        """

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


class TestGeneratedSkillFilesHaveValidFrontmatterAndBody:
    """
    Verify generated skill files have valid frontmatter and body cases.
    """

    def test_generated_skill_files_have_valid_frontmatter_and_body(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify generated skill files have valid frontmatter and body behavior.
        """

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


class TestRootRouterReferencesProjectFilesAndActiveSubSkills:
    """
    Verify root router references project files and active sub skills cases.
    """

    def test_root_router_references_project_files_and_active_sub_skills(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify root router references project files and active sub skills behavior.
        """

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

        assert (
            "Read `python/testing/pytest.md` when working with pytest tests" in router
        )

        assert "Read `python/tooling/ruff.md` when working with Ruff linting" in router


class TestRootRouterUsesFingerprintPlaceholderWhenMissing:
    """
    Verify root router uses fingerprint placeholder when missing cases.
    """

    def test_root_router_uses_fingerprint_placeholder_when_missing(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify root router uses fingerprint placeholder when missing behavior.
        """

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


class TestRootRouterIncludesCoreRulesFromStructuredFingerprint:
    """
    Verify root router includes core rules from structured fingerprint cases.
    """

    def test_root_router_includes_core_rules_from_structured_fingerprint(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify root router includes core rules from structured fingerprint behavior.
        """

        project = tmp_path / "project"

        project.mkdir()

        (project / "module.py").write_text(
            """
            from __future__ import annotations

            import os
            import sys


            def build_name(value: str | None) -> str:
                if value is None:
                    return "anonymous"

                return f"{value}"
            """,
            encoding="utf-8",
        )

        stack = StackInfo.from_signals(
            project,
            [Signal("python", "runtime", version="3.12", source="test")],
        )

        output = tmp_path / ".akira"

        analysis = fingerprint_project(project)

        generate_skills(stack, output, fingerprint=analysis)

        router = (output / "skills" / "SKILL.md").read_text(encoding="utf-8")

        assert "## Core Rules From Fingerprint" in router

        assert "- Prefer early returns over deeply nested branches." in router

        assert "- Put guard clauses near the top of functions." in router

        assert "- Use full type hints on function signatures." in router

        assert "- Use `X | None` syntax for optional values." in router

        assert "Treat `fingerprint.md` as the source of truth" not in router

        assert "`fingerprint.md` exists" not in router

        assert "`fingerprint.md` may not exist yet" not in router


class TestRootRouterDoesNotRescanWhenOnlyFingerprintFileExists:
    """
    Verify root router does not rescan when only fingerprint file exists cases.
    """

    def test_root_router_does_not_rescan_when_only_fingerprint_file_exists(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify root router does not rescan when only fingerprint file exists behavior.
        """

        project = tmp_path / "project"

        project.mkdir()

        (project / "module.py").write_text(
            """
            def build_name(value: str | None) -> str:
                if value is None:
                    return "anonymous"

                return f"{value}"
            """,
            encoding="utf-8",
        )

        output = tmp_path / ".akira"

        output.mkdir()

        (output / "fingerprint.md").write_text(
            "# Developer Fingerprint\n", encoding="utf-8"
        )

        stack = StackInfo.from_signals(
            project,
            [Signal("python", "runtime", version="3.12", source="test")],
        )

        generate_skills(stack, output)

        router = (output / "skills" / "SKILL.md").read_text(encoding="utf-8")

        assert "`fingerprint.md` exists" in router

        assert "enough high-confidence" in router

        assert "Prefer early returns" not in router

        assert "`fingerprint.md` may not exist yet" not in router


class TestRootRouterChangesActiveSubSkillsForDifferentStacks:
    """
    Verify root router changes active sub skills for different stacks cases.
    """

    def test_root_router_changes_active_sub_skills_for_different_stacks(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify root router changes active sub skills for different stacks behavior.
        """

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


class TestRootRouterOutputIsDeterministicForSignalOrder:
    """
    Verify root router output is deterministic for signal order cases.
    """

    def test_root_router_output_is_deterministic_for_signal_order(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify root router output is deterministic for signal order behavior.
        """

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


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _frontmatter(content: str) -> dict[str, object]:
    """
    Parse rendered skill frontmatter.
    """

    assert content.startswith("---\n")

    _, raw_frontmatter, _ = content.split("---", 2)

    loaded = yaml.safe_load(raw_frontmatter)

    assert isinstance(loaded, dict)

    return loaded
