---
name: akira-ruff
description: >
  Ruff linting and formatting guidance for fastapi_project.
  Consult when changing lint rules, formatting Python code, import sorting, or
  pre-commit hooks.
user-invocable: false
---

# Ruff Guidance

## Project Context

- Ruff version: 0.8.0
- Line length: project configured
- Config file: pyproject.toml

## Formatting

- Let Ruff format Python files when the project enables formatting.
- Keep line length and quote style aligned with project config.
- Avoid manual formatting churn outside touched code.
- Keep import ordering delegated to Ruff when `I` rules are enabled.

## Linting

- Prefer fixing the underlying issue over adding ignores.
- Keep per-file ignores narrow and documented by the config key.
- Add rule selections intentionally; broad rule expansions can create noisy
  follow-up work.
- Run Ruff before finalizing Python changes.
- Use `--fix` only when the resulting diff remains easy to review.
- Keep generated files excluded if they are not intended for manual edits.

## Python Style Baseline

- Follow PEP 8 unless the project configuration says otherwise.
- Use descriptive `snake_case` names for functions, variables, and modules.
- Use `PascalCase` for classes and `UPPER_SNAKE_CASE` for constants.
- Keep imports grouped as standard library, third-party, then local modules.
- Prefer small functions with explicit return values and clear guard clauses.
- Add comments only when they explain non-obvious intent or constraints.

## Imports

- Let Ruff organize imports according to the configured first-party package
  names.
- Avoid local imports unless they break a cycle or reduce startup cost.

## Configuration

- Keep rule changes in config files, not scattered in source comments.

## Avoid

- Adding Black or isort when Ruff already owns formatting and import sorting.
- Disabling rules globally to silence one local issue.
- Reformatting generated files unless they are meant to be edited.
- Changing lint config in the same commit as unrelated behavior changes.
