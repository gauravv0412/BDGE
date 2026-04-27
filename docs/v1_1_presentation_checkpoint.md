# V1.1 Presentation Checkpoint

V1.1 presentation changes are complete through Step 31L.

## Contract and rollback safety

- V1 engine behavior remains frozen.
- Public engine schema remains unchanged.
- `POST /api/v1/analyze` remains unchanged.
- `POST /api/v1/analyze/presentation` is the presentation-only view-model route.
- All changes are adapter/frontend-layer and rollback-safe independently of core engine scoring/retrieval.

## Step 31F to 31L summary

- **31F Crisis-safe mode**
  - Adds `presentation_mode` with `standard | crisis_safe`.
  - Preserves safety-first rendering and suppresses unsafe surfaces in crisis mode.
- **31G Closest Gita Lens**
  - Replaces technical fallback copy with user-facing closest-lens wording.
  - Keeps honesty about non-direct-verse cases.
- **31H Share repair**
  - Domain-aware deterministic share quote/question copy.
  - Fixes grammar/fragments and removes domain mismatch failures.
- **31I Counterfactual rewrite**
  - Domain-aware deterministic Adharmic/Dharmic card copy.
  - Removes repeated placeholder strings and mismatch framing.
- **31J Guidance/Higher Path explain-simply repair**
  - De-duplicates explain text from primary text.
  - Improves plain-language contextual clarity.
- **31K Sanitizer hardening**
  - Expands debug/internal-word sanitization.
  - Sanitizes verse guidance primary text.
  - Replaces verdict fallback engine phrasing with user-facing wording.
- **31L Domain detection hardening**
  - Uses dilemma-first high-confidence domain detection before broader-field fallback.
  - Reduces contamination from stub/generated non-dilemma fields.

## Validation snapshot

- `make test-fast`: 363 passed, 16 deselected
- `make test-browser`: 16 passed
- `make smoke`: pass

## Remaining non-blockers

- JS fallback parity for closest-lens Gita-direction can be improved later (low risk, separate task).
- Sentence-aware sanitizer refinement may further improve readability in edge phrasing.
- Future LLM prompt refinement remains a separate track from deterministic presentation adapter logic.
- W028/6.32 extractor work is unrelated to this presentation checkpoint.
