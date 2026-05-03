"""
Helpers for reading Python project metadata and source imports.
"""

# Standard Libraries
from __future__ import annotations

import ast
import configparser
import re
import tomllib
from pathlib import Path
from typing import Any, Iterable

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

EXCLUDED_DIRS = frozenset(
    {
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
        "fixtures",
    }
)

REQUIREMENT_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9_.-]+)"
    r"(?:\[[^\]]+\])?"
    r"\s*(?P<specifier>(?:===|==|~=|!=|<=|>=|<|>).*)?$"
)


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


def read_toml(path: Path) -> dict[str, Any]:
    """
    Read TOML, returning an empty mapping when the file is missing.

    Parameters
    ----------
    path : Path
        Path to the TOML file to read.

    Returns
    -------
    dict[str, Any]
        Parsed TOML data as a dictionary, or an empty dictionary if the file is missing.
    """

    if not path.exists():
        return {}

    with path.open("rb") as file:
        return tomllib.load(file)


def read_setup_cfg(path: Path) -> configparser.ConfigParser:
    """
    Read setup.cfg-style configuration.

    Parameters
    ----------
    path : Path
        Path to the setup.cfg file to read.

    Returns
    -------
    configparser.ConfigParser
        A ConfigParser object containing the parsed configuration, or an empty
        ConfigParser if the file is missing.
    """

    parser = configparser.ConfigParser()

    if path.exists():
        parser.read(path, encoding="utf-8")

    return parser


def normalize_package_name(name: str) -> str:
    """
    Normalize a Python package name according to dependency matching needs.

    Parameters
    ----------
    name : str
        The original package name to normalize.

    Returns
    -------
    str
        The normalized package name, with leading/trailing whitespace removed, converted
        to lowercase, and with underscores replaced by hyphens.
    """

    return name.strip().lower().replace("_", "-")


def package_to_import_name(name: str) -> str:
    """
    Return the import-style variant of a package name.

    Parameters
    ----------
    name : str
        The original package name to convert.

    Returns
    -------
    str
        The import-style package name, with hyphens replaced by underscores.
    """

    return normalize_package_name(name).replace("-", "_")


def parse_requirement(requirement: str) -> tuple[str, str | None] | None:
    """
    Parse a single PEP 508-ish requirement line into package and specifier.

    Parameters
    ----------
    requirement : str
        A single requirement line, such as "requests>=2.0" or "numpy==1.21.0".

    Returns
    -------
    tuple[str, str | None] | None
        A tuple of (normalized package name, pinned version or None), or None if the
        line is not a valid requirement.
    """

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
    """
    Extract a pinned version from a requirement specifier when present.

    Parameters
    ----------
    specifier : str | None
        A requirement specifier string, such as ">=2.0" or "==1.21.0", or None.

    Returns
    -------
    str | None
        The pinned version if the specifier is an exact match (e.g., "==1.21.0"), or
        None otherwise.
    """

    if not specifier:
        return None

    match = re.search(r"(?:===|==)\s*([A-Za-z0-9_.!+*-]+)", specifier)

    return match.group(1) if match else None


def extract_dependencies(project_root: Path) -> dict[str, str | None]:
    """
    Collect dependencies from pyproject, setup files, and requirements files.

    Parameters
    ----------
    project_root : Path
        The root directory of the Python project to analyze.

    Returns
    -------
    dict[str, str | None]
        A mapping of normalized package names to pinned versions (or None if not
        pinned).
    """

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


def scan_imports(
    project_root: Path,
    exclude_dirs: frozenset[str] = EXCLUDED_DIRS,
) -> set[str]:
    """
    Return top-level imported module names from project Python files.

    Parameters
    ----------
    project_root : Path
        The root directory of the Python project to analyze.
    exclude_dirs : frozenset[str]
        Directory names or relative paths to skip when scanning Python files.

    Returns
    -------
    set[str]
        A set of top-level module names imported in the project's Python source files.
    """

    imports: set[str] = set()

    for path in iter_python_files(project_root, exclude_dirs=exclude_dirs):
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


