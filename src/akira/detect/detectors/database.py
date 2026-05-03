"""
Detect Python database libraries and services.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Local Libraries
from akira.detect.detectors._python_project import (
    extract_dependencies,
    package_to_import_name,
    scan_imports,
)
from akira.detect.detectors.base import BaseDetector
from akira.detect.models import Signal

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DatabaseDetector(BaseDetector):
    """
    Detect common database libraries from metadata, files, and imports.

    Attributes
    ----------
    order : int
        The order in which this detector should be run relative to other
        detectors. Detectors with
        lower order values will be run before those with higher values. The
        default order is 50.
    DATABASE_PACKAGES : dict[str, str]
        A mapping of Python package names to their corresponding database tools
        or services. This is used to identify which database-related tools are
        likely being used based on the project's dependencies and imports.
    POSTGRES_DRIVERS : set[str]
        A set of package names that are known PostgreSQL drivers.

    Methods
    -------
    name
        A stable name for this detector, used for ordering and diagnostics.
    detect(project_root: Path) -> list[Signal]
        Scan a project and return detected signals.
    """

    order = 50

    DATABASE_PACKAGES = {
        "alembic": "alembic",
        "asyncpg": "asyncpg",
        "psycopg": "psycopg3",
        "psycopg2": "psycopg2",
        "psycopg2-binary": "psycopg2",
        "redis": "redis",
        "sqlalchemy": "sqlalchemy",
    }

    POSTGRES_DRIVERS = {"asyncpg", "psycopg", "psycopg2", "psycopg2-binary"}

    def detect(self, project_root: Path) -> list[Signal]:
        """
        Scan database dependencies, migration config, and imports.

        Parameters
        ----------
        project_root : Path
            The root directory of the project to scan.

        Returns
        -------
        list[Signal]
            A list of detected signals.
        """

        signals: list[Signal] = []

        detected: set[str] = set()

        dependencies = extract_dependencies(project_root)

        def emit(
            tool: str,
            source: str,
            confidence: float,
            *,
            package: str | None = None,
            metadata: dict | None = None,
        ) -> None:
            """
            Return emit result.
            """

            if tool in detected:

                return

            detected.add(tool)

            signals.append(
                Signal(
                    tool=tool,
                    category="database",
                    version=dependencies.get(package or tool),
                    confidence=confidence,
                    source=source,
                    metadata=metadata or {},
                )
            )

        if (project_root / "alembic.ini").exists():

            emit("alembic", "alembic.ini", 1.0, package="alembic")

        if (project_root / "alembic").is_dir():

            emit("alembic", "alembic/", 1.0, package="alembic")

        postgres_driver_detected = False

        for package, tool in self.DATABASE_PACKAGES.items():

            if package in dependencies:

                emit(tool, "dependencies", 0.9, package=package)

                postgres_driver_detected = postgres_driver_detected or (
                    package in self.POSTGRES_DRIVERS
                )

        if postgres_driver_detected:

            emit(
                "postgres",
                "dependencies",
                0.8,
                metadata={"inferred_from": "postgres driver"},
            )

        if _project_mentions_postgres(project_root):

            emit("postgres", "project config", 0.7)

        remaining_packages = {
            package: tool
            for package, tool in self.DATABASE_PACKAGES.items()
            if tool not in detected
        }

        if not remaining_packages:

            return signals

        imports = scan_imports(project_root)

        postgres_import_detected = False

        for package, tool in remaining_packages.items():

            if package_to_import_name(package) in imports:

                emit(tool, "source imports", 0.75, package=package)

                postgres_import_detected = postgres_import_detected or (
                    package in self.POSTGRES_DRIVERS
                )

        if postgres_import_detected:

            emit(
                "postgres",
                "source imports",
                0.65,
                metadata={"inferred_from": "postgres driver import"},
            )

        return signals


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _project_mentions_postgres(project_root: Path) -> bool:
    """
    Return whether lightweight project config hints at PostgreSQL.

    Parameters
    ----------
    project_root : Path
        The root directory of the project to scan.

    Returns
    -------
    bool
        True if the project contains hints of PostgreSQL usage, otherwise False.
    """

    for filename in ("alembic.ini", ".env", ".env.example", "docker-compose.yml"):

        path = project_root / filename

        if not path.exists() or not path.is_file():

            continue

        try:

            content = path.read_text(encoding="utf-8").lower()

        except UnicodeDecodeError:

            continue

        if any(
            token in content for token in ("postgresql://", "postgres://", "postgres:")
        ):

            return True

    for compose_file in ("docker-compose.yaml", "compose.yml", "compose.yaml"):

        path = project_root / compose_file

        if not path.exists() or not path.is_file():

            continue

        try:

            content = path.read_text(encoding="utf-8").lower()

        except UnicodeDecodeError:

            continue

        if "postgres" in content:

            return True

    return False
