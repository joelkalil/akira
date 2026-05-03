"""
Shared Rich output helpers for Akira commands.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path
from typing import Iterable

# Third-Party Libraries
from rich.console import Console
from rich.rule import Rule
from rich.text import Text


def print_phase(title: str, *, console: Console | None = None) -> None:
    """
    Print a titled phase header.
    """

    output = console or Console()

    output.print(f"\n  {title}...\n")


def print_check(label: object, *, console: Console | None = None) -> None:
    """
    Print one successful checklist line.
    """

    output = console or Console()

    output.print(success_line(label, console=output))


def print_done(*, console: Console | None = None) -> None:
    """
    Print the standard Akira completion block.
    """

    output = console or Console()

    output.print()

    output.print(Rule(style="red"))

    output.print("\n  [bold]Done. Your agent knows your stack.[/bold]\n")

    output.print("  To update skills after stack changes:")

    output.print("    akira detect --path .")

    output.print("\n  To recapture coding style:")

    output.print("    akira fingerprint --path .")


def success_line(message: object, *, console: Console | None = None) -> Text:
    """
    Return a styled success line.
    """

    output = console or Console()

    text = Text("  ")

    text.append(success_symbol(output), style="green")

    text.append(f"  {message}")

    return text


def success_symbol(console: Console) -> str:
    """
    Return a success symbol compatible with the console encoding.
    """

    symbol = "✓"

    try:

        symbol.encode(console.encoding or "utf-8")

    except UnicodeEncodeError:

        return "+"

    return symbol


def relative_to(path: Path, root: Path) -> Path:
    """
    Return a relative path when possible, otherwise the original path.
    """

    try:

        return path.relative_to(root)

    except ValueError:

        return path


def join_labels(labels: Iterable[str]) -> str:
    """
    Join labels with the v2 CLI separator.
    """

    return " · ".join(labels)

