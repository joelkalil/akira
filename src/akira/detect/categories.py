"""
Shared stack category helpers.
"""

# Standard Libraries
from __future__ import annotations

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

TOOLING_CATEGORIES = frozenset({"linting", "formatting", "type_checking", "pre_commit"})


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def normalize_skill_category(category: str) -> str:
    """
    Normalize detector categories to skill template categories.

    Parameters
    ----------
    category : str
        The category value.

    Returns
    -------
    str
        Skill template category name.
    """

    return "tooling" if category in TOOLING_CATEGORIES else category
