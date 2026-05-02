"""Project scanning orchestration for Akira detectors."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from akira.detect.detectors import FrameworkDetector, PythonDetector, ToolingDetector
from akira.detect.detectors.base import BaseDetector
from akira.detect.models import Signal, StackInfo

DEFAULT_DETECTORS = (PythonDetector, FrameworkDetector, ToolingDetector)


class Scanner:
    """Run detectors and aggregate their signals into a stack model."""

    def __init__(self, detectors: Iterable[BaseDetector] | None = None) -> None:
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
        """Run detectors in deterministic order and deduplicate their signals."""
        root = project_root.resolve()
        signals: list[Signal] = []

        for detector in self.detectors:
            signals.extend(detector.detect(root))

        return self._deduplicate(signals)

    def scan(self, project_root: Path) -> StackInfo:
        """Return normalized stack information for a project."""
        root = project_root.resolve()
        return StackInfo.from_signals(root, self.collect_signals(root))

    def _deduplicate(self, signals: list[Signal]) -> list[Signal]:
        seen: dict[tuple[str, str, str | None, str], Signal] = {}

        for signal in signals:
            existing = seen.get(signal.identity)
            if existing is None or signal.confidence > existing.confidence:
                seen[signal.identity] = signal

        return list(seen.values())


def scan_project(
    project_root: Path,
    detectors: Iterable[BaseDetector] | None = None,
) -> StackInfo:
    """Convenience wrapper for scanning a project."""
    return Scanner(detectors).scan(project_root)
