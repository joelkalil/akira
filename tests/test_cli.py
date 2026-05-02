from __future__ import annotations

import tomllib
from pathlib import Path

from typer.testing import CliRunner

from akira.cli import app


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


def test_package_script_points_to_cli_main() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    assert pyproject["project"]["scripts"]["akira"] == "akira.cli:main"
