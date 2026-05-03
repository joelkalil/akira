"""
Agent adapter package.
"""

# Local Libraries
from akira.agents.base import AgentInstallResult, BaseAgentAdapter
from akira.agents.claude_code import ClaudeCodeAdapter
from akira.agents.codex import CodexAdapter
from akira.agents.copilot import CopilotAdapter
from akira.agents.cursor import CursorAdapter

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_ADAPTERS: tuple[type[BaseAgentAdapter], ...] = (
    ClaudeCodeAdapter,
    CursorAdapter,
    CopilotAdapter,
    CodexAdapter,
)

SUPPORTED_AGENT_NAMES = tuple(adapter.name for adapter in _ADAPTERS)

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


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class UnsupportedAgent(ValueError):
    """
    Raised when an agent name has no registered adapter.

    Attributes
    ----------
    agent : str
        The name of the unsupported agent.
    supported : tuple[str, ...]
        A tuple of supported agent names.
    """

    def __init__(self, agent: str, supported: tuple[str, ...]) -> None:
        """
        Initialize the exception.

        Parameters
        ----------
        agent : str
            The name of the unsupported agent.
        supported : tuple[str, ...]
            A tuple of supported agent names.
        """

        self.agent = agent

        self.supported = supported

        supported_text = ", ".join(supported)

        super().__init__(
            f"Unsupported agent '{agent}'. Choose one of: {supported_text}."
        )


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def get_agent_adapter(agent: str) -> BaseAgentAdapter:
    """
    Return the registered adapter for an agent name.

    Parameters
    ----------
    agent : str
        The name of the agent for which to retrieve an adapter.

    Returns
    -------
    BaseAgentAdapter
        An instance of the registered agent adapter.

    Raises
    ------
    UnsupportedAgent
        Raised when the requested agent is unsupported.
    """

    for adapter_type in _ADAPTERS:

        if adapter_type.name == agent:

            return adapter_type()

    raise UnsupportedAgent(agent, SUPPORTED_AGENT_NAMES)
