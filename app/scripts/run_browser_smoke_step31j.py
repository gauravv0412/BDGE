"""Capture full visible prose from the browser shell for Step 31J.

Same harness as Step 31I; artifacts are written to `browser_smoke_step31J.*` by default
for before/after comparison. This step focuses on guidance/higher-path explain-simply repair.
Does not change engine behavior, retrieval scoring, or public schema.

Usage:
    PYTHONPATH=. python -m app.scripts.run_browser_smoke_step31j
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from wsgiref.simple_server import WSGIRequestHandler, make_server

import django
from django.core.wsgi import get_wsgi_application
from playwright.sync_api import Page, sync_playwright


_CASES: list[tuple[str, str]] = [
    ("wallet_found_cash", "I found a wallet with cash and an ID in a cafe, and I am tempted to keep the cash because my rent is due."),
    (
        "manager_takes_credit_public_correction",
        "My manager publicly took credit for my work, and I am considering correcting the record in the same public meeting.",
    ),
    (
        "legal_alcohol_shop",
        "I can legally open an alcohol shop in my neighborhood, but I worry it may increase harm even though it would support my family.",
    ),
    (
        "friends_partner_desire",
        "I have developed desire for my close friend's partner, and they seem interested too, but acting on it would betray my friend.",
    ),
    (
        "aging_parent_refuses_hospitalization",
        "My aging parent is refusing hospitalization after a serious diagnosis, and I am torn between respecting them and forcing treatment.",
    ),
    (
        "cosmetic_surgery",
        "I am considering cosmetic surgery mainly because I feel insecure and want social approval, though the procedure is legal and safe.",
    ),
    (
        "abusive_parent_no_contact",
        "My parent was abusive for years, and I am considering going no contact even though relatives say it is my duty to stay connected.",
    ),
    (
        "caste_disapproved_marriage",
        "I want to marry someone I love, but my family rejects the relationship because of caste and threatens to cut ties.",
    ),
    (
        "anonymous_scathing_restaurant_review",
        "A restaurant treated me badly, and I want to post an anonymous scathing review that might damage their business reputation.",
    ),
    (
        "doctor_hiding_terminal_diagnosis",
        "As a doctor, I know a patient has a terminal diagnosis, and the family asks me to hide it from the patient to preserve hope.",
    ),
    (
        "crisis_self_harm_adjacent_input",
        "I feel overwhelmed and keep thinking everyone would be better without me, and I want guidance before I do anything harmful.",
    ),
    ("low_information_vague_input", "I need to decide whether to do the thing soon, but I cannot share many details right now."),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", default="artifacts/browser_smoke_step31J.json")
    parser.add_argument("--md-out", default="artifacts/browser_smoke_step31J.md")
    parser.add_argument("--base-url", default="")
    args = parser.parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
    django.setup()

    if args.base_url:
        payload = _run_browser_capture(args.base_url)
    else:
        with _local_server() as base_url:
            payload = _run_browser_capture(base_url)

    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(_markdown_report(payload), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


class _local_server:
    def __enter__(self) -> str:
        class QuietHandler(WSGIRequestHandler):
            def log_message(self, format: str, *args: object) -> None:  # noqa: A003
                return

        app = get_wsgi_application()
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        host, port = sock.getsockname()
        sock.close()
        self._server = make_server(host, port, app, handler_class=QuietHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return f"http://{host}:{port}"

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._server.shutdown()
        self._thread.join(timeout=5)


def _run_browser_capture(base_url: str) -> dict[str, Any]:
    run_started_at = datetime.now(UTC).isoformat()
    results: list[dict[str, Any]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1365, "height": 900})
        page = context.new_page()
        for case_id, prompt in _CASES:
            results.append(_run_case(page, base_url, case_id, prompt))
        context.close()
        browser.close()

    warnings = _build_warnings(results)
    return {
        "step": "31J",
        "title": "Browser smoke full visible prose capture (guidance/higher-path explain repair)",
        "run_started_at": run_started_at,
        "run_completed_at": datetime.now(UTC).isoformat(),
        "base_url": base_url,
        "summary": {
            "case_count": len(results),
            "api_200": sum(1 for item in results if item["api_status"] == 200),
            "cases_with_details": sum(1 for item in results if item["details_present"]),
            "cases_with_openable_details": sum(1 for item in results if item["details_openable"]),
            "console_error_cases": sum(1 for item in results if item["console_errors"]),
            "network_error_cases": sum(1 for item in results if item["network_errors"]),
            "layout_issue_cases": sum(1 for item in results if item["layout_issues"]),
        },
        "warnings": warnings,
        "cases": results,
        "note": "Step 31J run after guidance/higher-path explain-simply repair. No retrieval/engine/schema changes; presentation-only copy update.",
    }


def _run_case(page: Page, base_url: str, case_id: str, prompt: str) -> dict[str, Any]:
    console_errors: list[str] = []
    network_errors: list[dict[str, Any]] = []
    api_records: list[dict[str, Any]] = []

    def on_console(msg) -> None:
        if msg.type == "error":
            console_errors.append(msg.text)

    def on_request_failed(req) -> None:
        network_errors.append({"url": req.url, "failure": req.failure})

    def on_response(resp) -> None:
        if "/api/v1/analyze/presentation" not in resp.url:
            return
        record: dict[str, Any] = {"url": resp.url, "status": resp.status}
        try:
            record["body"] = resp.json()
        except Exception as exc:  # noqa: BLE001
            record["body_error"] = repr(exc)
        api_records.append(record)

    page.on("console", on_console)
    page.on("requestfailed", on_request_failed)
    page.on("response", on_response)
    try:
        page.set_viewport_size({"width": 1365, "height": 900})
        page.goto(f"{base_url}/", wait_until="domcontentloaded", timeout=30000)
        page.fill("#dilemma", prompt)
        page.click("#submit-btn")
        page.wait_for_selector("text=Analysis Result", timeout=300000)
        desktop_layout = _layout_status(page)
        page.set_viewport_size({"width": 390, "height": 844})
        mobile_layout = _layout_status(page)
        cards = _extract_cards(page)
        details_status = _details_status(page)
    finally:
        page.remove_listener("console", on_console)
        page.remove_listener("requestfailed", on_request_failed)
        page.remove_listener("response", on_response)

    api = api_records[-1] if api_records else {"status": None, "body": {}}
    body = api.get("body") if isinstance(api.get("body"), dict) else {}
    output = body.get("output") if isinstance(body, dict) and isinstance(body.get("output"), dict) else {}
    verse = output.get("verse_match") if isinstance(output.get("verse_match"), dict) else None
    layout_issues = []
    if desktop_layout["overflow_x"]:
        layout_issues.append("desktop horizontal overflow")
    if mobile_layout["overflow_x"]:
        layout_issues.append("mobile horizontal overflow")

    return {
        "case_id": case_id,
        "prompt": prompt,
        "timestamp": datetime.now(UTC).isoformat(),
        "api_status": api.get("status"),
        "classification": output.get("classification"),
        "alignment_score": output.get("alignment_score"),
        "confidence": output.get("confidence"),
        "rendered_guidance_branch": _guidance_branch(cards),
        "verse_ref": verse.get("verse_ref") if verse else None,
        "share_domain": (
            body.get("presentation", {}).get("meta", {}).get("share_domain")
            if isinstance(body.get("presentation"), dict)
            else None
        ),
        "cards": cards,
        "details_present": details_status["present"],
        "details_openable": details_status["openable"],
        "console_errors": console_errors,
        "network_errors": network_errors,
        "layout_issues": layout_issues,
        "desktop_layout": desktop_layout,
        "mobile_layout": mobile_layout,
    }


def _extract_cards(page: Page) -> list[dict[str, Any]]:
    return page.evaluate(
        """() => Array.from(document.querySelectorAll('[data-card]'))
          .filter((node) => node.dataset.card !== 'share-spotlight')
          .map((node) => ({
            card: node.dataset.card || '',
            title: (node.querySelector('h2,h3')?.textContent || '').trim(),
            primary_text: (node.querySelector('[data-card-primary]')?.textContent || '').trim(),
            sections: Array.from(node.querySelectorAll('details.presentation-section')).map((details) => ({
              label: details.dataset.sectionLabel || (details.querySelector('summary')?.textContent || '').trim(),
              text: (details.querySelector('[data-section-text]')?.textContent || '').trim(),
              open: details.open
            }))
          }))"""
    )


def _details_status(page: Page) -> dict[str, bool]:
    return page.evaluate(
        """() => {
          const first = document.querySelector('details.presentation-section');
          if (!first) return { present: false, openable: false };
          const summary = first.querySelector('summary');
          if (!summary) return { present: true, openable: false };
          const before = first.open;
          summary.click();
          const after = first.open;
          if (first.open !== before) summary.click();
          return { present: true, openable: before !== after };
        }"""
    )


def _layout_status(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => ({
          overflow_x: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) > document.documentElement.clientWidth + 2,
          viewport_width: document.documentElement.clientWidth,
          scroll_width: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)
        })"""
    )


