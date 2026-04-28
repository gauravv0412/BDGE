"""Client-rendered read-only frontend shell for inspecting public API output."""

from __future__ import annotations

from html import escape

from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.views.decorators.http import require_GET

_MIN_DILEMMA_LEN = 20


@require_GET
def shell_view(request: HttpRequest) -> HttpResponse:
    csrf_token = get_token(request)
    return HttpResponse(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Wisdomize Read-Only Shell</title>
  <style>
    body {{ font-family: Inter, Arial, sans-serif; margin: 0; background: #f3f5fb; color: #172033; line-height: 1.5; }}
    .container {{ max-width: 1040px; margin: 0 auto; padding: 28px 20px 42px; }}
    h1 {{ margin: 0 0 6px; font-size: 34px; letter-spacing: -0.02em; }}
    h2 {{ margin: 0 0 10px; font-size: 23px; }}
    h3 {{ margin: 0 0 12px; font-size: 18px; letter-spacing: 0.01em; }}
    h4 {{ margin: 0 0 8px; font-size: 15px; letter-spacing: 0.01em; }}
    .subtitle {{ color: #4f5b77; margin-top: 0; margin-bottom: 18px; max-width: 760px; }}
    .card {{ background: #fff; border-radius: 14px; padding: 18px 20px; margin: 14px 0; box-shadow: 0 8px 20px rgba(17, 28, 45, 0.06); border: 1px solid #e8ecf5; }}
    .stack {{ display: grid; gap: 14px; }}
    .meta {{ background: #fcfdff; }}
    .meta-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; max-width: 420px; }}
    .error {{ border-left: 5px solid #d33b3b; background: #fff8f8; }}
    .error .code-chip {{ display: inline-block; background: #f3dede; color: #7f2626; border-radius: 999px; padding: 4px 10px; font-size: 12px; margin-bottom: 8px; }}
    .share {{ border-left: 5px solid #5b49d8; background: linear-gradient(155deg, #f6f2ff 0%, #fbf9ff 100%); }}
    .share.spotlight {{ border-left-width: 0; border: 1px solid #d9cffd; background: linear-gradient(145deg, #f1ebff 0%, #fcfaff 100%); box-shadow: 0 12px 26px rgba(91, 73, 216, 0.14); }}
    .share.spotlight h3 {{ margin-bottom: 6px; }}
    .share-title {{ margin: 0; color: #3d2f90; font-size: 20px; letter-spacing: -0.01em; }}
    .share-tag {{ display: inline-block; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; background: #e6ddff; color: #4a3bb9; padding: 4px 8px; border-radius: 999px; margin-bottom: 8px; }}
    .share-quote {{ margin: 10px 0; padding: 12px 14px; background: rgba(255,255,255,0.72); border-left: 4px solid #6e59e0; border-radius: 10px; font-size: 19px; font-weight: 700; color: #241a55; }}
    .share-question {{ margin-top: 8px; color: #433784; font-weight: 600; }}
    .share-actions {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 12px; }}
    .share-actions button {{ margin-top: 0; background: #5947c7; padding: 8px 11px; font-size: 13px; }}
    .share-actions button.secondary {{ background: #ffffff; color: #4a3bb9; border: 1px solid #cfc4fb; }}
    .copy-state {{ color: #3d2f90; font-size: 12px; font-weight: 700; min-height: 18px; }}
    textarea {{ width: 100%; min-height: 128px; border-radius: 10px; border: 1px solid #c7cfdf; padding: 12px; font-size: 14px; resize: vertical; }}
    textarea:focus {{ outline: 2px solid #8fb0ff; border-color: #7fa2f9; }}
    button {{ margin-top: 12px; background: #1d4ed8; color: #fff; border: none; border-radius: 10px; padding: 10px 16px; cursor: pointer; font-weight: 600; font-size: 14px; }}
    button:disabled {{ background: #94a3c3; cursor: not-allowed; }}
    .lead {{ font-size: 28px; line-height: 1.3; margin: 6px 0 16px; font-weight: 700; letter-spacing: -0.01em; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }}
    .metric {{ background: #f6f8fd; border-radius: 10px; padding: 10px 12px; border: 1px solid #e3e8f5; }}
    .metric-label {{ display: block; color: #5a6583; font-size: 12px; }}
    .metric-value {{ display: block; font-size: 16px; font-weight: 700; color: #1e2a42; margin-top: 2px; }}
    .verdict {{ border-left: 5px solid #7a8bb7; }}
    .verdict.positive {{ border-left-color: #2f9e65; }}
    .verdict.negative {{ border-left-color: #c85b5b; }}
    .verdict.mixed {{ border-left-color: #b88e2d; }}
    .verse {{ background: linear-gradient(180deg, #fffdf7 0%, #fffcf2 100%); border-left: 5px solid #af8a2a; }}
    .verse .capture-note {{ display: inline-block; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #7b6438; background: #f4e9cb; padding: 4px 7px; border-radius: 999px; margin-bottom: 8px; }}
    .verse-ref {{ color: #7a5c1e; font-size: 13px; margin: 0 0 6px; letter-spacing: 0.04em; text-transform: uppercase; }}
    .verse-sanskrit {{ font-size: 22px; color: #5a3e10; margin: 4px 0 2px; line-height: 1.4; overflow-wrap: anywhere; }}
    .verse-iast {{ font-style: italic; color: #9a7640; font-size: 13px; margin: 0 0 10px; }}
    .verse-translations {{ background: rgba(255,255,255,0.65); border-radius: 8px; padding: 8px 12px; margin: 6px 0 10px; border: 1px solid rgba(175,138,42,0.15); }}
    .verse-translations p {{ margin: 4px 0; font-size: 14px; }}
    .verse-why {{ margin-top: 8px; }}
    .verse-confidence {{ color: #9a8250; font-size: 13px; margin-top: 6px; }}
    .verse-source {{ color: #7b6438; font-size: 13px; margin-top: 8px; }}
    .verse-block {{ padding: 12px 14px; background: rgba(255,255,255,0.76); border: 1px solid rgba(175,138,42,0.18); border-radius: 10px; margin: 8px 0 10px; }}
    .consequence-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px; }}
    .consequence-card {{ background: #f8faff; border: 1px solid #e2e8f6; border-radius: 11px; padding: 12px 14px; }}
    .consequence-label {{ display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #5b6682; font-weight: 700; margin-bottom: 4px; }}
    .consequence-text {{ margin: 0 0 10px; font-weight: 650; color: #1f2a44; }}
    .consequence-explain {{ margin: 0; color: #3c4862; }}
    .why-applies {{ margin-top: 12px; padding: 11px 13px; background: #fbfcff; border: 1px solid #e4ebf8; border-radius: 10px; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .subtle-panel {{ background: #f7f9fe; border: 1px solid #e5eaf7; border-radius: 10px; padding: 10px 12px; }}
    .reading-block {{ margin-top: 10px; padding: 12px; background: #f9fbff; border-radius: 10px; border: 1px solid #e4ebf8; }}
    .cf {{ border-radius: 11px; padding: 12px; border: 1px solid #e6ebf7; }}
    .cf-risk {{ background: #fff7f7; border-color: #f2d9d9; }}
    .cf-path {{ background: #f5fcf7; border-color: #d4eede; }}
    .higher-path {{ font-size: 18px; font-weight: 600; color: #14274f; }}
    .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    .dim {{ background: #f8faff; border: 1px solid #e4eaf8; border-radius: 9px; padding: 8px 10px; }}
    .missing-facts .hint {{ color: #5a6783; margin-top: -4px; }}
    .missing-facts ul {{ margin: 10px 0 0 18px; }}
    .missing-facts li {{ margin: 6px 0; }}
    blockquote {{ margin: 8px 0; padding: 10px 12px; background: rgba(255,255,255,0.72); border-left: 4px solid #6e59e0; border-radius: 8px; font-size: 17px; font-weight: 600; }}
    #loading {{ display:none; color:#1f4ed8; font-weight:700; margin-top:10px; background:#eaf1ff; border:1px solid #cddcff; border-radius:8px; padding:8px 10px; }}
    .loading-dot {{ display:inline-block; margin-left:6px; width:6px; height:6px; border-radius:999px; background:#1f4ed8; vertical-align:middle; }}
    .hero-grid {{ display:grid; grid-template-columns: 1.3fr 1fr; gap: 14px; align-items: stretch; }}
    .empty-hint {{ color:#5f6b86; }}
    .safety-note {{ font-size: 13px; color: #4a5672; background: #f4f6fb; border: 1px solid #e0e6f2; border-radius: 10px; padding: 10px 12px; margin: 8px 0 12px; line-height: 1.45; }}
    .presentation-section {{ margin-top: 10px; border: 1px solid #dfe6f3; border-radius: 10px; background: #fbfcff; overflow: hidden; }}
    .presentation-section summary {{ cursor: pointer; padding: 10px 12px; font-weight: 700; color: #213252; list-style-position: inside; }}
    .presentation-section[open] summary {{ border-bottom: 1px solid #e2e8f4; background: #f4f7fc; }}
    .presentation-section p {{ margin: 0; padding: 10px 12px 12px; white-space: pre-wrap; color: #34415c; }}
    .presentation-primary {{ white-space: pre-wrap; }}
    .safety-card {{ border-left: 5px solid #c2410c; background: #fff7ed; }}
    .global-foot {{ margin-top: 28px; padding: 16px 20px 28px; border-top: 1px solid #dde3f0; background: #eef2fb; color: #3d4a63; font-size: 13px; line-height: 1.55; max-width: 1040px; margin-left: auto; margin-right: auto; }}
    .global-foot strong {{ color: #243047; }}
    @media (max-width: 860px) {{
      .summary-grid, .two-col, .row, .meta-grid, .hero-grid, .consequence-grid {{ grid-template-columns: 1fr; }}
      .lead {{ font-size: 24px; }}
      .share-quote {{ font-size: 17px; }}
    }}
    @media (max-width: 520px) {{
      body {{ background: #f6f8fd; }}
      .container {{ padding: 18px 12px 30px; }}
      h1 {{ font-size: 27px; }}
      h2 {{ font-size: 20px; }}
      h3 {{ font-size: 16px; margin-bottom: 8px; }}
      .subtitle {{ font-size: 14px; margin-bottom: 12px; }}
      .card {{ border-radius: 12px; padding: 14px 14px; margin: 10px 0; box-shadow: 0 5px 15px rgba(17, 28, 45, 0.05); }}
      .stack {{ gap: 10px; }}
      .hero-grid {{ gap: 10px; }}
      .verdict {{ border-left-width: 4px; }}
      .lead {{ font-size: 21px; line-height: 1.26; margin: 4px 0 12px; }}
      .summary-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; }}
      .metric {{ padding: 7px 8px; border-radius: 9px; }}
      .metric-label {{ font-size: 10px; line-height: 1.2; }}
      .metric-value {{ font-size: 14px; }}
      .presentation-section {{ margin-top: 8px; border-radius: 9px; }}
      .presentation-section summary {{ padding: 8px 10px; font-size: 13px; }}
      .presentation-section p {{ padding: 8px 10px 10px; font-size: 14px; }}
      .share.spotlight {{ padding: 13px 14px; }}
      .share-tag {{ font-size: 10px; padding: 3px 7px; margin-bottom: 5px; }}
      .share-title {{ font-size: 17px; }}
      .share-quote {{ margin: 8px 0; padding: 10px 11px; font-size: 16px; line-height: 1.35; border-left-width: 3px; }}
      .share-question {{ margin: 7px 0 0; font-size: 14px; line-height: 1.35; }}
      .share-actions {{ gap: 6px; margin-top: 10px; }}
      .share-actions button {{ padding: 7px 9px; font-size: 12px; border-radius: 8px; }}
      .copy-state {{ font-size: 11px; min-height: 16px; }}
      .consequence-grid {{ gap: 8px; }}
      .consequence-card, .why-applies, .subtle-panel, .reading-block {{ padding: 10px 11px; border-radius: 10px; }}
      .consequence-label {{ font-size: 10px; }}
      .consequence-text, .consequence-explain, .why-applies p {{ font-size: 14px; }}
      .verse {{ border-left-width: 4px; }}
      .verse-block {{ padding: 10px 11px; margin: 6px 0 8px; }}
      .verse-sanskrit {{ font-size: 19px; line-height: 1.5; }}
      .verse-iast, .verse-source, .verse-confidence {{ font-size: 12px; }}
      .verse-translations {{ padding: 7px 10px; }}
      .verse-translations p {{ font-size: 13px; }}
      .dim {{ padding: 7px 9px; font-size: 13px; }}
      .global-foot {{ margin-top: 18px; padding: 13px 14px 22px; font-size: 12px; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Wisdomize Read-Only Shell</h1>
    <p class="subtitle">Submit a dilemma and inspect the full stable API response in a readable view.</p>
    <section class="card">
      <form id="analyze-form" method="post" novalidate>
        <input type="hidden" name="csrfmiddlewaretoken" value="{escape(csrf_token)}">
        <label for="dilemma"><strong>Dilemma</strong></label>
        <p class="safety-note" id="shell-input-safety" role="note">
          For medical emergencies, legal decisions, active self-harm or harm to others, or an acute crisis,
          do not rely on this tool alone. Use emergency services and qualified professionals.
        </p>
        <textarea id="dilemma" name="dilemma" placeholder="Describe your dilemma..."></textarea>
        <div id="client-validation" style="color:#c52626;margin-top:8px;"></div>
        <button id="submit-btn" type="submit">Analyze Dilemma</button>
      </form>
      <p id="loading">Analyzing dilemma and preparing the structured response...<span class="loading-dot"></span></p>
    </section>
    <div id="result-root" class="stack">
      <section class="card meta" id="empty-state">
        <h2>Ready for Analysis</h2>
        <p class="empty-hint">Submit a dilemma to render a screenshot-ready Wisdomize response here.</p>
      </section>
    </div>
  </div>
  <footer class="global-foot" id="shell-global-disclaimer">
    <strong>About Wisdomize.</strong>
    This shell offers <em>reflective guidance</em>, not absolute religious, legal, or medical advice.
    Scripture is interpreted in many traditions; here it is one condensed lens for everyday ethics.
    If you face urgent harm, a mental-health emergency, or need tailored legal or clinical care,
    seek qualified human help rather than this output alone.
  </footer>
  <script>
    (function() {{
      const MIN_LEN = {_MIN_DILEMMA_LEN};
      const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
      const form = document.getElementById("analyze-form");
      const textarea = document.getElementById("dilemma");
      const loading = document.getElementById("loading");
      const submitBtn = document.getElementById("submit-btn");
      const validation = document.getElementById("client-validation");
      const resultRoot = document.getElementById("result-root");

      function text(v) {{
        return (v === null || v === undefined) ? "" : String(v);
      }}
      function make(tag, className, content) {{
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (content !== undefined) node.textContent = content;
        return node;
      }}
      function appendPair(parent, label, value) {{
        const p = make("p");
        const strong = make("strong", "", label + ": ");
        p.appendChild(strong);
        p.appendChild(document.createTextNode(text(value)));
        parent.appendChild(p);
      }}
      function compactSharePayload(shareLine, shareQuestion) {{
        const line = text(shareLine).trim();
        const question = text(shareQuestion).trim();
        if (question && (line + "\\n" + question).length <= 220) return line + "\\n" + question;
        return line;
      }}
      function fullInsightPayload(shareLine, verdictSentence, shareQuestion) {{
        return [text(shareLine).trim(), text(verdictSentence).trim(), text(shareQuestion).trim()]
          .filter(Boolean)
          .join("\\n");
      }}
      function copyTextToClipboard(value, stateNode) {{
        const payload = text(value).trim();
        if (!payload) return;
        const done = function () {{
          stateNode.textContent = "Copied";
          window.setTimeout(function () {{ stateNode.textContent = ""; }}, 1400);
        }};
        if (Array.isArray(window.__copiedPayloads)) {{
          window.__copiedPayloads.push(payload);
          done();
          return;
        }}
        if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(payload).then(done).catch(function () {{
            fallbackCopy(payload);
            done();
          }});
        }} else {{
          fallbackCopy(payload);
          done();
        }}
      }}
      function fallbackCopy(value) {{
        const area = document.createElement("textarea");
        area.value = value;
        area.setAttribute("readonly", "readonly");
        area.style.position = "fixed";
        area.style.left = "-9999px";
        document.body.appendChild(area);
        area.select();
        try {{ document.execCommand("copy"); }} catch (_err) {{}}
        document.body.removeChild(area);
      }}
      function sectionText(card, label) {{
        const sections = card && Array.isArray(card.sections) ? card.sections : [];
        const hit = sections.find((s) => text(s && s.label) === label);
        return text(hit && hit.text);
      }}
      function presentationCard(presentation, cardKey) {{
        const cards = presentation && presentation.cards ? presentation.cards : {{}};
        return cards && cards[cardKey] ? cards[cardKey] : {{}};
      }}
      function presentationCardCopy(presentation, cardKey, fieldName) {{
        const card = presentationCard(presentation, cardKey);
        return text(card && card[fieldName]);
      }}
      function overlaySection(label, sectionText, defaultOpen) {{
        return {{ label: label, text: text(sectionText), default_open: Boolean(defaultOpen) }};
      }}
      function humanizeClosestTeaching(raw) {{
        const value = text(raw).trim();
        if (!value) return "Pause, clarify intention, and choose the cleanest next action.";
        const forbidden = ["engine", "threshold", "fallback", "verse_match", "selected", "retrieval", "schema"];
        const parts = value.split(/[.?!]+/).map((p) => p.trim()).filter(Boolean);
        const kept = parts.filter((part) => !forbidden.some((w) => part.toLowerCase().includes(w)));
        if (!kept.length) return "Pause, clarify intention, and choose the cleanest next action.";
        return kept.join(". ");
      }}
      function summaryTone(classification) {{
        const c = text(classification).toLowerCase();
        if (c === "dharmic") return "positive";
        if (c === "adharmic") return "negative";
        return "mixed";
      }}
      function setLoading(isLoading) {{
        loading.style.display = isLoading ? "block" : "none";
        submitBtn.disabled = isLoading;
      }}
      function renderError(error, requestId) {{
        resultRoot.replaceChildren();
        const card = make("section", "card error");
        card.appendChild(make("h2", "", "Request Failed"));
        card.appendChild(make("div", "code-chip", text((error && error.code) || "engine_execution_failed")));
        appendPair(card, "Message", text((error && error.message) || "Internal engine failure."));
        if (requestId) appendPair(card, "Request ID", requestId);
        resultRoot.appendChild(card);
      }}
      function renderGuidanceCard(output, presentation, crisis) {{
        if (crisis) return renderPresentationCard(presentation.guidance_card, "", "guidance");
        const verse = output && output.verse_match;
        const closest = output && output.closest_teaching;
        const card = make("section", "card verse");
        card.dataset.card = "guidance";
        if (verse) {{
          card.appendChild(make("div", "capture-note", "Scriptural guidance"));
          card.appendChild(make("h3", "", "Gita Verse"));
          card.appendChild(make("p", "verse-ref", text(verse.verse_ref)));
          const verseBlock = make("div", "verse-block");
          if (text(verse.sanskrit_devanagari)) verseBlock.appendChild(make("p", "verse-sanskrit", text(verse.sanskrit_devanagari)));
          if (text(verse.sanskrit_iast)) verseBlock.appendChild(make("p", "verse-iast", text(verse.sanskrit_iast)));
          card.appendChild(verseBlock);
          const tr = make("div", "verse-translations");
          appendPair(tr, "Hindi", verse.hindi_translation);
          appendPair(tr, "English", verse.english_translation);
          card.appendChild(tr);
          if (text(verse.source)) card.appendChild(make("p", "verse-source", "Source: " + text(verse.source)));
          const why = presentationCardCopy(presentation, "gita_lens", "teaching") || sectionText(presentation.guidance_card, "Explain simply") || text(verse.why_it_applies);
          const whyPrimary = make("p", "verse-why", why);
          whyPrimary.dataset.cardPrimary = "true";
          card.appendChild(whyPrimary);
          card.appendChild(make("p", "verse-confidence", "Match confidence: " + text(verse.match_confidence)));
        }} else if (closest) {{
          card.appendChild(make("div", "capture-note", "Scriptural guidance"));
          card.appendChild(make("h3", "", "Closest Gita Lens"));
          const primary = make("p", "presentation-primary", "Paraphrased teaching, not a quoted verse: " + text(closest));
          primary.dataset.cardPrimary = "true";
          card.appendChild(primary);
          const why = presentationCardCopy(presentation, "gita_lens", "teaching") || sectionText(presentation.guidance_card, "Explain simply");
          if (why) appendPair(card, "Why it applies", why);
          const provisional = sectionText(presentation.guidance_card, "Why this stays provisional");
          if (provisional) appendPair(card, "Why this stays provisional", provisional);
        }} else {{
          card.appendChild(make("h3", "", "Guidance"));
          card.appendChild(make("p", "", "No verse or closest teaching is currently available for this response."));
        }}
        return card;
      }}
      function renderCounterfactual(title, block, tone) {{
        const card = make("div", "cf cf-" + tone);
        card.appendChild(make("h4", "", title));
        appendPair(card, "Assumed context", block && block.assumed_context);
        appendPair(card, "Decision", block && block.decision);
        appendPair(card, "Why", block && block.why);
        return card;
      }}
      function renderDimensions(dimensions) {{
        const wrap = make("div", "row");
        Object.entries(dimensions || {{}}).forEach(([key, value]) => {{
          const item = make("div", "dim");
          appendPair(item, key, value && value.score);
          const note = make("p");
          const em = make("em", "", text(value && value.note));
          note.appendChild(em);
          item.appendChild(note);
          wrap.appendChild(item);
        }});
        return wrap;
      }}
      function renderMissingFacts(missingFacts) {{
        if (!Array.isArray(missingFacts) || missingFacts.length === 0) return make("p", "", "None reported.");
        const ul = make("ul");
        missingFacts.forEach((fact) => {{
          ul.appendChild(make("li", "", text(fact)));
        }});
        return ul;
      }}
      function renderExpandableSection(section) {{
        const details = make("details", "presentation-section");
        details.dataset.sectionLabel = text(section && section.label);
        if (section && section.default_open) details.open = true;
        const summary = make("summary", "", text(section && section.label));
        summary.dataset.sectionLabel = text(section && section.label);
        const sectionText = make("p", "", text(section && section.text));
        sectionText.dataset.sectionText = "true";
        details.appendChild(summary);
        details.appendChild(sectionText);
        return details;
      }}
      function renderPresentationCard(card, className, cardKey) {{
        const node = make("section", "card " + (className || ""));
        if (cardKey) node.dataset.card = cardKey;
        node.appendChild(make("h3", "", text(card && card.title)));
        const primary = make("p", "presentation-primary", text(card && card.primary_text));
        primary.dataset.cardPrimary = "true";
        node.appendChild(primary);
        (card && Array.isArray(card.sections) ? card.sections : []).forEach((section) => {{
          if (text(section && section.text)) node.appendChild(renderExpandableSection(section));
        }});
        return node;
      }}
      function withCardSections(card, sections) {{
        return Object.assign({{}}, card || {{}}, {{ sections: sections.filter((section) => text(section && section.text)) }});
      }}
      function renderIfYouContinueCard(presentation) {{
        const copy = presentationCard(presentation, "if_you_continue");
        const card = make("section", "card");
        card.dataset.card = "if-you-continue";
        card.appendChild(make("h3", "", "If You Continue"));
        const grid = make("div", "consequence-grid");
        [
          ["short_term", "What happens soon", "What this means"],
          ["long_term", "What it can become", "What this means"]
        ].forEach(([key, consequenceLabel, explainLabel]) => {{
          const block = copy && copy[key] ? copy[key] : {{}};
          const item = make("div", "consequence-card");
          item.dataset.consequenceTerm = key;
          item.appendChild(make("span", "consequence-label", consequenceLabel));
          const consequence = make("p", "consequence-text", text(block.consequence));
          consequence.dataset.consequence = "true";
          item.appendChild(consequence);
          item.appendChild(make("span", "consequence-label", explainLabel));
          const explain = make("p", "consequence-explain", text(block.explain_simply));
          explain.dataset.explainSimply = "true";
          item.appendChild(explain);
          grid.appendChild(item);
        }});
        card.appendChild(grid);
        const why = text(copy && copy.why_this_applies);
        if (why) {{
          const whyBlock = make("div", "why-applies");
          appendPair(whyBlock, "Why this applies", why);
          card.appendChild(whyBlock);
        }}
        return card;
      }}
      function buildClientPresentation(output, meta) {{
        const crisisText = [output.dilemma, output.verdict_sentence, output.core_reading, output.gita_analysis, output.higher_path].map(text).join(" ").toLowerCase();
        const hasSafety = ["self-harm", "self harm", "suicide", "kill myself", "end my life", "hurt myself", "harm myself", "better without me", "do anything harmful"].some((term) => crisisText.includes(term));
        if (hasSafety) {{
          const sShort = "In the near term, focus on being physically safe: stay with someone you trust, or contact local crisis or emergency support if you might act on these thoughts.";
          const sLong = "Over time, steady support can make intense pain feel less absolute. You do not have to plan the rest of your life in this hour.";
          return {{
            presentation_mode: "crisis_safe",
            verdict_card: {{
              title: "Verdict",
              primary_text: text(output.verdict_sentence),
              sections: [{{ label: "Explain simply", text: "Pausing to reach out is a signal of care for yourself, not a final judgment of your character.", default_open: false }}]
            }},
            guidance_card: {{
              title: "Support first",
              primary_text: "Right now, the priority is safety and human connection—not a detailed moral score of your thoughts.",
              sections: [{{ label: "Explain simply", text: "If you are afraid you might hurt yourself, please reach out to someone who can be with you in real time.", default_open: false }}]
            }},
            if_you_continue_card: {{
              title: "If You Continue",
              primary_text: "Short-term: " + sShort + "\\nLong-term: " + sLong,
              sections: [
                {{ label: "Short-term - Explain simply", text: sShort, default_open: false }},
                {{ label: "Long-term - Explain simply", text: sLong, default_open: false }},
                {{ label: "What helps now", text: "A small, concrete next step is enough: one message, one call, or one visit to a safe place.", default_open: false }}
              ]
            }},
            counterfactuals_card: {{
              title: "Counterfactuals",
              primary_text: "Alternative storylines are not shown in this safety-focused view.",
              sections: [{{ label: "Explain simply", text: "Comparing paths is de-emphasized so the page does not ask you to rehearse a crisis as a thought experiment. The focus is your immediate safety.", default_open: false }}]
            }},
            higher_path_card: {{
              title: "Immediate Next Step",
              primary_text: "Before interpreting this as a moral decision, treat it as a safety moment. Please contact someone who can stay with you or help you right now.",
              sections: [
                {{ label: "Explain simply", text: "This is not the moment to judge yourself. The cleanest next step is to create distance from harm and involve a real person immediately.", default_open: false }},
                {{ label: "What to do now", text: "Move away from anything you could use to hurt yourself, contact a trusted person, and use local emergency or crisis support if you might act on these thoughts.", default_open: false }}
              ]
            }},
            ethical_dimensions_card: {{
              title: "Ethical Dimensions",
              primary_text: "Dimension scores and detailed reasons are not shown in this safety-focused view.",
              sections: []
            }},
            share_card: {{ title: "Shareable Insight", primary_text: "", sections: [], needs_copy_refinement: false }},
            safety_card: {{
              title: "Safety Note",
              primary_text: "This may need immediate human support, not only ethical reflection.",
              sections: [{{ label: "Explain simply", text: "If this situation involves self-harm, acute crisis, or immediate danger, qualified human support should come before product guidance.", default_open: true }}]
            }},
            meta: {{ presentation_version: "client-fallback", public_schema_changed: false, contract_version: meta && meta.contract_version, presentation_mode: "crisis_safe" }}
          }};
        }}
        const verse = output && output.verse_match;
        const closest = output && output.closest_teaching;
        const closestLens = humanizeClosestTeaching(closest);
        const guidance = verse ? {{
          title: "Gita Verse",
          primary_text: text(verse.why_it_applies || verse.english_translation),
          sections: [
            {{ label: "Explain simply", text: text(verse.why_it_applies || output.gita_analysis || verse.english_translation), default_open: false }},
            {{ label: "Show Gita anchor", text: ["Verse: " + text(verse.verse_ref), "English: " + text(verse.english_translation), "Hindi: " + text(verse.hindi_translation)].filter(Boolean).join("\\n"), default_open: false }}
          ]
        }} : !closest ? {{
          title: "Guidance",
          primary_text: "No verse or closest teaching is currently available for this response.",
          sections: [
            {{ label: "Explain simply", text: text(output.gita_analysis || "No additional guidance is attached to this response."), default_open: false }}
          ]
        }} : {{
          title: "Closest Gita Lens",
          primary_text: "Closest lens: " + text(closestLens) + ". Use this as a lens, not a command.",
          sections: [
            {{ label: "Explain simply", text: text(output.gita_analysis || (text(closestLens) + ". Let this lens help you examine motive, impact, and next step before acting.")), default_open: false }},
            {{ label: "Why this stays provisional", text: "This is not a direct verse verdict. The situation needs judgment beyond a single quote.", default_open: false }}
          ]
        }};
        const share = output.share_layer || {{}};
        return {{
          presentation_mode: "standard",
          verdict_card: {{
            title: "Verdict",
            primary_text: text(output.verdict_sentence),
            sections: [
              {{ label: "Explain simply", text: text(output.core_reading || "This verdict is a direction check based on motive, method, and likely harm."), default_open: false }},
              {{ label: "Why this verdict applies", text: text(output.gita_analysis || "The next step should stay honest, proportionate, and clean under pressure."), default_open: false }}
            ]
          }},
          guidance_card: guidance,
          if_you_continue_card: {{
            title: "If You Continue",
            primary_text: ["Short-term: " + text(output.if_you_continue && output.if_you_continue.short_term), "Long-term: " + text(output.if_you_continue && output.if_you_continue.long_term)].join("\\n"),
            sections: [
              {{ label: "Short-term - Explain simply", text: text(output.if_you_continue && output.if_you_continue.short_term), default_open: false }},
              {{ label: "Long-term - Explain simply", text: text(output.if_you_continue && output.if_you_continue.long_term), default_open: false }},
              {{ label: "Why this applies here", text: text(output.core_reading), default_open: false }}
            ]
          }},
          counterfactuals_card: {{
            title: "Counterfactuals",
            primary_text: ["Adharmic path: " + text(output.counterfactuals && output.counterfactuals.clearly_adharmic_version && output.counterfactuals.clearly_adharmic_version.decision), "Dharmic path: " + text(output.counterfactuals && output.counterfactuals.clearly_dharmic_version && output.counterfactuals.clearly_dharmic_version.decision)].join("\\n"),
            sections: [
              {{ label: "Adharmic assumed inner state", text: text(output.counterfactuals && output.counterfactuals.clearly_adharmic_version && output.counterfactuals.clearly_adharmic_version.assumed_context), default_open: false }},
              {{ label: "Adharmic likely decision", text: text(output.counterfactuals && output.counterfactuals.clearly_adharmic_version && output.counterfactuals.clearly_adharmic_version.decision), default_open: false }},
              {{ label: "Adharmic - Why this matters", text: text(output.counterfactuals && output.counterfactuals.clearly_adharmic_version && output.counterfactuals.clearly_adharmic_version.why), default_open: false }},
              {{ label: "Dharmic assumed inner state", text: text(output.counterfactuals && output.counterfactuals.clearly_dharmic_version && output.counterfactuals.clearly_dharmic_version.assumed_context), default_open: false }},
              {{ label: "Dharmic likely decision", text: text(output.counterfactuals && output.counterfactuals.clearly_dharmic_version && output.counterfactuals.clearly_dharmic_version.decision), default_open: false }},
              {{ label: "Dharmic - Why this matters", text: text(output.counterfactuals && output.counterfactuals.clearly_dharmic_version && output.counterfactuals.clearly_dharmic_version.why), default_open: false }}
            ]
          }},
          higher_path_card: {{
            title: "Higher Path",
            primary_text: text(output.higher_path),
            sections: [
              {{ label: "Explain simply", text: text(output.higher_path), default_open: false }},
              {{ label: "Why this path applies", text: text(output.gita_analysis || "This path keeps the next move accountable instead of letting pressure choose the method."), default_open: false }},
              {{ label: "What it is trying to protect", text: text(output.core_reading || "Truth, non-harm, and a next step that can be defended later."), default_open: false }}
            ]
          }},
          ethical_dimensions_card: {{
            title: "Ethical Dimensions",
            primary_text: text(output.classification) + " (" + text(output.alignment_score) + ")",
            sections: Object.entries(output.ethical_dimensions || {{}}).map(([key, value]) => {{
              return {{ label: key, text: "Score: " + text(value && value.score) + "\\nContext-specific reason: " + text(value && value.note), default_open: true }};
            }})
          }},
          share_card: {{
            title: "Shareable Insight",
            primary_text: text(share.card_quote),
            sections: [
              {{ label: "Reflective question", text: text(share.reflective_question), default_open: false }}
            ],
            needs_copy_refinement: false
          }},
          cards: {{
            verdict: {{
              explain_simply: text(output.core_reading || "This verdict is a direction check based on motive, method, and likely harm."),
              why_this_applies: text(output.gita_analysis || "The next step should stay honest, proportionate, and clean under pressure.")
            }},
            higher_path: {{
              explain_simply: text(output.higher_path),
              why_this_applies: text(output.gita_analysis || "This path keeps the next move accountable instead of letting pressure choose the method."),
              what_it_is_trying_to_protect: text(output.core_reading || "Truth, non-harm, and a next step that can be defended later.")
            }},
            share: {{
              share_line: text(share.card_quote),
              reflective_question: text(share.reflective_question)
            }},
            if_you_continue: {{
              short_term: {{
                consequence: text(output.if_you_continue && output.if_you_continue.short_term),
                explain_simply: "You may get quick relief, but the ethical tension remains active instead of resolved."
              }},
              long_term: {{
                consequence: text(output.if_you_continue && output.if_you_continue.long_term),
                explain_simply: "If this pattern repeats, the shortcut becomes easier to defend next time."
              }},
              why_this_applies: text(output.gita_analysis || "The consequences follow from whether the next step stays honest, proportionate, and clean.")
            }},
            inner_dynamics: {{
              what_is_happening: text(output.core_reading),
              risk: text(output.internal_driver && output.internal_driver.hidden_risk)
            }},
            gita_lens: {{
              teaching: text(output.gita_analysis),
              question: text(share.reflective_question)
            }}
          }},
          safety_card: null,
          meta: {{ presentation_version: "client-fallback", public_schema_changed: false, contract_version: meta && meta.contract_version, presentation_mode: "standard" }}
        }};
      }}
      function renderSuccess(payload, requestId) {{
        const output = payload && payload.output ? payload.output : {{}};
        const meta = payload && payload.meta ? payload.meta : {{}};
        const presentation = payload && payload.presentation ? payload.presentation : buildClientPresentation(output, meta);
        const mode = (presentation && presentation.presentation_mode) || "standard";
        const crisis = mode === "crisis_safe";
        const tone = summaryTone(output.classification);
        const verdictSections = withCardSections(presentation.verdict_card, [
          overlaySection("Explain simply", presentationCardCopy(presentation, "verdict", "explain_simply") || sectionText(presentation.verdict_card, "Explain simply"), false),
          overlaySection("Why this verdict applies", presentationCardCopy(presentation, "verdict", "why_this_applies") || sectionText(presentation.verdict_card, "Why this verdict applies") || sectionText(presentation.verdict_card, "Why this applies to your situation"), false)
        ]);
        const higherPathSections = withCardSections(presentation.higher_path_card, [
          overlaySection("Explain simply", presentationCardCopy(presentation, "higher_path", "explain_simply") || sectionText(presentation.higher_path_card, "Explain simply"), false),
          overlaySection("Why this path applies", presentationCardCopy(presentation, "higher_path", "why_this_applies") || sectionText(presentation.higher_path_card, "Why this path applies") || sectionText(presentation.higher_path_card, "Why this applies here"), false),
          overlaySection("What it is trying to protect", presentationCardCopy(presentation, "higher_path", "what_it_is_trying_to_protect") || sectionText(presentation.higher_path_card, "What it is trying to protect"), false)
        ]);
        const shareLine = presentationCardCopy(presentation, "share", "share_line") || text(presentation.share_card && presentation.share_card.primary_text);
        const shareQuestion = presentationCardCopy(presentation, "share", "reflective_question") || sectionText(presentation.share_card, "Reflective question");
        resultRoot.replaceChildren();

        if (presentation.safety_card) {{
          resultRoot.appendChild(renderPresentationCard(presentation.safety_card, "safety-card", "safety"));
        }}
        if (crisis && presentation.higher_path_card) {{
          resultRoot.appendChild(renderPresentationCard(presentation.higher_path_card, "crisis-immediate", "higher-path"));
        }}

        const metaCard = make("section", "card meta");
        metaCard.appendChild(make("h2", "", "Analysis Result"));
        const mg = make("div", "meta-grid");
        appendPair(mg, "Contract", meta.contract_version);
        appendPair(mg, "Engine", meta.engine_version);
        appendPair(mg, "Presentation mode", (presentation && presentation.presentation_mode) || "standard");
        metaCard.appendChild(mg);
        if (requestId) appendPair(metaCard, "Request ID", requestId);
        resultRoot.appendChild(metaCard);

        const hero = make("section", "hero-grid");
        const verdict = make("div", "card verdict " + tone);
        verdict.dataset.card = "verdict";
        verdict.appendChild(make("h3", "", "Verdict"));
        const verdictPrimary = make("p", "lead", text(presentation.verdict_card && presentation.verdict_card.primary_text));
        verdictPrimary.dataset.cardPrimary = "true";
        verdict.appendChild(verdictPrimary);
        const summary = make("div", "summary-grid");
        [["Classification", output.classification], ["Alignment Score", output.alignment_score], ["Confidence", output.confidence]].forEach(([label, value]) => {{
          const m = make("div", "metric");
          m.appendChild(make("span", "metric-label", label));
          m.appendChild(make("span", "metric-value", text(value)));
          summary.appendChild(m);
        }});
        verdict.appendChild(summary);
        (verdictSections && Array.isArray(verdictSections.sections) ? verdictSections.sections : []).forEach((section) => {{
          if (text(section && section.text)) verdict.appendChild(renderExpandableSection(section));
        }});
        hero.appendChild(verdict);

        if (!crisis) {{
          const shareSpotlight = make("div", "card share spotlight");
          shareSpotlight.dataset.card = "share";
          if (presentation.share_card && presentation.share_card.needs_copy_refinement) shareSpotlight.dataset.needsCopyRefinement = "true";
          shareSpotlight.appendChild(make("div", "share-tag", "Share-ready"));
          shareSpotlight.appendChild(make("h3", "share-title", "Shareable Insight"));
          const spotlightQuote = make("div", "share-quote", shareLine);
          spotlightQuote.dataset.cardPrimary = "true";
          shareSpotlight.appendChild(spotlightQuote);
          if (shareQuestion) shareSpotlight.appendChild(make("p", "share-question", shareQuestion));
          const shareActions = make("div", "share-actions");
          const copyShare = make("button", "", "Copy share line");
          copyShare.type = "button";
          copyShare.dataset.copyAction = "share-line";
          const copyFull = make("button", "secondary", "Copy full insight");
          copyFull.type = "button";
          copyFull.dataset.copyAction = "full-insight";
          const copyState = make("span", "copy-state", "");
          copyState.setAttribute("aria-live", "polite");
          copyShare.addEventListener("click", function () {{
            copyTextToClipboard(compactSharePayload(shareLine, shareQuestion), copyState);
          }});
          copyFull.addEventListener("click", function () {{
            copyTextToClipboard(fullInsightPayload(shareLine, output.verdict_sentence, shareQuestion), copyState);
          }});
          shareActions.appendChild(copyShare);
          shareActions.appendChild(copyFull);
          shareActions.appendChild(copyState);
          shareSpotlight.appendChild(shareActions);
          hero.appendChild(shareSpotlight);
        }}
        resultRoot.appendChild(hero);

        if (!crisis) {{
          const inner = make("section", "card");
          inner.appendChild(make("h3", "", "Inner Dynamics"));
          const two = make("div", "two-col");
          const p1 = make("div", "subtle-panel"); appendPair(p1, "Primary Driver", output.internal_driver && output.internal_driver.primary); two.appendChild(p1);
          const p2 = make("div", "subtle-panel"); appendPair(p2, "Hidden Risk", presentationCardCopy(presentation, "inner_dynamics", "risk") || (output.internal_driver && output.internal_driver.hidden_risk)); two.appendChild(p2);
          inner.appendChild(two);
          const reading = make("div", "reading-block");
          appendPair(reading, "What is happening", presentationCardCopy(presentation, "inner_dynamics", "what_is_happening") || output.core_reading);
          appendPair(reading, "Gita lens", presentationCardCopy(presentation, "gita_lens", "teaching") || output.gita_analysis);
          inner.appendChild(reading);
          resultRoot.appendChild(inner);
        }}

        resultRoot.appendChild(renderGuidanceCard(output, presentation, crisis));
        resultRoot.appendChild(crisis ? renderPresentationCard(presentation.if_you_continue_card, "", "if-you-continue") : renderIfYouContinueCard(presentation));
        resultRoot.appendChild(renderPresentationCard(presentation.counterfactuals_card, "", "counterfactuals"));
        if (!crisis) {{
          resultRoot.appendChild(renderPresentationCard(higherPathSections, "", "higher-path"));
        }}
        if (!crisis) {{
          resultRoot.appendChild(renderPresentationCard(presentation.ethical_dimensions_card, "", "ethical-dimensions"));
        }}

        const mf = make("section", "card missing-facts");
        mf.appendChild(make("h3", "", "Missing Facts"));
        mf.appendChild(make("p", "hint", "Clarifying these can materially change the verdict."));
        mf.appendChild(renderMissingFacts(output.missing_facts));
        resultRoot.appendChild(mf);

      }}

      form.addEventListener("submit", function (e) {{
        e.preventDefault();
        const dilemma = textarea.value.trim();
        if (!dilemma) {{
          validation.textContent = "Please enter a dilemma before submitting.";
          return;
        }}
        if (dilemma.length < MIN_LEN) {{
          validation.textContent = "Please enter at least " + MIN_LEN + " characters for meaningful analysis.";
          return;
        }}
        validation.textContent = "";
        setLoading(true);
        fetch("/api/v1/analyze/presentation", {{
          method: "POST",
          headers: {{
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
          }},
          credentials: "same-origin",
          body: JSON.stringify({{ dilemma: dilemma, contract_version: "1.0" }})
        }})
          .then(async function (response) {{
            const requestId = response.headers.get("X-Request-ID") || "";
            let payload = {{}};
            try {{
              payload = await response.json();
            }} catch (_err) {{
              payload = {{ error: {{ code: "engine_execution_failed", message: "Internal engine failure." }} }};
            }}
            if (response.ok && payload.output) {{
              renderSuccess(payload, requestId);
            }} else {{
              renderError(payload.error || {{ code: "engine_execution_failed", message: "Internal engine failure." }}, requestId);
            }}
          }})
          .catch(function () {{
            renderError({{ code: "engine_execution_failed", message: "Unable to reach analyze API. Please try again." }}, "");
          }})
          .finally(function () {{
            setLoading(false);
          }});
      }});
    }})();
  </script>
</body>
</html>"""
    )
