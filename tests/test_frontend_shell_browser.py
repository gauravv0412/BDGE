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

from app.presentation import build_card_copy_overlay, build_result_view_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
django.setup()


def _success_payload(*, verse: bool = False, closest: bool = True) -> dict[str, object]:
    dimensions = {
        "dharma_duty": {"score": 1, "note": "Partially aligned"},
        "satya_truth": {"score": 1, "note": "Truth under pressure"},
        "ahimsa_nonharm": {"score": 0, "note": "Harm depends on the next step"},
        "nishkama_detachment": {"score": 1, "note": "Outcome anxiety is present"},
        "shaucha_intent": {"score": 0, "note": "Motive is mixed"},
        "sanyama_restraint": {"score": 1, "note": "Restraint is still available"},
        "lokasangraha_welfare": {"score": 0, "note": "Wider impact is limited"},
        "viveka_discernment": {"score": 1, "note": "The facts support a careful step"},
    }
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
            "ethical_dimensions": dimensions,
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


def _valid_narrator() -> dict[str, object]:
    return {
        "share_line": "LLM share line: clean pressure needs a clean method.",
        "simple": {
            "headline": "Correct it without hiding the method.",
            "explanation": "The narrator copy says the visible test is whether fear makes truth negotiable.",
            "next_step": "Choose transparent correction.",
        },
        "krishna_lens": {
            "question": "What correction stays clean after the pressure fades?",
            "teaching": "Use duty as a practical check on method.",
            "mirror": "Fear can be loud without becoming the decision-maker.",
        },
        "brutal_truth": {
            "headline": "Shortcut now, residue later.",
            "punchline": "The method becomes the memory.",
            "share_quote": "A clean action survives pressure.",
        },
        "deep_view": {
            "what_is_happening": "Fear is narrowing the visible options.",
            "risk": "The risk is letting convenience train the next compromise.",
            "higher_path": "Correct the record transparently and keep the method accountable.",
        },
    }


def with_presentation_payload(payload: dict[str, object], *, narrator: dict[str, object] | None = None) -> dict[str, object]:
    """Match production: /analyze/presentation attaches the server-built view model."""
    if "error" in payload:
        return payload
    presentation = build_result_view_model(payload).model_dump(mode="json")
    output = payload["output"]
    assert isinstance(output, dict)
    presentation["cards"] = build_card_copy_overlay(
        output=output,
        deterministic_presentation=presentation,
        narrator=narrator,
    )
    if narrator is not None:
        presentation["narrator"] = narrator
        presentation["narrator_meta"] = {"final_source": "llm_initial", "fallback_returned": False}
    return {
        **payload,
        "presentation": presentation,
    }


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
        yield f"http://{host}:{port}/analyze"
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
    page.unroute("**/api/v1/analyze/presentation")

    def _handler(route):
        route.fulfill(
            status=status,
            headers={"Content-Type": "application/json", "X-Request-ID": request_id},
            body=json.dumps(payload),
        )

    page.route("**/api/v1/analyze/presentation", _handler)


def _submit(page: Page, dilemma: str) -> None:
    page.fill("#dilemma", dilemma)
    page.click("#submit-btn")


def _site_root(live_server_url: str) -> str:
    return live_server_url.rsplit("/analyze", 1)[0]


def _install_pending_fetch(page: Page, payload: dict[str, object], *, ok: bool = True) -> None:
    page.add_init_script(
        f"""
        (() => {{
          const payload = {json.dumps(payload)};
          const status = {200 if ok else 500};
          window.__presentationFetchCalls = [];
          window.__resolvePresentationFetch = null;
          const originalFetch = window.fetch.bind(window);
          window.fetch = (url, options) => {{
            const urlText = String(url);
            if (urlText.endsWith('/api/v1/analyze/presentation')) {{
              window.__presentationFetchCalls.push({{ url: urlText, body: options && options.body }});
              return new Promise((resolve) => {{
                window.__resolvePresentationFetch = () => resolve(new Response(JSON.stringify(payload), {{
                  status,
                  headers: {{ 'Content-Type': 'application/json', 'X-Request-ID': 'req-hidden-from-ui' }}
                }}));
              }});
            }}
            if (urlText.endsWith('/api/v1/analyze')) {{
              window.__presentationFetchCalls.push({{ url: urlText, body: options && options.body, wrongEndpoint: true }});
              return Promise.resolve(new Response(JSON.stringify({{ error: {{ message: 'wrong endpoint' }} }}), {{ status: 418 }}));
            }}
            return originalFetch(url, options);
          }};
        }})();
        """
    )


