"""Shared stack category helpers."""

from __future__ import annotations

TOOLING_CATEGORIES = frozenset({"linting", "formatting", "type_checking", "pre_commit"})


def normalize_skill_category(category: str) -> str:
    """Normalize detector categories to skill template categories."""
    return "tooling" if category in TOOLING_CATEGORIES else category
