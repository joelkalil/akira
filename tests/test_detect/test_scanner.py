from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest

from akira.detect import Scanner, Signal, StackInfo
from akira.detect.detectors import BaseDetector


class LaterDetector(BaseDetector):
    order = 20

    def detect(self, project_root: Path) -> list[Signal]:
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
    order = 10

    def detect(self, project_root: Path) -> list[Signal]:
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


def test_scanner_runs_fake_detectors_in_deterministic_order(tmp_path: Path) -> None:
    scanner = Scanner([LaterDetector(), EarlierDetector()])

    stack = scanner.scan(tmp_path)

    assert isinstance(stack, StackInfo)
    assert [signal.tool for signal in stack.signals] == ["fastapi", "pytest"]
    assert stack.has("fastapi")
    assert stack.has("fastapi", category="web_framework")
    assert stack.has_any("django", "pytest")


def test_signals_include_source_confidence_and_metadata(tmp_path: Path) -> None:
    scanner = Scanner([EarlierDetector()])

    signal = scanner.collect_signals(tmp_path)[0]

    assert signal.source == "pyproject.toml"
    assert signal.confidence == 1.0
    assert signal.metadata == {"detector": "EarlierDetector"}
    assert isinstance(signal.metadata, MappingProxyType)


def test_scanner_deduplicates_equivalent_signals_with_highest_confidence(
    tmp_path: Path,
) -> None:
    scanner = Scanner([EarlierDetector(), LaterDetector()])

    signals = scanner.collect_signals(tmp_path)

    assert [signal.tool for signal in signals] == ["fastapi", "pytest"]
    pytest_signal = next(signal for signal in signals if signal.tool == "pytest")
    assert pytest_signal.confidence == 0.8
    assert pytest_signal.metadata == {"detector": "LaterDetector"}


def test_stack_info_groups_tools_by_category(tmp_path: Path) -> None:
    stack = Scanner([EarlierDetector()]).scan(tmp_path)

    testing_tools = stack.by_category("testing")

    assert len(testing_tools) == 1
    assert testing_tools[0].name == "pytest"
    assert testing_tools[0].sources == ("pyproject.toml",)
    assert isinstance(testing_tools[0].metadata, MappingProxyType)


def test_signal_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="confidence"):
        Signal(
            tool="pytest",
            category="testing",
            confidence=1.5,
            source="pyproject.toml",
        )
