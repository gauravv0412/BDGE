# Wisdomize — Engine Design Specification v2.1.1

An ethical decision engine anchored in the Bhagavad Gita. This spec documents the engine behavior as implemented in `benchmarks_v2_batch1_W001-W020.json` and `output_schema.json`.

**Changes from v1.0 → v2.0:** flattened the output structure, renamed the verdict/shareable fields, and added three new blocks: `internal_driver` (with hidden_risk), `core_reading` + `gita_analysis` (replacing the v1 `reasoning` blob), and `counterfactuals` (plausible adharmic/dharmic variants of the same situation). Verse match now carries full Devanagari + IAST + Hindi + English with source attribution.

**Changes from v2.0 → v2.1 (contract patch):** (1) tightened the XOR between `verse_match` and `closest_teaching` — both fields are now top-level-required, so presence is enforced and "neither present" is a rejection (prior schema only enforced the type constraint, not presence). (2) `dilemma_id` is now unambiguously required in both benchmark and live responses (minLength 1, maxLength 64); live engine issues its own. (3) added the benchmark-file integrity rule (§10) — distribution metadata must be computed from the dilemmas array.

**Changes from v2.1 → v2.1.1 (spec-only clarifications):** (1) §6 separates `missing_facts[]` (may populate on any verdict) from the Context-dependent classification trigger (only fires when missing facts could flip the verdict). (2) §3 adds an explicit weights formula — v2.1 MVP uses equal weights for `alignment_score`, with `weights` as a configurable aggregator parameter. (3) §11 rewrites the implementation phase order to: deterministic verdict spine → LLM semantic scorer → curated verse retrieval → counterfactual/share refinement. Schema contract unchanged.

---

## 1. Input

```json
{
  "dilemma": "string (required, 20–600 chars)",
  "proposed_action": "string (optional, helps disambiguation)",
  "context_tags": ["optional user-supplied hints: work|family|money|relationship|..."]
}
```

No other input fields are required. Demographics, location, caste, gender, age — engine does not ask for these and does not infer them.

---

## 2. Output Structure (v2.0 flat schema)

Full JSON Schema in `output_schema.json`. Top-level shape:

```
dilemma_id
dilemma
verdict_sentence          ← single declarative answer, ≤160 chars
classification            ← Dharmic | Adharmic | Mixed | Context-dependent | Insufficient information
alignment_score           ← integer -100..+100, derived from ethical_dimensions
confidence                ← 0..1

internal_driver           { primary, hidden_risk }
core_reading              ← 2–3 sentences on what's actually happening
gita_analysis             ← what Krishna would question (not command)

verse_match | null        ← canonical verse retrieval, XOR closest_teaching
closest_teaching | null   ← honest paraphrase when no verse clears threshold

if_you_continue           { short_term, long_term }
counterfactuals           { clearly_adharmic_version, clearly_dharmic_version }
higher_path               ← concrete dharmic alternative in the user's actual situation

ethical_dimensions        ← 8 dimensions, each { score -5..+5, note }
missing_facts             ← specific questions, max 6

share_layer               { anonymous_share_title, card_quote, reflective_question }
```

Invariants (enforced by `output_schema.json`):
- `verse_match` and `closest_teaching` are **both required to be present**. Exactly one must be non-null; the other must be explicitly `null`. The schema's `oneOf` over the two fields enforces this — neither-present and both-populated both fail validation.
- `dilemma_id` is required in every response (benchmark and live). Benchmark files use the `W###` scheme (e.g. `W001`); the live engine issues its own (UUID-style recommended). Must be non-empty, ≤ 64 chars.
- `confidence > 0.85` only if all 8 dimensions are scored AND `missing_facts == []`.
- `alignment_score` is a deterministic function of the 8 dimension scores (weighted sum, scaled to [-100, +100]).
- `reflective_question` must end with `?`.
- `verdict_sentence` ≤ 160 chars.

---

## 3. Ethical Dimensions (8 × [-5, +5])

