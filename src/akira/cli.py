"""Command line entry point for Akira."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from akira.config import DEFAULT_AGENT, DEFAULT_OUTPUT_DIR, SUPPORTED_AGENTS
from akira.detect import scan_project, write_stack_markdown
from akira.skills import generate_skills, install_claude_skills

app = typer.Typer(
    help="Akira detects project context and generates agent skills.",
    no_args_is_help=True,
)


def _validate_agent(agent: str) -> str:
    if agent not in SUPPORTED_AGENTS:
        supported = ", ".join(SUPPORTED_AGENTS)
        raise typer.BadParameter(
            f"Unsupported agent '{agent}'. Choose one of: {supported}."
        )

    return agent


@app.callback()
def cli() -> None:
    """Akira detects project context and generates agent skills."""


@app.command()
def detect(
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Project directory to scan.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ] = Path("."),
    agent: Annotated[
        str,
        typer.Option(
            "--agent",
            "-a",
            help="Agent target for generated skills.",
            callback=_validate_agent,
        ),
    ] = DEFAULT_AGENT,
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Directory where Akira will write generated files.",
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = DEFAULT_OUTPUT_DIR,
) -> None:
    """Detect a project's stack and prepare agent skill output."""
    stack = scan_project(path)
    stack_path = write_stack_markdown(output, stack)
    skill_paths = generate_skills(stack, output)
    installed_paths = ()
    if agent == "claude-code":
        installed_paths = install_claude_skills(path, output)

    typer.echo(f"Project path: {path}")
    typer.echo(f"Agent: {agent}")
    typer.echo(f"Output: {output}")
    typer.echo(f"Wrote: {stack_path}")
    for skill in skill_paths:
        typer.echo(f"Wrote: {skill.path}")
    for installed in installed_paths:
        if installed.status in {"installed", "updated"}:
            typer.echo(f"{installed.status.title()}: {installed.path}")


def main() -> None:
    """Run the Akira CLI."""
    app()
