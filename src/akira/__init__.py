"""
Akira package.
"""

# Standard Libraries
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("akira")

except PackageNotFoundError:
    __version__ = "0+unknown"


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

__all__ = ["__version__"]
