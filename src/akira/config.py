"""Shared configuration values for Akira."""

from __future__ import annotations

from pathlib import Path

DEFAULT_OUTPUT_DIR = Path(".akira")
DEFAULT_AGENT = "claude-code"
SUPPORTED_AGENTS = ("claude-code", "cursor", "copilot", "codex")

