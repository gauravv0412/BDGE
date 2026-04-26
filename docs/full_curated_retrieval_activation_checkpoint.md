# Full Curated Retrieval Activation Checkpoint

## Status

The full curated retrieval catalog is active.

- Active curated verses: 109 / 109
- Draft curated verses: 0
- Retrieval scoring changes: none
- Schema / transport changes: none
- Semantic scorer changes: none
- Context extractor changes during activation write: none

## Validation

Final validation after Step 29D:

- W001-W020 shape-lock regressions: 0
- Blocker failures: 0
- Forced-match warnings: 0
- Overtrigger warnings: 0
- Changed winners: 0
- Test suite: 331 passed, 8 deselected

## Activation Method

Activation was performed through a guarded command:

```bash
python -m app.scripts.activate_all_curated_verses --write --confirm-production-curated-write