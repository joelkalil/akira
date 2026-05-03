"""
Migration references for Akira stack review findings.
"""

# Standard Libraries
from __future__ import annotations

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

MIGRATION_REFERENCES = {
    "testing/unittest-to-pytest": (
        "Replace unittest.TestCase classes with pytest-style tests.",
        "Prefer assert statements and fixtures over setUp/tearDown.",
    ),
}

__all__ = [
    "MIGRATION_REFERENCES",
]
