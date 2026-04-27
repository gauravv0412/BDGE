# Step 31E — Prose quality audit (from Step 31D browser smoke artifacts)

## Executive summary

This report audits **user-visible prose** captured in `artifacts/browser_smoke_step31D.json` (full browser text + expandable sections). The intent is a **pre-implementation** map of where copy is clear vs. where it is templated, abstract, or meta, consistent with the Step 31D warning histogram (8 repeated placeholder strings) and the product observations about difficulty, anchoring, and shareability.

**Bottom line**: the experience is *structurally* strong, but a few subsystems (counterfactuals, `closest_teaching` meta text, and share) still behave like **reusable text kits** more than like **per-dilemma narration**. The ‘easy’ explanation layer often **repeats the headline** instead of translating it.

**Crisis note**: a dedicated **Safety** card appears for self-harm-adjacent input, but the rest of the page can still import **incongruent templates**; that mismatch is a copy-risk even when the safety line itself is good.

## Aggregate metrics

- **Readability (not 'clear') label counts**: {'verbose': 71, 'hard': 1}
- **Simple explanation failures (placeholder/missing/too_hard/not_contextual)**: {'placeholder': 12, 'not_contextual': 12}
- **Context linkage issues (weak/generic/missing)**: {'generic': 13, 'weak': 8}
- **Counterfactual cards flagged (generic/weak/templated)**: 11
- **Share cards flagged (hook/context)**: 5
- **Safety tone concern events (borderline/concerning)**: 6
- **Safety tone: concerning card refs**: ['crisis_self_harm_adjacent_input:counterfactuals']

## Top repeated placeholder strings (from Step 31D histogram)

1. **8×** — `The engine did not select a direct verse_match for this case. This card preserves the existing closest_teaching fallback`
2. **6×** — `One honest conversation with specifics, then space or support—not a courtroom.`
3. **6×** — `Optimize for relief or leverage now; let clarity arrive later if at all.`
4. **5×** — `The line moves when method stops being accountable. The slip is believable because it feels efficient.`
5. **5×** — `The upgrade is procedural: same situation, clearer safeguards—so the trade you are in stays honest.`
6. **5×** — `Move now with partial transparency; tidy the record later if pressed.`
7. **5×** — `One bounded, reviewable move before anything irreversible.`
8. **4×** — `Write a short paragraph you would stand by if forwarded—then send it once, to the smallest circle that can act on it; le`

## Top 5 product copy issues

1. Counterfactuals recycle the same likely-decision/why text across many dilemmas, reading like a default branch, not a scenario fork.
2. Closest teaching surfaces engine/meta language and explicitly lacks a Gita quote anchor, which together feel 'unsupported' to users even when honest.
3. Plain language sections often repeat the primary line (guidance + higher path), so the 'easy' layer is not a second pass.
4. If-you-continue short-term lines are the densest/most metaphorical, so they do not function as a simple time horizon for a general user.
5. Share layer is aphorism-first and weakly scene-anchored; crisis-adjacent input makes this mismatch acute.

## Case-by-case audit

### wallet_found_cash

- **Prompt (excerpt)**: I found a wallet with cash and an ID in a cafe, and I am tempted to keep the cash because my rent is due.
- **Guidance branch / verse ref**: verse_match / 6.5

#### verdict — Verdict

- **readability**: verbose
- **context_specificity**: strong
- **simple_explanation_quality**: useful
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: The headline is often strong, but expandable text can load abstract moral language quickly, which is where the product can feel 'correct but not easy'.

- **Excerpt (visible primary)**: Taking the cash would transform financial pressure into moral compromise, creating a burden heavier than rent.

- **Improvement direction**: Start with plain, concrete language tied to the user's story; add broader framing as a follow-on, not the opener.

#### guidance — Gita Verse

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: placeholder
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: A verse is present, but the 'Explain simply' can repeat the primary blurb instead of a second, simpler pass.

- **Excerpt (visible primary)**: You become either your own ally or your own saboteur through action. It speaks directly to the tension around action, restraint. It also fits signals like found-property in your situation. Its emphasis aligns with the dominant ethical pull in this dilemma.

- **Improvement direction**: Make 'Explain simply' a rephrase, not a repeat, and add a single 'what this would look like tomorrow' line grounded in the scenario.

#### if-you-continue — If You Continue

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Short-term/long-term exists, but the short-term line is often the densest—exactly the opposite of a simple 'near horizon' read.

- **Excerpt (visible primary)**: Short-term: You buy days of relief by polishing your inner narration and dodging the one detail you do not want said aloud. (Normalizing theft as acceptable when personally convenient gets louder when nothing is named.) Long-term: You get fluent at plausible deniability—not as a villain move, but as a fatigue move.

- **Improvement direction**: Force short-term to be a concrete 7–30 day consequence; long-term a stable pattern/identity; align metaphors to the setting (work vs. money vs. care vs. family).

#### counterfactuals — Counterfactuals

- **readability**: verbose
- **context_specificity**: generic
- **simple_explanation_quality**: n/a
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The same likely-decision/why text shows up in multiple dilemmas, which overwhelms the otherwise careful primary framing.

- **Excerpt (visible primary)**: Adharmic path: Move now with partial transparency; tidy the record later if pressed. Dharmic path: One bounded, reviewable move before anything irreversible.

- **Improvement direction**: Rewrite likely paths per dilemma class: keep the structure, but change stakes, objects, and failure modes so it cannot be mistaken for a generic kit.

- **Flags**:
  - **repeated_path_templates**: Primary path lines and the 'why' lines match repeated 31D placeholder histogram patterns across cases.

#### higher-path — Higher Path

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: not_contextual
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The step can be good, but 'Explain simply' often duplicates the action line, and some placeholders/ellipses read unfinished in capture.

- **Excerpt (visible primary)**: Name Financial desperation overriding moral compass without adjectives for sixty seconds on paper; delete the story lines; pick the smallest external step that still matches what is left.

- **Improvement direction**: Remove ellipsis placeholders; put a true 'simple' line under the action, not a duplicate.

#### ethical-dimensions — Ethical Dimensions

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: n/a
- **safety_tone**: n/a

- **Human judgment**: Simple meanings are doing real work, but the full grid can still feel like scoring without a single, plain 'what next' sentence—especially if duty/violation language lands harshly in acute distress.

- **Excerpt (visible primary)**: Adharmic (-75)

- **Improvement direction**: Add a single, plain 'so what' action gloss for the set (or per pair of dimensions) without adding schema fields in engine output. For crisis inputs, keep duty language gentle and support-forward.

#### share — Share Layer

- **readability**: clear
- **context_specificity**: acceptable
- **simple_explanation_quality**: n/a
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: Aphorism mode can be polished, but it is usually not a strong, scene-specific share hook.

- **Excerpt (visible primary)**: Most costly moves are not malice—they are hurry with good adjectives.

- **Improvement direction**: Build share copy from 2 on-scene anchors + 1 question; suppress or replace share in crisis/self-harm adjacency.

### manager_takes_credit_public_correction

