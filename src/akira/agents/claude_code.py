"""
Claude Code adapter for Akira context installation.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Local Libraries
from akira.agents.base import BaseAgentAdapter

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ClaudeCodeAdapter(BaseAgentAdapter):
    """
    Install Akira context into Claude Code's project skill directory.

    Attributes
    ----------
    name : str
        The name of the agent adapter, used to match against agent configuration.
    target_relative_dir : Path
        The project-relative directory where the agent's context should be installed.
    """

    name = "claude-code"

    target_relative_dir = Path(".claude") / "skills" / "akira"
