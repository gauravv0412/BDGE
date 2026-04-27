# V1.1 Visible-Output Refinement Spec

## Product Goal

V1.1 improves comprehension, context-specificity, and shareability of the visible Wisdomize output while preserving the frozen V1 engine as a rollback baseline.

The current V1 output has the right ethical spine and a useful sharp/wisdom style, but Step 30B showed that some cards are too hard to understand, too generic, or not specific enough to the user's dilemma. V1.1 should keep the serious Krishna-style line and add simpler contextual explanations alongside it.

This is a presentation and product-language refinement plan. It does not change retrieval scoring, verse metadata, semantic scoring, context extraction, output schema, or frontend behavior in this step.

## Output Layering Model

Each visible card should support a layered copy model:

- `wisdom_line`: the current sharp, serious wording. This preserves the V1 tone and should remain the primary product voice.
- `simple_explanation`: easy-language explanation for users who need a plain reading.
- `context_link`: how this applies to the user's specific dilemma, using concrete nouns from the situation rather than generic ethics labels.
- `next_action`: a practical next step where appropriate. This should be concrete, modest, and non-commanding.

The goal is not to make the product softer or bland. The goal is to make the sharp line understandable without diluting it.

## Card-by-Card Refinement Requirements

### A. Verdict / Core Reading

V1.1 requirements:

- Keep the current verdict sentence.
- Add an expandable `Explain simply` surface.
- Add an expandable `Why this applies to your situation` surface.
- Keep the verdict visually primary.
- Avoid replacing the sharp verdict with a generic summary.

Expected layering:

- `wisdom_line`: current `verdict_sentence` or current core reading line.
- `simple_explanation`: one to two plain sentences.
- `context_link`: why this verdict follows from the dilemma details.
- `next_action`: optional, only when the next step is obvious and safe.

### B. Closest Teaching

Current issue:

- The fallback card can feel like "no verse" because `closest_teaching` has no explicit Gita anchor.

V1.1 requirement:

When safe and honest, include a `closest_gita_anchor` presentation object:

- `verse_ref`
- `translation`
- `why_not_direct_match`
- `assumed_connection`
- `simple_explanation`

Label it honestly:

```text
Closest Gita anchor, not a direct verse verdict
```

Rules:

- Never force a direct `verse_match` if threshold or blocker logic fails.
- Never present the anchor as a direct verse verdict.
- The anchor must explain why it is only adjacent or instructive, not decisive.
- If no safe anchor exists, keep `closest_teaching` without a verse reference and say that the system did not find a direct enough Gita anchor.

### C. If You Continue

For both `short_term` and `long_term`, V1.1 should keep the sharp consequence and add:

- `simple_explanation`
- `context_specific_reason`

Requirements:

- The sharp consequence should remain short and memorable.
- The simple explanation should state what the consequence means in everyday language.
- The context-specific reason should connect the consequence to the user's actual action, pressure, or relationship.

Example structure:

- `wisdom_line`: "Relief now, residue later."
- `simple_explanation`: "This may feel easier today, but it leaves an unresolved ethical cost."
- `context_link`: "Because the wallet has an ID, keeping the cash is not just need; it is choosing not to return what can be returned."

### D. Counterfactuals

Current issue:

- The assumed context can feel generic or templated.

V1.1 requirement:

For both adharmic and dharmic paths, use a human-readable path model:

- `assumed_inner_state`
- `likely_decision`
- `why_it_degrades_or_elevates`
- `simple_explanation`
- `context_link`

Rules:

- Avoid taxonomy/debug language.
- Avoid labels like "dimension pressure" in the user-facing card.
- Avoid generic moral summaries that could apply to any dilemma.
- Show the inner movement: what desire, fear, duty, resentment, attachment, or clarity is driving the path.
- Make the dharmic path concrete, not saintly or unrealistic.

### E. Higher Path

V1.1 requirements:

- Make `higher_path` concrete and contextual.
- Include `first_clean_step`.
- Include `what_not_to_do`.
- Include `simple_explanation`.

Expected behavior:

- The higher path should not merely say "act with truth" or "choose clarity."
- It should tell the user what the first cleaner move looks like in this situation.
- `what_not_to_do` should name the tempting but degrading move without shaming the person.

Example structure:

- `wisdom_line`: current higher-path line.
- `first_clean_step`: "Return the wallet through the ID or the cafe counter."
- `what_not_to_do`: "Do not turn urgent rent pressure into permission to keep identifiable money."
- `simple_explanation`: "The cleaner path is the one that solves need without creating theft."

### F. Ethical Dimensions

For each shown dimension:

- Score/label remains.
- Add `simple_meaning`.
- Add `context_specific_reason`.

Requirements:

- Keep existing dimension names for consistency.
- Do not expose internal scoring mechanics as the main user-facing explanation.
- Explain what the score means in plain language.
- Tie the score to the concrete dilemma.

Example:

- `dimension`: `satya_truth`
- `score`: existing score
- `simple_meaning`: "How much the action stays honest with reality and other people."
- `context_specific_reason`: "Because the wallet has an ID, pretending the owner is unreachable weakens truthfulness."

