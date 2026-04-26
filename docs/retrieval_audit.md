# Retrieval Audit

`app/evals/run_retrieval_audit.py` is a read-only deterministic audit for curated verse retrieval. It makes retrieval behavior visible without tuning scoring, changing metadata, or touching the engine output schema.

## Run

Recommended from the repo root:

```bash
PATH="/home/gaurav/Documents/BDGE/.venv/bin:$PATH" python -m app.evals.run_retrieval_audit \
  --input docs/benchmarks_v2_batch1_W001-W020.json \
  --out-json artifacts/retrieval_audit_benchmarks_v2_batch1_W001-W020.json \
  --out-md artifacts/retrieval_audit_benchmarks_v2_batch1_W001-W020.md
```

For tests, use the virtualenv on `PATH`:

```bash
PATH="/home/gaurav/Documents/BDGE/.venv/bin:$PATH" make test-fast
```

You can also activate the virtualenv first:

```bash
source .venv/bin/activate
make test-fast
```

## What It Reports

The JSON report is machine-readable and includes per-case top-5 candidate diagnostics: score, theme overlap, applies_when hits, blocker hits, dominant dimension alignment, expected result, actual result, and flags.

The Markdown report is human-readable and sorted by retrieval risk:

- Blocker failures
- Expected/actual mismatches
- Low-margin wins
- Weak matches
- Near-threshold fallbacks
- Concentration warnings

## Benchmark Audit Vs Live Inference

The current audit validates retrieval quality against benchmark-derived rich context. For benchmark rows, the audit builds `RetrievalContext` from the dilemma plus available benchmark narrative and semantic fields such as `core_reading`, `gita_analysis`, and `internal_driver`.

That makes the audit useful for checking curated verse metadata, ranking behavior, blockers, and expected/actual retrieval drift. It does not prove that live sparse-text semantic extraction is perfect, because live requests may begin with only the user's dilemma text and whatever semantic signals the live scorer extracts.

A live-path retrieval audit would be a separate harness that runs the live sparse-text path end to end. That is intentionally outside Step 26.

## Flag Categories

- `weak verse match`: an attached verse has fewer than 2 theme overlaps or no `applies_when` hits.
- `blocker ignored`: retrieval attached a verse despite blocker evidence.
- `wrong verse beating better runner-up`: expected verse appears below another winner.
- `expected/actual mismatch`: benchmark expected output differs from retrieval output.
- `fallback despite near-threshold strong candidate`: no verse attached while the top candidate is just below threshold.
- `semantic context missing obvious signals`: benchmark-derived retrieval context has no theme, applies, or blocker signals.
- `generic verse dominance` / `repeated verse dominating unrelated clusters`: a verse is concentrated across unrelated theme clusters.

## Reuse Concentration

Verse reuse concentration is diagnostic only. It should be reported through `verse_usage`, `top_1_verse_share_pct`, and `top_5_verse_share_pct`, but it is not a failure condition by itself.

Current product direction is high verse coverage where retrieval has a responsible fit, not artificial diversity. Do not add a max verse reuse cap just to spread usage across verses.

## Seed Curation Notes

Intentional metadata changes that are not captured in the standard diff but affect retrieval behavior.

### 3.35 — `livelihood-harm-tradeoff` removed from `applies_when` (pre-Step-28E)

`livelihood-harm-tradeoff` was removed from 3.35's `applies_when` list. Reason: 18.47 (svadharma duty verse, priority=5) is the canonical handler for livelihood–harm tradeoffs and fires on the same signal. Keeping both created a cluster-saturation risk where livelihood dilemmas would surface two duty-adjacent verses simultaneously, diluting the stronger match. 3.35 retains its existing applies_when signals and continues to fire correctly on its intended cluster. This change does not affect W001-W020 or W021-W050 retrieval shape.

### Step 29C — guarded full curated activation

All 109 curated verse entries in `app/verses/data/curated/verses_seed.json` were activated through `app/scripts/activate_all_curated_verses.py`.

The production write required `--write --confirm-production-curated-write` and was guarded by the full-activation dry-run audit. At activation time:

- W001-W020 shape regressions: `0`
- Blocker failures: `0`
- Forced-match warnings: `0`
- Overtrigger warnings: `0`
- Changed winners: `0`

The activation did not add/remove verses or change retrieval scoring, schema, semantic scoring, context extraction, or transport behavior.

Activation-time tests also exposed a few formerly draft entries that needed narrow metadata safety repairs once active: `16.2` and `13.8` now block `deception-intent`, and `13.8`, `18.25`, and `11.55` were narrowed to avoid weak live OOD overtriggers. These were metadata-only repairs; all 109 curated entries remain active.