- **Prompt (excerpt)**: My manager publicly took credit for my work, and I am considering correcting the record in the same public meeting.
- **Guidance branch / verse ref**: closest_teaching / None
- **Closest teaching special checks**:
  - **no_visible_gita_anchor**: UI shows concept guidance without a named verse/quote, so the teaching can read 'unsupported' (even if that is the intended product tradeoff).
  - **engine_process_visible**: User-visible copy still explains match thresholds and engine fallbacks, which is product meta, not a teaching frame.
  - **unsupported_feeling_risk**: The card is explicit about 'not a quote', which is honest but increases the 'weak without anchor' user perception.

#### verdict — Verdict

- **readability**: verbose
- **context_specificity**: strong
- **simple_explanation_quality**: useful
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: The headline is often strong, but expandable text can load abstract moral language quickly, which is where the product can feel 'correct but not easy'.

- **Excerpt (visible primary)**: Correcting the record publicly serves truth but requires skillful timing and tone to avoid workplace disruption.

- **Improvement direction**: Start with plain, concrete language tied to the user's story; add broader framing as a follow-on, not the opener.

#### guidance — Closest Teaching

- **readability**: verbose
- **context_specificity**: weak
- **simple_explanation_quality**: placeholder
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Closest teaching is transparent about 'no direct quote', but the visible 'engine' explanation can make the card read like a system label.

- **Excerpt (visible primary)**: No single verse clears the match threshold, but the closest Gita lens here is clean intention before action. This is concept-level guidance, not a scripture quote. The pull here is mixed, not one-dimensional. The framing is useful, while the modern details still need case-level judgment.

- **Improvement direction**: Teach the lens in human language; remove any engine/QA phrasing; keep the honesty of 'not a direct quote' without product jargon (no new verse metadata).

#### if-you-continue — If You Continue

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Short-term/long-term exists, but the short-term line is often the densest—exactly the opposite of a simple 'near horizon' read.

- **Excerpt (visible primary)**: Short-term: You trade focus for vigilance: small wins in meetings, larger tabs kept open on who said what. (Ego-driven reaction could escalate into ongoing workplace conflict gets louder when nothing is named.) Long-term: What people remember is how pressure felt in the room; the factual record stops being the headline.

- **Improvement direction**: Force short-term to be a concrete 7–30 day consequence; long-term a stable pattern/identity; align metaphors to the setting (work vs. money vs. care vs. family).

#### counterfactuals — Counterfactuals

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: n/a
- **shareability**: not_shareable
- **safety_tone**: n/a

- **Human judgment**: The same likely-decision/why text shows up in multiple dilemmas, which overwhelms the otherwise careful primary framing.

- **Excerpt (visible primary)**: Adharmic path: Win the room or the narrative first; fix the record only if forced. Dharmic path: Private specificity first, written follow-up, public only as a bounded last step.

- **Improvement direction**: Rewrite likely paths per dilemma class: keep the structure, but change stakes, objects, and failure modes so it cannot be mistaken for a generic kit.

#### higher-path — Higher Path

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: not_contextual
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The step can be good, but 'Explain simply' often duplicates the action line, and some placeholders/ellipses read unfinished in capture.

- **Excerpt (visible primary)**: Put the dispute in one email thread with specifics and dates; ask for a correction window; if none, attach the same packet to whoever owns integrity reviews—keep the audience shrinking, not growing.

- **Improvement direction**: Remove ellipsis placeholders; put a true 'simple' line under the action, not a duplicate.

#### ethical-dimensions — Ethical Dimensions

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: n/a
- **safety_tone**: n/a

- **Human judgment**: Simple meanings are doing real work, but the full grid can still feel like scoring without a single, plain 'what next' sentence—especially if duty/violation language lands harshly in acute distress.

- **Excerpt (visible primary)**: Mixed (15)

- **Improvement direction**: Add a single, plain 'so what' action gloss for the set (or per pair of dimensions) without adding schema fields in engine output. For crisis inputs, keep duty language gentle and support-forward.

#### share — Share Layer

- **readability**: clear
- **context_specificity**: acceptable
- **simple_explanation_quality**: n/a
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: Aphorism mode can be polished, but it is usually not a strong, scene-specific share hook.

- **Excerpt (visible primary)**: Public truth can be righteous and still train the room to remember your tone, not the theft.

- **Improvement direction**: Build share copy from 2 on-scene anchors + 1 question; suppress or replace share in crisis/self-harm adjacency.

- **Flags**:
  - **question_fragment_or_templatey**: Reflective question looks templated (ellipsis fragments, reused counterfactual phrasing in the question).

### legal_alcohol_shop

- **Prompt (excerpt)**: I can legally open an alcohol shop in my neighborhood, but I worry it may increase harm even though it would support my family.
- **Guidance branch / verse ref**: verse_match / 18.47

#### verdict — Verdict

- **readability**: verbose
- **context_specificity**: strong
- **simple_explanation_quality**: useful
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: The headline is often strong, but expandable text can load abstract moral language quickly, which is where the product can feel 'correct but not easy'.

- **Excerpt (visible primary)**: Legal business rights don't override the predictable harm of increasing alcohol dependency in your community.

- **Improvement direction**: Start with plain, concrete language tied to the user's story; add broader framing as a follow-on, not the opener.

#### guidance — Gita Verse

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: placeholder
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: A verse is present, but the 'Explain simply' can repeat the primary blurb instead of a second, simpler pass.

- **Excerpt (visible primary)**: Work aligned with your nature is preferable to borrowed ideals. It speaks directly to the tension around duty, right-livelihood. It also fits signals like career-crossroads, livelihood-harm-tradeoff in your situation. Its emphasis aligns with the dominant ethical pull in this dilemma.

- **Improvement direction**: Make 'Explain simply' a rephrase, not a repeat, and add a single 'what this would look like tomorrow' line grounded in the scenario.

#### if-you-continue — If You Continue

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Short-term/long-term exists, but the short-term line is often the densest—exactly the opposite of a simple 'near horizon' read.

- **Excerpt (visible primary)**: Short-term: Relief if you vent sideways: someone else carries the stress as gossip instead of as information. (Normalizing harm as acceptable cost of economic survival gets louder when nothing is named.) Long-term: Trust becomes positional: who is 'in' on edits to the story, and which facts stop traveling with the kids.

- **Improvement direction**: Force short-term to be a concrete 7–30 day consequence; long-term a stable pattern/identity; align metaphors to the setting (work vs. money vs. care vs. family).

#### counterfactuals — Counterfactuals

- **readability**: verbose
- **context_specificity**: generic
- **simple_explanation_quality**: n/a
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The same likely-decision/why text shows up in multiple dilemmas, which overwhelms the otherwise careful primary framing.

- **Excerpt (visible primary)**: Adharmic path: Optimize for relief or leverage now; let clarity arrive later if at all. Dharmic path: One honest conversation with specifics, then space or support—not a courtroom.

- **Improvement direction**: Rewrite likely paths per dilemma class: keep the structure, but change stakes, objects, and failure modes so it cannot be mistaken for a generic kit.

#### higher-path — Higher Path

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: not_contextual
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The step can be good, but 'Explain simply' often duplicates the action line, and some placeholders/ellipses read unfinished in capture.

- **Excerpt (visible primary)**: Write a short paragraph you would stand by if forwarded—then send it once, to the smallest circle that can act on it; let silence after that be a choice, not a dodge.

- **Improvement direction**: Remove ellipsis placeholders; put a true 'simple' line under the action, not a duplicate.

#### ethical-dimensions — Ethical Dimensions

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: n/a
- **safety_tone**: n/a

