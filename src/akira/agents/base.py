"""
Agent adapter interface for installing Akira context.
"""

# Standard Libraries
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

# Local Libraries
from akira.skills.installer import InstalledSkillFile, install_generated_skills


@dataclass(frozen=True)

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class AgentInstallResult:
    """
    Result returned by an agent adapter installation.

    Attributes
    ----------
    agent : str
        The name of the agent for which context was installed.
    installed_files : tuple[InstalledSkillFile, ...]
        A tuple of InstalledSkillFile objects representing the files installed for the agent.
    """

    agent: str

    installed_files: tuple[InstalledSkillFile, ...]


class BaseAgentAdapter(ABC):
    """
    Install generated Akira artifacts for a specific coding agent.

    Methods
    -------
    name : str
        The name of the agent adapter, used to match against agent configuration.
    target_relative_dir : Path
        The project-relative directory where the agent's context should be installed.
    target_directory(project_root: Path) -> Path
        Resolve the absolute target directory for the agent's context based on the project root.
    install(project_root: Path, artifact_dir: Path) -> AgentInstallResult
        Install the generated artifacts from artifact_dir into the agent-specific location within
        the project, returning an AgentInstallResult.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the supported agent name.
        """

    @property
    @abstractmethod
    def target_relative_dir(self) -> Path:
        """
        Return the project-relative install directory for this agent.
        """

    def target_directory(self, project_root: Path) -> Path:
        """
        Return the resolved project-local directory for this agent.

        Parameters
        ----------
        project_root : Path
            The root directory of the project, used to resolve the target directory.

        Returns
        -------
        Path
            The absolute path to the target directory where the agent's context should be installed.
        """

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
        """
        Install artifact_dir content into the agent-specific location.

        Parameters
        ----------
        project_root : Path
            The root directory of the project, used to resolve the target directory.
        artifact_dir : Path
            The directory containing generated artifacts to be installed for the agent.

        Returns
        -------
        AgentInstallResult
            An object containing the results of the installation, including the agent name
            and installed files.
        """

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
