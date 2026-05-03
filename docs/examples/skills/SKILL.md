---
name: akira
description: >
  Project-aware coding conventions for fastapi_project.
  Detected stack: FastAPI + SQLAlchemy + PostgreSQL + Alembic + pytest + ruff + mypy + uv + Docker + GitHub Actions.
  Always consult this skill before writing or modifying code. Read ../stack.md
  for project context, ../fingerprint.md for style, and task-specific sub-skills
  for implementation patterns.
user-invocable: false
---

# Akira - fastapi_project

Use this router as the entry point for generated Akira guidance.

Before writing code, consult:

1. `../stack.md` for detected project tools, versions, and sources.
2. `../fingerprint.md` for developer coding style and preferences.
3. The active sub-skill that matches the current task.

## Project Context

- Project: fastapi_project
- Detected stack: FastAPI + SQLAlchemy + PostgreSQL + Alembic + pytest + ruff + mypy + uv + Docker + GitHub Actions
- Runtime: Python 3.12
- Package manager: uv

## Active Sub-Skills

- Read `python/SKILL.md` when working with Python modules, imports, typing, or shared code.
- Read `python/tooling/uv.md` when working with Python package and environment work.
- Read `python/web_framework/fastapi.md` when working with FastAPI endpoints, routers, dependencies, or middleware.
- Read `python/testing/pytest.md` when working with pytest tests, fixtures, parametrization, or test configuration.
- Read `python/database/sqlalchemy.md` when working with SQLAlchemy models, sessions, queries, or persistence code.
- Read `python/database/alembic.md` when working with Alembic migrations or database schema changes.
- Read `python/database/postgres.md` when working with PostgreSQL schema, queries, drivers, or database behavior.
- Read `python/tooling/ruff.md` when working with Ruff linting, formatting, or import organization.
- Read `python/tooling/mypy.md` when working with mypy typing, annotations, or static analysis.
- Read `python/infra/docker.md` when working with Dockerfiles, images, containers, or compose integration.
- Read `python/ci_cd/github_actions.md` when working with GitHub Actions workflows or CI/CD automation.

## Core Rules From Fingerprint

- `fingerprint.md` exists, but Akira did not find enough high-confidence
  structured rules for the router. Use it as the source of truth for detailed
  style guidance.
- Prefer the conventions already present in the repository.
- Keep generated code offline, deterministic, and inspectable unless the task
  explicitly requires integration with an external service.

## Python Style Baseline

- Follow PEP 8 unless the project configuration says otherwise.
- Use descriptive `snake_case` names for functions, variables, and modules.
- Use `PascalCase` for classes and `UPPER_SNAKE_CASE` for constants.
- Keep imports grouped as standard library, third-party, then local modules.
- Prefer small functions with explicit return values and clear guard clauses.
- Add comments only when they explain non-obvious intent or constraints.

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

## When To Drill Down

- API endpoint or middleware work: read the web framework skill first.
- Tests and fixtures: read the pytest or unittest skill first.
- Models, sessions, migrations, or SQL: read the database skills first.
- Formatting, linting, typing, or packaging: read the tooling skills first.
- Docker, GCP, or GitHub Actions: read the infrastructure and CI skills first.
