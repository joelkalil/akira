"""Naming convention extractor."""

from __future__ import annotations

import ast
from collections import Counter

from akira.fingerprint.extractors._common import (
    BOOLEAN_PREFIXES,
    PASCAL_CASE_RE,
    SNAKE_CASE_RE,
    UPPER_SNAKE_CASE_RE,
    make_pattern,
    modal_pattern,
)
from akira.fingerprint.models import FingerprintAnalysis, StylePattern


def extract(analysis: FingerprintAnalysis) -> tuple[StylePattern, ...]:
    """Extract naming conventions for common Python symbols."""
    names: dict[str, list[str]] = {
        "functions": [],
        "variables": [],
        "classes": [],
        "constants": [],
        "private_helpers": [],
        "boolean_prefixes": [],
    }

    for source in analysis.parsed_files:
        if source.tree is None:
            continue
        module = source.tree
        assert isinstance(module, ast.Module)

        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef):
                names["classes"].append(node.name)
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                names["functions"].append(node.name)
                if node.name.startswith("_") and not node.name.startswith("__"):
                    names["private_helpers"].append(node.name)
                names["variables"].extend(arg.arg for arg in node.args.args)
                names["variables"].extend(arg.arg for arg in node.args.kwonlyargs)
            elif isinstance(node, ast.Assign | ast.AnnAssign):
                targets = _assignment_targets(node)
                for target in targets:
                    if _is_module_level_constant(module, node, target):
                        names["constants"].append(target)
                    else:
                        names["variables"].append(target)
                    if _looks_boolean(node, target):
                        names["boolean_prefixes"].append(target)
            elif isinstance(node, ast.For | ast.AsyncFor | ast.comprehension):
                names["variables"].extend(_target_names(node.target))

    patterns: list[StylePattern] = []
    patterns.extend(_convention_pattern("functions", names["functions"]))
    patterns.extend(_convention_pattern("variables", names["variables"]))
    patterns.extend(_convention_pattern("classes", names["classes"]))
    patterns.extend(_convention_pattern("constants", names["constants"]))
    patterns.extend(_private_helper_pattern(names["private_helpers"]))
    patterns.extend(_boolean_prefix_pattern(names["boolean_prefixes"]))
    return tuple(patterns)


def _convention_pattern(category: str, values: list[str]) -> tuple[StylePattern, ...]:
    if not values:
        return ()

    conventions = [_classify_name(value, category) for value in values]
    convention, share, samples = modal_pattern(conventions)
    return (
        make_pattern(
            dimension="naming",
            name=category,
            value=convention,
            confidence=share,
            samples=samples,
            description=f"Dominant naming convention for {category.replace('_', ' ')}.",
            evidence={"distribution": dict(sorted(Counter(conventions).items()))},
        ),
    )


def _private_helper_pattern(values: list[str]) -> tuple[StylePattern, ...]:
    if not values:
        return ()

    single_underscore = sum(
        1 for value in values if value.startswith("_") and not value.startswith("__")
    )
    return (
        make_pattern(
            dimension="naming",
            name="private_helpers",
            value="single_leading_underscore",
            confidence=single_underscore / len(values),
            samples=len(values),
            description="Private helper names use a single leading underscore.",
            evidence={"examples": values[:5]},
        ),
    )


def _boolean_prefix_pattern(values: list[str]) -> tuple[StylePattern, ...]:
    if not values:
        return ()

    prefixed = [value for value in values if value.startswith(BOOLEAN_PREFIXES)]
    prefixes = [value.split("_", 1)[0] + "_" for value in prefixed]
    return (
        make_pattern(
            dimension="naming",
            name="boolean_prefixes",
            value=tuple(sorted(set(prefixes))),
            confidence=len(prefixed) / len(values),
            samples=len(values),
            description="Boolean-like names use readable predicate prefixes.",
            evidence={"observed": values[:10]},
        ),
    )


def _classify_name(name: str, category: str) -> str:
    if category == "classes" and PASCAL_CASE_RE.match(name):
        return "PascalCase"
    if category == "constants" and UPPER_SNAKE_CASE_RE.match(name):
        return "UPPER_SNAKE_CASE"
    if SNAKE_CASE_RE.match(name):
        return "snake_case"
    if PASCAL_CASE_RE.match(name):
        return "PascalCase"
    if UPPER_SNAKE_CASE_RE.match(name):
        return "UPPER_SNAKE_CASE"
    if "_" not in name and any(char.isupper() for char in name[1:]):
        return "camelCase"
    return "mixed_or_other"


def _assignment_targets(node: ast.Assign | ast.AnnAssign) -> list[str]:
    if isinstance(node, ast.AnnAssign):
        return _target_names(node.target)

    names: list[str] = []
    for target in node.targets:
        names.extend(_target_names(target))
    return names


def _target_names(target: ast.AST) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, ast.Tuple | ast.List):
        names: list[str] = []
        for element in target.elts:
            names.extend(_target_names(element))
        return names
    return []


def _is_module_level_constant(module: ast.Module, node: ast.AST, name: str) -> bool:
    return node in module.body and UPPER_SNAKE_CASE_RE.match(name) is not None


def _looks_boolean(node: ast.Assign | ast.AnnAssign, name: str) -> bool:
    value = getattr(node, "value", None)
    annotation = getattr(node, "annotation", None)
    if isinstance(value, ast.Constant) and isinstance(value.value, bool):
        return True
    if isinstance(annotation, ast.Name) and annotation.id == "bool":
        return True
    return name.startswith(BOOLEAN_PREFIXES)
