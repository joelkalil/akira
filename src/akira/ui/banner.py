"""
Akira command banner rendering.
"""

# Standard Libraries
from __future__ import annotations

# Third-Party Libraries
from rich.console import Console
from rich.text import Text

AKIRA_ASCII = """\
    ___    __ __ ____ ____  ___
   /   |  / //_//  _// __ \\/   |
  / /| | / ,<   / / / /_/ / /| |
 / ___ |/ /| |_/ / / _, _/ ___ |
/_/  |_/_/ |_/___//_/ |_/_/  |_|"""

TAGLINE = "明 — bright, clear, intelligent\nOne command to teach your agent your stack."


def print_banner(console: Console | None = None) -> None:
    """
    Print the Akira ASCII banner and tagline.

    Parameters
    ----------
    console : Console | None
        The console value.
    """

    output = console or Console()

    output.print(Text(AKIRA_ASCII, style="bold red"))

    output.print(Text(TAGLINE, style="dim white"))
