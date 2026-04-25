# Engineering Backlog

This file tracks non-blocking review findings and optional hardening tasks.
Blocking issues should be fixed inside the active milestone. Backlog items should not interrupt milestone progress unless reclassified.

## Classification Rule

### Blocking
Fix before a milestone is complete:
- boundary violation
- failing tests
- public contract drift
- security/safety bug
- production-breaking issue
- data corruption risk

### Same-pass small fix
May fix immediately if directly related and tiny:
- dead function introduced in same step
- duplicated UI field
- missing obvious test for new logic
- misleading label introduced in same step

### Backlog
Valid but should not interrupt progress:
- extra edge tests
- robustness polish
- CI convenience
- optional refactors
- nicer error messages
- docs wording improvements

---

## Safety / trust (post–Step 24)

- Explicit **crisis / self-harm keyword routing** (detection + hotline links or block-and-signpost flow)—not implemented; UI copy only today.
- Stronger **legal / medical disclaimer** surfaces (e.g. modal on first visit, locale-specific copy) if product requires it.
- **Abuse-case evaluation pack** (prompt suites for harmful jailbreaks, crisis feints, medical triage requests).
- **Moderation pre-checks** on dilemma text before engine call (latency + false-positive tradeoffs).
- **Consent or age gate** if distribution context requires it.

## Frontend Shell

- Add browser test for client-side short-input validation.
- Add browser test for network failure catch path.
- Add browser test for non-JSON API response fallback.
- Consider pruning duplicated source-inspection tests once browser tests cover equivalent behavior.
- Add browser test for share spotlight rendering if not already covered.
- Consider dedicated share-card capture mode later, after core MVP stability.

## Browser Tests / CI

- Add optional **second** GitHub Actions job that runs `pytest -m browser` after `playwright install chromium` (cache browser binaries between runs).
- Consider Playwright trace artifacts on browser job failure for debugging.

## Raw Corpus

- Add duplicate `verse_id` rejection test.
- Add non-contiguous chapter sequence rejection test.
- Wrap raw corpus `json.JSONDecodeError` with clearer `ValueError`.

## Curation Prep

- Replace bare `assert` in `app/scripts/export_curation_prep.py` with explicit `RuntimeError`.
- Add `FileNotFoundError` test for `load_curation_prep_artifact`.
- Add placeholder `priority` out-of-range validation test.
- Add default-path write test for `write_curation_prep_artifact(path=None)`.
- Make explicit in code/docs that active curated path guard assumes no nested curated subdirectories.

## Promotion Workflow

- Add optional CLI flag to run `merge_promoted_into_seed_json` against a **non-production** path with pre-flight diff summary.
- Add integration test that loads a tiny prep fixture from `tests/fixtures/` (avoid building 701-row prep where unnecessary).
- Consider `verse_id` duplicate-only conflict message distinct from `verse_ref` for operator clarity.
- Optional: checksum or content hash of `scripture` block in review artifact for audit trails.

## Release / Deployment

- Add production logging / log shipping notes when a real deployment exists.
- Optional: CPU-only `torch` wheel in `requirements-ci.txt` if semantic code starts importing torch in CI.
- Optional: `requirements-dev.txt` symlink or merge strategy to avoid drift between `requirements-ci.txt` and `requirements.txt` pins.
- Document a hardened `DJANGO_SETTINGS_MODULE` for production when that milestone exists (not `tests.django_test_settings`).