def iter_python_files(
    project_root: Path,
    exclude_dirs: frozenset[str] = EXCLUDED_DIRS,
) -> Iterable[Path]:
    """
    Yield Python files while skipping virtualenvs, caches, and build output.

    Parameters
    ----------
    project_root : Path
        The root directory of the Python project to analyze.
    exclude_dirs : frozenset[str]
        Directory names or relative paths to skip when walking the project.

    Yields
    ------
    Iterable[Path]
        Paths to Python source files within the project, excluding those in common
        excluded directories.
    """

    for path in project_root.rglob("*.py"):
        if _is_excluded_python_path(path, project_root, exclude_dirs):
            continue

        yield path


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _is_excluded_python_path(
    path: Path,
    project_root: Path,
    exclude_dirs: frozenset[str],
) -> bool:
    """
    Return whether a Python file lives under an excluded directory.

    Parameters
    ----------
    path : Path
        The path value.
    project_root : Path
        The project root value.
    exclude_dirs : frozenset[str]
        The exclude dirs value.

    Returns
    -------
    bool
        The result of the operation.
    """

    relative_parts = path.relative_to(project_root).parts
    directory_parts = relative_parts[:-1]
    directory_paths = {
        Path(*directory_parts[: index + 1]).as_posix()
        for index in range(len(directory_parts))
    }

    return any(
        excluded in directory_parts or excluded in directory_paths
        for excluded in exclude_dirs
    )


def _dependencies_from_pyproject(path: Path) -> list[str]:
    """
    Extract dependencies from a pyproject.toml file, handling various formats and tools.

    Parameters
    ----------
    path : Path
        Path to the pyproject.toml file to read.

    Returns
    -------
    list[str]
        A list of dependency requirement strings extracted from the pyproject.toml file,
        including those from standard sections and tool-specific configurations.
    """

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

    for name, specifier in (
        poetry.get("group", {}).get("dev", {}).get("dependencies", {}).items()
    ):
        dependencies.append(_poetry_dependency_to_requirement(name, specifier))

    return dependencies


def _dependencies_from_setup_cfg(path: Path) -> list[str]:
    """
    Extract dependencies from a setup.cfg file's install_requires field.

    Parameters
    ----------
    path : Path
        Path to the setup.cfg file to read.

    Returns
    -------
    list[str]
        A list of dependency requirement strings extracted from the install_requires
        field of the setup.cfg file.
    """

    parser = read_setup_cfg(path)

    if not parser.has_section("options"):
        return []

    raw = parser.get("options", "install_requires", fallback="")

    return [line.strip() for line in raw.splitlines() if line.strip()]


def _dependencies_from_setup_py(path: Path) -> list[str]:
    """
    Extract dependencies from a setup.py file by parsing its AST for install_requires.

    Parameters
    ----------
    path : Path
        Path to the setup.py file to read.

    Returns
    -------
    list[str]
        A list of dependency requirement strings extracted from the install_requires
        argument in the setup.py file.
    """

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
    """
    Convert a Poetry dependency entry to a standard requirement string.

    Parameters
    ----------
    name : str
        The name of the dependency package.
    specifier : object
        The version specifier for the dependency, which can be a string or a dictionary.

    Returns
    -------
    str
        A requirement string combining the package name and version specifier, if
        applicable.
    """

    if isinstance(specifier, str):
        normalized = (
            specifier if specifier.startswith(("=", "<", ">", "~", "!")) else ""
        )

        return f"{name}{normalized}"

    if isinstance(specifier, dict):
        version = specifier.get("version")

        if isinstance(version, str):
            normalized = (
                version if version.startswith(("=", "<", ">", "~", "!")) else ""
            )

            return f"{name}{normalized}"

    return name


def _string_items(value: object) -> list[str]:
    """
    Return only string dependency entries from a pyproject sequence.

    Parameters
    ----------
    value : object
        The value to filter, expected to be a list of dependency entries from a
        pyproject.toml section.

    Returns
    -------
    list[str]
        A list of string items extracted from the input value, or an empty list if the
        input is not a list.
    """

    if not isinstance(value, list):
        return []

    return [item for item in value if isinstance(item, str)]


def _add_requirement(dependencies: dict[str, str | None], requirement: str) -> None:
    """
    Parse a requirement string and add it to the dependencies mapping if it's not.

    already present.

    Parameters
    ----------
    dependencies : dict[str, str | None]
        The mapping of package names to pinned versions to update with the new
        requirement.
    requirement : str
        The requirement string to parse and add, such as "requests>=2.0" or
        "numpy==1.21.0".
    """

    parsed = parse_requirement(requirement)

    if parsed is None:
        return

    name, version = parsed

    existing_version = dependencies.get(name)

    if name not in dependencies or (existing_version is None and version is not None):
        dependencies[name] = version
