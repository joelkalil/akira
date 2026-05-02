"""
Module and class organization extractor.
"""

# Standard Libraries
import ast
from __future__ import annotations
from collections import Counter

# Local Libraries
from akira.fingerprint.extractors._common import make_pattern, modal_pattern
from akira.fingerprint.models import FingerprintAnalysis, StylePattern

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

MODULE_ORDER = {
    "module_docstring": 0,
    "imports": 1,
    "constants": 2,
    "types": 3,
    "private_helpers": 4,
    "public_functions": 5,
    "classes": 6,
    "main_block": 7,
}


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def extract(analysis: FingerprintAnalysis) -> tuple[StylePattern, ...]:
    """
    Extract module ordering, helper placement, class order, and main blocks.

    Parameters
    ----------
    analysis : FingerprintAnalysis
        The analysis containing parsed files to extract patterns from.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple of StylePattern instances representing the extracted patterns.
    """

    module_sequences: list[tuple[str, ...]] = []

    ordered_modules = 0

    private_before_public = 0

    modules_with_helpers = 0

    class_orders: list[tuple[str, ...]] = []

    main_blocks_at_end = 0

    main_blocks = 0

    for source in analysis.parsed_files:

        if source.tree is None:

            continue

        module = source.tree

        assert isinstance(module, ast.Module)

        sequence = _module_sequence(module)

        if sequence:

            module_sequences.append(sequence)

            if _is_ordered(sequence, MODULE_ORDER):

                ordered_modules += 1

        helper_result = _helper_placement(module)

        if helper_result is not None:

            modules_with_helpers += 1

            if helper_result:

                private_before_public += 1

        for node in module.body:

            if isinstance(node, ast.ClassDef):

                class_sequence = _class_member_sequence(node)

                if class_sequence:

                    class_orders.append(class_sequence)

        main_index = _main_block_index(module)

        if main_index is not None:

            main_blocks += 1

            if main_index == len(module.body) - 1:

                main_blocks_at_end += 1

    patterns: list[StylePattern] = []

    patterns.extend(_module_order_pattern(module_sequences, ordered_modules))

    patterns.extend(
        _helper_placement_pattern(private_before_public, modules_with_helpers)
    )

    patterns.extend(_class_member_order_pattern(class_orders))

    patterns.extend(_main_block_pattern(main_blocks_at_end, main_blocks))

    return tuple(patterns)


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _module_order_pattern(
    sequences: list[tuple[str, ...]],
    ordered_modules: int,
) -> tuple[StylePattern, ...]:
    """
    Analyze the ordering of top-level elements in modules to identify common patterns.

    Parameters
    ----------
    sequences : list[tuple[str, ...]]
        A list of tuples representing the sequence of top-level element categories in each module.
    ordered_modules : int
        The count of modules that follow the defined ordering pattern.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple containing a StylePattern instance if a common ordering pattern is found, otherwise
        an empty tuple.
    """

    sequence, _, samples = modal_pattern(sequences)

    if sequence is None:

        return ()

    return (
        make_pattern(
            dimension="organization",
            name="module_order",
            value=sequence,
            confidence=ordered_modules / len(sequences),
            samples=samples,
            description="Top-level module elements follow a stable structural order.",
            evidence={
                "sequences": {
                    " > ".join(key): count for key, count in Counter(sequences).items()
                }
            },
        ),
    )


def _helper_placement_pattern(before: int, samples: int) -> tuple[StylePattern, ...]:
    """
    Analyze the placement of private helper functions relative to public functions in modules.

    Parameters
    ----------
    before : int
        The count of modules where private helper functions are placed before public functions.
    samples : int
        The total count of modules that contain both private helper functions and public functions.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple containing a StylePattern instance if a common helper placement pattern is found,
        otherwise an empty tuple.
    """

    if not samples:

        return ()

    return (
        make_pattern(
            dimension="organization",
            name="helper_placement",
            value="private_helpers_before_public_api",
            confidence=before / samples,
            samples=samples,
            description="Private helper functions are placed before public functions.",
            evidence={"matching_modules": before, "modules_with_helpers": samples},
        ),
    )


