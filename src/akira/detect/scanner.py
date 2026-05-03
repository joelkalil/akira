"""
Project scanning orchestration for Akira detectors.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path
from typing import Iterable

# Local Libraries
from akira.detect.detectors import (
    CiCdDetector,
    DatabaseDetector,
    DocsDetector,
    FrameworkDetector,
    InfrastructureDetector,
    PythonDetector,
    TestingDetector,
    ToolingDetector,
)
from akira.detect.detectors.base import BaseDetector
from akira.detect.models import Signal, StackInfo

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

DEFAULT_DETECTORS = (
    PythonDetector,
    FrameworkDetector,
    ToolingDetector,
    TestingDetector,
    DatabaseDetector,
    InfrastructureDetector,
    CiCdDetector,
    DocsDetector,
)


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class Scanner:
    """
    Run detectors and aggregate their signals into a stack model.

    Attributes
    ----------
    detectors : tuple[BaseDetector, ...]
        Tuple of detector instances to use for scanning.

    Methods
    -------
    collect_signals(project_root: Path) -> list[Signal]
        Run detectors in deterministic order and deduplicate their signals.
    scan(project_root: Path) -> StackInfo
        Return normalized stack information for a project.
    """

    def __init__(
        self,
        *,
        detectors: Iterable[BaseDetector] | None = None,
    ) -> None:
        """
        Initialize the scanner with the provided detectors.

        Parameters
        ----------
        detectors
            Optional detector instances to use instead of the defaults.
        """

        detector_instances = (
            tuple(detector() for detector in DEFAULT_DETECTORS)
            if detectors is None
            else tuple(detectors)
        )

        self.detectors = tuple(
            sorted(
                detector_instances,
                key=lambda detector: (detector.order, detector.name),
            )
        )

    def collect_signals(self, project_root: Path) -> list[Signal]:
        """
        Run detectors in deterministic order and deduplicate their signals.

        Parameters
        ----------
        project_root
            Root directory of the project being scanned.

        Returns
        -------
        list[Signal]
            Unique detector signals ordered by detector execution.
        """

        root = project_root.resolve()

        signals: list[Signal] = []

        for detector in self.detectors:

            signals.extend(detector.detect(root))

        return self._deduplicate(signals)

    def scan(self, project_root: Path) -> StackInfo:
        """
        Return normalized stack information for a project.

        Parameters
        ----------
        project_root
            Root directory of the project being scanned.

        Returns
        -------
        StackInfo
            Normalized stack information for the project.
        """

        root = project_root.resolve()

        return StackInfo.from_signals(root, self.collect_signals(root))

    def _deduplicate(self, signals: list[Signal]) -> list[Signal]:
        """
        Deduplicate signals by their identity, keeping the one with the highest.

        confidence.

        Parameters
        ----------
        signals : list[Signal]
            List of signals to deduplicate.

        Returns
        -------
        list[Signal]
            Deduplicated list of signals.
        """

        seen: dict[tuple[str, str, str | None, str], Signal] = {}

        for signal in signals:

            existing = seen.get(signal.identity)

            if existing is None or signal.confidence > existing.confidence:

                seen[signal.identity] = signal

        return list(seen.values())


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def scan_project(
    project_root: Path,
    *,
    detectors: Iterable[BaseDetector] | None = None,
) -> StackInfo:
    """
    Scan a project using the default Akira detector set.

    Parameters
    ----------
    project_root
        Root directory of the project being scanned.
    detectors
        Optional detector instances to use instead of the defaults.

    Returns
    -------
    StackInfo
        Normalized stack information for the project.
    """

    return Scanner(detectors=detectors).scan(project_root)
