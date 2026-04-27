import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "artifacts" / "browser_smoke_step31D.json"
AUDIT_JSON = ROOT / "artifacts" / "browser_smoke_step31E_prose_audit.json"
AUDIT_MD = ROOT / "artifacts" / "browser_smoke_step31E_prose_audit.md"

REQUIRED_CLASSIFICATION_KEYS = {
    "readability",
    "context_specificity",
    "simple_explanation_quality",
    "shareability",
    "safety_tone",
    "human_judgment",
    "excerpt_visible",
    "suggested_improvement_direction",
    "flags",
}
VALID_CLASSIFICATION_VALUES = {
    "readability": {"clear", "hard", "too_abstract", "verbose", "confusing"},
    "context_specificity": {"strong", "acceptable", "weak", "generic", "missing"},
    "simple_explanation_quality": {
        "useful",
        "placeholder",
        "missing",
        "too_hard",
        "not_contextual",
        "n/a",
    },
    "shareability": {
        "screenshot_ready",
        "decent",
        "not_shareable",
        "n/a",
    },
    "safety_tone": {"safe", "borderline", "concerning", "n/a"},
}


def _case_card_keys(cards: list[dict], case_id: str) -> set[str]:
    return {c.get("card") for c in cards if c.get("card") is not None}


def test_step31e_audit_artifacts_present_and_parsable() -> None:
    assert SRC.is_file()
    for p in (AUDIT_JSON, AUDIT_MD):
        assert p.is_file() and p.stat().st_size > 0, f"missing/empty: {p}"

    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    assert audit.get("step") == "31E"
    assert audit.get("source_artifact") == "artifacts/browser_smoke_step31D.json"
    for k in [
        "aggregate_metrics",
        "top_repeated_placeholders",
        "top_5_copy_problems",
        "recommended_implementation_order",
        "cases",
    ]:
        assert k in audit

    source = json.loads(SRC.read_text(encoding="utf-8"))
    src_ids = {c.get("case_id") for c in source.get("cases", []) if c.get("case_id")}
    out_cases = {c.get("case_id") for c in audit.get("cases", []) if c.get("case_id")}
    assert out_cases == src_ids
    assert len(out_cases) == 12

    for case in audit.get("cases", []):
        case_id = case["case_id"]
        assert isinstance(case.get("special_checks", {}).get("closest_teaching", []), list)
        for card in case.get("cards", []):
            key = card.get("card")
            assert key
            for field in ["title", *REQUIRED_CLASSIFICATION_KEYS]:
                assert field in card
            for fname, values in VALID_CLASSIFICATION_VALUES.items():
                val = card.get(fname)
                assert val in values, f"{case_id}::{key} {fname}={val!r}"

            ex = (card.get("excerpt_visible") or "").strip()
            assert 10 <= len(ex) <= 400

            for f in card.get("flags", []) or []:
                assert isinstance(f, dict)
                assert f.get("code")
                if "label" in f:
                    assert isinstance(f.get("label"), str) and f["label"].strip()

        sc_ids = {c.get("case_id") for c in source.get("cases", []) if c.get("case_id") == case_id}
        assert len(sc_ids) == 1
        src_case = next(c for c in source.get("cases", []) if c.get("case_id") == case_id)
        out_keys = _case_card_keys(case.get("cards", []), case_id)
        for k0 in _case_card_keys(src_case.get("cards", []), case_id):
            assert k0 in out_keys, f"audit missing card {k0} for {case_id}"

    m = audit["aggregate_metrics"]
    for k in [
        "readability_not_clear_label_counts",
        "simple_explanation_failures",
        "context_specificity_issue_counts",
        "counterfactual_cards_flagged_generic_weak_or_templated",
        "share_cards_flagged_for_hook_or_context",
        "safety_tone_concern_events",
    ]:
        assert k in m

    text = AUDIT_MD.read_text(encoding="utf-8")
    for heading in [
        "Executive summary",
        "Aggregate metrics",
        "Top repeated placeholder strings",
        "Top 5 product copy issues",
        "Case-by-case audit",
        "Checkpoint summary",
    ]:
        assert heading in text


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
