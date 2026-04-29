# Production settings (Step 37A)

This document complements `docs/environment_setup.md` with deployment-focused configuration for Wisdomize/BGE when using `DJANGO_SETTINGS_MODULE=app.deploy.site_settings`.

## Quick commands

| Command | Purpose |
|--------|---------|
| `PYTHONPATH=. .venv/bin/python -m app.scripts.smoke_deploy_surface` | No HTTP bind: URL patterns, auth middleware, DB settings parse, static basics (no LLM). |
| `PYTHONPATH=. .venv/bin/python -m app.scripts.smoke_analyze_api` | Verifies `/api/v1/analyze` in-process contract (never fails on absent prod secrets). |
| `PYTHONPATH=. .venv/bin/python -m app.scripts.check_deploy_readiness` | Local/dev readiness (warnings-only unless `--assume-production`). |
| Same with `--assume-production` | Strict checks for CI/production simulation. |

## Required environment variables (production-facing)

Always set **`DJANGO_DEBUG=false`** and a strong **`DJANGO_SECRET_KEY`** before external traffic.

| Variable | Typical production |
|----------|---------------------|
| `DJANGO_SECRET_KEY` | Cryptographically random, 50+ characters; never reuse dev keys. |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated domains (no lone `*`). Example: `wisdomize.example.com,www.wisdomize.example.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://`-prefixed origins, comma-separated (`https://wisdomize.example.com`). |
| `DJANGO_SECURE_SSL_REDIRECT` | `true` when TLS terminates behind the Django app correctly. |
| `DJANGO_SESSION_COOKIE_SECURE` | `true` on HTTPS deployments. |
| `DJANGO_CSRF_COOKIE_SECURE` | `true` on HTTPS deployments. |
| `DJANGO_SECURE_HSTS_SECONDS` | Start with `2592000` (30 days) once TLS is validated; escalate later. |
| `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS` | `true` once DNS layout is settled. |
| `DJANGO_SECURE_HSTS_PRELOAD` | `true` only when you intend HSTS preload. |
| `DJANGO_STATIC_ROOT` | Absolute filesystem path passed to `collectstatic` (often under `/var`). |

### Database URLs (production)

When **`DATABASE_URL`** is set (parsed via **`dj-database-url`**, see `requirements.txt`), Django **`DATABASES['default']`** is built from that URL. Omit **`DATABASE_URL`** for local SQLite (default file under **`{repo}/var/wisdomize.sqlite3`**, unless **`DJANGO_SQLITE_PATH`** overrides).

| Variable | Notes |
|---------|-------|
| `DATABASE_URL` | e.g. `postgresql://user:password@host:5432/dbname` — passwords must never appear in logs; readiness/smoke tooling masks URLs. Install **`psycopg`** **or** **`psycopg2`** alongside Django in production images (not pinned in repo `requirements.txt` to avoid brittle local installs). |
| `DJANGO_SQLITE_PATH` | Optional override for SQLite **when `DATABASE_URL` is absent**. |
| `DJANGO_ALLOW_SQLITE_IN_PRODUCTION` | `true` acknowledges intentional SQLite-like deployments **without** **`DATABASE_URL`** (readiness may still warn). |
| `DJANGO_DATABASE_CONN_MAX_AGE` | Optional; default `600` when using **`DATABASE_URL`**. |

Deploy readiness with **`--assume-production`** blocks **`DEBUG=false`** while still using implicit repo-local SQLite **unless** **`DATABASE_URL`** is set **or** **`DJANGO_ALLOW_SQLITE_IN_PRODUCTION=true`**.

### Secrets policy

- **Never commit** `.env` or credential files — only **`.env.example`** placeholders ship in git.
- **Always** inject secrets via environment variables or your platform secrets manager (`/run/secrets/…`, KMS, Vault, etc.).
- **Do not log** `DJANGO_EMAIL_HOST_PASSWORD`, OAuth client secrets (`DJANGO_GOOGLE_OAUTH_CLIENT_SECRET`), `PRESENTATION_LLM_API_KEY`, or raw `DATABASE_URL` strings in application logs — operational tooling masks database URLs where possible.
- **`DJANGO_SECRET_KEY` rotation** invalidates sessions, password-reset tokens, and email verification links that rely on Django’s signing — plan rotation alongside user communication and dual-key strategies if needed.

