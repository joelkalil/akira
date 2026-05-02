from __future__ import annotations

from pathlib import Path

from akira.detect.detectors.database import DatabaseDetector
from akira.detect.detectors.testing import TestingDetector


def test_database_detector_skips_import_scan_when_all_packages_found(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
        "psycopg",
        "psycopg2",
        "redis",
    }


def test_testing_detector_skips_import_scan_when_config_or_dependency_found(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = ["pytest==8.3.0"]
""".strip(),
        encoding="utf-8",
    )

    def fail_scan_imports(project_root: Path) -> set[str]:
        raise AssertionError("scan_imports should not be called")

    monkeypatch.setattr(
        "akira.detect.detectors.testing.scan_imports",
        fail_scan_imports,
    )

    signals = TestingDetector().detect(tmp_path)

    assert [signal.tool for signal in signals] == ["pytest"]
