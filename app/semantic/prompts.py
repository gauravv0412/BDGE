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
- Set ambiguity_flag=true only when unresolved ambiguity could plausibly flip final class.
- missing_facts can be present even when ambiguity_flag is false.
- reflective_question must end with '?'.
- Do not include verse_match, closest_teaching, alignment_score, classification, or confidence.
""".strip()


def build_user_prompt(dilemma: str) -> str:
    """Render the semantic scorer user prompt for a dilemma string."""
    return USER_PROMPT_TEMPLATE.format(dilemma=dilemma.strip())

