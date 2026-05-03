"""
Agent skill generation package.
"""

# Local Libraries
from akira.skills.generator import GeneratedSkill, SkillGenerator, generate_skills
from akira.skills.installer import (
    ClaudeSkillInstaller,
    GeneratedSkillInstaller,
    InstalledSkillFile,
    install_claude_skills,
    install_generated_skills,
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

__all__ = [
    "ClaudeSkillInstaller",
    "GeneratedSkillInstaller",
    "GeneratedSkill",
    "InstalledSkillFile",
    "SkillGenerator",
    "generate_skills",
    "install_claude_skills",
    "install_generated_skills",
]
