"""
Prompt templates for the semantic scorer call.
"""

from __future__ import annotations

SYSTEM_PROMPT = """
You are Wisdomize semantic scorer.
Return only JSON that matches the provided semantic scorer schema.
Do not output canonical verse text, verse references, or fabricated scripture.
Use an observational, anti-preachy tone.
"""

USER_PROMPT_TEMPLATE = """
Analyze the following dilemma and return a JSON object that matches the semantic scorer schema.

Dilemma:
{dilemma}

Requirements:
- Score all 8 ethical dimensions with integer scores in [-5, 5] and concise notes.
- ethical_dimensions must be an OBJECT (dictionary), never a list.
- ethical_dimensions must use ONLY these exact keys:
  dharma_duty, satya_truth, ahimsa_nonharm, nishkama_detachment,
  shaucha_intent, sanyama_restraint, lokasangraha_welfare, viveka_discernment.
- Do not invent alternate moral dimensions or alternate dimension names.
- ambiguity_flag guidance:
  - Set ambiguity_flag=true only when unresolved facts could plausibly flip the final class.
  - missing_facts can refine recommendation while ambiguity_flag=false when class would likely stay the same.
  - Do not set ambiguity_flag=true just because many facts are missing.
  - Positive example (set ambiguity_flag=true): "Should I quit to follow my calling?"
    If runway, spouse alignment, and minimum viability are unknown, plausible answers can flip class.
  - Positive example (set ambiguity_flag=true): "Should I cut contact with an abusive parent?"
    If severity/currentness, safe alternatives, and safety obligations are unknown, class can flip.
  - Positive example (set ambiguity_flag=true): close friend cheating where your spouse is also that friend.
    Health risk, solicited involvement, and role proximity can flip class.
  - Negative example (keep ambiguity_flag=false): inter-caste marriage where parental disapproval is high.
    Motive quality may refine advice, but parental disapproval alone does not make class ambiguous.
  - Negative example (keep ambiguity_flag=false): terminal diagnosis disclosure by a doctor.
    Missing facts can refine disclosure method, not whether patient autonomy matters.
  - Negative example (keep ambiguity_flag=false): elective cosmetic surgery for an adult.
    Motive questions exist, but not every body-autonomy case is class-flipping.
  - Negative example (keep ambiguity_flag=false): competent adult parent refuses treatment.
    Missing facts may refine care planning, but explicit refusal should not default to ambiguity_flag=true.
  - Negative example (keep ambiguity_flag=false): apparently competent adult explicitly refusing treatment.
    Missing facts may refine care planning; do not default this to ambiguity_flag=true.
  - Negative example (keep ambiguity_flag=false): whistleblowing on serious pollution with strong
    evidence and clear harm. Many missing facts may refine tactics, but class itself may stay stable.
- reflective_question must be nested inside share_layer and must end with '?'.
- All required top-level fields must be present:
  verdict_sentence, ethical_dimensions, internal_driver, core_reading, gita_analysis, higher_path,
  missing_facts, ambiguity_flag, if_you_continue, counterfactuals, share_layer.
- verdict_sentence must be one declarative top-line judgment (<=160 chars), anti-preachy,
  and not a label-only phrase.
- Do not include verse_match, closest_teaching, alignment_score, classification, or confidence.

Compact JSON shape (field names must match exactly):
{{
  "verdict_sentence": "...",
  "ethical_dimensions": {{
    "dharma_duty": {{"score": 0, "note": "..."}},
    "satya_truth": {{"score": 0, "note": "..."}},
    "ahimsa_nonharm": {{"score": 0, "note": "..."}},
    "nishkama_detachment": {{"score": 0, "note": "..."}},
    "shaucha_intent": {{"score": 0, "note": "..."}},
    "sanyama_restraint": {{"score": 0, "note": "..."}},
    "lokasangraha_welfare": {{"score": 0, "note": "..."}},
    "viveka_discernment": {{"score": 0, "note": "..."}}
  }},
  "internal_driver": {{"primary": "...", "hidden_risk": "..."}},
  "core_reading": "...",
  "gita_analysis": "...",
  "higher_path": "...",
  "missing_facts": [],
  "ambiguity_flag": false,
  "if_you_continue": {{"short_term": "...", "long_term": "..."}},
  "counterfactuals": {{
    "clearly_adharmic_version": {{"assumed_context": "...", "decision": "...", "why": "..."}},
    "clearly_dharmic_version": {{"assumed_context": "...", "decision": "...", "why": "..."}}
  }},
  "share_layer": {{
    "anonymous_share_title": "...",
    "card_quote": "...",
    "reflective_question": "..."
  }}
}}
""".strip()


def build_user_prompt(dilemma: str) -> str:
    """Render the semantic scorer user prompt for a dilemma string."""
    return USER_PROMPT_TEMPLATE.format(dilemma=dilemma.strip())

