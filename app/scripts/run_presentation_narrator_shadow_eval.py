"""Offline shadow-eval harness for presentation narrator behavior."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest import mock

from app.core.benchmark_loader import DEFAULT_BENCHMARK_PATH, load_dilemmas
from app.presentation.config import load_presentation_llm_config
from app.presentation.prompts import select_narrator_style
from app.presentation.provider import ProviderCallResult
from app.presentation.validators import detect_style_repetition_warnings

_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OOD_PATH = _ROOT / "tests" / "fixtures" / "live_retrieval_ood_W021-W050.json"
DEFAULT_OUT_JSON = _ROOT / "artifacts" / "presentation_narrator_shadow_eval.json"
DEFAULT_OUT_MD = _ROOT / "artifacts" / "presentation_narrator_shadow_eval.md"


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _valid_narrator_payload() -> dict[str, Any]:
    return {
        "share_line": "Pressure explains urgency. It does not erase the cost.",
        "simple": {
            "headline": "The pressure is real; keep the method clean.",
            "explanation": "This decision asks for disciplined action under strain.",
            "next_step": "Take one accountable step that avoids hidden harm.",
        },
        "krishna_lens": {
            "question": "Which choice still stands after urgency fades?",
            "teaching": "Clarity under pressure reveals alignment.",
            "mirror": "Relief now can become regret later if method drifts.",
        },
        "brutal_truth": {
            "headline": "Shortcuts collect interest.",
            "punchline": "A private compromise can harden into pattern.",
            "share_quote": "Pressure explains urgency, not permission.",
        },
        "deep_view": {
            "what_is_happening": "Urgency is compressing discernment.",
            "risk": "Fast relief can normalize avoidable harm.",
            "higher_path": "Choose the clean next step and keep it reviewable.",
        },
    }


def _invalid_narrator_payload() -> dict[str, Any]:
    return {
        "share_line": "Pressure explains urgency. It does not erase the cost.",
        "simple": {"headline": "classification says okay", "explanation": "theme and scorer agree", "next_step": "go"},
        "krishna_lens": {"question": "q?", "teaching": "t", "mirror": "m"},
        "brutal_truth": {"headline": "h", "punchline": "p", "share_quote": "s"},
        "deep_view": {"what_is_happening": "w", "risk": "r", "higher_path": "h"},
    }


@contextmanager
def _forced_shadow_env() -> Any:
    forced = {
        "PRESENTATION_LLM_SHADOW": "true",
        "PRESENTATION_LLM_ENABLED": "false",
        "PRESENTATION_LLM_REPAIR_ENABLED": "true",
    }
    backup = {k: os.getenv(k) for k in forced}
    try:
        for key, value in forced.items():
            os.environ[key] = value
        yield
    finally:
        for key, old in backup.items():
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old


@contextmanager
def _mock_provider(mode: str) -> Any:
    if mode == "none":
        yield
        return

    state = {"calls": 0}

    def _provider(**kwargs: Any) -> ProviderCallResult:
        state["calls"] += 1
        if mode == "always_valid":
            return ProviderCallResult(ok=True, payload=_valid_narrator_payload())
        if mode == "always_invalid":
            return ProviderCallResult(ok=True, payload=_invalid_narrator_payload())
        # repair_success: odd call invalid, even call valid
        if state["calls"] % 2 == 1:
            return ProviderCallResult(ok=True, payload=_invalid_narrator_payload())
        return ProviderCallResult(ok=True, payload=_valid_narrator_payload())

    with mock.patch("app.presentation.llm_narrator.call_presentation_provider", _provider):
        yield


def _load_ood_cases(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list):
        return []
    rows: list[dict[str, str]] = []
    for row in cases:
        if not isinstance(row, dict):
            continue
        dilemma = str(row.get("dilemma") or "").strip()
        if not dilemma:
            continue
        rows.append(
            {
                "dilemma_id": str(row.get("dilemma_id") or "").strip() or "ood-unknown",
                "dilemma": dilemma,
                "source": "ood",
            }
        )
    return rows


def _load_benchmark_cases(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for case in load_dilemmas(path=path):
        dilemma = str(case.get("dilemma") or "").strip()
        if not dilemma:
            continue
        rows.append(
            {
                "dilemma_id": str(case.get("dilemma_id") or "").strip() or "benchmark-unknown",
                "dilemma": dilemma,
                "source": "benchmark",
                "classification": str(case.get("classification") or "").strip(),
            }
        )
    return rows


def _run_case(client: Any, case: dict[str, str]) -> dict[str, Any]:
    response = client.post(
        "/api/v1/analyze/presentation",
        data=json.dumps(
            {
                "dilemma": case["dilemma"],
                "dilemma_id": case["dilemma_id"],
                "contract_version": "1.0",
            }
        ),
        content_type="application/json",
    )
    body = response.json()
    output = body.get("output", {}) if isinstance(body, dict) else {}
    presentation = body.get("presentation", {}) if isinstance(body, dict) else {}
    narrator_meta = presentation.get("narrator_meta", {}) if isinstance(presentation, dict) else {}
    core_classification = str(case.get("classification") or output.get("classification") or "Unknown")
    accepted_preview = narrator_meta.get("accepted_llm_preview") if isinstance(narrator_meta, dict) else None
    style_profile = select_narrator_style(case["dilemma_id"])
    return {
        "dilemma_id": case["dilemma_id"],
        "source": case["source"],
        "http_status": response.status_code,
        "classification": core_classification,
        "api_output_classification": str(output.get("classification") or "Unknown"),
        "style_profile": style_profile["name"],
        "presentation_mode": str(presentation.get("presentation_mode") or "unknown"),
        "narrator_meta": narrator_meta if isinstance(narrator_meta, dict) else {},
        "accepted_llm_preview": accepted_preview if isinstance(accepted_preview, dict) else None,
        "error_code": (body.get("error") or {}).get("code") if isinstance(body, dict) and isinstance(body.get("error"), dict) else None,
    }


def _compute_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    provider_called = sum(1 for row in rows if row["narrator_meta"].get("provider_called") is True)
    initial_valid = sum(1 for row in rows if row["narrator_meta"].get("initial_attempt_valid") is True)
    repair_attempted = sum(1 for row in rows if row["narrator_meta"].get("repair_attempted") is True)
    repair_valid = sum(1 for row in rows if row["narrator_meta"].get("repair_valid") is True)
    crisis_bypass = sum(
        1
        for row in rows
        if row["presentation_mode"] == "crisis_safe" and row["narrator_meta"].get("provider_called") is False
    )
    final_sources = Counter(str(row["narrator_meta"].get("final_source") or "unknown") for row in rows)
    style_profiles = Counter(str(row.get("style_profile") or "unknown") for row in rows)
    fallback_count = sum(1 for row in rows if row["narrator_meta"].get("fallback_returned") is True)
    accepted_previews = [row["accepted_llm_preview"] for row in rows if isinstance(row.get("accepted_llm_preview"), dict)]

    rejection_counter: Counter[str] = Counter()
    breakdown: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "accepted_initial": 0, "accepted_repair": 0, "fallback": 0})
    for row in rows:
        classification = row["classification"]
        breakdown[classification]["total"] += 1
        meta = row["narrator_meta"]
        final_source = str(meta.get("final_source") or "")
        if final_source == "llm_initial":
            breakdown[classification]["accepted_initial"] += 1
        elif final_source == "llm_repair":
            breakdown[classification]["accepted_repair"] += 1
        else:
            breakdown[classification]["fallback"] += 1
        for reason in meta.get("rejection_reasons", []):
            rejection_counter[str(reason)] += 1

    examples = {
        "accepted_initial": next((row for row in rows if row["narrator_meta"].get("final_source") == "llm_initial"), None),
        "accepted_after_repair": next((row for row in rows if row["narrator_meta"].get("final_source") == "llm_repair"), None),
        "rejected_fallback": next((row for row in rows if row["narrator_meta"].get("final_source") in {"deterministic_fallback", "shadow_fallback"}), None),
        "suspected_over_rejection": next(
            (
                row
                for row in rows
                if "duplicate copy across sections" in [str(x) for x in row["narrator_meta"].get("rejection_reasons", [])]
                and row["narrator_meta"].get("final_source") in {"deterministic_fallback", "shadow_fallback"}
            ),
            None,
        ),
    }

    def _rate(n: int) -> float:
        return round((n / total) * 100.0, 2) if total else 0.0

    return {
        "total_cases": total,
        "provider_called_count": provider_called,
        "initial_attempt_valid_count": initial_valid,
        "initial_attempt_valid_rate_pct": _rate(initial_valid),
        "repair_attempted_count": repair_attempted,
        "repair_valid_count": repair_valid,
        "repair_valid_rate_pct": _rate(repair_valid),
        "final_source_distribution": dict(final_sources),
        "style_profile_distribution": dict(style_profiles),
        "deterministic_fallback_rate_pct": _rate(fallback_count),
        "top_rejection_reasons": rejection_counter.most_common(10),
        "style_repetition_warnings": detect_style_repetition_warnings(accepted_previews),
        "crisis_bypass_count": crisis_bypass,
        "per_classification_acceptance_breakdown": dict(breakdown),
        "examples": examples,
    }


def render_markdown(report: dict[str, Any]) -> str:
    m = report["metrics"]
    lines = [
        "# Presentation Narrator Shadow Eval",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- benchmark_path: `{report['benchmark_path']}`",
        f"- ood_path: `{report['ood_path']}`",
        f"- total_cases: `{m['total_cases']}`",
        f"- provider_called_count: `{m['provider_called_count']}`",
        f"- initial_attempt_valid: `{m['initial_attempt_valid_count']}` ({m['initial_attempt_valid_rate_pct']}%)",
        f"- repair_attempted_count: `{m['repair_attempted_count']}`",
        f"- repair_valid: `{m['repair_valid_count']}` ({m['repair_valid_rate_pct']}%)",
        f"- deterministic_fallback_rate: `{m['deterministic_fallback_rate_pct']}%`",
        f"- crisis_bypass_count: `{m['crisis_bypass_count']}`",
        "",
        "## Final Source Distribution",
    ]
    for key, value in sorted(m["final_source_distribution"].items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Style Profile Distribution"])
    for key, value in sorted(m["style_profile_distribution"].items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Top Rejection Reasons"])
    if not m["top_rejection_reasons"]:
        lines.append("- None")
    else:
        for reason, count in m["top_rejection_reasons"]:
            lines.append(f"- `{reason}`: {count}")
    lines.extend(["", "## Style Repetition Warnings"])
    if not m["style_repetition_warnings"]:
        lines.append("- None")
    else:
        for warning in m["style_repetition_warnings"]:
            lines.append(f"- `{warning['warning']}`: {warning['count']}")
    lines.extend(["", "## Per-Classification Acceptance Breakdown"])
    for cls, row in sorted(m["per_classification_acceptance_breakdown"].items()):
        lines.append(
            f"- `{cls}`: total={row['total']}, accepted_initial={row['accepted_initial']}, accepted_repair={row['accepted_repair']}, fallback={row['fallback']}"
        )
    lines.extend(["", "## Examples"])
    for key, row in m["examples"].items():
        if row is None:
            lines.append(f"- `{key}`: none")
            continue
        lines.append(
            f"- `{key}`: {row['dilemma_id']} ({row['classification']}), final_source={row['narrator_meta'].get('final_source')}"
        )
    preview_rows = [row for row in report["cases"] if isinstance(row.get("accepted_llm_preview"), dict)]
    lines.extend(["", "## Accepted LLM Preview Snippets"])
    if not preview_rows:
        lines.append("- None")
    else:
        for row in preview_rows[:10]:
            preview = row["accepted_llm_preview"]
            lines.append(f"- `{row['dilemma_id']}` ({row['classification']}):")
            for key in ("share_line", "simple.headline", "brutal_truth.punchline", "deep_view.risk", "krishna_lens.question"):
                value = preview.get(key)
                if isinstance(value, str) and value:
                    lines.append(f"  - `{key}`: {value}")
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(report: dict[str, Any], *, out_json: Path, out_md: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")


def run_shadow_eval(
    *,
    benchmark_path: Path = DEFAULT_BENCHMARK_PATH,
    include_ood: bool = True,
    ood_path: Path = DEFAULT_OOD_PATH,
    mock_provider_mode: str = "none",
) -> dict[str, Any]:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_test_settings")
    import django
    from django.test import Client

    django.setup()
    from django.contrib.auth.models import User

    config = load_presentation_llm_config()
    if mock_provider_mode == "none":
        if config.provider not in {"openai_compatible", "anthropic"} or not config.base_url or not config.api_key:
            raise RuntimeError(
                "Provider is not configured for shadow eval. Set PRESENTATION_LLM_PROVIDER to "
                "openai_compatible or anthropic with base URL + API key, or run with --mock-provider-mode."
            )

    from app.semantic import scorer as semantic_scorer_mod

    def _semantic_stub_only(dilemma: str, *, use_stub: bool | None = None) -> dict[str, Any]:
        return semantic_scorer_mod.semantic_scorer(dilemma, use_stub=True)

    cases = _load_benchmark_cases(benchmark_path)
    if include_ood:
        cases.extend(_load_ood_cases(ood_path))

    rows: list[dict[str, Any]] = []
    with (
        _forced_shadow_env(),
        _mock_provider(mock_provider_mode),
        mock.patch("app.engine.analyzer.semantic_scorer", _semantic_stub_only),
    ):
        client = Client()
        eval_user, _created = User.objects.get_or_create(username="presentation-shadow-eval")
        eval_user.set_password("presentation-shadow-eval-pass")
        eval_user.save(update_fields=["password"])
        if not client.login(username="presentation-shadow-eval", password="presentation-shadow-eval-pass"):
            raise RuntimeError("Could not authenticate presentation shadow eval client.")
        for case in cases:
            rows.append(_run_case(client, case))

    report = {
        "eval_version": "presentation-narrator-shadow-eval-v1",
        "generated_at": _iso_now(),
        "benchmark_path": str(benchmark_path),
        "ood_path": str(ood_path) if include_ood else None,
        "shadow_forced": {
            "PRESENTATION_LLM_SHADOW": True,
            "PRESENTATION_LLM_ENABLED": False,
            "PRESENTATION_LLM_REPAIR_ENABLED": True,
        },
        "mock_provider_mode": mock_provider_mode,
        "metrics": _compute_metrics(rows),
        "cases": rows,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run presentation narrator shadow evaluation harness.")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK_PATH)
    parser.add_argument("--ood", type=Path, default=DEFAULT_OOD_PATH)
    parser.add_argument("--include-ood", action="store_true", default=False)
    parser.add_argument("--mock-provider-mode", choices=["none", "always_valid", "repair_success", "always_invalid"], default="none")
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = parser.parse_args()

    report = run_shadow_eval(
        benchmark_path=args.benchmark,
        include_ood=args.include_ood,
        ood_path=args.ood,
        mock_provider_mode=args.mock_provider_mode,
    )
    write_outputs(report, out_json=args.out_json, out_md=args.out_md)
    print(f"Saved JSON report to: {args.out_json}")
    print(f"Saved Markdown report to: {args.out_md}")
    print(
        "Shadow eval summary:"
        f" total={report['metrics']['total_cases']},"
        f" provider_called={report['metrics']['provider_called_count']},"
        f" initial_valid={report['metrics']['initial_attempt_valid_count']},"
        f" repair_valid={report['metrics']['repair_valid_count']}"
    )


if __name__ == "__main__":
    main()
