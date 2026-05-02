---
name: akira-github-actions
description: >
  GitHub Actions guidance for fastapi_project.
  Consult when editing workflows, CI jobs, dependency caching, test matrices, or
  release automation.
user-invocable: false
---

# GitHub Actions Guidance

## Project Context

- Workflow path: .github/workflows
- Python versions: configured in CI
- Package manager: uv

## Workflow Shape

- Keep CI jobs focused: install, lint, type-check, test, build, and publish
  should be easy to scan.
- Use a matrix only when multiple Python versions or platforms are meaningful.
- Keep permissions minimal at the workflow or job level.
- Pin third-party actions to stable versions according to project policy.
- Use concurrency groups for branch or pull request workflows that should cancel
  stale runs.
- Keep job names stable so branch protection rules remain understandable.

## uv In CI

- Install uv before syncing dependencies.
- Cache uv-managed dependencies when the workflow already uses caching.
- Use locked installs for repeatable CI runs.

## Secrets And Releases

- Read secrets only in jobs that need them.
- Avoid printing secrets, tokens, or cloud credentials.
- Separate pull request validation from release or deployment jobs.
- Require explicit tags, environments, or protected branches for publishing.

## Python Checks

- Run tests through the same project command developers use locally.
- Upload coverage or build artifacts only when a downstream job consumes them.

## Avoid

- Workflow steps that require interactive input.
- Network credentials in generated skills or checked-in examples.
- Unrelated formatting, lint, and release changes in one workflow edit.
- Permissions broader than the job needs.
