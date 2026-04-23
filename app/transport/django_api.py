"""
Thin Django transport adapter for the public engine boundary.
"""

from __future__ import annotations

import json
from http import HTTPStatus

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

from app.engine.analyzer import build_engine_error_response, handle_engine_request

_STATUS_BY_ERROR_CODE = {
    "request_validation_failed": HTTPStatus.BAD_REQUEST,
    "engine_execution_failed": HTTPStatus.INTERNAL_SERVER_ERROR,
}


@require_POST
def analyze_view(request: HttpRequest) -> JsonResponse:
    """
    POST /api/v1/analyze

    Accepts JSON payload matching EngineAnalyzeRequest and returns the engine
    success/error envelope unchanged, with stable HTTP status mapping.
    """
    try:
        raw_payload = request.body.decode("utf-8") if request.body else "{}"
        payload = json.loads(raw_payload)
    except Exception:  # noqa: BLE001
        error = build_engine_error_response(
            code="request_validation_failed",
            message="Malformed JSON payload.",
        )
        return JsonResponse(error.model_dump(mode="json"), status=HTTPStatus.BAD_REQUEST)

    if not isinstance(payload, dict):
        error = build_engine_error_response(
            code="request_validation_failed",
            message="JSON request body must be an object.",
        )
        return JsonResponse(error.model_dump(mode="json"), status=HTTPStatus.BAD_REQUEST)

    result = handle_engine_request(payload)
    body = result.model_dump(mode="json")
    if "error" in body:
        code = str(body["error"].get("code", "engine_execution_failed"))
        status = int(_STATUS_BY_ERROR_CODE.get(code, HTTPStatus.INTERNAL_SERVER_ERROR))
    else:
        status = int(HTTPStatus.OK)
    return JsonResponse(body, status=status)
