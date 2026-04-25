# Release / deployment checklist (lightweight)

Use this before tagging a release or handing off a build. This repo does **not** ship Docker, cloud IaC, or production secrets in-tree.

## 1. Install dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

For a **CPU-only** sanity pass (e.g. matching CI):

```bash
pip install -r requirements-ci.txt
```

## 2. Fast tests (default local / CI)

```bash
make test-fast
```

Excludes `@pytest.mark.browser` so Playwright is not required.

## 3. Browser tests (manual / optional gate)

```bash
playwright install chromium
make test-browser
```

## 4. Full test suite

```bash
make test-all
```

## 5. Smoke test (`/api/v1/analyze`)

```bash
make smoke
```

Checks HTTP **200**, **`X-Request-ID`** (echo when sent), and **`meta` / `output`** envelope shape for a valid stub payload.

## 6. Public error contract

```bash
pytest tests/test_public_error_contract.py
```

## 7. Canonical raw corpus

```bash
PYTHONPATH=. python -c "from app.verses.raw_corpus import load_canonical_raw_corpus; load_canonical_raw_corpus()"
```

## 8. Curation prep / promotion (optional gate)

If you ship verse data changes:

```bash
pytest tests/test_curation_prep.py tests/test_curation_promotion.py
```

## 9. Run Django locally (demo)

```bash
export DJANGO_SETTINGS_MODULE=tests.django_test_settings
export PYTHONPATH=.
django-admin runserver 0.0.0.0:8000
```

Use the URL patterns under `app/transport/urls.py` (e.g. shell + `/api/v1/analyze`). This uses **test** settings only — not a hardened production configuration.

## Known non-goals (this step)

- No Docker, Kubernetes, or cloud-specific pipelines in-repo.
- No auth, persistence, payments, or admin UI.
- No engine or retrieval behavior changes as part of checklist execution.

## References

- **`docs/environment_setup.md`** — Python, Playwright, env vars.
- **`docs/first_user_readiness.md`** — trusted-demo expectations and safety positioning.
- **`docs/engineering_backlog.md`** — optional hardening and CI/browser follow-ups.
