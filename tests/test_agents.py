"""
Tests for agents.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Third-Party Libraries
import pytest

# Local Libraries
from akira.agents import SUPPORTED_AGENT_NAMES, UnsupportedAgent, get_agent_adapter
from akira.agents.base import BaseAgentAdapter

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

EXPECTED_TARGETS = {
    "claude-code": Path(".claude") / "skills" / "akira",
    "cursor": Path(".cursor") / "skills" / "akira",
    "copilot": Path(".agents") / "skills" / "akira",
    "codex": Path(".codex") / "skills" / "akira",
}


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


class TestSupportedAgentsMatchDocumentedTargets:
    """
    Verify supported agents match documented targets cases.
    """

    def test_supported_agents_match_documented_targets(self, tmp_path: Path) -> None:
        """
        Verify supported agents match documented targets behavior.
        """

        project = tmp_path / "project"

        project.mkdir()

        assert SUPPORTED_AGENT_NAMES == ("claude-code", "cursor", "copilot", "codex")

        for agent, relative_target in EXPECTED_TARGETS.items():
            adapter = get_agent_adapter(agent)

            assert adapter.target_relative_dir == relative_target

            assert (
                adapter.target_directory(project)
                == (project / relative_target).resolve()
            )


class TestInvalidAgentListsSupportedNames:
    """
    Verify invalid agent lists supported names cases.
    """

    def test_invalid_agent_lists_supported_names(self) -> None:
        """
        Verify invalid agent lists supported names behavior.
        """

        with pytest.raises(UnsupportedAgent) as exc_info:
            get_agent_adapter("unknown-agent")

        message = str(exc_info.value)

        assert "Unsupported agent 'unknown-agent'" in message

        for agent in EXPECTED_TARGETS:
            assert agent in message


class TestBaseAgentAdapterIsNotInstantiable:
    """
    Verify base agent adapter is not instantiable cases.
    """

    def test_base_agent_adapter_is_not_instantiable(self) -> None:
        """
        Verify base agent adapter is not instantiable behavior.
        """

        with pytest.raises(TypeError):
            BaseAgentAdapter()


class TestAdapterInstallsIntoProjectLocalTarget:
    """
    Verify adapter installs into project local target cases.
    """

    @pytest.mark.parametrize("agent, relative_target", EXPECTED_TARGETS.items())
    def test_adapter_installs_into_project_local_target(
        self,
        tmp_path: Path,
        agent: str,
        relative_target: Path,
    ) -> None:
        """
        Verify adapter installs into project local target behavior.
        """

        project = tmp_path / "project"

        artifacts = tmp_path / ".akira"

        project.mkdir()

        (artifacts / "skills" / "python").mkdir(parents=True)

        (artifacts / "skills" / "SKILL.md").write_text(
            "Read ../stack.md and ../fingerprint.md",
            encoding="utf-8",
        )

        (artifacts / "skills" / "python" / "SKILL.md").write_text(
            "python",
            encoding="utf-8",
        )

        (artifacts / "stack.md").write_text("stack", encoding="utf-8")

        (artifacts / "fingerprint.md").write_text("fingerprint", encoding="utf-8")

        adapter = get_agent_adapter(agent)

        first = adapter.install(project, artifacts)

        second = adapter.install(project, artifacts)

        target = project / relative_target

        assert first.agent == agent

        assert {item.status for item in first.installed_files} == {"installed"}

        assert {item.status for item in second.installed_files} == {"unchanged"}

        assert (target / "SKILL.md").read_text(encoding="utf-8") == (
            "Read stack.md and fingerprint.md"
        )

        assert (target / "python" / "SKILL.md").read_text(encoding="utf-8") == "python"

        assert (target / "stack.md").read_text(encoding="utf-8") == "stack"

        assert (target / "fingerprint.md").read_text(encoding="utf-8") == "fingerprint"

        for installed in first.installed_files:
            installed.path.resolve().relative_to(project.resolve())
