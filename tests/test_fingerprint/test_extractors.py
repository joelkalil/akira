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