def _class_member_order_pattern(
    sequences: list[tuple[str, ...]],
) -> tuple[StylePattern, ...]:
    """
    Analyze the ordering of class members (attributes, constructor, public methods, private methods)
    to identify common patterns.

    Parameters
    ----------
    sequences : list[tuple[str, ...]]
        A list of tuples representing the sequence of class member categories in each class.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple containing a StylePattern instance if a common class member ordering pattern is found,
        otherwise an empty tuple.
    """

    sequence, share, samples = modal_pattern(sequences)

    if sequence is None:

        return ()

    return (
        make_pattern(
            dimension="organization",
            name="class_member_order",
            value=sequence,
            confidence=share,
            samples=samples,
            description="Class members follow a repeatable constructor/public/private order.",
            evidence={
                "distribution": {
                    " > ".join(key): count for key, count in Counter(sequences).items()
                }
            },
        ),
    )


def _main_block_pattern(at_end: int, samples: int) -> tuple[StylePattern, ...]:
    """
    Analyze the placement of `if __name__ == '__main__'` blocks to identify common patterns.

    Parameters
    ----------
    at_end : int
        The count of modules where the `if __name__ == '__main__'` block is placed at the end of
        the module.
    samples : int
        The total count of modules that contain the `if __name__ == '__main__'` block.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple containing a StylePattern instance if a common main block placement pattern is found,
        otherwise an empty tuple.
    """

    if not samples:

        return ()

    return (
        make_pattern(
            dimension="organization",
            name="main_block",
            value="at_module_end",
            confidence=at_end / samples,
            samples=samples,
            description="if __name__ == '__main__' blocks are placed at module end.",
            evidence={"main_blocks": samples, "at_end": at_end},
        ),
    )


def _module_sequence(module: ast.Module) -> tuple[str, ...]:
    """
    Determine the sequence of top-level element categories in a module.

    Parameters
    ----------
    module : ast.Module
        The AST node representing the module to analyze.

    Returns
    -------
    tuple[str, ...]
        A tuple of strings representing the sequence of top-level element categories in the module.
    """

    categories = [_module_category(node) for node in module.body]

    return tuple(dict.fromkeys(category for category in categories if category))


def _module_category(node: ast.stmt) -> str | None:
    """
    Categorize a top-level AST node in a module into a specific category for organizational analysis.

    Parameters
    ----------
    node : ast.stmt
        The AST node to categorize.

    Returns
    -------
    str | None
        A string representing the category of the node, or None if it does not fit any category.
    """

    if _is_docstring_expr(node):

        return "module_docstring"

    if isinstance(node, ast.Import | ast.ImportFrom):

        return "imports"

    if _is_main_block(node):

        return "main_block"

    if isinstance(node, ast.ClassDef):

        return "types" if _is_type_container(node) else "classes"

    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):

        return "private_helpers" if node.name.startswith("_") else "public_functions"

    if isinstance(node, ast.Assign | ast.AnnAssign):

        return "constants"

    return None


def _class_member_sequence(node: ast.ClassDef) -> tuple[str, ...]:
    """
    Determine the sequence of member categories within a class definition.

    Parameters
    ----------
    node : ast.ClassDef
        The AST node representing the class definition to analyze.

    Returns
    -------
    tuple[str, ...]
        A tuple of strings representing the sequence of member categories within the class.
    """

    categories: list[str] = []

    for child in node.body:

        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):

            if child.name == "__init__":

                categories.append("constructor")

            elif child.name.startswith("_"):

                categories.append("private_methods")

            else:

                categories.append("public_methods")

        elif isinstance(child, ast.Assign | ast.AnnAssign):

            categories.append("attributes")

    return tuple(dict.fromkeys(categories))


