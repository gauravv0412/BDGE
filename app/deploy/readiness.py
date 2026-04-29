"""Deploy readiness checks driven by environment (no Django required)."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from app.deploy.db_settings import databases_from_environ, try_parse_database_url
from app.deploy.env_helpers import env_bool, env_csv_list, is_placeholder_secret, mask_database_url, secret_fingerprint


class ReadinessSeverity:
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"


@dataclass
class Finding:
    code: str
    message: str
    severity: str

    def line(self) -> str:
        marker = "[OK]" if self.severity == ReadinessSeverity.PASS else (
            "[!!]" if self.severity == ReadinessSeverity.WARN else "[XX]"
        )
        return f"{marker} {self.code}: {self.message}"


@dataclass
class ReadinessReport:
    findings: list[Finding] = field(default_factory=list)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    @property
    def blocking_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == ReadinessSeverity.BLOCK)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == ReadinessSeverity.WARN)

    def print_report(self, *, fh=None) -> None:
        fh = fh or sys.stdout
        fh.write("\nWisdomize deploy readiness\n")
        fh.write("=" * 40 + "\n")
        for finding in self.findings:
            fh.write(finding.line() + "\n")


def collect_readiness(debug_mode: bool, *, enforce_production_checks: bool) -> ReadinessReport:
    report = ReadinessReport()

    raw_debug = os.environ.get("DJANGO_DEBUG")
    if enforce_production_checks:
        if raw_debug is None:
            report.add(
                Finding(
                    "DJANGO_DEBUG",
                    "DJANGO_DEBUG unset (site settings default to DEBUG=True locally). "
                    "Set explicitly to false before going live.",
                    ReadinessSeverity.WARN,
                )
            )
        if debug_mode:
            report.add(
                Finding(
                    "DJANGO_DEBUG",
                    "DEBUG is enabled — set DJANGO_DEBUG=false on production-facing hosts.",
                    ReadinessSeverity.BLOCK,
                )
            )
        elif raw_debug is not None:
            report.add(Finding("DJANGO_DEBUG", "DJANGO_DEBUG explicitly disables Django DEBUG mode.", ReadinessSeverity.PASS))
    else:
        hint = (
            "unset (defaults permissive locally)"
            if raw_debug is None
            else f"explicit DJANGO_DEBUG={debug_mode}"
        )
        report.add(Finding("DJANGO_DEBUG", f"Production checks deferred ({hint})", ReadinessSeverity.PASS))

    sk = (
        os.environ.get("DJANGO_SECRET_KEY").strip()
        if os.environ.get("DJANGO_SECRET_KEY")
        else (os.environ.get("SECRET_KEY", "").strip() or "")
    )
    if enforce_production_checks:
        if not sk:
            report.add(Finding("SECRET_KEY", "Missing (required before production)", ReadinessSeverity.BLOCK))
        elif is_placeholder_secret(sk):
            report.add(
                Finding(
                    "SECRET_KEY",
                    "Value looks like development placeholder — rotate before traffic.",
                    ReadinessSeverity.BLOCK,
                )
            )
        else:
            report.add(
                Finding(
                    "SECRET_KEY",
                    f"Present (fingerprint={secret_fingerprint(sk)})",
                    ReadinessSeverity.PASS,
                )
            )
    else:
        report.add(
            Finding(
                "SECRET_KEY",
                "Production secret checks skipped (debug mode or readiness not enforcing).",
                ReadinessSeverity.PASS,
            )
        )

    hosts = env_csv_list(os.environ.get("DJANGO_ALLOWED_HOSTS"))
    if enforce_production_checks:
        if not hosts:
            report.add(
                Finding("ALLOWED_HOSTS", "DJANGO_ALLOWED_HOSTS is empty (unsafe for production)", ReadinessSeverity.BLOCK)
            )
        elif len(hosts) == 1 and hosts[0] == "*":
            report.add(
                Finding("ALLOWED_HOSTS", "Wildcard-only ALLOWED_HOSTS is insecure for production deployments", ReadinessSeverity.BLOCK)
            )
        elif any(h == "*" for h in hosts):
            report.add(
                Finding(
                    "ALLOWED_HOSTS",
                    "ALLOWED_HOSTS includes '*' alongside other names — remove wildcard in production.",
                    ReadinessSeverity.WARN,
                )
            )
        else:
            report.add(Finding("ALLOWED_HOSTS", f"Configured ({len(hosts)} hostnames)", ReadinessSeverity.PASS))
    else:
        report.add(Finding("ALLOWED_HOSTS", "(strict host checks deferred)", ReadinessSeverity.PASS))

    csrf_origins = env_csv_list(os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS"))
    secure_redirect = env_bool(os.environ.get("DJANGO_SECURE_SSL_REDIRECT"), False)

    if enforce_production_checks and secure_redirect and not csrf_origins:
        report.add(
            Finding(
                "CSRF_TRUSTED_ORIGINS",
                "SSL redirect is enabled but DJANGO_CSRF_TRUSTED_ORIGINS is empty (HTTPS forms may fail)",
                ReadinessSeverity.BLOCK,
            )
        )
    elif enforce_production_checks and not csrf_origins:
        report.add(
            Finding(
                "CSRF_TRUSTED_ORIGINS",
                "No HTTPS origins listed — configure with https://… values when terminating TLS externally",
                ReadinessSeverity.WARN,
            )
        )
    else:
        report.add(Finding("CSRF_TRUSTED_ORIGINS", f"{len(csrf_origins)} origin(s)", ReadinessSeverity.PASS))

    if enforce_production_checks:
        if not env_bool(os.environ.get("DJANGO_SESSION_COOKIE_SECURE"), False):
            report.add(
                Finding(
                    "SESSION_COOKIE_SECURE",
                    "DJANGO_SESSION_COOKIE_SECURE=false (enable for HTTPS deployments)",
                    ReadinessSeverity.WARN,
                )
            )
        else:
            report.add(Finding("SESSION_COOKIE_SECURE", "Enabled", ReadinessSeverity.PASS))

        if not env_bool(os.environ.get("DJANGO_CSRF_COOKIE_SECURE"), False):
            report.add(
                Finding(
                    "CSRF_COOKIE_SECURE",
                    "DJANGO_CSRF_COOKIE_SECURE=false (enable for HTTPS deployments)",
                    ReadinessSeverity.WARN,
                )
            )
        else:
            report.add(Finding("CSRF_COOKIE_SECURE", "Enabled", ReadinessSeverity.PASS))

        if env_int_simple(os.environ.get("DJANGO_SECURE_HSTS_SECONDS"), 0) == 0:
            report.add(
                Finding(
                    "HSTS",
                    "DJANGO_SECURE_HSTS_SECONDS is 0 (consider non-zero HTTPS hardening)",
                    ReadinessSeverity.WARN,
                )
            )

    sr = os.environ.get("DJANGO_STATIC_ROOT", "").strip()
    fallback_static = _repo_root() / "static_collected"
    if enforce_production_checks and not sr:
        report.add(
            Finding(
                "STATIC_ROOT",
                f"DJANGO_STATIC_ROOT unset — configure before collectstatic in production "
                f"(defaults to {fallback_static.as_posix()}).",
                ReadinessSeverity.WARN,
            )
        )
    else:
        report.add(Finding("STATIC_ROOT", sr or f"(defaults to {fallback_static.as_posix()})", ReadinessSeverity.PASS))

    # Email — strict SMTP gate is opt-in via DJANGO_EMAIL_VERIFICATION_REQUIRES_SMTP
    verification_strict = env_bool(os.environ.get("DJANGO_EMAIL_VERIFICATION_REQUIRES_SMTP"), False)
    email_backend_hint = (
        os.environ.get("DJANGO_EMAIL_BACKEND", "").strip().lower()
        if os.environ.get("DJANGO_EMAIL_BACKEND")
        else "(django settings default derived from DEBUG)"
    )
    if verification_strict:
        eh = os.environ.get("DJANGO_EMAIL_HOST", "").strip()
        if not eh:
            report.add(
                Finding(
                    "EMAIL",
                    "DJANGO_EMAIL_VERIFICATION_REQUIRES_SMTP=true but DJANGO_EMAIL_HOST is empty.",
                    ReadinessSeverity.BLOCK,
                )
            )
        else:
            report.add(Finding("EMAIL", "SMTP host present for outbound mail", ReadinessSeverity.PASS))
    elif enforce_production_checks:
        report.add(
            Finding(
                "EMAIL",
                "Set DJANGO_EMAIL_VERIFICATION_REQUIRES_SMTP=true (and SMTP host/user) before requiring "
                "email verification in production. "
                f"Current DJANGO_EMAIL_BACKEND hint: {email_backend_hint}.",
                ReadinessSeverity.WARN,
            )
        )
    else:
        report.add(Finding("EMAIL", "(strict SMTP checks skipped)", ReadinessSeverity.PASS))

    # Google OAuth informational
    gcid = (os.environ.get("DJANGO_GOOGLE_OAUTH_CLIENT_ID") or os.environ.get("GOOGLE_OAUTH_CLIENT_ID") or "").strip()
    if gcid:
        report.add(Finding("GOOGLE_OAUTH", "Google OAuth client id present (masked server-side)", ReadinessSeverity.PASS))
    else:
        report.add(
            Finding(
                "GOOGLE_OAUTH",
                "Missing Google OAuth client id — optional unless Google login is rolled out.",
                ReadinessSeverity.WARN,
            )
        )

    # Presentation LLM
    llm_enabled = env_bool(os.environ.get("PRESENTATION_LLM_ENABLED"), True)
    provider_raw = os.environ.get("PRESENTATION_LLM_PROVIDER") or ""
    provider = provider_raw.strip().lower() if provider_raw else ""
    if llm_enabled and provider and provider != "none":
        key = (os.environ.get("PRESENTATION_LLM_API_KEY") or "").strip()
        if not key:
            report.add(
                Finding(
                    "PRESENTATION_LLM",
                    f"Provider is '{provider}' but PRESENTATION_LLM_API_KEY is missing.",
                    ReadinessSeverity.BLOCK,
                )
            )
        else:
            report.add(
                Finding(
                    "PRESENTATION_LLM",
                    f"Provider '{provider}', API key present (not printed)",
                    ReadinessSeverity.PASS,
                )
            )
    else:
        report.add(
            Finding(
                "PRESENTATION_LLM",
                "LLM narration disabled or provider is 'none'",
                ReadinessSeverity.PASS,
            )
        )

    _collect_ops_repo_and_database(report, repo_root=_repo_root(), enforce_production_checks=enforce_production_checks)

    return report


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _within_repo(candidate: Path, repo_root: Path) -> bool:
    try:
        candidate.resolve().relative_to(repo_root.resolve())
        return True
    except ValueError:
        return False


def _wsgi_probe_cwd(repo_root: Path) -> tuple[bool, str]:
    snippet = """import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.deploy.site_settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "probe-" + "z" * 60)
