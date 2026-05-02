"""Shared pytest configuration for Akira tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the root directory for project fixtures."""
    return Path(__file__).parent / "fixtures"

