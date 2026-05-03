"""
Shared pytest configuration for Akira tests.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Third-Party Libraries
import pytest

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


@pytest.fixture
def fixtures_dir() -> Path:
    """
    Return the root directory for project fixtures.
    """

    return Path(__file__).parent / "fixtures"
