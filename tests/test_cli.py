"""
Tests for cli.
"""

# Standard Libraries
from __future__ import annotations

import shutil
import subprocess
import tarfile
from pathlib import Path
from zipfile import ZipFile

# Third-Party Libraries
import pytest
from typer.testing import CliRunner

try:
    import tomllib

except ModuleNotFoundError:
    import tomli as tomllib

# Local Libraries
from akira.cli import app
from akira.config import DEFAULT_OUTPUT_DIR
from akira.craft import (
    UnsupportedCraftAgent,
)
from akira.craft import (
    get_agent_adapter as get_craft_agent_adapter,
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

runner = CliRunner()


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


class TestHelpListsDetectCommand:
    """
    Verify help lists detect command cases.
    """

    def test_help_lists_detect_command(self) -> None:
        """
        Verify help lists detect command behavior.
        """

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0

        assert "Akira detects project context" in result.stdout

        assert "detect" in result.stdout

        assert "fingerprint" in result.stdout

        assert "craft" in result.stdout


class TestDetectHelpDocumentsOptions:
    """
    Verify detect help documents options cases.
    """

    def test_detect_help_documents_options(self) -> None:
        """
        Verify detect help documents options behavior.
        """

        result = runner.invoke(app, ["detect", "--help"])

        assert result.exit_code == 0

        assert "--path" in result.stdout

        assert "--agent" in result.stdout

        assert "--output" in result.stdout


class TestFingerprintHelpDocumentsOptions:
    """
    Verify fingerprint help documents options cases.
    """

    def test_fingerprint_help_documents_options(self) -> None:
        """
        Verify fingerprint help documents options behavior.
        """

        result = runner.invoke(app, ["fingerprint", "--help"])

        assert result.exit_code == 0

        assert "write fingerprint.md output" in result.stdout

        assert "--path" in result.stdout

        assert "--sample-size" in result.stdout

        assert "--exclude" in result.stdout

        assert "--output" in result.stdout


class TestReviewHelpDocumentsOptions:
    """
    Verify review help documents options cases.
    """

    def test_review_help_documents_options(self) -> None:
        """
        Verify review help documents options behavior.
        """

        result = runner.invoke(app, ["review", "--help"])

        assert result.exit_code == 0

        assert "compatibility and best-practice findings" in result.stdout

        assert "--path" in result.stdout

        assert "--strict" in result.stdout

        assert "--auto-apply" in result.stdout


class TestCraftHelpDocumentsOptions:
    """
    Verify craft help documents options cases.
    """

    def test_craft_help_documents_options(self) -> None:
        """
        Verify craft help documents options behavior.
        """

        result = runner.invoke(app, ["craft", "--help"])

        assert result.exit_code == 0

        assert "generated Akira context" in result.stdout

        assert "--path" in result.stdout

        assert "--agent" in result.stdout

        assert "--output" in result.stdout


class TestFingerprintCommandCollectsFilesAndParseFailures:
    """
    Verify fingerprint command collects files and parse failures cases.
    """

    def test_fingerprint_command_collects_files_and_parse_failures(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify fingerprint command collects files and parse failures behavior.
        """

        (tmp_path / "valid.py").write_text("VALUE = 1\n", encoding="utf-8")

        (tmp_path / "broken.py").write_text(
            "def broken(:\n    pass\n",
            encoding="utf-8",
        )

        tests_dir = tmp_path / "tests"

        tests_dir.mkdir()

        (tests_dir / "test_valid.py").write_text(
            "def test_valid():\n    pass\n", encoding="utf-8"
        )

        with runner.isolated_filesystem():

            fingerprint_path = Path.cwd() / DEFAULT_OUTPUT_DIR / "fingerprint.md"

            result = runner.invoke(
                app,
                ["fingerprint", "--path", str(tmp_path), "--exclude", "tests/"],
            )

            fingerprint_exists = fingerprint_path.exists()

        assert result.exit_code == 0

        assert fingerprint_exists

        assert "Files analyzed: 2" in result.stdout

        assert "Parsed: 1" in result.stdout

        assert "Parse failures: 1" in result.stdout

        assert f"Wrote: {fingerprint_path}" in result.stdout


class TestReviewReportsFindingsGroupedByCategory:
    """
    Verify review reports findings grouped by category cases.
    """

    def test_review_reports_findings_grouped_by_category(self, tmp_path: Path) -> None:
        """
        Verify review reports findings grouped by category behavior.
        """

        project = tmp_path / "project"

        project.mkdir()

        (project / "pyproject.toml").write_text(
            """
            [project]
            requires-python = ">=3.12"
            dependencies = [
                "fastapi==0.115.0",
                "ruff==0.8.0",
                "black==24.0.0",
                "alembic==1.13.0",
            ]
            """.strip(),
            encoding="utf-8",
        )

        (project / "tests").mkdir()

        (project / "tests" / "test_service.py").write_text(
            "import unittest\n",
            encoding="utf-8",
        )

        result = runner.invoke(app, ["review", "--path", str(project)])

        assert result.exit_code == 0

        assert "Akira Review" in result.stdout

        assert "Suggestion" in result.stdout

        assert "Incompatibility" in result.stdout

        assert "Missing" in result.stdout

        assert "pytest-over-unittest" in result.stdout

        assert "ruff-replaces-black-isort" in result.stdout

        assert "alembic-needs-sqlalchemy" in result.stdout

        assert "missing-type-checker" in result.stdout


class TestReviewStrictFailsForIncompatibilities:
    """
    Verify review strict fails for incompatibilities cases.
    """

    def test_review_strict_fails_for_incompatibilities(self, tmp_path: Path) -> None:
        """
        Verify review strict fails for incompatibilities behavior.
        """

        project = tmp_path / "project"

        output_dir = tmp_path / ".akira"

        project.mkdir()

        (project / "alembic.ini").write_text("[alembic]\n", encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "review",
                "--path",
                str(project),
                "--output",
                str(output_dir),
                "--strict",
            ],
        )

        assert result.exit_code == 1

        assert "alembic-needs-sqlalchemy" in result.stdout

        assert "Apply?" not in result.stdout

        assert not (output_dir / "stack.md").exists()

        assert not (output_dir / "skills").exists()


class TestReviewAutoApplyUpdatesStackAndRegeneratesSkills:
    """
    Verify review auto apply updates stack and regenerates skills cases.
    """

    def test_review_auto_apply_updates_stack_and_regenerates_skills(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify review auto apply updates stack and regenerates skills behavior.
        """

        project = tmp_path / "project"

        output_dir = tmp_path / ".akira"

        project.mkdir()

        (project / "pyproject.toml").write_text(
            """
            [project]
            requires-python = ">=3.12"
            dependencies = [
                "ruff==0.8.0",
                "black==24.0.0",
            ]
            """.strip(),
            encoding="utf-8",
        )

        (project / "tests").mkdir()

        (project / "tests" / "test_service.py").write_text(
            "import unittest\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            [
                "review",
                "--path",
                str(project),
                "--output",
                str(output_dir),
                "--auto-apply",
            ],
        )

        stack_path = output_dir / "stack.md"

        assert result.exit_code == 0

        assert stack_path.exists()

        stack = stack_path.read_text(encoding="utf-8")

        assert "Accepted changes: 3" in result.stdout

        assert "Skipped changes: 0" in result.stdout

        assert "Regenerated affected skills." in result.stdout

        assert "- **Framework**: pytest" in stack

        assert "- **Type checker**: mypy" in stack

        assert "black" not in stack

        assert (output_dir / "skills" / "python" / "testing" / "pytest.md").exists()

        assert not (
            output_dir / "skills" / "python" / "testing" / "unittest.md"
        ).exists()

        assert (output_dir / "skills" / "python" / "tooling" / "mypy.md").exists()


class TestReviewSkipLeavesArtifactsUnchanged:
    """
    Verify review skip leaves artifacts unchanged cases.
    """

    def test_review_skip_leaves_artifacts_unchanged(self, tmp_path: Path) -> None:
        """
        Verify review skip leaves artifacts unchanged behavior.
        """

        project = tmp_path / "project"

        output_dir = tmp_path / ".akira"

        project.mkdir()

        (project / "pyproject.toml").write_text(
            """
            [project]
            requires-python = ">=3.12"
            dependencies = []
            """.strip(),
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            ["review", "--path", str(project), "--output", str(output_dir)],
            input="n\n",
        )

        assert result.exit_code == 0

        assert "Accepted changes: 0" in result.stdout

        assert "Skipped changes: 1" in result.stdout

        assert not (output_dir / "stack.md").exists()

        assert not (output_dir / "skills").exists()


class TestReviewDetailsShowMigrationGuidanceBeforeAccepting:
    """
    Verify review details show migration guidance before accepting cases.
    """

    def test_review_details_show_migration_guidance_before_accepting(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify review details show migration guidance before accepting behavior.
        """

        project = tmp_path / "project"

        output_dir = tmp_path / ".akira"

        project.mkdir()

        (project / "tests").mkdir()

        (project / "tests" / "test_service.py").write_text(
            "import unittest\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            ["review", "--path", str(project), "--output", str(output_dir)],
            input="details\ny\n",
        )

        assert result.exit_code == 0

        assert "Migration guidance:" in result.stdout

        assert "testing/unittest-to-pytest" in result.stdout

        assert "Accepted changes: 1" in result.stdout

        assert (output_dir / "skills" / "python" / "testing" / "pytest.md").exists()


class TestFingerprintWritesMarkdownToOutput:
    """
    Verify fingerprint writes markdown to output cases.
    """

    def test_fingerprint_writes_markdown_to_output(self, tmp_path: Path) -> None:
        """
        Verify fingerprint writes markdown to output behavior.
        """

        project = tmp_path / "project"

        output_dir = tmp_path / ".akira"

        project.mkdir()

        (project / "module.py").write_text(
            """
            import os

            def load_value(name: str) -> str:
                if not name:
                    return "fallback"
                return f"Hello {name}"
            """,
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            [
                "fingerprint",
                "--path",
                str(project),
                "--sample-size",
                "5",
                "--output",
                str(output_dir),
            ],
        )

        fingerprint_path = output_dir / "fingerprint.md"

        assert result.exit_code == 0

        assert fingerprint_path.exists()

        content = fingerprint_path.read_text(encoding="utf-8")

        assert "sample_size: 5" in content

        assert '  - "module.py"' in content

        assert "confidence:" in content

        assert "## Spacing" in content

        assert "## Control Flow" in content

        assert "## General Patterns" in content


class TestDetectRejectsInvalidPath:
    """
    Verify detect rejects invalid path cases.
    """

    def test_detect_rejects_invalid_path(self) -> None:
        """
        Verify detect rejects invalid path behavior.
        """

        result = runner.invoke(app, ["detect", "--path", "does-not-exist"])

        output = f"{result.stdout}\n{result.stderr}"

        assert result.exit_code != 0

        assert "does-not-exist" in output

        assert "does not" in output.lower()

        assert "exist" in output.lower()


class TestDetectUsesConfigDefaults:
    """
    Verify detect uses config defaults cases.
    """

    def test_detect_uses_output_default_and_agent_fallback(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify detect uses output default and agent fallback behavior.
        """

        with runner.isolated_filesystem():

            expected_output = Path.cwd() / DEFAULT_OUTPUT_DIR

            result = runner.invoke(app, ["detect", "--path", str(tmp_path)])

        assert result.exit_code == 0

        assert (
            "No agent configuration detected. Defaulting to claude-code. "
            "Use --agent to override."
        ) in result.stdout

        assert "Agent: claude-code" in result.stdout

        assert f"Output: {expected_output}" in result.stdout

    def test_detect_auto_selects_claude_code_from_project_marker(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify detect auto selects claude code from project marker behavior.
        """

        (tmp_path / ".claude").mkdir()

        output_dir = tmp_path / ".akira"

        result = runner.invoke(
            app,
            ["detect", "--path", str(tmp_path), "--output", str(output_dir)],
        )

        installed_router = tmp_path / ".claude" / "skills" / "akira" / "SKILL.md"

        assert result.exit_code == 0

        assert "Detected agents: claude-code" in result.stdout

        assert "Agent: claude-code" in result.stdout

        assert installed_router.exists()

    def test_detect_falls_back_to_claude_code_without_agent_markers(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify detect falls back to claude code without agent markers behavior.
        """

        output_dir = tmp_path / ".akira"

        result = runner.invoke(
            app,
            ["detect", "--path", str(tmp_path), "--output", str(output_dir)],
        )

        installed_router = tmp_path / ".claude" / "skills" / "akira" / "SKILL.md"

        assert result.exit_code == 0

        assert (
            "No agent configuration detected. Defaulting to claude-code. "
            "Use --agent to override."
        ) in result.stdout

        assert "Agent: claude-code" in result.stdout

        assert installed_router.exists()


class TestDetectRejectsUnsupportedAgent:
    """
    Verify detect rejects unsupported agent cases.
    """

    def test_detect_rejects_unsupported_agent(self, tmp_path: Path) -> None:
        """
        Verify detect rejects unsupported agent behavior.
        """

        result = runner.invoke(
            app,
            ["detect", "--path", str(tmp_path), "--agent", "unknown-agent"],
        )

        output = f"{result.stdout}\n{result.stderr}"

        assert result.exit_code != 0

        assert "Unsupported agent 'unknown-agent'" in output


class TestDetectRejectsOutputFile:
    """
    Verify detect rejects output file cases.
    """

    def test_detect_rejects_output_file(self, tmp_path: Path) -> None:
        """
        Verify detect rejects output file behavior.
        """

        output_file = tmp_path / "stack.md"

        output_file.write_text("", encoding="utf-8")

        result = runner.invoke(
            app,
            ["detect", "--path", str(tmp_path), "--output", str(output_file)],
        )

        output = f"{result.stdout}\n{result.stderr}"

        assert result.exit_code != 0

        assert output_file.name in output

        assert "file" in output.lower()


class TestFingerprintRejectsOutputFile:
    """
    Verify fingerprint rejects output file cases.
    """

    def test_fingerprint_rejects_output_file(self, tmp_path: Path) -> None:
        """
        Verify fingerprint rejects output file behavior.
        """

        output_file = tmp_path / "fingerprint.md"

        output_file.write_text("", encoding="utf-8")

        result = runner.invoke(
            app,
            ["fingerprint", "--path", str(tmp_path), "--output", str(output_file)],
        )

        output = f"{result.stdout}\n{result.stderr}"

        assert result.exit_code != 0

        assert output_file.name in output

        assert "file" in output.lower()


class TestDetectWritesStackMarkdownToOutput:
    """
    Verify detect writes stack markdown to output cases.
    """

    def test_detect_writes_stack_markdown_to_output(self, tmp_path: Path) -> None:
        """
        Verify detect writes stack markdown to output behavior.
        """

        project = tmp_path / "project"

        output_dir = tmp_path / ".akira"

        project.mkdir()

        (project / "pyproject.toml").write_text(
            """
            [project]
            requires-python = ">=3.12"
            dependencies = ["fastapi==0.115.0"]
            """.strip(),
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            ["detect", "--path", str(project), "--output", str(output_dir)],
        )

        stack_path = output_dir / "stack.md"

        assert result.exit_code == 0

        assert stack_path.exists()

        assert f"Wrote: {stack_path}" in result.stdout


class TestDetectInstallsGeneratedSkillsForClaudeCode:
    """
    Verify detect installs generated skills for claude code cases.
    """

    def test_detect_installs_generated_skills_for_claude_code(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify detect installs generated skills for claude code behavior.
        """

        project = tmp_path / "project"

        output_dir = tmp_path / ".akira"

        project.mkdir()

        (project / "pyproject.toml").write_text(
            """
            [project]
            requires-python = ">=3.12"
            dependencies = ["pytest==8.0.0"]
            """.strip(),
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            [
                "detect",
                "--path",
                str(project),
                "--output",
                str(output_dir),
                "--agent",
                "claude-code",
            ],
        )

        installed_router = project / ".claude" / "skills" / "akira" / "SKILL.md"

        installed_stack = project / ".claude" / "skills" / "akira" / "stack.md"

        assert result.exit_code == 0

        assert installed_router.exists()

        assert installed_stack.exists()

        assert f"Installed: {installed_router}" in result.stdout


class TestCraftInstallsGeneratedContextForDetectedAgentByDefault:
    """
    Verify craft installs generated context for claude code by default cases.
    """

    def test_craft_installs_generated_context_for_detected_agent_by_default(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify craft installs generated context for detected agent by default behavior.
        """

        project = tmp_path / "project"

        output_dir = tmp_path / ".akira"

        project.mkdir()

        (project / "pyproject.toml").write_text(
            """
            [project]
            requires-python = ">=3.12"
            dependencies = ["pytest==8.0.0"]
            """.strip(),
            encoding="utf-8",
        )

        (project / "service.py").write_text(
            """
            def load_value(name: str) -> str:
                if not name:
                    return "fallback"
                return f"Hello {name}"
            """.strip(),
            encoding="utf-8",
        )

        detect_result = runner.invoke(
            app,
            [
                "detect",
                "--path",
                str(project),
                "--output",
                str(output_dir),
                "--agent",
                "cursor",
            ],
        )

        fingerprint_result = runner.invoke(
            app,
            [
                "fingerprint",
                "--path",
                str(project),
                "--output",
                str(output_dir),
            ],
        )

        craft_result = runner.invoke(
            app,
            ["craft", "--path", str(project), "--output", str(output_dir)],
        )

        target = project / ".cursor" / "skills" / "akira"

        assert detect_result.exit_code == 0

        assert fingerprint_result.exit_code == 0

        assert craft_result.exit_code == 0

        assert (target / "SKILL.md").exists()

        assert (target / "stack.md").exists()

        assert (target / "fingerprint.md").exists()

        assert (target / "python" / "testing" / "pytest.md").exists()

        assert "Detected agents: cursor" in craft_result.stdout

        assert "Agent: cursor" in craft_result.stdout

        assert f"Unchanged: {target / 'SKILL.md'}" in craft_result.stdout

        assert f"Installed: {target / 'fingerprint.md'}" in craft_result.stdout


class TestCraftIsIdempotent:
    """
    Verify craft is idempotent cases.
    """

    def test_craft_is_idempotent(self, tmp_path: Path) -> None:
        """
        Verify craft is idempotent behavior.
        """

        project = tmp_path / "project"

        artifacts = tmp_path / ".akira"

        project.mkdir()

        (artifacts / "skills").mkdir(parents=True)

        (artifacts / "skills" / "SKILL.md").write_text("router", encoding="utf-8")

        (artifacts / "stack.md").write_text("stack", encoding="utf-8")

        (artifacts / "fingerprint.md").write_text("fingerprint", encoding="utf-8")

        first = runner.invoke(
            app,
            ["craft", "--path", str(project), "--output", str(artifacts)],
        )

        second = runner.invoke(
            app,
            ["craft", "--path", str(project), "--output", str(artifacts)],
        )

        assert first.exit_code == 0

        assert second.exit_code == 0

        assert "Installed:" in first.stdout

        assert "Unchanged:" in second.stdout


class TestCraftReportsMissingArtifactsWithActions:
    """
    Verify craft reports missing artifacts with actions cases.
    """

    def test_craft_reports_missing_artifacts_with_actions(self, tmp_path: Path) -> None:
        """
        Verify craft reports missing artifacts with actions behavior.
        """

        project = tmp_path / "project"

        output_dir = tmp_path / ".akira"

        project.mkdir()

        result = runner.invoke(
            app,
            ["craft", "--path", str(project), "--output", str(output_dir)],
        )

        assert result.exit_code == 1

        assert "Missing Akira artifacts:" in result.stdout

        assert "Missing:" in result.stdout

        assert "stack.md" in result.stdout

        assert "fingerprint.md" in result.stdout

        assert "Run `akira detect --path <project>`" in result.stdout

        assert "Run `akira fingerprint --path <project>`" in result.stdout

        assert not (project / ".claude").exists()


class TestCraftInstallsGeneratedContextForCodex:
    """
    Verify craft installs generated context for codex cases.
    """

    def test_craft_installs_generated_context_for_codex(self, tmp_path: Path) -> None:
        """
        Verify craft installs generated context for codex behavior.
        """

        project = tmp_path / "project"

        artifacts = tmp_path / ".akira"

        project.mkdir()

        (artifacts / "skills").mkdir(parents=True)

        (artifacts / "skills" / "SKILL.md").write_text("router", encoding="utf-8")

        (artifacts / "stack.md").write_text("stack", encoding="utf-8")

        (artifacts / "fingerprint.md").write_text("fingerprint", encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "craft",
                "--path",
                str(project),
                "--output",
                str(artifacts),
                "--agent",
                "codex",
            ],
        )

        assert result.exit_code == 0

        assert (project / ".codex" / "skills" / "akira" / "SKILL.md").exists()

        assert "Agent: codex" in result.stdout


class TestCraftAgentAdapterWrapperRaisesCraftErrorForInvalidAgent:
    """
    Verify craft agent adapter wrapper raises craft error for invalid agent cases.
    """

    def test_craft_agent_adapter_wrapper_raises_craft_error_for_invalid_agent(
        self,
    ) -> None:
        """
        Verify craft agent adapter wrapper raises craft error for invalid agent.

        behavior.
        """

        with pytest.raises(UnsupportedCraftAgent) as exc_info:

            get_craft_agent_adapter("unknown-agent")

        assert "Unsupported agent 'unknown-agent'" in str(exc_info.value)


class TestCraftDefaultsToCurrentWorkingDirectoryArtifacts:
    """
    Verify craft defaults to current working directory artifacts cases.
    """

    def test_craft_defaults_to_current_working_directory_artifacts(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify craft defaults to current working directory artifacts behavior.
        """

        project = tmp_path / "project"

        project.mkdir()

        with runner.isolated_filesystem():

            artifacts = Path.cwd() / DEFAULT_OUTPUT_DIR

            (artifacts / "skills").mkdir(parents=True)

            (artifacts / "skills" / "SKILL.md").write_text("router", encoding="utf-8")

            (artifacts / "stack.md").write_text("stack", encoding="utf-8")

            (artifacts / "fingerprint.md").write_text("fingerprint", encoding="utf-8")

            result = runner.invoke(app, ["craft", "--path", str(project)])

        assert result.exit_code == 0

        assert (project / ".claude" / "skills" / "akira" / "SKILL.md").exists()

        assert f"Artifacts: {artifacts}" in result.stdout


class TestCraftRejectsArtifactsWithWrongPathTypes:
    """
    Verify craft rejects artifacts with wrong path types cases.
    """

    def test_craft_rejects_artifacts_with_wrong_path_types(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify craft rejects artifacts with wrong path types behavior.
        """

        project = tmp_path / "project"

        artifacts = tmp_path / ".akira"

        project.mkdir()

        (artifacts / "stack.md").mkdir(parents=True)

        (artifacts / "fingerprint.md").write_text("fingerprint", encoding="utf-8")

        (artifacts / "skills").write_text("not a directory", encoding="utf-8")

        result = runner.invoke(
            app,
            ["craft", "--path", str(project), "--output", str(artifacts)],
        )

        assert result.exit_code == 1

        assert f"Missing: {artifacts / 'stack.md'}" in result.stdout

        assert f"Missing: {artifacts / 'skills'}" in result.stdout

        assert f"Missing: {artifacts / 'skills' / 'SKILL.md'}" in result.stdout

        assert not (project / ".claude").exists()


class TestPackageScriptPointsToCliMain:
    """
    Verify package script points to cli main cases.
    """

    def test_package_script_points_to_cli_main(self) -> None:
        """
        Verify package script points to cli main behavior.
        """

        pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

        assert pyproject["project"]["scripts"]["akira"] == "akira.cli:main"


class TestBuildBackendAndPackageDiscoveryAreConfigured:
    """
    Verify build backend and package discovery are configured cases.
    """

    def test_build_backend_and_package_discovery_are_configured(self) -> None:
        """
        Verify build backend and package discovery are configured behavior.
        """

        pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

        assert pyproject["build-system"]["build-backend"] == "hatchling.build"

        assert pyproject["build-system"]["requires"] == ["hatchling>=1.26"]

        assert pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [
            "src/akira"
        ]

        assert pyproject["project"]["requires-python"] == ">=3.11"


class TestReleaseDocsIncludeInstallSmokeStepsAndNameFallbacks:
    """
    Verify release docs include install smoke steps and name fallbacks cases.
    """

    def test_release_docs_include_install_smoke_steps_and_name_fallbacks(self) -> None:
        """
        Verify release docs include install smoke steps and name fallbacks behavior.
        """

        release_docs = Path("docs/RELEASE.md").read_text(encoding="utf-8")

        assert "python -m build" in release_docs

        assert "pip install dist\\*.whl" in release_docs

        assert "uv tool install --force dist\\akira-*.whl" in release_docs

        assert "uvx --from akira-cli akira --help" in release_docs

        assert "uvx --from akira-skills akira --help" in release_docs

        assert 'akira = "akira.cli:main"' in release_docs


class TestBuildArtifactsIncludeJinjaTemplates:
    """
    Verify build artifacts include jinja templates cases.
    """

    def test_build_artifacts_include_jinja_templates(self, tmp_path: Path) -> None:
        """
        Verify build artifacts include jinja templates behavior.
        """

        uv = shutil.which("uv")

        if uv is None:

            pytest.skip(
                "uv is required to build artifacts for package-data validation."
            )

        subprocess.run(
            [uv, "build", "--out-dir", str(tmp_path)],
            check=True,
            cwd=Path.cwd(),
            stdout=subprocess.DEVNULL,
        )

        wheel_path = next(tmp_path.glob("*.whl"))

        sdist_path = next(tmp_path.glob("*.tar.gz"))

        with ZipFile(wheel_path) as archive:

            wheel_names = set(archive.namelist())

            entry_points_name = next(
                name
                for name in wheel_names
                if name.endswith(".dist-info/entry_points.txt")
            )

            entry_points = archive.read(entry_points_name).decode("utf-8")

        with tarfile.open(sdist_path, "r:gz") as archive:
            sdist_names = set(archive.getnames())

        expected_wheel_paths = {
            "akira/detect/templates/stack.md.j2",
            "akira/fingerprint/templates/fingerprint.md.j2",
            "akira/skills/templates/base.md.j2",
            "akira/skills/templates/python/python.md.j2",
            "akira/skills/templates/python/testing/pytest.md.j2",
        }

        expected_sdist_suffixes = {
            "src/akira/detect/templates/stack.md.j2",
            "src/akira/fingerprint/templates/fingerprint.md.j2",
            "src/akira/skills/templates/base.md.j2",
            "src/akira/skills/templates/python/python.md.j2",
            "src/akira/skills/templates/python/testing/pytest.md.j2",
        }

        assert expected_wheel_paths <= wheel_names

        assert "[console_scripts]" in entry_points

        assert "akira = akira.cli:main" in entry_points

        assert all(
            any(name.endswith(suffix) for name in sdist_names)
            for suffix in expected_sdist_suffixes
        )
