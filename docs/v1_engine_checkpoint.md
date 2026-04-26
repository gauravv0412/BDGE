# V1 Engine Checkpoint

Date: 2026-04-27

## Status

This checkpoint freezes the current full-catalog engine state as the V1 rollback baseline before visible-language, prompt, schema, Django frontend, or product presentation refinements.

- Full curated retrieval catalog: active
- Active curated verses: 109 / 109
- Draft curated verses: 0
- Step 29A-29D: closed
- Step 30A browser/live smoke: passed
- Step 30B qualitative smoke report: completed
- Behavior changes in this checkpoint: none

## Public Boundary

The public engine boundary remains:

```python
handle_engine_request(payload)
```

The Django API route remains:

```text
POST /api/v1/analyze
```

No output schema, transport contract, request contract, or response envelope change is part of this checkpoint.

## Engine Status

- Contract version remains `1.0`.
- Engine response metadata remains the current `engine_version` value, `2.1`.
- V1 baseline is a git tag/release concept, not a schema change and not a new runtime versioning system.
- The engine pipeline remains unchanged:
  - semantic interpretation
  - deterministic verdict aggregation
  - curated verse retrieval or `closest_teaching` fallback
  - deterministic counterfactual, higher-path, and share-layer refinement

## Django Transport Status

- The thin Django transport remains active at `/api/v1/analyze`.
- The read-only browser shell remains active at `/`.
- Request ID handling, public error envelope behavior, and JSON response shape are unchanged.
- Frontend behavior is unchanged in this checkpoint.

## Retrieval Status

- Full curated retrieval catalog is active: 109 / 109.
- Draft curated verses: 0.
- Retrieval scoring changes in this checkpoint: none.
- Verse metadata changes in this checkpoint: none.
- Semantic scorer changes in this checkpoint: none.
- Context extractor changes in this checkpoint: none.

## Browser Smoke Status

Step 30A browser/live smoke passed against the full active catalog.

- Total browser cases: 12
- API 200 responses: 12
- `verse_match` rendered: 4
- `closest_teaching` rendered: 8
- `share_layer` rendered: 12
- `counterfactuals` rendered: 12
- `higher_path` rendered: 12
- Console/network errors: 0
- Desktop/mobile layout issues: 0
- Blockers: 0

Step 30B qualitative smoke report completed and captured product-level limitations for the next refinement phase.

## Known Product Limitations

Known limitations from Step 30B:

- Language can be hard to understand or too generic in some cases.
- `closest_teaching` lacks an explicit verse anchor.
- Counterfactuals can be too generic.
- `share_layer` needs context rewrite before public-facing polish.
- Crisis/self-harm adjacent input needs a dedicated UX path.
- Medical/professional prompts need stronger boundary handling.
- Low-information prompts need uncertainty-first presentation.
- Frontend is still a read-only shell, not a full consumer product.

## Rollback Guidance

Use this checkpoint as the rollback target if later prompt, language, schema, frontend, or presentation refinements destabilize the engine.

Recommended rollback workflow:

1. Identify the commit tagged `v1-engine-baseline`.
2. Compare later changes against this baseline before reverting.
3. Prefer reverting only the refinement layer that caused the regression.
4. Re-run the validation commands below after rollback.
5. Confirm the XOR rule still holds: exactly one of `verse_match` or `closest_teaching` is non-null.

This checkpoint is intentionally documentation/tag prep only. It does not introduce migration logic or compatibility shims.

## Exact Validation Commands

Run from the repository root:

```bash
PATH="/home/gaurav/Documents/BDGE/.venv/bin:$PATH" make test-fast
PATH="/home/gaurav/Documents/BDGE/.venv/bin:$PATH" make smoke
PATH="/home/gaurav/Documents/BDGE/.venv/bin:$PATH" make test-browser
```

Expected results at checkpoint creation:

- `make test-fast`: 331 passed, 8 deselected
- `make smoke`: passed
- `make test-browser`: 8 passed, 331 deselected

## Tag Instructions

Recommended local commands after committing this checkpoint:

```bash
git tag -a v1-engine-baseline -m "V1 engine baseline: full curated retrieval catalog active"
git push origin v1-engine-baseline
```

Recommended commit message:

```text
Document V1 engine baseline checkpoint
```
