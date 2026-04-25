# First-user readiness (trusted demo)

This note is for **early trusted users** and anyone running a local demo. It describes what Wisdomize / BDGE does today, what it does not do, and how to prepare before showing the product.

## What the product can do today

- Accept a moral dilemma (plain text) and return a **structured JSON** response: verdict, dimensions, narrative layers, optional verse match or closest teaching, and share-oriented snippets—bounded by `docs/output_schema.json`.
- Expose the same contract through **Django transport**: `POST /api/v1/analyze`.
- Offer a **read-only web shell** at `/` to submit a dilemma and inspect the response in a readable layout (with global disclaimer and input-area safety copy; see Step 24).

## What it cannot do (today)

- **No** authentication, accounts, saved history, payments, or admin moderation UI.
- **No** dedicated crisis detection, self-harm classifier, or automatic routing to hotlines—the engine does **not** implement that pipeline. Treat any reflective language in outputs as **general ethics framing**, not a safety assessment.
- **No** guaranteed medical, legal, or religious authority: outputs are **heuristic and model-dependent** (stub or configured semantic path), not licensed advice.
- **No** promise of completeness on scripture: curated verses are a **small seed**; the full raw corpus is validated separately for editorial workflows, not for live retrieval breadth in MVP.

## How to run locally

See **`docs/environment_setup.md`** and **`docs/deployment_checklist.md`**.

Minimal path:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # or requirements-ci.txt for CPU-only CI parity
export DJANGO_SETTINGS_MODULE=tests.django_test_settings
export PYTHONPATH=.
django-admin runserver 0.0.0.0:8000
```

Open `/` for the shell; use `POST /api/v1/analyze` for API checks.

## How to test before demoing

```bash
make test-fast
make smoke
```

Optional full gate including browser tests (requires Playwright Chromium):

```bash
playwright install chromium
make test-browser
make test-all
```

## Dilemmas that are reasonable for first testing

- Everyday ethics: workplace tradeoffs, honesty vs. kindness, duty vs. desire, mild conflict of obligations.
- Clearly **non-emergency** framing; user is not describing imminent violence or medical crisis in the text.

## What to avoid or treat carefully

- **Active self-harm, suicide intent, or violence toward others**—the app is not a crisis service; do not demo with real crisis content.
- **Medical or legal decisions** that require a professional—do not position output as a second opinion that replaces clinicians or lawyers.
- **High-stakes emergencies**—direct people to emergency numbers and qualified help, not to the model.

## Known limitations

- Public **error contract** is stable; success content quality depends on semantic mode (stub vs. live) and curated verse coverage.
- Shell is **read-only inspection**; it is not a polished consumer product UI.
- **No** in-product crisis routing (see backlog in `docs/engineering_backlog.md`).

## Current safety-related behavior (accurate)

- **UI (Step 24):** Global footer disclaimer and a short note above the dilemma input discourage treating the tool as sole authority for emergencies, self-harm, legal, or medical situations.
- **Engine / API:** There is **no** automated detection of crisis keywords or escalation to human services. Any future signposting beyond static copy would be explicit product/engine work.

## Checklist before showing a trusted user

1. Dependencies installed; `make test-fast` green.
2. `make smoke` passes (verifies `/api/v1/analyze` envelope in-process).
3. You have set expectations: reflective tool, not therapy, law, religion, or emergency services.
4. You avoid live crisis examples in the session.
5. You know how to capture **Request ID** from errors if something fails (`X-Request-ID` header).
6. Optional: run `pytest tests/test_public_error_contract.py` if you changed transport code.

## See also

- `docs/deployment_checklist.md` — release-style gate.
- `docs/frontend_shell.md` — shell behavior and layout.
- `docs/engine_contract.md` — engine boundary.
