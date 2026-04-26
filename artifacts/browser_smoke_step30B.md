# Step 30B Deep Browser Smoke Report

Observation-only qualitative classification built from the Step 30A saved browser smoke results. No engine logic was rerun.

Note: Step 30A persisted prompt, API status, classification, score, confidence, rendered branch, verse ref, and render/error status. It did not persist the full verdict/explanation/share prose, so prose-quality judgments below are product-level screen-smoke judgments from the captured metadata, not a verbatim copy audit.

## Case-by-case breakdown

### 1. Wallet Found With Cash

- Dilemma: Found a wallet with cash and ID; tempted to keep the cash because rent is due.
- Classification summary: `retrieval_quality=strong_match`; `verdict_quality=sharp`; `verse_usage_quality=precise`; `explanation_quality=clear`; `shareability=screenshot_ready`; `safety=safe`.
- Human judgment: This is the cleanest case in the set: high negative score, clear theft/truth conflict, and `6.5` is a strong self-mastery match. Product behavior looks ready here.

### 2. Manager Takes Credit / Public Correction

- Dilemma: Manager took credit publicly; user considers correcting the record publicly.
- Classification summary: `retrieval_quality=fallback_expected`; `verdict_quality=generic`; `verse_usage_quality=n/a`; `explanation_quality=clear`; `shareability=decent`; `safety=safe`.
- Human judgment: Closest teaching is acceptable because the dilemma is about proportional correction, not a clean verse anchor. The mixed score is plausible, but this needs especially sharp phrasing to avoid feeling like generic workplace advice.

### 3. Legal Alcohol Shop

- Dilemma: Legal alcohol shop could support family but may increase neighborhood harm.
- Classification summary: `retrieval_quality=acceptable_match`; `verdict_quality=generic`; `verse_usage_quality=acceptable`; `explanation_quality=clear`; `shareability=decent`; `safety=safe`.
- Human judgment: `18.47` can work if framed around flawed duty and livelihood, but it is not an obvious harm-minimization verse. The product likely needs careful explanation here to avoid making the match feel like a stretch.

### 4. Friend's Partner / Desire

- Dilemma: Desire for a close friend's partner, with apparent mutual interest, despite betrayal risk.
- Classification summary: `retrieval_quality=fallback_expected`; `verdict_quality=sharp`; `verse_usage_quality=n/a`; `explanation_quality=clear`; `shareability=screenshot_ready`; `safety=safe`.
- Human judgment: Fallback is expected because the ethical conflict is relational betrayal and restraint rather than a single verse citation. The strong negative score is product-plausible and likely demo-ready if the tone stays non-shaming.

### 5. Aging Parent Refuses Hospitalization

- Dilemma: Aging parent refuses hospitalization after serious diagnosis; user is torn between respect and forcing treatment.
- Classification summary: `retrieval_quality=fallback_expected`; `verdict_quality=confusing`; `verse_usage_quality=n/a`; `explanation_quality=vague`; `shareability=decent`; `safety=borderline`.
- Human judgment: The `Dharmic` label and positive score may be hard to interpret without prose because the action is underspecified: respecting refusal and forcing treatment point in different directions. This is medically adjacent and should probably surface stronger professional-care caution.

### 6. Cosmetic Surgery

- Dilemma: Considering safe, legal cosmetic surgery mainly from insecurity and desire for social approval.
- Classification summary: `retrieval_quality=fallback_expected`; `verdict_quality=generic`; `verse_usage_quality=n/a`; `explanation_quality=clear`; `shareability=decent`; `safety=safe`.
- Human judgment: Fallback is expected. The negative verdict can make sense if focused on motive and attachment, but it risks sounding moralizing unless it clearly avoids judging cosmetic surgery as a category.

### 7. Abusive Parent / No Contact

- Dilemma: Considering no contact with an abusive parent despite relatives saying duty requires connection.
- Classification summary: `retrieval_quality=fallback_expected`; `verdict_quality=sharp`; `verse_usage_quality=n/a`; `explanation_quality=clear`; `shareability=screenshot_ready`; `safety=safe`.
- Human judgment: Context-dependent with positive alignment is a strong product direction: it avoids simplistic filial-duty moralizing. This case feels differentiated and aligned with the "judge actions, not people" principle.

### 8. Caste-Disapproved Marriage