### Email verification / SMTP placeholders

Configure real SMTP before relying on email verification flows:

| Variable | Purpose |
|---------|---------|
| `DJANGO_EMAIL_BACKEND` | e.g. `django.core.mail.backends.smtp.EmailBackend` |
| `DJANGO_EMAIL_HOST`, `DJANGO_EMAIL_PORT` | SMTP server |
| `DJANGO_EMAIL_USE_TLS` | Usually `true` |
| `DJANGO_EMAIL_HOST_USER`, `DJANGO_EMAIL_HOST_PASSWORD` | Credentials (`DJANGO_*` preferred over Django defaults) |
| `DJANGO_DEFAULT_FROM_EMAIL` | Envelope/from address |

Strict gate (optional): set **`DJANGO_EMAIL_VERIFICATION_REQUIRES_SMTP=true`** once SMTP is wired; the deploy readiness checker treats missing SMTP as **blocking**.

### Google OAuth (optional)

Google sign-in placeholders:

| Variable | Notes |
|---------|-------|
| `DJANGO_GOOGLE_OAUTH_CLIENT_ID` or `GOOGLE_OAUTH_CLIENT_ID` | Public client ID |
| `DJANGO_GOOGLE_OAUTH_CLIENT_SECRET` or `GOOGLE_OAUTH_CLIENT_SECRET` | Client secret |

Absence yields a readiness **warning**, not an automatic failure unless you opt in elsewhere.

### Presentation narrator LLM (existing project behavior)

Mirrors presentation config env reads:

| Variable | Notes |
|---------|-------|
| `PRESENTATION_LLM_ENABLED` | `false` disables outbound LLM for narration overlays. |
| `PRESENTATION_LLM_PROVIDER` | `none` keeps deterministic presentation only; other providers expect API connectivity. |
| `PRESENTATION_LLM_MODEL`, `PRESENTATION_LLM_TIMEOUT_SECONDS`, etc. | As documented elsewhere. |

## Security headers

Site settings enable:

- `SecurityMiddleware`
- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `X_FRAME_OPTIONS = DENY`
- `SECURE_CROSS_ORIGIN_OPENER_POLICY = same-origin`
- `SECURE_REFERRER_POLICY = same-origin`
- Conditional HSTS/session/CSRF flags via env vars above.

## Static assets

WhiteNoise is installed (`requirements.txt`). With `MIDDLEWARE` using `WhiteNoiseMiddleware`, deploy should:

```bash
export PYTHONPATH=.
export DJANGO_SETTINGS_MODULE=app.deploy.site_settings
export DJANGO_STATIC_ROOT=/srv/wisdomize/static_collected   # optional override
mkdir -p "$DJANGO_STATIC_ROOT"
python manage.py migrate
python manage.py collectstatic --noinput
```

**`collectstatic`** must target the configured **`STATIC_ROOT`**. See **`docs/deployment_ops.md`** for full command reference (Gunicorn, smoke scripts, local vs production settings).

## Logging policy

Operational logging must **not** include raw dilemmas, full engine JSON provider prompts/responses, passwords, OAuth client secrets, or verification tokens.

- Transport access logs intentionally record path/status/latency only (see `app/transport/django_api.py`).
- `django.request` is capped at ERROR in site settings console logging to suppress noisy stack traces leaking bodies.
- **`TODO / backlog**: integrate Sentry or similar for error aggregation without widening payload capture.**

## HTTP health probe

Expose `GET /healthz/` publicly (no authentication). Intended response JSON:

```json
{"ok": true, "service": "wisdomize"}
```

Load balancers may poll this endpoint; it avoids DB, caches, engines, or LLMs.

## Local developer defaults

Development and CI continue using `tests/django_test_settings` with permissive defaults. Production variables are optional until you simulate production checks.

## See also

- `docs/runtime_config.md` — plan limits, verse threshold, feedback/history knobs, env overrides
- `docs/deployment_ops.md` — install, `manage.py`, smoke/readiness, Gunicorn, health URL
- `docs/rate_limiting_plan.md`
- `docs/environment_setup.md`
- `CLAUDE.md` / `engineering_backlog.md` for unresolved observability backlog items.
