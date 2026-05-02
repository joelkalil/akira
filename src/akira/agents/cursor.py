"""
Cursor adapter for Akira context installation.
"""

# Standard Libraries
from __future__ import annotations
from pathlib import Path

# Third-Party Libraries

# Local Libraries
from akira.agents.base import BaseAgentAdapter

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class CursorAdapter(BaseAgentAdapter):
    """
    Install Akira context into Cursor's project skill directory.

    Attributes
    ----------
    name : str
        The name of the adapter.
    target_relative_dir : Path
        The relative path to the target directory where the context should be installed.
    """

    name = "cursor"

    target_relative_dir = Path(".cursor") / "skills" / "akira"
