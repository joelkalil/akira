"""
Detect configured coding agents in a project.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Local Libraries
from akira.agents import SUPPORTED_AGENT_NAMES


def detect_configured_agents(project_root: Path) -> tuple[str, ...]:
    """
    Return configured agents detected at the project root.

    Detection uses project-local configuration markers and returns agent names
    in the same stable order as ``SUPPORTED_AGENT_NAMES``.
    """

    indicators = {
        "claude-code": _has_claude_code_config,
        "cursor": _has_cursor_config,
        "copilot": _has_copilot_config,
        "codex": _has_codex_config,
    }

    return tuple(
        agent
        for agent in SUPPORTED_AGENT_NAMES
        if indicators.get(agent, _never_detect)(project_root)
    )


def _has_claude_code_config(project_root: Path) -> bool:
    return (project_root / ".claude").is_dir()


def _has_cursor_config(project_root: Path) -> bool:
    return (project_root / ".cursor").is_dir()


def _has_copilot_config(project_root: Path) -> bool:
    github_dir = project_root / ".github"

    if (github_dir / "copilot-instructions.md").is_file():

        return True

    if not github_dir.is_dir():

        return False

    return any(path.is_file() for path in github_dir.glob("copilot*.md"))


def _has_codex_config(project_root: Path) -> bool:
    return (project_root / ".codex").is_dir()


def _never_detect(_project_root: Path) -> bool:
    return False
