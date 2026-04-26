# Full-corpus curation in 10 reviewable batches

This workflow drafts metadata for the entire canonical Bhagavad Gita corpus **without** mixing layers:

- Raw source of truth: `app/verses/data/raw/bhagavad_gita_corpus_canonical.json`
- Batch draft artifacts: `app/verses/data/curation_prep/batches/`
- Active retrieval metadata: `app/verses/data/curated/verses_seed.json`

Batch artifacts are prep-only. They are **not** loaded by retrieval until explicit promotion.

## Deterministic 10-batch plan

| Batch | Coverage |
|---|---|
| B01 | Chapter 1 + Chapter 2 (verses 1–36) |
| B02 | Chapter 2 (verses 37–72) |
| B03 | Chapters 3–4 |
| B04 | Chapters 5–6 |
| B05 | Chapters 7–9 |
| B06 | Chapters 10–11 |
| B07 | Chapters 12–13 |
| B08 | Chapters 14–15 |
| B09 | Chapters 16–17 |
| B10 | Chapter 18 |

The plan is deterministic and test-backed. Every canonical verse is covered exactly once.

## Export one batch

```bash
PYTHONPATH=. .venv/bin/python -m app.scripts.curation_batches export B03
```

Output defaults to:

`app/verses/data/curation_prep/batches/curation_batch_b03.json`

Each batch artifact includes:

- `batch_id`, label, chapter coverage, verse count
- canonical scripture identity/text/source in each entry
- editable placeholders
- `promotion_requested: false` by default

## Send batch to AI drafting

Use `docs/prompts/full_corpus_curation_batch_prompt.md` with the exported batch JSON.

Important:

- AI must return **JSON only**
- AI must not alter scripture fields
- AI should fill metadata only for rows it marks `promotion_requested: true`

## Validate AI-filled batch

```bash
PYTHONPATH=. .venv/bin/python -m app.scripts.curation_batches validate   app/verses/data/curation_prep/batches/curation_batch_b03.json
```

Validation enforces:

- canonical scripture identity/text/source unchanged
- promotable rows require complete metadata (`core_teaching`, tags, `priority`, `status`)
- promotable rows reject generic placeholders (`todo`, `misc`, etc.)
- non-promoted incomplete rows allowed

## Merge validated batch back into prep layer

```bash
PYTHONPATH=. .venv/bin/python -m app.scripts.curation_batches import   app/verses/data/curation_prep/batches/curation_batch_b03.json
```

Import writes a merged prep artifact under `curation_prep/batches/` by default.
It refuses curated output paths.

## Review and promotion safety

After batch import:

1. Review changed rows.
2. Build a promotion review artifact (`app.scripts.run_curation_promotion`).
3. Human-review that artifact (e.g., Claude review pass).
4. Run guarded apply in dry-run mode (`app.scripts.apply_curation_promotion`).
5. Apply with explicit confirmation flags only after dry-run is clean.

Even if all verses become eligible, this does **not** mean all verses should rank equally in retrieval.

## Priority guidance

- `5` = highly useful practical decision retrieval
- `4` = strong practical relevance
- `3` = moderate relevance
- `2` = narrow/specialized
- `1` = mostly theological/background, rarely retrieved

## Batch safety controls

- Invalid batch id is rejected.
- All-batch export is blocked unless explicitly requested (`--allow-all`).
- Batch plan coverage can be reported with:

```bash
PYTHONPATH=. .venv/bin/python -m app.scripts.curation_batches report
```
