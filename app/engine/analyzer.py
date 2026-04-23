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

Counterfactuals in the final output are built by ``app/counterfactuals/deterministic.py``;
``share_layer`` by ``app/share/deterministic.py``; ``if_you_continue`` and ``higher_path``
by ``app/narrative/deterministic.py``.  Stage 1 semantic JSON still carries placeholder-shaped
fields for those keys for validation only.

To wire in the live LLM for Stage 1, set ``use_stub=False`` in
``semantic_scorer`` once the API integration is ready.  Stages 2 and 3 are
independent of that change.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.core.models import (
    Counterfactuals,
    EngineAnalyzeErrorResponse,
    EngineAnalyzeRequest,
    EngineAnalyzeResponse,
    EngineError,
    EngineResponseMeta,
    EthicalDimensions,
    IfYouContinue,
    InternalDriver,
    ShareLayer,
    WisdomizeEngineOutput,
)
from app.core.types import EngineOutputDict
from app.counterfactuals.deterministic import build_refined_counterfactuals
from app.semantic.scorer import load_semantic_config, semantic_scorer
from app.narrative.deterministic import build_refined_higher_path, build_refined_if_you_continue
from app.share.deterministic import build_refined_share_layer
from app.verdict.aggregator import aggregate_verdict
from app.verses.retriever import retrieve_verse
from app.verses.scorer import RetrievalContext
from app.verses.types import DimensionKey

_CONTRACT_VERSION = "1.0"
_ENGINE_VERSION = "2.1"


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
        semantic_verdict_sentence=str(semantic.get("verdict_sentence", "")).strip() or None,
        ambiguity_can_flip_class=ambiguity_flag,
        missing_facts=missing_facts,
    )

    # Stage 3 — verse match or closest_teaching fallback (XOR enforced below)
    context_override = _build_retrieval_context_override(
        dilemma_id=did,
        dilemma=text,
        semantic=semantic,
        verdict_classification=str(verdict["classification"]),
        dimensions=dimensions,
        missing_facts=missing_facts,
    )
    verse_result = retrieve_verse(text, dimensions, context_override=context_override)

    internal_driver_raw = semantic.get("internal_driver")
    cf_dict = build_refined_counterfactuals(
        dilemma=text,
        classification=str(verdict["classification"]),
        internal_driver=internal_driver_raw if isinstance(internal_driver_raw, dict) else None,
        dimensions=dimensions,
        missing_facts=missing_facts,
    )
    counterfactuals_model = Counterfactuals.model_validate(cf_dict)
    share_dict = build_refined_share_layer(
        dilemma=text,
        classification=str(verdict["classification"]),
        verdict_sentence=str(verdict["verdict_sentence"]),
        internal_driver=internal_driver_raw if isinstance(internal_driver_raw, dict) else None,
        core_reading=str(semantic["core_reading"]),
        gita_analysis=str(semantic["gita_analysis"]),
        verse_match=verse_result["verse_match"],
        closest_teaching=verse_result["closest_teaching"],
        counterfactuals=counterfactuals_model,
        missing_facts=missing_facts,
    )
    iyc_dict = build_refined_if_you_continue(
        dilemma=text,
        classification=str(verdict["classification"]),
        internal_driver=internal_driver_raw if isinstance(internal_driver_raw, dict) else None,
        dimensions=dimensions,
        missing_facts=missing_facts,
        counterfactuals=counterfactuals_model,
        verse_match=verse_result["verse_match"],
        closest_teaching=verse_result["closest_teaching"],
    )
    higher_path_refined = build_refined_higher_path(
        dilemma=text,
        classification=str(verdict["classification"]),
        internal_driver=internal_driver_raw if isinstance(internal_driver_raw, dict) else None,
        dimensions=dimensions,
        missing_facts=missing_facts,
        counterfactuals=counterfactuals_model,
        verse_match=verse_result["verse_match"],
        closest_teaching=verse_result["closest_teaching"],
    )

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
        if_you_continue=IfYouContinue.model_validate(iyc_dict),
        counterfactuals=counterfactuals_model,
        higher_path=higher_path_refined,
        ethical_dimensions=dimensions,
        missing_facts=missing_facts,
        share_layer=ShareLayer.model_validate(share_dict),
    )


