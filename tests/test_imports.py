# Standard Libraries
from __future__ import annotations
from importlib.metadata import PackageNotFoundError, version

# Third-Party Libraries

# Local Libraries
import akira

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def test_package_exposes_version() -> None:
    try:
        expected_version = version("akira")
    except PackageNotFoundError:
        expected_version = "0+unknown"

    assert akira.__version__ == expected_version
