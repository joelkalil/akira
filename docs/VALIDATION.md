# Manual Validation

Sprint 1 release checks should run `akira detect` against representative real
projects before publishing detector changes.

## Targets

- `portfolio-service`: validates FastAPI, uv, Ruff, mypy, pre-commit, database,
  and stack rendering behavior on a production-style service.
- `solarsim2`: validates detector behavior on a second real project shape and
  catches assumptions that only hold for portfolio-service.

Private repositories are manual validation targets only. They should not be
copied into fixtures or required by CI.

## Release Packaging

Run the release checklist in [`RELEASE.md`](RELEASE.md) before publishing. It
covers wheel and sdist builds, installed CLI smoke tests with pip and uv, Jinja2
template availability from installed packages, and PyPI fallback package names
that preserve the `akira` command.
