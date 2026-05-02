# Release Checklist

Use this checklist before publishing Akira to PyPI or to a fallback package name.
Akira supports Python 3.11 and newer.

## Package Name

- Primary PyPI distribution name: `akira`.
- If `akira` is unavailable, publish as `akira-cli` or `akira-skills`.
- Keep the installed command named `akira` in every distribution by preserving:

```toml
[project.scripts]
akira = "akira.cli:main"
```

## Preflight

- Confirm `pyproject.toml` has the intended release version.
- Confirm the build backend is `hatchling.build`.
- Confirm wheel package discovery includes `src/akira`.
- Confirm Jinja2 templates live under `src/akira/**/templates/` so package
  loaders can find them after installation.
- Run the test suite and linter:

```bash
uv run pytest
uv run ruff check .
```

## Build

Build both wheel and source distribution:

```bash
python -m build
```

If `build` is not installed in the active environment:

```bash
uv run --with build python -m build
```

Expected output includes one `.whl` and one `.tar.gz` under `dist/`.

## Smoke Test: pip

Install the built wheel into a clean virtual environment and confirm the CLI and
templates work outside the repository checkout:

```bash
python -m venv .venv-release
.venv-release\Scripts\python -m pip install --upgrade pip
.venv-release\Scripts\python -m pip install dist\*.whl
.venv-release\Scripts\akira --help
.venv-release\Scripts\akira detect --path tests\fixtures\fastapi_project --output .akira-release
```

The `akira --help` command must list the CLI commands. The `detect` command must
write `stack.md` and generate skill files from packaged Jinja2 templates.

## Smoke Test: uv Tool Install

Install the built wheel as a global-style uv tool from the local artifact:

```bash
uv tool install --force dist\akira-*.whl
akira --help
akira detect --path tests\fixtures\fastapi_project --output .akira-release-uv
```

If testing a fallback distribution name, install that wheel path but still
confirm the command is `akira`.

## Smoke Test: uvx

After publishing to PyPI or TestPyPI, confirm one-shot execution:

```bash
uvx akira --help
uvx akira detect --path tests\fixtures\fastapi_project --output .akira-release-uvx
```

For fallback package names, call uvx with the package and command explicitly:

```bash
uvx --from akira-cli akira --help
uvx --from akira-skills akira --help
```

## Publish

Publish only after the build artifacts and smoke tests pass:

```bash
uv publish
```

For TestPyPI or another index, pass the appropriate uv publish index settings
for that environment.

## Final Verification

- Wheel and sdist build successfully.
- Installed package exposes `akira`.
- Installed package can render skill templates.
- Fallback package-name guidance still preserves the `akira` command.
