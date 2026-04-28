"""Deterministic presentation view model for V1.1 visible-output layering.

This module deliberately does not change the public engine schema.  It converts
the existing success envelope into UI-friendly cards with expandable sections.
Copy quality is intentionally conservative; later V1.1 steps can improve prose
without changing the frozen V1 engine response.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ExpandableSection(BaseModel):
    """Tap/expand UI section attached to a presentation card."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str = Field(min_length=1, max_length=120)
    text: str = Field(default="", max_length=1200)
    default_open: bool = False


class PresentationCard(BaseModel):
    """Generic UI card derived from the strict engine response."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str = Field(min_length=1, max_length=120)
    primary_text: str = Field(default="", max_length=1600)
    sections: list[ExpandableSection] = Field(default_factory=list)


class SharePresentationCard(PresentationCard):
    """Share card with explicit copy-refinement marker for V1.1."""

    needs_copy_refinement: bool = True


class ResultPresentationViewModel(BaseModel):
    """Presentation-only card model for a successful engine response."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    presentation_mode: Literal["standard", "crisis_safe"] = "standard"
    verdict_card: PresentationCard
    guidance_card: PresentationCard
    if_you_continue_card: PresentationCard
    counterfactuals_card: PresentationCard
    higher_path_card: PresentationCard
    ethical_dimensions_card: PresentationCard
    share_card: SharePresentationCard
    safety_card: PresentationCard | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


_DIMENSION_MEANINGS: dict[str, str] = {
    "dharma_duty": "Whether the action fits the responsibility in front of you.",
    "satya_truth": "Whether the action stays honest with reality and other people.",
    "ahimsa_nonharm": "Whether the action reduces harm instead of adding to it.",
    "nishkama_detachment": "Whether the action is clean without clinging to outcome or reward.",
    "shaucha_intent": "Whether the motive behind the action is clean.",
    "sanyama_restraint": "Whether the action is guided by restraint rather than impulse.",
    "lokasangraha_welfare": "Whether the action supports the wider good around you.",
    "viveka_discernment": "Whether the action comes from clear judgment rather than confusion.",
}

_CRISIS_TERMS = (
    "self-harm",
    "self harm",
    "suicide",
    "kill myself",
    "end my life",
    "hurt myself",
    "harm myself",
    "better without me",
    "do anything harmful",
)

_SHARE_DOMAIN_ORDER = (
    "integrity_property",
    "workplace_public_correction",
    "livelihood_community_harm",
    "desire_betrayal",
    "family_medical_autonomy",
    "body_insecurity",
    "abuse_boundary",
    "caste_equality",
    "public_review_retaliation",
    "medical_truth_consent",
    "low_information",
    "generic",
)

_SHARE_LIBRARY: dict[str, dict[str, tuple[str, ...]]] = {
    "integrity_property": {
        "quotes": (
            "Need explains pressure. It does not make someone else's loss yours.",
            "Urgency can be real without turning a stranger's wallet into permission.",
            "Pressure asks for relief; character decides the method.",
        ),
        "questions": (
            "What would you do if the owner were standing in front of you?",
            "Which action would still feel clean if the full story became public tomorrow?",
            "Can you solve this pressure without borrowing from someone else's harm?",
        ),
    },
    "workplace_public_correction": {
        "quotes": (
            "Truth needs a clean vehicle, not just a loud room.",
            "Correct the record in a way that keeps both facts and dignity intact.",
            "A sharp fact can land better through a steady channel.",
        ),
        "questions": (
            "What is the smallest correction that protects the truth without turning the room into a trial?",
            "Which channel fixes the record and still protects tomorrow's working trust?",
            "How can you separate accuracy from public escalation in this moment?",
        ),
    },
    "livelihood_community_harm": {
        "quotes": (
            "A legal income can still ask an ethical price.",
            "Profit is clearer when its social cost is named honestly.",
            "Livelihood matters; so does the harm pattern it normalizes nearby.",
        ),
        "questions": (
            "Would this still feel right if you had to explain its harm to the people nearby?",
            "What guardrail would prove you are not outsourcing harm to the neighborhood?",
            "Where is the line between earning and quietly expanding community damage?",
        ),
    },
    "desire_betrayal": {
        "quotes": (
            "Chemistry is not rare enough to be worth becoming untrustworthy.",
            "Desire can be intense without becoming a license to betray trust.",
            "A private thrill is costly when trust is the collateral.",
        ),
        "questions": (
            "Are you protecting love, or just giving desire a noble name?",
            "Which choice leaves you more trustworthy after the feeling cools?",
            "If roles were reversed, what boundary would you call fair?",
        ),
    },
    "family_medical_autonomy": {
        "quotes": (
            "Care is strongest when it protects dignity, not just control.",
            "Love can guide support without erasing another adult's agency.",
            "Protecting life and respecting autonomy can both belong in the same decision.",
        ),
        "questions": (
            "How can you support safety without taking away their final say?",
            "Which step adds clarity and consent before force?",
            "What would respectful care look like if fear were quieter?",
        ),
    },
    "body_insecurity": {
        "quotes": (
            "A body decision is clearer when it is not run by borrowed approval.",
            "Confidence built for spectators rarely lasts in private.",
            "Change can be valid; the motive still needs clean light.",
        ),
        "questions": (
            "Would you still choose this if no one else were watching?",
            "Which part of this choice is yours, and which part is social pressure?",
            "What outcome are you hoping surgery will solve that no procedure can guarantee?",
        ),
    },
    "abuse_boundary": {
        "quotes": (
            "Duty does not require staying available for harm.",
            "A boundary can be compassionate and still be firm.",
            "Distance can be the cleanest form of non-harm when patterns stay abusive.",
        ),
        "questions": (
            "What boundary protects your safety without turning into revenge?",
            "Which contact level is sustainable without reopening harm?",
            "If this pattern continued unchanged, what limit would you set now?",
        ),
    },
    "caste_equality": {
        "quotes": (
            "Love does not become lower because prejudice calls itself tradition.",
            "Inherited hierarchy is not a moral argument against equal dignity.",
            "A family demand is not automatically an ethical claim.",
        ),
        "questions": (
            "Which choice protects dignity without mirroring the same exclusion?",
            "If fear of social fallout disappeared, what would you call just?",
            "How can you defend the relationship while reducing collateral damage?",
        ),
    },
    "public_review_retaliation": {
        "quotes": (
            "A true review can warn people without becoming revenge.",
            "Accuracy protects more people than outrage does.",
            "Public accountability is strongest when facts stay clean and proportionate.",
        ),
        "questions": (
            "What wording informs others without exaggeration you cannot defend?",
            "Are you trying to correct behavior, or to inflict equal pain?",
            "Which facts belong in public, and which belong in a complaint channel?",
        ),
    },
    "medical_truth_consent": {
        "quotes": (
            "Compassion that hides the truth can quietly take away someone's choice.",
            "Hope and honesty do not have to be enemies in care.",
            "In medicine, dignity includes informed consent, not just comfort.",
        ),
        "questions": (
            "How can truth be shared in a way the patient can actually bear and use?",
            "Whose fear is leading this decision: the patient's, or the family's?",
            "What preserves both compassion and the patient's right to choose?",
        ),
    },
    "low_information": {
        "quotes": (
            "When the facts are hidden, certainty should stay humble.",
            "Incomplete context calls for reversible steps, not dramatic conclusions.",
            "Low-information decisions deserve slower confidence.",
        ),
        "questions": (
            "Which missing fact could reverse your decision?",
            "What is the safest reversible step while key details remain unknown?",
            "What would you need to know before calling this final?",
        ),
    },
    "generic": {
        "quotes": (
            "Clarity improves when motive, method, and impact are all named.",
            "A cleaner decision usually survives both urgency and daylight.",
            "The right move is often the one that needs the least narrative repair.",
        ),
        "questions": (
            "Which step is both honest now and defensible later?",
            "What would this choice look like without self-justifying language?",
            "Which action reduces harm without hiding key facts?",
        ),
    },
}

