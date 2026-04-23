"""Counterfactual generation — Phase 3 implementation target."""

from app.counterfactuals.deterministic import build_refined_counterfactuals, detect_dilemma_family
from app.counterfactuals.generator import generate_counterfactuals

__all__ = ["build_refined_counterfactuals", "detect_dilemma_family", "generate_counterfactuals"]
