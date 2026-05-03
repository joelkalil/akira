"""
Codex adapter for Akira context installation.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Local Libraries
from akira.agents.base import BaseAgentAdapter

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class CodexAdapter(BaseAgentAdapter):
    """
    Install Akira context into Codex's project skill directory.

    Attributes
    ----------
    name : str
        The name of the adapter.
    target_relative_dir : Path
        The relative path to the target directory where the context should be installed.
    """

    name = "codex"

    target_relative_dir = Path(".codex") / "skills" / "akira"
