---
name: akira-fastapi
description: >
  FastAPI guidance for fastapi_project.
  Consult when creating or modifying routers, endpoints, dependencies,
  middleware, response models, or application startup code.
user-invocable: false
---

# FastAPI Guidance

## Project Context

- FastAPI version: 0.115.0
- Async stack: detected from database and imports
- Router style: APIRouter per feature or domain

## Endpoint Shape

- Define routes on `APIRouter`, then include routers in the application factory
  or main app module.
- Use `response_model` for successful JSON responses.
- Use `status` constants instead of raw status integers.
- Keep route functions thin: validate input, call service/domain code, and
  translate results into API responses.
- Put shared concerns such as auth, database sessions, and pagination in
  `Depends()` dependencies.

## Pydantic v2

- Use `model_validate()` when converting ORM or domain objects to schemas.
- Use `model_dump()` when passing request payloads into domain constructors.
- Keep request and response models separate when fields differ.

## Error Handling

- Catch specific exceptions and handle only failures the code can recover from.
- Preserve exception context with `raise ... from exc` when wrapping errors.
- Avoid broad `except Exception` blocks in request handlers and library code.
- Validate inputs at boundaries and keep domain functions focused on domain work.
- Return actionable error messages without leaking secrets or internal tokens.

## Testing Hooks

- Structure dependencies so tests can override them cleanly.
- Prefer `TestClient` or `httpx.AsyncClient` according to the app's async style.
- Assert status codes and response bodies, not framework internals.

## Avoid

- Business logic embedded directly in route functions.
- Catching generic exceptions to return `500` manually.
- Returning raw ORM objects without an explicit response model.
- Creating database engines or clients inside individual endpoints.
