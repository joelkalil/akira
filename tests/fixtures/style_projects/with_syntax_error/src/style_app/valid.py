"""
Valid file next to a syntax-error fixture.
"""

# Standard Libraries
from __future__ import annotations


def load_value(value: str | None) -> str:
    """
    Return load value result.
    """

    if value is None:
        return "fallback"

    return value
