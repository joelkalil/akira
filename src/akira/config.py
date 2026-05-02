"""
Shared configuration values for Akira.
"""

# Standard Libraries
from __future__ import annotations
from pathlib import Path

# Local Libraries
from akira.agents import SUPPORTED_AGENT_NAMES

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

DEFAULT_OUTPUT_DIR = Path(".akira")

DEFAULT_AGENT = "claude-code"

SUPPORTED_AGENTS = SUPPORTED_AGENT_NAMES
