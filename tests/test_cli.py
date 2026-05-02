from __future__ import annotations

import shutil
import subprocess
import tomllib
from pathlib import Path
from zipfile import ZipFile

import pytest
from typer.testing import CliRunner

from akira.cli import app
from akira.config import DEFAULT_AGENT, DEFAULT_OUTPUT_DIR


runner = CliRunner()


def test_help_lists_detect_command() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Akira detects project context" in result.stdout
    assert "detect" in result.stdout
    assert "fingerprint" in result.stdout


def test_detect_help_documents_options() -> None:
    result = runner.invoke(app, ["detect", "--help"])

    assert result.exit_code == 0
    assert "--path" in result.stdout
    assert "--agent" in result.stdout
    assert "--output" in result.stdout


def test_fingerprint_help_documents_options() -> None:
    result = runner.invoke(app, ["fingerprint", "--help"])

    assert result.exit_code == 0
    assert "--path" in result.stdout
    assert "--sample-size" in result.stdout
    assert "--exclude" in result.stdout
    assert "--output" in result.stdout


def test_fingerprint_command_collects_files_and_parse_failures(tmp_path: Path) -> None:
    (tmp_path / "valid.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "broken.py").write_text("def broken(:\n    pass\n", encoding="utf-8")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_valid.py").write_text("def test_valid():\n    pass\n", encoding="utf-8")

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


def test_fingerprint_writes_markdown_to_output(tmp_path: Path) -> None:
    project = tmp_path / "project"
    output_dir = tmp_path / ".akira"
    project.mkdir()
    (project / "module.py").write_text(
        '''import os


def load_value(name: str) -> str:
    if not name:
        return "fallback"
    return f"Hello {name}"
''',
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
    content = fingerprint_path.read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert fingerprint_path.exists()
    assert "sample_size: 5" in content
    assert '  - "module.py"' in content
    assert "confidence:" in content
    assert "## Spacing" in content
    assert "## Control Flow" in content
    assert "## General Patterns" in content


def test_detect_rejects_invalid_path() -> None:
    result = runner.invoke(app, ["detect", "--path", "does-not-exist"])
    output = f"{result.stdout}\n{result.stderr}"

    assert result.exit_code != 0
    assert "does-not-exist" in output
    assert "does not" in output.lower()
    assert "exist" in output.lower()


def test_detect_uses_config_defaults(tmp_path: Path) -> None:
    with runner.isolated_filesystem():
        expected_output = Path.cwd() / DEFAULT_OUTPUT_DIR
        result = runner.invoke(app, ["detect", "--path", str(tmp_path)])

    assert result.exit_code == 0
    assert f"Agent: {DEFAULT_AGENT}" in result.stdout
    assert f"Output: {expected_output}" in result.stdout


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


def test_detect_writes_stack_markdown_to_output(tmp_path: Path) -> None:
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


def test_detect_installs_generated_skills_for_claude_code(tmp_path: Path) -> None:
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

    installed_router = (
        project / ".claude" / "skills" / "akira" / "SKILL.md"
    )
    installed_stack = (
        project / ".claude" / "skills" / "akira" / "stack.md"
    )
    assert result.exit_code == 0
    assert installed_router.exists()
    assert installed_stack.exists()
    assert f"Installed: {installed_router}" in result.stdout


def test_package_script_points_to_cli_main() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    assert pyproject["project"]["scripts"]["akira"] == "akira.cli:main"


def test_wheel_build_includes_jinja_templates(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is required to build the wheel for package-data validation.")

    subprocess.run(
        [uv, "build", "--wheel", "--out-dir", str(tmp_path)],
        check=True,
        cwd=Path.cwd(),
        stdout=subprocess.DEVNULL,
    )
    wheel_path = next(tmp_path.glob("*.whl"))

    with ZipFile(wheel_path) as archive:
        names = set(archive.namelist())

    assert "akira/detect/templates/stack.md.j2" in names
    assert "akira/fingerprint/templates/fingerprint.md.j2" in names
    assert "akira/skills/templates/base.md.j2" in names
    assert "akira/skills/templates/python/python.md.j2" in names
    assert "akira/skills/templates/python/testing/pytest.md.j2" in names
