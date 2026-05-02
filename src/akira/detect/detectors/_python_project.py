"""Helpers for reading Python project metadata and source imports."""

from __future__ import annotations

import ast
import configparser
import re
from pathlib import Path
from typing import Any, Iterable

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "venv",
}

REQUIREMENT_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9_.-]+)"
    r"(?:\[[^\]]+\])?"
    r"\s*(?P<specifier>(?:===|==|~=|!=|<=|>=|<|>).*)?$"
)


def read_toml(path: Path) -> dict[str, Any]:
    """Read TOML, returning an empty mapping when the file is missing."""
    if not path.exists():
        return {}

    import tomllib

    with path.open("rb") as file:
        return tomllib.load(file)


def read_setup_cfg(path: Path) -> configparser.ConfigParser:
    """Read setup.cfg-style configuration."""
    parser = configparser.ConfigParser()
    if path.exists():
        parser.read(path, encoding="utf-8")

    return parser


def normalize_package_name(name: str) -> str:
    """Normalize a Python package name according to dependency matching needs."""
    return name.strip().lower().replace("_", "-")


def package_to_import_name(name: str) -> str:
    """Return the import-style variant of a package name."""
    return normalize_package_name(name).replace("-", "_")


def parse_requirement(requirement: str) -> tuple[str, str | None] | None:
    """Parse a single PEP 508-ish requirement line into package and specifier."""
    line = requirement.split("#", 1)[0].strip()
    if not line or line.startswith(("-", "git+", "http://", "https://")):
        return None

    line = line.split(";", 1)[0].strip()
    match = REQUIREMENT_RE.match(line)
    if not match:
        return None

    name = normalize_package_name(match.group("name"))
    specifier = match.group("specifier")
    version = extract_pinned_version(specifier)
    return name, version


def extract_pinned_version(specifier: str | None) -> str | None:
    """Extract a pinned version from a requirement specifier when present."""
    if not specifier:
        return None

    match = re.search(r"(?:===|==)\s*([A-Za-z0-9_.!+*-]+)", specifier)
    return match.group(1) if match else None


def extract_dependencies(project_root: Path) -> dict[str, str | None]:
    """Collect dependencies from pyproject, setup files, and requirements files."""
    dependencies: dict[str, str | None] = {}

    for requirement in _dependencies_from_pyproject(project_root / "pyproject.toml"):
        _add_requirement(dependencies, requirement)

    for requirement in _dependencies_from_setup_cfg(project_root / "setup.cfg"):
        _add_requirement(dependencies, requirement)

    for requirement in _dependencies_from_setup_py(project_root / "setup.py"):
        _add_requirement(dependencies, requirement)

    for requirements_file in sorted(project_root.glob("requirements*.txt")):
        for requirement in requirements_file.read_text(encoding="utf-8").splitlines():
            _add_requirement(dependencies, requirement)

    return dependencies


def scan_imports(project_root: Path) -> set[str]:
    """Return top-level imported module names from project Python files."""
    imports: set[str] = set()

    for path in iter_python_files(project_root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".", 1)[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".", 1)[0])

    return imports


def iter_python_files(project_root: Path) -> Iterable[Path]:
    """Yield Python files while skipping virtualenvs, caches, and build output."""
    for path in project_root.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(project_root).parts):
            continue

        yield path


def _dependencies_from_pyproject(path: Path) -> list[str]:
    data = read_toml(path)
    if not data:
        return []

    dependencies: list[str] = []
    project = data.get("project", {})
    dependencies.extend(_string_items(project.get("dependencies", [])))

    optional_dependencies = project.get("optional-dependencies", {})
    if isinstance(optional_dependencies, dict):
        for values in optional_dependencies.values():
            dependencies.extend(_string_items(values))

    dependency_groups = data.get("dependency-groups", {})
    if isinstance(dependency_groups, dict):
        for values in dependency_groups.values():
            dependencies.extend(_string_items(values))

    uv = data.get("tool", {}).get("uv", {})
    if isinstance(uv, dict):
        uv_dev_dependencies = uv.get("dev-dependencies", [])
        dependencies.extend(_string_items(uv_dev_dependencies))
        uv_dependency_groups = uv.get("dependency-groups", {})
        if isinstance(uv_dependency_groups, dict):
            for group in uv_dependency_groups.values():
                dependencies.extend(_string_items(group))

    poetry = data.get("tool", {}).get("poetry", {})
    for name, specifier in poetry.get("dependencies", {}).items():
        if name.lower() == "python":
            continue
        dependencies.append(_poetry_dependency_to_requirement(name, specifier))

    for name, specifier in poetry.get("group", {}).get("dev", {}).get(
        "dependencies", {}
    ).items():
        dependencies.append(_poetry_dependency_to_requirement(name, specifier))

    return dependencies


def _dependencies_from_setup_cfg(path: Path) -> list[str]:
    parser = read_setup_cfg(path)
    if not parser.has_section("options"):
        return []

    raw = parser.get("options", "install_requires", fallback="")
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _dependencies_from_setup_py(path: Path) -> list[str]:
    if not path.exists():
        return []

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    dependencies: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function_name = getattr(node.func, "id", "")
        attr_name = getattr(node.func, "attr", "")
        if function_name != "setup" and attr_name != "setup":
            continue
        for keyword in node.keywords:
            if keyword.arg == "install_requires":
                try:
                    value = ast.literal_eval(keyword.value)
                except (ValueError, TypeError):
                    continue
                if isinstance(value, list):
                    dependencies.extend(item for item in value if isinstance(item, str))

    return dependencies


def _poetry_dependency_to_requirement(name: str, specifier: object) -> str:
    if isinstance(specifier, str):
        return f"{name}{specifier if specifier.startswith(('=', '<', '>', '~', '!')) else ''}"
    if isinstance(specifier, dict):
        version = specifier.get("version")
        if isinstance(version, str):
            return f"{name}{version if version.startswith(('=', '<', '>', '~', '!')) else ''}"

    return name


def _string_items(value: object) -> list[str]:
    """Return only string dependency entries from a pyproject sequence."""
    if not isinstance(value, list):
        return []

    return [item for item in value if isinstance(item, str)]


def _add_requirement(dependencies: dict[str, str | None], requirement: str) -> None:
    parsed = parse_requirement(requirement)
    if parsed is None:
        return

    name, version = parsed
    existing_version = dependencies.get(name)
    if name not in dependencies or (existing_version is None and version is not None):
        dependencies[name] = version
