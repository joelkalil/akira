"""Install generated Akira skills into agent-specific skill directories."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


InstallStatus = Literal["installed", "updated", "unchanged", "removed"]


@dataclass(frozen=True)
class InstalledSkillFile:
    """A file touched while installing generated skills."""

    path: Path
    status: InstallStatus


class ClaudeSkillInstaller:
    """Install generated Akira skills for Claude Code."""

    target_relative_dir = Path(".claude") / "skills" / "akira"

    def install(self, project_root: Path, output_dir: Path) -> tuple[InstalledSkillFile, ...]:
        """Copy generated Akira output into project_root/.claude/skills/akira."""
        source_files = _generated_source_files(output_dir)
        target_dir = project_root / self.target_relative_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        results: list[InstalledSkillFile] = []
        desired_paths = set(source_files)

        for relative_path, source_path in sorted(
            source_files.items(),
            key=lambda item: item[0].as_posix(),
        ):
            target_path = target_dir / relative_path
            status = _copy_file(source_path, target_path, relative_path)
            results.append(InstalledSkillFile(target_path, status))

        for stale_path in _stale_installed_files(target_dir, desired_paths):
            stale_path.unlink()
            results.append(InstalledSkillFile(stale_path, "removed"))

        _remove_empty_directories(target_dir)
        return tuple(results)


def install_claude_skills(
    project_root: Path,
    output_dir: Path,
) -> tuple[InstalledSkillFile, ...]:
    """Install generated Akira skills into Claude Code's project skill directory."""
    return ClaudeSkillInstaller().install(project_root, output_dir)


def _generated_source_files(output_dir: Path) -> dict[Path, Path]:
    files: dict[Path, Path] = {}
    skills_dir = output_dir / "skills"

    if skills_dir.exists():
        for path in skills_dir.rglob("*"):
            if path.is_file():
                files[path.relative_to(skills_dir)] = path

    for filename in ("stack.md", "fingerprint.md"):
        path = output_dir / filename
        if path.is_file():
            files[Path(filename)] = path

    return files


def _copy_file(
    source_path: Path,
    target_path: Path,
    relative_path: Path,
) -> InstallStatus:
    content = source_path.read_bytes()
    if relative_path == Path("SKILL.md"):
        content = _rewrite_router_references_for_install(content)

    if target_path.exists():
        if target_path.read_bytes() == content:
            return "unchanged"
        status: InstallStatus = "updated"
    else:
        status = "installed"

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(content)
    return status


def _rewrite_router_references_for_install(content: bytes) -> bytes:
    return (
        content.replace(b"../stack.md", b"stack.md")
        .replace(b"../fingerprint.md", b"fingerprint.md")
    )


def _stale_installed_files(target_dir: Path, desired_paths: set[Path]) -> tuple[Path, ...]:
    if not target_dir.exists():
        return ()

    return tuple(
        sorted(
            (
                path
                for path in target_dir.rglob("*")
                if path.is_file() and path.relative_to(target_dir) not in desired_paths
            ),
            key=lambda path: path.as_posix(),
        )
    )


def _remove_empty_directories(target_dir: Path) -> None:
    directories = sorted(
        (path for path in target_dir.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in directories:
        try:
            directory.rmdir()
        except OSError:
            continue
