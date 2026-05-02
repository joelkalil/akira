"""Claude Code adapter for Akira context installation."""

from __future__ import annotations

from pathlib import Path

from akira.agents.base import AgentInstallResult, BaseAgentAdapter
from akira.skills.installer import install_claude_skills


class ClaudeCodeAdapter(BaseAgentAdapter):
    """Install Akira context into Claude Code's project skill directory."""

    name = "claude-code"

    def install(
        self,
        project_root: Path,
        artifact_dir: Path,
    ) -> AgentInstallResult:
        """Install generated Akira artifacts for Claude Code."""
        return AgentInstallResult(
            agent=self.name,
            installed_files=install_claude_skills(project_root, artifact_dir),
        )