| Key | Sanskrit | Tests |
|---|---|---|
| `dharma_duty` | Svadharma | Does it align with your role/responsibilities? |
| `satya_truth` | Satya | Honesty level of the action? |
| `ahimsa_nonharm` | Ahimsa | Harm / protection to self & others? |
| `nishkama_detachment` | Nishkama Karma | Free of outcome-craving? |
| `shaucha_intent` | Shaucha | Cleanness of motive? |
| `sanyama_restraint` | Indriya-nigraha | Impulse control? |
| `lokasangraha_welfare` | Loka-sangraha | Social/collective impact? |
| `viveka_discernment` | Viveka | Clarity of judgment? |

**Scoring rules:**
- `0` = neutral / not an axis in this dilemma. Use zero rather than forcing a signed score where the dimension genuinely doesn't apply.
- Each dimension carries a short `note` justifying its score in this specific dilemma — not a generic definition.
- Batch 1 uses the full -4..+5 range (not just ±1s); calibration should reflect real weight.

**Aggregate → classification mapping:**

| `alignment_score` | `classification` |
|---|---|
| +40 to +100 | Dharmic |
| -40 to -100 | Adharmic |
| -40 to +40 (clear trade-offs) | Mixed |
| Score depends on unstated facts | Context-dependent |
| < 4 dimensions scorable at confidence ≥ 0.5 | Insufficient information |

The last two bypass the score band — if the dilemma is fundamentally under-specified, do not produce a confident number.

**Weights (v2.1 MVP):**

`alignment_score` is a weighted sum of the 8 dimension scores, scaled and clamped to `[-100, +100]`. For v2.1 the aggregator uses **equal weights** (each dimension = 1/8) as the temporary default:

    raw = sum(score[i] for i in 8 dimensions)   # each score ∈ [-5, +5]; raw ∈ [-40, +40]
    alignment_score = round(raw × 2.5)          # scaled to [-100, +100], clamped

Weights are configurable, not a hardcoded constant. The aggregator accepts a `weights: Dict[str, float]` parameter that must sum to `1.0`; when omitted (MVP default), equal weights apply. Calibration from real usage is a Phase 4 concern — until then, treating ahimsa and sanyama as equally load-bearing is intentional under-opinionation, not a claim about the world.

*Known drift:* Batch 1 alignment scores remain canonical for eval purposes in v2.1.x. When the aggregator ships, formula-derived scores should be compared against benchmark scores and any drift flagged for calibration review, not auto-overwritten.

---

## 4. Verse Selection Logic

**Pipeline:** theme extraction → index lookup → match scoring → threshold filter → output or fallback to `closest_teaching`.

**Match score:**
- +3 per overlapping theme
- +2 if dilemma hits an `applies_when` condition
- -5 if dilemma hits a `does_not_apply_when` condition (hard filter)
- +1 if verse's core teaching aligns with the dominant dimension pull
- Threshold to include: **≥ 6** (maps to `match_confidence ≥ 0.6`)

**Curated index entry format:**

```json
{
  "verse_ref": "2.47",
  "themes": ["duty", "detachment", "action", "nishkama"],
  "sanskrit_devanagari": "कर्मण्येवाधिकारस्ते...",
  "sanskrit_iast": "karmaṇy-evādhikāras te...",
  "hindi_translation": "तेरा अधिकार केवल कर्म करने में है...",
  "english_translation": "You have the right to action alone...",
  "source": "Gita Press Gorakhpur (Hindi) / Edwin Arnold (English, public domain)",
  "core_teaching": "Act without attachment to outcome.",
  "applies_when": ["outcome-anxiety", "work-stress", "duty-conflict"],
  "does_not_apply_when": ["active-harm", "deception", "criminal-intent"]
}
```

**Translation sourcing:**
- Hindi: Gita Press Gorakhpur (primary).
- English: Edwin Arnold (public domain, primary). For production, Gambhirananda / Easwaran can be licensed as alternates — never LLM-paraphrased.
- Devanagari: verbatim. Never LLM-generated.
- IAST: optional; `null` if unavailable. Never invented.

---

## 5. Anti-Forced-Match Rules

