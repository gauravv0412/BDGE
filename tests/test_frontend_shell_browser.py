"""Browser-level integration tests for client-rendered shell (Step 18)."""

from __future__ import annotations

import json
import os
import socket
import threading
from wsgiref.simple_server import WSGIRequestHandler, make_server

import django
import pytest
from django.core.wsgi import get_wsgi_application
from playwright.sync_api import Browser, Page, Playwright, sync_playwright

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
django.setup()


def _success_payload(*, verse: bool = False, closest: bool = True) -> dict[str, object]:
    payload: dict[str, object] = {
        "meta": {"contract_version": "1.0", "engine_version": "2.1", "semantic_mode_default": "stub_default"},
        "output": {
            "dilemma_id": "browser-1",
            "dilemma": "Another synthetic dilemma for the analyzer stub path, long enough for schema.",
            "verdict_sentence": "Choose truthful action with disciplined intent.",
            "classification": "Mixed",
            "alignment_score": 12,
            "confidence": 0.7,
            "internal_driver": {"primary": "Fear", "hidden_risk": "Self-justification"},
            "core_reading": "The conflict is between convenience and integrity.",
            "gita_analysis": "Duty and truth should remain aligned.",
            "verse_match": None,
            "closest_teaching": "Act from duty without clinging to outcomes." if closest else None,
            "if_you_continue": {"short_term": "Relief with residue.", "long_term": "Compounded ethical debt."},
            "counterfactuals": {
                "clearly_adharmic_version": {"assumed_context": "Hide facts", "decision": "Conceal", "why": "Avoid blame"},
                "clearly_dharmic_version": {
                    "assumed_context": "Disclose facts",
                    "decision": "Report",
                    "why": "Protect trust",
                },
            },
            "higher_path": "Choose transparent correction.",
            "ethical_dimensions": {
                "dharma_duty": {"score": 1, "note": "Partially aligned"},
                "satya_truth": {"score": 1, "note": "Truth under pressure"},
            },
            "missing_facts": ["Stakeholder timing"],
            "share_layer": {
                "anonymous_share_title": "Duty vs convenience",
                "card_quote": "Shortcuts become chains.",
                "reflective_question": "What action survives daylight?",
            },
        },
    }
    if verse:
        output = payload["output"]
        assert isinstance(output, dict)
        output["closest_teaching"] = None
        output["verse_match"] = {
            "verse_ref": "2.47",
            "sanskrit_devanagari": "कर्मण्येवाधिकारस्ते",
            "sanskrit_iast": "karmaṇy evādhikāras te",
            "hindi_translation": "तुझे कर्म करने का अधिकार है।",
            "english_translation": "Thy right is to work only.",
            "source": "Gita",
            "why_it_applies": "Focus on right action, not result anxiety.",
            "match_confidence": 0.8,
        }
    return payload


@pytest.fixture(scope="session")
def live_server_url() -> str:
    class QuietHandler(WSGIRequestHandler):
        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    app = get_wsgi_application()
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    host, port = sock.getsockname()
    sock.close()
    server = make_server(host, port, app, handler_class=QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.fixture(scope="session")
def browser() -> Browser:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture
def page(browser: Browser) -> Page:
    context = browser.new_context()
    p = context.new_page()
    yield p
    context.close()


def _route_api(page: Page, *, payload: dict[str, object], status: int = 200, request_id: str = "req-browser-1") -> None:
    def _handler(route):
        route.fulfill(
            status=status,
            headers={"Content-Type": "application/json", "X-Request-ID": request_id},
            body=json.dumps(payload),
        )

    page.route("**/api/v1/analyze", _handler)


def _submit(page: Page, dilemma: str) -> None:
    page.fill("#dilemma", dilemma)
    page.click("#submit-btn")


@pytest.mark.browser
def test_shell_page_loads_and_submits_via_client_request(page: Page, live_server_url: str) -> None:
    call_count = {"n": 0}

    def _handler(route):
        call_count["n"] += 1
        route.fulfill(
            status=200,
            headers={"Content-Type": "application/json", "X-Request-ID": "req-client-flow"},
            body=json.dumps(_success_payload()),
        )

    page.route("**/api/v1/analyze", _handler)
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Analysis Result")
    assert call_count["n"] == 1
    assert page.locator("text=Verdict").count() > 0
    assert page.locator("text=Classification").count() > 0


@pytest.mark.browser
def test_success_renders_major_sections(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=_success_payload())
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    for section in [
        "Analysis Result",
        "Verdict",
        "Inner Dynamics",
        "If You Continue",
        "Counterfactuals",
        "Higher Path",
        "Ethical Dimensions",
        "Missing Facts",
        "Share Layer",
    ]:
        page.wait_for_selector(f"text={section}")


@pytest.mark.browser
def test_verse_match_branch_renders(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=_success_payload(verse=True, closest=False))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Verse Match")
    assert page.locator("text=Closest Teaching").count() == 0


@pytest.mark.browser
def test_closest_teaching_branch_renders(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=_success_payload(verse=False, closest=True))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Closest Teaching")
    assert page.locator("text=Verse Match").count() == 0


@pytest.mark.browser
def test_null_null_guidance_fallback_renders(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=_success_payload(verse=False, closest=False))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Guidance")
    page.wait_for_selector("text=No verse or closest teaching is currently available for this response.")


@pytest.mark.browser
def test_public_error_and_request_id_render_and_loading_clears(page: Page, live_server_url: str) -> None:
    _route_api(
        page,
        payload={
            "meta": {"contract_version": "1.0", "engine_version": "2.1", "semantic_mode_default": "stub_default"},
            "error": {
                "code": "engine_execution_failed",
                "message": "Internal engine failure.",
                "internal_debug": "this must never be shown",
            },
        },
        status=500,
        request_id="req-error-browser-1",
    )
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Request Failed")
    page.wait_for_selector("text=Internal engine failure.")
    page.wait_for_selector("text=Request ID: req-error-browser-1")
    assert page.locator("text=this must never be shown").count() == 0
    loading_display = page.eval_on_selector("#loading", "el => getComputedStyle(el).display")
    assert loading_display == "none"


@pytest.mark.browser
def test_xss_content_rendered_as_text_not_executed(page: Page, live_server_url: str) -> None:
    payload = _success_payload()
    output = payload["output"]
    assert isinstance(output, dict)
    output["verdict_sentence"] = "<script>window.__xss_test = 'pwned'</script>"
    _route_api(page, payload=payload)
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Verdict")
    xss_flag = page.evaluate("() => window.__xss_test || null")
    assert xss_flag is None
    assert page.locator("text=<script>window.__xss_test = 'pwned'</script>").count() > 0


@pytest.mark.browser
def test_share_spotlight_renders_in_dom(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=_success_payload())
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Share-ready")
    page.wait_for_selector("text=Shortcuts become chains.")