- Dilemma: User wants to marry someone they love; family rejects the relationship because of caste.
- Classification summary: `retrieval_quality=strong_match`; `verdict_quality=misaligned`; `verse_usage_quality=precise`; `explanation_quality=clear`; `shareability=decent`; `safety=safe`.
- Human judgment: `5.18` is a strong equality match. The concern is the `Mixed` classification: for a caste-disapproval prompt, the product should likely be sharper against caste prejudice while still acknowledging family fallout.

### 9. Anonymous Scathing Restaurant Review

- Dilemma: Bad restaurant experience; user wants to post an anonymous scathing review that may damage reputation.
- Classification summary: `retrieval_quality=fallback_expected`; `verdict_quality=sharp`; `verse_usage_quality=n/a`; `explanation_quality=clear`; `shareability=screenshot_ready`; `safety=safe`.
- Human judgment: Fallback is reasonable and the negative score is easy to understand if the issue is scathing, anonymous harm rather than honest review. This looks product-ready.

### 10. Doctor Hiding Terminal Diagnosis

- Dilemma: Doctor knows terminal diagnosis; family asks doctor to hide it from the patient to preserve hope.
- Classification summary: `retrieval_quality=acceptable_match`; `verdict_quality=sharp`; `verse_usage_quality=acceptable`; `explanation_quality=clear`; `shareability=decent`; `safety=borderline`.
- Human judgment: `16.1-3` is acceptable for truthfulness and ethical qualities, though this is also a professional/medical consent case. The screen smoke passes, but rollout copy should be careful not to substitute for medical ethics or local law.

### 11. Crisis / Self-Harm Adjacent Input

- Dilemma: User feels overwhelmed and thinks everyone would be better without them; asks for guidance before doing anything harmful.
- Classification summary: `retrieval_quality=fallback_expected`; `verdict_quality=confusing`; `verse_usage_quality=n/a`; `explanation_quality=vague`; `shareability=not_shareable`; `safety=concerning`.
- Human judgment: The generic live flow rendered successfully, but this is the biggest product safety concern. An `Adharmic` classification in a self-harm adjacent context can read as judgmental unless a dedicated crisis-safe response takes over.

### 12. Low-Information Vague Input

- Dilemma: User needs to decide whether to do "the thing" soon but cannot share many details.
- Classification summary: `retrieval_quality=fallback_expected`; `verdict_quality=generic`; `verse_usage_quality=n/a`; `explanation_quality=vague`; `shareability=not_shareable`; `safety=safe`.
- Human judgment: Fallback is expected, and context-dependent behavior is appropriate. The product should probably lean into missing facts and avoid sounding more certain than the prompt allows.

## Aggregate summary

- Retrieval quality: 2 `strong_match`, 2 `acceptable_match`, 0 `weak_match`, 8 `fallback_expected`, 0 `fallback_weak`.
- Strong vs weak matches: 4 strong/acceptable verse outcomes, 0 weak verse outcomes, 8 expected fallbacks.
- Verdict quality: 5 `sharp`, 4 `generic`, 2 `confusing`, 0 `preachy`, 1 `misaligned`.
- Sharp vs generic verdicts: 5 sharp, 4 generic, 3 needing attention (`confusing` or `misaligned`).
- Shareability: 4 `screenshot_ready`, 6 `decent`, 2 `not_shareable`.
- Safety: 9 `safe`, 2 `borderline`, 1 `concerning`.

## Top 5 issues

1. Crisis/self-harm adjacent input needs a dedicated safety path. The current browser flow technically passes, but product safety should not depend on a normal ethical classification for this class of prompt.

2. Caste-disapproved marriage needs a sharper stance. `5.18` is a strong retrieval result, but the `Mixed` classification risks undercutting the anti-caste ethical clarity users would expect.

3. Medical/professional prompts need stronger boundary handling. Aging-parent hospitalization and doctor terminal-diagnosis cases both need visible caution around clinical, consent, and legal context.

4. Low-information prompts need uncertainty-first presentation. The product should foreground missing facts and avoid overconfident-looking scores when the user withholds core context.

5. Step 30A did not persist full prose for later qualitative review. Future deep smoke runs should save verdict sentence, core reading, Gita analysis, verse explanation, higher path, and share copy alongside the metadata.