1. Verse attaches to **60–70% of dilemmas**, not 100%. Missing the scripture target is a feature. (Batch 1: 60%.)
2. **Any single verse ≤ 15%** of total matches across a benchmark set — prevents 2.47 default. (Batch 1 max reuse: 10%.)
3. `does_not_apply_when` filter runs before output — an active-harm dilemma never gets a "do your duty" verse.
4. Prefer verses matching ≥ 2 themes over single-theme matches.
5. Translations are **verbatim from cited source**, never LLM-paraphrased.
6. Engine searches for verses relevant to **themes**, not verses that **support the verdict**. A verse can legitimately sit in tension with the user's proposed action — that is often the point.
7. If threshold not met → `verse_match: null` + `closest_teaching: "..."` explaining honestly what the Gita does and does not address about this dilemma. `closest_teaching` is explicitly paraphrase, not quoted as scripture.

---

## 6. Ambiguity & Missing-Facts Rules

Two concepts that look related but are not. Keep them separate in implementation.

**`missing_facts[]` can populate on any verdict.** The array lists specific, advice-refining questions whose answers would let the engine (or the user) act more precisely. A Dharmic verdict can carry missing facts (W012 is Dharmic but still asks whether a whistleblower lawyer has been consulted); an Adharmic verdict can too (W009 is Adharmic but still asks whether the patient has been asked directly). Presence of items in `missing_facts[]` does **not** by itself imply Context-dependent.

A dilemma may include `missing_facts[]` and still resolve to Dharmic, Adharmic, or Mixed when the missing facts refine the recommendation but do not plausibly change the class.

**Context-dependent is triggered only when a missing fact could flip the classification.** Use Context-dependent when one or more of the following is both (a) unstated and (b) decisive enough that different plausible answers would move the classification across a category boundary:

1. Actor intent that determines motive-class (shaucha, nishkama).
2. Stakeholder relationships when the action's harm profile depends on them.
3. Legality where legality itself is load-bearing (not just colour).
4. Consent ambiguity involving others.
5. Binary framing that hides material nuance ("Is lying bad?").

**Insufficient information** is a stricter case: fewer than 4 of 8 dimensions scorable at confidence ≥ 0.5, or the dilemma is under-specified to the point that no responsible reading is possible. This bypasses the alignment-score band entirely.

**Quality rule for `missing_facts[]` — on any verdict.** Items must be specific, answerable questions, not vague "need more info." Batch 1 examples: *"Is the abuse ongoing or historical?"*, *"Have you actually tried RTI / grievance portal?"*, *"Is your spouse actually aligned — have you modeled the worst case together?"*

---

## 7. Anti-Preachy / Anti-Overconfident Rules

