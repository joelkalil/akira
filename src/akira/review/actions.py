"""Apply accepted review findings to generated Akira artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from akira.detect.models import Signal, StackInfo
from akira.detect.renderer import write_stack_markdown
from akira.review.analyzer import Finding
from akira.skills.generator import GeneratedSkill, generate_skills


@dataclass(frozen=True)
class AppliedReviewChange:
    """A review finding that changed generated Akira artifacts."""

    finding: Finding
    stack_path: Path
    generated_skills: tuple[GeneratedSkill, ...]


def apply_review_findings(
    stack: StackInfo,
    findings: tuple[Finding, ...],
    output_dir: Path,
) -> tuple[StackInfo, tuple[AppliedReviewChange, ...]]:
    """Apply accepted safe findings and regenerate stack-dependent artifacts."""
    accepted_stack = stack
    applied: list[AppliedReviewChange] = []

    for finding in findings:
        updated_stack = apply_finding_to_stack(accepted_stack, finding)
        if updated_stack == accepted_stack:
            continue

        stack_path = write_stack_markdown(output_dir, updated_stack)
        generated = generate_skills(updated_stack, output_dir)
        applied.append(
            AppliedReviewChange(
                finding=finding,
                stack_path=stack_path,
                generated_skills=generated,
            )
        )
        accepted_stack = updated_stack

    return accepted_stack, tuple(applied)


def apply_finding_to_stack(stack: StackInfo, finding: Finding) -> StackInfo:
    """Return a new stack model with a finding's safe metadata change applied."""
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
