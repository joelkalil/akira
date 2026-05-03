"""
Tests for detector performance.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Third-Party Libraries
import pytest

# Local Libraries
from akira.detect.detectors.database import DatabaseDetector
from akira.detect.detectors.testing import TestingDetector

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


class TestDatabaseDetectorSkipsImportScanWhenAllPackagesFound:
    """
    Verify database detector skips import scan when all packages found cases.
    """

    def test_database_detector_skips_import_scan_when_all_packages_found(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Verify database detector skips import scan when all packages found behavior.
        """

        (tmp_path / "pyproject.toml").write_text(
            """
[project]
dependencies = [
    "sqlalchemy",
    "alembic",
    "asyncpg",
    "psycopg",
    "psycopg2",
    "redis",
]
""".strip(),
            encoding="utf-8",
        )

        def fail_scan_imports(project_root: Path) -> set[str]:
            """
            Return fail scan imports result.
            """

            raise AssertionError("scan_imports should not be called")

        monkeypatch.setattr(
            "akira.detect.detectors.database.scan_imports",
            fail_scan_imports,
        )

        signals = DatabaseDetector().detect(tmp_path)

        assert {signal.tool for signal in signals} == {
            "sqlalchemy",
            "alembic",
            "asyncpg",
            "psycopg3",
            "psycopg2",
            "postgres",
            "redis",
        }


class TestTestingDetectorSkipsImportScanWhenConfigOrDependencyFound:
    """
    Verify testing detector skips import scan when config or dependency found cases.
    """

    def test_testing_detector_skips_import_scan_when_config_or_dependency_found(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Verify testing detector skips import scan when config or dependency.

        found behavior.
        """

        (tmp_path / "pyproject.toml").write_text(
            """
[project]
dependencies = ["pytest==8.3.0"]
""".strip(),
            encoding="utf-8",
        )

        def fail_scan_imports(project_root: Path) -> set[str]:
            """
            Return fail scan imports result.
            """

            raise AssertionError("scan_imports should not be called")

        monkeypatch.setattr(
            "akira.detect.detectors.testing.scan_imports",
            fail_scan_imports,
        )

        signals = TestingDetector().detect(tmp_path)

        assert [signal.tool for signal in signals] == ["pytest"]
