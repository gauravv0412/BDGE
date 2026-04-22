"""
Lightweight typing for engine boundaries. Pydantic shapes live in ``models``;
this module holds protocols and aliases so future modules (dimensions, verses,
share layer, counterfactuals) can plug in without circular imports.
"""

from __future__ import annotations

from typing import Any, Protocol, TypeAlias

# Serialized engine payload (JSON-compatible keys and values after ``model_dump``).
EngineOutputDict: TypeAlias = dict[str, Any]


class DilemmaAnalyzer(Protocol):
    """Contract for a component that turns user dilemma text into output JSON."""

    def analyze_dilemma(self, dilemma: str) -> EngineOutputDict:
        """Return one per-dilemma engine object as a plain dict (JSON-serializable)."""
        ...
