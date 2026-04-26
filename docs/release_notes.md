# Release Notes

## V1 Engine Baseline

The current engine state is frozen as the V1 rollback/checkpoint baseline before product-language, prompt, schema, Django frontend, or visible presentation refinements.

- Full curated retrieval catalog active: 109 / 109.
- Draft curated verses: 0.
- Guarded activation complete.
- Step 29A-29D closed.
- Step 30A browser/live smoke passed.
- Step 30B qualitative smoke report completed.
- Fast tests passed: 331 passed, 8 deselected.
- API smoke passed.
- Browser tests passed: 8 passed, 331 deselected.

Known limitations:

- Language can be hard to understand.
- `closest_teaching` lacks explicit verse anchor.
- Counterfactuals are too generic.
- `share_layer` needs context rewrite.
- Crisis/self-harm needs dedicated UX path.
- Frontend is read-only shell.

Versioning note:

- Runtime `engine_version` remains the current value.
- V1 baseline is a git tag/release concept, not an output schema change.
- No engine behavior, retrieval scoring, semantic scorer, context extractor, verse metadata, Django transport, frontend behavior, or tests were changed for this baseline.

Recommended tag after commit:

```bash
git tag -a v1-engine-baseline -m "V1 engine baseline: full curated retrieval catalog active"
git push origin v1-engine-baseline
```
