"""
Command line entry point for Akira.
"""

# Standard Libraries
from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

# Third-Party Libraries
import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text

# Local Libraries
from akira.agents import SUPPORTED_AGENT_NAMES, get_agent_adapter
from akira.cli_install import (
    install_command,
    install_to_agents,
    print_detect_output,
    print_fingerprint_output,
    resolve_agents_for_command,
)
from akira.config import DEFAULT_OUTPUT_DIR
from akira.detect import scan_project, write_stack_markdown
from akira.detect.models import StackInfo
from akira.detect.renderer import SECTION_CATEGORIES, tool_value
from akira.fingerprint import fingerprint_project, write_fingerprint_markdown
from akira.review import (
    Finding,
    ReviewCategory,
    analyze_stack,
    apply_review_findings,
    render_review,
)
from akira.skills import InstalledSkillFile, generate_skills

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

app = typer.Typer(
    help="Akira detects project context and generates agent skills.",
    no_args_is_help=True,
)

console = Console(width=160)


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


@app.callback()
def cli() -> None:
    """Akira detects project context and generates agent skills."""


@app.command()
def install(
    *,
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Project directory to install Akira into.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ] = Path("."),
    agent: Annotated[
        str | None,
        typer.Option(
            "--agent",
            "-a",
            help="Agent target for generated skills.",
            callback=_validate_agent,
        ),
    ] = None,
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
    sample_size: Annotated[
        int,
        typer.Option(
            "--sample-size",
            "-s",
            min=0,
            help="Maximum number of Python files to sample.",
        ),
    ] = 20,
    exclude: Annotated[
        list[str] | None,
        typer.Option(
            "--exclude",
            "-x",
            help=(
                "Project-relative path or glob to exclude from fingerprinting. "
                "May be passed multiple times."
            ),
        ),
    ] = None,
    no_claude_md: Annotated[
        bool,
        typer.Option(
            "--no-claude-md",
            help="Skip writing Akira slash command instructions to CLAUDE.md.",
        ),
    ] = False,
) -> None:
    """
    Detect stack, capture style, generate skills, and install them for agents.

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
    exclude : list[str] | None
        The exclude value.
    no_claude_md : bool
        The no claude md value.
    """

    install_command(
        path=path,
        agent=agent,
        output=output,
        sample_size=sample_size,
        exclude=tuple(exclude or ()),
        no_claude_md=no_claude_md,
        console=console,
    )


@app.command()
def detect(
    *,
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
        str | None,
        typer.Option(
            "--agent",
            "-a",
            help="Agent target for generated skills.",
            callback=_validate_agent,
        ),
    ] = None,
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
    """
    Detect a project's stack and prepare agent skill output.

    Parameters
    ----------
    path : Path
        The path value.
    agent : str | None
        The agent value.
    output : Path
        The output value.
    """

    agents = resolve_agents_for_command(agent, path, console=console)

    stack = scan_project(path)

    write_stack_markdown(output, stack)

    skill_paths = generate_skills(stack, output)

    install_results = install_to_agents(path, output, agents)

    print_detect_output(
        stack,
        skill_paths,
        install_results,
        output,
        console=console,
    )


@app.command()
def fingerprint(
    *,
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Project directory to analyze.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ] = Path("."),
    sample_size: Annotated[
        int,
        typer.Option(
            "--sample-size",
            "-s",
            min=0,
            help="Maximum number of Python files to sample.",
        ),
    ] = 20,
    exclude: Annotated[
        list[str] | None,
        typer.Option(
            "--exclude",
            "-x",
            help=(
                "Project-relative path or glob to exclude. May be passed "
                "multiple times."
            ),
        ),
    ] = None,
    agent: Annotated[
        str | None,
        typer.Option(
            "--agent",
            "-a",
            help="Agent target for updated fingerprint output.",
            callback=_validate_agent,
        ),
    ] = None,
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
    """
    Analyze source files and write fingerprint.md output.

    Parameters
    ----------
    path : Path
        The path value.
    sample_size : int
        The sample size value.
    exclude : list[str] | None
        The exclude value.
    agent : str | None
        The agent value.
    output : Path
        The output value.
    """

    agents = resolve_agents_for_command(agent, path, console=console)

    analysis = fingerprint_project(path, sample_size=sample_size, exclude=exclude or ())

    write_fingerprint_markdown(
        output,
        analysis,
        sample_size=sample_size,
    )

    install_results = install_to_agents(path, output, agents)

    print_fingerprint_output(
        analysis,
        sample_size=sample_size,
        exclude=tuple(exclude or ()),
        install_results=install_results,
        console=console,
    )


