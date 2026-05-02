# Standard Libraries
from __future__ import annotations
from pathlib import Path

# Third-Party Libraries

# Local Libraries
from akira.detect import Scanner

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def test_minimal_pyproject_emits_runtime_and_package_manager_signals(
    fixtures_dir: Path,
) -> None:
    project_root = fixtures_dir / "minimal_project"

    stack = Scanner().scan(project_root)

    assert stack.has("python", category="runtime")

    assert stack.has("uv", category="package_manager")

    python_signal = next(signal for signal in stack.signals if signal.tool == "python")

    assert python_signal.version == "3.12"

    assert python_signal.source == "pyproject.toml"

    assert python_signal.confidence == 1.0


def test_fastapi_fixture_emits_framework_testing_and_tooling_signals(
    fixtures_dir: Path,
) -> None:
    stack = Scanner().scan(fixtures_dir / "fastapi_project")

    expected_by_category = {
        "web_framework": {"fastapi"},
        "testing": {"pytest", "pytest-asyncio"},
        "linting": {"ruff"},
        "type_checking": {"mypy"},
        "pre_commit": {"pre-commit"},
        "package_manager": {"uv"},
    }

    for category, tools in expected_by_category.items():
        assert tools <= {
            signal.tool for signal in stack.signals if signal.category == category
        }, category

    fastapi_signal = next(
        signal for signal in stack.signals if signal.tool == "fastapi"
    )

    assert fastapi_signal.version == "0.115.0"

    assert fastapi_signal.source == "dependencies"


def test_django_fixture_emits_framework_signal(fixtures_dir: Path) -> None:
    stack = Scanner().scan(fixtures_dir / "django_project")

    assert stack.has("django", category="web_framework")

    django_signal = next(signal for signal in stack.signals if signal.tool == "django")

    assert django_signal.version == "5.0.0"

    assert django_signal.source == "dependencies"


def test_detects_frameworks_from_dependencies(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = [
    "fastapi==0.115.0",
    "typer>=0.15",
]
""".strip(),
        encoding="utf-8",
    )

    stack = Scanner().scan(tmp_path)

    assert stack.has("fastapi", category="web_framework")

    assert stack.has("typer", category="cli_framework")

    fastapi_signal = next(
        signal for signal in stack.signals if signal.tool == "fastapi"
    )

    assert fastapi_signal.version == "0.115.0"

    assert fastapi_signal.source == "dependencies"

    assert fastapi_signal.confidence == 1.0


def test_detects_frameworks_from_source_imports(tmp_path: Path) -> None:
    package = tmp_path / "src" / "sample"

    package.mkdir(parents=True)

    (package / "app.py").write_text(
        "from flask import Flask\nimport click\n",
        encoding="utf-8",
    )

    stack = Scanner().scan(tmp_path)

    assert stack.has("flask", category="web_framework")

    assert stack.has("click", category="cli_framework")

    flask_signal = next(signal for signal in stack.signals if signal.tool == "flask")

    assert flask_signal.source == "source imports"

    assert flask_signal.confidence == 0.75


def test_detects_ruff_mypy_and_pre_commit_from_config(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.ruff]
line-length = 88

[tool.mypy]
strict = true
""".strip(),
        encoding="utf-8",
    )

    (tmp_path / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")

    stack = Scanner().scan(tmp_path)

    assert stack.has("ruff", category="linting")

    assert stack.has("mypy", category="type_checking")

    assert stack.has("pre-commit", category="pre_commit")

    for tool in ("ruff", "mypy", "pre-commit"):
        signal = next(signal for signal in stack.signals if signal.tool == tool)

        assert signal.source

        assert signal.confidence == 1.0


def test_later_pinned_dependency_updates_unpinned_dependency(
    tmp_path: Path,
) -> None:
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")

    (tmp_path / "requirements-dev.txt").write_text(
        "fastapi==0.115.0\n",
        encoding="utf-8",
    )

    stack = Scanner().scan(tmp_path)

    fastapi_signal = next(
        signal for signal in stack.signals if signal.tool == "fastapi"
    )

    assert fastapi_signal.version == "0.115.0"


def test_tooling_config_signal_uses_dependency_version_without_duplicate(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = ["ruff==0.8.0"]

[tool.ruff]
line-length = 88
""".strip(),
        encoding="utf-8",
    )

    stack = Scanner().scan(tmp_path)

    ruff_signals = [signal for signal in stack.signals if signal.tool == "ruff"]

    assert len(ruff_signals) == 1

    assert ruff_signals[0].version == "0.8.0"

    assert ruff_signals[0].source == "pyproject.toml"

    assert ruff_signals[0].confidence == 1.0


def test_parse_setup_cfg_setup_py_and_requirements_txt(tmp_path: Path) -> None:
    (tmp_path / "setup.cfg").write_text(
        """
[options]
install_requires =
    django==5.0
    black==24.1

[flake8]
max-line-length = 88
""".strip(),
        encoding="utf-8",
    )

    (tmp_path / "setup.py").write_text(
        """
from setuptools import setup

setup(install_requires=["streamlit==1.40.0"])
""".strip(),
        encoding="utf-8",
    )

    (tmp_path / "requirements-dev.txt").write_text(
        "pyright==1.1.380\n",
        encoding="utf-8",
    )

    stack = Scanner().scan(tmp_path)

    assert stack.has("pip", category="package_manager")

    assert stack.has("django", category="web_framework")

    assert stack.has("streamlit", category="web_framework")

    assert stack.has("black", category="formatting")

    assert stack.has("flake8", category="linting")

    assert stack.has("pyright", category="type_checking")
