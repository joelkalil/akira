"""Craft generated Akira artifacts into an agent-ready context."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from akira.agents import (
    AgentInstallResult,
    BaseAgentAdapter,
    UnsupportedAgent,
    get_agent_adapter as get_registered_agent_adapter,
)
from akira.config import DEFAULT_AGENT, DEFAULT_OUTPUT_DIR


@dataclass(frozen=True)
class CraftPrerequisite:
    """A generated Akira artifact required before crafting agent context."""

    path: Path
    message: str


@dataclass(frozen=True)
class CraftResult:
    """The result of crafting Akira context for an agent."""

    project_root: Path
    artifact_dir: Path
    install_result: AgentInstallResult


class CraftError(Exception):
    """Raised when Akira context cannot be crafted."""


class MissingCraftPrerequisites(CraftError):
    """Raised when generated Akira artifacts are missing."""

    def __init__(self, missing: tuple[CraftPrerequisite, ...]) -> None:
        self.missing = missing
        super().__init__("Missing generated Akira artifacts.")


class UnsupportedCraftAgent(CraftError):
    """Raised when the requested agent has no craft adapter."""

    def __init__(
        self,
        agent: str,
        supported: tuple[str, ...] = (),
    ) -> None:
        self.agent = agent
        self.supported = supported
        supported_text = ", ".join(supported)
        message = f"Unsupported agent '{agent}'."
        if supported_text:
            message = f"{message} Choose one of: {supported_text}."
        super().__init__(message)


def craft_context(
    project_root: Path,
    *,
    agent: str = DEFAULT_AGENT,
    artifact_dir: Path | None = None,
) -> CraftResult:
    """Install generated Akira artifacts into the requested agent target."""
    resolved_project = project_root.resolve()
    resolved_artifacts = (
        artifact_dir.resolve()
        if artifact_dir is not None
        else (resolved_project / DEFAULT_OUTPUT_DIR).resolve()
    )
    missing = validate_craft_prerequisites(resolved_artifacts)
    if missing:
        raise MissingCraftPrerequisites(missing)

    adapter = get_agent_adapter(agent)
    install_result = adapter.install(resolved_project, resolved_artifacts)
    return CraftResult(
        project_root=resolved_project,
        artifact_dir=resolved_artifacts,
        install_result=install_result,
    )


def validate_craft_prerequisites(
    artifact_dir: Path,
) -> tuple[CraftPrerequisite, ...]:
    """Return missing generated artifacts required by craft."""
    checks = (
        (
            CraftPrerequisite(
                artifact_dir / "stack.md",
                "Run `akira detect --path <project>` to generate stack.md.",
            ),
            "file",
        ),
        (
            CraftPrerequisite(
                artifact_dir / "fingerprint.md",
                "Run `akira fingerprint --path <project>` to generate fingerprint.md.",
            ),
            "file",
        ),
        (
            CraftPrerequisite(
                artifact_dir / "skills",
                "Run `akira detect --path <project>` to generate the skill tree.",
            ),
            "dir",
        ),
        (
            CraftPrerequisite(
                artifact_dir / "skills" / "SKILL.md",
                "Run `akira detect --path <project>` to generate the router skill.",
            ),
            "file",
        ),
    )
    missing: list[CraftPrerequisite] = []
    for item, expected_type in checks:
        if expected_type == "file" and not item.path.is_file():
            missing.append(item)
        if expected_type == "dir" and not item.path.is_dir():
            missing.append(item)

    return tuple(missing)


def get_agent_adapter(agent: str) -> BaseAgentAdapter:
    """Return the craft adapter for an agent."""
    try:
        return get_registered_agent_adapter(agent)
    except UnsupportedAgent as exc:
        raise UnsupportedCraftAgent(exc.agent, exc.supported) from exc
