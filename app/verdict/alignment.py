"""
Deterministic rollup from eight dimension scores to ``alignment_score`` [-100, 100].

Each dimension contributes in [-5, 5]; the raw sum lies in [-40, 40].  We map
linearly to [-100, 100] per design_spec.md §2–3 (weighted aggregate, scaled).

Current weighting: all eight dimensions are equal-weight (weight = 1).  The spec
says "weighted sum" without specifying the weights; calibrated per-dimension
weights should be introduced in Phase 1 once real scorers are benchmarked.
"""

from __future__ import annotations

from app.core.models import EthicalDimensions

_RAW_SUM_MIN = -40
_RAW_SUM_MAX = 40


def compute_alignment_score(dimensions: EthicalDimensions) -> int:
    """
    Return ``alignment_score`` as a deterministic function of the eight scores.

    ``sum(scores)`` is mapped from ``[-40, 40]`` to ``[-100, 100]`` with
    rounding and clamping so the result always satisfies the JSON Schema bounds.
    """
    raw = sum(
        (
            dimensions.dharma_duty.score,
            dimensions.satya_truth.score,
            dimensions.ahimsa_nonharm.score,
            dimensions.nishkama_detachment.score,
            dimensions.shaucha_intent.score,
            dimensions.sanyama_restraint.score,
            dimensions.lokasangraha_welfare.score,
            dimensions.viveka_discernment.score,
        )
    )
    if raw <= _RAW_SUM_MIN:
        return -100
    if raw >= _RAW_SUM_MAX:
        return 100
    # Linear map: raw * (100/40) = raw * 2.5
    return int(round(raw * (100.0 / _RAW_SUM_MAX)))
