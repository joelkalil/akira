"""Agent adapter interface for installing Akira context."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from akira.skills.installer import InstalledSkillFile


@dataclass(frozen=True)
class AgentInstallResult:
    """Result returned by an agent adapter installation."""

    agent: str
    installed_files: tuple[InstalledSkillFile, ...]


class BaseAgentAdapter(ABC):
    """Install generated Akira artifacts for a specific coding agent."""

    name: str

    @abstractmethod
    def install(
        self,
        project_root: Path,
        artifact_dir: Path,
    ) -> AgentInstallResult:
        """Install artifact_dir content into the agent-specific location."""
        ...