- **Human judgment**: Simple meanings are doing real work, but the full grid can still feel like scoring without a single, plain 'what next' sentence—especially if duty/violation language lands harshly in acute distress.

- **Excerpt (visible primary)**: Mixed (-28)

- **Improvement direction**: Add a single, plain 'so what' action gloss for the set (or per pair of dimensions) without adding schema fields in engine output. For crisis inputs, keep duty language gentle and support-forward.

#### share — Share Layer

- **readability**: clear
- **context_specificity**: acceptable
- **simple_explanation_quality**: n/a
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: Aphorism mode can be polished, but it is usually not a strong, scene-specific share hook.

- **Excerpt (visible primary)**: Intimacy is not a license to edit someone else's information for your comfort.

- **Improvement direction**: Build share copy from 2 on-scene anchors + 1 question; suppress or replace share in crisis/self-harm adjacency.

### friends_partner_desire

- **Prompt (excerpt)**: I have developed desire for my close friend's partner, and they seem interested too, but acting on it would betray my friend.
- **Guidance branch / verse ref**: closest_teaching / None
- **Closest teaching special checks**:
  - **no_visible_gita_anchor**: UI shows concept guidance without a named verse/quote, so the teaching can read 'unsupported' (even if that is the intended product tradeoff).
  - **engine_process_visible**: User-visible copy still explains match thresholds and engine fallbacks, which is product meta, not a teaching frame.

#### verdict — Verdict

- **readability**: verbose
- **context_specificity**: strong
- **simple_explanation_quality**: useful
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: The headline is often strong, but expandable text can load abstract moral language quickly, which is where the product can feel 'correct but not easy'.

- **Excerpt (visible primary)**: This attraction tests whether you value momentary chemistry over established trust and friendship.

- **Improvement direction**: Start with plain, concrete language tied to the user's story; add broader framing as a follow-on, not the opener.

#### guidance — Closest Teaching

- **readability**: verbose
- **context_specificity**: weak
- **simple_explanation_quality**: placeholder
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Closest teaching is transparent about 'no direct quote', but the visible 'engine' explanation can make the card read like a system label.

- **Excerpt (visible primary)**: No specific verse cleared the threshold for this case. The Gita still offers useful lenses through duty, intention, non-harm, restraint, and welfare-of-all, but this modern structure does not map cleanly to one verse without forced certainty.

- **Improvement direction**: Teach the lens in human language; remove any engine/QA phrasing; keep the honesty of 'not a direct quote' without product jargon (no new verse metadata).

#### if-you-continue — If You Continue

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Short-term/long-term exists, but the short-term line is often the densest—exactly the opposite of a simple 'near horizon' read.

- **Excerpt (visible primary)**: Short-term: Short term you win quiet at the dinner table; the hardest sentence does not get spoken where it belongs. (Using 'mutual attraction' to rationalize betrayal while avoiding… gets louder when nothing is named.) Long-term: Trust becomes positional: who is 'in' on edits to the story, and which facts stop traveling with the kids.

- **Improvement direction**: Force short-term to be a concrete 7–30 day consequence; long-term a stable pattern/identity; align metaphors to the setting (work vs. money vs. care vs. family).

#### counterfactuals — Counterfactuals

- **readability**: verbose
- **context_specificity**: generic
- **simple_explanation_quality**: n/a
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The same likely-decision/why text shows up in multiple dilemmas, which overwhelms the otherwise careful primary framing.

- **Excerpt (visible primary)**: Adharmic path: Optimize for relief or leverage now; let clarity arrive later if at all. Dharmic path: One honest conversation with specifics, then space or support—not a courtroom.

- **Improvement direction**: Rewrite likely paths per dilemma class: keep the structure, but change stakes, objects, and failure modes so it cannot be mistaken for a generic kit.

#### higher-path — Higher Path

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: not_contextual
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The step can be good, but 'Explain simply' often duplicates the action line, and some placeholders/ellipses read unfinished in capture.

- **Excerpt (visible primary)**: Tell the one person who truly needs the fact first, in one sitting, with no audience; refuse to triangulate through kids or group chats; schedule a second conversation instead of a second performance.

- **Improvement direction**: Remove ellipsis placeholders; put a true 'simple' line under the action, not a duplicate.

#### ethical-dimensions — Ethical Dimensions

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: n/a
- **safety_tone**: n/a

- **Human judgment**: Simple meanings are doing real work, but the full grid can still feel like scoring without a single, plain 'what next' sentence—especially if duty/violation language lands harshly in acute distress.

- **Excerpt (visible primary)**: Adharmic (-75)

- **Improvement direction**: Add a single, plain 'so what' action gloss for the set (or per pair of dimensions) without adding schema fields in engine output. For crisis inputs, keep duty language gentle and support-forward.

#### share — Share Layer

- **readability**: clear
- **context_specificity**: acceptable
- **simple_explanation_quality**: n/a
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: Aphorism mode can be polished, but it is usually not a strong, scene-specific share hook.

- **Excerpt (visible primary)**: Family peace bought with selective silence still has a receipt—someone reads it later.

- **Improvement direction**: Build share copy from 2 on-scene anchors + 1 question; suppress or replace share in crisis/self-harm adjacency.

### aging_parent_refuses_hospitalization

- **Prompt (excerpt)**: My aging parent is refusing hospitalization after a serious diagnosis, and I am torn between respecting them and forcing treatment.
- **Guidance branch / verse ref**: closest_teaching / None
- **Closest teaching special checks**:
  - **no_visible_gita_anchor**: UI shows concept guidance without a named verse/quote, so the teaching can read 'unsupported' (even if that is the intended product tradeoff).
  - **engine_process_visible**: User-visible copy still explains match thresholds and engine fallbacks, which is product meta, not a teaching frame.
  - **unsupported_feeling_risk**: The card is explicit about 'not a quote', which is honest but increases the 'weak without anchor' user perception.

#### verdict — Verdict

- **readability**: verbose
- **context_specificity**: strong
- **simple_explanation_quality**: useful
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: The headline is often strong, but expandable text can load abstract moral language quickly, which is where the product can feel 'correct but not easy'.

- **Excerpt (visible primary)**: Respecting your parent's autonomy while ensuring they understand consequences honors both their dignity and your duty of care.

- **Improvement direction**: Start with plain, concrete language tied to the user's story; add broader framing as a follow-on, not the opener.

#### guidance — Closest Teaching

- **readability**: verbose
- **context_specificity**: weak
- **simple_explanation_quality**: placeholder
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Closest teaching is transparent about 'no direct quote', but the visible 'engine' explanation can make the card read like a system label.

- **Excerpt (visible primary)**: No single verse clears the match threshold, but the closest Gita lens here is clean intention before action. This is concept-level guidance, not a scripture quote.  The framing is useful, while the modern details still need case-level judgment.

- **Improvement direction**: Teach the lens in human language; remove any engine/QA phrasing; keep the honesty of 'not a direct quote' without product jargon (no new verse metadata).

#### if-you-continue — If You Continue

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Short-term/long-term exists, but the short-term line is often the densest—exactly the opposite of a simple 'near horizon' read.

- **Excerpt (visible primary)**: Short-term: You buy a few calm days by tightening the family narrative—then the next surprise lands louder. (Conflating your anxiety about loss with their best interests gets louder when nothing is named.) Long-term: People learn what not to ask you; intimacy shrinks to what can be safely performed.