_COUNTERFACTUAL_LIBRARY: dict[str, dict[str, str]] = {
    "integrity_property": {
        "primary": "Two possible paths: one driven by immediate relief, one guided by ownership and restraint.",
        "adharmic_assumed": "I need relief now, so I can treat this wallet as an exception.",
        "adharmic_decision": "Keep the cash while telling yourself returning the ID is enough.",
        "adharmic_why": "The compromise hides inside a partial good action.",
        "dharmic_assumed": "My need is real, but the money still belongs to someone else.",
        "dharmic_decision": "Return the wallet intact and seek rent help without making another person pay for it.",
        "dharmic_why": "You address pressure without training yourself to call theft necessity.",
    },
    "workplace_public_correction": {
        "primary": "Two possible paths: one driven by status recovery, one guided by factual correction and proportion.",
        "adharmic_assumed": "I need to reclaim face now, even if the room turns into combat.",
        "adharmic_decision": "Correct them publicly to win the room back.",
        "adharmic_why": "The fact gets blurred by the spectacle of the correction.",
        "dharmic_assumed": "The record matters, and so does the channel that keeps the correction usable.",
        "dharmic_decision": "Document the facts, ask privately for correction, and escalate only if the pattern continues.",
        "dharmic_why": "You protect truth while reducing avoidable collateral conflict.",
    },
    "livelihood_community_harm": {
        "primary": "Two possible paths: one driven by short-term revenue, one guided by livelihood with social accountability.",
        "adharmic_assumed": "If the business is legal, that should end the ethical question.",
        "adharmic_decision": "Treat legality and family need as enough reason to ignore predictable harm.",
        "adharmic_why": "Legality can hide a cost that still lands on neighbors.",
        "dharmic_assumed": "Family support matters, and the harm footprint still has to count.",
        "dharmic_decision": "Look for income that supports your family without depending on your neighborhood's weakness.",
        "dharmic_why": "You keep provider duty without externalizing the ethical bill.",
    },
    "desire_betrayal": {
        "primary": "Two possible paths: one driven by attraction and secrecy, one guided by trust and boundary.",
        "adharmic_assumed": "This attraction is special enough to suspend ordinary loyalty.",
        "adharmic_decision": "Follow the attraction and rename betrayal as rare chemistry.",
        "adharmic_why": "The story flatters desire while trust carries the damage later.",
        "dharmic_assumed": "Strong feeling does not erase responsibility to people already trusting me.",
        "dharmic_decision": "Create distance, refuse secrecy, and protect the friendship before desire writes the story.",
        "dharmic_why": "You avoid a short thrill that hardens into a long trust debt.",
    },
    "family_medical_autonomy": {
        "primary": "Two possible paths: one driven by fear-based control, one guided by care with autonomy.",
        "adharmic_assumed": "If I force treatment, I am automatically being the better caregiver.",
        "adharmic_decision": "Override their refusal without first building informed, supported consent.",
        "adharmic_why": "Control can look like care while quietly erasing the person's agency.",
        "dharmic_assumed": "Urgency is real, and dignity still includes informed choice.",
        "dharmic_decision": "Clarify risks, involve support, and push for consent-based treatment before coercion.",
        "dharmic_why": "You hold safety and respect together instead of sacrificing one to the other.",
    },
    "body_insecurity": {
        "primary": "Two possible paths: one driven by social comparison, one guided by clear motive and proportion.",
        "adharmic_assumed": "If others approve me more, the decision must be right.",
        "adharmic_decision": "Proceed mainly to reduce insecurity through external validation.",
        "adharmic_why": "A body change cannot reliably solve a status wound.",
        "dharmic_assumed": "Any change should survive private reflection, not just public pressure.",
        "dharmic_decision": "Pause, verify your motive, and proceed only if the choice remains yours after pressure is removed.",
        "dharmic_why": "You reduce regret by aligning action with durable intent.",
    },
    "abuse_boundary": {
        "primary": "Two possible paths: one driven by guilt-compliance, one guided by protective boundary.",
        "adharmic_assumed": "If relatives call it duty, I should keep absorbing harm.",
        "adharmic_decision": "Stay available to harm so relatives can call it duty.",
        "adharmic_why": "Naming harm as duty keeps the harm system alive.",
        "dharmic_assumed": "Safety is part of duty; distance can be clean and non-vindictive.",
        "dharmic_decision": "Set a boundary that protects you without turning the boundary into revenge.",
        "dharmic_why": "You stop the cycle while preserving your own integrity.",
    },
    "caste_equality": {
        "primary": "Two possible paths: one driven by inherited prejudice, one guided by equal dignity and courage.",
        "adharmic_assumed": "Family rank rules should decide who is acceptable to love.",
        "adharmic_decision": "Yield to caste pressure and treat exclusion as moral duty.",
        "adharmic_why": "Tradition language can mask a direct dignity violation.",
        "dharmic_assumed": "Relationship decisions must honor human worth over inherited hierarchy.",
        "dharmic_decision": "Defend the relationship with firm boundaries and non-escalatory communication.",
        "dharmic_why": "You refuse prejudice without copying its dehumanizing style.",
    },
    "public_review_retaliation": {
        "primary": "Two possible paths: one driven by retaliation, one guided by accurate public warning.",
        "adharmic_assumed": "The hurt I felt justifies maximum damage in return.",
        "adharmic_decision": "Write a scathing anonymous post that mixes facts with vengeance.",
        "adharmic_why": "Retaliation framing weakens credibility and fairness.",
        "dharmic_assumed": "People should be warned, but only through verifiable and proportionate facts.",
        "dharmic_decision": "Publish a factual review that warns others without exaggeration or personal attack.",
        "dharmic_why": "You protect public interest without turning truth into revenge.",
    },
    "medical_truth_consent": {
        "primary": "Two possible paths: one driven by fear-shielding, one guided by compassionate disclosure and consent.",
        "adharmic_assumed": "Withholding truth is kinder if the family feels less afraid.",
        "adharmic_decision": "Hide the diagnosis because the family's fear feels kinder in the moment.",
        "adharmic_why": "Temporary comfort can quietly remove the patient's right to choose.",
        "dharmic_assumed": "Care includes truth-sharing with timing, support, and dignity.",
        "dharmic_decision": "Disclose with compassion, pacing, and support while respecting the patient's right to know.",
        "dharmic_why": "You preserve agency without abandoning emotional care.",
    },
    "low_information": {
        "primary": "Two possible paths: one driven by premature certainty, one guided by reversibility and missing-fact discipline.",
        "adharmic_assumed": "I can act decisively now and fill in the missing facts later.",
        "adharmic_decision": "Act fast while key facts stay hidden, then justify the move afterward.",
        "adharmic_why": "Speed without crucial context raises avoidable error and harm risk.",
        "dharmic_assumed": "Confidence should stay provisional while unknowns can still reverse the verdict.",
        "dharmic_decision": "Delay irreversible action until the missing fact that could change the verdict is clear.",
        "dharmic_why": "You preserve options while uncertainty is still decisive.",
    },
    "generic": {
        "primary": "Two possible paths: one driven by impulse and narrative comfort, one guided by clarity and accountable method.",
        "adharmic_assumed": "Immediate relief matters more than method.",
        "adharmic_decision": "Choose the faster move first, then repair the story if challenged.",
        "adharmic_why": "Method drift now becomes a repeated pattern later.",
        "dharmic_assumed": "A durable action should survive both urgency and scrutiny.",
        "dharmic_decision": "Take the smallest accountable step before any irreversible move.",
        "dharmic_why": "You keep flexibility while preserving integrity in process.",
    },
}

