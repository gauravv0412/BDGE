"""
Top-level dilemma analysis entrypoint.

``analyze_dilemma`` is the single public function.  It orchestrates five
sequential stages that map directly to the implementation phases in
design_spec.md §11:

    Stage 1  dimensions/scorer.py      — score all 8 ethical dimensions
    Stage 2  verdict/aggregator.py     — derive alignment_score, classification,
                                         confidence, and all prose verdict fields
    Stage 3  verses/retriever.py       — retrieve matched verse or closest_teaching
    Stage 4  counterfactuals/gen.py    — generate adharmic / dharmic variants
    Stage 5  share/layer.py            — build the shareable card / question

To implement a phase, replace the stub function in the relevant stage module.
The assembler below and all other stages remain untouched.
"""

from __future__ import annotations

import uuid

from app.core.models import WisdomizeEngineOutput
from app.core.types import EngineOutputDict
from app.counterfactuals.generator import generate_counterfactuals
from app.dimensions.scorer import score_dimensions
from app.share.layer import generate_share_layer
from app.verdict.aggregator import aggregate_verdict
from app.verses.retriever import retrieve_verse


def _normalize_dilemma(text: str) -> str:
    """
    Clamp *text* to JSON Schema length bounds (20–600 chars).

    Pads short input during development so pipeline calls always emit
    valid payloads even when fed a one-word test string.
    """
    t = text.strip()
    if len(t) < 20:
        pad = " [stub padding for schema minLength]"
        t = (t + pad)[:600]
    if len(t) < 20:
        t = (t + " " * (20 - len(t)))[:600]
    return t[:600]


def _run_pipeline(
    dilemma: str,
    *,
    dilemma_id: str | None = None,
) -> WisdomizeEngineOutput:
    """
    Execute all five stages and assemble a validated ``WisdomizeEngineOutput``.

    Private; called by ``analyze_dilemma`` (returns dict) and re-exported by
    ``engine/factory.py`` (returns the typed model, used in tests).
    """
    did = dilemma_id or f"live-{uuid.uuid4().hex[:16]}"
    text = _normalize_dilemma(dilemma)

    # Stage 1 — ethical dimension scores
    dimensions = score_dimensions(text)

    # Stage 2 — verdict: alignment_score, classification, confidence, prose
    verdict = aggregate_verdict(dimensions, text)

    # Stage 3 — verse match or closest_teaching fallback (XOR enforced below)
    verse_result = retrieve_verse(text, dimensions)

    # Stage 4 — counterfactual adharmic / dharmic variants
    counterfactuals = generate_counterfactuals(text, verdict)

    # Stage 5 — shareable card fields
    share = generate_share_layer(text, verdict)

    return WisdomizeEngineOutput(
        dilemma_id=did,
        dilemma=text,
        verdict_sentence=verdict["verdict_sentence"],
        classification=verdict["classification"],
        alignment_score=verdict["alignment_score"],
        confidence=verdict["confidence"],
        internal_driver=verdict["internal_driver"],
        core_reading=verdict["core_reading"],
        gita_analysis=verdict["gita_analysis"],
        verse_match=verse_result["verse_match"],
        closest_teaching=verse_result["closest_teaching"],
        if_you_continue=verdict["if_you_continue"],
        counterfactuals=counterfactuals,
        higher_path=verdict["higher_path"],
        ethical_dimensions=dimensions,
        missing_facts=verdict["missing_facts"],
        share_layer=share,
    )


def analyze_dilemma(dilemma: str) -> EngineOutputDict:
    """
    Analyze a user dilemma and return a schema-valid engine output dict.

    This is the public entrypoint used by scripts, evals, and the future API
    layer.  It calls ``_run_pipeline`` and serializes the result to plain JSON.
    """
    return _run_pipeline(dilemma).model_dump(mode="json")
