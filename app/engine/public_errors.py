"""Versioned public error taxonomy and message policy for API boundary."""

from __future__ import annotations

from http import HTTPStatus

PUBLIC_ERROR_CONTRACT_VERSION = "1.0"
PUBLIC_ERROR_CODES = {
    "request_validation_failed",
    "engine_execution_failed",
    "usage_limit_reached",
}
PUBLIC_ERROR_HTTP_STATUS = {
    "request_validation_failed": int(HTTPStatus.BAD_REQUEST),
    "engine_execution_failed": int(HTTPStatus.INTERNAL_SERVER_ERROR),
    "usage_limit_reached": int(HTTPStatus.TOO_MANY_REQUESTS),
}
PUBLIC_ERROR_FIXED_MESSAGES = {
    "engine_execution_failed": "Internal engine failure.",
}
MAX_PUBLIC_ERROR_MESSAGE_LENGTH = 500


def normalize_public_error(*, code: str, message: str) -> tuple[str, str]:
    normalized_code = code if code in PUBLIC_ERROR_CODES else "engine_execution_failed"
    if normalized_code in PUBLIC_ERROR_FIXED_MESSAGES:
        return normalized_code, PUBLIC_ERROR_FIXED_MESSAGES[normalized_code]
    normalized_message = str(message).strip() or "Request failed."
    if len(normalized_message) > MAX_PUBLIC_ERROR_MESSAGE_LENGTH:
        normalized_message = normalized_message[:MAX_PUBLIC_ERROR_MESSAGE_LENGTH]
    return normalized_code, normalized_message
