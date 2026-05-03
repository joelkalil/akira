"""
Error-handling style extractor.
"""

# Standard Libraries
from __future__ import annotations

import ast

# Local Libraries
from akira.fingerprint.extractors._common import make_pattern
from akira.fingerprint.models import FingerprintAnalysis, StylePattern

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

GENERIC_EXCEPTIONS = {"BaseException", "Exception"}

LOG_METHODS = {"debug", "info", "warning", "warn", "error", "exception", "critical"}


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def extract(analysis: FingerprintAnalysis) -> tuple[StylePattern, ...]:
    """
    Extract exception specificity and logging behavior in except handlers.

    Parameters
    ----------
    analysis : FingerprintAnalysis
        The analysis context containing parsed files and other relevant information.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple of StylePattern instances representing the extracted
        error-handling patterns.
    """

    handlers: list[ast.ExceptHandler] = []

    for source in analysis.parsed_files:

        if source.tree is not None:

            handlers.extend(
                node
                for node in ast.walk(source.tree)
                if isinstance(node, ast.ExceptHandler)
            )

    if not handlers:

        return ()

    specific = sum(1 for handler in handlers if _is_specific_exception(handler))

    logged = sum(1 for handler in handlers if _logs_on_catch(handler))

    reraised = sum(1 for handler in handlers if _reraises(handler))

    return (
        make_pattern(
            dimension="error_handling",
            name="exception_specificity",
            value="specific_exceptions",
            confidence=specific / len(handlers),
            samples=len(handlers),
            description=(
                "Except handlers avoid bare except and generic Exception catches."
            ),
            evidence={"specific": specific, "handlers": len(handlers)},
        ),
        make_pattern(
            dimension="error_handling",
            name="logging_on_catch",
            value="logs_caught_exceptions",
            confidence=logged / len(handlers),
            samples=len(handlers),
            description="Except handlers log caught exceptions.",
            evidence={"logged": logged, "handlers": len(handlers)},
        ),
        make_pattern(
            dimension="error_handling",
            name="reraising",
            value="reraises_after_catch",
            confidence=reraised / len(handlers),
            samples=len(handlers),
            description="Except handlers re-raise after local handling.",
            evidence={"reraised": reraised, "handlers": len(handlers)},
        ),
    )


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _is_specific_exception(handler: ast.ExceptHandler) -> bool:
    """
    Determine if an except handler catches specific exceptions rather than using a.

    bare except or.

    generic Exception.

    Parameters
    ----------
    handler : ast.ExceptHandler
        The except handler node to analyze.

    Returns
    -------
    bool
        True if the handler catches specific exceptions, False if it uses a bare
        except or generic
        Exception.
    """

    if handler.type is None:

        return False

    names = _exception_names(handler.type)

    return bool(names) and all(name not in GENERIC_EXCEPTIONS for name in names)


def _exception_names(node: ast.AST) -> list[str]:
    """
    Recursively extract exception names from an AST node representing an exception.

    type in an except.

    handler.

    Parameters
    ----------
    node : ast.AST
        The AST node to extract exception names from.

    Returns
    -------
    list[str]
        A list of exception names extracted from the node.
    """

    if isinstance(node, ast.Name):

        return [node.id]

    if isinstance(node, ast.Attribute):

        return [node.attr]

    if isinstance(node, ast.Tuple):

        names: list[str] = []

        for element in node.elts:

            names.extend(_exception_names(element))

        return names

    return []


def _logs_on_catch(handler: ast.ExceptHandler) -> bool:
    """
    Determine if an except handler logs caught exceptions by checking for calls to.

    logging methods.

    within the handler body.

    Parameters
    ----------
    handler : ast.ExceptHandler
        The except handler node to analyze.

    Returns
    -------
    bool
        True if the handler logs caught exceptions, False otherwise.
    """

    for node in ast.walk(handler):

        if not isinstance(node, ast.Call):

            continue

        function = node.func

        if isinstance(function, ast.Attribute) and function.attr in LOG_METHODS:

            return True

    return False


def _reraises(handler: ast.ExceptHandler) -> bool:
    """
    Determine if an except handler re-raises exceptions after local handling by.

    checking for raise.

    statements within the handler body.

    Parameters
    ----------
    handler : ast.ExceptHandler
        The except handler node to analyze.

    Returns
    -------
    bool
        True if the handler re-raises exceptions, False otherwise.
    """

    return any(isinstance(node, ast.Raise) for node in ast.walk(handler))
