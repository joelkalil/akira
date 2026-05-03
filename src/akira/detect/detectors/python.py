"""
Detect Python runtime and package manager signals.
"""

# Standard Libraries
from __future__ import annotations
import re
from pathlib import Path

# Local Libraries
from akira.detect.detectors._python_project import read_toml
from akira.detect.detectors.base import BaseDetector
from akira.detect.models import Signal

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class PythonDetector(BaseDetector):
    """
    Detect Python version and Python package managers.

    Attributes
    ----------
    order : int
        The order in which this detector should be run relative to other detectors.

    Methods
    -------
    detect(project_root: Path) -> list[Signal]
        Scan the project directory for Python-related signals and return a list of detected signals.
    """

    order = 10

    def detect(self, project_root: Path) -> list[Signal]:
        """
        Scan Python metadata and lock files.

        Parameters
        ----------
        project_root : Path
            The root directory of the project to scan.

        Returns
        -------
        list[Signal]
            A list of detected signals related to Python runtime and package managers.
        """

        signals: list[Signal] = []

        pyproject = read_toml(project_root / "pyproject.toml")

        python_version = self._python_version(pyproject, project_root)

        if python_version:

            version, source = python_version

            signals.append(
                Signal(
                    tool="python",
                    category="runtime",
                    version=version,
                    confidence=1.0,
                    source=source,
                )
            )

        signals.extend(self._package_manager_signals(project_root, pyproject))

        return signals

    def _python_version(
        self,
        pyproject: dict,
        project_root: Path,
    ) -> tuple[str, str] | None:
        """
        Extract the Python version from pyproject.toml or other common files.

        Parameters
        ----------
        pyproject : dict
            The parsed contents of pyproject.toml.
        project_root : Path
            The root directory of the project to scan.

        Returns
        -------
        tuple[str, str] | None
            A tuple of (normalized_version, source) if a Python version is found, otherwise None.
        """

        project = pyproject.get("project", {})

        requires_python = project.get("requires-python")

        if isinstance(requires_python, str):

            return _normalize_python_version(requires_python), "pyproject.toml"

        poetry_python = (
            pyproject.get("tool", {})
            .get("poetry", {})
            .get("dependencies", {})
            .get("python")
        )

        if isinstance(poetry_python, str):

            return _normalize_python_version(poetry_python), "pyproject.toml"

        for filename in (".python-version", "runtime.txt"):

            path = project_root / filename

            if path.exists():

                raw = path.read_text(encoding="utf-8").strip()

                if raw:

                    return _normalize_python_version(raw), filename

        return None

    def _package_manager_signals(
        self,
        project_root: Path,
        pyproject: dict,
    ) -> list[Signal]:
        """
        Detect which Python package manager(s) are being used based on lock files and pyproject.toml.

        Parameters
        ----------
        project_root : Path
            The root directory of the project to scan.
        pyproject : dict
            The parsed contents of pyproject.toml.

        Returns
        -------
        list[Signal]
            A list of signals indicating which package managers are detected.
        """

        signals: list[Signal] = []

        tool_config = pyproject.get("tool", {})

        build_requires = pyproject.get("build-system", {}).get("requires", [])

        if (project_root / "uv.lock").exists():

            signals.append(_package_manager_signal("uv", "uv.lock", 1.0))

        elif "uv" in tool_config:

            signals.append(_package_manager_signal("uv", "pyproject.toml", 1.0))

        if (project_root / "poetry.lock").exists():

            signals.append(_package_manager_signal("poetry", "poetry.lock", 1.0))

        elif "poetry" in tool_config or any(
            str(item).startswith("poetry-core") for item in build_requires
        ):

            signals.append(_package_manager_signal("poetry", "pyproject.toml", 1.0))

        for conda_file in ("environment.yml", "environment.yaml", "conda-lock.yml"):

            if (project_root / conda_file).exists():

                signals.append(_package_manager_signal("conda", conda_file, 1.0))

                break

        if (
            any(project_root.glob("requirements*.txt"))
            or (project_root / "setup.py").exists()
        ):

            signals.append(
                _package_manager_signal("pip", "requirements/setup files", 0.9)
            )

        return signals


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _package_manager_signal(
    tool: str,
    source: str,
    confidence: float,
) -> Signal:
    """
    Helper function to create a Signal for a detected package manager.

    Parameters
    ----------
    tool : str
        The name of the package manager.
    source : str
        The source file where the package manager was detected.
    confidence : float
        The confidence level of the detection.

    Returns
    -------
    Signal
        A signal indicating the detected package manager.
    """

    return Signal(
        tool=tool,
        category="package_manager",
        confidence=confidence,
        source=source,
    )


def _normalize_python_version(specifier: str) -> str:
    """
    Normalize a Python version specifier to extract the version number.

    Parameters
    ----------
    specifier : str
        The raw version specifier string (e.g., ">=3.8", "^3.9", "3.10.5").

    Returns
    -------
    str
        The normalized version string (e.g., "3.8", "3.9", "3.10.5").
    """

    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", specifier)

    return match.group(1) if match else specifier.strip()
