# Raw → curation prep (editor-prep) workflow

## Sources of truth

| Layer | Path | Role |
|--------|------|------|
| Canonical raw scripture | `app/verses/data/raw/bhagavad_gita_corpus_canonical.json` | Full corpus; loaded via `app/verses/raw_corpus.py` only. |
| Editor-prep artifact | `app/verses/data/curation_prep/verses_editor_prep.json` | **Generated** skeleton for human curation; not used by retrieval. |
| Active curated retrieval | `app/verses/data/curated/verses_seed.json` (+ vocab JSONs) | MVP retrieval index; loaded by `app/verses/loader.py`. |

Other files under `data/raw/` are not merged into this workflow.

## What the prep workflow produces

Module: `app/verses/curation_prep.py`.

- **Input:** canonical raw corpus (default: `load_canonical_raw_corpus()`).
- **Output:** a JSON document with `schema_id` `bdge.curation_prep.v1` and `artifact_role` `editor_prep_not_active_retrieval`.
- **Per verse:** `scripture` matches `VerseRecord` (text + `VerseSource` mapped from raw per-verse attribution). `placeholders` holds empty retrieval fields (`core_teaching`, tags, `dimension_affinity`, `priority`) for editors to fill deliberately.

Validation: `validate_curation_prep_payload` / `load_curation_prep_artifact` enforce structure, header/entry count consistency, and that the declared canonical filename is `bhagavad_gita_corpus_canonical.json`.

`write_curation_prep_artifact` **refuses** to overwrite guarded active curated files (`verses_seed.json`, `themes.json`, `applies_when.json`, `blockers.json`).

## Generate the artifact

```bash
PYTHONPATH=. .venv/bin/python -m app.scripts.export_curation_prep
```

The default output file is gitignored (large JSON); run the command locally or in CI when you need a fresh skeleton.

## How this differs from active retrieval

- Prep files are **not** loaded by `load_curated_verses`.
- Placeholders are **not** validated against theme / applies_when vocabularies until an entry is promoted into `verses_seed.json` and passes `validate_curated_entry`.
- Promotion is a separate, explicit step (manual or future tooling), not automatic.

## Promotion (Step 22)

After editors set `promotion_requested` and fill placeholders, use **`app/verses/curation_promotion.py`** to plan promotion, emit a **review** JSON, and optionally merge into a seed file with explicit flags. See **`docs/curation_promotion_workflow.md`**.

## Out of scope

- Admin/editor UI, automatic tagging of the full 701 verses, retrieval retuning, frontend changes, or doctrine beyond this Bhagavad Gita corpus.

## Tests

See `tests/test_curation_prep.py`.

## See also

- `docs/verses_raw_corpus.md` — canonical raw corpus validation.
- `docs/environment_setup.md` — Python, Playwright, smoke / CI assumptions.
- `docs/deployment_checklist.md` — release gate commands.
