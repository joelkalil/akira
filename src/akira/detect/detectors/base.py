"""
Base contracts for stack detectors.
"""

# Standard Libraries
import tomllib
from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

# Local Libraries
from akira.detect.models import Signal

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class BaseDetector(ABC):
    """
    Base class for stack detectors.

    Attributes
    ----------
    order : int
        The order in which this detector should be run relative to other detectors. Detectors with
        lower order values will be run before those with higher values. The default order is 100.

    Methods
    -------
    name
        A stable name for this detector, used for ordering and diagnostics.
    detect(project_root: Path) -> list[Signal]
        Scan a project and return detected signals.
    """

    order = 100

    @property
    def name(self) -> str:
        """
        Return a stable detector name for ordering and diagnostics.
        """

        return self.__class__.__name__

    @abstractmethod
    def detect(self, project_root: Path) -> list[Signal]:
        """
        Scan a project and return detected signals

        Parameters
        ----------
        project_root : Path
            The root directory of the project to scan.

        Returns
        -------
        list[Signal]
            A list of detected signals.
        """

    def _read_toml(self, path: Path) -> dict[str, Any]:
        """
        Read a TOML file, returning an empty mapping when it is absent.

        Parameters
        ----------
        path : Path
            The path to the TOML file to read.

        Returns
        -------
        dict[str, Any]
            The contents of the TOML file as a dictionary, or an empty dictionary if the file
            does not exist.
        """

        if not path.exists():

            return {}

        with path.open("rb") as file:

            return tomllib.load(file)
