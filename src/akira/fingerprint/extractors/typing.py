"""
Type hint style extractor.
"""

# Standard Libraries
from __future__ import annotations
import ast
from collections import Counter

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

COMPLEX_TYPING_NAMES = {
    "Any",
    "Callable",
    "ClassVar",
    "Final",
    "Generic",
    "Iterable",
    "Iterator",
    "Literal",
    "Mapping",
    "MutableMapping",
    "NamedTuple",
    "Protocol",
    "Sequence",
    "TypedDict",
    "TypeVar",
    "cast",
    "overload",
}


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def extract(analysis: FingerprintAnalysis) -> tuple[StylePattern, ...]:
    """
    Extract type annotation coverage and annotation syntax preferences.

    Parameters
    ----------
    analysis: FingerprintAnalysis
        The fingerprint analysis context containing parsed source files.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple of style patterns related to type hint usage.
    """

    functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

    optional_styles: list[str] = []

    typing_imports: list[str] = []

    for source in analysis.parsed_files:

        if source.tree is None:

            continue

        functions.extend(iter_function_defs(source.tree))

        optional_styles.extend(_optional_styles(source.tree))

        typing_imports.extend(_typing_imports(source.tree))

    patterns: list[StylePattern] = []

    patterns.extend(_signature_coverage_pattern(functions))

    patterns.extend(_return_hint_pattern(functions))

    patterns.extend(_optional_syntax_pattern(optional_styles))

    patterns.extend(_complex_type_import_pattern(typing_imports))

    return tuple(patterns)


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _signature_coverage_pattern(
    functions: list[ast.FunctionDef | ast.AsyncFunctionDef],
) -> tuple[StylePattern, ...]:
    """
    Analyze the coverage of type hints in function signatures.

    Parameters
    ----------
    functions: list[ast.FunctionDef | ast.AsyncFunctionDef]
        A list of function definitions to analyze.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple containing a style pattern for signature coverage.
    """

    if not functions:

        return ()

    fully_typed = sum(1 for function in functions if _has_full_signature(function))

    share = fully_typed / len(functions)

    if share >= 0.8:

        value = "full_signature_hints"

    elif share >= 0.35:

        value = "partial_signature_hints"

    else:

        value = "minimal_signature_hints"

    return (
        make_pattern(
            dimension="typing",
            name="signature_coverage",
            value=value,
            confidence=share,
            samples=len(functions),
            description="Function signatures include argument and return type hints.",
            evidence={"fully_typed": fully_typed, "functions": len(functions)},
        ),
    )


def _return_hint_pattern(
    functions: list[ast.FunctionDef | ast.AsyncFunctionDef],
) -> tuple[StylePattern, ...]:
    """
    Analyze the presence of explicit return type hints in functions.

    Parameters
    ----------
    functions: list[ast.FunctionDef | ast.AsyncFunctionDef]
        A list of function definitions to analyze.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple containing a style pattern for return type hint usage.
    """

    if not functions:

        return ()

    annotated = sum(1 for function in functions if function.returns is not None)

    return (
        make_pattern(
            dimension="typing",
            name="return_hints",
            value="explicit_return_hints",
            confidence=annotated / len(functions),
            samples=len(functions),
            description="Functions declare explicit return type hints.",
            evidence={"annotated": annotated, "functions": len(functions)},
        ),
    )


def _optional_syntax_pattern(styles: list[str]) -> tuple[StylePattern, ...]:
    """
    Analyze the preferred syntax for optional type annotations.

    Parameters
    ----------
    styles: list[str]
        A list of identified optional annotation styles from the codebase.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple containing a style pattern for optional annotation syntax preference.
    """

    style, share, samples = modal_pattern(styles)

    if style is None:

        return ()

    return (
        make_pattern(
            dimension="typing",
            name="optional_syntax",
            value=style,
            confidence=share,
            samples=samples,
            description="Optional values use a consistent annotation syntax.",
            evidence={"distribution": dict(sorted(Counter(styles).items()))},
        ),
    )