def _install_pending_feedback_fetch(page: Page, *, ok: bool = True) -> None:
    page.add_init_script(
        f"""
        (() => {{
          const status = {200 if ok else 500};
          window.__feedbackFetchCalls = [];
          window.__resolveFeedbackFetch = null;
          const previousFetch = window.fetch.bind(window);
          window.fetch = (url, options) => {{
            const urlText = String(url);
            if (urlText.endsWith('/api/v1/feedback')) {{
              window.__feedbackFetchCalls.push({{ url: urlText, body: options && options.body }});
              return new Promise((resolve) => {{
                window.__resolveFeedbackFetch = () => resolve(new Response(JSON.stringify({{
                  ok: {str(ok).lower()},
                  feedback_id: 'fb-browser-1',
                  error: {{ code: 'feedback_storage_failed', message: 'internal hidden failure' }}
                }}), {{
                  status,
                  headers: {{ 'Content-Type': 'application/json', 'X-Request-ID': 'feedback-hidden-id' }}
                }}));
              }});
            }}
            return previousFetch(url, options);
          }};
        }})();
        """
    )


def _extract_cards(page: Page) -> list[dict[str, object]]:
    return page.evaluate(
        """() => Array.from(document.querySelectorAll('[data-card]'))
          .map((node) => ({
            card: node.dataset.card || '',
            title: (node.querySelector('h2,h3')?.textContent || '').trim(),
            primary_text: (node.querySelector('[data-card-primary]')?.textContent || '').trim(),
            sections: Array.from(node.querySelectorAll('details.presentation-section')).map((details) => ({
              label: details.dataset.sectionLabel || (details.querySelector('summary')?.textContent || '').trim(),
              text: (details.querySelector('[data-section-text]')?.textContent || '').trim()
            }))
          }))"""
    )


def _extract_if_you_continue_blocks(page: Page) -> list[dict[str, str]]:
    return page.evaluate(
        """() => Array.from(document.querySelectorAll('[data-card="if-you-continue"] [data-consequence-term]'))
          .map((node) => ({
            term: node.dataset.consequenceTerm || '',
            consequence: (node.querySelector('[data-consequence]')?.textContent || '').trim(),
            explain: (node.querySelector('[data-explain-simply]')?.textContent || '').trim()
          }))"""
    )


@pytest.mark.browser
def test_public_landing_page_loads_at_desktop_viewport(page: Page, live_server_url: str) -> None:
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(f"{_site_root(live_server_url)}/")
    page.wait_for_selector("text=Ethical clarity for real-life dilemmas")
    assert page.locator("text=Analyze a dilemma").is_visible()


@pytest.mark.browser
def test_public_landing_page_mobile_has_no_horizontal_overflow(page: Page, live_server_url: str) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{_site_root(live_server_url)}/")
    page.wait_for_selector("text=Ethical clarity for real-life dilemmas")
    has_overflow = page.evaluate(
        "() => Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) > document.documentElement.clientWidth + 2"
    )
    assert has_overflow is False


@pytest.mark.browser
def test_public_landing_cta_opens_analyze_ui(page: Page, live_server_url: str) -> None:
    page.goto(f"{_site_root(live_server_url)}/")
    page.locator("a", has_text="Analyze a dilemma").first.click()
    page.wait_for_url("**/analyze/")
    page.wait_for_selector("#dilemma")
    assert page.locator("text=Wisdomize Read-Only Shell").is_visible()


@pytest.mark.browser
def test_public_faq_page_is_reachable_from_nav(page: Page, live_server_url: str) -> None:
    page.goto(f"{_site_root(live_server_url)}/")
    page.locator("nav a", has_text="FAQ").click()
    page.wait_for_url("**/faq/")
    page.wait_for_selector("text=Why does it sometimes show")
    assert page.locator("text=Crisis-safe mode").is_visible()


