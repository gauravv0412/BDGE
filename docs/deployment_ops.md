# Deployment operations (Step 37B)

Project-specific commands for installing dependencies, running migrations, collecting static files, and validating the Wisdomize surface before traffic. This is **not** a full platform runbook (TLS, load balancers, systemd, etc.—those stay with your infra).

Conventions:

- Repo root: where `manage.py` lives.
- `PYTHONPATH=.` keeps imports stable for packaged layout (same pattern as pytest / smoke scripts).

## Virtualenv and Python dependencies

```bash
python -m venv .venv
. .venv/bin/activate   # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Production Postgres: install **`psycopg`** or **`psycopg2`** in the deployment image (either works with Django); this repo does **not** pin Postgres drivers—see your platform/package manager.

## Environment file

- Copy placeholders from **`.env.example`** (never commit real secrets).
- Load into the process env for your orchestrator/containers (**not** sourced automatically by Django unless something you own loads dotenv).

## Django management commands

Default `manage.py` uses **`tests.django_test_settings`** (matches pytest fixtures). Production deploy/migrate/collect flows should export:

```bash
export PYTHONPATH=.
export DJANGO_SETTINGS_MODULE=app.deploy.site_settings
```

Then:

| Step | Command |
|------|---------|
| System checks | `python manage.py check` |
| Migrations | `python manage.py migrate` |
| Static files | `python manage.py collectstatic --noinput` |

**Local/dev** (SQLite + test settings defaults):

```bash
PYTHONPATH=. python manage.py check
PYTHONPATH=. python manage.py migrate
PYTHONPATH=. python manage.py collectstatic --noinput
```

(no `DJANGO_SETTINGS_MODULE` export → mirrors pytest `tests.django_test_settings`)

## Smoke and readiness scripts

| Script | Purpose |
|--------|---------|
| `PYTHONPATH=. python -m app.scripts.smoke_deploy_surface` | In-process URLs, DB config parsing, auth stack, static basics—no HTTP bind, **no LLM**. |
| `PYTHONPATH=. python -m app.scripts.smoke_analyze_api` | Contract smoke for **`/api/v1/analyze`** (unchanged). |
| `PYTHONPATH=. python -m app.scripts.check_deploy_readiness` | Env-driven readiness (**warnings locally** unless `--assume-production`). |

Readiness **`--assume-production`** simulates **`DEBUG=false`** expectations (including DATABASE_URL posture). Output **masks** passwords in database URLs—never feeds secrets to logs.

Example production-ish env snippet (adapt hosts):

```bash
export DJANGO_DEBUG=false
export DJANGO_SECRET_KEY='(strong random)'
export DJANGO_ALLOWED_HOSTS=example.com,www.example.com
export DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
export DATABASE_URL='postgresql://user:***@your-db-host:5432/wisdemo'
PYTHONPATH=. python -m app.scripts.check_deploy_readiness --assume-production
```

## Gunicorn (WSGI)

Target application object:

```bash
PYTHONPATH=. gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Set `DJANGO_SETTINGS_MODULE`, secrets, and `DATABASE_URL` in the supervisor/container environment (see `docs/production_settings.md`).

## HTTP health probe

Expose **`GET /healthz/`** — returns JSON **`{"ok": true, "service": "wisdomize"}`** (stable for load balancers; no dilemma text or secrets).

See also **`docs/production_settings.md`** for security headers and env semantics.
