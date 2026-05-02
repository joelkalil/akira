"""Command line entry point for Akira."""

from __future__ import annotations

import typer

app = typer.Typer(
    help="Detect project context and generate agent skills.",
    no_args_is_help=True,
)


def main() -> None:
    """Run the Akira CLI."""
    app()