_HIGHER_PATH_EXPLAIN_LIBRARY: dict[str, str] = {
    "integrity_property": "Do the clean external action first: return what is not yours. Then solve your pressure without making the owner pay for it.",
    "workplace_public_correction": "Protect the truth with evidence and process before using public confrontation.",
    "livelihood_community_harm": "Do not treat family need and legality as the whole answer. Look for income that does not depend on predictable harm.",
    "desire_betrayal": "Create distance before secrecy turns attraction into betrayal.",
    "family_medical_autonomy": "Care means making sure they understand, not taking control because you are afraid.",
    "body_insecurity": "Slow the decision until you can separate self-care from approval-seeking.",
    "abuse_boundary": "A boundary is cleanest when it protects you without becoming punishment.",
    "caste_equality": "Stand for the relationship without turning your family into enemies.",
    "public_review_retaliation": "Give accurate feedback in a channel meant for correction, not revenge.",
    "medical_truth_consent": "Tell the truth with support, timing, and dignity rather than hiding it for comfort.",
    "low_information": "Do not make an irreversible move while the facts that could change the answer are still hidden.",
    "generic": "Take the clean, reviewable next step before any irreversible action.",
}

_VERDICT_EXPLAIN_LIBRARY: dict[str, str] = {
    "integrity_property": "The pressure is understandable, but the ethical center is ownership. A clean decision does not make someone else absorb your emergency.",
    "workplace_public_correction": "Truth matters here, and the method of correction matters too. The cleaner move protects accuracy without turning the moment into a status fight.",
    "livelihood_community_harm": "Family support is real, but income is not ethically clean just because it is legal. The wider harm pattern still counts.",
    "desire_betrayal": "The attraction may be real, but secrecy would move the cost onto trust that already exists.",
    "family_medical_autonomy": "Care is strongest when it protects safety and dignity together. Fear should not quietly erase another adult's agency.",
    "body_insecurity": "The choice needs a motive check. A body decision becomes clearer when it is not mainly driven by borrowed approval.",
    "abuse_boundary": "Duty does not require staying open to repeated harm. The cleaner question is what boundary protects safety without revenge.",
    "caste_equality": "The ethical issue is dignity under social pressure. Caste status is not a moral reason to reject equal worth.",
    "public_review_retaliation": "Public truth can protect others, but retaliation can distort the method. Accuracy and proportion are the test.",
    "medical_truth_consent": "Compassion cannot remove the patient's right to know. The cleaner path keeps truth and support together.",
    "low_information": "The available facts do not support high certainty. A reversible step is cleaner than acting as if the missing context is irrelevant.",
    "generic": "This is a mixed ethical situation. The cleanest reading comes from testing motive, method, and likely harm before acting.",
}

_VERDICT_APPLIES_LIBRARY: dict[str, str] = {
    "integrity_property": "Because the owner can be identified, the decision is not only about need; it is about whether need becomes permission.",
    "workplace_public_correction": "Because a public correction can protect truth or become escalation, the channel and proportion affect the verdict.",
    "livelihood_community_harm": "Because the benefit lands with your family while predictable harm may land on the neighborhood, both sides need to be counted.",
    "desire_betrayal": "Because existing trust would carry the damage, the feeling itself is less important than the method it invites.",
    "family_medical_autonomy": "Because medical fear can turn support into control, consent and clarity are part of the ethical answer.",
    "body_insecurity": "Because social approval can masquerade as self-care, the verdict depends on whether the motive remains clean in private.",
    "abuse_boundary": "Because the pattern involves harm, preserving contact is not automatically the higher duty.",
    "caste_equality": "Because inherited hierarchy is being used as a decision rule, dignity has to be separated from social fear.",
    "public_review_retaliation": "Because the review could warn others or punish someone, truthfulness and restraint determine the ethical direction.",
    "medical_truth_consent": "Because the hidden information changes the patient's choices, withholding it affects dignity and consent.",
    "low_information": "Because a missing fact could reverse the judgment, confidence should stay humble and the next step should be bounded.",
    "generic": "Because the visible facts point in more than one direction, the verdict should guide the next step without pretending to know everything.",
}

_HIGHER_PATH_WHY_LIBRARY: dict[str, str] = {
    "integrity_property": "This path solves the immediate ethical duty first: restore what belongs to someone else, then address your pressure without transferring harm.",
    "workplace_public_correction": "This path keeps the correction usable by making evidence and channel carry the weight instead of public heat.",
    "livelihood_community_harm": "This path keeps provider duty alive while refusing to make predictable community damage the business model.",
    "desire_betrayal": "This path interrupts secrecy before it becomes a decision you have to defend later.",
    "family_medical_autonomy": "This path creates informed support before force, so care does not become control too quickly.",
    "body_insecurity": "This path slows the decision until the motive is clear enough to survive without audience approval.",
    "abuse_boundary": "This path treats safety as part of duty and keeps the boundary from becoming retaliation.",
    "caste_equality": "This path defends dignity while trying to reduce needless collateral conflict.",
    "public_review_retaliation": "This path warns or corrects through facts that can stand without exaggeration.",
    "medical_truth_consent": "This path gives the patient truth with support, so dignity is not sacrificed for temporary comfort.",
    "low_information": "This path protects reversibility while the facts that could change the answer are still missing.",
    "generic": "This path keeps the next move accountable, proportionate, and easier to review later.",
}

