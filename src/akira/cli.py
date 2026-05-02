"""Command line entry point for Akira."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(
    help="Akira detects project context and generates agent skills.",
    no_args_is_help=True,
)


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
        ),
    ] = "claude-code",
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Directory where Akira will write generated files.",
        ),
    ] = Path(".akira"),
) -> None:
    """Detect a project's stack and prepare agent skill output."""
    typer.echo(f"Project path: {path}")
    typer.echo(f"Agent: {agent}")
    typer.echo(f"Output: {output}")


def main() -> None:
    """Run the Akira CLI."""
    app()