def _helper_placement(module: ast.Module) -> bool | None:
    """
    Determine if private helper functions are placed before public functions in a module.

    Parameters
    ----------
    module : ast.Module
        The AST node representing the module to analyze.

    Returns
    -------
    bool | None
        True if private helpers are before public functions, False if not, or None if the module
        does not contain both private helper functions and public functions.
    """

    private_lines = [
        node.lineno
        for node in module.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("_")
    ]

    public_lines = [
        node.lineno
        for node in module.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and not node.name.startswith("_")
    ]

    if not private_lines or not public_lines:

        return None

    return max(private_lines) < min(public_lines)


def _main_block_index(module: ast.Module) -> int | None:
    """
    Determine the index of the `if __name__ == '__main__'` block in a module, if it exists.

    Parameters
    ----------
    module : ast.Module
        The AST node representing the module to analyze.

    Returns
    -------
    int | None
        The index of the `if __name__ == '__main__'` block in the module body, or None if it does
        not exist.
    """

    for index, node in enumerate(module.body):

        if _is_main_block(node):

            return index

    return None


def _is_main_block(node: ast.stmt) -> bool:
    """
    Check if a given AST node represents an `if __name__ == '__main__'` block.

    Parameters
    ----------
    node : ast.stmt
        The AST node to check.

    Returns
    -------
    bool
        True if the node is an `if __name__ == '__main__'` block, False otherwise.
    """

    if not isinstance(node, ast.If):

        return False

    compare = node.test

    if not isinstance(compare, ast.Compare):

        return False

    left_is_name = isinstance(compare.left, ast.Name) and compare.left.id == "__name__"

    is_eq = len(compare.ops) == 1 and isinstance(compare.ops[0], ast.Eq)

    has_main = (
        len(compare.comparators) == 1
        and isinstance(compare.comparators[0], ast.Constant)
        and compare.comparators[0].value == "__main__"
    )

    return left_is_name and is_eq and has_main


def _is_type_container(node: ast.ClassDef) -> bool:
    """
    Check if a given AST node represents a type container (e.g., dataclass, TypedDict).

    Parameters
    ----------
    node : ast.ClassDef
        The AST node to check.

    Returns
    -------
    bool
        True if the node is a type container, False otherwise.
    """

    base_names = {_base_name(base) for base in node.bases}

    decorator_names = {_base_name(decorator) for decorator in node.decorator_list}

    type_markers = {"dataclass", "TypedDict", "NamedTuple", "Protocol"}

    return bool((base_names | decorator_names) & type_markers)


def _base_name(node: ast.AST) -> str:
    """
    Extract the base name from an AST node representing a type or decorator.

    Parameters
    ----------
    node : ast.AST
        The AST node to extract the base name from.

    Returns
    -------
    str
        The base name extracted from the node, or an empty string if it cannot be determined.
    """

    if isinstance(node, ast.Name):

        return node.id

    if isinstance(node, ast.Attribute):

        return node.attr

    if isinstance(node, ast.Call):

        return _base_name(node.func)

    return ""


def _is_docstring_expr(node: ast.stmt) -> bool:
    """
    Check if a given AST node is an expression containing a string constant, which is typically used
    for docstrings.

    Parameters
    ----------
    node : ast.stmt
        The AST node to check.

    Returns
    -------
    bool
        True if the node is an expression containing a string constant, False otherwise.
    """

    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _is_ordered(sequence: tuple[str, ...], order: dict[str, int]) -> bool:
    """
    Check if the given sequence of categories follows the specified order.

    Parameters
    ----------
    sequence : tuple[str, ...]
        The sequence of categories to check.
    order : dict[str, int]
        A mapping of category names to their expected order index.

    Returns
    -------
    bool
        True if the sequence follows the specified order, False otherwise.
    """

    ranks = [order[item] for item in sequence if item in order]

    return ranks == sorted(ranks)
