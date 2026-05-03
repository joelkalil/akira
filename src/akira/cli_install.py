"""
Implementation of the v2 Akira install command.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Third-Party Libraries
import typer
from rich.console import Console
from rich.prompt import Prompt

# Local Libraries
from akira.agents import SUPPORTED_AGENT_NAMES, AgentInstallResult, get_agent_adapter
from akira.agents.detector import detect_configured_agents
from akira.claude_md import write_akira_section
from akira.config import DEFAULT_AGENT
from akira.detect import scan_project, write_stack_markdown
from akira.detect.models import StackInfo
from akira.detect.renderer import SECTION_CATEGORIES, tool_value
from akira.fingerprint import fingerprint_project, write_fingerprint_markdown
from akira.fingerprint.models import FingerprintAnalysis
from akira.skills import GeneratedSkill, generate_skills
from akira.ui.banner import print_banner
from akira.ui.output import (
    join_labels,
    print_check,
    print_done,
    print_phase,
    relative_to,
)

AGENT_LABELS = {
    "claude-code": "Claude Code",
    "cursor": "Cursor",
    "copilot": "Copilot",
    "codex": "Codex",
}


def install_command(
    *,
    path: Path,
    agent: str | None,
    output: Path,
    sample_size: int,
    exclude: tuple[str, ...],
    no_claude_md: bool,
    console: Console | None = None,
) -> None:
    """
    Run the full v2 install flow.

    Parameters
    ----------
    path : Path
        The path value.
    agent : str | None
        The agent value.
    output : Path
        The output value.
    sample_size : int
        The sample size value.
    exclude : tuple[str, ...]
        The exclude value.
    no_claude_md : bool
        The no claude md value.
    console : Console | None
        The console value.
    """

    output_console = console or Console()

    print_banner(output_console)

    agents = _select_install_agents(path, explicit_agent=agent, console=output_console)

    print_phase(f"Scanning {path.resolve()}", console=output_console)

    stack = scan_project(path)

    write_stack_markdown(output, stack)

    for line in stack_summary_lines(stack):
        print_check(line, console=output_console)

    print_phase("Capturing coding style", console=output_console)

    fingerprint = fingerprint_project(
        path,
        sample_size=sample_size,
        exclude=exclude,
    )

    write_fingerprint_markdown(output, fingerprint, sample_size=sample_size)

    style_summary = (
        f"{len(fingerprint.files)} files sampled · "
        f"confidence {fingerprint.confidence:.2f}"
    )

    print_check(style_summary, console=output_console)

    print_check(
        "Spacing, naming, imports, docstrings - all captured",
        console=output_console,
    )

    print_phase("Generating skill tree", console=output_console)

    generated_skills = generate_skills(stack, output, fingerprint=fingerprint)

    for generated_skill in generated_skills:
        print_check(
            relative_to(generated_skill.path, output),
            console=output_console,
        )

    install_results = install_to_agents(path, output, agents)

    print_install_results(install_results, console=output_console)

    if not no_claude_md:
        write_akira_section(path, agents)

        print_check(
            "CLAUDE.md updated with /akira slash commands",
            console=output_console,
        )

    print_done(console=output_console)


def resolve_agents_for_command(
    agent: str | None,
    path: Path,
    *,
    console: Console | None = None,
) -> tuple[str, ...]:
    """
    Resolve an optional agent flag for secondary commands.

    Parameters
    ----------
    agent : str | None
        The agent value.
    path : Path
        The path value.
    console : Console | None
        The console value.

    Returns
    -------
    tuple[str, ...]
        The result of the operation.
    """

    output = console or Console()

    if agent is not None:
        return (agent,)

    detected = detect_configured_agents(path)

    if not detected:
        output.print(
            "[dim]No agent configuration detected. Defaulting to claude-code. "
            "Use --agent to override.[/dim]"
        )

        return (DEFAULT_AGENT,)

    output.print(f"[dim]Detected agents: {', '.join(detected)}[/dim]")

    return detected


def install_to_agents(
    project_root: Path,
    output_dir: Path,
    agents: tuple[str, ...],
) -> tuple[AgentInstallResult, ...]:
    """
    Install generated Akira artifacts for all selected agents.

    Parameters
    ----------
    project_root : Path
        The project root value.
    output_dir : Path
        The output dir value.
    agents : tuple[str, ...]
        The agents value.

    Returns
    -------
    tuple[AgentInstallResult, ...]
        The result of the operation.
    """

    return tuple(
        get_agent_adapter(selected_agent).install(project_root, output_dir)
        for selected_agent in agents
    )


def print_install_results(
    install_results: tuple[AgentInstallResult, ...],
    *,
    console: Console | None = None,
) -> None:
    """
    Print the v2 installation result block.

    Parameters
    ----------
    install_results : tuple[AgentInstallResult, ...]
        The install results value.
    console : Console | None
        The console value.
    """

    output = console or Console()

    print_phase(f"Installing to {len(install_results)} agents", console=output)

    for result in install_results:
        installed_count = len(
            [
                installed
                for installed in result.installed_files
                if installed.status in {"installed", "updated", "unchanged"}
            ]
        )

        output.print(
            f"  {AGENT_LABELS.get(result.agent, result.agent):<13} "
            f"[green]✓[/green]  {installed_count} skills installed"
        )


def stack_summary_lines(stack: StackInfo) -> tuple[str, ...]:
    """
    Build stack summary lines grouped by rendered detect sections.

    Parameters
    ----------
    stack : StackInfo
        The stack value.

    Returns
    -------
    tuple[str, ...]
        The result of the operation.
    """

    lines: list[str] = []

    for categories in SECTION_CATEGORIES.values():
        tools = [
            tool_value(tool)
            for category in categories
            for tool in stack.by_category(category)
        ]

        if tools:
            lines.append(join_labels(tools))

    return tuple(lines)


def print_detect_output(
    stack: StackInfo,
    generated_skills: tuple[GeneratedSkill, ...],
    install_results: tuple[AgentInstallResult, ...],
    output_dir: Path,
    *,
    console: Console | None = None,
) -> None:
    """
    Print the secondary detect command output.

    Parameters
    ----------
    stack : StackInfo
        The stack value.
    generated_skills : tuple[GeneratedSkill, ...]
        The generated skills value.
    install_results : tuple[AgentInstallResult, ...]
        The install results value.
    output_dir : Path
        The output dir value.
    console : Console | None
        The console value.
    """

    output = console or Console()

    print_phase(f"Scanning {stack.project_root}", console=output)

    for line in stack_summary_lines(stack):
        print_check(line, console=output)

    print_phase("Generating skill tree", console=output)

    for generated_skill in generated_skills:
        print_check(relative_to(generated_skill.path, output_dir), console=output)

    print_install_results(install_results, console=output)

    output.print("\n  [bold]Done. Your agent knows your stack.[/bold]")


def print_fingerprint_output(
    analysis: FingerprintAnalysis,
    *,
    sample_size: int,
    exclude: tuple[str, ...],
    install_results: tuple[AgentInstallResult, ...],
    console: Console | None = None,
) -> None:
    """
    Print the secondary fingerprint command output.

    Parameters
    ----------
    analysis : FingerprintAnalysis
        The analysis value.
    sample_size : int
        The sample size value.
    exclude : tuple[str, ...]
        The exclude value.
    install_results : tuple[AgentInstallResult, ...]
        The install results value.
    console : Console | None
        The console value.
    """

    output = console or Console()

    print_phase("Capturing coding style", console=output)

    print_check(f"Files analyzed: {len(analysis.files)}", console=output)

    print_check(f"Parsed: {len(analysis.parsed_files)}", console=output)

    print_check(f"Parse failures: {len(analysis.failed_files)}", console=output)

    print_check(f"Patterns extracted: {len(analysis.patterns)}", console=output)

    print_check(f"Confidence: {analysis.confidence:.2f}", console=output)

    print_check(
        f"{len(analysis.files)} files sampled · confidence {analysis.confidence:.2f}",
        console=output,
    )

    print_check(
        "Spacing, naming, imports, docstrings - all captured",
        console=output,
    )

    if sample_size:
        output.print(f"\n  Sample size: {sample_size}")

    for pattern in exclude:
        output.print(f"  Exclude: {pattern}")

    print_install_results(install_results, console=output)

    output.print("\n  [bold]Done.[/bold]")


def _select_install_agents(
    project_root: Path,
    *,
    explicit_agent: str | None,
    console: Console,
) -> tuple[str, ...]:
    """
    Select agents for the install command.

    Parameters
    ----------
    project_root : Path
        The project root value.
    explicit_agent : str | None
        The explicit agent value.
    console : Console
        The console value.

    Returns
    -------
    tuple[str, ...]
        The result of the operation.
    """

    if explicit_agent is not None:
        return (explicit_agent,)

    detected = detect_configured_agents(project_root)

    console.print("\nDetected agents in this project:")

    if len(detected) == 1:
        console.print(
            f"  {AGENT_LABELS.get(detected[0], detected[0])} "
            f"({get_agent_adapter(detected[0]).target_relative_dir.as_posix()}/)"
        )

        return detected

    if not detected:
        console.print("  No agent configuration detected. Defaulting to Claude Code.")

        return (DEFAULT_AGENT,)

    return _select_agents_interactively(detected, console=console)


def _select_agents_interactively(
    detected: tuple[str, ...],
    *,
    console: Console,
) -> tuple[str, ...]:
    """
    Select agents with a Rich numbered multi-select prompt.

    Parameters
    ----------
    detected : tuple[str, ...]
        The detected value.
    console : Console
        The console value.

    Returns
    -------
    tuple[str, ...]
        The result of the operation.
    """

    selected = set(detected)

    console.print("\n  Which agents do you want to install to?\n")

    for index, agent in enumerate(SUPPORTED_AGENT_NAMES, start=1):
        marker = "●" if agent in selected else "○"

        detected_label = " detected" if agent in detected else ""

        target = get_agent_adapter(agent).target_relative_dir.as_posix() + "/"

        console.print(
            f"  {index}. {marker} {AGENT_LABELS.get(agent, agent)}"
            f"{detected_label} ({target})"
        )

    console.print()

    answer = Prompt.ask(
        "  Enter numbers to install, comma-separated",
        default=",".join(
            str(index)
            for index, agent in enumerate(SUPPORTED_AGENT_NAMES, start=1)
            if agent in selected
        ),
        console=console,
    )

    choices = _parse_agent_selection(answer)

    if not choices:
        console.print("[yellow]No agents selected.[/yellow]")

        raise typer.Exit(1)

    return choices


def _parse_agent_selection(answer: str) -> tuple[str, ...]:
    """
    Parse comma-separated agent numbers from the install prompt.

    Parameters
    ----------
    answer : str
        The answer value.

    Returns
    -------
    tuple[str, ...]
        The result of the operation.
    """

    selected: list[str] = []

    for item in answer.replace(" ", "").split(","):
        if not item:
            continue

        if not item.isdigit():
            continue

        index = int(item) - 1

        if 0 <= index < len(SUPPORTED_AGENT_NAMES):
            selected.append(SUPPORTED_AGENT_NAMES[index])

    return tuple(dict.fromkeys(selected))
