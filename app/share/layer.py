"""
Share-layer generation — stub.

Phase 1 target: generate the three shareable fields
(``anonymous_share_title``, ``card_quote``, ``reflective_question``) that are
consistent with the verdict (§9 of design_spec.md).

All three must align with the classification and verdict_sentence — no
shareable should chase engagement at the cost of contradicting the analysis.
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
