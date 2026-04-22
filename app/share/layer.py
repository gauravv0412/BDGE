"""
Share-layer generation — stub (not currently called by the live pipeline).

The live pipeline obtains the share layer from ``app/semantic/scorer.py``,
which produces it as part of the LLM semantic payload.  This module is
retained for offline testing of share-layer shapes without invoking the
full semantic scorer.

If a deterministic or template-based share-layer generator is ever needed
alongside the LLM path, implement it here (§9 of design_spec.md).
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
