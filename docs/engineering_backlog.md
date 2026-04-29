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


## Batch curation workflow

- Add a semantic diff viewer for batch import (scripture unchanged + metadata delta summary).
- Add per-batch QA scorecard (tag entropy, priority distribution, blocker coverage).
- Consider fixture-driven micro-batches for faster unit tests than full canonical loads.

- Add optional `--print-diff` mode to `apply_curation_promotion` for concise metadata deltas before write.

## Release / Deployment

- Add production logging / log shipping notes when a real deployment exists.
- Optional: CPU-only `torch` wheel in `requirements-ci.txt` if semantic code starts importing torch in CI.
- Optional: `requirements-dev.txt` symlink or merge strategy to avoid drift between `requirements-ci.txt` and `requirements.txt` pins.
- Expand production operations: log shipping, alerting, Sentry (policy: no dilemma text / provider payloads in telemetry). `app.deploy.site_settings` shipped in Step 37A; see `docs/production_settings.md`.

## Billing / payments / quota (post–Step 38A)

Explicit product/engineering work before real monetization:

- **Real checkout integration** (hosted checkout or embedded flow) wired to plan catalog and account state.
- **Payment provider decision**: Razorpay vs Stripe (and jurisdiction, reconciliation, ops).
- **Webhook verification** (signature, replay protection, idempotent event handling).
- **Signed / server-trusted plan changes** (no client-trusted plan upgrades; admin or payment webhooks only).
- **Payment idempotency** (duplicate charge protection, safe retries).
- **Invoices / receipts** (tax fields, email delivery, retention policy).
- **Cancellation / refund policy** (product copy + operational rules + provider alignment).
- **Quota race / TOCTOU fix before paid plans** (atomic check-and-consume or equivalent so two parallel requests cannot exceed quota at the boundary).
- **Stale / unknown `plan_key` safe fallback** before self-serve plan changes (if `BillingProfile.plan_key` no longer exists in config, avoid crashing; degrade gracefully with support path).

### Claude Code review notes (non-blocking, Step 38A)

- Quota **TOCTOU race at the monthly limit boundary** — same as above; document and fix before relying on paid limits.
- **`get_plan()` KeyError** if a stored `BillingProfile.plan_key` no longer exists in the loaded plan catalog.
- **`_env_int` silently defaulting** on invalid env strings — consider logging a warning once observability is in place.
- **`WISDOMIZE_PLANS_CONFIG_PATH` file override** — expand automated test coverage later (inline JSON is covered more heavily).
- **Usage period rollover** — add tests for month-boundary behavior when presentation usage buckets advance.
- **Layering**: `get_runtime_config()` imports presentation LLM config — acceptable for now; revisit if config modules grow tangled.
