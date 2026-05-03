"""
Tests for skill installer.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Third-Party Libraries
import pytest

# Local Libraries
from akira.skills.installer import install_claude_skills, install_generated_skills

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


class TestInstallClaudeSkillsCopiesGeneratedTreeAndProjectReferences:
    """
    Verify install claude skills copies generated tree and project references cases.
    """

    def test_install_claude_skills_copies_generated_tree_and_project_references(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify install claude skills copies generated tree and project.

        references behavior.
        """

        project = tmp_path / "project"

        output = tmp_path / ".akira"

        project.mkdir()

        (output / "skills" / "python" / "testing").mkdir(parents=True)

        (output / "skills" / "SKILL.md").write_text(
            "Read ../stack.md and ../fingerprint.md",
            encoding="utf-8",
        )

        (output / "skills" / "python" / "SKILL.md").write_text(
            "python",
            encoding="utf-8",
        )

        (output / "skills" / "python" / "testing" / "pytest.md").write_text(
            "pytest",
            encoding="utf-8",
        )

        (output / "stack.md").write_text("stack", encoding="utf-8")

        (output / "fingerprint.md").write_text("fingerprint", encoding="utf-8")

        installed = install_claude_skills(project, output)

        target = project / ".claude" / "skills" / "akira"

        assert {item.status for item in installed} == {"installed"}

        assert (target / "SKILL.md").read_text(
            encoding="utf-8"
        ) == "Read stack.md and fingerprint.md"

        assert (target / "python" / "SKILL.md").read_text(encoding="utf-8") == "python"

        assert (target / "python" / "testing" / "pytest.md").read_text(
            encoding="utf-8"
        ) == "pytest"

        assert (target / "stack.md").read_text(encoding="utf-8") == "stack"

        assert (target / "fingerprint.md").read_text(encoding="utf-8") == "fingerprint"

        assert not (target / "skills" / "SKILL.md").exists()


class TestInstallClaudeSkillsIsIdempotentAndUpdatesChangedFiles:
    """
    Verify install claude skills is idempotent and updates changed files cases.
    """

    def test_install_claude_skills_is_idempotent_and_updates_changed_files(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify install claude skills is idempotent and updates changed files behavior.
        """

        project = tmp_path / "project"

        output = tmp_path / ".akira"

        project.mkdir()

        (output / "skills").mkdir(parents=True)

        (output / "skills" / "SKILL.md").write_text("first", encoding="utf-8")

        first = install_claude_skills(project, output)

        second = install_claude_skills(project, output)

        (output / "skills" / "SKILL.md").write_text("second", encoding="utf-8")

        third = install_claude_skills(project, output)

        assert [item.status for item in first] == ["installed"]

        assert [item.status for item in second] == ["unchanged"]

        assert [item.status for item in third] == ["updated"]

        assert (project / ".claude" / "skills" / "akira" / "SKILL.md").read_text(
            encoding="utf-8"
        ) == "second"


class TestInstallClaudeSkillsRemovesStaleAkiraFilesButPreservesOtherSkills:
    """
    Verify install claude skills removes stale akira files but preserves other.

    skills cases.
    """

    def test_install_claude_skills_removes_stale_akira_files_but_preserves_other_skills(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify install claude skills removes stale akira files but preserves other.

        skills behavior.
        """

        project = tmp_path / "project"

        output = tmp_path / ".akira"

        project.mkdir()

        (output / "skills").mkdir(parents=True)

        (output / "skills" / "SKILL.md").write_text("router", encoding="utf-8")

        target = project / ".claude" / "skills"

        (target / "akira" / "python" / "testing").mkdir(parents=True)

        (target / "akira" / "python" / "testing" / "old.md").write_text(
            "old",
            encoding="utf-8",
        )

        (target / "custom" / "SKILL.md").parent.mkdir(parents=True)

        (target / "custom" / "SKILL.md").write_text("custom", encoding="utf-8")

        installed = install_claude_skills(project, output)

        assert (target / "akira" / "SKILL.md").exists()

        assert not (target / "akira" / "python" / "testing" / "old.md").exists()

        assert (target / "custom" / "SKILL.md").read_text(encoding="utf-8") == "custom"

        assert any(item.status == "removed" for item in installed)


class TestInstallGeneratedSkillsRejectsTargetsOutsideProject:
    """
    Verify install generated skills rejects targets outside project cases.
    """

    def test_install_generated_skills_rejects_targets_outside_project(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify install generated skills rejects targets outside project behavior.
        """

        project = tmp_path / "project"

        outside = tmp_path / "outside"

        output = tmp_path / ".akira"

        project.mkdir()

        outside.mkdir()

        (output / "skills").mkdir(parents=True)

        (output / "skills" / "SKILL.md").write_text("router", encoding="utf-8")

        (outside / "old.md").write_text("old", encoding="utf-8")

        with pytest.raises(ValueError, match="within the project"):

            install_generated_skills(project, output, Path("..") / "outside")

        assert (outside / "old.md").read_text(encoding="utf-8") == "old"

        assert not (outside / "SKILL.md").exists()
