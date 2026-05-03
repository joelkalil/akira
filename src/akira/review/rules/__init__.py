"""
Stack review rule definitions.
"""

# Local Libraries
from akira.review.rules.compatibility import COMPATIBILITY_RULES
from akira.review.rules.migrations import MIGRATION_REFERENCES
from akira.review.rules.suggestions import SUGGESTION_RULES

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

__all__ = [
    "COMPATIBILITY_RULES",
    "MIGRATION_REFERENCES",
    "SUGGESTION_RULES",
]
