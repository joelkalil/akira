---
name: akira-sqlalchemy
description: >
  SQLAlchemy guidance for fastapi_project.
  Consult when editing ORM models, sessions, queries, transactions, or
  repository/data-access code.
user-invocable: false
---

# SQLAlchemy Guidance

## Project Context

- SQLAlchemy version: 2.0.36
- Session style: sync or async detected by Akira
- Database: postgres

## Models

- Keep ORM models focused on persistence shape and small domain helpers.
- Use explicit column types, nullability, indexes, and relationship loading.
- Keep naming aligned with the existing table and metadata conventions.
- Avoid implicit defaults when server-side defaults are required.

## Sessions And Transactions

- Pass sessions through application boundaries instead of creating them deep in
  domain functions.
- Keep transaction ownership clear: one unit of work should commit or roll back.
- Flush when generated IDs are needed before commit.
- Do not hide commits in low-level helper functions unless the project already
  follows that pattern.


## Error Handling

- Catch specific exceptions and handle only failures the code can recover from.
- Preserve exception context with `raise ... from exc` when wrapping errors.
- Avoid broad `except Exception` blocks in request handlers and library code.
- Validate inputs at boundaries and keep domain functions focused on domain work.
- Return actionable error messages without leaking secrets or internal tokens.

## Query Practices

- Keep reusable query construction in named functions or repository methods.
- Use eager loading deliberately to avoid repeated lazy loads.
- Return domain objects or DTOs according to the project's current pattern.

## Avoid

- Global sessions shared across requests or tests.
- Raw SQL for ORM-friendly queries without a clear reason.
- Mixing migration concerns into runtime model code.
- Silent transaction failures without rollback and logging.