- **Improvement direction**: Force short-term to be a concrete 7–30 day consequence; long-term a stable pattern/identity; align metaphors to the setting (work vs. money vs. care vs. family).

#### counterfactuals — Counterfactuals

- **readability**: verbose
- **context_specificity**: generic
- **simple_explanation_quality**: n/a
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The same likely-decision/why text shows up in multiple dilemmas, which overwhelms the otherwise careful primary framing.

- **Excerpt (visible primary)**: Adharmic path: Optimize for relief or leverage now; let clarity arrive later if at all. Dharmic path: One honest conversation with specifics, then space or support—not a courtroom.

- **Improvement direction**: Rewrite likely paths per dilemma class: keep the structure, but change stakes, objects, and failure modes so it cannot be mistaken for a generic kit.

#### higher-path — Higher Path

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: not_contextual
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The step can be good, but 'Explain simply' often duplicates the action line, and some placeholders/ellipses read unfinished in capture.

- **Excerpt (visible primary)**: Write a short paragraph you would stand by if forwarded—then send it once, to the smallest circle that can act on it; let silence after that be a choice, not a dodge.

- **Improvement direction**: Remove ellipsis placeholders; put a true 'simple' line under the action, not a duplicate.

#### ethical-dimensions — Ethical Dimensions

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: n/a
- **safety_tone**: n/a

- **Human judgment**: Simple meanings are doing real work, but the full grid can still feel like scoring without a single, plain 'what next' sentence—especially if duty/violation language lands harshly in acute distress.

- **Excerpt (visible primary)**: Dharmic (40)

- **Improvement direction**: Add a single, plain 'so what' action gloss for the set (or per pair of dimensions) without adding schema fields in engine output. For crisis inputs, keep duty language gentle and support-forward.

#### share — Share Layer

- **readability**: clear
- **context_specificity**: generic
- **simple_explanation_quality**: n/a
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: Aphorism mode can be polished, but it is usually not a strong, scene-specific share hook.

- **Excerpt (visible primary)**: The gentlest story can still steer someone if they never get to see the full map.

- **Improvement direction**: Build share copy from 2 on-scene anchors + 1 question; suppress or replace share in crisis/self-harm adjacency.

- **Flags**:
  - **question_fragment_or_templatey**: Reflective question looks templated (ellipsis fragments, reused counterfactual phrasing in the question).
  - **low_prompt_overlap**: Share layer does not reuse concrete tokens from the user's dilemma beyond generic ethics language.

### cosmetic_surgery

- **Prompt (excerpt)**: I am considering cosmetic surgery mainly because I feel insecure and want social approval, though the procedure is legal and safe.
- **Guidance branch / verse ref**: closest_teaching / None
- **Closest teaching special checks**:
  - **no_visible_gita_anchor**: UI shows concept guidance without a named verse/quote, so the teaching can read 'unsupported' (even if that is the intended product tradeoff).
  - **engine_process_visible**: User-visible copy still explains match thresholds and engine fallbacks, which is product meta, not a teaching frame.
  - **unsupported_feeling_risk**: The card is explicit about 'not a quote', which is honest but increases the 'weak without anchor' user perception.

#### verdict — Verdict

- **readability**: verbose
- **context_specificity**: strong
- **simple_explanation_quality**: useful
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: The headline is often strong, but expandable text can load abstract moral language quickly, which is where the product can feel 'correct but not easy'.

- **Excerpt (visible primary)**: Seeking surgical validation for social insecurity typically deepens the very wound it promises to heal.

- **Improvement direction**: Start with plain, concrete language tied to the user's story; add broader framing as a follow-on, not the opener.

#### guidance — Closest Teaching

- **readability**: verbose
- **context_specificity**: weak
- **simple_explanation_quality**: placeholder
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Closest teaching is transparent about 'no direct quote', but the visible 'engine' explanation can make the card read like a system label.

- **Excerpt (visible primary)**: No single verse clears the match threshold, but the closest Gita lens here is discernment over emotional rush. This is concept-level guidance, not a scripture quote. Related grounding appears in Chapter 6.  The framing is useful, while the modern details still need case-level judgment.

- **Improvement direction**: Teach the lens in human language; remove any engine/QA phrasing; keep the honesty of 'not a direct quote' without product jargon (no new verse metadata).

#### if-you-continue — If You Continue

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Short-term/long-term exists, but the short-term line is often the densest—exactly the opposite of a simple 'near horizon' read.

- **Excerpt (visible primary)**: Short-term: Short term the room relaxes; you pay in private rumination and sharper self-editing. (Surgery may temporarily boost confidence but leave core insecurity… gets louder when nothing is named.) Long-term: What starts as a one-time smoothing becomes the default tool whenever stakes rise.

- **Improvement direction**: Force short-term to be a concrete 7–30 day consequence; long-term a stable pattern/identity; align metaphors to the setting (work vs. money vs. care vs. family).

#### counterfactuals — Counterfactuals

- **readability**: verbose
- **context_specificity**: generic
- **simple_explanation_quality**: n/a
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The same likely-decision/why text shows up in multiple dilemmas, which overwhelms the otherwise careful primary framing.

- **Excerpt (visible primary)**: Adharmic path: Move now with partial transparency; tidy the record later if pressed. Dharmic path: One bounded, reviewable move before anything irreversible.

- **Improvement direction**: Rewrite likely paths per dilemma class: keep the structure, but change stakes, objects, and failure modes so it cannot be mistaken for a generic kit.

- **Flags**:
  - **repeated_path_templates**: Primary path lines and the 'why' lines match repeated 31D placeholder histogram patterns across cases.

#### higher-path — Higher Path

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: not_contextual
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The step can be good, but 'Explain simply' often duplicates the action line, and some placeholders/ellipses read unfinished in capture.

- **Excerpt (visible primary)**: Name Fear of social rejection and belief that acceptance requires physical perfection without adjectives for sixty seconds on paper; delete the story lines; pick the smallest external step that still matches what is left.

- **Improvement direction**: Remove ellipsis placeholders; put a true 'simple' line under the action, not a duplicate.

#### ethical-dimensions — Ethical Dimensions

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: n/a
- **safety_tone**: n/a

- **Human judgment**: Simple meanings are doing real work, but the full grid can still feel like scoring without a single, plain 'what next' sentence—especially if duty/violation language lands harshly in acute distress.

- **Excerpt (visible primary)**: Adharmic (-48)

- **Improvement direction**: Add a single, plain 'so what' action gloss for the set (or per pair of dimensions) without adding schema fields in engine output. For crisis inputs, keep duty language gentle and support-forward.

#### share — Share Layer

- **readability**: clear
- **context_specificity**: acceptable
- **simple_explanation_quality**: n/a
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: Aphorism mode can be polished, but it is usually not a strong, scene-specific share hook.

- **Excerpt (visible primary)**: Clarity without restraint becomes noise; restraint without clarity becomes drift.

- **Improvement direction**: Build share copy from 2 on-scene anchors + 1 question; suppress or replace share in crisis/self-harm adjacency.

### abusive_parent_no_contact

