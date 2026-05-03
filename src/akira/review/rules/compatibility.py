"""
Compatibility rule exports for Akira stack review.
"""

# Local Libraries
from akira.review.analyzer import INITIAL_RULES, Rule

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

COMPATIBILITY_RULES: tuple[Rule, ...] = INITIAL_RULES

__all__ = [
    "COMPATIBILITY_RULES",
]
