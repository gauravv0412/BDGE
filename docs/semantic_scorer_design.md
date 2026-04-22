# Wisdomize Semantic Scorer — Module Design

Complete design for the first semantic interpretation layer of Wisdomize.

This module is a **single semantic scorer call** in v1. It produces structured semantic analysis for a dilemma, while leaving deterministic verdict computation and curated verse retrieval to downstream modules.

This design is intended to integrate with:
- `docs/design_spec.md`
- `docs/output_schema.json`
- `docs/benchmarks_v2_batch1_W001-W020.json`

---

## Module Boundary

This module should NOT live under `app/dimensions/`, because it emits much more than dimension scores.

It should live under:

```text
app/semantic/
  __init__.py
  scorer.py
  prompts.py
  guards.py
