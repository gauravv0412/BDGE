# Environment and local runtime (BDGE / Wisdomize)

This document describes **local** development and test assumptions. It does not define cloud production secrets or deployment topology.

## Python

- **Target:** Python **3.11** (matches CI and typical `.venv` layout).
- Other 3.x versions may work but are not validated in CI.

## Dependencies

**Full tree (includes CUDA PyTorch pins for future GPU work):**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**CI / CPU-only fast install** (no `torch` / NVIDIA stack):

```bash
pip install -r requirements-ci.txt
```

## Django settings

- **Transport and API tests** use `DJANGO_SETTINGS_MODULE=tests.django_test_settings` (minimal `ROOT_URLCONF`, `SECRET_KEY`, etc.).
- The smoke script and `pytest` set or assume this module where needed.
- There is **no** separate production settings package in this milestone; run the Django dev server with the same test settings only for local demos unless you add your own settings module.

## Environment variables

- **None are required** for the default stub semantic path and local `pytest` / smoke runs.
- Optional: `ANTHROPIC_API_KEY` (or paths in `config/`) only if you enable live semantic modes in `config/app_config.json` — out of scope for CI.

## Playwright (browser tests)

Browser tests live under `tests/test_frontend_shell_browser.py` and are marked `@pytest.mark.browser`.

```bash
pip install playwright   # included in requirements / requirements-ci
playwright install chromium
```

Run **only** browser tests:

```bash
make test-browser
# or: pytest -m browser
```

Default **fast** feedback excludes them:

```bash
make test-fast
# or: pytest -m "not browser"
```

## Repo test entrypoints

See the root **Makefile** (`make help`) and **`docs/deployment_checklist.md`**.

For **trusted-user demos**, read **`docs/first_user_readiness.md`** (what the product does / does not do, and crisis limitations).

## Smoke check

In-process POST to `/api/v1/analyze` (no running server):

```bash
PYTHONPATH=. python -m app.scripts.smoke_analyze_api
# or: make smoke
```

The smoke script **forces the semantic stub** internally so it stays fast and offline even when `config/app_config.json` sets `use_stub_default` to false (live Anthropic path for normal runs).
