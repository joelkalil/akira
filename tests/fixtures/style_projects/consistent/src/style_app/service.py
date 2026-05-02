"""User-facing service module for the consistent style fixture."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException

from style_app.helpers import _normalize_name, build_tags

LOGGER = logging.getLogger(__name__)

MAX_RETRIES = 3


# --- Models ---
@dataclass(frozen=True)
class UserRecord:
    """
    Stored user record.

    Args:
        name: Normalized user name.
        tags: Normalized user tags.
    """

    name: str
    tags: list[str]


class UserService:
    """Coordinate user record loading."""

    retries = MAX_RETRIES

    def __init__(self, source: str) -> None:
        self.source = source

    def load_user(self, name: str | None, tags: list[str] | None = None) -> UserRecord:
        """Load a normalized user record.

        Args:
            name: Raw user name.
            tags: Optional raw tags.

        Returns:
            Normalized user record.
        """
        if not self.source:
            raise HTTPException(status_code=500, detail="Missing source")

        normalized_name = _normalize_name(name)
        normalized_tags = build_tags(tags)

        return UserRecord(name=normalized_name, tags=normalized_tags)

    def _log_failure(self, path: str) -> None:
        LOGGER.exception("Could not load %s", path)


def render_user(record: UserRecord) -> str:
    """Render a user record."""
    if not record.tags:
        return f"{record.name}: none"

    return f"{record.name}: {', '.join(record.tags)}"


def load_user_file(path: Path) -> str:
    """Load a user fixture file."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        LOGGER.exception("Could not load %s", path)
        raise
