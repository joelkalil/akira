"""Detect Python linting, formatting, type checking, and hook tooling."""

from __future__ import annotations

from pathlib import Path

from akira.detect.detectors._python_project import extract_dependencies, read_setup_cfg, read_toml
from akira.detect.detectors.base import BaseDetector
from akira.detect.models import Signal


class ToolingDetector(BaseDetector):
    """Detect common Python developer tooling."""

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
        """Scan metadata and configuration files for tool signals."""
        signals: list[Signal] = []
        detected: set[tuple[str, str]] = set()

        def emit(tool: str, source: str, confidence: float, version: str | None = None) -> None:
            key = (tool, source)
            if key in detected:
                return
            detected.add(key)
            signals.append(
                Signal(
                    tool=tool,
                    category=self.TOOL_CATEGORIES[tool],
                    version=version,
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

        dependencies = extract_dependencies(project_root)
        for tool in self.TOOL_CATEGORIES:
            if tool in dependencies:
                emit(tool, "dependencies", 0.9, version=dependencies[tool])

        return signals
