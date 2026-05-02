from __future__ import annotations

import shutil
import socket
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from akira.cli import app


runner = CliRunner()


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail fast if an end-to-end workflow tries to open a network socket."""

    def blocked_connect(self: socket.socket, address: Any) -> None:
        raise AssertionError(f"Network access is not allowed in E2E tests: {address}")

    def blocked_create_connection(*args: Any, **kwargs: Any) -> socket.socket:
        raise AssertionError("Network access is not allowed in E2E tests.")

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)
    monkeypatch.setattr(socket, "create_connection", blocked_create_connection)


def test_v1_workflow_generates_and_installs_agent_context(
    tmp_path: Path,
    fixtures_dir: Path,
    no_network: None,
) -> None:
    project = tmp_path / "fastapi_project"
    output_dir = tmp_path / ".akira"
    shutil.copytree(fixtures_dir / "fastapi_project", project)

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
            "--sample-size",
            "10",
        ],
    )
    craft_result = runner.invoke(
        app,
        [
            "craft",
            "--path",
            str(project),
            "--output",
            str(output_dir),
            "--agent",
            "claude-code",
        ],
    )

    stack_path = output_dir / "stack.md"
    fingerprint_path = output_dir / "fingerprint.md"
    skills_dir = output_dir / "skills"
    claude_target = project / ".claude" / "skills" / "akira"

    assert detect_result.exit_code == 0
    assert stack_path.exists()
    assert (skills_dir / "SKILL.md").exists()
    assert (skills_dir / "python" / "SKILL.md").exists()
    assert (skills_dir / "python" / "web_framework" / "fastapi.md").exists()
    assert (skills_dir / "python" / "testing" / "pytest.md").exists()
    assert (skills_dir / "python" / "database" / "sqlalchemy.md").exists()
    assert (skills_dir / "python" / "infra" / "docker.md").exists()
    assert f"Wrote: {stack_path}" in detect_result.stdout

    stack = stack_path.read_text(encoding="utf-8")
    assert "# Stack - fastapi_project" in stack
    assert "- **Web**: FastAPI" in stack
    assert "- **Framework**: pytest" in stack
    assert "- `python/web_framework/fastapi.md`" in stack

    assert fingerprint_result.exit_code == 0
    assert fingerprint_path.exists()
    fingerprint = fingerprint_path.read_text(encoding="utf-8")
    assert "# Developer Fingerprint" in fingerprint
    assert "files_analyzed:" in fingerprint
    assert "## Control Flow" in fingerprint

    assert craft_result.exit_code == 0
    assert (claude_target / "SKILL.md").exists()
    assert (claude_target / "stack.md").exists()
    assert (claude_target / "fingerprint.md").exists()
    assert (claude_target / "python" / "web_framework" / "fastapi.md").exists()
    assert (claude_target / "python" / "testing" / "pytest.md").exists()
    assert "Agent: claude-code" in craft_result.stdout
    assert f"Installed: {claude_target / 'SKILL.md'}" in craft_result.stdout


@pytest.mark.parametrize("command", ("detect", "fingerprint", "craft"))
def test_commands_report_missing_project_path(command: str) -> None:
    result = runner.invoke(app, [command, "--path", "does-not-exist"])
    output = f"{result.stdout}\n{result.stderr}"

    assert result.exit_code != 0
    assert "does-not-exist" in output
    assert "does not" in output.lower()
    assert "exist" in output.lower()


def test_craft_before_generated_artifacts_reports_required_commands(
    tmp_path: Path,
    no_network: None,
) -> None:
    project = tmp_path / "project"
    output_dir = tmp_path / ".akira"
    project.mkdir()

    result = runner.invoke(
        app,
        ["craft", "--path", str(project), "--output", str(output_dir)],
    )

    assert result.exit_code == 1
    assert "Missing Akira artifacts:" in result.stdout
    assert "stack.md" in result.stdout
    assert "fingerprint.md" in result.stdout
    assert "Run `akira detect --path <project>`" in result.stdout
    assert "Run `akira fingerprint --path <project>`" in result.stdout
    assert not (project / ".claude").exists()


@pytest.mark.parametrize("command", ("detect", "craft"))
def test_agent_commands_reject_invalid_agent(command: str, tmp_path: Path) -> None:
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