@pytest.mark.browser
def test_shell_page_loads_and_submits_via_client_request(page: Page, live_server_url: str) -> None:
    call_count = {"n": 0}
    wrong_endpoint_count = {"n": 0}

    def _handler(route):
        call_count["n"] += 1
        route.fulfill(
            status=200,
            headers={"Content-Type": "application/json", "X-Request-ID": "req-client-flow"},
            body=json.dumps(with_presentation_payload(_success_payload())),
        )

    page.route("**/api/v1/analyze/presentation", _handler)
    page.route("**/api/v1/analyze", lambda route: (wrong_endpoint_count.__setitem__("n", wrong_endpoint_count["n"] + 1), route.abort()))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Analysis Result")
    assert call_count["n"] == 1
    assert wrong_endpoint_count["n"] == 0
    assert page.locator("text=Verdict").count() > 0
    assert page.locator("text=Classification").count() > 0


@pytest.mark.browser
def test_loading_state_disables_button_and_blocks_duplicate_submit(page: Page, live_server_url: str) -> None:
    _install_pending_fetch(page, with_presentation_payload(_success_payload()))
    page.goto(f"{live_server_url}/")
    page.fill("#dilemma", "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.click("#submit-btn")

    page.wait_for_selector("#loading")
    assert page.locator("#submit-btn").is_disabled()
    assert page.locator("#submit-btn").inner_text() == "Analyzing..."
    assert page.locator("text=Reading this dilemma with care").is_visible()

    page.evaluate("() => document.getElementById('analyze-form').requestSubmit()")
    assert page.evaluate("() => window.__presentationFetchCalls.length") == 1

    page.evaluate("() => window.__resolvePresentationFetch()")
    page.wait_for_selector("text=Analysis Result")
    loading_display = page.eval_on_selector("#loading", "el => getComputedStyle(el).display")
    assert loading_display == "none"
    assert not page.locator("#submit-btn").is_disabled()
    assert page.locator("#submit-btn").inner_text() == "Analyze Dilemma"


@pytest.mark.browser
def test_theme_toggle_switches_and_persists_after_reload(page: Page, live_server_url: str) -> None:
    page.goto(f"{live_server_url}/")
    initial_theme = page.evaluate("() => document.documentElement.dataset.theme")
    assert initial_theme in {"light", "dark"}

    page.locator("#theme-toggle").click()
    toggled_theme = page.evaluate("() => document.documentElement.dataset.theme")
    assert toggled_theme in {"light", "dark"}
    assert toggled_theme != initial_theme
    assert page.evaluate("() => localStorage.getItem('wisdomize-theme')") == toggled_theme

    page.reload()
    page.wait_for_selector("#theme-toggle")
    assert page.evaluate("() => document.documentElement.dataset.theme") == toggled_theme


@pytest.mark.browser
def test_success_renders_major_sections(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=with_presentation_payload(_success_payload()))
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
        "Shareable Insight",
    ]:
        page.wait_for_selector(f"text={section}")


@pytest.mark.browser
def test_feedback_ui_hidden_before_result_and_visible_after_success(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=with_presentation_payload(_success_payload()))
    page.goto(f"{live_server_url}/")
    assert page.locator("[data-card='feedback']").count() == 0

    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("[data-card='feedback']")
    assert page.locator("[data-card='feedback']", has_text="Was this useful?").count() == 1


@pytest.mark.browser
def test_feedback_usefulness_submit_sends_safe_payload(page: Page, live_server_url: str) -> None:
    captured: list[dict[str, object]] = []
    raw_dilemma = "Another synthetic dilemma for the analyzer stub path, long enough for schema."

    def _feedback_handler(route):
        captured.append(json.loads(route.request.post_data or "{}"))
        route.fulfill(status=200, headers={"Content-Type": "application/json"}, body=json.dumps({"ok": True, "feedback_id": "fb-1"}))

    _route_api(page, payload=with_presentation_payload(_success_payload()))
    page.route("**/api/v1/feedback", _feedback_handler)
    page.goto(f"{live_server_url}/")
    _submit(page, raw_dilemma)
    page.wait_for_selector("[data-card='feedback']")

    page.locator("[data-card='feedback'] [data-feedback-group='usefulness'][data-feedback-value='up']").click()
    page.locator("[data-card='feedback'] [data-feedback-submit='true']").click()
    page.wait_for_selector("text=Thanks — this helps improve Wisdomize.")

    assert len(captured) == 1
    body = captured[0]
    assert body["result_id"] == "browser-1"
    assert body["usefulness"] == "up"
    assert body["route"] == "presentation"
    assert body["guidance_type"] == "closest_teaching"
    serialized = json.dumps(body)
    assert raw_dilemma not in serialized
    assert "output" not in body
    assert "verdict_sentence" not in serialized


