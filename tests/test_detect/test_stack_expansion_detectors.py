"""
Tests for stack expansion detectors.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Local Libraries
from akira.detect import Scanner

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


class TestDetectsTestingToolsAndPytestPlugins:
    """
    Verify detects testing tools and pytest plugins cases.
    """

    def test_detects_testing_tools_and_pytest_plugins(self, tmp_path: Path) -> None:
        """
        Verify detects testing tools and pytest plugins behavior.
        """

        (tmp_path / "pyproject.toml").write_text(
            """
            [project]
            dependencies = [
                "pytest==8.3.0",
                "pytest-cov==5.0.0",
                "pytest-xdist==3.6.0",
                "coverage==7.6.0",
            ]

            [dependency-groups]
            dev = ["tox==4.20.0", "nox==2024.10.9"]

            [tool.pytest.ini_options]
            testpaths = ["tests"]

            [tool.coverage.run]
            branch = true
            """.strip(),
            encoding="utf-8",
        )

        tests_dir = tmp_path / "tests"

        tests_dir.mkdir()

        (tests_dir / "test_smoke.py").write_text(
            "import unittest\n\nclass SmokeTest(unittest.TestCase):\n    pass\n",
            encoding="utf-8",
        )

        stack = Scanner().scan(tmp_path)

        for tool in ("pytest", "pytest-cov", "pytest-xdist", "coverage", "tox", "nox"):

            assert stack.has(tool, category="testing")

        assert stack.has("unittest", category="testing")

        plugin = next(
            signal for signal in stack.signals if signal.tool == "pytest-xdist"
        )

        assert plugin.metadata["plugin"] is True

        assert plugin.source == "dependencies"

        assert plugin.confidence == 0.9


class TestDetectsPytestPluginsFromSourceImports:
    """
    Verify detects pytest plugins from source imports cases.
    """

    def test_detects_pytest_plugins_from_source_imports(self, tmp_path: Path) -> None:
        """
        Verify detects pytest plugins from source imports behavior.
        """

        package = tmp_path / "tests"

        package.mkdir()

        (package / "test_async.py").write_text(
            "import pytest_asyncio\nimport pytest_cov\n",
            encoding="utf-8",
        )

        stack = Scanner().scan(tmp_path)

        assert stack.has("pytest-asyncio", category="testing")

        assert stack.has("pytest-cov", category="testing")


class TestDependencyGroupIncludeObjectsDoNotCrashDetection:
    """
    Verify dependency group include objects do not crash detection cases.
    """

    def test_dependency_group_include_objects_do_not_crash_detection(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify dependency group include objects do not crash detection behavior.
        """

        (tmp_path / "pyproject.toml").write_text(
            """
            [dependency-groups]
            dev = [
                "pytest==8.3.0",
                { include-group = "lint" },
            ]
            lint = ["ruff==0.8.0"]
            """.strip(),
            encoding="utf-8",
        )

        stack = Scanner().scan(tmp_path)

        assert stack.has("pytest", category="testing")

        assert stack.has("ruff", category="linting")


