"""CLI entrypoint for Wisdomize deploy readiness."""

from __future__ import annotations

from app.deploy.readiness import main

if __name__ == "__main__":
    raise SystemExit(main())