### G. Share Layer

Current issue:

- The share layer is not attractive or context-based enough.

V1.1 requirement:

The share layer should become:

- context-derived
- screenshot-worthy
- emotionally sharp
- not generic
- short enough for a card

Good examples:

```text
You don't lose dharma by wanting justice. You lose it when justice becomes revenge.
```

```text
The question is not whether you are right. The question is whether your next move makes you cleaner or smaller.
```

Rules:

- No generic motivational lines.
- No debug taxonomy.
- No moral preaching.
- No long paragraphs.
- No "you must" imperatives.
- Judge the action, not the person.
- Preserve the sharp/wisdom style, but make the line traceable to the dilemma.

## Schema Strategy

Recommendation: prefer adding a presentation/view-model layer first.

V1.1 should avoid extending the strict public output schema until it is clear which fields must be persisted or API-visible. The safer first implementation path is:

1. Keep the public engine schema unchanged.
2. Build an internal presentation/view-model adapter that derives the visible layers from existing output fields.
3. Let the frontend render the view model behind expandable sections.
4. Persist full smoke outputs and manually evaluate readability/shareability.
5. Only extend the strict public schema if these fields need to become stable API contract fields.

Possible strategies:

- Presentation/view-model layer: preferred first step. Lowest schema risk, easiest rollback to V1, and compatible with UI experiments.
- Frontend-derived explanation fields: acceptable for very small explanations, but weaker for consistency and testability.
- Public schema extension: use only after field names and product behavior stabilize, or if external API consumers need the fields.

V1.1 should not change XOR behavior. Exactly one of `verse_match` or `closest_teaching` remains non-null unless a future schema version explicitly changes that contract.

## Step 31B Adapter Decision

Step 31B implements the recommended first step as an internal presentation view-model adapter.

- Public engine schema remains unchanged.
- Public Django transport contract remains unchanged.
- The presentation view model is an internal UI layer built from the existing V1 success envelope.
- The adapter is deterministic and does not call the LLM.
- The adapter preserves V1 sharp/wisdom copy as `primary_text`.
- Expandable sections are structural placeholders where the current schema does not yet contain true simple/contextual prose.
- Final copy quality improvements come in later V1.1 steps.

This means V1.1 can experiment with card organization, expandable explanations, and closest-teaching presentation without weakening the V1 rollback baseline or expanding the strict public output contract prematurely.

## UI Strategy

Use expandable sections, not hover-only UI.

Recommended expandable surfaces:

- `Explain simply`
- `Why this applies here`
- `Show Gita anchor`

Reasons:

- Mobile users need tap/expand behavior.
- Hover-only explanations are inaccessible on touch devices.
- Progressive disclosure preserves the current sharp first impression while letting confused users expand for clarity.
- Screenshots can still show the wisdom line, while deeper review can reveal context.

Initial UI order:

1. Show the existing sharp card.
2. Offer `Explain simply`.
3. Offer `Why this applies here`.
4. For closest teaching only, offer `Show Gita anchor` when an honest anchor exists.

## Safety Note

Self-harm/crisis adjacent input should not be solved in this visible-copy refinement step.

Create a separate future step:

```text
V1.1 Safety/Crisis UX path
```

That step should define:

- detection threshold
- dedicated UI state
- emergency/help-seeking language
- what engine output is hidden, softened, or bypassed
- how to avoid labeling a user in crisis as morally bad

Until then, V1.1 visible-output work should avoid treating crisis safety as a wording-only problem.

## Non-Goals

- No retrieval tuning.
- No scoring changes.
- No verse metadata changes.
- No semantic scorer changes.
- No context extractor changes.
- No output schema change in this spec step.
- No full frontend redesign.
- No removing current wisdom copy.
- No forced direct verse matches.
- No crisis UX implementation in this step.

## Acceptance Criteria For Future Implementation

Future V1.1 implementation should be accepted only when:

- The 12 Step 30A smoke cases are rerun.
- Full prose is persisted for each case, including verdict sentence, core reading, Gita analysis, verse/teaching copy, `if_you_continue`, counterfactuals, higher path, ethical dimensions, and share layer.
- Readability is judged manually.
- Share layer is rated `screenshot_ready`, `decent`, or `not_shareable`.
- No output schema validation failures occur.
- No Django transport contract regressions occur.
- No retrieval scoring or verse metadata changes are included accidentally.
- The V1 rollback tag remains valid.

## Recommended V1.1 Implementation Order

1. Add a presentation/view-model adapter behind the existing engine output.
2. Persist full prose in browser smoke artifacts.
3. Add expandable frontend sections using the adapter output.
4. Improve closest-teaching presentation with honest Gita anchors where safe.
5. Refine `if_you_continue`, counterfactuals, higher path, and ethical-dimension explanations.
6. Rewrite share-layer presentation for context-derived screenshot quality.
7. Rerun the 12-case browser smoke and Step 30B-style qualitative review.
8. Decide whether any stabilized fields deserve a public schema extension.
9. Design the separate V1.1 Safety/Crisis UX path.
