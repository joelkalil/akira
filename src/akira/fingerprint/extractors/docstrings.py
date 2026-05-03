"""
Docstring style and coverage extractor.
"""

# Standard Libraries
from __future__ import annotations

import ast
from collections import Counter

# Local Libraries
from akira.fingerprint.extractors._common import (
    make_pattern,
    modal_pattern,
)
from akira.fingerprint.models import FingerprintAnalysis, StylePattern

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def extract(analysis: FingerprintAnalysis) -> tuple[StylePattern, ...]:
    """
    Extract docstring coverage, style, and public/private behavior.

    Parameters
    ----------
    analysis : FingerprintAnalysis
        The analysis object containing parsed files and metadata.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple of StylePattern instances representing docstring patterns.
    """

    public_defs: list[ast.AST] = []

    private_defs: list[ast.AST] = []

    classes: list[ast.ClassDef] = []

    functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

    styles: list[str] = []

    for source in analysis.parsed_files:
        if source.tree is None:
            continue

        for node in ast.walk(source.tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node)

                _append_by_visibility(node, public_defs, private_defs)

                styles.extend(_docstring_style(node))

            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                functions.append(node)

                _append_by_visibility(node, public_defs, private_defs)

                styles.extend(_docstring_style(node))

    patterns: list[StylePattern] = []

    patterns.extend(_coverage_pattern("public_docstrings", public_defs))

    patterns.extend(_private_behavior_pattern(private_defs))

    patterns.extend(_coverage_pattern("class_docstrings", classes))

    patterns.extend(_coverage_pattern("function_docstrings", functions))

    patterns.extend(_style_pattern(styles))

    return tuple(patterns)


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _coverage_pattern(name: str, nodes: list[ast.AST]) -> tuple[StylePattern, ...]:
    """
    Create a StylePattern for docstring coverage.

    Parameters
    ----------
    name : str
        The name of the pattern dimension (e.g., "public_docstrings").
    nodes : list[ast.AST]
        A list of AST nodes (classes or functions) to analyze for docstring coverage.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple of StylePattern instances representing docstring patterns.
    """

    if not nodes:
        return ()

    documented = sum(1 for node in nodes if ast.get_docstring(node) is not None)

    return (
        make_pattern(
            dimension="docstrings",
            name=name,
            value="documented" if documented / len(nodes) >= 0.5 else "sparse",
            confidence=documented / len(nodes),
            samples=len(nodes),
            description=f"Docstring coverage for {name.replace('_', ' ')}.",
            evidence={"documented": documented, "total": len(nodes)},
        ),
    )


def _private_behavior_pattern(nodes: list[ast.AST]) -> tuple[StylePattern, ...]:
    """
    Create a StylePattern for private docstring behavior.

    Parameters
    ----------
    nodes : list[ast.AST]
        A list of AST nodes representing private definitions to analyze for docstring
        behavior.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple of StylePattern instances representing private docstring behavior.
    """

    if not nodes:
        return ()

    undocumented = sum(1 for node in nodes if ast.get_docstring(node) is None)

    return (
        make_pattern(
            dimension="docstrings",
            name="private_docstring_behavior",
            value="omit_private_docstrings",
            confidence=undocumented / len(nodes),
            samples=len(nodes),
            description="Private functions and classes omit docstrings.",
            evidence={"undocumented_private": undocumented, "private_defs": len(nodes)},
        ),
    )


def _style_pattern(styles: list[str]) -> tuple[StylePattern, ...]:
    """
    Create a StylePattern for docstring style.

    Parameters
    ----------
    styles : list[str]
        A list of docstring styles identified in the codebase (e.g., "google", "numpy",
        "sphinx", "plain").

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple of StylePattern instances representing the dominant docstring style.
    """

    style, share, samples = modal_pattern(styles)

    if style is None:
        return ()

    return (
        make_pattern(
            dimension="docstrings",
            name="docstring_style",
            value=style,
            confidence=share,
            samples=samples,
            description="Dominant docstring format among documented definitions.",
            evidence={"distribution": dict(sorted(Counter(styles).items()))},
        ),
    )


def _append_by_visibility(
    node: ast.AST, public_defs: list[ast.AST], private_defs: list[ast.AST]
) -> None:
    """
    Append an AST node to the public or private definitions list.

    Parameters
    ----------
    node : ast.AST
        The AST node representing a class or function definition.
    public_defs : list[ast.AST]
        The list to append to if the node is considered public.
    private_defs : list[ast.AST]
        The list to append to if the node is considered private.
    """

    name = getattr(node, "name", "")

    if name.startswith("_") and not name.startswith("__"):
        private_defs.append(node)

    else:
        public_defs.append(node)


def _docstring_style(node: ast.AST) -> list[str]:
    """
    Identify the docstring style used in the given AST node.

    Parameters
    ----------
    node : ast.AST
        The AST node representing a class or function definition to analyze for
        docstring style.

    Returns
    -------
    list[str]
        A list containing the identified docstring style(s) for the given node.
    """

    docstring = ast.get_docstring(node)

    if not docstring:
        return []

    if "Args:" in docstring or "Returns:" in docstring or "Raises:" in docstring:
        return ["google"]

    if "Parameters\n" in docstring and "-------" in docstring:
        return ["numpy"]

    if ":param " in docstring or ":returns:" in docstring or ":raises " in docstring:
        return ["sphinx"]

    return ["plain"]
