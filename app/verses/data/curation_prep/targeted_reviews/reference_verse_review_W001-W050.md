# Targeted Reference Verse Review W001-W050

- Total cases: 7
- Fixture precision cases: W044
- Curated addition candidates: W028
- Current actual may be acceptable: W021, W029, W031, W033, W036

## Cases
### `W021`
- Reference: `3.20`
- Current actual: `3.20`
- Current category: `same_reference_verse`
- Active in seed: `True`
- Equivalent active range: `None`
- Diagnosis: `current_actual_acceptable`
- Recommended action: `keep_current_actual`
- Top candidate: 3.20 score=11 themes=['action', 'duty', 'welfare-of-all'] applies=['duty-conflict']
- Rationale: Approved reference 3.20 is now active and current retrieval matches it.

### `W028`
- Reference: `6.32`
- Current actual: `fallback`
- Current category: `needs_review_metadata_or_scoring`
- Active in seed: `False`
- Equivalent active range: `None`
- Diagnosis: `inactive_reference_verse_candidate`
- Recommended action: `consider_curated_addition`
- Top candidate: 3.37 score=4 themes=['desire'] applies=[]
- Rationale: Reference 6.32 remains inactive and is marked add-later for a future curation batch.

### `W029`
- Reference: `4.11`
- Current actual: `fallback`
- Current category: `needs_review_metadata_or_scoring`
- Active in seed: `False`
- Equivalent active range: `None`
- Diagnosis: `current_actual_acceptable`
- Recommended action: `keep_current_actual`
- Top candidate: 3.37 score=1 themes=[] applies=[]
- Rationale: Reference 4.11 remains inactive by review decision; keep the current fallback.

### `W031`
- Reference: `6.16`
- Current actual: `6.16`
- Current category: `same_reference_verse`
- Active in seed: `True`
- Equivalent active range: `None`
- Diagnosis: `current_actual_acceptable`
- Recommended action: `keep_current_actual`
- Top candidate: 6.16 score=10 themes=['restraint', 'self-mastery'] applies=['private-conduct-test', 'self-sabotage']
- Rationale: Approved reference 6.16 is now active and current retrieval matches it.

### `W033`
- Reference: `16.14`
- Current actual: `16.21`
- Current category: `needs_review_metadata_or_scoring`
- Active in seed: `False`
- Equivalent active range: `None`
- Diagnosis: `current_actual_acceptable`
- Recommended action: `keep_current_actual`
- Top candidate: 16.21 score=12 themes=['anger', 'desire', 'greed'] applies=['anger-spike']
- Rationale: Reference 16.14 remains inactive; current 16.21 was approved as the better active match.

### `W036`
- Reference: `2.70`
- Current actual: `2.70`
- Current category: `same_reference_verse`
- Active in seed: `True`
- Equivalent active range: `None`
- Diagnosis: `current_actual_acceptable`
- Recommended action: `keep_current_actual`
- Top candidate: 2.70 score=11 themes=['detachment', 'equanimity', 'self-mastery'] applies=['private-conduct-test']
- Rationale: Approved reference 2.70 is now active and current retrieval matches it.

### `W044`
- Reference: `16.3`
- Current actual: `16.1-3`
- Current category: `same_reference_verse`
- Active in seed: `False`
- Equivalent active range: `16.1-3`
- Diagnosis: `fixture_precision`
- Recommended action: `update_allowed_verse_refs`
- Top candidate: 16.1-3 score=7 themes=['compassion', 'nonharm'] applies=[]
- Rationale: Reference 16.3 is contained in active range 16.1-3; update eval allowance before metadata work.
