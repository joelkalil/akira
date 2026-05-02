"""Claude Code adapter for Akira context installation."""

from __future__ import annotations

from pathlib import Path

from akira.agents.base import BaseAgentAdapter


class ClaudeCodeAdapter(BaseAgentAdapter):
    """Install Akira context into Claude Code's project skill directory."""

    name = "claude-code"
    target_relative_dir = Path(".claude") / "skills" / "akira"
