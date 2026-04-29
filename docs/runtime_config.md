# Runtime & product configuration (Step 38A)

Wisdomize reads **product limits**, **plan display**, and selected **engine/UI knobs** from `app/config/runtime_config.py` (plus optional JSON/env overrides). Business logic should call helpers such as `get_plan()`, `get_runtime_config()`, and `get_verse_match_score_threshold()` instead of hardcoding numbers in feature modules.

## Precedence

1. **Environment variables** (see below and `.env.example`) override numeric/string fields where supported.
2. **`WISDOMIZE_PLANS_JSON`** or **`WISDOMIZE_PLANS_CONFIG_PATH`** merge on top of built-in default plan definitions (`free`, `plus`, `pro` must remain present after merge).
3. **Built-in defaults** in `app/config/runtime_config.py` preserve current product behavior when nothing is overridden.

## Plans (billing + pricing)

| Source | Purpose |
|--------|---------|
| Default dict in code | Labels, `monthly_analysis_limit`, `price_display`, `enabled` for `free` / `plus` / `pro`. |
| `WISDOMIZE_PLANS_JSON` | Inline JSON object keyed by plan id; merges shallowly per plan. |
| `WISDOMIZE_PLANS_CONFIG_PATH` | Path to JSON file with the same shape as `WISDOMIZE_PLANS_JSON`. |

The public **`/pricing/`** page and authenticated **`/billing/`** shell both call `ordered_plan_definitions()` so plan cards never diverge.

**Monthly usage** for quota enforcement uses `free.monthly_analysis_limit` (default **5**) unless overridden. Only **successful** **`POST /api/v1/analyze/presentation`** responses increment usage (after engine + presentation build). **`POST /api/v1/analyze`** never increments.

## Verse attachment threshold

| Variable | Default | Meaning |
|----------|---------|--------|
| `WISDOMIZE_VERSE_MATCH_SCORE_THRESHOLD` | `6` | Minimum integer retrieval score for a curated verse to attach (same default as historical `_MATCH_THRESHOLD`). |

Changing this value does **not** alter scoring, metadata, or algorithms—only the cutoff applied after `rank_candidates`. Confidence mapping into `[0.6, 1.0]` scales with the same threshold.

**Not yet moved to config (audit / backlog):** semantic scorer weights, dimension aggregation weights, counterfactual/share narrative limits beyond schema caps, and retrieval audit “near threshold” heuristics that assume the default score scale.

## Other runtime knobs

| Variable | Default | Notes |
|----------|---------|------|
| `WISDOMIZE_MAX_MISSING_FACTS` | `6` | Truncates Stage‑1 `missing_facts` before verdict/verse; capped at **6** to stay within `output_schema.json`. |
| `WISDOMIZE_FEEDBACK_COMMENT_MAX_LEN` | `500` | `app/feedback/validation.py` reads via `get_feedback_comment_max_len()`. |
| `WISDOMIZE_DASHBOARD_HISTORY_PAGE_SIZE` | `20` | Recent history slice on `/dashboard/`. |
| Presentation LLM timeout | (see `PRESENTATION_LLM_TIMEOUT_SECONDS`) | Already env-driven in `app/presentation/config.py`; duplicated in `get_runtime_config().presentation_llm_timeout_seconds` for observability/docs alignment only. |

## Safe vs risky tuning

- **Relatively safe:** plan display strings, monthly limits (after you accept quota UX), dashboard page size, feedback comment max (keep within support expectations).
- **Risky / eval-sensitive:** verse score threshold, missing-facts truncation—small changes can move golden benchmarks; always re-run retrieval audits and benchmark comparisons after changes.

## Tests

`tests/test_step38a_config_billing.py` covers defaults, plan JSON merge, verse threshold behavior, quota enforcement, and feedback length wiring.
