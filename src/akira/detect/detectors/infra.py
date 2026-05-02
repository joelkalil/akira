"""Detect infrastructure and CI/CD signals."""

from __future__ import annotations

from pathlib import Path

from akira.detect.detectors.base import BaseDetector
from akira.detect.models import Signal


class InfrastructureDetector(BaseDetector):
    """Detect container and CI/CD configuration."""

    order = 60

    def detect(self, project_root: Path) -> list[Signal]:
        """Scan root-level infrastructure files."""
        signals: list[Signal] = []

        if (project_root / "Dockerfile").exists():
            signals.append(
                Signal(
                    tool="docker",
                    category="infrastructure",
                    confidence=1.0,
                    source="Dockerfile",
                )
            )

        for filename in ("docker-compose.yml", "docker-compose.yaml", "compose.yml"):
            if (project_root / filename).exists():
                signals.append(
                    Signal(
                        tool="docker-compose",
                        category="infrastructure",
                        confidence=1.0,
                        source=filename,
                    )
                )
                break

        if any((project_root / ".github" / "workflows").glob("*.yml")) or any(
            (project_root / ".github" / "workflows").glob("*.yaml")
        ):
            signals.append(
                Signal(
                    tool="github-actions",
                    category="ci_cd",
                    confidence=1.0,
                    source=".github/workflows",
                )
            )

        return signals
