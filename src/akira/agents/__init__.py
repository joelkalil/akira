"""Agent adapter package."""

from akira.agents.base import AgentInstallResult, BaseAgentAdapter
from akira.agents.claude_code import ClaudeCodeAdapter

__all__ = [
    "AgentInstallResult",
    "BaseAgentAdapter",
    "ClaudeCodeAdapter",
]
