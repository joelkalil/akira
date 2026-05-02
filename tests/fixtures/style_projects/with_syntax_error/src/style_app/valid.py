"""Valid file next to a syntax-error fixture."""

from __future__ import annotations


def load_value(value: str | None) -> str:
    if value is None:
        return "fallback"

    return value
