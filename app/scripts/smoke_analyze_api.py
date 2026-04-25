"""
In-process smoke check for POST /api/v1/analyze (no live HTTP server required).

Uses the same Django settings module as transport tests. Verifies HTTP 200,
``X-Request-ID``, and a stable success envelope (``meta`` + ``output``).

The engine's semantic stage is **forced to the stub** for this script only
(``unittest.mock.patch``), so no Anthropic key or network is required regardless
of ``use_stub_default`` in ``config/app_config.json``.

Usage (from repo root)::

    PYTHONPATH=. .venv/bin/python -m app.scripts.smoke_analyze_api
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

_REQUEST_ID_HEADER = "X-Request-ID"

# Keep aligned with transport contract tests (valid stub path, schema-safe length).
_SMOKE_PAYLOAD: dict[str, Any] = {
    "dilemma": "Another synthetic dilemma for the analyzer stub path, long enough for schema.",
    "dilemma_id": "smoke-analyze-01",
    "contract_version": "1.0",
}


def run_smoke() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")

    import django
    from unittest import mock

    django.setup()

    from app.semantic import scorer as semantic_scorer_mod

    def _semantic_stub_only(dilemma: str, *, use_stub: bool | None = None) -> dict[str, Any]:
        return semantic_scorer_mod.semantic_scorer(dilemma, use_stub=True)

    from django.test import Client

    client = Client()
    with mock.patch("app.engine.analyzer.semantic_scorer", _semantic_stub_only):
        response = client.post(
            "/api/v1/analyze",
            data=json.dumps(_SMOKE_PAYLOAD),
            content_type="application/json",
            HTTP_X_REQUEST_ID="smoke-req-1",
        )
    if response.status_code != 200:
        print(f"Expected HTTP 200, got {response.status_code}: {response.content!r}", file=sys.stderr)
        return 1
    rid = response.headers.get(_REQUEST_ID_HEADER)
    if not rid:
        print(f"Missing {_REQUEST_ID_HEADER} header.", file=sys.stderr)
        return 1
    if rid != "smoke-req-1":
        print(f"Expected echo request id, got {rid!r}.", file=sys.stderr)
        return 1

    body = response.json()
    if set(body.keys()) != {"meta", "output"}:
        print(f"Unexpected top-level keys: {sorted(body.keys())}", file=sys.stderr)
        return 1
    meta = body["meta"]
    required_meta = {"contract_version", "engine_version", "semantic_mode_default"}
    missing = required_meta - set(meta.keys())
    if missing:
        print(f"Smoke: meta missing required keys: {sorted(missing)}", file=sys.stderr)
        return 1
    if meta.get("contract_version") != "1.0":
        print("meta.contract_version must be 1.0 for this smoke payload.", file=sys.stderr)
        return 1

    out = body["output"]
    if not isinstance(out, dict) or "dilemma_id" not in out:
        print("output must be an object including dilemma_id.", file=sys.stderr)
        return 1
    if out.get("dilemma_id") != _SMOKE_PAYLOAD["dilemma_id"]:
        print("output.dilemma_id mismatch.", file=sys.stderr)
        return 1

    return 0


def main() -> int:
    return run_smoke()


if __name__ == "__main__":
    raise SystemExit(main())
