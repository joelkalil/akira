"""
Tests for scanner.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

# Third-Party Libraries
import pytest

# Local Libraries
from akira.detect import Scanner, Signal, StackInfo
from akira.detect.detectors import BaseDetector

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class LaterDetector(BaseDetector):
    """
    Represent laterdetector behavior.
    """

    order = 20

    def detect(self, project_root: Path) -> list[Signal]:
        """
        Return detect result.
        """

        return [
            Signal(
                tool="pytest",
                category="testing",
                version="8.0",
                confidence=0.8,
                source="pyproject.toml",
                metadata={"detector": self.name},
            )
        ]


class EarlierDetector(BaseDetector):
    """
    Represent earlierdetector behavior.
    """

    order = 10

    def detect(self, project_root: Path) -> list[Signal]:
        """
        Return detect result.
        """

        return [
            Signal(
                tool="fastapi",
                category="web_framework",
                version="0.115",
                confidence=1.0,
                source="pyproject.toml",
                metadata={"detector": self.name},
            ),
            Signal(
                tool="pytest",
                category="testing",
                version="8.0",
                confidence=0.6,
                source="pyproject.toml",
                metadata={"detector": self.name},
            ),
        ]


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


class TestScannerRunsFakeDetectorsInDeterministicOrder:
    """
    Verify scanner runs fake detectors in deterministic order cases.
    """

    def test_scanner_runs_fake_detectors_in_deterministic_order(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify scanner runs fake detectors in deterministic order behavior.
        """

        scanner = Scanner(detectors=[LaterDetector(), EarlierDetector()])

        stack = scanner.scan(tmp_path)

        assert isinstance(stack, StackInfo)

        assert [signal.tool for signal in stack.signals] == ["fastapi", "pytest"]

        assert stack.has("fastapi")

        assert stack.has("fastapi", category="web_framework")

        assert stack.has_any("django", "pytest")


class TestSignalsIncludeSourceConfidenceAndMetadata:
    """
    Verify signals include source confidence and metadata cases.
    """

    def test_signals_include_source_confidence_and_metadata(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify signals include source confidence and metadata behavior.
        """

        scanner = Scanner(detectors=[EarlierDetector()])

        signal = scanner.collect_signals(tmp_path)[0]

        assert signal.source == "pyproject.toml"

        assert signal.confidence == 1.0

        assert signal.metadata == {"detector": "EarlierDetector"}

        assert isinstance(signal.metadata, MappingProxyType)


class TestScannerDeduplicatesEquivalentSignalsWithHighestConfidence:
    """
    Verify scanner deduplicates equivalent signals with highest confidence cases.
    """

    def test_scanner_deduplicates_equivalent_signals_with_highest_confidence(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify scanner deduplicates equivalent signals with highest confidence behavior.
        """

        scanner = Scanner(detectors=[EarlierDetector(), LaterDetector()])

        signals = scanner.collect_signals(tmp_path)

        assert [signal.tool for signal in signals] == ["fastapi", "pytest"]

        pytest_signal = next(signal for signal in signals if signal.tool == "pytest")

        assert pytest_signal.confidence == 0.8

        assert pytest_signal.metadata == {"detector": "LaterDetector"}


class TestStackInfoGroupsToolsByCategory:
    """
    Verify stack info groups tools by category cases.
    """

    def test_stack_info_groups_tools_by_category(self, tmp_path: Path) -> None:
        """
        Verify stack info groups tools by category behavior.
        """

        stack = Scanner(detectors=[EarlierDetector()]).scan(tmp_path)

        testing_tools = stack.by_category("testing")

        assert len(testing_tools) == 1

        assert testing_tools[0].name == "pytest"

        assert testing_tools[0].sources == ("pyproject.toml",)

        assert isinstance(testing_tools[0].metadata, MappingProxyType)


class TestScannerIntegrationDetectsFastapiFixtureStack:
    """
    Verify scanner integration detects fastapi fixture stack cases.
    """

    def test_scanner_integration_detects_fastapi_fixture_stack(
        self,
        fixtures_dir: Path,
    ) -> None:
        """
        Verify scanner integration detects fastapi fixture stack behavior.
        """

        stack = Scanner().scan(fixtures_dir / "fastapi_project")

        assert stack.has("python", category="runtime")

        assert stack.has("uv", category="package_manager")

        assert stack.has("fastapi", category="web_framework")

        assert stack.has("pytest", category="testing")

        assert stack.has("ruff", category="linting")

        assert stack.has("mypy", category="type_checking")

        assert stack.has("pre-commit", category="pre_commit")

        assert stack.has("docker", category="infrastructure")

        assert stack.has("github-actions", category="ci_cd")


class TestSignalRejectsInvalidConfidence:
    """
    Verify signal rejects invalid confidence cases.
    """

    def test_signal_rejects_invalid_confidence(self) -> None:
        """
        Verify signal rejects invalid confidence behavior.
        """

        with pytest.raises(ValueError, match="confidence"):

            Signal(
                tool="pytest",
                category="testing",
                confidence=1.5,
                source="pyproject.toml",
            )
