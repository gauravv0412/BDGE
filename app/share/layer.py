"""
Share-layer generation — stub (not currently called by the live pipeline).

The live pipeline overlays ``share_layer`` in ``app/engine/analyzer.py`` using
``app/share/deterministic.build_refined_share_layer``.  Semantic JSON still
includes share-shaped fields for schema validation.

This module remains a small offline stub for tests that import
``generate_share_layer`` directly.
"""

from __future__ import annotations

from app.core.models import ShareLayer
from app.verdict.aggregator import VerdictResult


def generate_share_layer(dilemma: str, verdict: VerdictResult) -> ShareLayer:
    """
    Build the share layer for *dilemma* given the resolved *verdict*.

    Stub returns clearly-marked placeholder strings.  Real implementation will
    derive ``card_quote`` from ``verdict["verdict_sentence"]`` and tailor
    ``reflective_question`` to ``verdict["classification"]``.
    """
    return ShareLayer(
        anonymous_share_title="[STUB] Overheard: the app said …",
        card_quote="[STUB] Card-sized takeaway.",
        reflective_question="[STUB] What would change if you saw this clearly?",
    )