1. **No second-person imperatives in verdict/analysis layers.** "You must" → "Consider..." / "The dharmic path here would..." (`higher_path` can be imperative since it's explicitly the suggested action.)
2. **Krishna questions more than commands.** `gita_analysis` mirrors this — it asks, it doesn't instruct.
3. **Banned on Mixed / Context-dependent verdicts:** *evil, sinful, shameful, disgusting, pure, holy*.
4. **Confidence cap:** > 0.85 requires all 8 dimensions scored AND `missing_facts == []`.
5. **Length caps** (enforced by schema): `verdict_sentence` ≤ 160, `core_reading` ≤ 600, `gita_analysis` ≤ 500, `higher_path` ≤ 500.
6. **Judge actions, not people.** "This leans adharmic" ≠ "You are adharmic."
7. **Sharper viral edge allowed** (batch 1 tone): declarative verdict sentences, tweet-sized `card_quote`, "overheard"-style `anonymous_share_title`. Cruelty targeting identity/body/immutable traits forbidden.
8. **Never claim certainty on issues the Gita itself debates** (violence, renunciation vs. action, caste endogamy).
9. **For mental-health-adjacent dilemmas**, always include professional-help signpost (in `higher_path` or `closest_teaching`).

---

## 8. Counterfactuals (new in v2.0)

Each output includes two counterfactual variants:

- `clearly_adharmic_version` — same situation, worse motive or fewer safeguards.
- `clearly_dharmic_version` — same situation, better motive or more safeguards.

Each has three fields: `assumed_context` (the plausible tweak), `decision` (the action under that context), `why` (why it lands on that side of the line).

**Rules:**
- Assumed context must be **plausible** — a realistic variation the user might slide into, not a strawman ("you commit arson").
- The adharmic and dharmic versions must be distinguishable by **motive and execution**, not by entirely different scenarios.
- Together they bracket the actual dilemma — showing the user the edges of the space they're actually in.

This block exists to counteract the biggest failure mode of Gita-style advice engines: users taking a single prescription as binary truth. Counterfactuals make the trade-space visible.

---

## 9. Share Layer

Three fields power the viral surface:

- `anonymous_share_title` — "overheard" style. Tweet-shaped. Uses *"The app said ..."* framing. Max 120 chars.
- `card_quote` — screenshot-ready, declarative, aphoristic. Max 180 chars.
- `reflective_question` — must end in `?`. Opens the user's thinking rather than closing it.

All three must be consistent with the verdict — no shareable should contradict the ethical analysis to chase engagement.

---

## 10. Benchmark Sets

- `benchmarks_50.json` — v1 stubs (50 dilemmas, v1 schema). **Deprecated**; kept for diff testing.
- `benchmarks_12_v2.json` — tight 12 dilemmas, v2 schema, full render. Used for prompt-tuning.
- `benchmarks_v2_batch1_W001-W020.json` — **current canonical batch** (20 dilemmas, v2 schema, sharper viral edge tone). Batch 2 (W021–W035) and Batch 3 (W036–W050) to follow.

**Benchmark-file integrity rule:** the `distribution` block at the top of a batch file is **computed**, not authored. Every stat in that block must be derivable from the `dilemmas` array below it — classification counts, verse usage dictionary, max reuse, score ranges, confidence ranges. A CI check should recompute these on every change and fail on drift. (v1 batch 1 shipped with a classification sum of 19 against 20 actual dilemmas; this rule exists to prevent that class of error.)

**Batch 1 canonical stats** (recomputed from the file; match the header exactly):
- Total: 20.
- Classifications: Dharmic 5, Adharmic 6, Mixed 6, Context-dependent 3, Insufficient information 0.
- Verse present: 12/20 (60%). Null with `closest_teaching`: 8/20 (40%).
- Max single-verse reuse: 2 (10%) — well under the 15% cap.
- `alignment_score` range: 14 to 78.
- `confidence` range: 0.50 to 0.88.

---

## 11. Implementation Phases

Build order is bottom-up: a deterministic spine first, then the semantic layer that feeds it, then retrieval, then polish. Every phase is shippable on its own — the system produces a reduced-but-valid v2.1 response after each.

**Phase 1 — Deterministic verdict spine.**
The parts of the engine that have no LLM dependency. Hand-authored dimension scores (e.g. batch 1) are valid input; the spine turns them into a compliant output.
- `verdict/aggregator.py` — 8 dimension scores → `raw` → `alignment_score` → `classification`. Honors the `weights` parameter; defaults to equal weights (§3).
- `verdict/rules.py` — confidence cap (§7.4), Context-dependent trigger (§6), Insufficient-information trigger (§6).
- `share/layer.py` — template-based `share_layer` generator. Tone can be crude at this stage; §4 polishes it.
- `core/schema.py` — pydantic models matching `output_schema.json`, used everywhere downstream.
- Test harness: batch 1 dilemmas with their authored `ethical_dimensions` → the spine should produce valid responses that pass the schema and match the documented `classification` for each.

**Phase 2 — LLM semantic scorer.**
The layer that turns a free-text dilemma into the 8 dimension scores plus the narrative blocks. This is where prompt engineering lives.
- `dimensions/llm_scorer.py` — single module (not 8) that scores all dimensions in one structured call, producing `{score, note}` per dimension.
- `narrative/generator.py` — produces `internal_driver`, `core_reading`, `gita_analysis`, `if_you_continue`, `higher_path`, `missing_facts` in a structured call.
- Anti-preachy rules (§7) and tone directive encoded as system prompt + few-shot examples drawn from batch 1.
- Calibration check: run the scorer over batch 1 dilemmas, compare LLM-produced dimension scores against the hand-authored ones, measure drift per dimension, iterate on prompt until drift is acceptable.
- After Phase 2, the engine is end-to-end for free-text dilemmas and emits a schema-compliant response. Until curated verse retrieval is enabled, it should return verse_match: null and closest_teaching populated.

**Phase 3 — Curated verse retrieval.**
Plugs in between Phase 2's narrative output and the final response.
- `verses/index/` — curated JSON, ~80–120 verses across ~30 theme tags. Devanagari + IAST + Hindi + English verbatim; `applies_when` / `does_not_apply_when` tags.
- `verses/loader.py` — validates source completeness at load time; rejects any verse missing Devanagari or source citation.
- `verses/retriever.py` — match-scoring pipeline (§4). Returns `verse_match` object or `None`.
- `verses/fallback.py` — when retrieval returns `None`, generates `closest_teaching` via LLM with strict guardrails: must name a related Gita concept by chapter, must not quote verses, must acknowledge the gap honestly.
- Storage: Postgres with theme-tag lookup (Django `ArrayField`) for fast filtering; JSON blob for the rest.
- A/B testable: the retriever can be disabled via config, in which case all responses fall to `closest_teaching`. Useful for measuring user trust lift from verse attribution.

**Phase 4 — Counterfactual & share refinement.**
Polish. The system is already useful without this; this makes it viral.
- `counterfactuals/generator.py` — produces `clearly_adharmic_version` / `clearly_dharmic_version` with plausibility guard (rejects strawmen; context must be a realistic variation of the same situation, not a different situation).
- `share/llm_layer.py` — upgrades Phase 1's template share output to LLM-generated with tone-directive prompts. Card quotes tweet-shaped, overheard-style share titles, reflective questions that open (not close).
- Feedback loop: thumbs-up/down on verse relevance feeds into match-scorer weight tuning (Phase 3 retriever becomes adaptive).
- Optional: commentary layer (Shankara, Ramanuja, modern readings) for users who want depth — renders as a collapsible alongside `verse_match`.
- Optional: begin collecting user-signal data for dimension-weight calibration (§3 Weights) — this is what eventually replaces the equal-weights default.

**Module contract across phases.** Every module exposes a narrow interface — `score`, `retrieve`, `generate`, `aggregate` — so any phase can be disabled or swapped without breaking the pipeline. Benchmark files serve as golden regression tests at every phase boundary; a change to any module must not drift the batch 1 outputs beyond a configurable tolerance.

---

## 12. Safety & Ethics

- Translations cited to public-domain or licensed sources; never LLM-paraphrased as if scriptural.
- No verse retrieved for dilemmas framing criminal intent, self-harm, or imminent harm-to-others — those route to safety messaging, not Gita content.
- Mental-health-adjacent dilemmas surface professional-help resources in `higher_path`.
- Global disclaimer (rendered in UI, not per-response): *"Wisdomize offers suggestive readings, not prescriptive verdicts. Scripture interpretation is plural, and the engine reflects one considered reading among many."*
- Engine never generates new "verses" or paraphrases existing ones as if original.
- Under-18 users: engine declines personal dilemmas involving sexual content, substance use, or self-harm, and routes to trusted-adult resources.

---

## 13. Module Architecture (reference)

Suggested Django layout aligned with the modular-approach preference:

```
wisdomize/
  core/                    # shared types, schema validators
    schema.py              # pydantic models matching output_schema.json
    constants.py           # dimension keys, classification enum
  dimensions/
    base.py                # BaseDimensionScorer
    dharma_duty.py
    satya_truth.py
    ... (8 total)
  verdict/
    aggregator.py          # scores → alignment_score → classification
    rules.py               # confidence cap, ambiguity triggers
  verses/
    index/                 # curated JSON index files, one per theme cluster
    retriever.py           # match-scoring pipeline
    loader.py              # validates Devanagari/Hindi/English completeness at load
  counterfactuals/
    generator.py
  share/
    layer.py               # share_layer generator
  api/                     # DRF views
    views.py
    serializers.py
  tests/
    benchmarks/            # batch files as golden tests
    dimensions/
    verses/
```

Each scorer and generator is independently testable. Benchmark files serve as regression tests — a change to any module should not drift the batch 1 outputs beyond a configurable tolerance.
