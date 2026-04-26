# Reference Benchmark Comparison

- Fixture: `/home/gaurav/Documents/BDGE/tests/fixtures/benchmarks/retrieval_eval/retrieval_eval_W001-W050.json`
- Total cases: 50
- Reference verse coverage: 58.0%
- Actual verse coverage: 50.0%
- Needs human review: 3

## Summary
- `same_reference_verse_count`: 24
- `same_reference_fallback_count`: 21
- `upgraded_fallback_to_verse_count`: 0
- `downgraded_verse_to_fallback_count`: 0
- `accepted_reference_disagreement_count`: 2
- `needs_review_extractor_count`: 0
- `needs_review_metadata_or_scoring_count`: 3
- `different_verse_from_reference_count`: 0
- `unexpected_error_count`: 0
- `raw_downgraded_verse_to_fallback_count`: 4

## Needs Human Review
### `W028` needs_review_metadata_or_scoring
- Reference answer: `6.32`
- Actual answer: `fallback`
- Top candidate: 3.37 score=4 themes=['desire'] applies=[] blockers=[]
- Review reason: Reference verse 6.32 is not active in the curated retrieval catalog.

### `W029` needs_review_metadata_or_scoring
- Reference answer: `4.11`
- Actual answer: `fallback`
- Top candidate: 3.37 score=1 themes=[] applies=[] blockers=[]
- Review reason: Reference verse 4.11 is not active in the curated retrieval catalog.

### `W033` needs_review_metadata_or_scoring
- Reference answer: `16.14`
- Actual answer: `16.21`
- Top candidate: 16.21 score=12 themes=['anger', 'desire', 'greed'] applies=['anger-spike'] blockers=[]
- Review reason: Reference verse 16.14 is not active in the curated retrieval catalog.

## All Cases By Risk
- `W028` needs_review_metadata_or_scoring: reference `6.32`, actual `fallback`
- `W029` needs_review_metadata_or_scoring: reference `4.11`, actual `fallback`
- `W033` needs_review_metadata_or_scoring: reference `16.14`, actual `16.21`
- `W024` accepted_reference_disagreement: reference `2.31`, actual `fallback`
- `W050` accepted_reference_disagreement: reference `2.7`, actual `fallback`
- `W007` same_reference_fallback: reference `fallback`, actual `fallback`
- `W010` same_reference_fallback: reference `fallback`, actual `fallback`
- `W011` same_reference_fallback: reference `fallback`, actual `fallback`
- `W015` same_reference_fallback: reference `fallback`, actual `fallback`
- `W016` same_reference_fallback: reference `fallback`, actual `fallback`
- `W017` same_reference_fallback: reference `fallback`, actual `fallback`
- `W018` same_reference_fallback: reference `fallback`, actual `fallback`
- `W019` same_reference_fallback: reference `fallback`, actual `fallback`
- `W025` same_reference_fallback: reference `fallback`, actual `fallback`
- `W027` same_reference_fallback: reference `fallback`, actual `fallback`
- `W030` same_reference_fallback: reference `fallback`, actual `fallback`
- `W032` same_reference_fallback: reference `fallback`, actual `fallback`
- `W034` same_reference_fallback: reference `fallback`, actual `fallback`
- `W037` same_reference_fallback: reference `fallback`, actual `fallback`
- `W038` same_reference_fallback: reference `fallback`, actual `fallback`
- `W040` same_reference_fallback: reference `fallback`, actual `fallback`
- `W041` same_reference_fallback: reference `fallback`, actual `fallback`
- `W043` same_reference_fallback: reference `fallback`, actual `fallback`
- `W045` same_reference_fallback: reference `fallback`, actual `fallback`
- `W048` same_reference_fallback: reference `fallback`, actual `fallback`
- `W049` same_reference_fallback: reference `fallback`, actual `fallback`
- `W001` same_reference_verse: reference `17.15`, actual `17.15`
- `W002` same_reference_verse: reference `6.5`, actual `6.5`
- `W003` same_reference_verse: reference `3.35`, actual `3.35`
- `W004` same_reference_verse: reference `17.15`, actual `17.15`
- `W005` same_reference_verse: reference `18.47`, actual `18.47`
- `W006` same_reference_verse: reference `16.21`, actual `16.21`
- `W008` same_reference_verse: reference `5.18`, actual `5.18`
- `W009` same_reference_verse: reference `16.1-3`, actual `16.1-3`
- `W012` same_reference_verse: reference `2.47`, actual `2.47`
- `W013` same_reference_verse: reference `3.37`, actual `3.37`
- `W014` same_reference_verse: reference `17.20`, actual `17.20`
- `W020` same_reference_verse: reference `2.27`, actual `2.27`
- `W021` same_reference_verse: reference `3.20`, actual `3.20`
- `W022` same_reference_verse: reference `17.20`, actual `17.20`
- `W023` same_reference_verse: reference `2.47`, actual `2.47`
- `W026` same_reference_verse: reference `18.47`, actual `18.47`
- `W031` same_reference_verse: reference `6.16`, actual `6.16`
- `W035` same_reference_verse: reference `3.37`, actual `3.37`
- `W036` same_reference_verse: reference `2.70`, actual `2.70`
- `W039` same_reference_verse: reference `6.5`, actual `6.5`
- `W042` same_reference_verse: reference `18.47`, actual `18.47`
- `W044` same_reference_verse: reference `16.3`, actual `16.1-3`
- `W046` same_reference_verse: reference `2.47`, actual `2.47`
- `W047` same_reference_verse: reference `17.15`, actual `17.15`
