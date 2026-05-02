"""Cursor adapter for Akira context installation."""

from __future__ import annotations

from pathlib import Path

from akira.agents.base import BaseAgentAdapter


class CursorAdapter(BaseAgentAdapter):
    """Install Akira context into Cursor's project skill directory."""

    name = "cursor"
    target_relative_dir = Path(".cursor") / "skills" / "akira"
