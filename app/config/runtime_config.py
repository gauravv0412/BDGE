"""Config-driven product limits, plan catalog, and safe runtime knobs.

Precedence for plan definitions:
  1. ``WISDOMIZE_PLANS_JSON`` (inline JSON object)
  2. ``WISDOMIZE_PLANS_CONFIG_PATH`` (path to JSON file)
  3. Built-in defaults

Environment overrides for runtime knobs (see ``docs/runtime_config.md``).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]

_DEFAULT_PLANS_RAW: dict[str, dict[str, Any]] = {
    "free": {
        "label": "Free",
        "monthly_analysis_limit": 5,
        "price_display": "₹0",
        "enabled": True,
    },
    "plus": {
        "label": "Plus",
        "monthly_analysis_limit": 100,
        "price_display": "₹199/month",
        "enabled": True,
    },
    "pro": {
        "label": "Pro",
        "monthly_analysis_limit": 500,
        "price_display": "₹499/month",
        "enabled": True,
    },
}


@dataclass(frozen=True)
class PlanDefinition:
    key: str
    label: str
    monthly_analysis_limit: int
    price_display: str
    enabled: bool


@dataclass(frozen=True)
class RuntimeConfig:
    """Mutable-via-env knobs; read through this dataclass only from product code."""

    verse_match_score_threshold: int
    max_missing_facts: int
    feedback_comment_max_len: int
    dashboard_history_page_size: int
    presentation_llm_timeout_seconds: int


def _env_int(name: str, default: int, *, minimum: int | None = None, maximum: int | None = None) -> int:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        v = int(str(raw).strip())
    except ValueError:
        return default
    if minimum is not None:
        v = max(minimum, v)
    if maximum is not None:
        v = min(maximum, v)
    return v


def _parse_plan_entry(key: str, raw: Mapping[str, Any]) -> PlanDefinition:
    if not isinstance(key, str) or not key.strip():
        raise ValueError("plan keys must be non-empty strings")
    label = str(raw.get("label", "")).strip()
    if not label:
        raise ValueError(f"plan {key!r}: missing label")
    try:
        limit = int(raw.get("monthly_analysis_limit", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"plan {key!r}: monthly_analysis_limit must be int") from exc
    if limit < 0:
        raise ValueError(f"plan {key!r}: monthly_analysis_limit must be >= 0")
    price_display = str(raw.get("price_display", "")).strip()
    if not price_display:
        raise ValueError(f"plan {key!r}: missing price_display")
    enabled = bool(raw.get("enabled", True))
    return PlanDefinition(
        key=key.strip(),
        label=label,
        monthly_analysis_limit=limit,
        price_display=price_display,
        enabled=enabled,
    )


def _merge_plan_dicts(base: dict[str, dict[str, Any]], overlay: dict[str, Any]) -> dict[str, dict[str, Any]]:
    merged = {k: dict(v) for k, v in base.items()}
    for key, entry in overlay.items():
        if not isinstance(key, str):
            raise ValueError("plan config keys must be strings")
        if not isinstance(entry, dict):
            raise ValueError(f"plan {key!r}: value must be an object")
        if key in merged:
            merged[key].update(entry)
        else:
            merged[key] = dict(entry)
    return merged


def _load_plans_from_env() -> dict[str, PlanDefinition]:
    inline = os.environ.get("WISDOMIZE_PLANS_JSON", "").strip()
    path_raw = os.environ.get("WISDOMIZE_PLANS_CONFIG_PATH", "").strip()
    data: dict[str, Any] = dict(_DEFAULT_PLANS_RAW)
    if inline:
        try:
            parsed = json.loads(inline)
        except json.JSONDecodeError as exc:
            raise ValueError(f"WISDOMIZE_PLANS_JSON is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("WISDOMIZE_PLANS_JSON must be a JSON object keyed by plan id")
        data = _merge_plan_dicts(data, parsed)
    elif path_raw:
        path = Path(path_raw).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"WISDOMIZE_PLANS_CONFIG_PATH not found: {path}")
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"plan config file {path} is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("plan config file must contain a JSON object keyed by plan id")
        data = _merge_plan_dicts(data, parsed)

    required = {"free", "plus", "pro"}
    missing = required - set(data)
    if missing:
        raise ValueError(f"plan definitions missing required keys: {sorted(missing)}")
    return {k: _parse_plan_entry(k, data[k]) for k in sorted(data)}


_plans_cache: dict[str, PlanDefinition] | None = None
_plans_cache_sig: str | None = None


def _plans_env_signature() -> str:
    return "|".join(
        [
            os.environ.get("WISDOMIZE_PLANS_JSON", ""),
            os.environ.get("WISDOMIZE_PLANS_CONFIG_PATH", ""),
        ]
    )


def clear_runtime_config_caches() -> None:
    """Clear cached plan definitions (tests / reload)."""
    global _plans_cache, _plans_cache_sig
    _plans_cache = None
    _plans_cache_sig = None


def get_plan_definitions() -> dict[str, PlanDefinition]:
    global _plans_cache, _plans_cache_sig
    sig = _plans_env_signature()
    if _plans_cache is not None and sig == _plans_cache_sig:
        return _plans_cache
    loaded = _load_plans_from_env()
    _plans_cache = loaded
    _plans_cache_sig = sig
    return loaded


def get_plan(plan_key: str) -> PlanDefinition:
    plans = get_plan_definitions()
    if plan_key not in plans:
        raise KeyError(f"unknown plan key: {plan_key!r}")
    return plans[plan_key]


def get_runtime_config() -> RuntimeConfig:
    """Read current runtime knobs from environment (no on-disk cache)."""
    from app.presentation.config import load_presentation_llm_config

    llm_cfg = load_presentation_llm_config()
    return RuntimeConfig(
        verse_match_score_threshold=_env_int("WISDOMIZE_VERSE_MATCH_SCORE_THRESHOLD", 6, minimum=1, maximum=20),
        max_missing_facts=_env_int("WISDOMIZE_MAX_MISSING_FACTS", 6, minimum=1, maximum=6),
        feedback_comment_max_len=_env_int("WISDOMIZE_FEEDBACK_COMMENT_MAX_LEN", 500, minimum=1, maximum=4000),
        dashboard_history_page_size=_env_int("WISDOMIZE_DASHBOARD_HISTORY_PAGE_SIZE", 20, minimum=1, maximum=200),
        presentation_llm_timeout_seconds=int(llm_cfg.timeout_seconds),
    )


def get_verse_match_score_threshold() -> int:
    return get_runtime_config().verse_match_score_threshold


def get_feedback_comment_max_len() -> int:
    return get_runtime_config().feedback_comment_max_len
