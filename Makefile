# BDGE / Wisdomize — local and CI test entrypoints.
# Activate your venv first (e.g. source .venv/bin/activate), or set PYTEST explicitly.

PYTEST ?= pytest
PYTHON ?= python3

.PHONY: test-fast test-browser test-all smoke help

help:
	@echo "Targets:"
	@echo "  make test-fast   - pytest excluding @pytest.mark.browser (default local feedback)"
	@echo "  make test-browser - browser / Playwright tests only"
	@echo "  make test-all    - full pytest suite"
	@echo "  make smoke       - in-process POST /api/v1/analyze smoke check"

test-fast:
	$(PYTEST) -m "not browser"

test-browser:
	$(PYTEST) -m browser

test-all:
	$(PYTEST)

smoke:
	PYTHONPATH=. $(PYTHON) -m app.scripts.smoke_analyze_api
