"""
CLAUDE.md integration for Akira slash command instructions.
"""

# Standard Libraries
from __future__ import annotations

import textwrap
from pathlib import Path

# Local Libraries
from akira.agents import get_agent_adapter

START_MARKER = "<!-- akira:start -->"
END_MARKER = "<!-- akira:end -->"


def read_claude_md(project_root: Path) -> str:
    """
    Read CLAUDE.md from project_root, returning an empty string if absent.

    Parameters
    ----------
    project_root : Path
        The project root value.

    Returns
    -------
    str
        The result of the operation.
    """

    path = project_root / "CLAUDE.md"

    if not path.exists():
        return ""

    return path.read_text(encoding="utf-8")


def write_akira_section(project_root: Path, agents: tuple[str, ...]) -> Path:
    """
    Upsert the Akira managed section in CLAUDE.md.

    Parameters
    ----------
    project_root : Path
        The project root value.
    agents : tuple[str, ...]
        The agents value.

    Returns
    -------
    Path
        The result of the operation.
    """

    path = project_root / "CLAUDE.md"

    existing = read_claude_md(project_root)

    section = _akira_section(agents)

    if START_MARKER in existing and END_MARKER in existing:
        before, rest = existing.split(START_MARKER, 1)

        _, after = rest.split(END_MARKER, 1)

        content = f"{before.rstrip()}\n\n{section}\n\n{after.lstrip()}".rstrip()

    elif existing.strip():
        content = f"{existing.rstrip()}\n\n{section}"

    else:
        content = section

    path.write_text(f"{content.rstrip()}\n", encoding="utf-8")

    return path


def _akira_section(agents: tuple[str, ...]) -> str:
    """
    Render the managed Akira CLAUDE.md section.

    Parameters
    ----------
    agents : tuple[str, ...]
        The agents value.

    Returns
    -------
    str
        The result of the operation.
    """

    skill_path = _claude_skill_path(agents)

    return textwrap.dedent(
        f"""\
        {START_MARKER}
        ## Akira - Stack Intelligence

        Akira skills are installed at `{skill_path}`. Read `SKILL.md`
        before any coding task in this project.

        ### Slash Commands

        When the user types `/akira detect`:
        1. Run `akira detect --path .` in the terminal
        2. Confirm: "Stack re-scanned. Skills updated."

        When the user types `/akira fingerprint`:
        1. Run `akira fingerprint --path .` in the terminal
        2. Confirm: "Coding style captured. Fingerprint updated."

        When the user types `/akira review`:
        1. Read `.akira/stack.md`
        2. Analyze the stack for incompatibilities, redundancies, and gaps
        3. Present findings with suggested fixes
        4. Ask the user which changes to apply
        {END_MARKER}
        """
    ).strip()


def _claude_skill_path(agents: tuple[str, ...]) -> str:
    """
    Return the Claude-facing Akira skill path for the managed section.

    Parameters
    ----------
    agents : tuple[str, ...]
        The agents value.

    Returns
    -------
    str
        The result of the operation.
    """

    if "claude-code" in agents:
        return get_agent_adapter("claude-code").target_relative_dir.as_posix() + "/"

    if agents:
        return get_agent_adapter(agents[0]).target_relative_dir.as_posix() + "/"

    return ".claude/skills/akira/"
