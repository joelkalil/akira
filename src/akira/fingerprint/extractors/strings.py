"""String literal and interpolation style extractor."""

from __future__ import annotations

import ast
import io
import re
import tokenize
from collections import Counter

from akira.fingerprint.extractors._common import make_pattern, modal_pattern
from akira.fingerprint.models import FingerprintAnalysis, StylePattern

STRING_PREFIX_RE = re.compile(r"(?is)^[rubf]*")


def extract(analysis: FingerprintAnalysis) -> tuple[StylePattern, ...]:
    """Extract quote, f-string, and multiline string preferences."""
    quote_styles: list[str] = []
    multiline_styles: list[str] = []
    fstrings = 0
    format_calls = 0
    percent_formats = 0

    for source in analysis.files:
        file_strings = _string_tokens(source.text)
        quote_styles.extend(item["quote"] for item in file_strings if item["quote"])
        multiline_styles.extend(item["quote"] for item in file_strings if item["multiline"])

    for source in analysis.parsed_files:
        if source.tree is None:
            continue
        fstrings += sum(1 for node in ast.walk(source.tree) if isinstance(node, ast.JoinedStr))
        format_calls += sum(1 for node in ast.walk(source.tree) if _is_format_call(node))
        percent_formats += sum(1 for node in ast.walk(source.tree) if _is_percent_format(node))

    patterns: list[StylePattern] = []
    patterns.extend(_quote_style_pattern(quote_styles))
    patterns.extend(_interpolation_pattern(fstrings, format_calls, percent_formats))
    patterns.extend(_multiline_pattern(multiline_styles))
    return tuple(patterns)


def _quote_style_pattern(styles: list[str]) -> tuple[StylePattern, ...]:
    style, share, samples = modal_pattern(styles)
    if style is None:
        return ()

    return (
        make_pattern(
            dimension="strings",
            name="quote_style",
            value=style,
            confidence=share,
            samples=samples,
            description="Dominant quote character used for string literals.",
            evidence={"distribution": dict(sorted(Counter(styles).items()))},
        ),
    )


def _interpolation_pattern(
    fstrings: int,
    format_calls: int,
    percent_formats: int,
) -> tuple[StylePattern, ...]:
    total = fstrings + format_calls + percent_formats
    if not total:
        return ()

    counts = {
        "f_strings": fstrings,
        "format_calls": format_calls,
        "percent_formatting": percent_formats,
    }
    value, count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
    return (
        make_pattern(
            dimension="strings",
            name="interpolation_style",
            value=value,
            confidence=count / total,
            samples=total,
            description="Dominant string interpolation technique.",
            evidence=counts,
        ),
    )


def _multiline_pattern(styles: list[str]) -> tuple[StylePattern, ...]:
    style, share, samples = modal_pattern(styles)
    if style is None:
        return ()

    return (
        make_pattern(
            dimension="strings",
            name="multiline_strings",
            value=f"triple_{style}",
            confidence=share,
            samples=samples,
            description="Dominant quote style for multiline string literals.",
            evidence={"distribution": dict(sorted(Counter(styles).items()))},
        ),
    )


def _string_tokens(text: str) -> list[dict[str, object]]:
    strings: list[dict[str, object]] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for token in tokens:
            if token.type != tokenize.STRING:
                continue
            strings.append(_classify_string_token(token.string))
    except tokenize.TokenError:
        return strings
    return strings


def _classify_string_token(token: str) -> dict[str, object]:
    stripped = token.lstrip()
    prefix = STRING_PREFIX_RE.match(stripped)
    start = prefix.end() if prefix else 0
    literal = stripped[start:]

    if literal.startswith('"""'):
        quote = "double"
        multiline = True
    elif literal.startswith("'''"):
        quote = "single"
        multiline = True
    elif literal.startswith('"'):
        quote = "double"
        multiline = False
    elif literal.startswith("'"):
        quote = "single"
        multiline = False
    else:
        quote = ""
        multiline = False

    return {"quote": quote, "multiline": multiline}


def _is_format_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "format"
    )


def _is_percent_format(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Mod)
        and isinstance(node.left, ast.Constant)
        and isinstance(node.left.value, str)
    )
