"""Base contracts for stack detectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from akira.detect.models import Signal


class BaseDetector(ABC):
    """Base class for stack detectors."""

    order = 100

    @property
    def name(self) -> str:
        """Return a stable detector name for ordering and diagnostics."""
        return self.__class__.__name__

    @abstractmethod
    def detect(self, project_root: Path) -> list[Signal]:
        """Scan a project and return detected signals."""

    def _read_toml(self, path: Path) -> dict[str, Any]:
        """Read a TOML file, returning an empty mapping when it is absent."""
        if not path.exists():
            return {}

        import tomllib

        with path.open("rb") as file:
            return tomllib.load(file)
