"""Public Wisdomize web page route tests."""

from __future__ import annotations

import json
import os

import django
from django.test import Client

from app.core.models import EngineAnalyzeResponse, WisdomizeEngineOutput

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
django.setup()


def _html(path: str) -> str:
    response = Client().get(path)
    assert response.status_code == 200
    return response.content.decode("utf-8")


def test_landing_page_returns_200_and_contains_positioning() -> None:
    html = _html("/")
    assert "Wisdomize" in html
    assert "Ethical clarity for real-life dilemmas" in html
    assert "Inspired by the Bhagavad Gita" in html
    assert "not professional advice" in html


def test_faq_page_contains_privacy_verse_and_crisis_safe_content() -> None:
    html = _html("/faq/")
    assert "Raw dilemma logging is not enabled by default" in html
    assert "feedback layer does not store raw dilemma text or the full engine response" in html
    assert "A verse appears only when retrieval clears the match threshold" in html
    assert "Closest teaching is a paraphrased ethical lens" in html
    assert "Crisis-safe mode" in html
    assert "bypasses spiritual, viral, and share-oriented framing" in html


def test_placeholder_pages_return_200() -> None:
    for path in ["/about/", "/pricing/", "/contact/"]:
        assert Client().get(path).status_code == 200


def test_landing_page_cta_points_to_analyze_ui_route() -> None:
    html = _html("/")
    assert 'href="/analyze/"' in html
    assert "Analyze a dilemma" in html


def test_public_nav_links_and_footer_disclaimer_render() -> None:
    html = _html("/")
    for href in ['href="/analyze/"', 'href="/faq/"', 'href="/about/"', 'href="/pricing/"', 'href="/contact/"']:
        assert href in html
    assert "contact local emergency services or a trusted person" in html


def test_api_analyze_still_behaves_unchanged(monkeypatch) -> None:
    output = WisdomizeEngineOutput.model_validate(
        {
            "dilemma_id": "web-api-unchanged",
            "dilemma": "Another synthetic dilemma for the analyzer stub path, long enough for schema.",
            "verdict_sentence": "Choose truthful action with disciplined intent.",
            "classification": "Mixed",
            "alignment_score": 12,
            "confidence": 0.7,
            "internal_driver": {"primary": "Fear", "hidden_risk": "Self-justification"},
            "core_reading": "The conflict is between convenience and integrity.",
            "gita_analysis": "Duty and truth should remain aligned.",
            "verse_match": None,
            "closest_teaching": "Act from duty without clinging to outcomes.",
            "if_you_continue": {"short_term": "Relief with residue.", "long_term": "Compounded ethical debt."},
            "counterfactuals": {
                "clearly_adharmic_version": {"assumed_context": "Hide facts", "decision": "Conceal", "why": "Avoid blame"},
                "clearly_dharmic_version": {"assumed_context": "Disclose facts", "decision": "Report", "why": "Protect trust"},
            },
            "higher_path": "Choose transparent correction.",
            "ethical_dimensions": {
                "dharma_duty": {"score": 1, "note": "Partially aligned"},
                "satya_truth": {"score": 1, "note": "Truth under pressure"},
                "ahimsa_nonharm": {"score": 0, "note": "Harm depends on the next step"},
                "nishkama_detachment": {"score": 1, "note": "Outcome anxiety is present"},
                "shaucha_intent": {"score": 0, "note": "Motive is mixed"},
                "sanyama_restraint": {"score": 1, "note": "Restraint is still available"},
                "lokasangraha_welfare": {"score": 0, "note": "Wider impact is limited"},
                "viveka_discernment": {"score": 1, "note": "The facts support a careful step"},
            },
            "missing_facts": [],
            "share_layer": {
                "anonymous_share_title": "Duty vs convenience",
                "card_quote": "Shortcuts become chains.",
                "reflective_question": "What action survives daylight?",
            },
        }
    )
    response_model = EngineAnalyzeResponse.model_validate(
        {
            "meta": {"contract_version": "1.0", "engine_version": "2.1", "semantic_mode_default": "stub_default"},
            "output": output.model_dump(mode="json"),
        }
    )
    monkeypatch.setattr("app.transport.django_api.handle_engine_request", lambda payload: response_model)
    response = Client().post(
        "/api/v1/analyze",
        data=json.dumps(
            {
                "dilemma": "Another synthetic dilemma for the analyzer stub path, long enough for schema.",
                "contract_version": "1.0",
            }
        ),
        content_type="application/json",
    )
    body = response.json()
    assert response.status_code == 200
    assert list(body.keys()) == ["meta", "output"]
    assert body["output"]["dilemma_id"] == "web-api-unchanged"


def test_analyze_ui_still_posts_to_presentation_route() -> None:
    html = _html("/analyze/")
    assert 'fetch("/api/v1/analyze/presentation"' in html
    assert 'fetch("/api/v1/analyze",' not in html