@app.command()
def review(
    *,
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Project directory to review.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ] = Path("."),
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Exit with a failure code when incompatibilities are found.",
        ),
    ] = False,
    auto_apply: Annotated[
        bool,
        typer.Option(
            "--auto-apply",
            help="Accept safe review changes without interactive prompts.",
        ),
    ] = False,
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Directory where Akira will write updated artifacts.",
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = DEFAULT_OUTPUT_DIR,
) -> None:
    """
    Review a detected stack for compatibility and best-practice findings.

    Parameters
    ----------
    path : Path
        The path value.
    strict : bool
        The strict value.
    auto_apply : bool
        The auto apply value.
    output : Path
        The output value.
    """

    stack = scan_project(path)

    result = analyze_stack(stack)

    render_review(result)

    if strict and result.has_incompatibilities:
        raise typer.Exit(1)

    console = Console()

    accepted, skipped = _collect_review_decisions(
        result.findings,
        auto_apply=auto_apply,
        console=console,
    )

    _, applied = apply_review_findings(stack, tuple(accepted), output)

    _render_review_summary(
        accepted=accepted,
        skipped=skipped,
        applied_count=len(applied),
        output=output,
        console=console,
    )


def main() -> None:
    """Run the Akira CLI."""

    app()


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _validate_agent(agent: str | None) -> str | None:
    """
    Validate an optional CLI agent name.

    Parameters
    ----------
    agent : str | None
        The agent value.

    Returns
    -------
    str | None
        The result of the operation.
    """

    if agent is None:
        return None

    if agent not in SUPPORTED_AGENT_NAMES:
        supported = ", ".join(SUPPORTED_AGENT_NAMES)

        raise typer.BadParameter(
            f"Unsupported agent '{agent}'. Choose one of: {supported}."
        )

    return agent


def _detect_section_lines(stack: StackInfo) -> tuple[str, ...]:
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
            lines.append(" · ".join(tools))

    return tuple(lines)


def _print_phase_header(title: str) -> None:
    """
    Print a titled CLI phase header.

    Parameters
    ----------
    title : str
        The title value.
    """

    console.print(f"\n{title}...\n")

    if console.is_terminal:
        console.print(Rule(style="cyan"))


def _success_line(message: object) -> Text:
    """
    Render a green success line for CLI output.

    Parameters
    ----------
    message : object
        The message value.

    Returns
    -------
    Text
        The result of the operation.
    """

    text = Text("  ")

    text.append(_success_symbol(), style="green")

    text.append(f" {message}")

    return text


def _success_symbol() -> str:
    """
    Return a success symbol compatible with the console encoding.

    Returns
    -------
    str
        The result of the operation.
    """

    symbol = "✓"

    try:
        symbol.encode(console.encoding or "utf-8")

    except UnicodeEncodeError:
        return "+"

    return symbol


def _relative_to(path: Path, root: Path) -> Path:
    """
    Return a relative path when possible, otherwise the original path.

    Parameters
    ----------
    path : Path
        The path value.
    root : Path
        The root value.

    Returns
    -------
    Path
        The result of the operation.
    """

    try:
        return path.relative_to(root)

    except ValueError:
        return path


def _agent_target(
    installed_files: tuple[InstalledSkillFile, ...],
    project_root: Path,
    agent: str | tuple[str, ...] | None,
) -> str:
    """
    Render the agent installation target for summary output.

    Parameters
    ----------
    installed_files : tuple[InstalledSkillFile, ...]
        The installed files value.
    project_root : Path
        The project root value.
    agent : str | tuple[str, ...] | None
        The agent value.

    Returns
    -------
    str
        The result of the operation.
    """

    if installed_files:
        common_target = Path(
            os.path.commonpath(
                [str(installed.path.parent) for installed in installed_files]
            )
        )

        return str(_relative_to(common_target, project_root))

    agents = (agent,) if isinstance(agent, str) else tuple(agent or ())

    if not agents:
        return "agent skills"

    return ", ".join(
        str(get_agent_adapter(resolved_agent).target_relative_dir)
        for resolved_agent in agents
    )


