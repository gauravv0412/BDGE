## ⚠️ SYSTEM BEHAVIOR RULES (HIGH PRIORITY)

You are not a generic coding assistant. You are helping build a production-grade Bhagavad Gita ethical decision engine (Wisdomize v2.1).

### NON-NEGOTIABLE RULES

- Follow `docs/output_schema.json` EXACTLY — no deviation.
- Never add fields not defined in schema.
- Enforce XOR rule strictly:
  - exactly one of `verse_match` or `closest_teaching` must be non-null
  - the other must be explicitly null
- Never hallucinate Bhagavad Gita verses or translations.
- If no verse meets threshold → use `closest_teaching`, not forced verse.

### OUTPUT PHILOSOPHY

- Anti-preachy tone (no “you must”, no moral policing)
- Judge actions, not people
- Krishna-style reasoning = questioning, not commanding
- Maintain sharp, viral clarity (not bland explanations)

### ARCHITECTURE RULES

- Code must be modular and production-grade
- Never combine logic into a single file
- Follow separation strictly:
  - dimensions/
  - verdict/
  - verses/
  - counterfactuals/
  - share/
- Each module must be independently testable

### CODING RULES

- Write clean, explicit Python (no over-abstraction)
- Always explain plan before implementing
- Make minimal changes — do not refactor entire repo unless asked
- Preserve working behavior unless intentionally changing
- Add tests when adding logic

### WORKFLOW RULES

When implementing anything:
1. Read relevant files first
2. Explain plan briefly
3. Implement in small steps
4. Show how to test
5. Ensure schema compliance

### PRODUCT PRIORITY

This is a monetizable AI SaaS system. Optimize for:
- correctness
- modularity
- scalability
- evaluation via benchmarks
- strong differentiation (not generic AI output)

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BDGE implements **Wisdomize v2.1** — a Bhagavad Gita-based ethical decision engine. It analyzes user moral dilemmas across 8 ethical dimensions derived from Gita teachings, producing structured JSON output with verdicts, verse matches, and counterfactuals.

Current state: stub engine with schema validation in place. Real dimension scorers, verse retrieval, and counterfactual generation are not yet implemented.

## Commands

```bash
# Fast tests (excludes Playwright browser tests — default local feedback)
make test-fast
# or: pytest -m "not browser"

# Browser tests only (requires: playwright install chromium)
make test-browser

# Full suite including browser
make test-all

# Smoke: in-process POST /api/v1/analyze (no server)
make smoke

# Run all tests (same as make test-all)
pytest

# Run a single test file
pytest tests/test_schema_validation.py

# Run a single test by name
pytest tests/test_stub_engine.py::test_build_placeholder_response_validates

# Test the stub engine on a sample dilemma (outputs validated JSON)
PYTHONPATH=. python -m app.scripts.run_single_dilemma

# Run benchmark validation over all 20 golden dilemmas
PYTHONPATH=. python -m app.evals.run_benchmarks
PYTHONPATH=. python -m app.evals.run_benchmarks --benchmark docs/benchmarks_v2_batch1_W001-W020.json
```

The virtual environment is at `.venv/`. Tests are discovered automatically via `pytest.ini` (`pythonpath = .`, `testpaths = tests`).

Trusted-user / demo expectations (safety copy, limitations, checklist): **`docs/first_user_readiness.md`**.

## Architecture

### Data flow

```
User dilemma string
  → app/engine/analyzer.py   (analyze_dilemma — top-level entrypoint)
  → app/engine/factory.py    (build_placeholder_response — currently stub)
  → WisdomizeEngineOutput    (Pydantic model, app/core/models.py)
  → validate_against_output_schema()  (JSON Schema draft-07, app/core/validator.py)
  → dict output
```

### Schema enforcement: two layers

1. **Pydantic models** (`app/core/models.py`) — typed construction with field-level constraints
2. **JSON Schema** (`docs/output_schema.json`) — strict draft-07 validation via `app/core/validator.py`

Both are enforced on every output. The schema is the source of truth for the contract.

### Critical schema constraint — XOR on verse

Every output must have **exactly one** of `verse_match` or `closest_teaching` non-null (the other must be `null`). This is enforced via `oneOf` in the JSON schema and tested in `test_schema_validation.py::test_broken_sample_fails_schema`.

Target distribution from the design spec: verse present in ~60% of dilemmas, `closest_teaching` in ~40%.

### Ethical dimensions (8, each scored −5 to +5)

| Field | Concept | Meaning |
|---|---|---|
| `dharma_duty` | Svadharma | Role/responsibility alignment |
| `satya_truth` | Satya | Honesty level |
| `ahimsa_nonharm` | Ahimsa | Harm vs. protection |
| `nishkama_detachment` | Nishkama Karma | Outcome-craving |
| `shaucha_intent` | Shaucha | Motive cleanness |
| `sanyama_restraint` | Indriya-nigraha | Impulse control |
| `lokasangraha_welfare` | Loka-sangraha | Social impact |
| `viveka_discernment` | Viveka | Clarity of judgment |

### Key constraints from the spec

- `confidence` is capped at **0.85** unless all 8 dimensions are scored *and* `missing_facts` is empty
- `alignment_score` range: [−100, +100]
- `reflective_question` must end with `?`
- `verdict_sentence` max 160 chars; `dilemma` 20–600 chars; `dilemma_id` 1–64 chars
- Verse translations must be verbatim from cited sources (Gita Press Gorakhpur for Hindi, Edwin Arnold for English public domain)
- Anti-preachy rule: no "you must" imperatives; judge actions not people

### Golden benchmark data

`docs/benchmarks_v2_batch1_W001-W020.json` — 20 complete golden engine outputs (W001–W020). These are the canonical reference for output quality and schema compliance. Use them when testing real scorer implementations.

### Implementation phases (from design spec)

- **Phase 1**: Core ethics engine — dimension scoring for all 8 dimensions
- **Phase 2**: Verse layer — theme extraction, match scoring (6-point threshold), fallback to `closest_teaching`
- **Phase 3**: Counterfactuals + share layer refinement

### GPU dependencies

`requirements-gpu.txt` pins PyTorch 2.6.0+cu124 (CUDA 12.4) and NVIDIA runtime libs. These are separate from the base `requirements.txt` and intended for future ML-assisted verse matching or semantic scoring.
