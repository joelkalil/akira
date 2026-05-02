# Akira

Akira is a Python CLI that will detect a project's stack, generate contextual
agent skills, and capture a developer coding fingerprint.

This repository is currently in the v1.0 foundation phase. The initial package
scaffold exposes an importable `akira` package and reserves the CLI entry point
for upcoming `detect`, `review`, `fingerprint`, and `craft` commands.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

