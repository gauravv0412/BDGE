"""Centralized product and runtime configuration (Step 38A)."""

from app.config.runtime_config import (
    PlanDefinition,
    clear_runtime_config_caches,
    get_feedback_comment_max_len,
    get_plan,
    get_plan_definitions,
    get_runtime_config,
    get_verse_match_score_threshold,
)

__all__ = [
    "PlanDefinition",
    "clear_runtime_config_caches",
    "get_feedback_comment_max_len",
    "get_plan",
    "get_plan_definitions",
    "get_runtime_config",
    "get_verse_match_score_threshold",
]