@pytest.mark.browser
def test_feedback_duplicate_submission_is_prevented(page: Page, live_server_url: str) -> None:
    _install_pending_feedback_fetch(page)
    _route_api(page, payload=with_presentation_payload(_success_payload()))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("[data-card='feedback']")

    page.locator("[data-card='feedback'] [data-feedback-group='usefulness'][data-feedback-value='down']").click()
    page.locator("[data-card='feedback'] [data-feedback-submit='true']").click()
    page.wait_for_function("() => window.__feedbackFetchCalls && window.__feedbackFetchCalls.length === 1")
    assert page.locator("[data-card='feedback'] [data-feedback-submit='true']").is_disabled()

    page.evaluate("() => document.querySelector('[data-feedback-submit=\"true\"]').click()")
    assert page.evaluate("() => window.__feedbackFetchCalls.length") == 1
    page.evaluate("() => window.__resolveFeedbackFetch()")
    page.wait_for_selector("text=Thanks — this helps improve Wisdomize.")


@pytest.mark.browser
def test_feedback_failure_shows_friendly_retryable_error(page: Page, live_server_url: str) -> None:
    _install_pending_feedback_fetch(page, ok=False)
    _route_api(page, payload=with_presentation_payload(_success_payload()))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("[data-card='feedback']")

    page.locator("[data-card='feedback'] [data-feedback-group='usefulness'][data-feedback-value='up']").click()
    page.locator("[data-card='feedback'] [data-feedback-submit='true']").click()
    page.evaluate("() => window.__resolveFeedbackFetch()")
    page.wait_for_selector("text=Feedback could not be saved. Please try again.")

    assert page.locator("[data-card='feedback'] [data-feedback-submit='true']").inner_text() == "Try again"
    assert page.locator("text=internal hidden failure").count() == 0
    assert page.locator("text=feedback-hidden-id").count() == 0


@pytest.mark.browser
def test_verse_match_branch_renders(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=with_presentation_payload(_success_payload(verse=True, closest=False)))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Gita Verse")
    page.wait_for_selector("text=कर्मण्येवाधिकारस्ते")
    page.wait_for_selector("text=karmaṇy evādhikāras te")
    page.wait_for_selector("text=Source: Gita")
    page.wait_for_selector("text=Thy right is to work only.")
    assert page.locator("text=Closest Teaching").count() == 0
    assert page.locator("[data-card='feedback']", has_text="Verse relevance").count() == 1


@pytest.mark.browser
def test_closest_teaching_branch_renders(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=with_presentation_payload(_success_payload(verse=False, closest=True)))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Closest Gita Lens")
    page.wait_for_selector("text=Why this stays provisional")
    assert page.locator("text=Gita Verse").count() == 0
    assert page.locator("summary", has_text="Show Gita anchor").count() == 0
    assert page.locator("text=कर्मण्येवाधिकारस्ते").count() == 0
    assert page.locator("text=Paraphrased teaching, not a quoted verse").count() > 0
    assert page.locator("[data-card='feedback']", has_text="Teaching relevance").count() == 1


@pytest.mark.browser
def test_null_null_guidance_fallback_renders(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=with_presentation_payload(_success_payload(verse=False, closest=False)))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Guidance")
    page.wait_for_selector("text=No verse or closest teaching is currently available for this response.")


@pytest.mark.browser
def test_public_error_is_friendly_retryable_and_loading_clears(page: Page, live_server_url: str) -> None:
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
    page.wait_for_selector("text=Something went wrong")
    page.wait_for_selector("text=Something went wrong while reading this dilemma. Please try again.")
    assert page.locator("[data-retry-action='true']").is_visible()
    assert page.locator("text=this must never be shown").count() == 0
    assert page.locator("text=Internal engine failure.").count() == 0
    assert page.locator("text=req-error-browser-1").count() == 0
    loading_display = page.eval_on_selector("#loading", "el => getComputedStyle(el).display")
    assert loading_display == "none"


