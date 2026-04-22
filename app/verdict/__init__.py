"""Verdict aggregation — alignment, classification, confidence, prose assembly."""

from app.verdict.aggregator import VerdictResult, aggregate_verdict
from app.verdict.alignment import compute_alignment_score
from app.verdict.classification import resolve_classification
from app.verdict.confidence import compute_confidence

__all__ = [
    "VerdictResult",
    "aggregate_verdict",
    "compute_alignment_score",
    "compute_confidence",
    "resolve_classification",
]
