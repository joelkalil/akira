"""Agent adapter interface for installing Akira context."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from akira.skills.installer import InstalledSkillFile, install_generated_skills


@dataclass(frozen=True)
class AgentInstallResult:
    """Result returned by an agent adapter installation."""

    agent: str
    installed_files: tuple[InstalledSkillFile, ...]


class BaseAgentAdapter(ABC):
    """Install generated Akira artifacts for a specific coding agent."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the supported agent name."""

    @property
    @abstractmethod
    def target_relative_dir(self) -> Path:
        """Return the project-relative install directory for this agent."""

    def target_directory(self, project_root: Path) -> Path:
        """Return the resolved project-local directory for this agent."""
        resolved_project = project_root.resolve()
        target = (resolved_project / self.target_relative_dir).resolve()
        try:
            target.relative_to(resolved_project)
        except ValueError as exc:
            raise ValueError(
                f"Agent target for '{self.name}' must stay within the project."
            ) from exc

        return target

    def install(
        self,
        project_root: Path,
        artifact_dir: Path,
    ) -> AgentInstallResult:
        """Install artifact_dir content into the agent-specific location."""
        target = self.target_directory(project_root)
        installed_files = install_generated_skills(
            project_root,
            artifact_dir,
            target.relative_to(project_root.resolve()),
        )
        return AgentInstallResult(
            agent=self.name,
            installed_files=installed_files,
        )
