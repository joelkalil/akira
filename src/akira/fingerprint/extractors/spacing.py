"""Spacing style extractor."""

from __future__ import annotations

import ast
from collections import Counter

from akira.fingerprint.extractors._common import (
    blank_lines_before,
    blank_lines_between,
    make_pattern,
    modal_pattern,
)
from akira.fingerprint.models import FingerprintAnalysis, StylePattern


def extract(analysis: FingerprintAnalysis) -> tuple[StylePattern, ...]:
    """Extract blank-line and logical spacing preferences."""
    top_level: list[int] = []
    methods: list[int] = []
    after_imports: list[int] = []
    logical_blocks: list[int] = []

    for source in analysis.parsed_files:
        if source.tree is None:
            continue

        lines = source.text.splitlines()
        module = source.tree
        assert isinstance(module, ast.Module)

        for node in module.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                top_level.append(blank_lines_before(lines, node.lineno))
            if isinstance(node, ast.ClassDef):
                class_methods = [
                    child
                    for child in node.body
                    if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
                ]
                for child in class_methods[1:]:
                    methods.append(blank_lines_before(lines, child.lineno))

        import_gap = _blank_lines_after_import_section(module, lines)
        if import_gap is not None:
            after_imports.append(import_gap)

        for node in ast.walk(module):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                for previous, current in zip(node.body, node.body[1:]):
                    previous_end = getattr(previous, "end_lineno", previous.lineno)
                    gap = blank_lines_between(lines, previous_end, current.lineno)
                    if gap > 0:
                        logical_blocks.append(gap)

    patterns: list[StylePattern] = []
    patterns.extend(
        _dominant_blank_line_pattern(
            name="top_level_definitions",
            values=top_level,
            description="Blank lines before top-level functions and classes.",
        )
    )
    patterns.extend(
        _dominant_blank_line_pattern(
            name="methods",
            values=methods,
            description="Blank lines before methods inside classes.",
        )
    )
    patterns.extend(
        _dominant_blank_line_pattern(
            name="after_imports",
            values=after_imports,
            description="Blank lines between the import section and the next statement.",
        )
    )
    patterns.extend(
        _dominant_blank_line_pattern(
            name="logical_blocks",
            values=logical_blocks,
            description="Blank lines used between logical statement groups inside functions.",
        )
    )
    return tuple(patterns)


def _dominant_blank_line_pattern(
    *,
    name: str,
    values: list[int],
    description: str,
) -> tuple[StylePattern, ...]:
    value, share, samples = modal_pattern(values)
    if value is None:
        return ()

    return (
        make_pattern(
            dimension="spacing",
            name=name,
            value=value,
            confidence=share,
            samples=samples,
            description=description,
            evidence={"distribution": dict(sorted(Counter(values).items()))},
        ),
    )


def _blank_lines_after_import_section(module: ast.Module, lines: list[str]) -> int | None:
    import_nodes = [
        node
        for node in module.body
        if isinstance(node, ast.Import | ast.ImportFrom)
        or (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
    ]
    imports = [node for node in import_nodes if isinstance(node, ast.Import | ast.ImportFrom)]
    if not imports:
        return None

    last_import = max(imports, key=lambda node: getattr(node, "end_lineno", node.lineno))
    last_line = getattr(last_import, "end_lineno", last_import.lineno)
    next_nodes = [node for node in module.body if node.lineno > last_line]
    if not next_nodes:
        return None

    return blank_lines_between(lines, last_line, next_nodes[0].lineno)
