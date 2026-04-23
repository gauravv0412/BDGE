# Engine Contract Boundary (Step 10)

## Public Entrypoints

- Primary API boundary:
  - `app.engine.analyzer.handle_engine_request(payload: dict) -> EngineAnalyzeResponse | EngineAnalyzeErrorResponse`
- Typed boundary (raises on invalid request/execution):
  - `app.engine.analyzer.analyze_dilemma_request(request: EngineAnalyzeRequest) -> EngineAnalyzeResponse`
- Legacy convenience helper (non-envelope, internal/scripts):
  - `app.engine.analyzer.analyze_dilemma(dilemma: str) -> dict`

For web/API integration, call only `handle_engine_request(...)`.

## Request Shape

`EngineAnalyzeRequest` (`app/core/models.py`)

- `dilemma: str` (20..600 chars)
- `dilemma_id: str | null` (1..64 chars when present)
- `contract_version: str` (default `"1.0"`)
- `extra="forbid"` to reject unknown request keys

## Success Response Shape

`EngineAnalyzeResponse` (`app/core/models.py`)

- `meta: EngineResponseMeta`
  - `contract_version`
  - `engine_version`
  - `semantic_mode_default` (`stub_default` or `live_default`)
- `output: WisdomizeEngineOutput`

`WisdomizeEngineOutput` remains aligned with `docs/output_schema.json`.

## Error Response Shape

`EngineAnalyzeErrorResponse` (`app/core/models.py`)

- `meta: EngineResponseMeta`
- `error: EngineError`
  - `code`:
    - `request_validation_failed`
    - `engine_execution_failed`
  - `message`: human-readable error text

## Validation Failure Behavior

- `handle_engine_request(...)` never raises for request-shape errors; it returns `EngineAnalyzeErrorResponse` with code `request_validation_failed`.
- Runtime execution failures are also enveloped as `engine_execution_failed`.
- `analyze_dilemma_request(...)` remains strict/typed and can raise; use it for internal callers that want exception flow.

## Ownership Boundary (High Level)

1. Stage 1 semantic interpretation (`app.semantic.scorer.semantic_scorer`)
   - Authors narrative fields and primary `verdict_sentence`.
2. Stage 2 deterministic verdict layer (`app.verdict.aggregator.aggregate_verdict`)
   - Owns deterministic math only (`alignment_score`, `classification`, `confidence`)
   - Sanitizes/clips semantic `verdict_sentence`, deterministic fallback if invalid/missing.
3. Stage 3 verse retrieval (`app.verses.retriever.retrieve_verse`)
4. Deterministic overlays (`counterfactuals`, `narrative`, `share`)

Consumers should treat only request/response envelope fields as stable contract.

## Stable vs Internal Fields

- Stable API envelope:
  - request: `dilemma`, `dilemma_id`, `contract_version`
  - response: `meta`, `output` OR `error`
- Stable output contract:
  - `WisdomizeEngineOutput` keys constrained by `docs/output_schema.json`
- Internal details (subject to implementation change without API change):
  - stage helper names
  - intermediate semantic payload internals
  - deterministic module internals and retrieval heuristics

## Multi-Engine Future Compatibility

This contract is engine-agnostic at the boundary: any future engine (e.g. HR policy engine, alternate doctrine engine) can plug in by:

1. Accepting `EngineAnalyzeRequest`
2. Producing either:
   - `EngineAnalyzeResponse(meta, output)` matching `WisdomizeEngineOutput`, or
   - `EngineAnalyzeErrorResponse(meta, error)`
3. Preserving `contract_version` semantics while internal reasoning modules evolve independently.
