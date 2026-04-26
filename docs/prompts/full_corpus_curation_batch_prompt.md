# Prompt: full-corpus curation batch drafting (JSON only)

You are assisting curation of Bhagavad Gita metadata for retrieval.

You will receive ONE batch artifact JSON from:
`app/verses/data/curation_prep/batches/curation_batch_*.json`

## Output format (strict)

- Return **JSON only**.
- Return the same top-level structure (`header`, `entries`).
- Keep entry order unchanged.
- Do not wrap JSON in markdown fences.

## Hard constraints

1. **Do not alter scripture identity/text/source** in `entries[].scripture`.
   - No edits to `verse_id`, `verse_ref`, chapter/span, Sanskrit, Hindi, English, or source.
2. Only edit:
   - `entries[].promotion_requested`
   - `entries[].placeholders.*`
3. Do not introduce new fields.
4. Do not mass-set all rows to promotable.

## Promotion quality rules

Set `promotion_requested: true` only when metadata is genuinely useful for practical retrieval.

For rows with `promotion_requested: true`, fill all required fields:

- `core_teaching` (specific, non-generic)
- `themes` (focused tags, avoid over-tagging)
- `applies_when`
- `does_not_apply_when` (include misuse/blocker context)
- `priority` (1-5)
- `status` (`draft` preferred unless clearly ready)

For non-promoted rows:

- Keep placeholders empty or partial as needed.

## Tagging discipline

- Avoid generic tags like `misc`, `general`, `spiritual`.
- Avoid priority inflation.
- Avoid long tag lists; precision over breadth.

## Priority rubric

- `5` = highly useful practical decision retrieval
- `4` = strong practical relevance
- `3` = moderate relevance
- `2` = narrow/specialized
- `1` = mostly theological/background, rarely retrieved

## Allowed tag vocabularies

You must **only** use tags from these lists. Do not invent tags outside them.

**themes:**
action, anger, charity, compassion, death, desire, detachment, discernment, duty,
equality, equanimity, greed, grief, nonharm, restraint, right-livelihood, self-mastery,
speech, truth, welfare-of-all

**applies_when:**
anger-spike, bereavement, career-crossroads, career-vs-calling, caste-or-identity-boundary,
class-bias, credit-theft, duty-conflict, ethical-speech, family-disapproval, found-property,
livelihood-harm-tradeoff, outcome-anxiety, private-conduct-test, provider-duty,
public-humiliation-impulse, self-sabotage, service-without-return, temptation,
terminal-diagnosis-disclosure, truth-compassion-conflict, whistleblowing-risk

**does_not_apply_when:**
abuse-context, active-harm, criminal-intent, deception, deception-intent, imminent-violence,
public-shaming-intent, retaliatory-speech, scripture-as-weapon, self-harm

## Final check before output

- JSON parses cleanly.
- Scripture fields unchanged.
- Promotable rows complete and specific.
- Non-promoted rows not forced.
