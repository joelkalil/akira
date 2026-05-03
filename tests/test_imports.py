"""
Tests for imports.
"""

# Standard Libraries
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

# Local Libraries
import akira

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


class TestPackageExposesVersion:
    """
    Verify package exposes version cases.
    """

    def test_package_exposes_version(self) -> None:
        """
        Verify package exposes version behavior.
        """

        try:

            expected_version = version("akira")

        except PackageNotFoundError:

            expected_version = "0+unknown"

        assert akira.__version__ == expected_version
