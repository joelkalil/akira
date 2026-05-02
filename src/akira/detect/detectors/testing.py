"""Detect Python testing tools."""

from __future__ import annotations

from pathlib import Path

from akira.detect.detectors._python_project import (
    extract_dependencies,
    package_to_import_name,
    read_setup_cfg,
    read_toml,
    scan_imports,
)
from akira.detect.detectors.base import BaseDetector
from akira.detect.models import Signal


class TestingDetector(BaseDetector):
    """Detect common Python test frameworks and runners."""

    order = 40

    TESTING_TOOLS = {
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "tox",
        "nox",
        "coverage",
    }

    def detect(self, project_root: Path) -> list[Signal]:
        """Scan metadata, config files, and imports for testing signals."""
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
                    category="testing",
                    version=dependencies.get(tool),
                    confidence=confidence,
                    source=source,
                )
            )

        pyproject = read_toml(project_root / "pyproject.toml")
        pyproject_tools = pyproject.get("tool", {})
        if "pytest" in pyproject_tools:
            emit("pytest", "pyproject.toml", 1.0)
        if "coverage" in pyproject_tools:
            emit("coverage", "pyproject.toml", 1.0)

        setup_cfg = read_setup_cfg(project_root / "setup.cfg")
        if setup_cfg.has_section("tool:pytest"):
            emit("pytest", "setup.cfg", 1.0)
        if setup_cfg.has_section("coverage:run"):
            emit("coverage", "setup.cfg", 1.0)

        for filename, tool in (("tox.ini", "tox"), ("nox.py", "nox")):
            if (project_root / filename).exists():
                emit(tool, filename, 1.0)

        for tool in self.TESTING_TOOLS:
            if tool in dependencies:
                emit(tool, "dependencies", 0.9)

        imports = scan_imports(project_root)
        if "unittest" in imports:
            emit("unittest", "source imports", 0.75)
        for tool in self.TESTING_TOOLS:
            if package_to_import_name(tool) in imports:
                emit(tool, "source imports", 0.75)

        return signals
