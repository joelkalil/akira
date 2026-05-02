"""Rich reporting for Akira stack reviews."""

from __future__ import annotations

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from akira.review.analyzer import ReviewCategory, ReviewResult


CATEGORY_STYLES = {
    ReviewCategory.CONSISTENCY: ("green", "Consistency"),
    ReviewCategory.SUGGESTION: ("yellow", "Suggestion"),
    ReviewCategory.INCOMPATIBILITY: ("red", "Incompatibility"),
    ReviewCategory.MISSING: ("blue", "Missing"),
}


def render_review(result: ReviewResult, console: Console | None = None) -> None:
    """Display categorized review findings with Rich."""
    output = console or Console()
    output.print(
        Panel.fit(
            f"[bold]Akira Review[/bold]\n{escape(result.stack.project_name)}",
            border_style="cyan",
        )
    )

    if not result.findings:
        output.print("[green]No review findings.[/green]")
        return

    for category in ReviewCategory:
        findings = result.by_category(category)
        if not findings:
            continue

        style, title = CATEGORY_STYLES[category]
        table = Table(
            title=f"{title} ({len(findings)})",
            title_style=f"bold {style}",
            border_style=style,
            show_lines=False,
        )
        table.add_column("Rule", style=f"bold {style}", no_wrap=True)
        table.add_column("Message")
        table.add_column("Migration", no_wrap=True)

        for finding in findings:
            table.add_row(
                finding.rule_id,
                finding.message,
                finding.migration or "",
            )

        output.print(table)
