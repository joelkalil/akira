"""Codex adapter for Akira context installation."""

from __future__ import annotations

from pathlib import Path

from akira.agents.base import BaseAgentAdapter


class CodexAdapter(BaseAgentAdapter):
    """Install Akira context into Codex's project skill directory."""

    name = "codex"
    target_relative_dir = Path(".codex") / "skills" / "akira"