def _guidance_branch(cards: list[dict[str, Any]]) -> str:
    guidance = next((card for card in cards if card.get("card") == "guidance"), {})
    title = str(guidance.get("title", ""))
    labels = {section.get("label") for section in guidance.get("sections", [])}
    if title == "Gita Verse" or "Show Gita anchor" in labels:
        return "verse_match"
    if title == "Support first":
        return "crisis_safe_support"
    if title == "Closest Gita Lens":
        return "closest_gita_lens"
    if title == "Closest Teaching":
        return "closest_teaching"
    return "neither"


def _build_warnings(results: list[dict[str, Any]]) -> dict[str, Any]:
    missing_cards: list[str] = []
    too_long: list[str] = []
    repeated: dict[str, int] = {}
    seen_sections: dict[str, int] = {}
    share_lines: dict[str, int] = {}
    broken_share_questions: list[str] = []
    share_domain_distribution: dict[str, int] = {}
    counterfactual_sections: dict[str, int] = {}
    crisis_counterfactual_not_suppressed: list[str] = []
    guidance_explain_duplicates: list[str] = []
    higher_path_explain_duplicates: list[str] = []
    guidance_metadata_word_leakage: list[str] = []
    for item in results:
        cards = item["cards"]
        present = {card["card"] for card in cards}
        has_safety = "safety" in present
        if has_safety:
            # crisis_safe: share + ethical-dimension card surfaces are not rendered; higher-path is Immediate Next Step at top.
            expected = {"safety", "verdict", "guidance", "if-you-continue", "counterfactuals", "higher-path"}
        else:
            expected = {"verdict", "guidance", "if-you-continue", "counterfactuals", "higher-path", "ethical-dimensions", "share"}
        for card in sorted(expected - present):
            missing_cards.append(f"{item['case_id']}:{card}")
        domain = str(item.get("share_domain") or "n/a")
        share_domain_distribution[domain] = share_domain_distribution.get(domain, 0) + 1
        for card in cards:
            primary = str(card.get("primary_text", ""))
            if not primary.strip():
                missing_cards.append(f"{item['case_id']}:{card.get('card')}:primary_text")
            if len(primary) > 500:
                too_long.append(f"{item['case_id']}:{card.get('card')}:primary_text:{len(primary)}")
            for section in card.get("sections", []):
                text = str(section.get("text", "")).strip()
                if not text:
                    missing_cards.append(f"{item['case_id']}:{card.get('card')}:{section.get('label')}")
                    continue
                if len(text) > 800:
                    too_long.append(f"{item['case_id']}:{card.get('card')}:{section.get('label')}:{len(text)}")
                seen_sections[text] = seen_sections.get(text, 0) + 1
                if card.get("card") == "share" and section.get("label") == "Reflective question":
                    normalized_q = " ".join(text.split())
                    if (
                        " keeps I " in f" {normalized_q} "
                        or "..." in normalized_q
                        or "… " in normalized_q
                        or not normalized_q.endswith("?")
                    ):
                        broken_share_questions.append(f"{item['case_id']}:{normalized_q[:120]}")
                if card.get("card") == "guidance" and section.get("label") == "Explain simply":
                    if " ".join(primary.split()).lower() == " ".join(text.split()).lower():
                        guidance_explain_duplicates.append(item["case_id"])
                    low = text.lower()
                    if any(word in low for word in ("signals", "dominant ethical pull", "theme", "theme tags", "applies")):
                        guidance_metadata_word_leakage.append(f"{item['case_id']}:{text[:140]}")
                if card.get("card") == "higher-path" and section.get("label") == "Explain simply":
                    if " ".join(primary.split()).lower() == " ".join(text.split()).lower():
                        higher_path_explain_duplicates.append(item["case_id"])
            if card.get("card") == "share":
                normalized_primary = " ".join(primary.split())
                if normalized_primary:
                    share_lines[normalized_primary] = share_lines.get(normalized_primary, 0) + 1
            if card.get("card") == "counterfactuals":
                for section in card.get("sections", []):
                    label = str(section.get("label", ""))
                    text = " ".join(str(section.get("text", "")).split())
                    if text:
                        key = f"{label}:{text}"
                        counterfactual_sections[key] = counterfactual_sections.get(key, 0) + 1
                if has_safety:
                    primary_low = primary.lower()
                    section_blob = " ".join(str(s.get("text", "")) for s in card.get("sections", [])).lower()
                    if "adharmic path" in primary_low or "dharmic path" in primary_low or "adharmic likely decision" in section_blob:
                        crisis_counterfactual_not_suppressed.append(item["case_id"])
    for text, count in seen_sections.items():
        if count >= 4:
            repeated[text[:120]] = count
    repeated_share = {line[:120]: count for line, count in share_lines.items() if count >= 2}
    repeated_counterfactual = {
        key[:140]: count for key, count in counterfactual_sections.items() if count >= 3
    }
    return {
        "empty_or_missing_card_text": missing_cards,
        "too_long_card_text": too_long,
        "repeated_placeholder_text": repeated,
        "repeated_share_text": repeated_share,
        "broken_share_question_fragments": broken_share_questions,
        "share_domain_distribution": share_domain_distribution,
        "repeated_counterfactual_text": repeated_counterfactual,
        "crisis_counterfactual_not_suppressed": crisis_counterfactual_not_suppressed,
        "guidance_explain_duplicates": guidance_explain_duplicates,
        "higher_path_explain_duplicates": higher_path_explain_duplicates,
        "guidance_metadata_word_leakage": guidance_metadata_word_leakage,
    }