@pytest.mark.browser
def test_failed_request_loading_appears_then_disappears(page: Page, live_server_url: str) -> None:
    _install_pending_fetch(
        page,
        {
            "meta": {"contract_version": "1.0", "engine_version": "2.1", "semantic_mode_default": "stub_default"},
            "error": {"code": "engine_execution_failed", "message": "Provider timeout", "debug": "hidden"},
        },
        ok=False,
    )
    page.goto(f"{live_server_url}/")
    page.fill("#dilemma", "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.click("#submit-btn")
    page.wait_for_selector("#loading")
    assert page.locator("#loading").is_visible()

    page.evaluate("() => window.__resolvePresentationFetch()")
    page.wait_for_selector("text=Something went wrong while reading this dilemma. Please try again.")
    loading_display = page.eval_on_selector("#loading", "el => getComputedStyle(el).display")
    assert loading_display == "none"
    assert page.locator("text=Provider timeout").count() == 0
    assert page.locator("text=hidden").count() == 0


@pytest.mark.browser
def test_xss_content_rendered_as_text_not_executed(page: Page, live_server_url: str) -> None:
    payload = _success_payload()
    output = payload["output"]
    assert isinstance(output, dict)
    output["verdict_sentence"] = "<script>window.__xss_test = 'pwned'</script>"
    _route_api(page, payload=with_presentation_payload(payload))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Verdict")
    xss_flag = page.evaluate("() => window.__xss_test || null")
    assert xss_flag is None
    assert page.locator("text=<script>window.__xss_test = 'pwned'</script>").count() > 0


@pytest.mark.browser
def test_share_spotlight_renders_in_dom(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=with_presentation_payload(_success_payload()))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Share-ready")
    spotlight_text = page.locator("[data-card='share'] [data-card-primary]").inner_text().strip()
    assert spotlight_text
    assert len(spotlight_text) <= 160
    assert page.locator("[data-card='share'] .share-question").inner_text().strip().endswith("?")


@pytest.mark.browser
def test_if_you_continue_renders_non_duplicate_humanized_rows(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=with_presentation_payload(_success_payload()))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("[data-card='if-you-continue']")

    blocks = _extract_if_you_continue_blocks(page)
    assert {block["term"] for block in blocks} == {"short_term", "long_term"}
    for block in blocks:
        assert block["consequence"]
        assert block["explain"]
        assert block["consequence"] != block["explain"]
    visible = page.locator("[data-card='if-you-continue']").inner_text()
    assert visible.count("Relief with residue.") == 1
    assert visible.count("Compounded ethical debt.") == 1
    visible_lower = visible.lower()
    assert "what happens soon" in visible_lower
    assert "what this means" in visible_lower
    assert "what it can become" in visible_lower


@pytest.mark.browser
def test_hero_share_card_uses_llm_narrator_copy_once(page: Page, live_server_url: str) -> None:
    narrator = _valid_narrator()
    _route_api(page, payload=with_presentation_payload(_success_payload(), narrator=narrator))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("[data-card='share']")

    share_line = str(narrator["share_line"])
    reflective_question = str(narrator["krishna_lens"]["question"])
    assert page.locator("[data-card='share'] [data-card-primary]").inner_text().strip() == share_line
    assert page.locator("[data-card='share'] .share-question").inner_text().strip() == reflective_question
    assert page.locator(".share-question", has_text=reflective_question).count() == 1
    for forbidden in ("Dilemma context:", "Core reading:", "Gita analysis:"):
        assert page.locator("body", has_text=forbidden).count() == 0


@pytest.mark.browser
def test_hero_share_copy_buttons_copy_expected_payloads(page: Page, live_server_url: str) -> None:
    narrator = _valid_narrator()
    _route_api(page, payload=with_presentation_payload(_success_payload(), narrator=narrator))
    page.goto(f"{live_server_url}/")
    page.evaluate("() => { window.__copiedPayloads = []; }")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("[data-card='share']")

    page.locator("[data-card='share'] [data-copy-action='share-line']").click()
    page.wait_for_function("() => window.__copiedPayloads && window.__copiedPayloads.length === 1")
    first_payload = page.evaluate("() => window.__copiedPayloads[0]")
    assert str(narrator["share_line"]) in first_payload
    assert str(narrator["krishna_lens"]["question"]) in first_payload

    page.locator("[data-card='share'] [data-copy-action='full-insight']").click()
    page.wait_for_function("() => window.__copiedPayloads && window.__copiedPayloads.length === 2")
    second_payload = page.evaluate("() => window.__copiedPayloads[1]")
    assert str(narrator["share_line"]) in second_payload
    assert "Choose truthful action with disciplined intent." in second_payload
    assert str(narrator["krishna_lens"]["question"]) in second_payload
    assert page.locator(".share-question", has_text=str(narrator["krishna_lens"]["question"])).count() == 1
    assert page.locator("[data-card='share'] .copy-state").inner_text() == "Copied"


@pytest.mark.browser
def test_expandable_sections_open_on_click(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=with_presentation_payload(_success_payload()))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.locator("summary", has_text="Explain simply").first.wait_for()
    first_details = page.locator("details.presentation-section").first
    assert first_details.evaluate("el => el.open") is False
    page.locator("summary", has_text="Explain simply").first.click()
    assert first_details.evaluate("el => el.open") is True


@pytest.mark.browser
def test_ethical_dimensions_all_visible_by_default(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=with_presentation_payload(_success_payload()))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("[data-card='ethical-dimensions']")
    dimension_details = page.locator("[data-card='ethical-dimensions'] details.presentation-section")
    assert dimension_details.count() == 8
    for index in range(8):
        assert dimension_details.nth(index).evaluate("el => el.open") is True
    assert page.locator("[data-card='ethical-dimensions']", has_text="dharma_duty").count() == 1
    assert page.locator("[data-card='ethical-dimensions']", has_text="viveka_discernment").count() == 1


@pytest.mark.browser
def test_verdict_and_higher_path_hide_raw_context_labels(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=with_presentation_payload(_success_payload()))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("[data-card='higher-path']")
    cards = _extract_cards(page)
    by_key = {str(card["card"]): card for card in cards}
    text_blob = " ".join(
        [
            *[section["text"] for section in by_key["verdict"]["sections"]],
            *[section["text"] for section in by_key["higher-path"]["sections"]],
        ]
    )
    for forbidden in ("Dilemma context:", "Core reading:", "Gita analysis:"):
        assert forbidden not in text_blob


@pytest.mark.browser
def test_mobile_viewport_has_no_horizontal_overflow(page: Page, live_server_url: str) -> None:
    narrator = _valid_narrator()
    _route_api(page, payload=with_presentation_payload(_success_payload(verse=True, closest=False), narrator=narrator))
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("text=Gita Verse")

    share_card = page.locator("[data-card='share']")
    assert share_card.is_visible()
    assert page.locator("[data-card='share'] [data-copy-action='share-line']").is_visible()
    assert page.locator("[data-card='share'] [data-copy-action='full-insight']").is_visible()
    assert page.locator(".share-question", has_text=str(narrator["krishna_lens"]["question"])).count() == 1
    assert page.locator("[data-card='ethical-dimensions'] details.presentation-section").count() == 8
    assert page.locator("[data-card='ethical-dimensions'] details.presentation-section").first.evaluate("el => el.open") is False
    assert page.locator("[data-card='guidance'] .verse-sanskrit", has_text="कर्मण्येवाधिकारस्ते").is_visible()

    has_overflow = page.evaluate(
        "() => Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) > document.documentElement.clientWidth + 2"
    )
    assert has_overflow is False


@pytest.mark.browser
def test_browser_smoke_capture_reads_full_card_and_section_text(page: Page, live_server_url: str) -> None:
    _route_api(page, payload=with_presentation_payload(_success_payload()))
    page.goto(f"{live_server_url}/")
    _submit(page, "Another synthetic dilemma for the analyzer stub path, long enough for schema.")
    page.wait_for_selector("[data-card='guidance']")
    cards = _extract_cards(page)
    by_key = {str(card["card"]): card for card in cards}

    assert by_key["verdict"]["primary_text"] == "Choose truthful action with disciplined intent."
    assert by_key["guidance"]["title"] == "Closest Gita Lens"
    assert "Paraphrased teaching, not a quoted verse" in by_key["guidance"]["primary_text"]
    guidance_text = page.locator("[data-card='guidance']").inner_text()
    assert "Duty and truth should remain aligned." in guidance_text
    assert "not a direct verse verdict" in guidance_text
    assert "Show Gita anchor" not in guidance_text
    combined = guidance_text.lower()
    for forbidden in ("engine", "threshold", "fallback", "verse_match", "selected", "retrieval", "schema"):
        assert forbidden not in combined
    assert by_key["share"]["primary_text"]
    assert len(by_key["share"]["primary_text"]) <= 160
    share_question = page.locator("[data-card='share'] .share-question").inner_text().strip()
    assert share_question.endswith("?")
    assert " keeps I " not in share_question
    assert page.locator(".share-question", has_text=share_question).count() == 1


@pytest.mark.browser
def test_livelihood_share_copy_is_contextual_not_relationship_based(page: Page, live_server_url: str) -> None:
    payload = _success_payload()
    output = payload["output"]
    assert isinstance(output, dict)
    output["dilemma"] = (
        "I can legally open an alcohol shop in my neighborhood, but I worry it may increase harm "
        "even though it would support my family."
    )
    output["core_reading"] = "The tension is livelihood versus community harm."
    _route_api(page, payload=with_presentation_payload(payload))
    page.goto(f"{live_server_url}/")
    _submit(page, output["dilemma"])
    page.wait_for_selector("[data-card='share']")
    cards = _extract_cards(page)
    by_key = {str(card["card"]): card for card in cards}
    share_text = str(by_key["share"]["primary_text"]).lower()
    assert "chemistry" not in share_text
    assert "betray" not in share_text
    assert "partner" not in share_text
    assert any(term in share_text for term in ("legal", "income", "profit", "harm", "community", "livelihood"))


@pytest.mark.browser
def test_counterfactual_wallet_vs_desire_vs_low_info_are_domain_specific(page: Page, live_server_url: str) -> None:
    wallet_payload = _success_payload()
    wallet_out = wallet_payload["output"]
    assert isinstance(wallet_out, dict)
    wallet_out["dilemma"] = "I found a wallet with cash and an ID in a cafe, and I am tempted to keep the cash because my rent is due."
    _route_api(page, payload=with_presentation_payload(wallet_payload))
    page.goto(f"{live_server_url}/")
    _submit(page, wallet_out["dilemma"])
    page.wait_for_selector("[data-card='counterfactuals']")
    wallet_cards = _extract_cards(page)
    wallet_cf = next(card for card in wallet_cards if card["card"] == "counterfactuals")
    wallet_sections = {s["label"]: s["text"] for s in wallet_cf["sections"]}

    desire_payload = _success_payload()
    out = desire_payload["output"]
    assert isinstance(out, dict)
    out["dilemma"] = "I have developed desire for my close friend's partner, and they seem interested too, but acting on it would betray my friend."
    _route_api(page, payload=with_presentation_payload(desire_payload))
    page.goto(f"{live_server_url}/")
    _submit(page, out["dilemma"])
    page.wait_for_selector("[data-card='counterfactuals']")
    desire_cards = _extract_cards(page)
    desire_cf = next(card for card in desire_cards if card["card"] == "counterfactuals")
    desire_sections = {s["label"]: s["text"] for s in desire_cf["sections"]}

    low_payload = _success_payload()
    low_out = low_payload["output"]
    assert isinstance(low_out, dict)
    low_out["dilemma"] = "I need to decide whether to do the thing soon, but I cannot share many details right now."
    _route_api(page, payload=with_presentation_payload(low_payload))
    page.goto(f"{live_server_url}/")
    _submit(page, low_out["dilemma"])
    page.wait_for_selector("[data-card='counterfactuals']")
    low_cards = _extract_cards(page)
    low_cf = next(card for card in low_cards if card["card"] == "counterfactuals")
    low_sections = {s["label"]: s["text"] for s in low_cf["sections"]}

    assert "wallet" in wallet_sections["Adharmic likely decision"].lower() or "cash" in wallet_sections["Adharmic likely decision"].lower()
    assert "chemistry" in desire_sections["Adharmic likely decision"].lower() or "betray" in desire_sections["Adharmic likely decision"].lower()
    assert "missing fact" in low_sections["Dharmic likely decision"].lower() or "irreversible" in low_sections["Dharmic likely decision"].lower()
    assert wallet_sections["Adharmic likely decision"] != desire_sections["Adharmic likely decision"] != low_sections["Adharmic likely decision"]


@pytest.mark.browser
def test_guidance_and_higher_path_explain_simply_are_not_duplicates(page: Page, live_server_url: str) -> None:
    payload = _success_payload(verse=True, closest=False)
    output = payload["output"]
    assert isinstance(output, dict)
    output["dilemma"] = "I found a wallet with cash and an ID in a cafe, and I am tempted to keep the cash because my rent is due."
    output["verse_match"] = {
        "verse_ref": "6.5",
        "sanskrit_devanagari": "उद्धरेदात्मनात्मानं",
        "sanskrit_iast": "uddhared ātmanātmānaṁ",
        "hindi_translation": "अपने द्वारा अपना उद्धार करे।",
        "english_translation": "Let a man raise himself by himself.",
        "source": "Gita",
        "why_it_applies": "The verse points to self-mastery before impulse takes over.",
        "match_confidence": 0.8,
    }
    _route_api(page, payload=with_presentation_payload(payload))
    page.goto(f"{live_server_url}/")
    _submit(page, output["dilemma"])
    page.wait_for_selector("[data-card='guidance']")
    cards = _extract_cards(page)
    by_key = {str(card["card"]): card for card in cards}
    guidance = by_key["guidance"]
    guidance_text = page.locator("[data-card='guidance']").inner_text()
    assert "strengthens you or weakens you" in guidance["primary_text"]
    assert guidance["primary_text"] != "The verse points to self-mastery before impulse takes over."
    assert "signals" not in guidance_text.lower()
    assert "dominant ethical pull" not in guidance_text.lower()
    higher = by_key["higher-path"]
    h_sections = {section["label"]: section["text"] for section in higher["sections"]}
    assert h_sections["Explain simply"] != higher["primary_text"]


@pytest.mark.browser
def test_browser_smoke_capture_reads_verse_anchor_and_safety_card(page: Page, live_server_url: str) -> None:
    payload = _success_payload(verse=True, closest=False)
    output = payload["output"]
    assert isinstance(output, dict)
    output["dilemma"] = "I feel everyone would be better without me and I may do anything harmful tonight."
    _route_api(page, payload=with_presentation_payload(payload))
    page.goto(f"{live_server_url}/")
    _submit(page, "I feel everyone would be better without me and I may do anything harmful tonight.")
    page.wait_for_selector("[data-card='safety']")
    page.wait_for_selector("text=crisis_safe")
    assert page.locator("text=Adharmic path").count() == 0
    assert page.locator("text=Dharmic path").count() == 0
    assert page.locator("text=Share Layer").count() == 0
    cards = _extract_cards(page)
    by_key = {str(card["card"]): card for card in cards}

    assert "immediate human support" in str(by_key["safety"]["primary_text"])
    assert by_key["higher-path"]["title"] == "Immediate Next Step"
    assert "moral decision" in by_key["higher-path"]["primary_text"].lower()
    guidance_sections = {section["label"]: section["text"] for section in by_key["guidance"]["sections"]}
    assert by_key["guidance"]["title"] == "Support first"
    assert "Show Gita anchor" not in guidance_sections
    assert "share" not in by_key
    assert "ethical-dimensions" not in by_key
    assert "Alternative storylines" in by_key["counterfactuals"]["primary_text"]


@pytest.mark.browser
def test_crisis_safe_no_duplicate_higher_path_card(page: Page, live_server_url: str) -> None:
    payload = _success_payload(verse=True, closest=False)
    out = payload["output"]
    assert isinstance(out, dict)
    out["dilemma"] = "I may hurt myself and need help before I do anything harmful."
    _route_api(page, payload=with_presentation_payload(payload))
    page.goto(f"{live_server_url}/")
    _submit(page, "I may hurt myself and need help before I do anything harmful.")
    page.wait_for_selector("[data-card='higher-path']")
    assert page.locator("[data-card='higher-path']").count() == 1
