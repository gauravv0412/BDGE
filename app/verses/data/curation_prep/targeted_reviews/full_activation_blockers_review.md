# Full Activation Blockers Review

- Scope: Step 29B metadata repair for all-active dry-run blockers.
- Policy: preserve full activation direction, do not mutate every status active yet, and do not change retrieval scoring or semantic extraction.
- Decision summary: 30 metadata repairs, 0 quarantines, 0 keep-as-is.

## Decisions
### `18.26` - `REPAIR_METADATA`
- Problem cases: `W012`
- Problem: overtook `2.47` in whistleblowing/civic-duty context through broad action, detachment, outcome-anxiety, and career-crossroads overlap.
- Repair: keep themes `action`, `equanimity`, `detachment`; narrow `applies_when` to `service-without-return`.
- Rationale: `18.26` is about the qualities of a sattvic doer. `2.47` remains the sharper match for whistleblowing where outcome fear and inaction are central.

### `2.63` - `REPAIR_METADATA`
- Problem cases: `W018`
- Problem: attached to cosmetic surgery/body insecurity with only generic discernment plus self-mastery and no applies_when hit.
- Repair: narrow themes to `anger`, `desire`; narrow `applies_when` to `anger-spike`, `public-humiliation-impulse`.
- Rationale: `2.63` is the anger-delusion collapse after attachment, not a generic self-image discernment verse.

### `2.58` - `REPAIR_METADATA`
- Problem cases: `W031`
- Problem: beat specific eating-moderation verse `6.16` through broad restraint/self-mastery/private-conduct overlap.
- Repair: narrow themes to `restraint`; narrow `applies_when` to `temptation`.
- Rationale: `2.58` should be sensory withdrawal under temptation. `6.16` should own overdoing/underdoing and food moderation.

### `16.2` - `REPAIR_METADATA`
- Problem cases: `W019`, `W044`
- Problem: overtook `16.1-3` in forgiveness/compassion and forced a verse for workplace resource misuse.
- Repair: remove broad `self-mastery`, `private-conduct-test`, and `anger-spike`; keep themes `nonharm`, `truth`, `compassion` with `ethical-speech`.
- Rationale: `16.2` is a compact virtue list and should not become a broad fallback replacement.

## Follow-On Repairs
After the initial four repairs, the all-active dry-run exposed 26 additional broad draft entries that were taking the same weak replacement slots. Step 29D is traceability-only: it documents the already-applied metadata narrowing and does not change retrieval behavior.

For all follow-on entries, `metadata_before` is marked as `not captured during original run` in the JSON artifact. The current `metadata_after` is captured from `verses_seed.json`, including themes, applies_when, blockers, priority, and active status. Each row also includes narrowed fields, risk prevented, behavior status, and clean-audit evidence.

### Follow-On Groups
- Whistleblowing shape-lock protection: `4.22` was narrowed so broad outcome/career applies do not compete with `2.47`.
- Body-image weak-match protection: `4.42`, `2.50`, `7.27`, `17.3`, `18.37`, `18.38`, `2.41`, `3.27`, `3.33`, `3.40`, `4.36`, `7.11`, `14.12`, `14.13`, `15.5`, `17.18`, `18.59` were narrowed to avoid generic `discernment` + `self-mastery` matches with no applies_when hit.
- Eating-moderation specificity: `6.35`, `6.6`, `3.6`, `6.17` were narrowed so `6.16` remains the specific food moderation match.
- Forgiveness/compassion specificity: `12.13`, `13.29`, `17.16` were narrowed so `16.1-3` remains the approved forgiveness/compassion range.
- Fallback overtrigger protection: `13.8` was narrowed to prevent broad private-conduct/self-mastery overlap from forcing fallback cases.

All follow-on repairs have `behavior_status: verified_clean_after_step_29c` in the JSON artifact. Clean evidence: `0` shape regressions, `0` blocker failures, `0` forced-match warnings, `0` overtrigger warnings, and `0` changed winners.

## Activation-Time Repairs
Full activation exposed a few tests/audits that only become meaningful once formerly draft entries are active. These were repaired by metadata narrowing only:

- `16.2`, `13.8`: added `deception-intent` blocking for virtue-list speech/truth matches.
- `13.8`: removed broad `nonharm` overlap to avoid addiction-enablement overtrigger.
- `18.25`: removed broad `nonharm` overlap to avoid weak live OOD overtrigger on addiction-enablement.
- `11.55`: removed broad `duty` overlap to avoid weak live OOD overtrigger on caregiver burnout.

## Step 29D Confirmation
Step 29D changed only this review artifact and its Markdown companion. It did not change retrieval scoring, semantic scoring, context extraction, schema, transport, or verse metadata. All 109 curated entries remain active, and the full activation dry-run remains clean.
