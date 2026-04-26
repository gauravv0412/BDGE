# Live Retrieval Audit

- Source: `tests/fixtures/live_retrieval_ood_W021-W050.json`
- Input style: `live_sparse_dilemma_only`
- Semantic mode: `stubbed_deterministic`
- Total cases: 30
- Live verse attach rate: 30.0%
- Live fallback rate: 70.0%
- Live vs rich diff count: 0

## Expected/Actual Live Mismatches
None.

## Rich Pass, Live Fail
None.

## Too Sparse Context
None.

## Fallback Due To Missing Live Signals
None.

## Live Verse Where Rich Expected Fallback
None.

## Expected Shape Mismatches
None.

## Unexpected Verse Cases
None.

## Unexpected Fallback Cases
None.

## Disallowed Verse Cases
None.

## Missing Expected Signal Cases
- dilemma_id=`W024`, missing_expected_signals=`{'themes': ['self-mastery'], 'applies': ['temptation'], 'blockers': []}`
- dilemma_id=`W026`, missing_expected_signals=`{'themes': ['duty', 'discernment'], 'applies': [], 'blockers': []}`
- dilemma_id=`W035`, missing_expected_signals=`{'themes': ['speech'], 'applies': [], 'blockers': []}`
- dilemma_id=`W038`, missing_expected_signals=`{'themes': ['equality', 'compassion'], 'applies': [], 'blockers': []}`
- dilemma_id=`W043`, missing_expected_signals=`{'themes': ['restraint'], 'applies': ['anger-spike'], 'blockers': []}`
- dilemma_id=`W044`, missing_expected_signals=`{'themes': ['desire'], 'applies': ['temptation'], 'blockers': []}`
- dilemma_id=`W046`, missing_expected_signals=`{'themes': ['duty', 'discernment'], 'applies': [], 'blockers': []}`

## Possible Forced Match Cases
None.

## Possible Overtrigger Cases
None.
