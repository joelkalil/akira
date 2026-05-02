from __future__ import annotations

from pathlib import Path

from akira.fingerprint import extract_style_patterns, fingerprint_project
from akira.fingerprint.models import StylePattern


def test_spacing_extractor_reports_blank_line_conventions(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        '''import os
import sys


CONSTANT = 1


class Service:
    def first_method(self):
        value = 1

        return value

    def second_method(self):
        return 2


def helper_function():
    value = 3

    return value
''',
        encoding="utf-8",
    )

    patterns = _patterns_by_name(fingerprint_project(tmp_path).patterns)

    assert patterns["top_level_definitions"].value == 2
    assert patterns["top_level_definitions"].confidence == 1.0
    assert patterns["methods"].value == 1
    assert patterns["after_imports"].value == 2
    assert patterns["logical_blocks"].value == 1


def test_naming_extractor_reports_symbol_conventions(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        '''MAX_RETRIES = 3
is_enabled = True


class UserService:
    def _build_payload(self, user_name: str) -> dict[str, str]:
        has_access: bool = True
        payload_data = {"name": user_name}
        return payload_data


def load_user(user_id: str) -> str:
    should_retry = False
    return user_id
''',
        encoding="utf-8",
    )

    patterns = _patterns_by_name(fingerprint_project(tmp_path).patterns)

    assert patterns["functions"].value == "snake_case"
    assert patterns["variables"].value == "snake_case"
    assert patterns["classes"].value == "PascalCase"
    assert patterns["constants"].value == "UPPER_SNAKE_CASE"
    assert patterns["private_helpers"].value == "single_leading_underscore"
    assert "has_" in patterns["boolean_prefixes"].value
    assert "should_" in patterns["boolean_prefixes"].value


def test_import_extractor_reports_grouping_and_safety_conventions(tmp_path: Path) -> None:
    package = tmp_path / "src" / "demo"
    package.mkdir(parents=True)
    (package / "helpers.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "main.py").write_text(
        '''import os
import sys

import fastapi

from demo.helpers import VALUE
''',
        encoding="utf-8",
    )

    patterns = _patterns_by_name(fingerprint_project(tmp_path).patterns)

    assert patterns["grouping_order"].value == ("stdlib", "third_party", "local")
    assert patterns["grouping_order"].confidence == 1.0
    assert patterns["alphabetical_order"].confidence == 1.0
    assert patterns["one_import_per_line"].confidence == 1.0
    assert patterns["wildcard_usage"].value == "avoid_wildcards"
    assert patterns["relative_imports"].value == "avoid_relative_imports"


def test_comment_extractor_reports_comment_style_dimensions(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        '''# --- Public helpers ---
# TODO(joel): use the shared fixture later
def load_value():
    value = 1
    return value  # return the stable value
''',
        encoding="utf-8",
    )

    patterns = _patterns_by_name(fingerprint_project(tmp_path).patterns)

    assert patterns["section_separators"].value == "hash_dash_section_separator"
    assert patterns["section_separators"].confidence > 0
    assert patterns["inline_comment_frequency"].value == "present"
    assert patterns["language"].value == "english"
    assert patterns["todo_format"].confidence == 1.0


def test_typing_extractor_reports_signature_and_optional_conventions(
    tmp_path: Path,
) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        '''from __future__ import annotations

from typing import Iterable, Mapping


def load_user(user_id: str, tags: Iterable[str] | None = None) -> Mapping[str, str]:
    return {"id": user_id, "tags": ",".join(tags or [])}


def _coerce_name(value: str | None) -> str:
    return value or "anonymous"
''',
        encoding="utf-8",
    )

    patterns = _patterns_by_name(fingerprint_project(tmp_path).patterns)

    assert patterns["signature_coverage"].value == "full_signature_hints"
    assert patterns["signature_coverage"].confidence == 1.0
    assert patterns["return_hints"].confidence == 1.0
    assert patterns["optional_syntax"].value == "pipe_union_none"
    assert patterns["complex_type_imports"].value == ("Iterable", "Mapping")


def test_structure_extractor_reports_control_flow_shape(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        '''def classify(value: int) -> str:
    if value < 0:
        return "negative"
    if value == 0:
        return "zero"

    label = "large" if value > 10 else "small"
    return label


def nested(items: list[int]) -> int:
    total = 0
    for item in items:
        if item > 0:
            total += item
    return total
''',
        encoding="utf-8",
    )

    patterns = _patterns_by_name(fingerprint_project(tmp_path).patterns)

    assert patterns["early_returns"].value == "occasional"
    assert patterns["early_returns"].confidence == 0.5
    assert patterns["guard_clauses"].value == "occasional"
    assert patterns["nesting_depth"].value in {1, 2}
    assert patterns["ternary_usage"].value == "uses_ternary"
    assert patterns["function_length"].value == "under_30_lines"


def test_structure_extractor_ignores_nested_scopes_for_outer_function_shape(
    tmp_path: Path,
) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        '''def outer(flag: bool) -> int:
    def inner() -> int:
        if flag:
            if not flag:
                return 1
            return 2
        return 3

    return inner()
''',
        encoding="utf-8",
    )

    patterns = _patterns_by_name(fingerprint_project(tmp_path).patterns)

    assert patterns["early_returns"].confidence == 0.5
    assert patterns["nesting_depth"].evidence["distribution"] == {0: 1, 2: 1}