- **Prompt (excerpt)**: My parent was abusive for years, and I am considering going no contact even though relatives say it is my duty to stay connected.
- **Guidance branch / verse ref**: closest_teaching / None
- **Closest teaching special checks**:
  - **no_visible_gita_anchor**: UI shows concept guidance without a named verse/quote, so the teaching can read 'unsupported' (even if that is the intended product tradeoff).
  - **engine_process_visible**: User-visible copy still explains match thresholds and engine fallbacks, which is product meta, not a teaching frame.
  - **unsupported_feeling_risk**: The card is explicit about 'not a quote', which is honest but increases the 'weak without anchor' user perception.

#### verdict — Verdict

- **readability**: verbose
- **context_specificity**: strong
- **simple_explanation_quality**: useful
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: The headline is often strong, but expandable text can load abstract moral language quickly, which is where the product can feel 'correct but not easy'.

- **Excerpt (visible primary)**: Protecting yourself from ongoing harm takes precedence over maintaining harmful family connections out of obligation.

- **Improvement direction**: Start with plain, concrete language tied to the user's story; add broader framing as a follow-on, not the opener.

#### guidance — Closest Teaching

- **readability**: verbose
- **context_specificity**: weak
- **simple_explanation_quality**: placeholder
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Closest teaching is transparent about 'no direct quote', but the visible 'engine' explanation can make the card read like a system label.

- **Excerpt (visible primary)**: No single verse clears the match threshold, but the closest Gita lens here is clean intention before action. This is concept-level guidance, not a scripture quote. Related grounding appears in Chapter 6. The dilemma turns on missing context, so this stays provisional. The framing is useful, while the modern details still need case-level judgment.

- **Improvement direction**: Teach the lens in human language; remove any engine/QA phrasing; keep the honesty of 'not a direct quote' without product jargon (no new verse metadata).

#### if-you-continue — If You Continue

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Short-term/long-term exists, but the short-term line is often the densest—exactly the opposite of a simple 'near horizon' read.

- **Excerpt (visible primary)**: Short-term: Short term you win quiet at the dinner table; the hardest sentence does not get spoken where it belongs. (Guilt manipulation and family system pressure gets louder when nothing is named.) Long-term: The workaround becomes habit—honesty deferred until 'after the holidays' becomes its own kind of policy.

- **Improvement direction**: Force short-term to be a concrete 7–30 day consequence; long-term a stable pattern/identity; align metaphors to the setting (work vs. money vs. care vs. family).

#### counterfactuals — Counterfactuals

- **readability**: verbose
- **context_specificity**: generic
- **simple_explanation_quality**: n/a
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The same likely-decision/why text shows up in multiple dilemmas, which overwhelms the otherwise careful primary framing.

- **Excerpt (visible primary)**: Adharmic path: Optimize for relief or leverage now; let clarity arrive later if at all. Dharmic path: One honest conversation with specifics, then space or support—not a courtroom.

- **Improvement direction**: Rewrite likely paths per dilemma class: keep the structure, but change stakes, objects, and failure modes so it cannot be mistaken for a generic kit.

#### higher-path — Higher Path

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: not_contextual
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The step can be good, but 'Explain simply' often duplicates the action line, and some placeholders/ellipses read unfinished in capture.

- **Excerpt (visible primary)**: Write a short paragraph you would stand by if forwarded—then send it once, to the smallest circle that can act on it; let silence after that be a choice, not a dodge.

- **Improvement direction**: Remove ellipsis placeholders; put a true 'simple' line under the action, not a duplicate.

#### ethical-dimensions — Ethical Dimensions

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: n/a
- **safety_tone**: n/a

- **Human judgment**: Simple meanings are doing real work, but the full grid can still feel like scoring without a single, plain 'what next' sentence—especially if duty/violation language lands harshly in acute distress.

- **Excerpt (visible primary)**: Context-dependent (42)

- **Improvement direction**: Add a single, plain 'so what' action gloss for the set (or per pair of dimensions) without adding schema fields in engine output. For crisis inputs, keep duty language gentle and support-forward.

#### share — Share Layer

- **readability**: clear
- **context_specificity**: acceptable
- **simple_explanation_quality**: n/a
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: Aphorism mode can be polished, but it is usually not a strong, scene-specific share hook.

- **Excerpt (visible primary)**: Family peace bought with selective silence still has a receipt—someone reads it later.

- **Improvement direction**: Build share copy from 2 on-scene anchors + 1 question; suppress or replace share in crisis/self-harm adjacency.

### caste_disapproved_marriage

- **Prompt (excerpt)**: I want to marry someone I love, but my family rejects the relationship because of caste and threatens to cut ties.
- **Guidance branch / verse ref**: verse_match / 5.18

#### verdict — Verdict

- **readability**: verbose
- **context_specificity**: strong
- **simple_explanation_quality**: useful
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: The headline is often strong, but expandable text can load abstract moral language quickly, which is where the product can feel 'correct but not easy'.

- **Excerpt (visible primary)**: Choosing authentic love over caste prejudice reflects evolved consciousness, though the family rupture carries real weight.

- **Improvement direction**: Start with plain, concrete language tied to the user's story; add broader framing as a follow-on, not the opener.

#### guidance — Gita Verse

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: placeholder
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: A verse is present, but the 'Explain simply' can repeat the primary blurb instead of a second, simpler pass.

- **Excerpt (visible primary)**: A wise person sees equal dignity across social categories. It speaks directly to the tension around compassion, equality. It also fits signals like caste-or-identity-boundary, family-disapproval in your situation. Its emphasis aligns with the dominant ethical pull in this dilemma.

- **Improvement direction**: Make 'Explain simply' a rephrase, not a repeat, and add a single 'what this would look like tomorrow' line grounded in the scenario.

#### if-you-continue — If You Continue

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Short-term/long-term exists, but the short-term line is often the densest—exactly the opposite of a simple 'near horizon' read.

- **Excerpt (visible primary)**: Short-term: You buy a few calm days by tightening the family narrative—then the next surprise lands louder. (Underestimating the psychological toll of family estrangement gets louder when nothing is named.) Long-term: People learn what not to ask you; intimacy shrinks to what can be safely performed.

- **Improvement direction**: Force short-term to be a concrete 7–30 day consequence; long-term a stable pattern/identity; align metaphors to the setting (work vs. money vs. care vs. family).

#### counterfactuals — Counterfactuals

- **readability**: verbose
- **context_specificity**: generic
- **simple_explanation_quality**: n/a
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The same likely-decision/why text shows up in multiple dilemmas, which overwhelms the otherwise careful primary framing.

- **Excerpt (visible primary)**: Adharmic path: Optimize for relief or leverage now; let clarity arrive later if at all. Dharmic path: One honest conversation with specifics, then space or support—not a courtroom.

- **Improvement direction**: Rewrite likely paths per dilemma class: keep the structure, but change stakes, objects, and failure modes so it cannot be mistaken for a generic kit.

#### higher-path — Higher Path

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: not_contextual
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The step can be good, but 'Explain simply' often duplicates the action line, and some placeholders/ellipses read unfinished in capture.

- **Excerpt (visible primary)**: Write a short paragraph you would stand by if forwarded—then send it once, to the smallest circle that can act on it; let silence after that be a choice, not a dodge.

- **Improvement direction**: Remove ellipsis placeholders; put a true 'simple' line under the action, not a duplicate.

