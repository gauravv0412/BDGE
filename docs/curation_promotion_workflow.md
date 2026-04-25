# Curation promotion (prep → active curated)

## Lifecycle

1. **Canonical raw** — `app/verses/data/raw/bhagavad_gita_corpus_canonical.json` (scripture only).
2. **Editor prep** — `app/verses/data/curation_prep/verses_editor_prep.json`: skeleton rows with `scripture` + `placeholders`. Not used by retrieval.
3. **Promotion review** — optional JSON output `verses_promotion_review.json` under `curation_prep/`: validated `CuratedVerseEntry`-shaped dicts ready for human review.
4. **Active curated** — `app/verses/data/curated/verses_seed.json`: loaded by `load_curated_verses()`.

Promotion never reads alternate raw files and does not auto-tag the full corpus.

## What makes a row promotable

- `promotion_requested` must be **true** on that prep row (default is false — prevents lazy bulk promotion).
- **All** of the following placeholders must be explicitly set (non-empty / non-null as applicable):
  - `core_teaching`, at least one `themes`, `applies_when`, `does_not_apply_when`
  - `priority` (1–5)
  - `status` (`draft` | `active` | `archived`)
- `dimension_affinity` may be `{}`; if present, scores must be in `[1, 5]` and keys must be valid dimension names at `CuratedVerseEntry` parse time.
- The merged row is validated with **`validate_curated_entry`** (theme / applies_when / blocker vocab, active Hindi rule, etc.).
- Scripture on the promoted entry must match the prep row’s `scripture` field exactly (grounding check).

Rows without `promotion_requested` are **skipped** with no error. Rows with `promotion_requested` but incomplete metadata produce a **`PromotionError`** listing all issues (no partial success).

## Batch safety

- Default **maximum 25** rows with `promotion_requested` per call unless `allow_large_batch=True`.
- Duplicate `verse_ref` or `verse_id` within the batch is rejected.
- Conflict with **existing** seed entries (by `verse_ref` / `verse_id`) is rejected.

## Dry-run / review-first behavior

- **`build_promotion_plan`** only returns typed `CuratedVerseEntry` models; it does not write files.
- **`write_promotion_review_artifact`** writes a review JSON document (`bdge.curation_promotion_review.v1`, role `promotion_review_not_active_retrieval`). Retrieval does not load this file.
- **`merge_promoted_into_seed_json(..., write=False)`** validates a merged list in memory only.
- **`merge_promoted_into_seed_json(..., write=True)`** on the **production** `verses_seed.json` path additionally requires **`confirm_production_curated_write=True`**.

CLI (review artifact only):

```bash
PYTHONPATH=. .venv/bin/python -m app.scripts.run_curation_promotion \\
  --prep app/verses/data/curation_prep/verses_editor_prep.json \\
  --out app/verses/data/curation_prep/verses_promotion_review.json
```

## Out of scope

- Admin/editor UI, automatic full-corpus tagging, retrieval retuning, frontend changes, doctrine beyond this Bhagavad Gita corpus.

## Code

- `app/verses/curation_promotion.py`
- Tests: `tests/test_curation_promotion.py`

## See also

- `docs/curation_prep_workflow.md` — building the prep artifact.
- `docs/verses_raw_corpus.md` — raw corpus validation.
