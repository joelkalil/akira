---
name: akira-docker
description: >
  Docker guidance for fastapi_project.
  Consult when editing Dockerfiles, compose files, images, runtime commands, or
  containerized development workflows.
user-invocable: false
---

# Docker Guidance

## Project Context

- Dockerfile: Dockerfile
- Compose file: docker-compose.yml
- Package manager: uv

## Dockerfiles

- Keep build stages purposeful and easy to audit.
- Install only runtime dependencies in the final image.
- Pin base images according to the project's release policy.
- Copy dependency metadata before application code to preserve layer caching.
- Run the application as a non-root user when practical.

## uv In Containers

- Copy `pyproject.toml` and `uv.lock` before syncing dependencies.
- Use frozen or locked installs for reproducible builds.
- Keep the virtual environment path predictable if the project relies on one.

## Compose

- Use compose for local dependencies such as PostgreSQL, Redis, or worker
  services.
- Keep ports, volumes, and environment variables explicit.
- Do not commit local secrets in compose files.
- Prefer named volumes for persistent local service data.
- Keep service names stable so application connection strings remain readable.

## Logging Patterns

- Use module-level loggers created with `logging.getLogger(__name__)`.
- Log operational events at `INFO`, unexpected recoverable failures at
  `WARNING`, and actionable failures at `ERROR` or `EXCEPTION`.
- Include stable identifiers in log context, not raw payloads or credentials.
- Do not use `print()` for application diagnostics outside CLI user output.
- Prefer structured context through `extra` when the project logger supports it.

## Runtime Checks

- Keep healthcheck commands cheap and available in the final image.

## Avoid

- Network calls during generated skill rendering.
- Baking credentials or `.env` contents into images.
- Copying the entire repository before dependency installation.
- Large images with build tools left in the runtime stage.
