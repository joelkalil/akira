"""
Suggestion rule exports for Akira stack review.
"""

# Local Libraries
from akira.review.analyzer import INITIAL_RULES, ReviewCategory, Rule

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

SUGGESTION_RULES: tuple[Rule, ...] = tuple(
    rule for rule in INITIAL_RULES if rule.category is ReviewCategory.SUGGESTION
)

__all__ = [
    "SUGGESTION_RULES",
]