#### ethical-dimensions — Ethical Dimensions

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: n/a
- **safety_tone**: n/a

- **Human judgment**: Simple meanings are doing real work, but the full grid can still feel like scoring without a single, plain 'what next' sentence—especially if duty/violation language lands harshly in acute distress.

- **Excerpt (visible primary)**: Mixed (28)

- **Improvement direction**: Add a single, plain 'so what' action gloss for the set (or per pair of dimensions) without adding schema fields in engine output. For crisis inputs, keep duty language gentle and support-forward.

#### share — Share Layer

- **readability**: clear
- **context_specificity**: acceptable
- **simple_explanation_quality**: n/a
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: Aphorism mode can be polished, but it is usually not a strong, scene-specific share hook.

- **Excerpt (visible primary)**: The gentlest story can still steer someone if they never get to see the full map.

- **Improvement direction**: Build share copy from 2 on-scene anchors + 1 question; suppress or replace share in crisis/self-harm adjacency.

### anonymous_scathing_restaurant_review

- **Prompt (excerpt)**: A restaurant treated me badly, and I want to post an anonymous scathing review that might damage their business reputation.
- **Guidance branch / verse ref**: closest_teaching / None
- **Closest teaching special checks**:
  - **no_visible_gita_anchor**: UI shows concept guidance without a named verse/quote, so the teaching can read 'unsupported' (even if that is the intended product tradeoff).
  - **engine_process_visible**: User-visible copy still explains match thresholds and engine fallbacks, which is product meta, not a teaching frame.
  - **unsupported_feeling_risk**: The card is explicit about 'not a quote', which is honest but increases the 'weak without anchor' user perception.

#### verdict — Verdict

- **readability**: hard
- **context_specificity**: strong
- **simple_explanation_quality**: useful
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: The headline is often strong, but expandable text can load abstract moral language quickly, which is where the product can feel 'correct but not easy'.

- **Excerpt (visible primary)**: Anonymous revenge reviews weaponize truth claims to inflict maximum damage while avoiding accountability.

- **Improvement direction**: Start with plain, concrete language tied to the user's story; add broader framing as a follow-on, not the opener.

#### guidance — Closest Teaching

- **readability**: verbose
- **context_specificity**: weak
- **simple_explanation_quality**: placeholder
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Closest teaching is transparent about 'no direct quote', but the visible 'engine' explanation can make the card read like a system label.

- **Excerpt (visible primary)**: No single verse clears the match threshold, but the closest Gita lens here is inner restraint before reaction. This is concept-level guidance, not a scripture quote. Related grounding appears in Chapter 17.  The framing is useful, while the modern details still need case-level judgment.

- **Improvement direction**: Teach the lens in human language; remove any engine/QA phrasing; keep the honesty of 'not a direct quote' without product jargon (no new verse metadata).

#### if-you-continue — If You Continue

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Short-term/long-term exists, but the short-term line is often the densest—exactly the opposite of a simple 'near horizon' read.

- **Excerpt (visible primary)**: Short-term: Short term the room relaxes; you pay in private rumination and sharper self-editing. (Creating a pattern of anonymous aggression when feeling wronged gets louder when nothing is named.) Long-term: The workaround becomes character: faster stories, cleaner self-image, a smaller circle that actually knows what is true.

- **Improvement direction**: Force short-term to be a concrete 7–30 day consequence; long-term a stable pattern/identity; align metaphors to the setting (work vs. money vs. care vs. family).

#### counterfactuals — Counterfactuals

- **readability**: verbose
- **context_specificity**: generic
- **simple_explanation_quality**: n/a
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The same likely-decision/why text shows up in multiple dilemmas, which overwhelms the otherwise careful primary framing.

- **Excerpt (visible primary)**: Adharmic path: Move now with partial transparency; tidy the record later if pressed. Dharmic path: One bounded, reviewable move before anything irreversible.

- **Improvement direction**: Rewrite likely paths per dilemma class: keep the structure, but change stakes, objects, and failure modes so it cannot be mistaken for a generic kit.

- **Flags**:
  - **repeated_path_templates**: Primary path lines and the 'why' lines match repeated 31D placeholder histogram patterns across cases.

#### higher-path — Higher Path

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: not_contextual
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The step can be good, but 'Explain simply' often duplicates the action line, and some placeholders/ellipses read unfinished in capture.

- **Excerpt (visible primary)**: Before you act, write Creating a pattern of anonymous aggression when feeling wronged as a single observable sentence; strip blame; choose the channel where repair is still possible—not the channel where you win.

- **Improvement direction**: Remove ellipsis placeholders; put a true 'simple' line under the action, not a duplicate.

#### ethical-dimensions — Ethical Dimensions

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: n/a
- **safety_tone**: n/a

- **Human judgment**: Simple meanings are doing real work, but the full grid can still feel like scoring without a single, plain 'what next' sentence—especially if duty/violation language lands harshly in acute distress.

- **Excerpt (visible primary)**: Adharmic (-62)

- **Improvement direction**: Add a single, plain 'so what' action gloss for the set (or per pair of dimensions) without adding schema fields in engine output. For crisis inputs, keep duty language gentle and support-forward.

#### share — Share Layer

- **readability**: clear
- **context_specificity**: acceptable
- **simple_explanation_quality**: n/a
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: Aphorism mode can be polished, but it is usually not a strong, scene-specific share hook.

- **Excerpt (visible primary)**: Clarity without restraint becomes noise; restraint without clarity becomes drift.

- **Improvement direction**: Build share copy from 2 on-scene anchors + 1 question; suppress or replace share in crisis/self-harm adjacency.

### doctor_hiding_terminal_diagnosis

- **Prompt (excerpt)**: As a doctor, I know a patient has a terminal diagnosis, and the family asks me to hide it from the patient to preserve hope.
- **Guidance branch / verse ref**: verse_match / 16.1-3

#### verdict — Verdict

- **readability**: verbose
- **context_specificity**: strong
- **simple_explanation_quality**: useful
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: The headline is often strong, but expandable text can load abstract moral language quickly, which is where the product can feel 'correct but not easy'.

- **Excerpt (visible primary)**: Withholding terminal diagnosis from a competent patient violates their fundamental right to truth and self-determination.

- **Improvement direction**: Start with plain, concrete language tied to the user's story; add broader framing as a follow-on, not the opener.

#### guidance — Gita Verse

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: placeholder
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: A verse is present, but the 'Explain simply' can repeat the primary blurb instead of a second, simpler pass.

- **Excerpt (visible primary)**: Divine qualities hold truth and compassion together. It speaks directly to the tension around compassion, nonharm. It also fits signals like truth-compassion-conflict in your situation. Its emphasis aligns with the dominant ethical pull in this dilemma.

- **Improvement direction**: Make 'Explain simply' a rephrase, not a repeat, and add a single 'what this would look like tomorrow' line grounded in the scenario.

#### if-you-continue — If You Continue

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Short-term/long-term exists, but the short-term line is often the densest—exactly the opposite of a simple 'near horizon' read.

- **Excerpt (visible primary)**: Short-term: You buy a few calm days by tightening the family narrative—then the next surprise lands louder. (Creating complicity in deception that erodes professional integrity gets louder when nothing is named.) Long-term: The workaround becomes habit—honesty deferred until 'after the holidays' becomes its own kind of policy.

