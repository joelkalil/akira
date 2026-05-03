---
name: akira-pytest
description: >
  pytest guidance for fastapi_project.
  Consult when adding tests, fixtures, parametrization, coverage, or test
  configuration.
user-invocable: false
---

# pytest Guidance

## Project Context

- pytest version: 8.3.0
- Test path: tests
- Async tests: True

## Test Shape

- Name test files and functions so the behavior under test is obvious.
- Keep one behavior per test when practical.
- Use plain `assert` statements and let pytest show rich diffs.
- Prefer parametrization for repeated cases with different inputs.
- Keep tests deterministic and independent of external network services.

## Fixtures

- Put reusable fixtures in `conftest.py` near the tests that use them.
- Keep fixture scope as narrow as possible.
- Compose fixtures instead of hiding large setup flows in one fixture.
- Use factories for data variations instead of mutating shared objects.

## Async Tests

- Use the project's existing async plugin and marker style.
- Await async clients, database calls, and background task helpers.
- Keep event loop setup centralized in fixtures.

## Error Handling

- Catch specific exceptions and handle only failures the code can recover from.
- Preserve exception context with `raise ... from exc` when wrapping errors.
- Avoid broad `except Exception` blocks in request handlers and library code.
- Validate inputs at boundaries and keep domain functions focused on domain work.
- Return actionable error messages without leaking secrets or internal tokens.

## Coverage Priorities

- Cover public behavior, edge cases, and failure paths.
- Add regression tests for bug fixes before or alongside the fix.
- For CLI code, assert exit code, output, and filesystem effects.

## Avoid

- Tests that depend on execution order.
- Assertions against private implementation details when behavior is enough.
- Network calls, real cloud credentials, or local machine-specific paths.
- Large snapshot updates without reviewing the generated diff.