os.environ.setdefault("DJANGO_DEBUG", "true")
django.setup()
import config.wsgi

assert getattr(config.wsgi, "application", None) is not None
"""
    env = dict(os.environ)
    env.pop("DATABASE_URL", None)
    env.pop("DJANGO_SQLITE_PATH", None)
    env["PYTHONPATH"] = str(repo_root)
    proc = subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode == 0:
        return True, ""
    tail = ((proc.stderr or "") + "\n" + (proc.stdout or "")).strip()[:400]
    return False, tail or "(no output)"


def _collect_ops_repo_and_database(report: ReadinessReport, *, repo_root: Path, enforce_production_checks: bool) -> None:
    manage = repo_root / "manage.py"
    wsgi_path = repo_root / "config" / "wsgi.py"
    asgi_path = repo_root / "config" / "asgi.py"

    if manage.is_file():
        report.add(Finding("MANAGE_PY", "manage.py present at repo root", ReadinessSeverity.PASS))
    else:
        report.add(
            Finding(
                "MANAGE_PY",
                "manage.py missing at repo root (expected django operational entrypoint).",
                ReadinessSeverity.BLOCK if enforce_production_checks else ReadinessSeverity.WARN,
            )
        )

    if wsgi_path.is_file():
        report.add(Finding("WSGI_FILE", "config/wsgi.py present", ReadinessSeverity.PASS))
    else:
        report.add(
            Finding(
                "WSGI_FILE",
                "config/wsgi.py missing.",
                ReadinessSeverity.BLOCK if enforce_production_checks else ReadinessSeverity.WARN,
            )
        )

    if asgi_path.is_file():
        report.add(Finding("ASGI_FILE", "config/asgi.py present", ReadinessSeverity.PASS))
    else:
        report.add(Finding("ASGI_FILE", "config/asgi.py missing (optional for ASGI workers)", ReadinessSeverity.WARN))

    if enforce_production_checks and wsgi_path.is_file():
        ok, detail = _wsgi_probe_cwd(repo_root)
        if ok:
            report.add(Finding("WSGI_IMPORT", "config.wsgi imports with django.setup()", ReadinessSeverity.PASS))
        else:
            report.add(
                Finding(
                    "WSGI_IMPORT",
                    f"Could not import config.wsgi ({detail})",
                    ReadinessSeverity.BLOCK,
                )
            )
    elif wsgi_path.is_file():
        report.add(Finding("WSGI_IMPORT", "Skipped WSGI import probe until production readiness", ReadinessSeverity.PASS))

    allow_sqlite = env_bool(os.environ.get("DJANGO_ALLOW_SQLITE_IN_PRODUCTION"), False)
    raw_url = os.environ.get("DATABASE_URL", "").strip()

    if raw_url:
        masked = mask_database_url(raw_url)
        ok, err = try_parse_database_url(raw_url)
        if not ok:
            report.add(Finding("DATABASE_URL", f"Not parseable: {err}", ReadinessSeverity.BLOCK))
            return
        cfg = databases_from_environ(repo_root)["default"]

        engine = cfg.get("ENGINE", "")
        if "sqlite" in engine:
            db_name = str(cfg.get("NAME", "")).lower()
            if ":memory:" in db_name or db_name.endswith(":memory:"):
                report.add(
                    Finding(
                        "DATABASE_URL",
                        f"DATABASE_URL targets in-memory SQLite ({masked}) — not suitable for production.",
                        ReadinessSeverity.BLOCK,
                    )
                )
            elif allow_sqlite:
                report.add(
                    Finding(
                        "DATABASE_URL",
                        f"SQLite explicitly tolerated via DJANGO_ALLOW_SQLITE_IN_PRODUCTION ({masked})",
                        ReadinessSeverity.WARN,
                    )
                )
            else:
                report.add(
                    Finding(
                        "DATABASE_URL",
                        f"SQLite DATABASE_URL ({masked}) — PostgreSQL recommended for concurrent production workloads.",
                        ReadinessSeverity.WARN,
                    )
                )
        elif "postgresql" in engine or "postgres" in engine:
            report.add(Finding("DATABASE_URL", f"PostgreSQL DATABASE_URL resolved ({masked})", ReadinessSeverity.PASS))
        else:
            report.add(Finding("DATABASE_URL", f"DATABASE_URL resolved ({masked})", ReadinessSeverity.PASS))
        return

    # Implicit SQLite (no DATABASE_URL)
    inferred = databases_from_environ(repo_root)["default"]
    inferred_name = inferred.get("NAME", "")
    path_obj = Path(str(inferred_name)).resolve()

    if not enforce_production_checks:
        rel = ""
        try:
            rel = str(path_obj.resolve().relative_to(repo_root.resolve()))
        except ValueError:
            rel = path_obj.as_posix()
        report.add(
            Finding(
                "DATABASE_BACKEND",
                f"No DATABASE_URL — implicit SQLite backend ({rel})",
                ReadinessSeverity.PASS,
            )
        )
        return

    if allow_sqlite:
        report.add(
            Finding(
                "DATABASE_BACKEND",
                "DATABASE_URL absent — SQLite file backend enabled "
                "(DJANGO_ALLOW_SQLITE_IN_PRODUCTION=true acknowledges this explicitly).",
                ReadinessSeverity.WARN,
            )
        )
    elif _within_repo(path_obj, repo_root):
        report.add(
            Finding(
                "DATABASE_BACKEND",
                "DEBUG=false readiness: default SQLite under repository path without DATABASE_URL. "
                "Set DATABASE_URL to PostgreSQL or set DJANGO_ALLOW_SQLITE_IN_PRODUCTION=true for intentional SQLite.",
                ReadinessSeverity.BLOCK,
            )
        )
    else:
        report.add(
            Finding(
                "DATABASE_BACKEND",
                f"DATABASE_URL absent — DJANGO_SQLITE_PATH points outside repo ({path_obj.as_posix()}); "
                "confirm persistence and backups.",
                ReadinessSeverity.WARN,
            )
        )


def env_int_simple(raw: str | None, default: int) -> int:
    try:
        if raw is None or raw.strip() == "":
            return default
        return max(0, int(raw.strip()))
    except ValueError:
        return default


def read_debug_os() -> bool:
    raw = os.environ.get("DJANGO_DEBUG")
    if raw is None:
        return True
    return env_bool(raw, True)


def should_enforce_production(*, assume_production: bool) -> bool:
    if assume_production:
        return True
    raw_dbg = os.environ.get("DJANGO_DEBUG")
    if raw_dbg is None:
        # Local ergonomics: no explicit DJANGO_DEBUG → skipped hard checks unless --assume-production
        return False
    return not read_debug_os()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Wisdomize deploy readiness checker")
    parser.add_argument(
        "--assume-production",
        action="store_true",
        help="Force production assertions even while DJANGO_DEBUG is unset/true (CI/production simulation).",
    )
    args = parser.parse_args(argv)

    dbg = read_debug_os()
    enforce = should_enforce_production(assume_production=args.assume_production)
    report = collect_readiness(dbg, enforce_production_checks=enforce)
    report.print_report()

    fh = sys.stdout
    fh.write("\nSummary\n")
    fh.write(f"- blocking findings: {report.blocking_count}\n")
    fh.write(f"- warnings: {report.warning_count}\n")

    exit_code = 1 if report.blocking_count > 0 else 0
    if exit_code == 0 and report.warning_count > 0:
        fh.write("\n(No blocking issues — review warnings above.)\n")
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
