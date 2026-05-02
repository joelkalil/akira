"""Agent adapter package."""

from akira.agents.base import AgentInstallResult, BaseAgentAdapter
from akira.agents.claude_code import ClaudeCodeAdapter
from akira.agents.codex import CodexAdapter
from akira.agents.copilot import CopilotAdapter
from akira.agents.cursor import CursorAdapter


class UnsupportedAgent(ValueError):
    """Raised when an agent name has no registered adapter."""

    def __init__(self, agent: str, supported: tuple[str, ...]) -> None:
        self.agent = agent
        self.supported = supported
        supported_text = ", ".join(supported)
        super().__init__(
            f"Unsupported agent '{agent}'. Choose one of: {supported_text}."
        )


_ADAPTERS: tuple[type[BaseAgentAdapter], ...] = (
    ClaudeCodeAdapter,
    CursorAdapter,
    CopilotAdapter,
    CodexAdapter,
)
SUPPORTED_AGENT_NAMES = tuple(adapter.name for adapter in _ADAPTERS)


def get_agent_adapter(agent: str) -> BaseAgentAdapter:
    """Return the registered adapter for an agent name."""
    for adapter_type in _ADAPTERS:
        if adapter_type.name == agent:
            return adapter_type()

    raise UnsupportedAgent(agent, SUPPORTED_AGENT_NAMES)

__all__ = [
    "AgentInstallResult",
    "BaseAgentAdapter",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "CopilotAdapter",
    "CursorAdapter",
    "SUPPORTED_AGENT_NAMES",
    "UnsupportedAgent",
    "get_agent_adapter",
]
