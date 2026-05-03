"""
Detect Python testing tools.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Local Libraries
from akira.detect.detectors._python_project import (
    extract_dependencies,
    iter_python_files,
    package_to_import_name,
    read_setup_cfg,
    read_toml,
    scan_imports,
)
from akira.detect.detectors.base import BaseDetector
from akira.detect.models import Signal

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class TestingDetector(BaseDetector):
    """
    Detect common Python test frameworks and runners.

    Attributes
    ----------
    order : int
        The order in which this detector should be run relative to others. Lower
        numbers run first.
    TESTING_TOOLS : dict[str, tuple[str, str]]
        A mapping of package names to tuples containing the tool name and its
        import name.

    Methods
    -------
    detect(project_root: Path) -> list[Signal]
        Scan the project for evidence of testing tools and return a list of signals.
    """

    order = 40

    TESTING_TOOLS = {
        "coverage": ("coverage", "coverage"),
        "nox": ("nox", "nox"),
        "pytest": ("pytest", "pytest"),
        "pytest-asyncio": ("pytest-asyncio", "pytest_asyncio"),
        "pytest-cov": ("pytest-cov", "pytest_cov"),
        "tox": ("tox", "tox"),
    }

    def detect(self, project_root: Path) -> list[Signal]:
        """
        Scan metadata, config files, and imports for testing signals.

        Parameters
        ----------
        project_root : Path
            The root directory of the Python project to analyze.

        Returns
        -------
        list[Signal]
            A list of detected signals related to testing tools.
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
            Emit a signal for a detected testing tool, ensuring no duplicates.

            Parameters
            ----------
            tool : str
                The name of the testing tool being detected.
            source : str
                The source of the detection (e.g., "pyproject.toml", "dependencies").
            confidence : float
                A confidence score between 0 and 1 indicating the
                strength of the signal.
            package : str | None, optional
                The specific package that led to the detection, if applicable.
            metadata : dict | None, optional
                Additional metadata to include with the signal.
            """

            if tool in detected:

                return

            detected.add(tool)

            signals.append(
                Signal(
                    tool=tool,
                    category="testing",
                    version=dependencies.get(package or tool),
                    confidence=confidence,
                    source=source,
                    metadata=metadata or {},
                )
            )

        pyproject = read_toml(project_root / "pyproject.toml")

        pyproject_tools = pyproject.get("tool", {})

        if "pytest" in pyproject_tools:

            emit("pytest", "pyproject.toml", 1.0)

        if "coverage" in pyproject_tools:

            emit("coverage", "pyproject.toml", 1.0)

        if "tox" in pyproject_tools:

            emit("tox", "pyproject.toml", 1.0)

        if "nox" in pyproject_tools:

            emit("nox", "pyproject.toml", 1.0)

        setup_cfg = read_setup_cfg(project_root / "setup.cfg")

        if setup_cfg.has_section("tool:pytest"):

            emit("pytest", "setup.cfg", 1.0)

        if setup_cfg.has_section("coverage:run"):

            emit("coverage", "setup.cfg", 1.0)

        if (project_root / "pytest.ini").exists():

            emit("pytest", "pytest.ini", 1.0)

        if (project_root / ".coveragerc").exists():

            emit("coverage", ".coveragerc", 1.0)

        for filename, tool in (
            ("tox.ini", "tox"),
            ("nox.py", "nox"),
            ("noxfile.py", "nox"),
        ):

            if (project_root / filename).exists():

                emit(tool, filename, 1.0)

        for package, (tool, import_name) in self.TESTING_TOOLS.items():

            if package in dependencies:

                emit(tool, "dependencies", 0.9, package=package)

        for package in sorted(dependencies):

            if package.startswith("pytest-"):

                emit(
                    package,
                    "dependencies",
                    0.9,
                    package=package,
                    metadata={"plugin": True, "framework": "pytest"},
                )

        if not any(iter_python_files(project_root)):

            return signals

        imports = scan_imports(project_root)

        if "unittest" in imports:

            emit("unittest", "source imports", 0.75)

        for package, (tool, import_name) in self.TESTING_TOOLS.items():

            if package_to_import_name(import_name) in imports:

                emit(tool, "source imports", 0.75, package=package)

        return signals
