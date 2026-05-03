"""
GitHub Copilot adapter for Akira context installation.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Local Libraries
from akira.agents.base import BaseAgentAdapter

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class CopilotAdapter(BaseAgentAdapter):
    """
    Install Akira context into Copilot's project skill directory.

    Attributes
    ----------
    name : str
        The name of the adapter.
    target_relative_dir : Path
        The relative path to the target directory where the context should be installed.
    """

    name = "copilot"

    target_relative_dir = Path(".github") / "copilot-instructions"