_HIGHER_PATH_PROTECTS_LIBRARY: dict[str, str] = {
    "integrity_property": "Ownership, trust, and your own habit of not turning pressure into entitlement.",
    "workplace_public_correction": "Truth, dignity, and future working trust.",
    "livelihood_community_harm": "Family responsibility without normalizing avoidable harm around you.",
    "desire_betrayal": "Trust, friendship, and the line between feeling and betrayal.",
    "family_medical_autonomy": "Safety, consent, and the person's dignity under medical fear.",
    "body_insecurity": "Agency, clean motive, and protection from regret driven by comparison.",
    "abuse_boundary": "Personal safety, restraint, and freedom from revenge framing.",
    "caste_equality": "Equal dignity, courage, and humane handling of family conflict.",
    "public_review_retaliation": "Public accountability, fairness, and credibility.",
    "medical_truth_consent": "Truth, compassion, and informed choice.",
    "low_information": "Reversibility, humility, and room for new facts to matter.",
    "generic": "Truth, non-harm, and a next step that does not need hidden justification.",
}

_SHORT_TERM_EXPLAIN_LIBRARY: dict[str, str] = {
    "integrity_property": "The relief may be immediate, but the mind starts managing the fact that the owner was knowable.",
    "workplace_public_correction": "The room may feel easier for a moment, but the unresolved truth keeps pressure alive underneath.",
    "livelihood_community_harm": "The income may help quickly, while the harm cost starts landing around the business.",
    "desire_betrayal": "The feeling may get fed quickly, but secrecy starts making trust harder to face.",
    "family_medical_autonomy": "Force may reduce panic for a moment, but it can also make the person feel handled instead of respected.",
    "body_insecurity": "Approval may feel closer for a while, but the insecurity can simply move to a new target.",
    "abuse_boundary": "Staying available may calm family pressure briefly, but it can reopen the pattern you are trying to survive.",
    "caste_equality": "Yielding may reduce family conflict briefly, but it asks dignity to absorb the cost.",
    "public_review_retaliation": "A harsh post may feel satisfying at first, but the extra heat can weaken your credibility.",
    "medical_truth_consent": "Withholding the truth may seem gentler at first, but the patient loses time to choose with clarity.",
    "low_information": "Acting fast may feel decisive, but you will be carrying uncertainty that could have changed the move.",
    "generic": "You may get short-term relief, while the actual ethical tension remains unresolved.",
}

_LONG_TERM_EXPLAIN_LIBRARY: dict[str, str] = {
    "integrity_property": "If this becomes easier to justify, need starts becoming a private permission slip.",
    "workplace_public_correction": "If the pattern repeats, truth becomes something negotiated after status pressure has already won.",
    "livelihood_community_harm": "Over time, the livelihood can become dependent on harm you no longer want to count.",
    "desire_betrayal": "If secrecy becomes normal, the relationship damage outlasts the original attraction.",
    "family_medical_autonomy": "Over time, care can become control if consent keeps getting treated as optional.",
    "body_insecurity": "If approval remains the measure, no single change can finish the insecurity loop.",
    "abuse_boundary": "Without a clean boundary, the old harm can keep recruiting guilt as its messenger.",
    "caste_equality": "If prejudice decides this choice, it becomes easier for inherited hierarchy to decide the next one.",
    "public_review_retaliation": "If outrage becomes the method, even true claims can start sounding unreliable.",
    "medical_truth_consent": "If truth is delayed too long, dignity and informed choice may be impossible to restore.",
    "low_information": "If you keep acting before decisive facts are known, preventable errors become more likely.",
    "generic": "Repeated shortcuts can turn a single pressured choice into a pattern you have to keep defending.",
}


def build_result_view_model(engine_response: dict[str, Any]) -> ResultPresentationViewModel:
    """
    Build a UI presentation model from a strict V1 success envelope or output dict.

    The adapter is pure and deterministic.  It never mutates ``engine_response``,
    never calls an LLM, and never invents verse matches.
    """

    output = _extract_output(engine_response)
    meta = _extract_meta(engine_response)
    safety = _build_safety_card(output)
    if safety is not None:
        return _build_crisis_safe_view_model(output, safety, meta)
    return _build_standard_view_model(output, meta)


