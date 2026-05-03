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
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.text import Text

# Local Libraries
from akira.agents import (
    SUPPORTED_AGENT_NAMES,
    AgentInstallResult,
    UnsupportedAgent,
    get_agent_adapter,
)
from akira.agents.detector import detect_configured_agents
from akira.config import DEFAULT_AGENT, DEFAULT_OUTPUT_DIR
from akira.craft import (
    MissingCraftPrerequisites,
    UnsupportedCraftAgent,
    craft_context,
)
from akira.detect import scan_project, write_stack_markdown
from akira.detect.models import StackInfo
from akira.detect.renderer import SECTION_CATEGORIES, tool_value
from akira.fingerprint import fingerprint_project, write_fingerprint_markdown
from akira.fingerprint.models import FingerprintAnalysis
from akira.review import (
    Finding,
    ReviewCategory,
    analyze_stack,
    apply_review_findings,
    render_review,
)
from akira.skills import GeneratedSkill, InstalledSkillFile, generate_skills

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

app = typer.Typer(
    help="Akira detects project context and generates agent skills.",
    no_args_is_help=True,
)

console = Console()


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


@app.callback()
def cli() -> None:
    """
    Akira detects project context and generates agent skills.
    """


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
    """

    stack = scan_project(path)

    write_stack_markdown(output, stack)

    skill_paths = generate_skills(stack, output)

    agents = _resolve_agents(agent, path)

    install_results = [
        get_agent_adapter(resolved_agent).install(path, output)
        for resolved_agent in agents
    ]

    _print_detect_summary(
        stack,
        skill_paths,
        tuple(
            installed
            for install_result in install_results
            for installed in install_result.installed_files
        ),
        output,
        tuple(install_result.agent for install_result in install_results),
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
    """

    analysis = fingerprint_project(path, sample_size=sample_size, exclude=exclude or ())

    fingerprint_path = write_fingerprint_markdown(
        output,
        analysis,
        sample_size=sample_size,
    )

    _print_fingerprint_summary(
        analysis,
        fingerprint_path,
        path=path,
        output_dir=output,
        sample_size=sample_size,
        exclude=tuple(exclude or ()),
    )


@app.command()
def craft(
    *,
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Project directory containing generated .akira artifacts.",
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
            help="Agent target to configure.",
            callback=_validate_agent,
        ),
    ] = None,
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Directory containing generated Akira files.",
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = DEFAULT_OUTPUT_DIR,
) -> None:
    """
    Install generated Akira context for a coding agent.
    """

    try:

        agents = _resolve_agents(agent, path)

        results = [
            craft_context(path, agent=resolved_agent, artifact_dir=output)
            for resolved_agent in agents
        ]

    except MissingCraftPrerequisites as exc:

        typer.echo("Missing Akira artifacts:")

        for prerequisite in exc.missing:

            typer.echo(f"Missing: {prerequisite.path}")

            typer.echo(f"  {prerequisite.message}")

        raise typer.Exit(1) from exc

    except UnsupportedCraftAgent as exc:

        supported = (
            ", ".join(exc.supported)
            if exc.supported
            else ", ".join(SUPPORTED_AGENT_NAMES)
        )

        typer.echo(f"Unsupported agent '{exc.agent}'. Choose one of: {supported}.")

        raise typer.Exit(1) from exc

    except UnsupportedAgent as exc:

        supported = ", ".join(exc.supported)

        typer.echo(f"Unsupported agent '{exc.agent}'. Choose one of: {supported}.")

        raise typer.Exit(1) from exc

    _print_craft_summary(tuple(result.install_result for result in results))


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
    """
    Run the Akira CLI.
    """

    app()


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _validate_agent(agent: str | None) -> str | None:

    if agent is None:

        return None

    if agent not in SUPPORTED_AGENT_NAMES:

        supported = ", ".join(SUPPORTED_AGENT_NAMES)

        raise typer.BadParameter(
            f"Unsupported agent '{agent}'. Choose one of: {supported}."
        )

    return agent


