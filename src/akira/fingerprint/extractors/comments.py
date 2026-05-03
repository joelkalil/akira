"""
Comment style extractor.
"""

# Standard Libraries
from __future__ import annotations

import io
import re
import tokenize
from collections import Counter

# Local Libraries
from akira.fingerprint.extractors._common import make_pattern, modal_pattern
from akira.fingerprint.models import FingerprintAnalysis, StylePattern

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

SECTION_RE = re.compile(r"^#\s*[-=]{3,}\s*[^-=#].*?\s*[-=]{3,}\s*$")

TODO_AUTHOR_RE = re.compile(r"#\s*TODO\([^)]+\):\s*\S+", re.IGNORECASE)

TODO_ANY_RE = re.compile(r"#\s*TODO\b", re.IGNORECASE)

PORTUGUESE_HINTS = {
    "para",
    "quando",
    "deve",
    "nao",
    "não",
    "com",
    "sem",
    "arquivo",
    "funcao",
    "função",
}

ENGLISH_HINTS = {
    "the",
    "when",
    "with",
    "without",
    "return",
    "use",
    "file",
    "function",
    "section",
}


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def extract(analysis: FingerprintAnalysis) -> tuple[StylePattern, ...]:
    """
    Extract section, inline, language, and TODO comment preferences.

    Parameters
    ----------
    analysis : FingerprintAnalysis
        The fingerprint analysis context containing file information for extraction.

    Returns
    -------
    tuple[StylePattern, ...]
        A tuple of style patterns representing the extracted comment preferences.
    """

    comments: list[dict[str, object]] = []

    code_lines = 0

    for source in analysis.files:

        lines = source.text.splitlines()

        code_lines += sum(
            1 for line in lines if line.strip() and not line.lstrip().startswith("#")
        )

        comments.extend(_comments_for_text(source.text, lines))

    if not comments:

        return ()

    section_comments = [comment for comment in comments if comment["section"]]

    inline_comments = [comment for comment in comments if comment["inline"]]

    todos = [
        comment for comment in comments if TODO_ANY_RE.search(str(comment["text"]))
    ]

    formatted_todos = [
        comment for comment in todos if TODO_AUTHOR_RE.search(str(comment["text"]))
    ]

    languages = [_language_hint(str(comment["text"])) for comment in comments]

    language, language_share, language_samples = modal_pattern(languages)

    patterns = [
        make_pattern(
            dimension="comments",
            name="section_separators",
            value="hash_dash_section_separator",
            confidence=len(section_comments) / len(comments),
            samples=len(comments),
            description="Section separators use comments such as '# --- Section ---'.",
            evidence={"count": len(section_comments)},
        ),
        make_pattern(
            dimension="comments",
            name="inline_comment_frequency",
            value=(
                "low"
                if _inline_frequency(inline_comments, code_lines) < 0.1
                else "present"
            ),
            confidence=1.0 - min(1.0, _inline_frequency(inline_comments, code_lines)),
            samples=max(code_lines, 1),
            description=(
                "Inline comments are measured relative to executable code lines."
            ),
            evidence={
                "inline_comments": len(inline_comments),
                "code_lines": code_lines,
            },
        ),
        make_pattern(
            dimension="comments",
            name="language",
            value=language,
            confidence=language_share,
            samples=language_samples,
            description="Dominant natural-language hint in comments.",
            evidence={"distribution": dict(sorted(Counter(languages).items()))},
        ),
    ]

    if todos:

        patterns.append(
            make_pattern(
                dimension="comments",
                name="todo_format",
                value="TODO(author): description",
                confidence=len(formatted_todos) / len(todos),
                samples=len(todos),
                description="TODO comments include an owner tag and a description.",
                evidence={"todos": len(todos), "formatted": len(formatted_todos)},
            )
        )

    return tuple(patterns)


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _comments_for_text(text: str, lines: list[str]) -> list[dict[str, object]]:
    """
    Extract comment information from a source text, including section separators and.

    inline status.

    Parameters
    ----------
    text : str
        The source text from which to extract comments.
    lines : list[str]
        The lines of the source text.

    Returns
    -------
    list[dict[str, object]]
        A list of dictionaries containing comment information.
    """

    comments: list[dict[str, object]] = []

    try:

        tokens = tokenize.generate_tokens(io.StringIO(text).readline)

        for token in tokens:

            if token.type != tokenize.COMMENT:

                continue

            line = lines[token.start[0] - 1] if token.start[0] <= len(lines) else ""

            before_comment = line[: token.start[1]]

            comments.append(
                {
                    "text": token.string,
                    "inline": bool(before_comment.strip()),
                    "section": SECTION_RE.match(token.string.strip()) is not None,
                }
            )

    except tokenize.TokenError:

        return comments

    return comments


def _inline_frequency(
    inline_comments: list[dict[str, object]], code_lines: int
) -> float:
    """
    Calculate the frequency of inline comments relative to executable code lines.

    Parameters
    ----------
    inline_comments : list[dict[str, object]]
        A list of inline comment information dictionaries.
    code_lines : int
        The total number of executable code lines, used as the denominator for
        frequency calculation.

    Returns
    -------
    float
        The frequency of inline comments as a ratio of inline comments to
        executable code lines.
    """

    if code_lines <= 0:

        return 0.0

    return len(inline_comments) / code_lines


def _language_hint(comment: str) -> str:
    """
    Infer a natural language hint from a comment text, distinguishing between.

    Portuguese and English.

    Parameters
    ----------
    comment : str
        The comment text from which to infer a natural language hint, which may
        contain various
        words and punctuation.

    Returns
    -------
    str
        The inferred natural language hint ("portuguese", "english", or "unknown").
    """

    normalized = re.sub(r"[^\w\sãõáéíóúçâêôà-]", " ", comment.lower())

    words = set(normalized.split())

    portuguese_score = len(words & PORTUGUESE_HINTS)

    english_score = len(words & ENGLISH_HINTS)

    if portuguese_score > english_score:

        return "portuguese"

    if english_score > portuguese_score:

        return "english"

    return "unknown"
