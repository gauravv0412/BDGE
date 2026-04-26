# Step 30A Browser/Live Product Smoke

## Scope

Observation-first product smoke with the full curated retrieval catalog active.

- Active curated verses: 109 / 109
- Draft curated verses: 0
- Local URL: `http://localhost:8000/`
- Browser harness: Playwright Chromium against live frontend shell and live `/api/v1/analyze`
- Desktop viewport: 1365 x 900
- Mobile viewport: 390 x 844

No code-path changes were made to retrieval scoring, verse metadata, semantic scoring, extractor logic, Django transport contract, architecture, or output schema.

## What Became Real

- The read-only browser shell submitted real product requests to `/api/v1/analyze`.
- All 12 prompts returned HTTP 200 with `meta` + `output` success envelopes.
- Both guidance branches rendered: 4 `verse_match`, 8 `closest_teaching`.
- `share_layer`, `counterfactuals`, and `higher_path` rendered in every case.
- Desktop and mobile width checks had no horizontal overflow and no empty key nodes.

## What Is Still Stubbed

- The frontend remains a read-only shell, not a full consumer app with accounts, history, persistence, or real sharing.
- The share card is rendered as product copy only; there is no backend share/export flow.
- Crisis/self-harm adjacent handling is currently trust copy plus model output, not a dedicated crisis workflow.

## What Broke

Nothing broke in this smoke pass.

## What Was Fixed

Nothing was fixed. This pass was observation-only.

## What Was Added To Backlog

- Add a repeatable browser/live smoke script if Step 30A should become a release gate.
- Consider explicit crisis-response UX beyond the global disclaimer/input safety copy.
- Consider product-level latency budget tracking for live semantic calls.
- Persist screenshots/traces from future live browser smoke runs.

## Browser Smoke Summary Table

| Case | API | Classification | Score | Confidence | Rendered | Verse | Share | Counterfactuals | Higher Path | Console | Network | Layout | Severity |
|---|---:|---|---:|---:|---|---|---|---|---|---|---|---|---|
| wallet found with cash | 200 | Adharmic | -88 | 0.85 | verse_match | 6.5 | yes | yes | yes | none | none | none | pass |
| manager takes credit / public correction | 200 | Mixed | 15 | 0.85 | closest_teaching | - | yes | yes | yes | none | none | none | pass |
| legal alcohol shop | 200 | Mixed | -28 | 0.85 | verse_match | 18.47 | yes | yes | yes | none | none | none | pass |
| friend's partner / desire | 200 | Adharmic | -80 | 0.85 | closest_teaching | - | yes | yes | yes | none | none | none | pass |
| aging parent refuses hospitalization | 200 | Dharmic | 40 | 0.85 | closest_teaching | - | yes | yes | yes | none | none | none | pass |
| cosmetic surgery | 200 | Adharmic | -48 | 0.85 | closest_teaching | - | yes | yes | yes | none | none | none | pass |
| abusive parent / no contact | 200 | Context-dependent | 42 | 0.85 | closest_teaching | - | yes | yes | yes | none | none | none | pass |
| caste-disapproved marriage | 200 | Mixed | 32 | 0.85 | verse_match | 5.18 | yes | yes | yes | none | none | none | pass |
| anonymous scathing restaurant review | 200 | Adharmic | -48 | 0.85 | closest_teaching | - | yes | yes | yes | none | none | none | pass |
| doctor hiding terminal diagnosis | 200 | Mixed | -35 | 0.85 | verse_match | 16.1-3 | yes | yes | yes | none | none | none | pass |
| crisis/self-harm adjacent input | 200 | Adharmic | -42 | 0.85 | closest_teaching | - | yes | yes | yes | none | none | none | pass |
| low-information vague input | 200 | Context-dependent | -10 | 0.85 | closest_teaching | - | yes | yes | yes | none | none | none | pass |

## Blocking Issues Before First Live Rollout

- No browser/API/render blocker was observed in this smoke pass.
- Confirm production safety posture for crisis/self-harm adjacent inputs before public rollout.

## Same-Pass Small Fixes Recommended

None applied in this observation-only pass.

## Backlog Polish

- Persist screenshots/traces from future live browser smoke runs.
- Add visible response-time instrumentation to smoke artifacts.
- Add a manual copy/readability note field for each case when doing human QA.

## Next Irreversible Upgrade

Promote this from an ad hoc live smoke artifact to a guarded release checklist gate after safety and latency expectations are agreed.

## Test Commands

- `make test-fast`: passed, 331 passed, 8 deselected in 11.59s.
- `make smoke`: passed, API smoke target exited 0 in 0.53s.
- `make test-browser`: passed, 8 passed, 331 deselected in 2.55s.
