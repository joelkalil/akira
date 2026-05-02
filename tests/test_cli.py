from __future__ import annotations

import tomllib
from pathlib import Path

from typer.testing import CliRunner

from akira.cli import app
from akira.config import DEFAULT_AGENT, DEFAULT_OUTPUT_DIR


runner = CliRunner()


def test_help_lists_detect_command() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Akira detects project context" in result.stdout
    assert "detect" in result.stdout


def test_detect_help_documents_options() -> None:
    result = runner.invoke(app, ["detect", "--help"])

    assert result.exit_code == 0
    assert "--path" in result.stdout
    assert "--agent" in result.stdout
    assert "--output" in result.stdout


def test_detect_rejects_invalid_path() -> None:
    result = runner.invoke(app, ["detect", "--path", "does-not-exist"])
    output = f"{result.stdout}\n{result.stderr}"

    assert result.exit_code != 0
    assert "does-not-exist" in output
    assert "does not" in output.lower()
    assert "exist" in output.lower()


def test_detect_uses_config_defaults(tmp_path: Path) -> None:
    result = runner.invoke(app, ["detect", "--path", str(tmp_path)])

    assert result.exit_code == 0
    assert f"Agent: {DEFAULT_AGENT}" in result.stdout
    assert f"Output: {Path.cwd() / DEFAULT_OUTPUT_DIR}" in result.stdout


def test_detect_rejects_unsupported_agent(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["detect", "--path", str(tmp_path), "--agent", "unknown-agent"],
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.exit_code != 0
    assert "Unsupported agent 'unknown-agent'" in output


def test_detect_rejects_output_file(tmp_path: Path) -> None:
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


def test_package_script_points_to_cli_main() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    assert pyproject["project"]["scripts"]["akira"] == "akira.cli:main"
