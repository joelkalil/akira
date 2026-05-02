from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from akira.fingerprint import fingerprint_project, render_fingerprint_markdown


def test_render_fingerprint_markdown_includes_frontmatter_and_v1_sections(
    tmp_path: Path,
) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        '''# --- Public helpers ---
import os


MAX_RETRIES = 3


class UserService:
    """Load users.

    Args:
        source: Source name.
    """

    def _build_payload(self, user_name: str | None) -> dict[str, str]:
        if user_name is None:
            return {"name": "anonymous"}
        return {"name": f"{user_name}"}


def load_user(user_id: str) -> str:
    return user_id
''',
        encoding="utf-8",
    )

    analysis = fingerprint_project(tmp_path)
    content = render_fingerprint_markdown(
        analysis,
        generated_at=datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc),
        sample_size=20,
    )

    assert 'generated_at: "2026-05-02T12:00:00+00:00"' in content
    assert "sample_size: 20" in content
    assert '  - "module.py"' in content
    assert "confidence:" in content
    assert "- **Between top-level definitions**: 2 blank lines" in content
    assert "- **Classes**: PascalCase" in content
    assert "- **Optional style**: `X | None`" in content

    for section in (
        "Spacing",
        "Comments",
        "Control Flow",
        "Naming",
        "Imports",
        "Type Hints",
        "Docstrings",
        "Error Handling",
        "Organization",
        "Strings",
        "General Patterns",
    ):
        assert f"## {section}" in content
