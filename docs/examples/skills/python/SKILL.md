---
name: akira-python
description: >
  Python coding guidance for fastapi_project.
  Consult before editing Python modules, package structure, imports, or shared
  application logic.
user-invocable: false
---

# Python Guidance

## Project Context

- Python version: 3.12
- Source layout: src
- Package manager: uv

## Python Style Baseline

- Follow PEP 8 unless the project configuration says otherwise.
- Use descriptive `snake_case` names for functions, variables, and modules.
- Use `PascalCase` for classes and `UPPER_SNAKE_CASE` for constants.
- Keep imports grouped as standard library, third-party, then local modules.
- Prefer small functions with explicit return values and clear guard clauses.
- Add comments only when they explain non-obvious intent or constraints.

## Module Structure

- Keep modules focused around one responsibility or closely related use cases.
- Put constants near the top after imports and before runtime logic.
- Keep public functions and classes easy to scan; move local complexity into
  private helpers when it improves readability.
- Prefer absolute imports inside the package unless the project already uses
  relative imports consistently.

## Type Hints

- Add type hints to public functions, methods, and dataclasses.
- Prefer built-in generics such as `list[str]` and `dict[str, int]`.
- Use `X | None` for optional values on Python 3.10+ projects.
- Avoid `Any` unless the boundary is genuinely dynamic.

## Error Handling

- Catch specific exceptions and handle only failures the code can recover from.
- Preserve exception context with `raise ... from exc` when wrapping errors.
- Avoid broad `except Exception` blocks in request handlers and library code.
- Validate inputs at boundaries and keep domain functions focused on domain work.
- Return actionable error messages without leaking secrets or internal tokens.

## Logging Patterns

- Use module-level loggers created with `logging.getLogger(__name__)`.
- Log operational events at `INFO`, unexpected recoverable failures at
  `WARNING`, and actionable failures at `ERROR` or `EXCEPTION`.
- Include stable identifiers in log context, not raw payloads or credentials.
- Do not use `print()` for application diagnostics outside CLI user output.
- Prefer structured context through `extra` when the project logger supports it.

## Do

- Preserve existing naming, import ordering, and layout conventions.
- Keep side effects at application boundaries.
- Write code that can be tested without network access.
- Make configuration explicit through settings, environment parsing, or CLI
  options already used by the project.

## Avoid

- Hidden global state in import-time code.
- Bare `except:` clauses.
- New dependencies for simple standard-library problems.
- Reformatting unrelated files while making a targeted change.
