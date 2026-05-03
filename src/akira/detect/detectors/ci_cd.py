"""
Detect CI/CD configuration files.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Local Libraries
from akira.detect.detectors.base import BaseDetector
from akira.detect.models import Signal

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class CiCdDetector(BaseDetector):
    """
    Detect common CI/CD providers from project configuration.

    Attributes
    ----------
    order : int
        The order in which this detector should be run relative to other
        detectors. Detectors with
        lower order values will be run before those with higher values. The
        default order is 70.

    Methods
    -------
    name
        A stable name for this detector, used for ordering and diagnostics.
    detect(project_root: Path) -> list[Signal]
        Scan a project and return detected signals.
    """

    order = 70

    def detect(self, project_root: Path) -> list[Signal]:
        """
        Scan repository CI/CD configuration files.

        Parameters
        ----------
        project_root : Path
            The root directory of the project to scan.

        Returns
        -------
        list[Signal]
            A list of detected signals.
        """

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