def analyze_dilemma(dilemma: str) -> EngineOutputDict:
    """
    Analyze a user dilemma and return a schema-valid engine output dict.

    This is the public entrypoint used by scripts, evals, and the future API
    layer.  It calls ``_run_pipeline`` and serializes the result to plain JSON.
    """
    return _run_pipeline(dilemma).model_dump(mode="json")


def analyze_dilemma_request(request: EngineAnalyzeRequest) -> EngineAnalyzeResponse:
    """
    Public request/response contract entrypoint for API boundary wiring.

    Orchestrates:
    - Stage 1: ``app.semantic.scorer.semantic_scorer``
    - Stage 2: ``app.verdict.aggregator.aggregate_verdict``
    - Stage 3: ``app.verses.retriever.retrieve_verse``
    - Deterministic narrative, counterfactual, and share overlays
    """
    output = _run_pipeline(request.dilemma, dilemma_id=request.dilemma_id)
    return EngineAnalyzeResponse(
        meta=_build_response_meta(),
        output=output,
    )


def handle_engine_request(
    payload: dict[str, Any],
) -> EngineAnalyzeResponse | EngineAnalyzeErrorResponse:
    """
    API-facing boundary handler that validates request and returns a stable envelope.

    Unlike ``analyze_dilemma_request``, this function does not raise validation or
    runtime exceptions to callers; it returns ``EngineAnalyzeErrorResponse`` instead.
    """
    try:
        request = EngineAnalyzeRequest.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        return EngineAnalyzeErrorResponse(
            meta=_build_response_meta(),
            error=EngineError(
                code="request_validation_failed",
                message=str(exc),
            ),
        )
    try:
        return analyze_dilemma_request(request)
    except Exception as exc:  # noqa: BLE001
        return EngineAnalyzeErrorResponse(
            meta=_build_response_meta(),
            error=EngineError(
                code="engine_execution_failed",
                message=str(exc),
            ),
        )


def _build_response_meta() -> EngineResponseMeta:
    return EngineResponseMeta(
        contract_version=_CONTRACT_VERSION,
        engine_version=_ENGINE_VERSION,
        semantic_mode_default=_semantic_mode_default(),
    )


def _semantic_mode_default() -> str:
    cfg = load_semantic_config()
    if bool(cfg.get("use_stub_default", True)):
        return "stub_default"
    return "live_default"


def _top_dominant_dimensions(
    dimensions: EthicalDimensions,
    *,
    min_score: int = 2,
) -> list[DimensionKey]:
    pairs = [
        ("dharma_duty", dimensions.dharma_duty.score),
        ("satya_truth", dimensions.satya_truth.score),
        ("ahimsa_nonharm", dimensions.ahimsa_nonharm.score),
        ("nishkama_detachment", dimensions.nishkama_detachment.score),
        ("shaucha_intent", dimensions.shaucha_intent.score),
        ("sanyama_restraint", dimensions.sanyama_restraint.score),
        ("lokasangraha_welfare", dimensions.lokasangraha_welfare.score),
        ("viveka_discernment", dimensions.viveka_discernment.score),
    ]
    ranked = sorted(pairs, key=lambda item: item[1], reverse=True)
    return [name for name, score in ranked if score >= min_score]


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _build_retrieval_context_override(
    *,
    dilemma_id: str,
    dilemma: str,
    semantic: dict[str, object],
    verdict_classification: str,
    dimensions: EthicalDimensions,
    missing_facts: list[str],
) -> RetrievalContext:
    internal_driver = semantic.get("internal_driver")
    primary_driver = ""
    hidden_risk = ""
    if isinstance(internal_driver, dict):
        primary_driver = str(internal_driver.get("primary", "")).strip()
        hidden_risk = str(internal_driver.get("hidden_risk", "")).strip()

    return RetrievalContext(
        dilemma_id=dilemma_id,
        classification=verdict_classification,
        primary_driver=primary_driver,
        hidden_risk=hidden_risk,
        dominant_dimensions=_top_dominant_dimensions(dimensions),
        theme_tags=_as_str_list(semantic.get("theme_tags")) or [],
        applies_signals=_as_str_list(semantic.get("applies_signals")) or [],
        blocker_signals=_as_str_list(semantic.get("blocker_signals")) or [],
        missing_facts=missing_facts,
    )