- **Improvement direction**: Force short-term to be a concrete 7–30 day consequence; long-term a stable pattern/identity; align metaphors to the setting (work vs. money vs. care vs. family).

#### counterfactuals — Counterfactuals

- **readability**: verbose
- **context_specificity**: generic
- **simple_explanation_quality**: n/a
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The same likely-decision/why text shows up in multiple dilemmas, which overwhelms the otherwise careful primary framing.

- **Excerpt (visible primary)**: Adharmic path: Optimize for relief or leverage now; let clarity arrive later if at all. Dharmic path: One honest conversation with specifics, then space or support—not a courtroom.

- **Improvement direction**: Rewrite likely paths per dilemma class: keep the structure, but change stakes, objects, and failure modes so it cannot be mistaken for a generic kit.

#### higher-path — Higher Path

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: not_contextual
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The step can be good, but 'Explain simply' often duplicates the action line, and some placeholders/ellipses read unfinished in capture.

- **Excerpt (visible primary)**: Name the trade in one sentence your future self would sign; pick the channel that protects dignity more than drama; end with a clear next date, not a moral flourish.

- **Improvement direction**: Remove ellipsis placeholders; put a true 'simple' line under the action, not a duplicate.

#### ethical-dimensions — Ethical Dimensions

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: n/a
- **safety_tone**: n/a

- **Human judgment**: Simple meanings are doing real work, but the full grid can still feel like scoring without a single, plain 'what next' sentence—especially if duty/violation language lands harshly in acute distress.

- **Excerpt (visible primary)**: Mixed (-35)

- **Improvement direction**: Add a single, plain 'so what' action gloss for the set (or per pair of dimensions) without adding schema fields in engine output. For crisis inputs, keep duty language gentle and support-forward.

#### share — Share Layer

- **readability**: clear
- **context_specificity**: acceptable
- **simple_explanation_quality**: n/a
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: Aphorism mode can be polished, but it is usually not a strong, scene-specific share hook.

- **Excerpt (visible primary)**: The gentlest story can still steer someone if they never get to see the full map.

- **Improvement direction**: Build share copy from 2 on-scene anchors + 1 question; suppress or replace share in crisis/self-harm adjacency.

- **Flags**:
  - **question_fragment_or_templatey**: Reflective question looks templated (ellipsis fragments, reused counterfactual phrasing in the question).

### crisis_self_harm_adjacent_input

- **Prompt (excerpt)**: I feel overwhelmed and keep thinking everyone would be better without me, and I want guidance before I do anything harmful.
- **Guidance branch / verse ref**: closest_teaching / None
- **Closest teaching special checks**:
  - **no_visible_gita_anchor**: UI shows concept guidance without a named verse/quote, so the teaching can read 'unsupported' (even if that is the intended product tradeoff).
  - **engine_process_visible**: User-visible copy still explains match thresholds and engine fallbacks, which is product meta, not a teaching frame.
  - **unsupported_feeling_risk**: The card is explicit about 'not a quote', which is honest but increases the 'weak without anchor' user perception.

#### safety — Safety Note

- **readability**: clear
- **context_specificity**: strong
- **simple_explanation_quality**: useful
- **shareability**: n/a
- **safety_tone**: safe

- **Human judgment**: Clear crisis gating: it names self-harm risk and defers to qualified human help before the rest of the analysis. Tone is not accusatory, but downstream cards need to match this posture.

- **Excerpt (visible primary)**: This may need immediate human support, not only ethical reflection.

- **Improvement direction**: Keep safety first; if other cards stay visible, ensure they are emotionally aligned and avoid mismatched 'optics' templates under crisis gating.

#### verdict — Verdict

- **readability**: verbose
- **context_specificity**: strong
- **simple_explanation_quality**: useful
- **shareability**: not_shareable
- **safety_tone**: borderline

- **Human judgment**: The headline is often strong, but expandable text can load abstract moral language quickly, which is where the product can feel 'correct but not easy'.

- **Excerpt (visible primary)**: Your life has inherent value that pain temporarily obscures, and seeking help honors both your struggle and those who care about you.

- **Improvement direction**: Start with plain, concrete language tied to the user's story; add broader framing as a follow-on, not the opener.

#### guidance — Closest Teaching

- **readability**: verbose
- **context_specificity**: weak
- **simple_explanation_quality**: placeholder
- **shareability**: n/a
- **safety_tone**: borderline

- **Human judgment**: Closest teaching is transparent about 'no direct quote', but the visible 'engine' explanation can make the card read like a system label.

- **Excerpt (visible primary)**: No single verse clears the match threshold, but the closest Gita lens here is clean intention before action. This is concept-level guidance, not a scripture quote. The pull here is mixed, not one-dimensional. The framing is useful, while the modern details still need case-level judgment.

- **Improvement direction**: Teach the lens in human language; remove any engine/QA phrasing; keep the honesty of 'not a direct quote' without product jargon (no new verse metadata).

#### if-you-continue — If You Continue

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: not_shareable
- **safety_tone**: borderline

- **Human judgment**: Short-term/long-term exists, but the short-term line is often the densest—exactly the opposite of a simple 'near horizon' read.

