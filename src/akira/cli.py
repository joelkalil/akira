"""
Command line entry point for Akira.
"""

# Standard Libraries
from __future__ import annotations
from pathlib import Path
from typing import Annotated

# Third-Party Libraries
import typer
from rich.console import Console
from rich.prompt import Prompt

# Local Libraries
from akira.agents import SUPPORTED_AGENT_NAMES, UnsupportedAgent, get_agent_adapter
from akira.config import DEFAULT_AGENT, DEFAULT_OUTPUT_DIR
from akira.craft import (
    MissingCraftPrerequisites,
    UnsupportedCraftAgent,
    craft_context,
)
from akira.detect import scan_project, write_stack_markdown
from akira.fingerprint import fingerprint_project, write_fingerprint_markdown
from akira.review import (
    Finding,
    ReviewCategory,
    analyze_stack,
    apply_review_findings,
    render_review,
)
from akira.skills import generate_skills

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

app = typer.Typer(
    help="Akira detects project context and generates agent skills.",
    no_args_is_help=True,
)


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _validate_agent(agent: str) -> str:
    
    if agent not in SUPPORTED_AGENT_NAMES:
        
        supported = ", ".join(SUPPORTED_AGENT_NAMES)

        raise typer.BadParameter(
            f"Unsupported agent '{agent}'. Choose one of: {supported}."
        )

    return agent


@app.callback()

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def cli() -> None:
    """
    Akira detects project context and generates agent skills.
    """


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
    """
    Detect a project's stack and prepare agent skill output.
    """

    stack = scan_project(path)

    stack_path = write_stack_markdown(output, stack)

    skill_paths = generate_skills(stack, output)

    installed_paths = get_agent_adapter(agent).install(path, output).installed_files

    typer.echo(f"Project path: {path}")

    typer.echo(f"Agent: {agent}")

    typer.echo(f"Output: {output}")

    typer.echo(f"Wrote: {stack_path}")

    for skill in skill_paths:
        
        typer.echo(f"Wrote: {skill.path}")

    for installed in installed_paths:
        
        if installed.status in {"installed", "updated"}:
            
            typer.echo(f"{installed.status.title()}: {installed.path}")


@app.command()
def fingerprint(
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
            help="Project-relative path or glob to exclude. May be passed multiple times.",
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

    typer.echo(f"Project path: {path}")

    typer.echo(f"Sample size: {sample_size}")

    typer.echo(f"Output: {output}")

    for pattern in exclude or ():
        
        typer.echo(f"Exclude: {pattern}")

    typer.echo(f"Files analyzed: {len(analysis.files)}")

    typer.echo(f"Parsed: {len(analysis.parsed_files)}")

    typer.echo(f"Parse failures: {len(analysis.failed_files)}")

    typer.echo(f"Patterns extracted: {len(analysis.patterns)}")

    typer.echo(f"Confidence: {analysis.confidence:.2f}")

    typer.echo(f"Wrote: {fingerprint_path}")


@app.command()
def craft(
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
        str,
        typer.Option(
            "--agent",
            "-a",
            help="Agent target to configure.",
            callback=_validate_agent,
        ),
    ] = DEFAULT_AGENT,
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
        
        result = craft_context(path, agent=agent, artifact_dir=output)
        
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

    typer.echo(f"Project path: {result.project_root}")

    typer.echo(f"Agent: {result.install_result.agent}")

    typer.echo(f"Artifacts: {result.artifact_dir}")

    if not result.install_result.installed_files:
        
        typer.echo("No files found to install.")

        return

    for installed in result.install_result.installed_files:
        
        typer.echo(f"{installed.status.title()}: {installed.path}")


@app.command()
def review(
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


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


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
                "[yellow]This finding has no safe metadata-only change, so it was skipped.[/yellow]"
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
            "Replace unittest.TestCase classes with plain pytest test functions where practical.",
            "Prefer assert statements and fixtures over self.assert* and setUp/tearDown.",
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


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def main() -> None:
    """
    Run the Akira CLI.
    """

    app()
