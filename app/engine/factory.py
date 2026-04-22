"""
Typed model builder — thin wrapper kept for test compatibility.

``build_placeholder_response`` returns a ``WisdomizeEngineOutput`` (typed model)
rather than a plain dict.  Tests that need to inspect field types or call
``model_dump`` directly import this instead of ``analyze_dilemma``.

All stub data now lives in the stage modules it logically belongs to:
  - app/dimensions/scorer.py
  - app/verdict/aggregator.py
  - app/verses/retriever.py
  - app/counterfactuals/generator.py
  - app/share/layer.py
"""

from __future__ import annotations

from app.core.models import WisdomizeEngineOutput
from app.engine.analyzer import _run_pipeline


def build_placeholder_response(
    dilemma: str,
    *,
    dilemma_id: str | None = None,
) -> WisdomizeEngineOutput:
    """
    Return a schema-valid ``WisdomizeEngineOutput`` for *dilemma*.

    Delegates entirely to ``_run_pipeline``; the only reason this function
    exists is to provide a typed-model return for callers (tests, evals) that
    need the Pydantic model rather than a serialized dict.
    """
    return _run_pipeline(dilemma, dilemma_id=dilemma_id)
