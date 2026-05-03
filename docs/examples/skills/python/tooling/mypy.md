---
name: akira-mypy
description: >
  mypy type-checking guidance for fastapi_project.
  Consult when adding annotations, changing type-check configuration, or fixing
  static type errors.
user-invocable: false
---

# mypy Guidance

## Project Context

- mypy version: 1.13.0
- Strictness: project configured
- Config file: pyproject.toml

## Annotation Style

- Annotate public function parameters and return values.
- Prefer precise collection types and small typed structures.
- Use `Protocol` for behavior-based dependencies when it simplifies tests.
- Keep casts local and explain them when the reason is not obvious.

## Type Errors

- Fix the source of the type mismatch before reaching for `type: ignore`.
- Use narrow ignores such as `# type: ignore[code]`.
- Keep third-party missing-stub configuration centralized.
- Avoid widening types to `Any` to make errors disappear.
- Prefer small normalization functions over repeated optional checks spread
  across call sites.
- Keep public protocols and aliases near the code that owns them.

## Python 3.10+

- Prefer `X | None` over `Optional[X]`.
- Use built-in collection generics such as `list[str]`.

## Testing And Boundaries

- Type boundaries that parse external data explicitly.
- Keep mocks and fixtures typed enough that test failures remain meaningful.
- For CLI functions, type parsed options and return values clearly.

## Configuration

- Add stricter options gradually when existing code can satisfy them.

## Avoid

- Blanket ignores in package modules.
- Untyped helper functions that become hidden dynamic zones.
- Changing mypy strictness without updating affected code.
