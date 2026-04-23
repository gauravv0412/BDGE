# Django Transport API (Step 11)

Thin Django adapter route for the public engine boundary.

## Route

- `POST /api/v1/analyze`
- View: `app.transport.django_api.analyze_view`
- The view calls only `app.engine.analyzer.handle_engine_request(...)`

## HTTP Status Mapping

- `200` -> success envelope
- `400` -> `request_validation_failed`
- `500` -> `engine_execution_failed`

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

## API Boundary Note

The transport layer does not call semantic/verdict/verse/internal stage modules directly.
Those internals are not part of the public API contract and may evolve without changing
this route contract.
