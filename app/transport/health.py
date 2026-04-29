"""Minimal public health probe for load balancers (no engine, DB, or LLM)."""

from __future__ import annotations

from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def healthz(_request):  # type: ignore[no-untyped-def]
    return JsonResponse({"ok": True, "service": "wisdomize"})
