"""
Shared helpers for the consistent style fixture.
"""

from __future__ import annotations

from collections.abc import Iterable

DEFAULT_LABEL = "anonymous"


def _normalize_name(name: str | None) -> str:

    if name is None:
        return DEFAULT_LABEL

    return name.strip().lower()


def build_tags(*, tags: Iterable[str] | None = None) -> list[str]:
    """
    Return build tags result.
    """

    if tags is None:
        return []

    return [tag.strip().lower() for tag in tags if tag.strip()]