def _markdown_report(payload: dict[str, Any]) -> str:
    warnings = payload["warnings"]
    lines = [
        "# Step 31J Browser Smoke Full Prose Capture (guidance/higher-path explain repair)",
        "",
        "This artifact captures visible browser prose after explain-simply repair for guidance and higher-path.",
        "",
        "- Before/after note: guidance/higher-path explain sections are now domain-aware and de-duplicated from primary text.",
        "",
        "## Summary",
        "",
        f"- Cases captured: {payload['summary']['case_count']}",
        f"- API 200 responses: {payload['summary']['api_200']}",
        f"- Cases with details sections: {payload['summary']['cases_with_details']}",
        f"- Cases with openable details: {payload['summary']['cases_with_openable_details']}",
        f"- Console error cases: {payload['summary']['console_error_cases']}",
        f"- Network error cases: {payload['summary']['network_error_cases']}",
        f"- Layout issue cases: {payload['summary']['layout_issue_cases']}",
        "",
        "## Warnings",
        "",
        f"- Empty/missing card text warnings: {len(warnings['empty_or_missing_card_text'])}",
        f"- Too-long card warnings: {len(warnings['too_long_card_text'])}",
        f"- Repeated-placeholder warnings: {len(warnings['repeated_placeholder_text'])}",
        f"- Repeated share-text warnings: {len(warnings.get('repeated_share_text', {}))}",
        f"- Broken share-question fragment warnings: {len(warnings.get('broken_share_question_fragments', []))}",
        f"- Repeated counterfactual-text warnings: {len(warnings.get('repeated_counterfactual_text', {}))}",
        f"- Crisis counterfactual suppression failures: {len(warnings.get('crisis_counterfactual_not_suppressed', []))}",
        f"- Guidance explain-simply duplicate count: {len(warnings.get('guidance_explain_duplicates', []))}",
        f"- Higher-path explain-simply duplicate count: {len(warnings.get('higher_path_explain_duplicates', []))}",
        f"- Guidance metadata-word leakage count: {len(warnings.get('guidance_metadata_word_leakage', []))}",
        "",
    ]
    if warnings["empty_or_missing_card_text"]:
        lines.extend(["### Empty/Missing Card Text", ""])
        lines.extend(f"- `{item}`" for item in warnings["empty_or_missing_card_text"][:40])
        lines.append("")
    if warnings["too_long_card_text"]:
        lines.extend(["### Too-Long Card Text", ""])
        lines.extend(f"- `{item}`" for item in warnings["too_long_card_text"][:40])
        lines.append("")
    if warnings["repeated_placeholder_text"]:
        lines.extend(["### Repeated Placeholder Text", ""])
        lines.extend(f"- {count}x: {text}" for text, count in warnings["repeated_placeholder_text"].items())
        lines.append("")
    if warnings.get("repeated_share_text"):
        lines.extend(["### Repeated Share Text", ""])
        lines.extend(f"- {count}x: {text}" for text, count in warnings["repeated_share_text"].items())
        lines.append("")
    if warnings.get("broken_share_question_fragments"):
        lines.extend(["### Broken Share Question Fragments", ""])
        lines.extend(f"- `{item}`" for item in warnings["broken_share_question_fragments"][:40])
        lines.append("")
    if warnings.get("share_domain_distribution"):
        lines.extend(["### Share Domain Distribution", ""])
        lines.extend(f"- {domain}: {count}" for domain, count in sorted(warnings["share_domain_distribution"].items()))
        lines.append("")
    if warnings.get("repeated_counterfactual_text"):
        lines.extend(["### Repeated Counterfactual Text", ""])
        lines.extend(f"- {count}x: {text}" for text, count in warnings["repeated_counterfactual_text"].items())
        lines.append("")
    if warnings.get("crisis_counterfactual_not_suppressed"):
        lines.extend(["### Crisis Counterfactual Suppression Failures", ""])
        lines.extend(f"- `{item}`" for item in warnings["crisis_counterfactual_not_suppressed"])
        lines.append("")
    if warnings.get("guidance_explain_duplicates"):
        lines.extend(["### Guidance Explain Simply Duplicates", ""])
        lines.extend(f"- `{item}`" for item in warnings["guidance_explain_duplicates"])
        lines.append("")
    if warnings.get("higher_path_explain_duplicates"):
        lines.extend(["### Higher Path Explain Simply Duplicates", ""])
        lines.extend(f"- `{item}`" for item in warnings["higher_path_explain_duplicates"])
        lines.append("")
    if warnings.get("guidance_metadata_word_leakage"):
        lines.extend(["### Guidance Metadata-word Leakage", ""])
        lines.extend(f"- `{item}`" for item in warnings["guidance_metadata_word_leakage"][:40])
        lines.append("")

    lines.extend(["## Case-by-case Visible Prose Excerpts", ""])
    for item in payload["cases"]:
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Classification: {item.get('classification')} ({item.get('alignment_score')}, confidence {item.get('confidence')})",
                f"- Guidance branch: {item.get('rendered_guidance_branch')}; verse_ref: {item.get('verse_ref') or '-'}",
                f"- Share domain: {item.get('share_domain') or '-'}",
                f"- Details present/openable: {item.get('details_present')} / {item.get('details_openable')}",
                "",
            ]
        )
        for card in item["cards"]:
            lines.extend([f"#### {card['card']}: {card['title']}", "", _clip(card.get("primary_text", "")), ""])
            for section in card.get("sections", [])[:3]:
                lines.extend([f"- {section['label']}: {_clip(section.get('text', ''), 240)}"])
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _clip(value: str, limit: int = 320) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


if __name__ == "__main__":
    raise SystemExit(main())
