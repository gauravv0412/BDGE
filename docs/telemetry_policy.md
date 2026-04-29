# Safe Telemetry Policy

Wisdomize feedback capture is intentionally narrow. It exists to learn whether a rendered result was useful, not to build a hidden user history or collect raw moral dilemmas.

## What We Do Not Store By Default

- Raw dilemma text is not stored in feedback records.
- Full engine responses are not stored in feedback records.
- Provider prompts, provider responses, repair attempts, and narrator internals are not stored in feedback records.
- Request IDs are not exposed to users in the UI.
- Verse metadata, retrieval scores, curated data, semantic scorer inputs, and context extractor output are not modified by feedback.

## What Feedback May Store

Feedback records may store only small allowlisted fields:

- result identifier, usually `dilemma_id`
- usefulness signal: `up`, `down`, or empty
- verse or teaching relevance signal: `up`, `down`, or empty
- allowlisted product tags
- optional short user comment
- coarse route flag, currently `presentation`
- optional client theme: `light` or `dark`

Comments are user-submitted text and should be treated as potentially sensitive. They should not be copied into prompts, logs, demos, or evaluation datasets without an explicit review step.

## Safety Boundaries

Crisis-safe interactions should avoid spiritual, viral, or share-oriented feedback framing. If feedback is shown for a crisis-safe result, it should use neutral helpfulness language only.

Future account-linked feedback, history, admin dashboards, payments, or analytics integrations must be explicitly planned before implementation. They should not be added by expanding this lightweight endpoint.
