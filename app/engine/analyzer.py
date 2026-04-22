"""
Top-level dilemma analysis entrypoint.

``analyze_dilemma`` is the single public function.  ``_run_pipeline`` executes
three sequential stages:

    Stage 1  semantic/scorer.py        — LLM semantic interpretation: dimension
                                         scores, narrative prose, counterfactuals,
                                         share layer, ambiguity signals
    Stage 2  verdict/aggregator.py     — deterministic: alignment_score,
                                         classification, confidence, verdict_sentence
    Stage 3  verses/retriever.py       — curated verse match or closest_teaching

To wire in the live LLM for Stage 1, set ``use_stub=False`` in
``semantic_scorer`` once the API integration is ready.  Stages 2 and 3 are
independent of that change.
"""

from __future__ import annotations

import uuid

from app.core.models import (
    Counterfactuals,
    EthicalDimensions,
    IfYouContinue,
    InternalDriver,
    ShareLayer,
    WisdomizeEngineOutput,
)
from app.core.types import EngineOutputDict
from app.semantic.scorer import semantic_scorer
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
    Execute the three-stage pipeline and assemble a validated ``WisdomizeEngineOutput``.

    Private; called by ``analyze_dilemma`` (returns dict) and re-exported by
    ``engine/factory.py`` (returns the typed model, used in tests).
    """
    did = dilemma_id or f"live-{uuid.uuid4().hex[:16]}"
    text = _normalize_dilemma(dilemma)

    # Stage 1 — semantic interpretation (mode controlled by semantic scorer config)
    semantic = semantic_scorer(text)
    dimensions = EthicalDimensions.model_validate(semantic["ethical_dimensions"])
    ambiguity_flag = bool(semantic["ambiguity_flag"])
    missing_facts = list(semantic["missing_facts"])

    # Stage 2 — deterministic verdict layer
    verdict = aggregate_verdict(
        dimensions,
        text,
        ambiguity_can_flip_class=ambiguity_flag,
        missing_facts=missing_facts,
    )

    # Stage 3 — verse match or closest_teaching fallback (XOR enforced below)
    verse_result = retrieve_verse(text, dimensions)

    return WisdomizeEngineOutput(
        dilemma_id=did,
        dilemma=text,
        verdict_sentence=verdict["verdict_sentence"],
        classification=verdict["classification"],
        alignment_score=verdict["alignment_score"],
        confidence=verdict["confidence"],
        internal_driver=InternalDriver.model_validate(semantic["internal_driver"]),
        core_reading=str(semantic["core_reading"]),
        gita_analysis=str(semantic["gita_analysis"]),
        verse_match=verse_result["verse_match"],
        closest_teaching=verse_result["closest_teaching"],
        if_you_continue=IfYouContinue.model_validate(semantic["if_you_continue"]),
        counterfactuals=Counterfactuals.model_validate(semantic["counterfactuals"]),
        higher_path=str(semantic["higher_path"]),
        ethical_dimensions=dimensions,
        missing_facts=missing_facts,
        share_layer=ShareLayer.model_validate(semantic["share_layer"]),
    )


def analyze_dilemma(dilemma: str) -> EngineOutputDict:
    """
    Analyze a user dilemma and return a schema-valid engine output dict.

    This is the public entrypoint used by scripts, evals, and the future API
    layer.  It calls ``_run_pipeline`` and serializes the result to plain JSON.
    """
    return _run_pipeline(dilemma).model_dump(mode="json")
