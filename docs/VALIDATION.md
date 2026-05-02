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
