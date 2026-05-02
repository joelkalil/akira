# Akira

Akira is a Python CLI that detects a project's stack, generates contextual
Agent Skills, and captures a developer coding fingerprint so coding agents can
follow the repository's conventions.

Akira v1.0 is intentionally narrow: Python projects only, four commands, local
filesystem output, and deterministic templates. It runs offline and has zero LLM
dependency. Future releases may add LLM enrichment, multi-language detectors,
watch mode, or an MCP server, but those are roadmap items, not v1.0 behavior.

## What Akira Generates

Akira writes inspectable Markdown artifacts under `.akira/` by default:

```text
.akira/
|-- stack.md
|-- fingerprint.md
`-- skills/
    |-- SKILL.md
    `-- python/
        |-- SKILL.md
        |-- web_framework/fastapi.md
        |-- testing/pytest.md
        |-- database/sqlalchemy.md
        |-- tooling/ruff.md
        `-- ...
```

- `stack.md` records detected runtime, frameworks, databases, testing tools,
  developer tooling, infrastructure, CI, and active skills.
- `fingerprint.md` records style signals such as spacing, naming, imports,
  typing, comments, docstrings, control flow, error handling, and strings.
- `skills/` contains Agent Skills with YAML frontmatter and Markdown guidance.
  These skills are generated from Jinja2 templates in v1.0.

See example artifacts in [`docs/examples/stack.md`](docs/examples/stack.md),
[`docs/examples/fingerprint.md`](docs/examples/fingerprint.md), and
[`docs/examples/skills/`](docs/examples/skills/).

## Installation

Recommended global install with uv:

```bash
uv tool install akira
```

Install with pip:

```bash
pip install akira
```

Run once without installing:

```bash
uvx akira detect
```

The intended PyPI distribution name is `akira`. If that name is unavailable,
the package may be published as `akira-cli` or `akira-skills`, while preserving
the executable command as `akira` through the Python entry point.

## Commands

### `akira detect`

Scans a Python project, writes `.akira/stack.md`, generates the matching skill
tree, and installs those skills for the selected agent.

```bash
akira detect --path . --agent claude-code --output .akira
```

Supported agent targets include the adapters exposed by the CLI, such as
`claude-code`, `cursor`, `copilot`, and `codex`.

### `akira fingerprint`

Samples Python files and writes `.akira/fingerprint.md`.

```bash
akira fingerprint --path . --sample-size 20 --exclude tests/
```

### `akira review`

Reviews the detected stack for compatibility and best-practice findings. Safe
metadata-only changes can be accepted interactively or with `--auto-apply`.

```bash
akira review --path .
akira review --path . --strict
```

### `akira craft`

Installs previously generated Akira artifacts into the selected agent's context.
Use this after `detect` and `fingerprint` when you want to refresh agent files.

```bash
akira craft --path . --agent claude-code --output .akira
```

## Typical Flow

```bash
akira detect --path .
akira fingerprint --path .
akira review --path .
akira craft --path .
```

After this flow, review the generated `.akira/` files and the installed agent
skills before relying on them in a coding session.

## v1.0 Scope

Implemented scope:

- Python ecosystem detection.
- Four CLI commands: `detect`, `fingerprint`, `review`, and `craft`.
- Offline stack and style analysis.
- Template-based skill generation.
- Local agent skill installation.

Out of scope for v1.0:

- Hosted documentation.
- LLM-generated or API-enriched skills.
- Full migration guides for every review rule.
- JavaScript, TypeScript, or other language detectors.
- Watch mode or MCP server behavior.

## Local Development

Create the development environment and run the test suite:

```bash
uv sync --extra dev
uv run pytest
```

Useful focused checks:

```bash
uv run pytest tests/test_detect
uv run pytest tests/test_fingerprint
uv run pytest tests/test_skills
uv run ruff check .
```

Run the CLI from the working tree:

```bash
uv run akira detect --path tests/fixtures/fastapi_project --output .akira
uv run akira fingerprint --path tests/fixtures/style_projects/consistent --output .akira
```

Manual release validation targets are tracked in
[`docs/VALIDATION.md`](docs/VALIDATION.md).
