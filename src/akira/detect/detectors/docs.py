"""
Detect Python documentation tooling.
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
# Constants
# -----------------------------------------------------------------------------

DOC_TOOLS = {
    "mkdocs": "mkdocs",
    "pdoc": "pdoc",
    "sphinx": "sphinx",
}


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DocsDetector(BaseDetector):
    """
    Detect documentation generators from metadata, config files, and imports.

    Attributes
    ----------
    order : int
        The order in which this detector runs relative to other detectors.

    Methods
    -------
    detect(project_root: Path) -> list[Signal]
        Scan documentation dependencies, config files, and imports.
    """

    order = 80

    def detect(self, project_root: Path) -> list[Signal]:
        """
        Scan documentation dependencies, config files, and imports.

        Parameters
        ----------
        project_root : Path
            Root directory of the project being scanned.

        Returns
        -------
        list[Signal]
            Detected documentation tool signals.
        """

        signals: list[Signal] = []

        detected: set[str] = set()

        dependencies = extract_dependencies(project_root)

        for package, tool in DOC_TOOLS.items():

            if package in dependencies:

                detected.add(tool)

                signals.append(
                    Signal(
                        tool=tool,
                        category="documentation",
                        version=dependencies.get(package),
                        confidence=0.9,
                        source="dependencies",
                    )
                )

        for tool, path in _documentation_config_files(project_root).items():

            if tool in detected:

                continue

            detected.add(tool)

            signals.append(
                Signal(
                    tool=tool,
                    category="documentation",
                    confidence=1.0,
                    source=str(path.relative_to(project_root)),
                )
            )

        remaining = {
            package: tool for package, tool in DOC_TOOLS.items() if tool not in detected
        }

        if not remaining:

            return signals

        imports = scan_imports(project_root)

        for package, tool in remaining.items():

            if package_to_import_name(package) not in imports:

                continue

            signals.append(
                Signal(
                    tool=tool,
                    category="documentation",
                    version=dependencies.get(package),
                    confidence=0.75,
                    source="source imports",
                )
            )

        return signals


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _documentation_config_files(project_root: Path) -> dict[str, Path]:
    """
    Return documentation config files found in the project.

    Parameters
    ----------
    project_root : Path
        Root directory of the project being scanned.

    Returns
    -------
    dict[str, Path]
        Mapping of documentation tool names to config file paths.
    """

    config_files: dict[str, Path] = {}

    mkdocs_config = project_root / "mkdocs.yml"

    if mkdocs_config.is_file():

        config_files["mkdocs"] = mkdocs_config

    sphinx_config = project_root / "docs" / "conf.py"

    if sphinx_config.is_file():

        config_files["sphinx"] = sphinx_config

    pdoc_config = project_root / "pdoc.toml"

    if pdoc_config.is_file():

        config_files["pdoc"] = pdoc_config

    return config_files