- **Excerpt (visible primary)**: Short-term: Short term the room relaxes; you pay in private rumination and sharper self-editing. (Depression's lie that permanence exists in temporary suffering while… gets louder when nothing is named.) Long-term: What starts as a one-time smoothing becomes the default tool whenever stakes rise.

- **Improvement direction**: Force short-term to be a concrete 7–30 day consequence; long-term a stable pattern/identity; align metaphors to the setting (work vs. money vs. care vs. family).

#### counterfactuals — Counterfactuals

- **readability**: verbose
- **context_specificity**: generic
- **simple_explanation_quality**: n/a
- **shareability**: not_shareable
- **safety_tone**: concerning

- **Human judgment**: The same likely-decision/why text shows up in multiple dilemmas, which overwhelms the otherwise careful primary framing.

- **Excerpt (visible primary)**: Adharmic path: Move now with partial transparency; tidy the record later if pressed. Dharmic path: One bounded, reviewable move before anything irreversible.

- **Improvement direction**: Rewrite likely paths per dilemma class: keep the structure, but change stakes, objects, and failure modes so it cannot be mistaken for a generic kit.

- **Flags**:
  - **repeated_path_templates**: Primary path lines and the 'why' lines match repeated 31D placeholder histogram patterns across cases.

#### higher-path — Higher Path

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: not_contextual
- **shareability**: not_shareable
- **safety_tone**: safe

- **Human judgment**: The step can be good, but 'Explain simply' often duplicates the action line, and some placeholders/ellipses read unfinished in capture.

- **Excerpt (visible primary)**: Before you act, write Depression's lie that permanence exists in temporary suffering while… as a single observable sentence; strip blame; choose the channel where repair is still possible—not the channel where you win.

- **Improvement direction**: Remove ellipsis placeholders; put a true 'simple' line under the action, not a duplicate.

#### ethical-dimensions — Ethical Dimensions

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: n/a
- **safety_tone**: borderline

- **Human judgment**: Simple meanings are doing real work, but the full grid can still feel like scoring without a single, plain 'what next' sentence—especially if duty/violation language lands harshly in acute distress.

- **Excerpt (visible primary)**: Mixed (-22)

- **Improvement direction**: Add a single, plain 'so what' action gloss for the set (or per pair of dimensions) without adding schema fields in engine output. For crisis inputs, keep duty language gentle and support-forward.

#### share — Share Layer

- **readability**: clear
- **context_specificity**: acceptable
- **simple_explanation_quality**: n/a
- **shareability**: not_shareable
- **safety_tone**: borderline

- **Human judgment**: Crisis-adjacent input should not present a generic, poster-like share string; the emotional mismatch risk is high.

- **Excerpt (visible primary)**: Clarity without restraint becomes noise; restraint without clarity becomes drift.

- **Improvement direction**: Build share copy from 2 on-scene anchors + 1 question; suppress or replace share in crisis/self-harm adjacency.

- **Flags**:
  - **question_fragment_or_templatey**: Reflective question looks templated (ellipsis fragments, reused counterfactual phrasing in the question).

### low_information_vague_input

- **Prompt (excerpt)**: I need to decide whether to do the thing soon, but I cannot share many details right now.
- **Guidance branch / verse ref**: closest_teaching / None
- **Closest teaching special checks**:
  - **no_visible_gita_anchor**: UI shows concept guidance without a named verse/quote, so the teaching can read 'unsupported' (even if that is the intended product tradeoff).
  - **engine_process_visible**: User-visible copy still explains match thresholds and engine fallbacks, which is product meta, not a teaching frame.

#### verdict — Verdict

- **readability**: verbose
- **context_specificity**: strong
- **simple_explanation_quality**: useful
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: The headline is often strong, but expandable text can load abstract moral language quickly, which is where the product can feel 'correct but not easy'.

- **Excerpt (visible primary)**: The ethical verdict turns on unresolved facts that could plausibly reverse this classification, while key facts still shape execution details.

- **Improvement direction**: Start with plain, concrete language tied to the user's story; add broader framing as a follow-on, not the opener.

#### guidance — Closest Teaching

- **readability**: verbose
- **context_specificity**: weak
- **simple_explanation_quality**: placeholder
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Closest teaching is transparent about 'no direct quote', but the visible 'engine' explanation can make the card read like a system label.

- **Excerpt (visible primary)**: No specific verse cleared the threshold for this case. The Gita still offers useful lenses through duty, intention, non-harm, restraint, and welfare-of-all, but this modern structure does not map cleanly to one verse without forced certainty. The dilemma turns on missing context, so this stays provisional.

- **Improvement direction**: Teach the lens in human language; remove any engine/QA phrasing; keep the honesty of 'not a direct quote' without product jargon (no new verse metadata).

#### if-you-continue — If You Continue

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: Short-term/long-term exists, but the short-term line is often the densest—exactly the opposite of a simple 'near horizon' read.

- **Excerpt (visible primary)**: Short-term: You buy days of relief by polishing your inner narration and dodging the one detail you do not want said aloud. (Making rushed decisions while withholding information often masks… gets louder when nothing is named.) Long-term: What starts as a one-time smoothing becomes the default tool whenever stakes rise.

- **Improvement direction**: Force short-term to be a concrete 7–30 day consequence; long-term a stable pattern/identity; align metaphors to the setting (work vs. money vs. care vs. family).

#### counterfactuals — Counterfactuals

- **readability**: verbose
- **context_specificity**: generic
- **simple_explanation_quality**: n/a
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The same likely-decision/why text shows up in multiple dilemmas, which overwhelms the otherwise careful primary framing.

- **Excerpt (visible primary)**: Adharmic path: Move now with partial transparency; tidy the record later if pressed. Dharmic path: One bounded, reviewable move before anything irreversible.

- **Improvement direction**: Rewrite likely paths per dilemma class: keep the structure, but change stakes, objects, and failure modes so it cannot be mistaken for a generic kit.

- **Flags**:
  - **repeated_path_templates**: Primary path lines and the 'why' lines match repeated 31D placeholder histogram patterns across cases.

#### higher-path — Higher Path

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: not_contextual
- **shareability**: decent
- **safety_tone**: n/a

- **Human judgment**: The step can be good, but 'Explain simply' often duplicates the action line, and some placeholders/ellipses read unfinished in capture.

- **Excerpt (visible primary)**: Before you act, write Making rushed decisions while withholding information often masks… as a single observable sentence; strip blame; choose the channel where repair is still possible—not the channel where you win.

- **Improvement direction**: Remove ellipsis placeholders; put a true 'simple' line under the action, not a duplicate.

#### ethical-dimensions — Ethical Dimensions

- **readability**: verbose
- **context_specificity**: acceptable
- **simple_explanation_quality**: useful
- **shareability**: n/a
- **safety_tone**: n/a

- **Human judgment**: Simple meanings are doing real work, but the full grid can still feel like scoring without a single, plain 'what next' sentence—especially if duty/violation language lands harshly in acute distress.

- **Excerpt (visible primary)**: Context-dependent (-10)

- **Improvement direction**: Add a single, plain 'so what' action gloss for the set (or per pair of dimensions) without adding schema fields in engine output. For crisis inputs, keep duty language gentle and support-forward.

#### share — Share Layer

- **readability**: clear
- **context_specificity**: generic
- **simple_explanation_quality**: n/a
- **shareability**: screenshot_ready
- **safety_tone**: n/a

- **Human judgment**: Aphorism mode can be polished, but it is usually not a strong, scene-specific share hook.

- **Excerpt (visible primary)**: Most costly moves are not malice—they are hurry with good adjectives.

- **Improvement direction**: Build share copy from 2 on-scene anchors + 1 question; suppress or replace share in crisis/self-harm adjacency.

## Recommended implementation order (copy/product)

1. Crisis adjacency: ensure downstream cards cannot present mismatched templates (e.g., workplace/‘optics’ counterfactuals) or generic share aphorisms below the safety card.
2. User-facing reframe of closest teaching: teach the lens, remove any engine/QA phrasing, keep honesty about no direct quote (no new verse metadata).
3. Counterfactual rewrite pass: new nouns, stakes, and failure modes per dilemma class, keeping structure only.
4. De-duplicate 'Explain simply' from primary blurb, especially in verse + higher path cards.
5. If-you-continue rewrite: 7–30 day short-term, 6–12 month long-term, setting-aligned metaphors.
6. Share rewrite: 2 on-scene anchors + 1 question; suppress in crisis/self-harm adjacency or replace with supportive routing text.
7. Ethical dimensions: add a one-glance 'so what' action gloss at case level, without new engine schema changes (presentation copy only).

## Checkpoint summary

- **Artifacts created**: `artifacts/browser_smoke_step31E_prose_audit.json` and `artifacts/browser_smoke_step31E_prose_audit.md`.
- **Worst surfaces (thematic)**: counterfactual templates; `closest_teaching` meta/unsupported feel; if-you-continue metaphor load; share aphorism mode (especially in crisis adjacency).
- **Top repeated placeholders (from 31D)**: see the histogram list above (engine fallback line, counterfactual lines, a few if-you-continue / share lines).
- **Highest-priority product issues**: see **Top 5** above; lead with crisis-template mismatch, then de-template counterfactuals, then reframe `closest_teaching` user copy.
- **Next implementation move**: first item in **Recommended implementation order** (safety + template alignment), then counterfactuals, then closest-teaching, then de-dupe, then if-you-continue, then share.
