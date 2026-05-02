"""Control-flow and function-shape extractor."""

from __future__ import annotations

import ast
from collections import Counter
from statistics import median

from akira.fingerprint.extractors._common import (
    iter_function_defs,
    make_pattern,
    modal_pattern,
)
from akira.fingerprint.models import FingerprintAnalysis, StylePattern

BRANCH_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.With,
    ast.AsyncWith,
    ast.Match,
)


def extract(analysis: FingerprintAnalysis) -> tuple[StylePattern, ...]:
    """Extract early returns, nesting, ternary usage, and function length."""
    functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for source in analysis.parsed_files:
        if source.tree is not None:
            functions.extend(iter_function_defs(source.tree))

    if not functions:
        return ()

    early_return_count = sum(1 for function in functions if _has_early_return(function))
    guard_count = sum(1 for function in functions if _has_guard_clause(function))
    nesting_depths = [_max_nesting_depth(function) for function in functions]
    ternary_count = sum(
        1 for function in functions for node in ast.walk(function) if isinstance(node, ast.IfExp)
    )
    lengths = [_function_length(function) for function in functions]
    dominant_depth, depth_share, depth_samples = modal_pattern(nesting_depths)

    return (
        make_pattern(
            dimension="structure",
            name="early_returns",
            value=_frequency_label(early_return_count, len(functions)),
            confidence=early_return_count / len(functions),
            samples=len(functions),
            description="Functions use returns before the final statement.",
            evidence={"functions_with_early_return": early_return_count},
        ),
        make_pattern(
            dimension="structure",
            name="guard_clauses",
            value=_frequency_label(guard_count, len(functions)),
            confidence=guard_count / len(functions),
            samples=len(functions),
            description="Functions use top-of-body guard clauses with return or raise.",
            evidence={"functions_with_guard_clause": guard_count},
        ),
        make_pattern(
            dimension="structure",
            name="nesting_depth",
            value=dominant_depth,
            confidence=depth_share,
            samples=depth_samples,
            description="Dominant maximum control-flow nesting depth per function.",
            evidence={"distribution": dict(sorted(Counter(nesting_depths).items()))},
        ),
        make_pattern(
            dimension="structure",
            name="ternary_usage",
            value="uses_ternary" if ternary_count else "avoids_ternary",
            confidence=1.0 if ternary_count == 0 else min(1.0, ternary_count / len(functions)),
            samples=len(functions),
            description="Conditional expressions are detected in function bodies.",
            evidence={"ternary_expressions": ternary_count},
        ),
        make_pattern(
            dimension="structure",
            name="function_length",
            value="under_30_lines" if median(lengths) <= 30 else "over_30_lines",
            confidence=sum(1 for length in lengths if length <= 30) / len(lengths),
            samples=len(lengths),
            description="Function body length preference based on physical source lines.",
            evidence={"median": median(lengths), "max": max(lengths)},
        ),
    )


def _has_early_return(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
    if not returns:
        return False

    final_statement = function.body[-1] if function.body else None
    final_line = getattr(final_statement, "end_lineno", getattr(final_statement, "lineno", 0))
    return any(getattr(node, "lineno", final_line) < final_line for node in returns)


def _has_guard_clause(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for statement in function.body[:3]:
        if isinstance(statement, ast.If) and _body_exits(statement.body):
            return True
    return False


def _body_exits(body: list[ast.stmt]) -> bool:
    return bool(body) and isinstance(body[-1], ast.Return | ast.Raise | ast.Continue | ast.Break)


def _max_nesting_depth(function: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    return max((_nesting_depth(statement, 0) for statement in function.body), default=0)


def _nesting_depth(node: ast.AST, depth: int) -> int:
    next_depth = depth + 1 if isinstance(node, BRANCH_NODES) else depth
    child_depths = [_nesting_depth(child, next_depth) for child in ast.iter_child_nodes(node)]
    return max([next_depth, *child_depths])


def _function_length(function: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    end_lineno = getattr(function, "end_lineno", function.lineno)
    return max(1, end_lineno - function.lineno + 1)


def _frequency_label(count: int, total: int) -> str:
    share = count / total if total else 0.0
    if share >= 0.6:
        return "preferred"
    if share > 0:
        return "occasional"
    return "rare"