def build_card_copy_overlay(
    *,
    output: dict[str, Any],
    deterministic_presentation: dict[str, Any],
    narrator: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build card-specific presentation copy for the browser shell.

    This is intentionally presentation-only. It uses narrator copy when it is
    available and falls back to the deterministic card model without exposing
    debug-style engine labels in normal cards.
    """

    narrator_data = narrator if isinstance(narrator, dict) else {}
    verdict_card = _presentation_card_dict(deterministic_presentation.get("verdict_card"))
    higher_path_card = _presentation_card_dict(deterministic_presentation.get("higher_path_card"))
    if_you_continue_card = _presentation_card_dict(deterministic_presentation.get("if_you_continue_card"))
    share_card = _presentation_card_dict(deterministic_presentation.get("share_card"))

    simple = _dict_value(narrator_data.get("simple"))
    krishna_lens = _dict_value(narrator_data.get("krishna_lens"))
    deep_view = _dict_value(narrator_data.get("deep_view"))
    brutal_truth = _dict_value(narrator_data.get("brutal_truth"))

    raw_values = {
        _text(output.get("dilemma")).lower(),
        _text(output.get("core_reading")).lower(),
        _text(output.get("gita_analysis")).lower(),
    }

    verdict_explain = _first_non_raw(
        raw_values,
        _text(simple.get("explanation")),
        _text(simple.get("headline")),
        _section_text_from_card(verdict_card, "Explain simply"),
    )
    verdict_why = _first_non_raw(
        raw_values,
        _text(krishna_lens.get("teaching")),
        _text(krishna_lens.get("mirror")),
        _section_text_from_card(verdict_card, "Why this verdict applies"),
        _section_text_from_card(verdict_card, "Why this applies to your situation"),
    )

    higher_explain = _first_non_raw(
        raw_values,
        _text(deep_view.get("higher_path")),
        _text(simple.get("next_step")),
        _section_text_from_card(higher_path_card, "Explain simply"),
    )
    higher_why = _first_non_raw(
        raw_values,
        _section_text_from_card(higher_path_card, "Why this path applies"),
        _section_text_from_card(higher_path_card, "Why this applies here"),
        _text(deep_view.get("what_is_happening")),
    )
    higher_protects = _first_non_raw(
        raw_values,
        _section_text_from_card(higher_path_card, "What it is trying to protect"),
        _text(deep_view.get("risk")),
    )

    share_line = _first_non_raw(
        raw_values,
        _text(narrator_data.get("share_line")),
        _text(_dict_value(narrator_data.get("brutal_truth")).get("share_quote")),
        _text(share_card.get("primary_text")),
    )
    reflective_question = _first_question(
        _text(krishna_lens.get("question")),
        _section_text_from_card(share_card, "Reflective question"),
        _text((_dict_value(output.get("share_layer"))).get("reflective_question")),
    )
    consequence_copy = _if_you_continue_overlay(
        output=output,
        if_you_continue_card=if_you_continue_card,
        simple=simple,
        deep_view=deep_view,
        brutal_truth=brutal_truth,
    )

    return {
        "verdict": {
            "explain_simply": verdict_explain,
            "why_this_applies": verdict_why,
        },
        "higher_path": {
            "explain_simply": higher_explain,
            "why_this_applies": higher_why,
            "what_it_is_trying_to_protect": higher_protects,
        },
        "share": {
            "share_line": share_line,
            "reflective_question": reflective_question,
        },
        "if_you_continue": consequence_copy,
        "inner_dynamics": {
            "what_is_happening": _first_non_raw(
                raw_values,
                _text(deep_view.get("what_is_happening")),
                verdict_explain,
            ),
            "risk": _first_non_raw(
                raw_values,
                _text(deep_view.get("risk")),
                higher_protects,
            ),
        },
        "gita_lens": {
            "teaching": _first_non_raw(
                raw_values,
                _text(krishna_lens.get("teaching")),
                _text(krishna_lens.get("mirror")),
            ),
            "question": reflective_question,
        },
    }


def _build_standard_view_model(output: dict[str, Any], meta: dict[str, Any]) -> ResultPresentationViewModel:
    share_domain = _detect_share_domain(output)
    return ResultPresentationViewModel(
        presentation_mode="standard",
        verdict_card=_build_verdict_card(output),
        guidance_card=_build_guidance_card(output),
        if_you_continue_card=_build_if_you_continue_card(output),
        counterfactuals_card=_build_counterfactuals_card(output, domain=share_domain),
        higher_path_card=_build_higher_path_card(output),
        ethical_dimensions_card=_build_ethical_dimensions_card(output),
        share_card=_build_share_card(output, share_domain=share_domain),
        safety_card=None,
        meta=_base_meta("standard", meta, share_domain=share_domain),
    )


def _base_meta(
    presentation_mode: str,
    engine_meta: dict[str, Any],
    *,
    share_domain: str | None = None,
) -> dict[str, Any]:
    return {
        **engine_meta,
        "source": "v1_engine_response",
        "presentation_version": "v1.1-adapter",
        "public_schema_changed": False,
        "presentation_mode": presentation_mode,
        "share_domain": share_domain,
    }


def _build_crisis_safe_view_model(
    output: dict[str, Any],
    safety: PresentationCard,
    meta: dict[str, Any],
) -> ResultPresentationViewModel:
    return ResultPresentationViewModel(
        presentation_mode="crisis_safe",
        verdict_card=_build_crisis_verdict_card(output),
        guidance_card=_build_crisis_guidance_card(),
        if_you_continue_card=_build_crisis_if_you_continue_card(),
        counterfactuals_card=_build_crisis_counterfactuals_placeholder(),
        higher_path_card=_build_crisis_immediate_next_step_card(),
        ethical_dimensions_card=_build_crisis_ethical_dimensions_placeholder(),
        share_card=_build_crisis_suppressed_share_card(),
        safety_card=safety,
        meta=_base_meta("crisis_safe", meta, share_domain=None),
    )


def _extract_output(engine_response: dict[str, Any]) -> dict[str, Any]:
    candidate = engine_response.get("output", engine_response)
    return candidate if isinstance(candidate, dict) else {}


def _extract_meta(engine_response: dict[str, Any]) -> dict[str, Any]:
    meta = engine_response.get("meta")
    return dict(meta) if isinstance(meta, dict) else {}


def _build_verdict_card(output: dict[str, Any]) -> PresentationCard:
    verdict = _text(output.get("verdict_sentence"))
    classification = _text(output.get("classification"))
    domain = _detect_share_domain(output)

    sections = [
        _section(
            "Explain simply",
            _verdict_simple_explanation(domain=domain, classification=classification),
        ),
        _section("Why this verdict applies", _verdict_why_applies(domain=domain, classification=classification)),
    ]
    return PresentationCard(title="Verdict", primary_text=verdict, sections=sections)


def _build_guidance_card(output: dict[str, Any]) -> PresentationCard:
    verse = output.get("verse_match")
    closest = _text(output.get("closest_teaching"))
    gita = _text(output.get("gita_analysis"))
    domain = _detect_share_domain(output)

    if isinstance(verse, dict):
        why = _text(verse.get("why_it_applies"))
        english = _text(verse.get("english_translation"))
        hindi = _text(verse.get("hindi_translation"))
        verse_ref = _text(verse.get("verse_ref"))
        dilemma = _text(output.get("dilemma"))
        core = _text(output.get("core_reading"))
        anchor_text = "\n".join(
            part
            for part in [
                f"Verse: {verse_ref}" if verse_ref else "",
                f"English: {english}" if english else "",
                f"Hindi: {hindi}" if hindi else "",
            ]
            if part
        )
        primary = _sanitize_guidance_copy(_first_non_empty(why, english))
        return PresentationCard(
            title="Gita Verse",
            primary_text=primary,
            sections=[
                _section(
                    "Explain simply",
                    _guidance_simple_explanation_from_verse(
                        verse_ref=verse_ref,
                        domain=domain,
                        dilemma=dilemma,
                        core=core,
                        gita=gita,
                        primary=primary,
                    ),
                ),
                _section("Show Gita anchor", anchor_text),
            ],
        )

    if not closest:
        return PresentationCard(
            title="Guidance",
            primary_text="No verse or closest teaching is currently available for this response.",
            sections=[
                _section("Explain simply", _first_non_empty(gita, "No additional guidance is attached to this response.")),
            ],
        )

    lens_text = _humanize_closest_teaching_text(closest)
    provisional_text = (
        "This is not a direct verse verdict. The situation needs judgment beyond a single quote."
    )
    return PresentationCard(
        title="Closest Gita Lens",
        primary_text=(
            f"Closest lens: {lens_text}. Use this as a lens, not a command."
        ),
        sections=[
            _section(
                "Explain simply",
                _guidance_simple_explanation_from_closest(
                    primary=f"Closest lens: {lens_text}. Use this as a lens, not a command.",
                    gita=gita,
                    lens_text=lens_text,
                ),
            ),
            _section(
                "Why this stays provisional",
                provisional_text,
            ),
            *_closest_direction_sections(closest),
        ],
    )


def _build_if_you_continue_card(output: dict[str, Any]) -> PresentationCard:
    block = output.get("if_you_continue")
    data = block if isinstance(block, dict) else {}
    short = _text(data.get("short_term"))
    long = _text(data.get("long_term"))
    domain = _detect_share_domain(output)

    primary = "\n".join(part for part in [f"Short-term: {short}" if short else "", f"Long-term: {long}" if long else ""] if part)
    return PresentationCard(
        title="If You Continue",
        primary_text=primary,
        sections=[
            _section("What happens soon", short),
            _section("What this means", _consequence_explanation(output=output, term="short")),
            _section("What it can become", _consequence_explanation(output=output, term="long")),
            _section("Why this applies here", _VERDICT_APPLIES_LIBRARY.get(domain, _VERDICT_APPLIES_LIBRARY["generic"])),
        ],
    )


def _build_counterfactuals_card(output: dict[str, Any], *, domain: str) -> PresentationCard:
    cf = _COUNTERFACTUAL_LIBRARY.get(domain, _COUNTERFACTUAL_LIBRARY["generic"])
    sections = [
        _section("Adharmic assumed inner state", cf["adharmic_assumed"]),
        _section("Adharmic likely decision", cf["adharmic_decision"]),
        _section("Adharmic - Why this matters", cf["adharmic_why"]),
        _section("Dharmic assumed inner state", cf["dharmic_assumed"]),
        _section("Dharmic likely decision", cf["dharmic_decision"]),
        _section("Dharmic - Why this matters", cf["dharmic_why"]),
    ]
    return PresentationCard(
        title="Counterfactuals",
        primary_text=cf["primary"],
        sections=sections,
    )


def _build_higher_path_card(output: dict[str, Any]) -> PresentationCard:
    higher_path = _text(output.get("higher_path"))
    domain = _detect_share_domain(output)
    return PresentationCard(
        title="Higher Path",
        primary_text=higher_path,
        sections=[
            _section("Explain simply", _higher_path_simple_explanation(domain=domain, primary=higher_path)),
            _section("Why this path applies", _higher_path_why_applies(domain=domain)),
            _section("What it is trying to protect", _higher_path_protects(domain=domain)),
        ],
    )


def _build_ethical_dimensions_card(output: dict[str, Any]) -> PresentationCard:
    dimensions = output.get("ethical_dimensions")
    data = dimensions if isinstance(dimensions, dict) else {}
    sections: list[ExpandableSection] = []
    for key, raw_value in data.items():
        value = raw_value if isinstance(raw_value, dict) else {}
        score = value.get("score")
        note = _text(value.get("note"))
        meaning = _DIMENSION_MEANINGS.get(str(key), "Plain-language meaning is not defined yet for this dimension.")
        text = "\n".join(
            part
            for part in [
                f"Score: {score}" if score is not None else "",
                f"Simple meaning: {meaning}",
                f"Context-specific reason: {note}" if note else "",
            ]
            if part
        )
        sections.append(_section(str(key), text, default_open=True))

    classification = _text(output.get("classification"))
    score = output.get("alignment_score")
    primary = f"{classification} ({score})" if classification and score is not None else classification
    return PresentationCard(title="Ethical Dimensions", primary_text=primary, sections=sections)


def _build_share_card(output: dict[str, Any], *, share_domain: str) -> SharePresentationCard:
    quote, question = _share_quote_and_question(output, share_domain=share_domain)
    return SharePresentationCard(
        title="Shareable Insight",
        primary_text=quote,
        sections=[
            _section("Reflective question", question),
        ],
        needs_copy_refinement=False,
    )


def _build_crisis_verdict_card(output: dict[str, Any]) -> PresentationCard:
    verdict = _text(output.get("verdict_sentence"))
    return PresentationCard(
        title="Verdict",
        primary_text=verdict,
        sections=[
            _section(
                "Explain simply",
                "Pausing to reach out is a signal of care for yourself, not a final judgment of your character.",
            ),
        ],
    )


def _build_crisis_guidance_card() -> PresentationCard:
    return PresentationCard(
        title="Support first",
        primary_text=(
            "Right now, the priority is safety and human connection—not a detailed moral score of your thoughts."
        ),
        sections=[
            _section(
                "Explain simply",
                "If you are afraid you might hurt yourself, please reach out to someone who can be with you in real time.",
            ),
        ],
    )


def _build_crisis_if_you_continue_card() -> PresentationCard:
    short = (
        "In the near term, focus on being physically safe: stay with someone you trust, "
        "or contact local crisis or emergency support if you might act on these thoughts."
    )
    long = "Over time, steady support can make intense pain feel less absolute. You do not have to plan the rest of your life in this hour."
    primary = f"Short-term: {short}\nLong-term: {long}"
    return PresentationCard(
        title="If You Continue",
        primary_text=primary,
        sections=[
            _section("Short-term - Explain simply", short),
            _section("Long-term - Explain simply", long),
            _section(
                "What helps now",
                "A small, concrete next step is enough: one message, one call, or one visit to a safe place.",
            ),
        ],
    )


def _build_crisis_counterfactuals_placeholder() -> PresentationCard:
    return PresentationCard(
        title="Counterfactuals",
        primary_text="Alternative storylines are not shown in this safety-focused view.",
        sections=[
            _section(
                "Explain simply",
                "Comparing paths is de-emphasized so the page does not ask you to rehearse a crisis as a thought experiment. The focus is your immediate safety.",
            ),
        ],
    )


def _build_crisis_immediate_next_step_card() -> PresentationCard:
    return PresentationCard(
        title="Immediate Next Step",
        primary_text=(
            "Before interpreting this as a moral decision, treat it as a safety moment. "
            "Please contact someone who can stay with you or help you right now."
        ),
        sections=[
            _section(
                "Explain simply",
                "This is not the moment to judge yourself. The cleanest next step is to create distance from harm and involve a real person immediately.",
            ),
            _section(
                "What to do now",
                "Move away from anything you could use to hurt yourself, contact a trusted person, and use local emergency or crisis support if you might act on these thoughts.",
            ),
        ],
    )


def _build_crisis_ethical_dimensions_placeholder() -> PresentationCard:
    return PresentationCard(
        title="Ethical Dimensions",
        primary_text="Dimension scores and detailed reasons are not shown in this safety-focused view.",
        sections=[],
    )


def _build_crisis_suppressed_share_card() -> SharePresentationCard:
    return SharePresentationCard(
        title="Shareable Insight",
        primary_text="",
        sections=[],
        needs_copy_refinement=False,
    )


def _build_safety_card(output: dict[str, Any]) -> PresentationCard | None:
    haystack = " ".join(
        _text(value)
        for value in [
            output.get("dilemma"),
            output.get("verdict_sentence"),
            output.get("core_reading"),
            output.get("gita_analysis"),
            output.get("higher_path"),
        ]
    ).lower()
    if not any(term in haystack for term in _CRISIS_TERMS):
        return None
    return PresentationCard(
        title="Safety Note",
        primary_text="This may need immediate human support, not only ethical reflection.",
        sections=[
            _section(
                "Explain simply",
                "If this situation involves self-harm, acute crisis, or immediate danger, qualified human support should come before product guidance.",
                default_open=True,
            )
        ],
    )


def _counterfactual_block(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        "assumed_context": _text(value.get("assumed_context")),
        "decision": _text(value.get("decision")),
        "why": _text(value.get("why")),
    }


def _closest_direction_sections(closest: str) -> list[ExpandableSection]:
    chapter_match = _extract_chapter_hint(closest)
    if chapter_match is None:
        return []
    chapter_num, chapter_title = chapter_match
    label = f"Related direction: Chapter {chapter_num} themes"
    suffix = f" of {chapter_title}" if chapter_title else ""
    return [
        _section(
            "Gita direction",
            f"{label}{suffix}. Use these themes for orientation, not as a direct verse verdict.",
        )
    ]


def _extract_chapter_hint(text: str) -> tuple[str, str] | None:
    if not text:
        return None
    match = re.search(r"\bchapter\s+(\d{1,2})(?:\s*[:\-]\s*([A-Za-z ]{2,60}))?", text, flags=re.IGNORECASE)
    if not match:
        return None
    chapter_num = match.group(1)
    chapter_title = (match.group(2) or "").strip()
    return chapter_num, chapter_title


def _guidance_simple_explanation_from_verse(
    *,
    verse_ref: str,
    domain: str,
    dilemma: str,
    core: str,
    gita: str,
    primary: str,
) -> str:
    # NOTE: Bespoke verse text is intentionally limited to a few frequently smoke-tested
    # verse refs. For all other refs we use domain/fallback guidance below.
    # Future additions should avoid dilemma-specific phrasing unless verse+domain pairing
    # is stable across many cases.
    verse_map = {
        "6.5": (
            "This verse says your next action either strengthens you or weakens you. "
            "Choosing the clean action under pressure protects the kind of person you become."
        ),
        "18.47": (
            "This verse is not saying every legal job is clean. "
            "It asks whether the work itself fits a responsible way of living."
        ),
        "5.18": (
            "This verse cuts through status labels. "
            "It supports seeing a person's dignity beyond caste identity."
        ),
        "16.1-3": (
            "This verse joins truth with compassion. "
            "The point is not to be blunt, but not to hide what the patient has a right to know."
        ),
    }
    by_domain = {
        "integrity_property": (
            "This verse asks you to train action under pressure. "
            "Returning the wallet intact keeps your hardship from becoming someone else's loss."
        ),
        "livelihood_community_harm": (
            "This verse asks whether your path stays clean in method, not just legal in form. "
            "If income depends on predictable harm nearby, the method needs review."
        ),
        "caste_equality": (
            "This verse asks you to look past social rank and see equal dignity first. "
            "That framing does not support caste-based rejection."
        ),
        "medical_truth_consent": (
            "This verse supports truthful care with compassion. "
            "Do not hide life-changing facts from the person whose decision it is."
        ),
        "low_information": (
            "This verse points to disciplined action, not rushed certainty. "
            "Take a reversible step until the missing fact is clearer."
        ),
    }
    chosen = verse_map.get(verse_ref) or by_domain.get(domain) or _first_non_empty(
        gita,
        core,
        dilemma,
        "Take the next clean action without hiding key facts.",
    )
    cleaned = _sanitize_guidance_copy(chosen)
    if cleaned.strip().lower() == primary.strip().lower():
        cleaned = "This guidance asks for a cleaner next step that stays honest under pressure."
    return cleaned


def _guidance_simple_explanation_from_closest(*, primary: str, gita: str, lens_text: str) -> str:
    fallback = f"{lens_text}. Use this to test motive, method, and likely impact before acting."
    text = _sanitize_guidance_copy(_first_non_empty(gita, fallback))
    if text.strip().lower() == primary.strip().lower():
        text = "Use this lens to check whether your method stays honest, proportionate, and clean in context."
    return text


def _verdict_simple_explanation(*, domain: str, classification: str) -> str:
    text = _VERDICT_EXPLAIN_LIBRARY.get(domain, _VERDICT_EXPLAIN_LIBRARY["generic"])
    if classification and domain == "generic":
        return (
            f"This appears {classification.lower()} from the visible facts. "
            "Use the verdict as a direction check while any missing context is clarified."
        )
    return text


def _verdict_why_applies(*, domain: str, classification: str) -> str:
    text = _VERDICT_APPLIES_LIBRARY.get(domain, _VERDICT_APPLIES_LIBRARY["generic"])
    if classification and domain == "generic":
        return (
            f"The classification is {classification.lower()} because motive, method, and impact do not all point cleanly in one direction."
        )
    return text


def _higher_path_simple_explanation(*, domain: str, primary: str) -> str:
    text = _HIGHER_PATH_EXPLAIN_LIBRARY.get(domain, _HIGHER_PATH_EXPLAIN_LIBRARY["generic"])
    if text.strip().lower() == primary.strip().lower():
        return "Convert the direction into one concrete step you can do now without hidden cost."
    return text


def _higher_path_why_applies(*, domain: str) -> str:
    return _HIGHER_PATH_WHY_LIBRARY.get(domain, _HIGHER_PATH_WHY_LIBRARY["generic"])


def _higher_path_protects(*, domain: str) -> str:
    return _HIGHER_PATH_PROTECTS_LIBRARY.get(domain, _HIGHER_PATH_PROTECTS_LIBRARY["generic"])


def _if_you_continue_overlay(
    *,
    output: dict[str, Any],
    if_you_continue_card: dict[str, Any],
    simple: dict[str, Any],
    deep_view: dict[str, Any],
    brutal_truth: dict[str, Any],
) -> dict[str, Any]:
    block = output.get("if_you_continue")
    data = block if isinstance(block, dict) else {}
    short = _clean_consequence(_text(data.get("short_term")))
    long = _clean_consequence(_text(data.get("long_term")))
    raw_values = {short.lower(), long.lower()}
    short_explain = _first_non_raw(
        raw_values,
        _text(simple.get("explanation")),
        _section_text_from_card(if_you_continue_card, "What this means"),
        _consequence_explanation(output=output, term="short"),
    )
    long_explain = _first_non_raw(
        raw_values,
        _text(deep_view.get("risk")),
        _text(brutal_truth.get("punchline")),
        _section_text_from_card(if_you_continue_card, "What it can become"),
        _consequence_explanation(output=output, term="long"),
    )
    if not short_explain or short_explain.strip().lower() == short.lower():
        short_explain = _consequence_explanation(output=output, term="short")
    if not long_explain or long_explain.strip().lower() == long.lower():
        long_explain = _consequence_explanation(output=output, term="long")
    why = _first_non_empty(
        _section_text_from_card(if_you_continue_card, "Why this applies here"),
        _VERDICT_APPLIES_LIBRARY.get(_detect_share_domain(output), _VERDICT_APPLIES_LIBRARY["generic"]),
    )
    return {
        "short_term": {
            "consequence": short,
            "explain_simply": short_explain,
        },
        "long_term": {
            "consequence": long,
            "explain_simply": long_explain,
        },
        "why_this_applies": why,
    }


def _clean_consequence(value: str) -> str:
    return " ".join(value.split())


def _consequence_explanation(*, output: dict[str, Any], term: str) -> str:
    domain = _detect_share_domain(output)
    if term == "short":
        return _SHORT_TERM_EXPLAIN_LIBRARY.get(domain, _SHORT_TERM_EXPLAIN_LIBRARY["generic"])
    return _LONG_TERM_EXPLAIN_LIBRARY.get(domain, _LONG_TERM_EXPLAIN_LIBRARY["generic"])


def _humanize_closest_teaching_text(text: str) -> str:
    if not text:
        return "Pause, clarify intention, and choose the cleanest next action."
    forbidden = ("engine", "threshold", "fallback", "verse_match", "selected", "retrieval", "schema")
    normalized = " ".join(text.split())
    sentences = [s.strip(" .") for s in re.split(r"[.?!]+", normalized) if s.strip()]
    kept = [s for s in sentences if not any(word in s.lower() for word in forbidden)]
    if not kept:
        return "Pause, clarify intention, and choose the cleanest next action."
    concise = ". ".join(kept).strip()
    return concise.rstrip(".")


def _sanitize_guidance_copy(text: str) -> str:
    if not text:
        return ""
    cleaned = " ".join(text.split())
    forbidden_patterns = [
        (r"\bdominant ethical pull\b", "main pressure"),
        (r"\btheme tags?\b", "context notes"),
        (r"\bthemes?\b", "direction"),
        (r"\bapplies\b", "fits"),
        (r"\bsignals?\s+like\b", "details like"),
        (r"\bsignals?\b", "details"),
        (r"\bclassifier\b", ""),
        (r"\bmetadata\b", "context"),
        (r"\bverse_match\b", "verse"),
        (r"\bretrieval\b", "lookup"),
    ]
    for pattern, replacement in forbidden_patterns:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    hard_forbidden = ("engine", "threshold", "fallback", "schema")
    for word in hard_forbidden:
        cleaned = re.sub(rf"\b{word}\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
    return cleaned.strip()


def _share_quote_and_question(output: dict[str, Any], *, share_domain: str) -> tuple[str, str]:
    pack = _SHARE_LIBRARY.get(share_domain, _SHARE_LIBRARY["generic"])
    seed = _stable_seed(
        _text(output.get("dilemma")),
        _text(output.get("classification")),
        _text(output.get("verdict_sentence")),
        _text(output.get("core_reading")),
        _text(output.get("higher_path")),
        share_domain,
    )
    quote = _pick_by_seed(pack["quotes"], seed, limit=160)
    question = _pick_by_seed(pack["questions"], seed + 7, limit=220)
    if not question.endswith("?"):
        question = question.rstrip(".") + "?"
    return quote, question


def _detect_share_domain(output: dict[str, Any]) -> str:
    dilemma_text = _text(output.get("dilemma")).lower()
    # Pass 1: prioritize dilemma-only high-confidence signals to avoid contamination
    # from stub/generated fields in core_reading/higher_path/internal_driver.
    dilemma_checks: list[tuple[str, tuple[str, ...]]] = [
        ("low_information", ("cannot share many details", "can't share many details", "few details", "vague", "missing details", "missing facts", "do the thing soon")),
        ("integrity_property", ("found a wallet", "wallet", "cash and an id", "keep the cash", "lost property", "owner id")),
        ("workplace_public_correction", ("manager took credit", "public meeting", "correcting the record", "workplace credit")),
        ("public_review_retaliation", ("anonymous review", "scathing review", "bad review", "damage reputation", "restaurant review")),
        ("livelihood_community_harm", ("alcohol shop", "liquor shop", "legal shop", "neighborhood harm", "addiction", "support my family", "livelihood")),
        ("desire_betrayal", ("friend's partner", "close friend's partner", "desire", "attraction", "betray friend")),
        ("family_medical_autonomy", ("aging parent", "refuses hospitalization", "forcing treatment", "serious diagnosis", "autonomy")),
        ("body_insecurity", ("cosmetic surgery", "appearance", "insecure", "social approval", "beauty", "body", "looks")),
        ("abuse_boundary", ("abusive parent", "abuse", "no contact", "relatives say duty", "family pressure after abuse", "boundary")),
        ("caste_equality", ("caste", "marry someone", "family rejects", "cut ties")),
        ("medical_truth_consent", ("doctor", "patient", "terminal diagnosis", "hide it from patient", "family asks me to hide")),
    ]
    for domain, terms in dilemma_checks:
        if any(term in dilemma_text for term in terms):
            return domain

    # Pass 2: broader context for unresolved/ambiguous cases only.
    haystack = " ".join(
        [
            dilemma_text,
            _text(output.get("verdict_sentence")).lower(),
            _text(output.get("core_reading")).lower(),
            _text((output.get("internal_driver") or {}).get("primary") if isinstance(output.get("internal_driver"), dict) else ""),
            _text((output.get("internal_driver") or {}).get("hidden_risk") if isinstance(output.get("internal_driver"), dict) else ""),
            _text(output.get("higher_path")).lower(),
        ]
    )
    checks: list[tuple[str, tuple[str, ...]]] = [
        ("low_information", ("cannot share", "can't share", "few details", "few detail", "vague", "missing fact", "missing facts")),
        ("integrity_property", ("wallet", "cash", "found", "lost", "property", "owner")),
        ("workplace_public_correction", ("manager", "credit", "meeting", "publicly", "workplace", "record")),
        ("public_review_retaliation", ("anonymous", "review", "restaurant", "business reputation", "scathing")),
        ("livelihood_community_harm", ("alcohol shop", "liquor", "neighborhood", "community harm", "livelihood")),
        ("desire_betrayal", ("friend's partner", "friend", "betray", "desire", "attracted", "interested too")),
        ("family_medical_autonomy", ("aging parent", "hospitalization", "forcing treatment", "respecting them", "refusing hospitalization")),
        ("body_insecurity", ("cosmetic surgery", "insecure", "social approval", "appearance", "body")),
        ("abuse_boundary", ("abusive", "no contact", "boundary", "relatives", "duty to stay connected")),
        ("caste_equality", ("caste", "marry", "family rejects", "cut ties")),
        ("medical_truth_consent", ("doctor", "terminal diagnosis", "hide it", "patient", "family asks")),
    ]
    for domain, terms in checks:
        if any(term in haystack for term in terms):
            return domain
    return "generic"


def _stable_seed(*parts: str) -> int:
    joined = "|".join(part.strip().lower() for part in parts if part)
    return sum(ord(ch) for ch in joined)


def _pick_by_seed(options: tuple[str, ...], seed: int, *, limit: int) -> str:
    if not options:
        return ""
    value = options[seed % len(options)].strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _section(label: str, text: str, *, default_open: bool = False) -> ExpandableSection:
    return ExpandableSection(label=label, text=text, default_open=default_open)


def _presentation_card_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _section_text_from_card(card: dict[str, Any], label: str) -> str:
    sections = card.get("sections")
    if not isinstance(sections, list):
        return ""
    for section in sections:
        if isinstance(section, dict) and _text(section.get("label")) == label:
            return _text(section.get("text"))
    return ""


def _first_non_raw(raw_values: set[str], *values: str) -> str:
    for value in values:
        candidate = value.strip()
        if not candidate:
            continue
        if candidate.lower() in raw_values:
            continue
        return candidate
    return ""


def _first_question(*values: str) -> str:
    for value in values:
        candidate = value.strip()
        if not candidate:
            continue
        if not candidate.endswith("?"):
            candidate = candidate.rstrip(".") + "?"
        return candidate
    return "What choice stays clean after the pressure fades?"


def _first_non_empty(*values: str) -> str:
    for value in values:
        if value.strip():
            return value
    return ""


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()
