"""Frontend client-rendered shell tests (Step 17)."""

from __future__ import annotations

import os
import re
from pathlib import Path

import django
from django.test import Client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
django.setup()


def _page_html() -> str:
    client = Client()
    response = client.get("/analyze/")
    assert response.status_code == 200
    return response.content.decode("utf-8")


def test_frontend_shell_page_presence() -> None:
    html = _page_html()
    assert "Wisdomize Read-Only Shell" in html
    assert 'textarea id="dilemma"' in html
    assert 'id="result-root"' in html
    assert "Ready for Analysis" in html


def test_first_user_readiness_doc_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    doc = root / "docs" / "first_user_readiness.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "## What the product can do today" in text
    assert "crisis" in text.lower()


def test_frontend_shell_disclaimer_and_input_safety_present() -> None:
    html = _page_html()
    assert 'id="shell-global-disclaimer"' in html
    assert 'id="shell-input-safety"' in html
    assert "reflective guidance" in html
    assert "acute crisis" in html


def test_frontend_shell_presentation_mode_and_crisis_branch_present() -> None:
    html = _page_html()
    assert "presentation_mode" in html
    assert "crisis_safe" in html
    assert "buildClientPresentation" in html


def test_frontend_shell_client_submission_path_uses_presentation_api_without_changing_public_api() -> None:
    html = _page_html()
    assert 'fetch("/api/v1/analyze/presentation"' in html
    assert '"Content-Type": "application/json"' in html
    assert '"X-CSRFToken": csrfToken' in html
    assert 'JSON.stringify({ dilemma: dilemma, contract_version: "1.0" })' in html
    assert "form.addEventListener(\"submit\"" in html
    assert "e.preventDefault();" in html


def test_frontend_shell_success_section_renderers_present() -> None:
    html = _page_html()
    for section in [
        "Analysis Result",
        "Presentation mode",
        "Verdict",
        "Inner Dynamics",
        "If You Continue",
        "Counterfactuals",
        "Higher Path",
        "Ethical Dimensions",
        "Missing Facts",
        "Shareable Insight",
    ]:
        assert f'"{section}"' in html
    assert "renderSuccess(payload, requestId)" in html
    assert '"hero-grid"' in html
    assert '"card share spotlight"' in html
    assert '"Share-ready"' in html
    assert '"Copy share line"' in html
    assert '"Copy full insight"' in html
    assert "compactSharePayload" in html
    assert "presentationCardCopy" in html
    assert "renderPresentationCard" in html
    assert "renderExpandableSection" in html
    assert "presentation-section" in html


def test_frontend_shell_no_raw_context_labels_in_client_renderer() -> None:
    html = _page_html()
    assert "Dilemma context:" not in html
    assert "Core reading:" not in html
    assert "Gita analysis:" not in html
    assert "Copy refinement note" not in html


def test_frontend_shell_public_error_renderer_present() -> None:
    html = _page_html()
    assert "function renderError()" in html
    assert "\"Something went wrong\"" in html
    assert "\"Something went wrong while reading this dilemma. Please try again.\"" in html
    assert "retry.dataset.retryAction" in html


def test_frontend_shell_public_error_hides_request_id_and_internals() -> None:
    html = _page_html()
    assert "response.headers.get(\"X-Request-ID\")" in html
    assert "appendPair(card, \"Request ID\", requestId)" not in html
    assert "\"engine_execution_failed\"" in html
    assert "\"Internal engine failure.\"" in html


def test_frontend_shell_loading_and_theme_controls_present() -> None:
    html = _page_html()
    assert 'id="loading" class="loading-card"' in html
    assert "Reading this dilemma with care..." in html
    assert "Separating pressure from facts" in html
    assert "let isPending = false;" in html
    assert 'id="theme-toggle"' in html
    assert "localStorage.setItem(\"wisdomize-theme\"" in html


def test_frontend_shell_verse_branch_behavior_present() -> None:
    html = _page_html()
    assert "\"Gita Verse\"" in html
    assert "\"Closest Gita Lens\"" in html
    assert "\"Show Gita anchor\"" in html
    assert "\"Why this stays provisional\"" in html
    assert "\"No verse or closest teaching is currently available for this response.\"" in html


def test_frontend_shell_client_side_xss_safety_regression() -> None:
    html = _page_html()
    # Contract-aware client rendering should use textContent/createTextNode, not unsafe HTML injection.
    assert "textContent = content" in html
    assert "document.createTextNode" in html
    assert "innerHTML =" not in html


def test_frontend_shell_summary_tone_logic_present() -> None:
    html = _page_html()
    assert 'if (c === "dharmic") return "positive";' in html
    assert 'if (c === "adharmic") return "negative";' in html
    assert 'return "mixed";' in html


def test_frontend_shell_missing_facts_no_prefix_injected() -> None:
    html = _page_html()
    assert '"Follow-up prompt: "' not in html


def test_frontend_shell_csrf_token_is_real_path() -> None:
    html = _page_html()
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
    assert match is not None
    token = match.group(1)
    assert token
    assert token != "None"
