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
  <script>
    (function() {{
      try {{
        const saved = localStorage.getItem("wisdomize-theme");
        const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
        const theme = saved === "dark" || saved === "light" ? saved : (prefersDark ? "dark" : "light");
        document.documentElement.dataset.theme = theme;
      }} catch (_err) {{
        document.documentElement.dataset.theme = "light";
      }}
    }})();
  </script>
  <title>Wisdomize Read-Only Shell</title>
  <style>
    :root {{
      color-scheme: light;
      --page-bg: #f3f5fb;
      --page-bg-soft: #eef2fb;
      --card-bg: #ffffff;
      --card-bg-soft: #fbfcff;
      --panel-bg: #f7f9fe;
      --text: #172033;
      --text-strong: #1e2a42;
      --muted: #4f5b77;
      --muted-2: #5a6583;
      --border: #e3e8f5;
      --border-strong: #c7cfdf;
      --shadow: 0 12px 30px rgba(17, 28, 45, 0.07);
      --button-bg: #1d4ed8;
      --button-bg-hover: #173ea9;
      --button-disabled: #94a3c3;
      --focus: #8fb0ff;
      --share-bg: linear-gradient(145deg, #f1ebff 0%, #fcfaff 100%);
      --share-border: #d9cffd;
      --share-text: #241a55;
      --share-muted: #433784;
      --verse-bg: linear-gradient(180deg, #fffdf7 0%, #fffcf2 100%);
      --verse-panel: rgba(255,255,255,0.76);
      --verse-text: #5a3e10;
      --error-bg: #fff8f8;
      --error-border: #f1cdcd;
      --error-text: #7f2626;
      --loading-bg: linear-gradient(145deg, #edf4ff 0%, #f8fbff 100%);
      --loading-border: #cddcff;
    }}
    :root[data-theme="dark"] {{
      color-scheme: dark;
      --page-bg: #0d1320;
      --page-bg-soft: #111a2c;
      --card-bg: #151e31;
      --card-bg-soft: #111a2c;
      --panel-bg: #182237;
      --text: #ecf2ff;
      --text-strong: #f8fbff;
      --muted: #aebbd3;
      --muted-2: #95a4bf;
      --border: #283651;
      --border-strong: #3a4965;
      --shadow: 0 14px 34px rgba(0, 0, 0, 0.32);
      --button-bg: #6d8dff;
      --button-bg-hover: #8ca4ff;
      --button-disabled: #475569;
      --focus: #9bb5ff;
      --share-bg: linear-gradient(145deg, #251f46 0%, #171d31 100%);
      --share-border: #4c4281;
      --share-text: #f1ecff;
      --share-muted: #cbc1ff;
      --verse-bg: linear-gradient(180deg, #251f13 0%, #191b27 100%);
      --verse-panel: rgba(255,255,255,0.06);
      --verse-text: #f3d891;
      --error-bg: #2b171b;
      --error-border: #6f3039;
      --error-text: #ffd6d6;
      --loading-bg: linear-gradient(145deg, #17253f 0%, #121b2e 100%);
      --loading-border: #31456b;
    }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: Inter, Arial, sans-serif; margin: 0; background: radial-gradient(circle at top left, rgba(93, 117, 255, 0.10), transparent 32%), var(--page-bg); color: var(--text); line-height: 1.5; }}
    .container {{ max-width: 1040px; margin: 0 auto; padding: 28px 20px 42px; }}
    h1 {{ margin: 0 0 6px; font-size: 34px; letter-spacing: -0.02em; }}
    h2 {{ margin: 0 0 10px; font-size: 23px; }}
    h3 {{ margin: 0 0 12px; font-size: 18px; letter-spacing: 0.01em; }}
    h4 {{ margin: 0 0 8px; font-size: 15px; letter-spacing: 0.01em; }}
    .topbar {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 18px; }}
    .subtitle {{ color: var(--muted); margin-top: 0; margin-bottom: 0; max-width: 760px; }}
    .theme-toggle {{ margin-top: 2px; white-space: nowrap; background: var(--card-bg); color: var(--text-strong); border: 1px solid var(--border); box-shadow: var(--shadow); padding: 8px 12px; }}
    .theme-toggle:hover {{ background: var(--panel-bg); }}
    .theme-toggle .theme-icon {{ display: inline-block; margin-right: 5px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.78; }}
    .card {{ background: var(--card-bg); border-radius: 14px; padding: 18px 20px; margin: 14px 0; box-shadow: var(--shadow); border: 1px solid var(--border); }}
    .stack {{ display: grid; gap: 14px; }}
    .meta {{ background: var(--card-bg-soft); }}
    .meta-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; max-width: 420px; }}
    .error {{ border-left: 5px solid #d33b3b; background: var(--error-bg); border-color: var(--error-border); }}
    .error p {{ color: var(--error-text); }}
    .error-actions {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-top: 10px; }}
    .error-actions button {{ margin-top: 0; }}
    .feedback {{ background: var(--card-bg-soft); }}
    .feedback .hint {{ color: var(--muted); margin: -4px 0 12px; }}
    .feedback-row {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 8px 0 12px; }}
    .feedback-label {{ color: var(--text-strong); font-weight: 750; margin-right: 2px; }}
    .feedback-choice, .feedback-tag {{ margin-top: 0; background: var(--card-bg); color: var(--text-strong); border: 1px solid var(--border); padding: 7px 10px; box-shadow: none; }}
    .feedback-choice:hover:not(:disabled), .feedback-tag:hover:not(:disabled) {{ background: var(--panel-bg); transform: none; }}
    .feedback-choice.is-selected, .feedback-tag.is-selected {{ background: var(--button-bg); color: #fff; border-color: var(--button-bg); }}
    .feedback textarea {{ min-height: 72px; margin-top: 6px; }}
    .feedback-actions {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-top: 8px; }}
    .feedback-actions button {{ margin-top: 0; }}
    .feedback-state {{ min-height: 20px; color: var(--muted); font-weight: 700; }}
    .feedback-state.error-text {{ color: var(--error-text); }}
    .share {{ border-left: 5px solid #5b49d8; background: linear-gradient(155deg, #f6f2ff 0%, #fbf9ff 100%); }}
    .share.spotlight {{ border-left-width: 0; border: 1px solid var(--share-border); background: var(--share-bg); box-shadow: 0 12px 26px rgba(91, 73, 216, 0.14); }}
    .share.spotlight h3 {{ margin-bottom: 6px; }}
    .share-title {{ margin: 0; color: var(--share-muted); font-size: 20px; letter-spacing: -0.01em; }}
    .share-tag {{ display: inline-block; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; background: #e6ddff; color: #4a3bb9; padding: 4px 8px; border-radius: 999px; margin-bottom: 8px; }}
    .share-quote {{ margin: 10px 0; padding: 12px 14px; background: var(--verse-panel); border-left: 4px solid #6e59e0; border-radius: 10px; font-size: 19px; font-weight: 700; color: var(--share-text); }}
    .share-question {{ margin-top: 8px; color: var(--share-muted); font-weight: 600; }}
    .share-actions {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 12px; }}
    .share-actions button {{ margin-top: 0; background: #5947c7; padding: 8px 11px; font-size: 13px; }}
    .share-actions button.secondary {{ background: var(--card-bg); color: var(--share-muted); border: 1px solid var(--share-border); }}
    .copy-state {{ color: var(--share-muted); font-size: 12px; font-weight: 700; min-height: 18px; }}
    textarea {{ width: 100%; min-height: 128px; border-radius: 10px; border: 1px solid var(--border-strong); padding: 12px; font-size: 14px; resize: vertical; background: var(--card-bg); color: var(--text); }}
    textarea:focus {{ outline: 2px solid var(--focus); border-color: var(--focus); }}
    button {{ margin-top: 12px; background: var(--button-bg); color: #fff; border: none; border-radius: 10px; padding: 10px 16px; cursor: pointer; font-weight: 600; font-size: 14px; transition: background 150ms ease, transform 150ms ease, opacity 150ms ease; }}
    button:hover:not(:disabled) {{ background: var(--button-bg-hover); transform: translateY(-1px); }}
    button:disabled {{ background: var(--button-disabled); cursor: not-allowed; opacity: 0.78; transform: none; }}
    .lead {{ font-size: 28px; line-height: 1.3; margin: 6px 0 16px; font-weight: 700; letter-spacing: -0.01em; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }}
    .metric {{ background: var(--panel-bg); border-radius: 10px; padding: 10px 12px; border: 1px solid var(--border); }}
    .metric-label {{ display: block; color: var(--muted-2); font-size: 12px; }}
    .metric-value {{ display: block; font-size: 16px; font-weight: 700; color: var(--text-strong); margin-top: 2px; }}
    .verdict {{ border-left: 5px solid #7a8bb7; }}
    .verdict.positive {{ border-left-color: #2f9e65; }}
    .verdict.negative {{ border-left-color: #c85b5b; }}
    .verdict.mixed {{ border-left-color: #b88e2d; }}
    .verse {{ background: var(--verse-bg); border-left: 5px solid #af8a2a; }}
    .verse .capture-note {{ display: inline-block; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #7b6438; background: #f4e9cb; padding: 4px 7px; border-radius: 999px; margin-bottom: 8px; }}
    .verse-ref {{ color: var(--verse-text); font-size: 13px; margin: 0 0 6px; letter-spacing: 0.04em; text-transform: uppercase; }}
    .verse-sanskrit {{ font-size: 22px; color: var(--verse-text); margin: 4px 0 2px; line-height: 1.4; overflow-wrap: anywhere; }}
    .verse-iast {{ font-style: italic; color: #9a7640; font-size: 13px; margin: 0 0 10px; }}
    .verse-translations {{ background: var(--verse-panel); border-radius: 8px; padding: 8px 12px; margin: 6px 0 10px; border: 1px solid rgba(175,138,42,0.25); }}
    .verse-translations p {{ margin: 4px 0; font-size: 14px; }}
    .verse-why {{ margin-top: 8px; }}
    .verse-confidence {{ color: #9a8250; font-size: 13px; margin-top: 6px; }}
    .verse-source {{ color: #7b6438; font-size: 13px; margin-top: 8px; }}
    .verse-block {{ padding: 12px 14px; background: var(--verse-panel); border: 1px solid rgba(175,138,42,0.25); border-radius: 10px; margin: 8px 0 10px; }}
    .consequence-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px; }}
    .consequence-card {{ background: var(--panel-bg); border: 1px solid var(--border); border-radius: 11px; padding: 12px 14px; }}
    .consequence-label {{ display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted-2); font-weight: 700; margin-bottom: 4px; }}
    .consequence-text {{ margin: 0 0 10px; font-weight: 650; color: var(--text-strong); }}
    .consequence-explain {{ margin: 0; color: var(--muted); }}
    .why-applies {{ margin-top: 12px; padding: 11px 13px; background: var(--card-bg-soft); border: 1px solid var(--border); border-radius: 10px; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .subtle-panel {{ background: var(--panel-bg); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; }}
    .reading-block {{ margin-top: 10px; padding: 12px; background: var(--card-bg-soft); border-radius: 10px; border: 1px solid var(--border); }}
    .cf {{ border-radius: 11px; padding: 12px; border: 1px solid #e6ebf7; }}
    .cf-risk {{ background: #fff7f7; border-color: #f2d9d9; }}
    .cf-path {{ background: #f5fcf7; border-color: #d4eede; }}
    :root[data-theme="dark"] .share-tag {{ background: #352b63; color: #ddd5ff; }}
    :root[data-theme="dark"] .share-actions button.secondary {{ background: rgba(255,255,255,0.05); }}
    :root[data-theme="dark"] .cf {{ border-color: var(--border); }}
    :root[data-theme="dark"] .cf-risk {{ background: #2a1a20; border-color: #59323d; }}
    :root[data-theme="dark"] .cf-path {{ background: #16261e; border-color: #31543e; }}
    :root[data-theme="dark"] .safety-card {{ background: #2b1c12; }}
    .higher-path {{ font-size: 18px; font-weight: 600; color: var(--text-strong); }}
    .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    .dim {{ background: var(--panel-bg); border: 1px solid var(--border); border-radius: 9px; padding: 8px 10px; }}
    .missing-facts .hint {{ color: var(--muted); margin-top: -4px; }}
    .missing-facts ul {{ margin: 10px 0 0 18px; }}
    .missing-facts li {{ margin: 6px 0; }}
    blockquote {{ margin: 8px 0; padding: 10px 12px; background: var(--verse-panel); border-left: 4px solid #6e59e0; border-radius: 8px; font-size: 17px; font-weight: 600; }}
    #loading {{ display:none; }}
    .loading-card {{ margin-top: 14px; color: var(--text); background: var(--loading-bg); border: 1px solid var(--loading-border); border-radius: 14px; padding: 14px 16px; box-shadow: inset 0 1px 0 rgba(255,255,255,0.18); }}
    .loading-inner {{ display: grid; grid-template-columns: auto 1fr; gap: 12px; align-items: center; }}
    .loading-orb {{ width: 36px; height: 36px; border-radius: 999px; border: 2px solid rgba(109, 141, 255, 0.28); border-top-color: var(--button-bg); animation: wisdomize-spin 900ms linear infinite; }}
    .loading-title {{ margin: 0; font-weight: 800; color: var(--text-strong); }}
    .loading-steps {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 7px; }}
    .loading-step {{ font-size: 12px; color: var(--muted); border: 1px solid var(--border); background: var(--card-bg); border-radius: 999px; padding: 4px 8px; animation: wisdomize-pulse 1.8s ease-in-out infinite; }}
    .loading-step:nth-child(2) {{ animation-delay: 180ms; }}
    .loading-step:nth-child(3) {{ animation-delay: 360ms; }}
    .hero-grid {{ display:grid; grid-template-columns: 1.3fr 1fr; gap: 14px; align-items: stretch; }}
    @keyframes wisdomize-spin {{ to {{ transform: rotate(360deg); }} }}
    @keyframes wisdomize-pulse {{ 0%, 100% {{ opacity: 0.68; }} 50% {{ opacity: 1; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .loading-orb, .loading-step, button {{ animation: none; transition: none; }}
    }}
    .empty-hint {{ color: var(--muted); }}
    .safety-note {{ font-size: 13px; color: var(--muted); background: var(--panel-bg); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; margin: 8px 0 12px; line-height: 1.45; }}
    .presentation-section {{ margin-top: 10px; border: 1px solid var(--border); border-radius: 10px; background: var(--card-bg-soft); overflow: hidden; }}
    .presentation-section summary {{ cursor: pointer; padding: 10px 12px; font-weight: 700; color: var(--text-strong); list-style-position: inside; }}
    .presentation-section[open] summary {{ border-bottom: 1px solid var(--border); background: var(--panel-bg); }}
    .presentation-section p {{ margin: 0; padding: 10px 12px 12px; white-space: pre-wrap; color: var(--muted); }}
    .presentation-primary {{ white-space: pre-wrap; }}
    .safety-card {{ border-left: 5px solid #c2410c; background: #fff7ed; }}
    .global-foot {{ margin-top: 28px; padding: 16px 20px 28px; border-top: 1px solid var(--border); background: var(--page-bg-soft); color: var(--muted); font-size: 13px; line-height: 1.55; max-width: 1040px; margin-left: auto; margin-right: auto; }}
    .global-foot strong {{ color: var(--text-strong); }}
    @media (max-width: 860px) {{
      .summary-grid, .two-col, .row, .meta-grid, .hero-grid, .consequence-grid {{ grid-template-columns: 1fr; }}
      .lead {{ font-size: 24px; }}
      .share-quote {{ font-size: 17px; }}
    }}
    @media (max-width: 520px) {{
      body {{ background: var(--page-bg); }}
      .container {{ padding: 18px 12px 30px; }}
      .topbar {{ align-items: stretch; flex-direction: column; gap: 10px; margin-bottom: 12px; }}
      .theme-toggle {{ align-self: flex-start; box-shadow: none; }}
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
      .share-actions button {{ flex: 1 1 132px; padding: 8px 9px; font-size: 12px; border-radius: 8px; }}
      .copy-state {{ font-size: 11px; min-height: 16px; }}
      .loading-card {{ padding: 12px; }}
      .loading-inner {{ grid-template-columns: 1fr; gap: 9px; }}
      .loading-orb {{ width: 30px; height: 30px; }}
      .loading-steps {{ display: grid; grid-template-columns: 1fr; }}
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
      [data-card='ethical-dimensions'] .presentation-primary {{ font-size: 14px; }}
      .global-foot {{ margin-top: 18px; padding: 13px 14px 22px; font-size: 12px; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header class="topbar">
      <div>
        <h1>Wisdomize Read-Only Shell</h1>
        <p class="subtitle">Submit a dilemma and inspect the full stable API response in a readable view.</p>
      </div>
      <button id="theme-toggle" class="theme-toggle" type="button" aria-label="Switch to dark theme" aria-pressed="false">
        <span class="theme-icon" aria-hidden="true">Theme</span>
        <span id="theme-toggle-label">Light</span>
      </button>
    </header>
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
      <div id="loading" class="loading-card" role="status" aria-live="polite" aria-hidden="true">
        <div class="loading-inner">
          <div class="loading-orb" aria-hidden="true"></div>
          <div>
            <p class="loading-title">Reading this dilemma with care...</p>
            <div class="loading-steps" aria-label="Analysis progress">
              <span class="loading-step">Reading the dilemma</span>
              <span class="loading-step">Separating pressure from facts</span>
              <span class="loading-step">Preparing a clearer response</span>
            </div>
          </div>
        </div>
      </div>
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
      const themeToggle = document.getElementById("theme-toggle");
      const themeToggleLabel = document.getElementById("theme-toggle-label");
      let isPending = false;

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
      function applyTheme(theme, persist) {{
        const normalized = theme === "dark" ? "dark" : "light";
        document.documentElement.dataset.theme = normalized;
        themeToggleLabel.textContent = normalized === "dark" ? "Dark" : "Light";
        themeToggle.setAttribute("aria-pressed", normalized === "dark" ? "true" : "false");
        themeToggle.setAttribute("aria-label", normalized === "dark" ? "Switch to light theme" : "Switch to dark theme");
        if (persist) {{
          try {{ localStorage.setItem("wisdomize-theme", normalized); }} catch (_err) {{}}
        }}
      }}
      function setLoading(isLoading) {{
        isPending = isLoading;
        loading.style.display = isLoading ? "block" : "none";
        loading.setAttribute("aria-hidden", isLoading ? "false" : "true");
        submitBtn.disabled = isLoading;
        submitBtn.textContent = isLoading ? "Analyzing..." : "Analyze Dilemma";
      }}
      function renderError() {{
        resultRoot.replaceChildren();
        const card = make("section", "card error");
        card.setAttribute("role", "alert");
        card.appendChild(make("h2", "", "Something went wrong"));
        card.appendChild(make("p", "", "Something went wrong while reading this dilemma. Please try again."));
        const actions = make("div", "error-actions");
        const retry = make("button", "", "Try again");
        retry.type = "button";
        retry.dataset.retryAction = "true";
        retry.addEventListener("click", function () {{
          if (!isPending) form.requestSubmit();
        }});
        actions.appendChild(retry);
        card.appendChild(actions);
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
        const compactMobileDetails = cardKey === "ethical-dimensions" && window.matchMedia && window.matchMedia("(max-width: 520px)").matches;
        (card && Array.isArray(card.sections) ? card.sections : []).forEach((section) => {{
          if (text(section && section.text)) {{
            const detail = renderExpandableSection(section);
            if (compactMobileDetails) detail.open = false;
            node.appendChild(detail);
          }}
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
      function guidanceType(output) {{
        if (output && output.verse_match) return "verse_match";
        if (output && output.closest_teaching) return "closest_teaching";
        return "none";
      }}
      function feedbackSignal(card, groupName) {{
        const selected = card.querySelector("[data-feedback-group='" + groupName + "'].is-selected");
        return selected ? selected.dataset.feedbackValue || null : null;
      }}
      function feedbackTags(card) {{
        return Array.from(card.querySelectorAll("[data-feedback-tag].is-selected")).map((node) => node.dataset.feedbackTag);
      }}
      function setFeedbackBusy(card, isBusy) {{
        card.querySelectorAll("button, textarea").forEach((node) => {{
          node.disabled = isBusy || node.dataset.feedbackSubmitted === "true";
        }});
      }}
      function renderFeedbackCard(output, presentation, crisis) {{
        const card = make("section", "card feedback");
        card.dataset.card = "feedback";
        const gType = guidanceType(output);
        const resultId = text(output && output.dilemma_id).trim();
        let submitted = false;
        card.appendChild(make("h3", "", crisis ? "Was this response helpful?" : "Was this useful?"));
        card.appendChild(make("p", "hint", crisis ? "A quick signal helps improve the safety-focused response." : "A quick signal helps improve Wisdomize without storing your dilemma."));

        function addChoiceRow(label, groupName) {{
          const row = make("div", "feedback-row");
          row.appendChild(make("span", "feedback-label", label));
          [["up", "Thumbs up"], ["down", "Thumbs down"]].forEach(([value, copy]) => {{
            const button = make("button", "feedback-choice", copy);
            button.type = "button";
            button.dataset.feedbackGroup = groupName;
            button.dataset.feedbackValue = value;
            button.setAttribute("aria-pressed", "false");
            button.addEventListener("click", function () {{
              if (submitted) return;
              card.querySelectorAll("[data-feedback-group='" + groupName + "']").forEach((peer) => {{
                peer.classList.remove("is-selected");
                peer.setAttribute("aria-pressed", "false");
              }});
              button.classList.add("is-selected");
              button.setAttribute("aria-pressed", "true");
            }});
            row.appendChild(button);
          }});
          card.appendChild(row);
        }}

        addChoiceRow(crisis ? "Helpful response" : "Usefulness", "usefulness");
        if (!crisis && gType !== "none") {{
          addChoiceRow(gType === "verse_match" ? "Verse relevance" : "Teaching relevance", "verse_relevance");
        }}
        if (!crisis) {{
          const tagRow = make("div", "feedback-row");
          tagRow.appendChild(make("span", "feedback-label", "Optional tags"));
          [
            ["verdict_felt_right", "Verdict felt right"],
            ["verse_felt_relevant", "Verse felt relevant"],
            ["too_harsh", "Too harsh"],
            ["too_vague", "Too vague"],
            ["unsafe_concerning", "Unsafe / concerning"]
          ].forEach(([value, copy]) => {{
            const tag = make("button", "feedback-tag", copy);
            tag.type = "button";
            tag.dataset.feedbackTag = value;
            tag.setAttribute("aria-pressed", "false");
            tag.addEventListener("click", function () {{
              if (submitted) return;
              tag.classList.toggle("is-selected");
              tag.setAttribute("aria-pressed", tag.classList.contains("is-selected") ? "true" : "false");
            }});
            tagRow.appendChild(tag);
          }});
          card.appendChild(tagRow);
        }}

        const comment = document.createElement("textarea");
        comment.dataset.feedbackComment = "true";
        comment.maxLength = 500;
        comment.placeholder = crisis ? "Optional note..." : "Optional short comment...";
        card.appendChild(comment);

        const actions = make("div", "feedback-actions");
        const submit = make("button", "", "Send feedback");
        submit.type = "button";
        submit.dataset.feedbackSubmit = "true";
        const state = make("span", "feedback-state", "");
        state.setAttribute("aria-live", "polite");
        actions.appendChild(submit);
        actions.appendChild(state);
        card.appendChild(actions);

        submit.addEventListener("click", function () {{
          if (submitted || submit.disabled) return;
          state.classList.remove("error-text");
          state.textContent = "";
          const payload = {{
            result_id: resultId,
            usefulness: feedbackSignal(card, "usefulness"),
            verse_relevance: crisis ? null : feedbackSignal(card, "verse_relevance"),
            tags: crisis ? [] : feedbackTags(card),
            comment: text(comment.value).trim() || null,
            route: "presentation",
            client_theme: document.documentElement.dataset.theme === "dark" ? "dark" : "light",
            guidance_type: crisis ? "none" : gType
          }};
          setFeedbackBusy(card, true);
          submit.textContent = "Sending...";
          fetch("/api/v1/feedback", {{
            method: "POST",
            headers: {{
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken
            }},
            credentials: "same-origin",
            body: JSON.stringify(payload)
          }})
            .then(async function (response) {{
              let body = {{}};
              try {{ body = await response.json(); }} catch (_err) {{}}
              if (!response.ok || !body.ok) throw new Error("feedback failed");
              submitted = true;
              card.querySelectorAll("button, textarea").forEach((node) => {{
                node.disabled = true;
                node.dataset.feedbackSubmitted = "true";
              }});
              submit.textContent = "Feedback sent";
              state.textContent = "Thanks — this helps improve Wisdomize.";
            }})
            .catch(function () {{
              submit.textContent = "Try again";
              state.textContent = "Feedback could not be saved. Please try again.";
              state.classList.add("error-text");
              setFeedbackBusy(card, false);
            }});
        }});

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
        resultRoot.appendChild(renderFeedbackCard(output, presentation, crisis));

      }}

      applyTheme(document.documentElement.dataset.theme || "light", false);
      themeToggle.addEventListener("click", function () {{
        applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark", true);
      }});

      form.addEventListener("submit", function (e) {{
        e.preventDefault();
        if (isPending) return;
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
        resultRoot.replaceChildren();
        const pendingCard = make("section", "card meta");
        pendingCard.appendChild(make("h2", "", "Preparing analysis"));
        pendingCard.appendChild(make("p", "empty-hint", "Your result will appear here as soon as the response is ready."));
        resultRoot.appendChild(pendingCard);
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
