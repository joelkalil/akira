"""
Detect Python linting, formatting, type checking, and hook tooling.
"""

# Standard Libraries
from __future__ import annotations
from pathlib import Path

# Local Libraries
from akira.detect.detectors._python_project import (
    extract_dependencies,
    read_setup_cfg,
    read_toml,
)
from akira.detect.detectors.base import BaseDetector
from akira.detect.models import Signal

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ToolingDetector(BaseDetector):
    """
    Detect common Python developer tooling.

    Attributes
    ----------
    order : int
        The order in which this detector should be run relative to others.
    TOOL_CATEGORIES : dict[str, str]
        Mapping of tool names to their categories (e.g., linting, formatting).
    PYPROJECT_TOOL_KEYS : dict[str, str]
        Mapping of tool names to their corresponding keys in pyproject.toml.
    SETUP_CFG_SECTIONS : dict[str, str]
        Mapping of tool names to their corresponding sections in setup.cfg.
    ROOT_CONFIG_FILES : dict[str, tuple[str, ...]]
        Mapping of tool names to tuples of possible root configuration filenames.

    Methods
    -------
    detect(project_root: Path) -> list[Signal]
        Scan metadata and configuration files for tool signals.
    """

    order = 30

    TOOL_CATEGORIES = {
        "ruff": "linting",
        "mypy": "type_checking",
        "pyright": "type_checking",
        "pytype": "type_checking",
        "black": "formatting",
        "isort": "formatting",
        "flake8": "linting",
        "pre-commit": "pre_commit",
    }

    PYPROJECT_TOOL_KEYS = {
        "ruff": "ruff",
        "mypy": "mypy",
        "pyright": "pyright",
        "pytype": "pytype",
        "black": "black",
        "isort": "isort",
    }

    SETUP_CFG_SECTIONS = {
        "mypy": "mypy",
        "flake8": "flake8",
        "isort": "isort",
        "pytype": "pytype",
    }

    ROOT_CONFIG_FILES = {
        "mypy": ("mypy.ini", ".mypy.ini"),
        "pyright": ("pyrightconfig.json",),
        "pytype": ("pytype.cfg",),
        "flake8": (".flake8",),
        "pre-commit": (".pre-commit-config.yaml", ".pre-commit-config.yml"),
    }

    def detect(self, project_root: Path) -> list[Signal]:
        """
        Scan metadata and configuration files for tool signals.

        Parameters
        ----------
        project_root : Path
            The root directory of the project to scan.

        Returns
        -------
        list[Signal]
            A list of detected tooling signals.
        """

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
                    category=self.TOOL_CATEGORIES[tool],
                    version=dependencies.get(tool),
                    confidence=confidence,
                    source=source,
                )
            )

        pyproject = read_toml(project_root / "pyproject.toml")

        pyproject_tools = pyproject.get("tool", {})

        for tool, key in self.PYPROJECT_TOOL_KEYS.items():

            if key in pyproject_tools:

                emit(tool, "pyproject.toml", 1.0)

        setup_cfg = read_setup_cfg(project_root / "setup.cfg")

        for tool, section in self.SETUP_CFG_SECTIONS.items():

            if setup_cfg.has_section(section):

                emit(tool, "setup.cfg", 1.0)

        for tool, filenames in self.ROOT_CONFIG_FILES.items():

            for filename in filenames:

                if (project_root / filename).exists():

                    emit(tool, filename, 1.0)

                    break

        for tool in self.TOOL_CATEGORIES:

            if tool in dependencies:

                emit(tool, "dependencies", 0.9)

        return signals