def _resolve_agents(agent: str | None, path: Path) -> tuple[str, ...]:

    if agent is not None:

        return (agent,)

    detected_agents = detect_configured_agents(path)

    if not detected_agents:

        typer.echo(
            "No agent configuration detected. Defaulting to claude-code. "
            "Use --agent to override."
        )

        return (DEFAULT_AGENT,)

    typer.echo(f"Detected agents: {', '.join(detected_agents)}")

    if len(detected_agents) == 1:

        return detected_agents

    selected_agents = tuple(
        detected_agent
        for detected_agent in detected_agents
        if Confirm.ask(f"Install for {detected_agent}?", default=True)
    )

    if not selected_agents:

        typer.echo("No agents selected.")

        raise typer.Exit(1)

    return selected_agents


def _print_detect_summary(
    stack: StackInfo,
    generated_skills: tuple[GeneratedSkill, ...],
    installed_files: tuple[InstalledSkillFile, ...],
    output_dir: Path,
    agent: str | tuple[str, ...] | None,
) -> None:

    console.print(f"\nScanning [bold]{stack.project_root}[/bold]...\n")

    for line in _detect_section_lines(stack):

        console.print(_success_line(line))

    _print_phase_header("Generating skill tree")

    for generated_skill in generated_skills:

        console.print(_success_line(_relative_to(generated_skill.path, output_dir)))

    agent_target = _agent_target(installed_files, stack.project_root, agent)

    console.print()

    console.print(f"Installing to [bold]{agent_target}[/bold]...\n")

    installed_count = len(
        [
            installed
            for installed in installed_files
            if installed.status in {"installed", "updated", "unchanged"}
        ]
    )

    console.print(_success_line(f"{installed_count} skills installed"))

    console.print("\n  [bold]Done. Your agent knows your stack.[/bold]")


def _print_fingerprint_summary(
    analysis: FingerprintAnalysis,
    fingerprint_path: Path,
    *,
    path: Path,
    output_dir: Path,
    sample_size: int,
    exclude: tuple[str, ...],
) -> None:

    console.print(f"\nAnalyzing [bold]{path}[/bold]...\n")

    console.print(_success_line(f"Files analyzed: {len(analysis.files)}"))

    console.print(_success_line(f"Parsed: {len(analysis.parsed_files)}"))

    console.print(_success_line(f"Parse failures: {len(analysis.failed_files)}"))

    console.print(_success_line(f"Patterns extracted: {len(analysis.patterns)}"))

    console.print(_success_line(f"Confidence: {analysis.confidence:.2f}"))

    _print_phase_header("Writing fingerprint")

    console.print(_success_line(_relative_to(fingerprint_path, output_dir)))

    console.print(f"\n  Sample size: {sample_size}")

    for pattern in exclude:

        console.print(f"  Exclude: {pattern}")

    console.print("\n  [bold]Done.[/bold]")


def _print_craft_summary(results: tuple[AgentInstallResult, ...]) -> None:

    for result in results:

        target = _agent_target(
            result.installed_files,
            Path("."),
            result.agent,
        )

        console.print(f"\nInstalling to [bold]{target}[/bold]...\n")

        if not result.installed_files:

            console.print("  No files found to install.")

            continue

        installed_count = len(
            [
                installed
                for installed in result.installed_files
                if installed.status in {"installed", "updated", "unchanged"}
            ]
        )

        console.print(f"  Agent: {result.agent}")

        console.print(_success_line(f"{installed_count} files installed"))

    console.print("\n  [bold]Done.[/bold]")


def _detect_section_lines(stack: StackInfo) -> tuple[str, ...]:

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

    console.print(f"\n{title}...\n")

    if console.is_terminal:

        console.print(Rule(style="cyan"))


def _success_line(message: object) -> Text:

    text = Text("  ")

    text.append(_success_symbol(), style="green")

    text.append(f" {message}")

    return text


def _success_symbol() -> str:

    symbol = "✓"

    try:

        symbol.encode(console.encoding or "utf-8")

    except UnicodeEncodeError:

        return "+"

    return symbol


def _relative_to(path: Path, root: Path) -> Path:

    try:

        return path.relative_to(root)

    except ValueError:

        return path


def _agent_target(
    installed_files: tuple[InstalledSkillFile, ...],
    project_root: Path,
    agent: str | tuple[str, ...] | None,
) -> str:

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
