# Full-Corpus Curation Checkpoint

This checkpoint adds the full-corpus Bhagavad Gita curation workflow and expands the active curated verse seed through reviewed B01–B10 batches.

## What changed

- Added deterministic 10-batch curation workflow.
- Added AI-assisted batch export/validation/import flow.
- Added guarded promotion apply command.
- Expanded active curated verse seed from reviewed promotion artifacts.
- Preserved raw / curation_prep / curated separation.
- Added release/test/smoke workflow and safety/readiness docs.

## Safety boundaries

- No retrieval scoring changes.
- No engine architecture changes.
- No automatic full-corpus promotion.
- Active curated seed updates came through reviewed promotion artifacts.
- Production seed writes require explicit confirmation.

## Validation

- `make test-fast`
- `make smoke`
- curation workflow tests
