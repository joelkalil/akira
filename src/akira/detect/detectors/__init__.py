"""
Stack detector implementations.
"""

# Local Libraries
from akira.detect.detectors.base import BaseDetector
from akira.detect.detectors.ci_cd import CiCdDetector
from akira.detect.detectors.database import DatabaseDetector
from akira.detect.detectors.docs import DocsDetector
from akira.detect.detectors.frameworks import FrameworkDetector
from akira.detect.detectors.infra import InfrastructureDetector
from akira.detect.detectors.python import PythonDetector
from akira.detect.detectors.testing import TestingDetector
from akira.detect.detectors.tooling import ToolingDetector

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

__all__ = [
    "BaseDetector",
    "CiCdDetector",
    "DatabaseDetector",
    "DocsDetector",
    "FrameworkDetector",
    "InfrastructureDetector",
    "PythonDetector",
    "TestingDetector",
    "ToolingDetector",
]
