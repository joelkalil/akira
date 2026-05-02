"""GitHub Copilot adapter for Akira context installation."""

from __future__ import annotations

from pathlib import Path

from akira.agents.base import BaseAgentAdapter


class CopilotAdapter(BaseAgentAdapter):
    """Install Akira context into Copilot's project skill directory."""

    name = "copilot"
    target_relative_dir = Path(".agents") / "skills" / "akira"
