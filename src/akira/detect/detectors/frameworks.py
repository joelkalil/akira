"""
Detect Python web and CLI frameworks.
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


class FrameworkDetector(BaseDetector):
    """
    Detect common Python frameworks from dependencies and imports.

    Attributes
    ----------
    order : int
        The order in which this detector should be run relative to others.
    FRAMEWORKS : dict[str, str]
        A mapping of package names to their framework categories.

    Methods
    -------
    detect(project_root: Path) -> list[Signal]
        Analyze the project to identify used frameworks and return signals.
    """

    order = 20

    FRAMEWORKS = {
        "fastapi": "web_framework",
        "flask": "web_framework",
        "django": "web_framework",
        "streamlit": "web_framework",
        "typer": "cli_framework",
        "click": "cli_framework",
    }

    def detect(self, project_root: Path) -> list[Signal]:
        """
        Scan project metadata and source imports for frameworks.

        Parameters
        ----------
        project_root : Path
            The root directory of the project to analyze.

        Returns
        -------
        list[Signal]
            A list of detected framework signals with confidence scores.
        """

        signals: list[Signal] = []

        dependencies = extract_dependencies(project_root)

        for package, category in self.FRAMEWORKS.items():
            if package in dependencies:
                signals.append(
                    Signal(
                        tool=package,
                        category=category,
                        version=dependencies[package],
                        confidence=1.0,
                        source="dependencies",
                    )
                )

        imported_modules = scan_imports(project_root)

        detected = {signal.tool for signal in signals}

        for package, category in self.FRAMEWORKS.items():
            import_name = package_to_import_name(package)

            if package not in detected and import_name in imported_modules:
                signals.append(
                    Signal(
                        tool=package,
                        category=category,
                        confidence=0.75,
                        source="source imports",
                    )
                )

        return signals
