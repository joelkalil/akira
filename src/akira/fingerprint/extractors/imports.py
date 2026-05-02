"""Import style extractor."""

from __future__ import annotations

import ast
import sys
from collections import Counter, defaultdict

from akira.fingerprint.extractors._common import make_pattern, module_name_from_path
from akira.fingerprint.models import FingerprintAnalysis, SourceFile, StylePattern

GROUP_ORDER = {"stdlib": 0, "third_party": 1, "local": 2}


def extract(analysis: FingerprintAnalysis) -> tuple[StylePattern, ...]:
    """Extract import grouping, ordering, and import statement preferences."""
    local_roots = {
        module_name_from_path(source.relative_path)
        for source in analysis.parsed_files
        if module_name_from_path(source.relative_path)
    }
    imports_by_file = [_file_imports(source, local_roots) for source in analysis.parsed_files]
    non_empty = [imports for imports in imports_by_file if imports]
    if not non_empty:
        return ()

    all_imports = [item for imports in non_empty for item in imports]
    ordered_files = sum(1 for imports in non_empty if _groups_are_ordered(imports))
    alphabetized_files = sum(1 for imports in non_empty if _imports_are_alphabetized(imports))
    one_per_line = sum(1 for item in all_imports if item["one_per_line"])
    no_wildcards = sum(1 for item in all_imports if not item["wildcard"])
    no_relative = sum(1 for item in all_imports if not item["relative"])
    group_sequences = [tuple(dict.fromkeys(item["group"] for item in imports)) for imports in non_empty]
    sequence_counts = Counter(group_sequences)
    dominant_sequence = sorted(
        sequence_counts.items(), key=lambda item: (-item[1], item[0])
    )[0][0]

    return (
        make_pattern(
            dimension="imports",
            name="grouping_order",
            value=dominant_sequence,
            confidence=ordered_files / len(non_empty),
            samples=len(non_empty),
            description="Import groups follow a stable stdlib, third-party, local order.",
            evidence={"sequences": {" > ".join(key): count for key, count in sequence_counts.items()}},
        ),
        make_pattern(
            dimension="imports",
            name="alphabetical_order",
            value="alphabetical_within_groups",
            confidence=alphabetized_files / len(non_empty),
            samples=len(non_empty),
            description="Imports are alphabetized within their import groups.",
        ),
        make_pattern(
            dimension="imports",
            name="one_import_per_line",
            value=True,
            confidence=one_per_line / len(all_imports),
            samples=len(all_imports),
            description="Import statements avoid comma-packed imports.",
        ),
        make_pattern(
            dimension="imports",
            name="wildcard_usage",
            value="avoid_wildcards",
            confidence=no_wildcards / len(all_imports),
            samples=len(all_imports),
            description="Wildcard imports are avoided.",
        ),
        make_pattern(
            dimension="imports",
            name="relative_imports",
            value="avoid_relative_imports",
            confidence=no_relative / len(all_imports),
            samples=len(all_imports),
            description="Imports prefer absolute module paths over relative imports.",
        ),
    )


def _file_imports(source: SourceFile, local_roots: set[str]) -> list[dict[str, object]]:
    if source.tree is None:
        return []

    module = source.tree
    assert isinstance(module, ast.Module)
    imports: list[dict[str, object]] = []
    for node in ast.walk(module):
        if not isinstance(node, ast.Import | ast.ImportFrom):
            continue

        module_name = _imported_module_name(node)
        imports.append(
            {
                "line": node.lineno,
                "name": module_name,
                "group": _classify_import(node, module_name, local_roots),
                "one_per_line": len(node.names) == 1,
                "wildcard": any(alias.name == "*" for alias in node.names),
                "relative": isinstance(node, ast.ImportFrom) and node.level > 0,
            }
        )

    return sorted(imports, key=lambda item: (int(item["line"]), str(item["name"])))


def _imported_module_name(node: ast.Import | ast.ImportFrom) -> str:
    if isinstance(node, ast.Import):
        return node.names[0].name
    dots = "." * node.level
    return f"{dots}{node.module or ''}"


def _classify_import(
    node: ast.Import | ast.ImportFrom,
    module_name: str,
    local_roots: set[str],
) -> str:
    if isinstance(node, ast.ImportFrom) and node.level > 0:
        return "local"

    root = module_name.split(".", 1)[0]
    if root in local_roots:
        return "local"
    if root in sys.stdlib_module_names or root == "__future__":
        return "stdlib"
    return "third_party"


def _groups_are_ordered(imports: list[dict[str, object]]) -> bool:
    ranks = [GROUP_ORDER[str(item["group"])] for item in imports]
    return ranks == sorted(ranks)


def _imports_are_alphabetized(imports: list[dict[str, object]]) -> bool:
    by_group: dict[str, list[str]] = defaultdict(list)
    for item in imports:
        by_group[str(item["group"])].append(str(item["name"]).lstrip("."))

    return all(names == sorted(names, key=str.lower) for names in by_group.values())
