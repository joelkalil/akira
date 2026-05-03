"""
Tests for e2e workflow.
"""

# Standard Libraries
from __future__ import annotations

import shutil
import socket
from pathlib import Path
from typing import Any

# Third-Party Libraries
import pytest
from typer.testing import CliRunner

# Local Libraries
from akira.cli import app

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

runner = CliRunner()


@pytest.fixture

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Fail fast if an end-to-end workflow tries to open a network socket.
    """

    def blocked_connect(self: socket.socket, address: Any) -> None:
        """
        Return blocked connect result.
        """

        raise AssertionError(f"Network access is not allowed in E2E tests: {address}")

    def blocked_create_connection(*args: Any, **kwargs: Any) -> socket.socket:
        """
        Return blocked create connection result.
        """

        raise AssertionError("Network access is not allowed in E2E tests.")

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)

    monkeypatch.setattr(socket, "create_connection", blocked_create_connection)


class TestInstallWorkflowGeneratesAndInstallsAgentContext:
    """
    Verify install workflow generates and installs agent context cases.
    """

    def test_install_workflow_generates_and_installs_agent_context(
        self,
        tmp_path: Path,
        fixtures_dir: Path,
        no_network: None,
    ) -> None:
        """
        Verify install workflow generates and installs agent context behavior.
        """

        project = tmp_path / "fastapi_project"

        output_dir = tmp_path / ".akira"

        shutil.copytree(fixtures_dir / "fastapi_project", project)

        install_result = runner.invoke(
            app,
            [
                "install",
                "--path",
                str(project),
                "--output",
                str(output_dir),
                "--sample-size",
                "10",
                "--agent",
                "claude-code",
            ],
        )

        stack_path = output_dir / "stack.md"

        fingerprint_path = output_dir / "fingerprint.md"

        skills_dir = output_dir / "skills"

        claude_target = project / ".claude" / "skills" / "akira"

        assert install_result.exit_code == 0

        assert stack_path.exists()

        assert (skills_dir / "SKILL.md").exists()

        assert (skills_dir / "python" / "SKILL.md").exists()

        assert (skills_dir / "python" / "web_framework" / "fastapi.md").exists()

        assert (skills_dir / "python" / "testing" / "pytest.md").exists()

        assert (skills_dir / "python" / "database" / "sqlalchemy.md").exists()

        assert (skills_dir / "python" / "infra" / "docker.md").exists()

        assert "Generating skill tree" in install_result.stdout

        assert "Installing to 1 agents" in install_result.stdout

        assert "CLAUDE.md updated" in install_result.stdout

        stack = stack_path.read_text(encoding="utf-8")

        assert "# Stack - fastapi_project" in stack

        assert "- **Web**: FastAPI" in stack

        assert "- **Framework**: pytest" in stack

        assert "- `python/web_framework/fastapi.md`" in stack

        assert fingerprint_path.exists()

        fingerprint = fingerprint_path.read_text(encoding="utf-8")

        assert "# Developer Fingerprint" in fingerprint

        assert "files_analyzed:" in fingerprint

        assert "## Control Flow" in fingerprint

        assert (claude_target / "SKILL.md").exists()

        assert (claude_target / "stack.md").exists()

        assert (claude_target / "fingerprint.md").exists()

        assert (claude_target / "python" / "web_framework" / "fastapi.md").exists()

        assert (claude_target / "python" / "testing" / "pytest.md").exists()

        claude_md = (project / "CLAUDE.md").read_text(encoding="utf-8")

        assert "/akira detect" in claude_md

        assert "Claude Code" in install_result.stdout


class TestCraftCommandIsRemoved:
    """
    Verify craft is no longer exposed as a command cases.
    """

    def test_craft_command_reports_no_such_command(
        self,
        tmp_path: Path,
        no_network: None,
    ) -> None:
        """
        Verify craft command reports no such command behavior.
        """

        project = tmp_path / "project"

        project.mkdir()

        result = runner.invoke(app, ["craft", "--path", str(project)])

        assert result.exit_code == 2

        assert "No such command" in result.stderr

        assert not (project / ".claude").exists()


class TestUnknownCliSubcommandReportsCleanError:
    """
    Verify unknown cli subcommand reports clean error cases.
    """

    def test_unknown_cli_subcommand_reports_clean_error(self) -> None:
        """
        Verify unknown cli subcommand reports clean error behavior.
        """

        result = runner.invoke(app, ["detcet"])

        output = f"{result.stdout}\n{result.stderr}"

        assert result.exit_code != 0

        assert "detcet" in output

        assert "No such command" in output


class TestAgentCommandsRejectInvalidAgent:
    """
    Verify agent commands reject invalid agent cases.
    """

    @pytest.mark.parametrize("command", ("install", "detect", "fingerprint"))
    def test_agent_commands_reject_invalid_agent(
        self,
        command: str,
        tmp_path: Path,
    ) -> None:
        """
        Verify agent commands reject invalid agent behavior.
        """

        project = tmp_path / "project"

        project.mkdir()

        result = runner.invoke(
            app,
            [command, "--path", str(project), "--agent", "unknown-agent"],
        )

        output = f"{result.stdout}\n{result.stderr}"

        assert result.exit_code != 0

        assert "Unsupported agent 'unknown-agent'" in output

        assert "claude-code" in output

        assert "cursor" in output

        assert "copilot" in output

        assert "codex" in output
