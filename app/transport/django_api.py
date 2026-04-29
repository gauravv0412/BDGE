"""
Thin Django transport adapter for the public engine boundary.
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from http import HTTPStatus

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

from app.core.models import EngineAnalyzeErrorResponse
from app.billing.services import check_presentation_quota, record_presentation_success
from app.engine.analyzer import build_engine_error_response, handle_engine_request
from app.engine.public_errors import PUBLIC_ERROR_CODES, PUBLIC_ERROR_HTTP_STATUS
from app.feedback import FeedbackValidationError, append_feedback_record, validate_feedback_payload
from app.presentation import build_card_copy_overlay, build_presentation_narrator, build_result_view_model

_SUPPORTED_CONTRACT_VERSIONS = {"1.0"}
_REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_LOGGER = logging.getLogger(__name__)


@require_POST
def analyze_view(request: HttpRequest) -> JsonResponse:
    """
    POST /api/v1/analyze

    Accepts JSON payload matching EngineAnalyzeRequest and returns the engine
    success/error envelope unchanged, with stable HTTP status mapping.
    """
    request_id = _extract_or_generate_request_id(request)
    start = time.perf_counter()
    contract_version = None
    status = int(HTTPStatus.INTERNAL_SERVER_ERROR)
    outcome = "engine_execution_failed"
    try:
        raw_payload = request.body.decode("utf-8") if request.body else "{}"
        payload = json.loads(raw_payload)
    except Exception:  # noqa: BLE001
        error = build_engine_error_response(
            code="request_validation_failed",
            message="Malformed JSON payload.",
        )
        status = int(HTTPStatus.BAD_REQUEST)
        outcome = "request_validation_failed"
        response = _json_response(error.model_dump(mode="json"), status=status, request_id=request_id)
        _emit_access_log(
            request_id=request_id,
            request=request,
            status_code=status,
            duration_ms=_duration_ms_since(start),
            contract_version=contract_version,
            outcome=outcome,
        )
        return response

    if isinstance(payload, dict):
        contract_version = _extract_contract_version(payload)

    try:
        body, status, outcome, contract_version = _execute_public_payload(payload)
    except Exception as exc:  # noqa: BLE001
        _emit_error_log(
            request_id=request_id,
            request=request,
            contract_version=contract_version,
            exc=exc,
        )
        fallback = build_engine_error_response(code="engine_execution_failed", message="unexpected transport failure")
        body = fallback.model_dump(mode="json")
        status = int(HTTPStatus.INTERNAL_SERVER_ERROR)
        outcome = "engine_execution_failed"

    response = _json_response(body, status=status, request_id=request_id)
    _emit_access_log(
        request_id=request_id,
        request=request,
        status_code=status,
        duration_ms=_duration_ms_since(start),
        contract_version=contract_version,
        outcome=outcome,
    )
    return response


@require_POST
def analyze_presentation_view(request: HttpRequest) -> JsonResponse:
    """
    POST /api/v1/analyze/presentation

    Internal browser-shell helper.  It preserves the public engine response under
    ``meta`` + ``output`` and adds a presentation-only view model for UI cards.
    The public ``/api/v1/analyze`` contract remains unchanged.
    """
    request_id = _extract_or_generate_request_id(request)
    if not _is_authenticated(request):
        return _auth_required_response(request_id=request_id)

    start = time.perf_counter()
    contract_version = None
    status = int(HTTPStatus.INTERNAL_SERVER_ERROR)
    outcome = "engine_execution_failed"
    try:
        raw_payload = request.body.decode("utf-8") if request.body else "{}"
        payload = json.loads(raw_payload)
    except Exception:  # noqa: BLE001
        error = build_engine_error_response(
            code="request_validation_failed",
            message="Malformed JSON payload.",
        )
        status = int(HTTPStatus.BAD_REQUEST)
        outcome = "request_validation_failed"
        response = _json_response(error.model_dump(mode="json"), status=status, request_id=request_id)
        _emit_access_log(
            request_id=request_id,
            request=request,
            status_code=status,
            duration_ms=_duration_ms_since(start),
            contract_version=contract_version,
            outcome=outcome,
        )
        return response

    if isinstance(payload, dict):
        contract_version = _extract_contract_version(payload)

    quota = check_presentation_quota(request.user)
    if not quota.allowed:
        error = build_engine_error_response(
            code="usage_limit_reached",
            message=quota.user_message or "You have reached your monthly analysis limit.",
        )
        status = int(HTTPStatus.TOO_MANY_REQUESTS)
        outcome = "usage_limit_reached"
        response = _json_response(error.model_dump(mode="json"), status=status, request_id=request_id)
        _emit_access_log(
            request_id=request_id,
            request=request,
            status_code=status,
            duration_ms=_duration_ms_since(start),
            contract_version=contract_version,
            outcome=outcome,
        )
        return response

    try:
        body, status, outcome, contract_version = _execute_public_payload(payload)
        if status == int(HTTPStatus.OK) and "output" in body:
            view_model = build_result_view_model(body)
            narrator, narrator_meta = build_presentation_narrator(
                engine_response=body,
                deterministic_presentation=view_model.model_dump(mode="json"),
            )
            presentation = view_model.model_dump(mode="json")
            presentation["cards"] = build_card_copy_overlay(
                output=body["output"],
                deterministic_presentation=presentation,
                narrator=narrator,
            )
            body = {
                "meta": body["meta"],
                "output": body["output"],
                "presentation": {
                    **presentation,
                    "narrator": narrator,
                    "narrator_meta": narrator_meta,
                },
            }
            try:
                record_presentation_success(user=request.user, response_body=body)
            except Exception as exc:  # noqa: BLE001
                _LOGGER.warning("presentation_finalize_failed", extra={"error_type": type(exc).__name__})
    except Exception as exc:  # noqa: BLE001
        _emit_error_log(
            request_id=request_id,
            request=request,
            contract_version=contract_version,
            exc=exc,
        )
        fallback = build_engine_error_response(code="engine_execution_failed", message="unexpected transport failure")
        body = fallback.model_dump(mode="json")
        status = int(HTTPStatus.INTERNAL_SERVER_ERROR)
        outcome = "engine_execution_failed"

    response = _json_response(body, status=status, request_id=request_id)
    if status == int(HTTPStatus.OK) and isinstance(body, dict) and "output" in body:
        refreshed = check_presentation_quota(request.user)
        if refreshed.limit > 0:
            response["X-Wisdomize-Usage"] = f"{refreshed.used}/{refreshed.limit}"
    _emit_access_log(
        request_id=request_id,
        request=request,
        status_code=status,
        duration_ms=_duration_ms_since(start),
        contract_version=contract_version,
        outcome=outcome,
    )
    return response


@require_POST
def feedback_view(request: HttpRequest) -> JsonResponse:
    """POST /api/v1/feedback with a small, safe, allowlisted payload."""
    request_id = _extract_or_generate_request_id(request)
    if not _is_authenticated(request):
        return _auth_required_response(request_id=request_id)

    try:
        raw_payload = request.body.decode("utf-8") if request.body else "{}"
        payload = json.loads(raw_payload)
        validated = validate_feedback_payload(payload)
        record = append_feedback_record(validated)
    except (FeedbackValidationError, json.JSONDecodeError, UnicodeDecodeError):
        return _json_response(
            {
                "ok": False,
                "error": {
                    "code": "feedback_validation_failed",
                    "message": "Feedback could not be saved. Please check the fields and try again.",
                },
            },
            status=int(HTTPStatus.BAD_REQUEST),
            request_id=request_id,
        )
    except Exception as exc:  # noqa: BLE001
        _emit_error_log(request_id=request_id, request=request, contract_version=None, exc=exc)
        return _json_response(
            {
                "ok": False,
                "error": {
                    "code": "feedback_storage_failed",
                    "message": "Feedback could not be saved right now. Please try again.",
                },
            },
            status=int(HTTPStatus.INTERNAL_SERVER_ERROR),
            request_id=request_id,
        )

    return _json_response(
        {"ok": True, "feedback_id": record["feedback_id"]},
        status=int(HTTPStatus.OK),
        request_id=request_id,
    )


def _validate_contract_version(payload: dict[str, object]) -> EngineAnalyzeErrorResponse | None:
    raw_version = payload.get("contract_version")
    if raw_version is None:
        return build_engine_error_response(
            code="request_validation_failed",
            message="contract_version is required.",
        )
    if not isinstance(raw_version, str):
        return build_engine_error_response(
            code="request_validation_failed",
            message="contract_version must be a non-empty string.",
        )
    contract_version = raw_version.strip()
    if not contract_version:
        return build_engine_error_response(
            code="request_validation_failed",
            message="contract_version must be a non-empty string.",
        )
    if contract_version not in _SUPPORTED_CONTRACT_VERSIONS:
        return build_engine_error_response(
            code="request_validation_failed",
            message=f"Unsupported contract_version '{contract_version}'. Supported versions: 1.0.",
        )
    return None


def _execute_public_payload(payload: object) -> tuple[dict[str, object], int, str, str | None]:
    if not isinstance(payload, dict):
        error = build_engine_error_response(
            code="request_validation_failed",
            message="JSON request body must be an object.",
        )
        return error.model_dump(mode="json"), int(HTTPStatus.BAD_REQUEST), "request_validation_failed", None

    contract_version = _extract_contract_version(payload)
    contract_error = _validate_contract_version(payload)
    if contract_error is not None:
        return (
            contract_error.model_dump(mode="json"),
            int(HTTPStatus.BAD_REQUEST),
            "request_validation_failed",
            contract_version,
        )

    result = handle_engine_request(payload)
    body = result.model_dump(mode="json")
    if "error" in body:
        code = str(body["error"].get("code", "engine_execution_failed"))
        status = int(PUBLIC_ERROR_HTTP_STATUS.get(code, HTTPStatus.INTERNAL_SERVER_ERROR))
        outcome = code if code in PUBLIC_ERROR_CODES else "engine_execution_failed"
        return body, status, outcome, contract_version
    return body, int(HTTPStatus.OK), "success", contract_version


def _extract_or_generate_request_id(request: HttpRequest) -> str:
    inbound = request.headers.get(_REQUEST_ID_HEADER, "")
    if isinstance(inbound, str):
        candidate = inbound.strip()
        if _REQUEST_ID_PATTERN.fullmatch(candidate):
            return candidate
    return uuid.uuid4().hex


def _json_response(body: dict[str, object], *, status: int, request_id: str) -> JsonResponse:
    response = JsonResponse(body, status=status)
    response[_REQUEST_ID_HEADER] = request_id
    return response


def _auth_required_response(*, request_id: str) -> JsonResponse:
    return _json_response(
        {
            "ok": False,
            "error": {
                "code": "authentication_required",
                "message": "Please log in to use Wisdomize.",
            },
        },
        status=int(HTTPStatus.UNAUTHORIZED),
        request_id=request_id,
    )


def _is_authenticated(request: HttpRequest) -> bool:
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated)


def _extract_contract_version(payload: dict[str, object]) -> str | None:
    raw_version = payload.get("contract_version")
    if isinstance(raw_version, str):
        stripped = raw_version.strip()
        if stripped:
            return stripped
    return None


def _duration_ms_since(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _emit_access_log(
    *,
    request_id: str,
    request: HttpRequest,
    status_code: int,
    duration_ms: int,
    contract_version: str | None,
    outcome: str,
) -> None:
    _LOGGER.info(
        json.dumps(
            {
            "event": "transport.access",
            "request_id": request_id,
            "path": request.path,
            "method": request.method,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "contract_version": contract_version,
            "outcome": outcome,
            },
            sort_keys=True,
        )
    )


def _emit_error_log(
    *,
    request_id: str,
    request: HttpRequest,
    contract_version: str | None,
    exc: Exception,
) -> None:
    _LOGGER.exception(
        json.dumps(
            {
            "event": "transport.error",
            "request_id": request_id,
            "path": request.path,
            "method": request.method,
            "contract_version": contract_version,
            "error_type": type(exc).__name__,
            "error_message": str(exc)[:500],
            },
            sort_keys=True,
        )
    )
