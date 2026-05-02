"""Detect Python database libraries and services."""

from __future__ import annotations

from pathlib import Path

from akira.detect.detectors._python_project import (
    extract_dependencies,
    package_to_import_name,
    scan_imports,
)
from akira.detect.detectors.base import BaseDetector
from akira.detect.models import Signal


class DatabaseDetector(BaseDetector):
    """Detect common database libraries from metadata, files, and imports."""

    order = 50

    DATABASE_PACKAGES = {
        "sqlalchemy",
        "alembic",
        "asyncpg",
        "psycopg",
        "psycopg2",
        "redis",
    }

    def detect(self, project_root: Path) -> list[Signal]:
        """Scan database dependencies, migration config, and imports."""
        signals: list[Signal] = []
        detected: set[str] = set()
        dependencies = extract_dependencies(project_root)

        def emit(tool: str, source: str, confidence: float) -> None:
            if tool in detected:
                return
            detected.add(tool)
            signals.append(
                Signal(
                    tool=tool,
                    category="database",
                    version=dependencies.get(tool),
                    confidence=confidence,
                    source=source,
                )
            )

        if (project_root / "alembic.ini").exists() or (project_root / "alembic").exists():
            emit("alembic", "alembic config", 1.0)

        for package in self.DATABASE_PACKAGES:
            if package in dependencies:
                emit(package, "dependencies", 0.9)

        remaining_packages = self.DATABASE_PACKAGES - detected
        if not remaining_packages:
            return signals

        imports = scan_imports(project_root)
        for package in remaining_packages:
            if package_to_import_name(package) in imports:
                emit(package, "source imports", 0.75)

        return signals
