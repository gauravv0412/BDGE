"""Runtime configuration for presentation narrator provider."""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_loaded_dotenv_paths: set[Path] = set()
_ROOT = Path(__file__).resolve().parents[2]
_LOCAL_SECRETS_PATH = _ROOT / "config" / "local_secrets.json"
_ANTHROPIC_DEFAULT_BASE_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_DEFAULT_MODEL = "claude-haiku-4-5"
_ANTHROPIC_DEFAULT_TIMEOUT_SECONDS = 20
_VALID_PROVIDERS = {"none", "openai_compatible", "anthropic"}


def _maybe_load_dotenv_for_local_dev() -> None:
    """
    Load repo-root ``.env`` into ``os.environ`` for local development only.

    - Uses ``python-dotenv`` when installed; otherwise no-op.
    - ``override=False``: real process environment always wins over ``.env``.
    - Skipped when ``WISDOMIZE_LOAD_DOTENV`` is ``0``/``false``/``no``/``off``.
    - Each resolved ``.env`` path is loaded at most once per process.
    """
    raw = os.getenv("WISDOMIZE_LOAD_DOTENV", "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    repo_root = Path(__file__).resolve().parents[2]
    env_path = repo_root / ".env"
    if not env_path.is_file():
        return
    resolved = env_path.resolve()
    if resolved in _loaded_dotenv_paths:
        return
    load_dotenv(resolved, override=False)
    _loaded_dotenv_paths.add(resolved)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw.strip())
    except Exception:  # noqa: BLE001
        return default
    return value if value > 0 else default


def _load_local_secrets(secrets_path: Path | None = None) -> dict[str, Any]:
    """Read optional local developer secrets without requiring the file to exist."""
    path = secrets_path or _LOCAL_SECRETS_PATH
    try:
        with path.open(encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        return {}
    if not isinstance(raw, dict):
        return {}
    return raw


def _local_value(secrets: dict[str, Any], name: str) -> str | None:
    raw = secrets.get(name)
    if raw is None:
        return None
    return str(raw).strip()


def _local_bool(secrets: dict[str, Any], name: str, default: bool) -> bool:
    raw = _local_value(secrets, name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _local_int(secrets: dict[str, Any], name: str, default: int) -> int:
    raw = _local_value(secrets, name)
    if raw is None:
        return default
    try:
        value = int(raw.strip())
    except Exception:  # noqa: BLE001
        return default
    return value if value > 0 else default


def _configured_value(
    *,
    env_name: str,
    secrets: dict[str, Any],
    default: str,
) -> str:
    raw = os.getenv(env_name)
    if raw is not None:
        return raw.strip()
    local = _local_value(secrets, env_name)
    if local is not None:
        return local
    return default


def _configured_bool(
    *,
    env_name: str,
    secrets: dict[str, Any],
    default: bool,
) -> bool:
    if os.getenv(env_name) is not None:
        return _env_bool(env_name, default)
    return _local_bool(secrets, env_name, default)


def _configured_int(
    *,
    env_name: str,
    secrets: dict[str, Any],
    default: int,
) -> int:
    if os.getenv(env_name) is not None:
        return _env_int(env_name, default)
    return _local_int(secrets, env_name, default)


def _nested_anthropic_defaults(secrets: dict[str, Any]) -> dict[str, str]:
    anthropic = secrets.get("anthropic")
    if not isinstance(anthropic, dict):
        return {}
    api_key = anthropic.get("api_key")
    if not isinstance(api_key, str) or not api_key.strip():
        return {}
    return {
        "provider": "anthropic",
        "model": str(anthropic.get("model") or _ANTHROPIC_DEFAULT_MODEL).strip(),
        "base_url": str(anthropic.get("base_url") or _ANTHROPIC_DEFAULT_BASE_URL).strip(),
        "api_key": api_key.strip(),
        "timeout_seconds": str(anthropic.get("timeout_seconds") or _ANTHROPIC_DEFAULT_TIMEOUT_SECONDS).strip(),
    }


@dataclass(frozen=True)
class PresentationLLMConfig:
    enabled: bool = True
    shadow: bool = False
    provider: str = "none"
    model: str = "gpt-4o-mini"
    timeout_seconds: int = 4
    repair_enabled: bool = True
    max_repair_attempts: int = 1
    base_url: str = ""
    api_key: str = field(default="", repr=False)


def load_presentation_llm_config(*, local_secrets_path: Path | None = None) -> PresentationLLMConfig:
    """Read presentation LLM settings from env, ``.env``, and optional local secrets."""
    _maybe_load_dotenv_for_local_dev()
    secrets = _load_local_secrets(local_secrets_path)
    nested_defaults = _nested_anthropic_defaults(secrets)
    provider = (
        _configured_value(
            env_name="PRESENTATION_LLM_PROVIDER",
            secrets=secrets,
            default=nested_defaults.get("provider", "none"),
        )
        or "none"
    ).lower()
    model = _configured_value(
        env_name="PRESENTATION_LLM_MODEL",
        secrets=secrets,
        default=nested_defaults.get("model", "gpt-4o-mini"),
    ) or "gpt-4o-mini"
    return PresentationLLMConfig(
        enabled=_configured_bool(env_name="PRESENTATION_LLM_ENABLED", secrets=secrets, default=True),
        shadow=_configured_bool(env_name="PRESENTATION_LLM_SHADOW", secrets=secrets, default=False),
        provider=provider if provider in _VALID_PROVIDERS else "none",
        model=model.strip(),
        timeout_seconds=_configured_int(
            env_name="PRESENTATION_LLM_TIMEOUT_SECONDS",
            secrets=secrets,
            default=int(nested_defaults.get("timeout_seconds", "4")),
        ),
        repair_enabled=_configured_bool(env_name="PRESENTATION_LLM_REPAIR_ENABLED", secrets=secrets, default=True),
        max_repair_attempts=min(
            _configured_int(env_name="PRESENTATION_LLM_MAX_REPAIR_ATTEMPTS", secrets=secrets, default=1),
            1,
        ),
        base_url=_configured_value(
            env_name="PRESENTATION_LLM_BASE_URL",
            secrets=secrets,
            default=nested_defaults.get("base_url", ""),
        ),
        api_key=_configured_value(
            env_name="PRESENTATION_LLM_API_KEY",
            secrets=secrets,
            default=nested_defaults.get("api_key", ""),
        ),
    )
