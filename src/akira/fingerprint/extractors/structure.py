"""
Control-flow and function-shape extractor.
"""

# Standard Libraries
import ast
from __future__ import annotations
from collections import Counter
from statistics import median

# Local Libraries
from akira.fingerprint.extractors._common import (
    iter_function_defs,
    make_pattern,
    modal_pattern,
)
from akira.fingerprint.models import FingerprintAnalysis, StylePattern

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def extract(analysis: FingerprintAnalysis) -> tuple[StylePattern, ...]:
    """
    Extract early returns, nesting, ternary usage, and function length.

    Parameters
    ----------
    analysis : FingerprintAnalysis
        The analysis context containing parsed files and other relevant data.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple of StylePattern instances representing the extracted structural patterns.
    """

    functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

    for source in analysis.parsed_files:

        if source.tree is not None:

            functions.extend(iter_function_defs(source.tree))

    if not functions:

        return ()

    early_return_count = sum(1 for function in functions if _has_early_return(function))

    guard_count = sum(1 for function in functions if _has_guard_clause(function))

    nesting_depths = [_max_nesting_depth(function) for function in functions]

    ternary_counts = [
        sum(1 for node in _walk_current_scope(function) if isinstance(node, ast.IfExp))
        for function in functions
    ]

    ternary_count = sum(ternary_counts)

    functions_with_ternary = sum(1 for count in ternary_counts if count > 0)

    ternary_confidence = (
        1.0 if functions_with_ternary == 0 else functions_with_ternary / len(functions)
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
            value="uses_ternary" if functions_with_ternary else "avoids_ternary",
            confidence=ternary_confidence,
            samples=len(functions),
            description="Conditional expressions are detected in function bodies.",
            evidence={
                "ternary_expressions": ternary_count,
                "functions_with_ternary": functions_with_ternary,
            },
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


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _has_early_return(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """
    Determine if a function has early returns, defined as return statements that
    are not the final statement in the function body.

    Parameters
    ----------
    function : ast.FunctionDef | ast.AsyncFunctionDef
        The function definition node to analyze.

    Returns
    -------
    bool
        True if the function has early returns, False otherwise.
    """

    returns = [
        node for node in _walk_current_scope(function) if isinstance(node, ast.Return)
    ]

    if not returns:

        return False

    final_statement = function.body[-1] if function.body else None

    final_line = getattr(
        final_statement, "end_lineno", getattr(final_statement, "lineno", 0)
    )

    return any(getattr(node, "lineno", final_line) < final_line for node in returns)


def _has_guard_clause(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """
    Determine if a function has guard clauses, defined as if statements in the top
    three statements of the function body that exit the function (via return, raise,
    continue, or break).

    Parameters
    ----------
    function : ast.FunctionDef | ast.AsyncFunctionDef
        The function definition node to analyze.

    Returns
    -------
    bool
        True if the function has guard clauses, False otherwise.
    """

    for statement in function.body[:3]:

        if isinstance(statement, ast.If) and _body_exits(statement.body):

            return True

    return False


def _body_exits(body: list[ast.stmt]) -> bool:
    """
    Check if the given body of statements contains an exit statement (return, raise, continue,
    or break) as the last statement.

    Parameters
    ----------
    body : list[ast.stmt]
        The list of statements to check.

    Returns
    -------
    bool
        True if the body ends with an exit statement, False otherwise.
    """

    return bool(body) and isinstance(
        body[-1], ast.Return | ast.Raise | ast.Continue | ast.Break
    )


def _max_nesting_depth(function: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """
    Calculate the maximum control-flow nesting depth of a function, where nesting is
    defined by the presence of branch nodes (if, for, while, try, with, match) and is
    incremented when entering these nodes. Function and class definitions also increment
    nesting depth but do not contribute to the maximum depth calculation.

    Parameters
    ----------
    function : ast.FunctionDef | ast.AsyncFunctionDef
        The function definition node to analyze.

    Returns
    -------
    int
        The maximum nesting depth of the function.
    """

    return max((_nesting_depth(statement, 0) for statement in function.body), default=0)


def _nesting_depth(node: ast.AST, depth: int) -> int:
    """
    Recursively calculate the nesting depth of a node, where depth is incremented for
    branch nodes and function/class definitions.

    Parameters
    ----------
    node : ast.AST
        The AST node to analyze.
    depth : int
        The current nesting depth at this node.

    Returns
    -------
    int
        The maximum nesting depth found in this node and its children.
    """

    next_depth = depth + 1 if isinstance(node, BRANCH_NODES) else depth

    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):

        return next_depth

    child_depths = [
        _nesting_depth(child, next_depth) for child in ast.iter_child_nodes(node)
    ]

    return max([next_depth, *child_depths])


def _walk_current_scope(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[ast.AST]:
    """
    Walk the AST of a function body while ignoring nested function and class definitions, returning
    a flat list of nodes in the current scope.

    Parameters
    ----------
    function : ast.FunctionDef | ast.AsyncFunctionDef
        The function definition node to analyze.

    Returns
    -------
    list[ast.AST]
        A list of AST nodes in the current scope of the function body, excluding nested function and
        class definitions
    """

    nodes: list[ast.AST] = []

    for statement in function.body:

        nodes.extend(_walk_without_nested_scopes(statement))

    return nodes


def _walk_without_nested_scopes(node: ast.AST) -> list[ast.AST]:
    """
    Recursively walk an AST node while ignoring nested function and class definitions and return a
    flat list of nodes in the current scope.

    Parameters
    ----------
    node : ast.AST
        The AST node to analyze.

    Returns
    -------
    list[ast.AST]
        A list of AST nodes in the current scope, excluding nested function and class definitions.
    """

    nodes = [node]

    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):

        return nodes

    for child in ast.iter_child_nodes(node):

        nodes.extend(_walk_without_nested_scopes(child))

    return nodes


def _function_length(function: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """
    Calculate the length of a function in terms of physical source lines, using the function's
    starting line number and ending line number. If the end line number is not available, it is
    approximated as the starting line number, resulting in a minimum length of 1.

    Parameters
    ----------
    function : ast.FunctionDef | ast.AsyncFunctionDef
        The function definition node to analyze.

    Returns
    -------
    int
        The length of the function in terms of physical source lines.
    """

    end_lineno = getattr(function, "end_lineno", function.lineno)

    return max(1, end_lineno - function.lineno + 1)


def _frequency_label(count: int, total: int) -> str:
    """
    Convert a count and total into a frequency label of "preferred", "occasional", or "rare" based on
    the share of the count to the total.

    Parameters
    ----------
    count : int
        The count of occurrences for a particular pattern.
    total : int
        The total number of samples or instances considered for the pattern.

    Returns
    -------
    str
        A frequency label indicating the prevalence of the pattern: "preferred" for 60% or more,
        "occasional" for more than 0% but less than 60%, and "rare" for 0%.
    """

    share = count / total if total else 0.0

    if share >= 0.6:

        return "preferred"

    if share > 0:

        return "occasional"

    return "rare"