def _complex_type_import_pattern(imports: list[str]) -> tuple[StylePattern, ...]:
    """
    Analyze the usage of complex typing helpers imported from the typing module.

    Parameters
    ----------
    imports: list[str]
        A list of names imported from the typing module across the codebase.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple containing a style pattern for complex typing helper usage.
    """

    if not imports:

        return ()

    complex_imports = [name for name in imports if name in COMPLEX_TYPING_NAMES]

    return (
        make_pattern(
            dimension="typing",
            name="complex_type_imports",
            value=tuple(sorted(set(complex_imports))),
            confidence=len(complex_imports) / len(imports),
            samples=len(imports),
            description="Complex typing helpers are imported explicitly from typing.",
            evidence={"imports": dict(sorted(Counter(imports).items()))},
        ),
    )


def _has_full_signature(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """
    Determine if a function has type hints for all its parameters and return value.

    Parameters
    ----------
    function: ast.FunctionDef | ast.AsyncFunctionDef
        The function definition to analyze.

    Returns
    -------
    bool
        True if the function has type hints for all parameters and return value, False otherwise.
    """

    args = [
        *function.args.posonlyargs,
        *function.args.args,
        *function.args.kwonlyargs,
    ]

    required_args = [arg for arg in args if arg.arg not in {"self", "cls"}]

    args_typed = all(arg.annotation is not None for arg in required_args)

    return args_typed and function.returns is not None


def _typing_imports(tree: ast.AST) -> list[str]:
    """
    Extract names imported from the typing module in the given AST.

    Parameters
    ----------
    tree: ast.AST
        The abstract syntax tree to analyze for typing imports.

    Returns
    -------
    list[str]
        A list of names imported from the typing module.
    """

    imports: list[str] = []

    for node in ast.walk(tree):

        if isinstance(node, ast.ImportFrom) and node.module == "typing":

            imports.extend(alias.name for alias in node.names)

    return imports


def _optional_styles(tree: ast.AST) -> list[str]:
    """
    Identify the syntax styles used for optional type annotations in the given AST.

    Parameters
    ----------
    tree: ast.AST
        The abstract syntax tree to analyze for optional annotation styles.

    Returns
    -------
    list[str]
        A list of identified optional annotation styles (e.g., "pipe_union_none", "typing_optional",
        "typing_union_none").
    """

    styles: list[str] = []

    for node in ast.walk(tree):

        annotation = _annotation_node(node)

        if annotation is None:

            continue

        style = _classify_optional(annotation)

        if style is not None:

            styles.append(style)

    return styles


def _annotation_node(node: ast.AST) -> ast.AST | None:

    if isinstance(node, ast.arg):

        return node.annotation

    if isinstance(node, ast.AnnAssign):

        return node.annotation

    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):

        return node.returns

    return None


def _classify_optional(annotation: ast.AST) -> str | None:

    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):

        if _contains_none(annotation.left) or _contains_none(annotation.right):

            return "pipe_union_none"

    if isinstance(annotation, ast.Subscript):

        name = _annotation_name(annotation.value)

        if name == "Optional":

            return "typing_optional"

        if name == "Union" and _contains_none(annotation.slice):

            return "typing_union_none"

    return None


def _contains_none(node: ast.AST) -> bool:

    if isinstance(node, ast.Constant) and node.value is None:

        return True

    if isinstance(node, ast.Name) and node.id == "None":

        return True

    if isinstance(node, ast.Tuple):

        return any(_contains_none(element) for element in node.elts)

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):

        return _contains_none(node.left) or _contains_none(node.right)

    return False


def _annotation_name(node: ast.AST) -> str:

    if isinstance(node, ast.Name):

        return node.id

    if isinstance(node, ast.Attribute):

        return node.attr

    return ""
