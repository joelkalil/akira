"""
Project stack detection package.
"""

# Local Libraries
from akira.detect.models import Signal, StackCategory, StackInfo, ToolInfo
from akira.detect.renderer import render_stack_markdown, write_stack_markdown
from akira.detect.scanner import Scanner, scan_project

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

__all__ = [
    "Scanner",
    "Signal",
    "StackCategory",
    "StackInfo",
    "ToolInfo",
    "render_stack_markdown",
    "scan_project",
    "write_stack_markdown",
]
