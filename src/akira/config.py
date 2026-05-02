"""Shared configuration values for Akira."""

from __future__ import annotations

from pathlib import Path

from akira.agents import SUPPORTED_AGENT_NAMES

DEFAULT_OUTPUT_DIR = Path(".akira")
DEFAULT_AGENT = "claude-code"
SUPPORTED_AGENTS = SUPPORTED_AGENT_NAMES
