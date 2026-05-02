"""Normalized stack models produced by Akira detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class Signal:
    """A single detection signal emitted by a detector."""

    tool: str
    category: str
    version: str | None = None
    confidence: float = 1.0
    source: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            msg = "Signal confidence must be between 0.0 and 1.0."
            raise ValueError(msg)

        object.__setattr__(self, "tool", self.tool.strip().lower())
        object.__setattr__(self, "category", self.category.strip().lower())
        object.__setattr__(self, "source", self.source.strip())
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def identity(self) -> tuple[str, str, str | None, str]:
        """Return the stable identity used to deduplicate equivalent signals."""
        return (self.tool, self.category, self.version, self.source)


@dataclass(frozen=True)
class ToolInfo:
    """Aggregated view of one detected tool."""

    name: str
    category: str
    version: str | None = None
    confidence: float = 1.0
    sources: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class StackCategory:
    """A group of tools that belong to the same stack category."""

    name: str
    tools: tuple[ToolInfo, ...] = ()

    def has(self, tool: str) -> bool:
        """Return whether this category contains a tool."""
        normalized = tool.strip().lower()
        return any(item.name == normalized for item in self.tools)


@dataclass(frozen=True)
class StackInfo:
    """Normalized stack information for a project."""

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
        """Build a normalized stack model from detector signals."""
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
            for (tool_name, version), tool_signals in sorted(grouped[category_name].items()):
                sources = tuple(
                    dict.fromkeys(signal.source for signal in tool_signals if signal.source)
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
        """Return whether a tool is present in the detected stack."""
        normalized_tool = tool.strip().lower()
        normalized_category = category.strip().lower() if category else None

        return any(
            signal.tool == normalized_tool
            and (normalized_category is None or signal.category == normalized_category)
            for signal in self.signals
        )

    def has_any(self, *tools: str, category: str | None = None) -> bool:
        """Return whether any of the provided tools are present."""
        return any(self.has(tool, category=category) for tool in tools)

    def by_category(self, category: str) -> tuple[ToolInfo, ...]:
        """Return aggregated tools for a category."""
        normalized = category.strip().lower()
        for stack_category in self.categories:
            if stack_category.name == normalized:
                return stack_category.tools

        return ()