def _collect_review_decisions(
    findings: tuple[Finding, ...],
    *,
    auto_apply: bool,
    console: Console,
) -> tuple[list[Finding], list[Finding]]:
    """
    Collect accepted and skipped review findings.

    Parameters
    ----------
    findings : tuple[Finding, ...]
        The findings value.
    auto_apply : bool
        The auto apply value.
    console : Console
        The console value.

    Returns
    -------
    tuple[list[Finding], list[Finding]]
        The result of the operation.
    """

    actionable = [
        finding
        for finding in findings
        if finding.category is not ReviewCategory.CONSISTENCY
    ]

    if not actionable:
        return [], []

    accepted: list[Finding] = []

    skipped: list[Finding] = []

    for finding in actionable:
        if auto_apply:
            if finding.can_apply_safely:
                accepted.append(finding)

            else:
                skipped.append(finding)

            continue

        decision = _prompt_review_decision(finding, console)

        if decision == "y" and finding.can_apply_safely:
            accepted.append(finding)

        else:
            skipped.append(finding)

    return accepted, skipped


def _prompt_review_decision(finding: Finding, console: Console) -> str:
    """
    Prompt for a decision about applying one review finding.

    Parameters
    ----------
    finding : Finding
        The finding value.
    console : Console
        The console value.

    Returns
    -------
    str
        The result of the operation.
    """

    console.print()

    console.print(f"[bold]{finding.category.value}[/bold] {finding.rule_id}")

    console.print(finding.message)

    if finding.migration:
        console.print(f"[cyan]Migration reference:[/cyan] {finding.migration}")

    while True:
        try:
            decision = Prompt.ask(
                "Apply?",
                choices=("y", "n", "details"),
                default="n",
                show_default=False,
                console=console,
            )

        except (EOFError, KeyboardInterrupt):
            return "n"

        if decision == "details":
            _render_finding_details(finding, console)

            continue

        if decision == "y" and not finding.can_apply_safely:
            console.print(
                "[yellow]This finding has no safe metadata-only change, so it "
                "was skipped.[/yellow]"
            )

            return "n"

        return decision


def _render_finding_details(finding: Finding, console: Console) -> None:
    """
    Render detailed review finding guidance for interactive users.

    Parameters
    ----------
    finding : Finding
        The finding value.
    console : Console
        The console value.
    """

    console.print(f"[bold]Rule:[/bold] {finding.rule_id}")

    console.print(f"[bold]Category:[/bold] {finding.category.value}")

    console.print(f"[bold]Message:[/bold] {finding.message}")

    if finding.migration:
        console.print(f"[bold]Migration guidance:[/bold] {finding.migration}")

        guidance = _migration_guidance(finding.migration)

        if guidance:
            for item in guidance:
                console.print(f"- {item}")

    change = finding.safe_change

    if change is None:
        console.print("Akira will not change artifacts for this finding automatically.")

        return

    console.print(f"[bold]Safe change:[/bold] {change.summary}")

    for detail in change.details:
        console.print(f"- {detail}")


def _migration_guidance(reference: str) -> tuple[str, ...]:
    """
    Return short migration guidance for a review reference.

    Parameters
    ----------
    reference : str
        The reference value.

    Returns
    -------
    tuple[str, ...]
        The result of the operation.
    """

    if reference == "testing/unittest-to-pytest":
        return (
            "Replace unittest.TestCase classes with plain pytest test functions "
            "where practical.",
            "Prefer assert statements and fixtures over self.assert* and "
            "setUp/tearDown.",
            "Keep dependency file edits manual and reviewable.",
        )

    return ("Open the referenced migration guide before changing project code.",)


def _render_review_summary(
    *,
    accepted: list[Finding],
    skipped: list[Finding],
    applied_count: int,
    output: Path,
    console: Console,
) -> None:
    """
    Print the review command decision summary.

    Parameters
    ----------
    accepted : list[Finding]
        The accepted value.
    skipped : list[Finding]
        The skipped value.
    applied_count : int
        The applied count value.
    output : Path
        The output value.
    console : Console
        The console value.
    """

    if not accepted and not skipped:
        return

    console.print()

    console.print("[bold]Review Summary[/bold]")

    console.print(f"Accepted changes: {len(accepted)}")

    for finding in accepted:
        console.print(f"- {finding.rule_id}")

    console.print(f"Skipped changes: {len(skipped)}")

    for finding in skipped:
        console.print(f"- {finding.rule_id}")

    if applied_count:
        console.print(f"Updated artifacts in: {output}")

        console.print("Regenerated affected skills.")
