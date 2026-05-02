"""
Normalized stack models produced by Akira detectors.
"""

# Standard Libraries
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class Signal:
    """
    A single detection signal emitted by a detector.

    Attributes
    ----------
    tool : str
        Detected tool name.
    category : str
        Detected tool category.
    version : str | None
        Optional detected tool version.
    confidence : float
        Confidence score between 0.0 and 1.0 indicating the certainty of the detection
        (e.g., 1.0 for deterministic detections, lower for heuristic detections).
    source : str
        Optional source information about where the signal was detected (e.g., filename).
    metadata : Mapping[str, Any]
        Optional additional metadata about the signal.
    """

    tool: str

    category: str

    version: str | None = None

    confidence: float = 1.0

    source: str = ""

    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Validate and normalize signal fields after initialization.
        """

        if not 0.0 <= self.confidence <= 1.0:

            msg = "Signal confidence must be between 0.0 and 1.0."

            raise ValueError(msg)

        object.__setattr__(self, "tool", self.tool.strip().lower())

        object.__setattr__(self, "category", self.category.strip().lower())

        object.__setattr__(self, "source", self.source.strip())

        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def identity(self) -> tuple[str, str, str | None, str]:
        """
        Return the stable identity used to deduplicate equivalent signals.

        Returns
        -------
        tuple[str, str, str | None, str]
            Stable signal identity.
        """

        return (self.tool, self.category, self.version, self.source)


@dataclass(frozen=True)
class ToolInfo:
    """
    Aggregated view of one detected tool.

    Attributes
    ----------
    name : str
        Detected tool name.
    category : str
        Detected tool category.
    version : str | None
        Optional detected tool version.
    confidence : float
        Confidence score between 0.0 and 1.0 indicating the certainty of the detection
        (e.g., 1.0 for deterministic detections, lower for heuristic detections).
    sources : tuple[str, ...]
        Optional source information about where the tool was detected (e.g., filenames).
    metadata : Mapping[str, Any]
        Optional additional metadata about the tool aggregated from all contributing signals.
    """

    name: str

    category: str

    version: str | None = None

    confidence: float = 1.0

    sources: tuple[str, ...] = ()

    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Validate and normalize tool info fields after initialization.
        """

        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class StackCategory:
    """
    A group of tools that belong to the same stack category.

    Attributes
    ----------
    name : str
        Category name (e.g., "linting", "formatting").
    tools : tuple[ToolInfo, ...]
        Detected tools in this category.

    Methods
    -------
    has(tool: str) -> bool
        Return whether this category contains a tool.
    """

    name: str

    tools: tuple[ToolInfo, ...] = ()

    def has(self, tool: str) -> bool:
        """
        Return whether this category contains a tool.

        Parameters
        ----------
        tool
            Tool name to check.

        Returns
        -------
        bool
            Whether the category contains the tool.
        """

        normalized = tool.strip().lower()

        return any(item.name == normalized for item in self.tools)


@dataclass(frozen=True)
class StackInfo:
    """
    Normalized stack information for a project.

    Attributes
    ----------
    project_root : Path
        The root directory of the project.
    project_name : str
        The name of the project (derived from the root directory name).
    signals : tuple[Signal, ...]
        All individual signals that contributed to the detected stack.
    categories : tuple[StackCategory, ...]
        Detected stack categories with aggregated tool information.

    Methods
    -------
    from_signals(project_root: Path, signals: list[Signal] | tuple[Signal, ...]) -> StackInfo
        Build a normalized stack model from detector signals.
    has(tool: str, category: str | None = None) -> bool
        Return whether a tool is present in the detected stack, optionally restricted to a category.
    has_any(*tools: str, category: str | None = None) -> bool
        Return whether any of the provided tools are present, optionally restricted to a category.
    by_category(category: str) -> tuple[ToolInfo, ...]
        Return aggregated tools for a category.
    """

    project_root: Path

    project_name: str

    signals: tuple[Signal, ...] = ()

    categories: tuple[StackCategory, ...] = ()

    @classmethod
    def from_signals(
        cls,
        project_root: Path,
        signals: list[Signal] | tuple[Signal, ...],
    ) -> StackInfo:
        """
        Build a normalized stack model from detector signals.

        Parameters
        ----------
        project_root
            Root directory of the project being modeled.
        signals
            Detector signals to aggregate.

        Returns
        -------
        StackInfo
            Normalized stack information for the project.
        """

        root = project_root.resolve()

        signal_tuple = tuple(signals)

        grouped: dict[str, dict[tuple[str, str | None], list[Signal]]] = {}

        for signal in signal_tuple:

            category = signal.category

            key = (signal.tool, signal.version)

            grouped.setdefault(category, {}).setdefault(key, []).append(signal)

        categories = []

        for category_name in sorted(grouped):

            tools = []

            for (tool_name, version), tool_signals in sorted(
                grouped[category_name].items()
            ):

                sources = tuple(
                    dict.fromkeys(
                        signal.source for signal in tool_signals if signal.source
                    )
                )

                metadata: dict[str, Any] = {}

                for signal in tool_signals:

                    metadata.update(signal.metadata)

                tools.append(
                    ToolInfo(
                        name=tool_name,
                        category=category_name,
                        version=version,
                        confidence=max(signal.confidence for signal in tool_signals),
                        sources=sources,
                        metadata=metadata,
                    )
                )

            categories.append(StackCategory(name=category_name, tools=tuple(tools)))

        return cls(
            project_root=root,
            project_name=root.name,
            signals=signal_tuple,
            categories=tuple(categories),
        )

    def has(self, tool: str, category: str | None = None) -> bool:
        """
        Return whether a tool is present in the detected stack.

        Parameters
        ----------
        tool
            Tool name to check.
        category
            Optional category to restrict the check.

        Returns
        -------
        bool
            Whether the tool is present.
        """

        normalized_tool = tool.strip().lower()

        normalized_category = category.strip().lower() if category else None

        return any(
            signal.tool == normalized_tool
            and (normalized_category is None or signal.category == normalized_category)
            for signal in self.signals
        )

    def has_any(self, *tools: str, category: str | None = None) -> bool:
        """
        Return whether any of the provided tools are present.

        Parameters
        ----------
        tools
            Tool names to check.
        category
            Optional category to restrict the check.

        Returns
        -------
        bool
            Whether any tool is present.
        """

        return any(self.has(tool, category=category) for tool in tools)

    def by_category(self, category: str) -> tuple[ToolInfo, ...]:
        """
        Return aggregated tools for a category.

        Parameters
        ----------
        category
            Category name to look up.

        Returns
        -------
        tuple[ToolInfo, ...]
            Aggregated tools in the category.
        """

        normalized = category.strip().lower()

        for stack_category in self.categories:

            if stack_category.name == normalized:

                return stack_category.tools

        return ()
