# Django Transport API (Step 12)

Thin Django adapter route for the public engine boundary.

## Route

- `POST /api/v1/analyze`
- View: `app.transport.django_api.analyze_view`
- The view calls only `app.engine.analyzer.handle_engine_request(...)`

## HTTP Status Mapping

- `200` -> success envelope
- `400` -> `request_validation_failed`
- `500` -> `engine_execution_failed`

## Public Error Contract (v1.0)

Versioned artifact: `docs/public_error_contract_v1.json`

| `error.code` | HTTP | Meaning | Message stability |
|---|---:|---|---|
| `request_validation_failed` | `400` | Request shape/version validation failed at public boundary | Descriptive validation message (not for strict programmatic matching), bounded |
| `engine_execution_failed` | `500` | Unexpected internal failure while handling an accepted request | Fixed sanitized public message: `Internal engine failure.` |

Client integrations should rely on:
- envelope shape (`meta` + `error`)
- `error.code`
- HTTP status mapping

Clients should not rely on exact text of `request_validation_failed` messages.

## Request ID (`X-Request-ID`)

- The transport layer accepts optional inbound `X-Request-ID`.
- If inbound header is valid (safe chars, non-empty, max length bound), it is reused.
- If missing/invalid, the transport generates a new request ID.
- The response always includes `X-Request-ID` header.
- Request IDs are currently header-only (not included in `meta`).

## Supported Contract Versions

- Supported request `contract_version` values: `1.0`
- The transport boundary rejects requests when `contract_version` is:
  - missing
  - not a string
  - empty/whitespace
  - unsupported (for example `2.0`)
- Rejections are returned as a stable `request_validation_failed` envelope with HTTP `400`.

## Example Request

```json
{
  "dilemma": "My manager asks me to hide a material error before review; should I disclose now?",
  "dilemma_id": "api-demo-01",
  "contract_version": "1.0"
}
```

## Example Success Response (200)

```json
{
  "meta": {
    "contract_version": "1.0",
    "engine_version": "2.1",
    "semantic_mode_default": "stub_default"
  },
  "output": {
    "dilemma_id": "api-demo-01",
    "dilemma": "...",
    "verdict_sentence": "...",
    "classification": "Mixed",
    "alignment_score": 20,
    "confidence": 0.85
  }
}
```

## Example Error Response (400/500)

```json
{
  "meta": {
    "contract_version": "1.0",
    "engine_version": "2.1",
    "semantic_mode_default": "stub_default"
  },
  "error": {
    "code": "request_validation_failed",
    "message": "..."
  }
}
```

## Example Unsupported Contract Version (400)

```json
{
  "meta": {
    "contract_version": "1.0",
    "engine_version": "2.1",
    "semantic_mode_default": "stub_default"
  },
  "error": {
    "code": "request_validation_failed",
    "message": "Unsupported contract_version '2.0'. Supported versions: 1.0."
  }
}
```

## API Boundary Note

The transport layer does not call semantic/verdict/verse/internal stage modules directly.
Those internals are not part of the public API contract and may evolve without changing
this route contract.

## Contract Compatibility Guardrails

Transport compatibility is now snapshot-tested in `tests/test_django_transport.py` for:

- valid request success response
- invalid request validation response
- malformed JSON response
- internal engine failure response
- unsupported contract version response

These tests check envelope structure and key order where practical, so accidental contract
drift is surfaced immediately.

## Logging and Minimal Observability Hooks

- One structured access log is emitted per request (`event: transport.access`) with:
  - `request_id`, `path`, `method`, `status_code`, `duration_ms`, `contract_version`, `outcome`
- Unexpected escaped failures emit a structured error log (`event: transport.error`) with:
  - `request_id`, request context, error type, and bounded diagnostic message for internal debugging
- Structured transport logs are emitted as JSON text records (not Python dict repr), so log aggregators can parse them directly.
- Public failure responses remain sanitized (`engine_execution_failed`) and do not expose raw internal exception details.
