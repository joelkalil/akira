"""
Shared pytest configuration for Akira tests.
"""

# Standard Libraries
from __future__ import annotations
from pathlib import Path

# Third-Party Libraries
import pytest

# Local Libraries


@pytest.fixture

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def fixtures_dir() -> Path:
    """
    Return the root directory for project fixtures.
    """

    return Path(__file__).parent / "fixtures"