def test_ternary_confidence_counts_functions_not_expressions(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        '''def with_ternaries(first: bool, second: bool) -> tuple[str, str]:
    left = "yes" if first else "no"
    right = "up" if second else "down"
    return left, right


def without_ternary() -> str:
    return "plain"
''',
        encoding="utf-8",
    )

    patterns = _patterns_by_name(fingerprint_project(tmp_path).patterns)

    assert patterns["ternary_usage"].value == "uses_ternary"
    assert patterns["ternary_usage"].confidence == 0.5
    assert patterns["ternary_usage"].evidence == {
        "ternary_expressions": 2,
        "functions_with_ternary": 1,
    }


def test_docstring_extractor_reports_style_and_visibility(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        '''class Service:
    """Load user-facing values.

    Args:
        source: Source name.
    """

    def public_method(self, source: str) -> str:
        """Return a normalized value.

        Args:
            source: Source name.

        Returns:
            Normalized source.
        """
        return source.lower()

    def _private_method(self) -> None:
        return None
''',
        encoding="utf-8",
    )

    patterns = _patterns_by_name(fingerprint_project(tmp_path).patterns)

    assert patterns["public_docstrings"].value == "documented"
    assert patterns["public_docstrings"].confidence == 1.0
    assert patterns["private_docstring_behavior"].value == "omit_private_docstrings"
    assert patterns["docstring_style"].value == "google"
    assert patterns["class_docstrings"].confidence == 1.0


def test_organization_extractor_reports_module_and_class_order(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        '''"""Example module."""

import os

MAX_RETRIES = 3


class Payload(dict):
    pass


def _coerce(value: str) -> str:
    return value.strip()


def load(value: str) -> str:
    return _coerce(value)


class Service:
    timeout = 5

    def __init__(self) -> None:
        self.ready = True

    def run(self) -> None:
        return None

    def _reset(self) -> None:
        self.ready = False


if __name__ == "__main__":
    print(load(" demo "))
''',
        encoding="utf-8",
    )

    patterns = _patterns_by_name(fingerprint_project(tmp_path).patterns)

    assert patterns["module_order"].value == (
        "module_docstring",
        "imports",
        "constants",
        "classes",
        "private_helpers",
        "public_functions",
        "main_block",
    )
    assert patterns["helper_placement"].confidence == 1.0
    assert patterns["class_member_order"].value == (
        "attributes",
        "constructor",
        "public_methods",
        "private_methods",
    )
    assert patterns["main_block"].confidence == 1.0


def test_organization_extractor_only_treats_eq_main_compare_as_main_guard(
    tmp_path: Path,
) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        '''def load() -> str:
    return "ok"


if __name__ != "__main__":
    load()
''',
        encoding="utf-8",
    )

    patterns = _patterns_by_name(fingerprint_project(tmp_path).patterns)

    assert "main_block" not in patterns
    assert patterns["module_order"].value == ("public_functions",)


def test_error_and_string_extractors_report_idioms(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        '''import logging

LOGGER = logging.getLogger(__name__)


def render(name: str) -> str:
    message = f"Hello {name}"
    template = """User:
{name}
"""
    return message + template


def load(path: str) -> str:
    try:
        return open(path, encoding="utf-8").read()
    except FileNotFoundError:
        LOGGER.exception("Could not load %s", path)
        raise
''',
        encoding="utf-8",
    )

    patterns = _patterns_by_name(fingerprint_project(tmp_path).patterns)

    assert patterns["exception_specificity"].confidence == 1.0
    assert patterns["logging_on_catch"].confidence == 1.0
    assert patterns["reraising"].confidence == 1.0
    assert patterns["quote_style"].value == "double"
    assert patterns["interpolation_style"].value == "f_strings"
    assert patterns["multiline_strings"].value == "triple_double"


def test_new_extractors_tolerate_files_with_missing_ast(tmp_path: Path) -> None:
    (tmp_path / "valid.py").write_text(
        '''def load(value: str | None) -> str:
    if value is None:
        return "fallback"
    return value
''',
        encoding="utf-8",
    )
    (tmp_path / "broken.py").write_text("def broken(:\n    pass\n", encoding="utf-8")

    analysis = fingerprint_project(tmp_path)
    patterns = _patterns_by_name(analysis.patterns)

    assert analysis.failed_files
    assert patterns["signature_coverage"].value == "full_signature_hints"
    assert patterns["early_returns"].confidence == 1.0


def test_confidence_decreases_for_intentionally_mixed_style(tmp_path: Path) -> None:
    consistent = tmp_path / "consistent"
    mixed = tmp_path / "mixed"
    consistent.mkdir()
    mixed.mkdir()

    (consistent / "module.py").write_text(
        '''import os


def first_function():
    return 1


def second_function():
    return 2
''',
        encoding="utf-8",
    )
    (mixed / "module.py").write_text(
        '''import os


def first_function():
    return 1

def secondFunction():
    return 2
''',
        encoding="utf-8",
    )

    consistent_patterns = _patterns_by_name(fingerprint_project(consistent).patterns)
    mixed_patterns = _patterns_by_name(fingerprint_project(mixed).patterns)

    assert mixed_patterns["top_level_definitions"].confidence < consistent_patterns[
        "top_level_definitions"
    ].confidence
    assert mixed_patterns["functions"].confidence < consistent_patterns[
        "functions"
    ].confidence


def test_extract_style_patterns_is_deterministic(tmp_path: Path) -> None:
    (tmp_path / "module.py").write_text(
        '''import os


VALUE = 1


def load_value():
    return VALUE
''',
        encoding="utf-8",
    )

    first = fingerprint_project(tmp_path)
    second = fingerprint_project(tmp_path)

    assert extract_style_patterns(first) == extract_style_patterns(second)
    assert first.patterns == second.patterns


def _patterns_by_name(patterns: tuple[StylePattern, ...]) -> dict[str, StylePattern]:
    return {pattern.name: pattern for pattern in patterns}
