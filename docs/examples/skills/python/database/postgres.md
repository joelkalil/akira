---
name: akira-postgres
description: >
  PostgreSQL guidance for fastapi_project.
  Consult when writing SQL, indexes, constraints, transactions, or
  PostgreSQL-specific persistence code.
user-invocable: false
---

# PostgreSQL Guidance

## Project Context

- PostgreSQL version: detected by Akira
- Driver: psycopg, psycopg2, asyncpg, or detected driver
- ORM: SQLAlchemy

## Schema Design

- Model required fields with `NOT NULL` and sensible constraints.
- Use foreign keys for relational integrity unless the project has a deliberate
  boundary that prevents them.
- Add indexes for lookup, join, and ordering patterns used by production paths.
- Prefer `timestamptz` for timestamps that cross system boundaries.
- Use check constraints for simple domain invariants that must hold regardless
  of application code path.
- Keep extension usage explicit in migrations.

## Query Practices

- Keep queries parameterized; never interpolate user input into SQL strings.
- Read query plans for slow or high-volume paths.
- Use transactions for multi-step writes that must succeed or fail together.
- Keep locking behavior explicit when using `SELECT ... FOR UPDATE`.


## Error Handling

- Catch specific exceptions and handle only failures the code can recover from.
- Preserve exception context with `raise ... from exc` when wrapping errors.
- Avoid broad `except Exception` blocks in request handlers and library code.
- Validate inputs at boundaries and keep domain functions focused on domain work.
- Return actionable error messages without leaking secrets or internal tokens.

## Operational Notes

- Treat migrations and long-running queries as production operations.
- Keep backup and rollback expectations visible in risky schema changes.

## Avoid

- Unbounded queries in request paths.
- Indexes added without a query pattern.
- Database credentials in code, logs, tests, or generated skills.
- PostgreSQL-only syntax in code that must support multiple databases.