class TestDetectsDatabaseLibrariesMigrationsAndPostgresHints:
    """
    Verify detects database libraries migrations and postgres hints cases.
    """

    def test_detects_database_libraries_migrations_and_postgres_hints(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify detects database libraries migrations and postgres hints behavior.
        """

        (tmp_path / "pyproject.toml").write_text(
            """
            [project]
            dependencies = [
                "sqlalchemy==2.0.36",
                "alembic==1.14.0",
                "psycopg==3.2.3",
                "psycopg2-binary==2.9.10",
                "asyncpg==0.30.0",
                "redis==5.2.0",
            ]
            """.strip(),
            encoding="utf-8",
        )

        (tmp_path / "alembic.ini").write_text(
            "sqlalchemy.url = postgresql://app:app@localhost/app\n",
            encoding="utf-8",
        )

        (tmp_path / "alembic").mkdir()

        stack = Scanner().scan(tmp_path)

        for tool in (
            "sqlalchemy",
            "alembic",
            "psycopg3",
            "asyncpg",
            "redis",
            "postgres",
        ):

            assert stack.has(tool, category="database")

        psycopg_signal = next(
            signal for signal in stack.signals if signal.tool == "psycopg3"
        )

        assert psycopg_signal.version == "3.2.3"

        assert psycopg_signal.source == "dependencies"


class TestDetectsDockerComposeDatabaseServices:
    """
    Verify detects docker compose database services cases.
    """

    def test_detects_docker_compose_database_services(self, tmp_path: Path) -> None:
        """
        Verify detects docker compose database services behavior.
        """

        (tmp_path / "Dockerfile").write_text(
            "FROM python:3.12-slim\n",
            encoding="utf-8",
        )

        (tmp_path / "compose.yaml").write_text(
            """
            services:
            db:
                image: postgres:16
            cache:
                image: redis:7
            """.strip(),
            encoding="utf-8",
        )

        stack = Scanner().scan(tmp_path)

        assert stack.has("docker", category="infrastructure")

        assert stack.has("docker-compose", category="infrastructure")

        assert stack.has("postgres", category="database")

        assert stack.has("redis", category="database")

        compose = next(
            signal for signal in stack.signals if signal.tool == "docker-compose"
        )

        assert compose.metadata["services"] == ("postgres", "redis")

        assert compose.source == "compose.yaml"


class TestDetectsCloudTerraformAndCiCdHints:
    """
    Verify detects cloud terraform and ci cd hints cases.
    """

    def test_detects_cloud_terraform_and_ci_cd_hints(self, tmp_path: Path) -> None:
        """
        Verify detects cloud terraform and ci cd hints behavior.
        """

        github_workflows = tmp_path / ".github" / "workflows"

        github_workflows.mkdir(parents=True)

        (github_workflows / "ci.yml").write_text(
            """
            jobs:
            deploy:
                steps:
                - uses: google-github-actions/auth@v2
                - uses: aws-actions/configure-aws-credentials@v4
            """.strip(),
            encoding="utf-8",
        )

        (tmp_path / ".gitlab-ci.yml").write_text(
            "test:\n  script: pytest\n", encoding="utf-8"
        )

        terraform_dir = tmp_path / "infra" / "prod"

        terraform_dir.mkdir(parents=True)

        (terraform_dir / "main.tf").write_text(
            """
            provider "google" {}
            provider "aws" {}
            """.strip(),
            encoding="utf-8",
        )

        stack = Scanner().scan(tmp_path)

        for tool in ("terraform", "gcp", "aws"):

            assert stack.has(tool, category="infrastructure")

        assert stack.has("github-actions", category="ci_cd")

        assert stack.has("gitlab-ci", category="ci_cd")

        github_actions = next(
            signal for signal in stack.signals if signal.tool == "github-actions"
        )

        assert github_actions.metadata["workflow_files"] == ("ci.yml",)


class TestDetectsDocumentationToolsFromDependenciesAndConfigs:
    """
    Verify detects documentation tools from dependencies and configs cases.
    """

    def test_detects_documentation_tools_from_dependencies_and_configs(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify detects documentation tools from dependencies and configs behavior.
        """

        (tmp_path / "pyproject.toml").write_text(
            """
            [project]
            dependencies = [
                "mkdocs==1.6.1",
                "pdoc==15.0.0",
            ]
            """.strip(),
            encoding="utf-8",
        )

        docs_dir = tmp_path / "docs"

        docs_dir.mkdir()

        (docs_dir / "conf.py").write_text("project = 'Akira'\n", encoding="utf-8")

        stack = Scanner().scan(tmp_path)

        assert stack.has("mkdocs", category="documentation")

        assert stack.has("pdoc", category="documentation")

        assert stack.has("sphinx", category="documentation")
