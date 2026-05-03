<div align="center">

[![Akira](docs/assets/akira_logo_horizontal.png)](https://github.com/akira/akira)

[![PyPI](https://img.shields.io/pypi/v/akira?style=for-the-badge&color=ef233c)](https://pypi.org/project/akira/)
[![Python](https://img.shields.io/pypi/pyversions/akira?style=for-the-badge&logo=python&logoColor=white&color=111827)](https://pypi.org/project/akira/)
[![License](https://img.shields.io/badge/License-MIT-white?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Alpha-ef233c?style=for-the-badge)](#scope)

# Akira

**Stack intelligence for AI agents**

</div>

Akira is a local-first Python CLI that detects a project's stack, captures its
coding style, and generates agent-ready context so coding agents can work inside
the repository's real conventions.

It does not call an LLM. It reads the project, writes inspectable Markdown, and
installs deterministic Agent Skills for tools like Claude Code, Cursor, Copilot,
and Codex.

## Why Akira?

Coding agents are usually dropped into a repository cold. Akira gives them the
missing orientation layer: what stack this project uses, how this developer
writes code, and which guidance should be active before the first edit happens.

> One install gives an agent the project map, local coding style, and context
> files where the agent can actually use them.

## What Akira Does

```text
Project --> Akira CLI --> Detectors --> Stack Model --> Skills
             |              |
             |              +--> Python, frameworks, testing, databases, CI
             |
             +--> Fingerprint --> spacing, imports, naming, docstrings, typing
```

| Capability | Description |
| --- | --- |
| Stack detection | Finds Python runtime, package managers, frameworks, databases, testing tools, CI, infrastructure, and developer tooling. |
| Coding fingerprint | Extracts style signals from source files: spacing, imports, naming, comments, docstrings, typing, errors, strings, and structure. |
| Agent Skills | Generates stack-aware Markdown skills with YAML frontmatter from deterministic Jinja2 templates. |
| Stack review | Reports compatibility and cleanup findings, with optional metadata-only auto-apply behavior. |
| Agent install | Installs generated context into supported agent targets: `claude-code`, `cursor`, `copilot`, and `codex`. |

## Quick Start

### Install

```bash
# Recommended
uv tool install akira

# Or use pip
pip install akira

# Or run once
uvx akira install
```

### Install Agent Context

```bash
akira install --path .
```

After the flow finishes, Akira detects the stack, captures coding style,
generates skills, installs them for the selected agent, and updates `CLAUDE.md`
with Akira slash commands when appropriate.

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

> New to Akira? Start with `akira install --path .`. It runs the full setup
> flow and prompts for agent targets when needed.

---

## Commands

### `akira install`

Runs the full v2 setup flow: stack detection, fingerprinting, skill generation,
agent installation, and optional `CLAUDE.md` slash command setup.

```bash
akira install --path . --agent claude-code --output .akira
akira install --path . --no-claude-md
```

### `akira detect`

Scans a Python project, writes `.akira/stack.md`, generates matching skills, and
installs them for selected agents.

```bash
akira detect --path . --agent claude-code --output .akira
```

### `akira fingerprint`

Samples Python files and writes `.akira/fingerprint.md`.

```bash
akira fingerprint --path . --sample-size 20 --exclude tests/
```

### `akira review`

Reviews detected stack metadata for compatibility and best-practice findings.

```bash
akira review --path .
akira review --path . --strict
akira review --path . --auto-apply
```

<details>
<summary><strong>Generated artifacts</strong></summary>

| Artifact | Purpose |
| --- | --- |
| `.akira/stack.md` | Detected runtime, frameworks, databases, testing, tooling, infrastructure, CI, and active skills. |
| `.akira/fingerprint.md` | Style signals such as spacing, naming, imports, typing, comments, docstrings, control flow, error handling, and strings. |
| `.akira/skills/` | Agent Skills with YAML frontmatter and Markdown guidance generated from templates. |

Example outputs:

- [`docs/examples/stack.md`](docs/examples/stack.md)
- [`docs/examples/fingerprint.md`](docs/examples/fingerprint.md)
- [`docs/examples/skills/`](docs/examples/skills/)

</details>

<details>
<summary><strong>Supported agent targets</strong></summary>

| Agent | Target |
| --- | --- |
| Claude Code | `claude-code` |
| Cursor | `cursor` |
| GitHub Copilot | `copilot` |
| Codex | `codex` |

</details>

---

## Scope

Akira v2.0 is intentionally narrow, deterministic, and local-first.

| In scope | Out of scope for v2.0 |
| --- | --- |
| Python ecosystem detection | JavaScript, TypeScript, Go, Rust, or polyglot detection |
| Full setup through `install`, plus focused `detect`, `fingerprint`, and `review` commands | Hosted dashboard or web UI |
| Offline stack and style analysis | LLM-generated or API-enriched skills |
| Template-based skill generation | Watch mode |
| Local agent skill installation | MCP server behavior |

Roadmap candidates include multi-language detectors, LLM enrichment, watch mode,
hosted docs, and an MCP server.

## Development

```bash
# Create the dev environment
uv sync --extra dev

# Run the full test suite
uv run pytest

# Run linting
uv run ruff check .
```

Focused checks:

```bash
uv run pytest tests/test_detect
uv run pytest tests/test_fingerprint
uv run pytest tests/test_skills
```

Run the CLI from the working tree:

```bash
uv run akira detect --path tests/fixtures/fastapi_project --output .akira
uv run akira fingerprint --path tests/fixtures/style_projects/consistent --output .akira
uv run akira install --path tests/fixtures/fastapi_project --output .akira --agent claude-code
```

## Documentation

| Resource | Link |
| --- | --- |
| Validation checklist | [`docs/VALIDATION.md`](docs/VALIDATION.md) |
| Release process | [`docs/RELEASE.md`](docs/RELEASE.md) |
| Example stack output | [`docs/examples/stack.md`](docs/examples/stack.md) |
| Example fingerprint output | [`docs/examples/fingerprint.md`](docs/examples/fingerprint.md) |
| Example generated skills | [`docs/examples/skills/`](docs/examples/skills/) |

## License

MIT - see [LICENSE](LICENSE).
