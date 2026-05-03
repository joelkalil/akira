"""
Apply accepted review findings to generated Akira artifacts.
"""

# Standard Libraries
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Local Libraries
from akira.detect.models import Signal, StackInfo
from akira.detect.renderer import write_stack_markdown
from akira.review.analyzer import Finding
from akira.skills.generator import GeneratedSkill, generate_skills

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class AppliedReviewChange:
    """
    A review finding that changed generated Akira artifacts.
    """

    finding: Finding

    stack_path: Path

    generated_skills: tuple[GeneratedSkill, ...]


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def apply_review_findings(
    stack: StackInfo,
    findings: tuple[Finding, ...],
    output_dir: Path,
) -> tuple[StackInfo, tuple[AppliedReviewChange, ...]]:
    """
    Apply accepted safe findings and regenerate stack-dependent artifacts.

    Parameters
    ----------
    stack : StackInfo
        The stack value.
    findings : tuple[Finding, ...]
        The findings value.
    output_dir : Path
        The output dir value.

    Returns
    -------
    tuple[StackInfo, tuple[AppliedReviewChange, ...]]
        The result of the operation.
    """

    accepted_stack = stack

    changed_findings: list[Finding] = []

    for finding in findings:
        updated_stack = apply_finding_to_stack(accepted_stack, finding)

        if updated_stack == accepted_stack:
            continue

        changed_findings.append(finding)

        accepted_stack = updated_stack

    if not changed_findings:
        return accepted_stack, ()

    stack_path = write_stack_markdown(output_dir, accepted_stack)

    generated = generate_skills(accepted_stack, output_dir)

    applied = tuple(
        AppliedReviewChange(
            finding=finding,
            stack_path=stack_path,
            generated_skills=generated,
        )
        for finding in changed_findings
    )

    return accepted_stack, tuple(applied)


def apply_finding_to_stack(stack: StackInfo, finding: Finding) -> StackInfo:
    """
    Return a new stack model with a finding's safe metadata change applied.

    Parameters
    ----------
    stack : StackInfo
        The stack value.
    finding : Finding
        The finding value.

    Returns
    -------
    StackInfo
        The result of the operation.
    """

    change = finding.safe_change

    if change is None:
        return stack

    remove_keys = {
        (tool.strip().lower(), category.strip().lower())
        for tool, category in change.remove_signals
    }

    signals = [
        signal
        for signal in stack.signals
        if (signal.tool, signal.category) not in remove_keys
    ]

    existing_keys = {(signal.tool, signal.category) for signal in signals}

    for tool, category in change.add_signals:
        normalized_tool = tool.strip().lower()

        normalized_category = category.strip().lower()

        if (normalized_tool, normalized_category) in existing_keys:
            continue

        signals.append(
            Signal(
                tool=normalized_tool,
                category=normalized_category,
                confidence=1.0,
                source="akira review",
                metadata={"accepted_review_rule": finding.rule_id},
            )
        )

        existing_keys.add((normalized_tool, normalized_category))

    return StackInfo.from_signals(stack.project_root, signals)
