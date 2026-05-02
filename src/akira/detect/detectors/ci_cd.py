"""Detect CI/CD configuration files."""

from __future__ import annotations

from pathlib import Path

from akira.detect.detectors.base import BaseDetector
from akira.detect.models import Signal


class CiCdDetector(BaseDetector):
    """Detect common CI/CD providers from project configuration."""

    order = 70

    def detect(self, project_root: Path) -> list[Signal]:
        """Scan repository CI/CD configuration files."""
        signals: list[Signal] = []
        workflows_dir = project_root / ".github" / "workflows"
        workflow_files = sorted(
            path.name
            for pattern in ("*.yml", "*.yaml")
            for path in workflows_dir.glob(pattern)
        )
        if workflow_files:
            signals.append(
                Signal(
                    tool="github-actions",
                    category="ci_cd",
                    confidence=1.0,
                    source=".github/workflows",
                    metadata={"workflow_files": tuple(workflow_files)},
                )
            )

        if (project_root / ".gitlab-ci.yml").exists():
            signals.append(
                Signal(
                    tool="gitlab-ci",
                    category="ci_cd",
                    confidence=1.0,
                    source=".gitlab-ci.yml",
                )
            )

        return signals
