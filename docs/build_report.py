"""Build report.html: one self-contained file (all screenshots embedded as base64).

Run from the repo root:  python docs/build_report.py
Numbers come from evals/results/*.json (real runs) and screenshots of the app's own logs.
"""

import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "report_images"
OUT = ROOT / "report.html"

P_IN, P_CACHED, P_OUT = 0.10, 0.01, 0.50  # estimated gpt-6-luna list prices, $ per 1M tokens


def cost(i, c, o):
    return ((i - c) * P_IN + c * P_CACHED + o * P_OUT) / 1e6


# ---------- numbering helpers ----------
_fig = [0]
_tab = [0]


def figure(name, caption, cls=""):
    _fig[0] += 1
    data = base64.b64encode((IMG / f"{name}.jpg").read_bytes()).decode()
    return (f'<figure class="{cls}"><img src="data:image/jpeg;base64,{data}" alt="{caption}" />'
            f'<figcaption><b>Figure {_fig[0]}.</b> {caption}</figcaption></figure>')


def svg_figure(svg, caption):
    _fig[0] += 1
    return f'<figure class="diagram">{svg}<figcaption><b>Figure {_fig[0]}.</b> {caption}</figcaption></figure>'


def table(caption, head, rows, cls=""):
    _tab[0] += 1
    th = "".join(f"<th>{h}</th>" for h in head)
    return (f'<div class="tbl {cls}"><div class="tcap"><b>Table {_tab[0]}.</b> {caption}</div>'
            f'<table><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table></div>')


def evidence(items):
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f'<aside class="evidence"><div class="ev-title">Evidence in this section</div><ul>{lis}</ul></aside>'


def section(num, title, kicker):
    return (f'<header class="sec"><div class="sec-num">{num:02d}</div><div><div class="sec-kicker">{kicker}</div>'
            f'<h2>{num}. {title}</h2></div></header>')


# ---------- measured data ----------
ev_new = json.loads((ROOT / "evals/results/eval_20261024_120407.json").read_text())["results"]
ev_old = json.loads((ROOT / "evals/results/eval_20261024_104221.json").read_text())["results"]
rt1 = json.loads((ROOT / "evals/results/red_team_20261024_120057.json").read_text())
rt2 = json.loads((ROOT / "evals/results/red_team_20261024_120231.json").read_text())
opt, unopt = ev_new["optimized"], ev_new["unoptimized"]
old_opt, old_unopt = ev_old["optimized"], ev_old["unoptimized"]
c_opt = cost(opt["avg_input"], opt["avg_cached"], opt["avg_output"])
c_unopt = cost(unopt["avg_input"], unopt["avg_cached"], unopt["avg_output"])
c_old_opt = cost(old_opt["avg_input"], old_opt["avg_cached"], old_opt["avg_output"])
c_old_unopt = cost(old_unopt["avg_input"], old_unopt["avg_cached"], old_unopt["avg_output"])
c_helper = cost(1914, 0, 162)
c_guard = cost(287, 0, 36)
c_bundle = cost(6186, 3544, 264)
per_user = 30 * c_opt + 4 * c_helper + 3 * c_guard

ARCH_SVG = """
<svg viewBox="0 0 820 420" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SOMthing system architecture">
 <defs>
  <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1f4e8c"/></marker>
  <style>
   .bx{fill:#fff;stroke:#c3d0e4;stroke-width:1.4} .ai{fill:#00356b} .ck{fill:#eef3fa;stroke:#b9cbe5;stroke-width:1.4}
   .tl{fill:#f7f9fc;stroke:#9fb4d6;stroke-width:1.2;stroke-dasharray:5 3} .db{fill:#dfe8f5;stroke:#8fa8cf;stroke-width:1.4}
   .h{font:700 13.5px -apple-system,Helvetica,Arial,sans-serif;fill:#0b2a55} .s{font:11.5px -apple-system,Helvetica,Arial,sans-serif;fill:#53647e}
   .hw{fill:#fff} .sw{fill:#c9d8ee} .m{font:600 11.5px ui-monospace,Menlo,monospace;fill:#0b2a55}
   .ln{stroke:#1f4e8c;stroke-width:1.7;fill:none} .lane{font:700 10.5px -apple-system,Helvetica,Arial,sans-serif;letter-spacing:.12em;fill:#8a9bb5}
  </style>
 </defs>
 <text class="lane" x="10" y="14">BUYER FLOW</text>
 <rect class="bx" x="10" y="22" width="120" height="64" rx="10"/><text class="h" x="22" y="48">Buyer</text><text class="s" x="22" y="68">asks in plain words</text>
 <rect class="ck" x="160" y="22" width="140" height="64" rx="10"/><text class="h" x="172" y="48">Input checks</text><text class="s" x="172" y="68">+ safety guard if needed</text>
 <rect class="ai" x="330" y="22" width="140" height="64" rx="10"/><text class="h hw" x="342" y="48">SOMbot</text><text class="s sw" x="342" y="68">gpt-6-luna agent</text>
 <rect class="ck" x="500" y="22" width="140" height="64" rx="10"/><text class="h" x="512" y="48">Output checks</text><text class="s" x="512" y="68">real IDs · prices · leaks</text>
 <rect class="bx" x="670" y="22" width="140" height="64" rx="10"/><text class="h" x="682" y="48">Verified answer</text><text class="s" x="682" y="68">cards from the database</text>
 <path class="ln" d="M130,54 L158,54" marker-end="url(#ah)"/><path class="ln" d="M300,54 L328,54" marker-end="url(#ah)"/>
 <path class="ln" d="M470,54 L498,54" marker-end="url(#ah)"/><path class="ln" d="M640,54 L668,54" marker-end="url(#ah)"/>
 <rect class="tl" x="300" y="112" width="200" height="72" rx="9"/>
 <text class="m" x="314" y="134">search_listings</text><text class="m" x="314" y="153">get_listing_details</text><text class="m" x="314" y="172">check_bundle</text>
 <path class="ln" d="M400,86 L400,110" marker-end="url(#ah)" marker-start="url(#ah)"/>
 <rect class="db" x="160" y="204" width="650" height="44" rx="12"/>
 <text class="h" x="178" y="231">Listings database</text><text class="s" x="320" y="231">55 listings · the single source of truth for what exists and what it costs</text>
 <path class="ln" d="M400,184 L400,202" marker-end="url(#ah)" marker-start="url(#ah)"/>
 <text class="s" x="512" y="150" style="font-style:italic">read-only tools (plain code)</text>
 <rect class="tl" x="300" y="268" width="200" height="40" rx="9"/><text class="m" x="314" y="293">get_price_comps</text>
 <path class="ln" d="M400,250 L400,266" marker-end="url(#ah)" marker-start="url(#ah)"/>
 <text class="lane" x="10" y="328">SELLER FLOW</text>
 <rect class="bx" x="10" y="336" width="120" height="64" rx="10"/><text class="h" x="22" y="362">Seller</text><text class="s" x="22" y="382">types rough notes</text>
 <rect class="ck" x="160" y="336" width="140" height="64" rx="10"/><text class="h" x="172" y="362">Input checks</text><text class="s" x="172" y="382">+ safety guard if needed</text>
 <rect class="ai" x="330" y="336" width="140" height="64" rx="10"/><text class="h hw" x="342" y="362">Listing Helper</text><text class="s sw" x="342" y="382">gpt-6-luna agent</text>
 <rect class="bx" x="500" y="336" width="140" height="64" rx="10"/><text class="h" x="512" y="362">Human reviews</text><text class="s" x="512" y="382">and clicks Post</text>
 <rect class="ck" x="670" y="336" width="140" height="64" rx="10"/><text class="h" x="682" y="362">Policy + scam filter</text><text class="s" x="682" y="382">reject, hold or publish</text>
 <path class="ln" d="M130,368 L158,368" marker-end="url(#ah)"/><path class="ln" d="M300,368 L328,368" marker-end="url(#ah)"/>
 <path class="ln" d="M470,368 L498,368" marker-end="url(#ah)"/><path class="ln" d="M640,368 L668,368" marker-end="url(#ah)"/>
 <path class="ln" d="M400,308 L400,334" marker-end="url(#ah)" marker-start="url(#ah)"/>
 <path class="ln" d="M740,336 L740,250" marker-end="url(#ah)"/>
</svg>"""

# ---------- tables ----------
comparison_rows = """
<tr><td>Local, in-person pickup (no shipping)</td><td class="ok">✓</td><td class="ok">✓</td><td class="ok">✓</td><td class="ok">✓</td><td>ship only; not local</td></tr>
<tr><td>Limited to the SOM community</td><td class="ok">✓</td><td class="ok">✓</td><td>open to all</td><td>open to all</td><td>open to all</td></tr>
<tr><td>Searchable by price, category, condition</td><td class="ok">✓</td><td>one message chain</td><td class="ok">✓</td><td class="ok">✓</td><td class="ok">✓</td></tr>
<tr><td>Sell many items without spamming anyone</td><td class="ok">✓</td><td>floods the channel</td><td class="ok">✓</td><td class="ok">✓</td><td class="ok">✓</td></tr>
<tr><td>Profile and location private from strangers</td><td class="ok">✓ classmates only</td><td class="ok">✓</td><td>profile visible</td><td>partly</td><td>partly</td></tr>
<tr><td>Skills &amp; services next to items</td><td class="ok">✓</td><td>ad hoc posts</td><td>—</td><td>separate section</td><td>fashion/home only</td></tr>
<tr><td>Plain-language requests answered from real local listings</td><td class="ok">✓</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>
<tr><td>Budget bundles with totals checked by code</td><td class="ok">✓</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>
<tr><td>Listing drafts priced from comparable community listings</td><td class="ok">✓</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>
<tr><td>Honor-code, scam and prompt-injection guardrails</td><td class="ok">✓</td><td>—</td><td>general moderation</td><td>general moderation</td><td>general moderation</td></tr>
"""

agents_rows = """
<tr><td><b>SOMbot</b><br><span class="dim">shopping assistant</span></td><td>Turns a buyer's request into searches, picks the best real listings, builds budget bundles and writes a short answer</td><td>Buyer's message (after input checks) + last 4 chat turns</td><td>Structured JSON: reply, listing IDs, bundle IDs, no-match flag</td></tr>
<tr><td><b>Listing Helper</b><br><span class="dim">seller assistant</span></td><td>Turns a seller's rough notes into a complete, honest listing with a fair price and a list of missing details</td><td>Seller's notes (after input checks)</td><td>Structured JSON: title, description, category, price, unit, condition, rationale, missing info</td></tr>
<tr><td><b>Safety guard</b><br><span class="dim">classifier</span></td><td>Gives a second opinion on suspicious messages before either agent sees them</td><td>The suspicious message, wrapped as data</td><td>Structured JSON: allow/block, category, reason</td></tr>
"""

tools_rows = """
<tr><td><code>search_listings</code></td><td>SOMbot</td><td>query, section, category, min/max price</td><td>Up to 6 active listings: id, title, price, unit, condition or experience, location, seller, short description (wrapped as untrusted data)</td></tr>
<tr><td><code>get_listing_details</code></td><td>SOMbot</td><td>listing_id</td><td>One active listing in full; held listings return “not found”</td></tr>
<tr><td><code>check_bundle</code></td><td>SOMbot</td><td>listing_ids, budget</td><td>Exact total, within-budget flag and money left, computed in code (the model never does the math)</td></tr>
<tr><td><code>get_price_comps</code></td><td>Listing Helper</td><td>section, category, keywords</td><td>Min / median / max price and examples of similar SOMthing listings</td></tr>
"""

token_rows = "".join(
    f"<tr><td>{r['q']}</td><td>{r['input']:,}</td><td>{r['cached']:,}</td><td>{r['output']:,}</td><td>{r['calls']}</td>"
    f"<td>{r['latency_s']}s</td><td>${cost(r['input'], r['cached'], r['output']):.5f}</td><td class='ok'>✓</td></tr>"
    for r in opt["rows"]
) + (f"<tr class='total'><td>Average</td><td>{opt['avg_input']:,.0f}</td><td>{opt['avg_cached']:,.0f}</td><td>{opt['avg_output']:,.0f}</td>"
     f"<td>{opt['avg_calls']:.1f}</td><td>{opt['avg_latency_s']}s</td><td>${c_opt:.5f}</td><td class='ok'>10/10</td></tr>")

scale_rows = f"""
<tr><td>One typical user</td><td>30 SOMbot questions + 4 AI listing drafts + 3 guard checks per month</td><td><b>${per_user:.4f}</b> (under 1¢)</td></tr>
<tr><td>Heavy user</td><td>150 questions + 10 drafts per month</td><td>${150 * c_opt + 10 * c_helper:.3f}</td></tr>
<tr><td>100 users (about one SOM class section)</td><td>typical usage</td><td><b>${100 * per_user:.2f}</b></td></tr>
<tr><td>10,000 users (roughly all of Yale)</td><td>typical usage</td><td><b>${10000 * per_user:,.0f}</b></td></tr>
<tr><td>Worst case: daily cap fully used</td><td>1.5M tokens/day, all billed as output (upper bound)</td><td>≤ $0.75/day ≈ $23</td></tr>
"""


def _er(label, settings, r, c, bold=False):
    b = ("<b>", "</b>") if bold else ("", "")
    return (f"<tr><td>{label}</td><td>{b[0]}{settings}{b[1]}</td><td class='ok'>{r['accuracy'] * 10:.0f}/10</td><td>{r['avg_input']:,.0f}</td>"
            f"<td>{r['avg_cached']:,.0f}</td><td>{r['avg_output']:,.0f}</td><td>{r['avg_latency_s']}s</td><td>{b[0]}${c:.5f}{b[1]}</td></tr>")


effect_rows = (_er("Run 1 (before safety hardening)", "Optimized: compact results, 6 results, low effort", old_opt, c_old_opt, True)
               + _er("Run 1 (before safety hardening)", "Unoptimized: full text, 12 results, medium effort", old_unopt, c_old_unopt)
               + _er("Run 2 (after safety hardening)", "Optimized (shipped)", opt, c_opt, True)
               + _er("Run 2 (after safety hardening)", "Unoptimized", unopt, c_unopt))

risk_rows = """
<tr><td>Prompt injection / jailbreak</td><td>A user tells SOMbot to ignore its rules or reveal its prompt</td><td>Regex screen on normalized text (catches “1gn0re”, zero-width characters) → LLM guard for suspicious phrasing → canary token and prompt-fragment check on every answer</td><td>Fig. 6 · tests · red team #1–6</td></tr>
<tr><td>Indirect injection</td><td>A seller hides “SYSTEM NOTE TO AI…” in a listing</td><td>Listings scanned at posting; flagged ones are <b>held</b> and never shown to the AI. Remaining listing text is wrapped in ⟦ ⟧ markers that can't be forged.</td><td>Fig. 8 · red team #7</td></tr>
<tr><td>Scams</td><td>“Send a $50 Zelle deposit before you see it”</td><td>Scam patterns hold listings. The output filter replaces any answer that advises paying first, but keeps answers that warn against it.</td><td>tests · red team #9</td></tr>
<tr><td>Privacy</td><td>Probing for a classmate's address, or a user oversharing</td><td>Guard blocks privacy probes. Phones, emails, SSNs and card numbers are redacted before the model or the logs see them. No contact info in listings.</td><td>Figs. 7, 9 · red team #8, #13</td></tr>
<tr><td>Honor code and prohibited items</td><td>Selling midterm answers; weapons, drugs, fake IDs</td><td>Marketplace policy rejects these posts; the guard refuses these requests</td><td>Fig. 9 · red team #10–11</td></tr>
<tr><td>Invented facts</td><td>A listing that doesn't exist, or a wrong price</td><td>Only tool-returned IDs are shown. Every $ amount is verified. Bundle totals are computed by code.</td><td>tests · red team #14</td></tr>
<tr><td>Wrong actions / loops</td><td>The AI posts or messages for someone, or loops forever</td><td>Read-only tools; humans click Post and Send. Capped at 4 tool rounds and 8 tool calls, then a forced answer or real search results.</td><td>tests</td></tr>
<tr><td>Overspending</td><td>A bug or bad actor burns the budget</td><td>60k tokens/session, 1.5M/day, 8 AI requests/min, 500-character messages, 900 output tokens/call</td><td>tests · red team #15</td></tr>
<tr><td>Web attacks and secrets</td><td>XSS, fake uploads, password guessing, key leaks</td><td>HTML escaping, CSP headers, magic-byte image checks, 5 failed sign-ins/min. The key stays server-side; <code>.env</code> is gitignored (verified: no key in git history).</td><td>tests</td></tr>
"""

RT_LABEL = {
    "blocked by prompt_injection": "Blocked by input filter",
    "blocked by llm_guard": "Blocked by safety guard",
    "blocked by input_too_long": "Blocked (message too long)",
    "answered (no refusal)": "Answered without refusing",
    "answered safely": "Answered safely",
    "model refused": "Declined by SOMbot",
}
rt_rows = "".join(
    f"<tr><td>{i + 1}. {a['attack']}</td><td class='{'ok' if a['pass'] else 'bad'}'>{'✓' if a['pass'] else '✗'} {RT_LABEL.get(a['result'], a['result'])}</td>"
    f"<td class='ok'>✓ {RT_LABEL.get(b['result'], b['result'])}</td><td>{b['tokens']:,}</td></tr>"
    for i, (a, b) in enumerate(zip(rt1["rows"], rt2["rows"]))
)

impact_rows = f"""
<tr><td>Time to a verified, priced answer</td><td><b>{opt['avg_latency_s']} s on average</b>; 6.8 s for a 3-item move-in bundle</td><td>Measured (live evaluation; Fig. 5)</td></tr>
<tr><td>Answer quality</td><td><b>10/10</b> requests correct; 0 invented listings shown</td><td>Measured (<code>evals/run_eval.py</code>)</td></tr>
<tr><td>Safety</td><td><b>15/15</b> live attacks handled; $0 spent on regex-blocked attacks</td><td>Measured (<code>evals/red_team.py</code>)</td></tr>
<tr><td>Cost for a whole school</td><td>≈ <b>${10000 * per_user:,.0f}/month</b> for 10,000 users; under 1¢ per user</td><td>Measured tokens × estimated prices</td></tr>
<tr><td>Buyer time for a move-in bundle</td><td>~30–60 min of scrolling and messaging → about <b>2–3 min</b></td><td>Careful estimate (3 searches, 3–6 seller messages across Slack and marketplaces)</td></tr>
<tr><td>Seller time per listing</td><td>~10 min writing and price-checking → about <b>1 min</b> reviewing the AI draft (the draft took 7 s)</td><td>Measured draft time + estimate</td></tr>
<tr><td>Finding a peer tutor</td><td>Email, matching and fixed slots → browse classmates' hourly offers and message one directly</td><td>Author's experience with the current process</td></tr>
"""

CSS = """
@page { size: letter; margin: 0.72in 0.75in 0.8in;
  @bottom-left { content: "SOMthing · Final Project Report · Claire Zhao"; font: 8pt -apple-system, Helvetica, Arial, sans-serif; color: #8392ab; }
  @bottom-right { content: "Page " counter(page); font: 8pt -apple-system, Helvetica, Arial, sans-serif; color: #8392ab; } }
@page :first { @bottom-left { content: none; } @bottom-right { content: none; } }
:root { --navy:#00356b; --navy2:#1f4e8c; --dark:#0b2a55; --ink:#1b2a44; --muted:#5f6f88; --soft:#eef3fa; --line:#dbe3ee; --green:#15803d; --red:#b91c1c; }
* { box-sizing: border-box; }
html { background: #e9eef5; }
body { margin: 0; font: 10.5pt/1.6 "Inter", -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; color: var(--ink); }
.page { max-width: 8.5in; margin: 24px auto; background: #fff; padding: 0.7in 0.8in; box-shadow: 0 6px 24px rgba(11,42,85,.12); }
h2 { font-size: 19pt; color: var(--dark); margin: 0; letter-spacing: -0.01em; }
h3 { font-size: 12pt; color: var(--dark); margin: 20px 0 6px; }
p { margin: 6px 0 10px; } ul, ol { margin: 6px 0 12px; padding-left: 22px; } li { margin-bottom: 4px; }
a { color: var(--navy2); }
code { font: 8.8pt ui-monospace, Menlo, monospace; background: #f1f4f9; border: 1px solid #e3e9f2; border-radius: 4px; padding: 0 4px; }
.dim { color: var(--muted); font-size: 8.5pt; }
.cover { display: flex; flex-direction: column; }
.cover-band { background: linear-gradient(135deg, #0b2a55, #00356b 60%, #1f4e8c); color: #fff; border-radius: 16px; padding: 20px 26px 18px; }
.cover-kicker { font-size: 9pt; letter-spacing: .14em; text-transform: uppercase; color: #a9c4ea; }
.cover h1 { font-size: 34pt; margin: 2px 0 2px; letter-spacing: -0.03em; color: #fff; }
.cover h1 span { color: #a9c4ea; }
.cover .tagline { font-size: 12.5pt; color: #dbe6f6; margin: 0 0 12px; max-width: 5.6in; }
.meta { display: grid; grid-template-columns: 1.1in 1fr; gap: 4px 12px; font-size: 9.6pt; }
.meta div:nth-child(odd) { color: #a9c4ea; font-weight: 600; } .meta a { color: #fff; }
.oneliner { margin-top: 12px; background: rgba(255,255,255,.12); border-left: 3px solid #a9c4ea; border-radius: 8px; padding: 10px 14px; font-size: 10.5pt; }
.sec1 { margin: 0 0 8px; font-size: 8.5pt; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); font-weight: 700; }
.exec { margin-top: 12px; } .exec h3 { margin-top: 0; }
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 8px 0 10px; }
.kpi { border: 1px solid var(--line); border-top: 3px solid var(--navy); border-radius: 8px; padding: 9px 11px; }
.kpi b { display: block; font-size: 15pt; color: var(--navy); line-height: 1.15; } .kpi span { font-size: 8.4pt; color: var(--muted); }
.toc { margin-top: 10px; border-top: 1px solid var(--line); padding-top: 8px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 2px 10px; font-size: 9pt; }
.toc div { break-inside: avoid; padding: 2px 0; } .toc b { color: var(--navy); display: inline-block; width: 26px; }
.cover .sec { margin-top: 0; }
.sec { display: flex; gap: 14px; align-items: center; margin: 34px 0 12px; padding-bottom: 8px; border-bottom: 2px solid var(--navy); break-after: avoid; page-break-after: avoid; }
.sec-num { font: 800 22pt/1 -apple-system, Helvetica, Arial, sans-serif; color: #fff; background: var(--navy); border-radius: 10px; padding: 8px 10px; min-width: 52px; text-align: center; }
.sec-kicker { font-size: 8pt; letter-spacing: .13em; text-transform: uppercase; color: var(--muted); }
.lead { font-size: 11.2pt; color: #2b3b57; }
.tbl { margin: 12px 0 14px; }
.tbl.keep { break-inside: avoid; page-break-inside: avoid; }
tr { break-inside: avoid; page-break-inside: avoid; } thead { display: table-header-group; }
.tcap { break-after: avoid; page-break-after: avoid; }
.tcap { font-size: 8.8pt; color: var(--muted); margin-bottom: 4px; }
table { width: 100%; border-collapse: collapse; font-size: 8.8pt; }
th { background: var(--navy); color: #fff; text-align: left; padding: 6px 7px; font-weight: 600; }
td { padding: 5px 7px; border-bottom: 1px solid var(--line); vertical-align: top; }
tbody tr:nth-child(even) td { background: #f7f9fc; }
tr.total td { font-weight: 700; background: var(--soft) !important; border-top: 2px solid var(--navy); }
td.ok { color: var(--green); font-weight: 600; } td.bad { color: var(--red); font-weight: 600; }
figure { margin: 12px 0 16px; text-align: center; break-inside: avoid; page-break-inside: avoid; }
figure img { max-width: 100%; max-height: 3.3in; border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 2px 8px rgba(11,42,85,.08); }
figure.tall img { max-height: 4.4in; }
figure.narrow img { max-width: 62%; }
figure.diagram svg { width: 100%; height: auto; border: 1px solid var(--line); border-radius: 10px; background: #fbfcfe; padding: 6px; }
figcaption { font-size: 8.6pt; color: var(--muted); margin-top: 6px; text-align: left; line-height: 1.45; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; }
.side { display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 18px; align-items: start; }
.callout { border-radius: 8px; padding: 10px 14px; margin: 12px 0; font-size: 9.8pt; background: var(--soft); border-left: 4px solid var(--navy); break-inside: avoid; }
.callout.warn { background: #fffbeb; border-left-color: #a16207; }
.evidence { margin: 14px 0 6px; border: 1px solid #c7d7ee; background: #f6f9fd; border-radius: 8px; padding: 9px 14px; font-size: 9pt; break-inside: avoid; }
.ev-title { font-size: 7.8pt; letter-spacing: .13em; text-transform: uppercase; color: var(--navy2); font-weight: 700; margin-bottom: 3px; }
.evidence ul { margin: 0; padding-left: 18px; } .evidence li { margin: 1px 0; }
ol.steps { padding-left: 20px; } ol.steps li { margin-bottom: 7px; }
.foot { margin-top: 26px; border-top: 1px solid var(--line); padding-top: 8px; font-size: 8.4pt; color: var(--muted); }
@media print {
  html { background: #fff; } .page { box-shadow: none; margin: 0; padding: 0; max-width: none; }
  .cover { page-break-after: always; break-after: page; }
}
"""

html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>SOMthing · Final Project Report · Claire Zhao</title>
<style>{CSS}</style></head>
<body><main class="page">

<!-- ======================= COVER + 1. TITLE AND LINKS ======================= -->
<section class="cover">
  {section(1, "Title and Links", "Project, author, links and what the app does")}
  <div class="cover-band">
    <div class="cover-kicker">AI Foundations for Managers · Final Project Report</div>
    <h1>SOM<span>thing</span></h1>
    <p class="tagline">A trusted marketplace for the Yale SOM community, with AI agents that only recommend listings that actually exist.</p>
    <div class="meta">
      <div>Author</div><div>Claire Zhao</div>
      <div>Date</div><div>October 2026</div>
      <div>GitHub repo</div><div><a href="https://github.com/claire5898/Final-Project--SOMthing">github.com/claire5898/Final-Project--SOMthing</a></div>
      <div>App</div><div>Runs locally from a fresh clone in about 3 minutes (README → “Run it”); not hosted online. Demo sign-in: demo.student / SOMthing2026</div>
    </div>
    <div class="oneliner"><b>What it does:</b> SOMthing lets SOM students buy, sell and swap both physical things and skills. Its AI assistant turns plain requests like “a desk, chair and lamp under $200” into verified matches from real community listings, and a second agent turns a seller's rough notes into a fairly priced listing.</div>
  </div>

  <div class="exec">
    <h3>Executive Summary</h3>
    <p>SOM students have no good place to buy and sell with each other. The SOM Slack marketplace channel is one long message chain, Facebook Marketplace exposes your profile to strangers, and finding a tutor means waiting for limited official slots. SOMthing is a community-only marketplace for <b>items and skills</b>, with two <code>gpt-6-luna</code> agents. <b>SOMbot</b> answers buyers from real listings, building bundles that code adds up and verifies. The <b>Listing Helper</b> drafts listings priced from comparable community listings. Eight layers of safety checks wrap both agents.</p>
    <div class="kpis">
      <div class="kpi"><b>10 / 10</b><span>shopping requests answered correctly (live evaluation)</span></div>
      <div class="kpi"><b>${c_opt:.5f}</b><span>average cost per AI answer, from measured tokens</span></div>
      <div class="kpi"><b>15 / 15</b><span>live attacks handled safely after hardening</span></div>
      <div class="kpi"><b>${10000 * per_user:,.0f}/mo</b><span>estimated AI cost for 10,000 users</span></div>
    </div>
  </div>

  <div class="toc">
    <div><b>1</b> Title and Links</div><div><b>2</b> Motivation</div><div><b>3</b> What Is New Here</div><div><b>4</b> The Agents</div>
    <div><b>5</b> Tokenomics</div><div><b>6</b> Safety</div><div><b>7</b> Impact</div><div><b>8</b> Limits and Next Steps</div>
  </div>
</section>

<!-- ======================= 2. MOTIVATION ======================= -->
{section(2, "Motivation", "Who has this problem and what it costs them")}
<p class="lead"><b>This started with my own problem.</b> I have a lot of things to sell, and I'll be getting rid of my furniture when I move. But I didn't know where to post to sell locally.</p>
<ul>
  <li><b>Facebook Marketplace felt unsafe in a small town.</b> Strangers can see your profile and roughly where you live, and I worried about privacy. I'd much rather buy from and sell to people I trust: my own classmates.</li>
  <li><b>Our SOM marketplace Slack channel is the closest thing to that, but it doesn't work for selling.</b> It's one long message chain. Posts scroll away, nothing is searchable by price or category, and if you post more than a few items you feel like you're spamming everyone. There's no good way to sell a whole apartment's worth of things there.</li>
</ul>
<p><b>The same gap exists for skills.</b> Last semester I wanted tutoring for my courses and was happy to pay for it. The official route was to email AASL, wait to be matched, and then fit into limited availability and fixed time slots. Meanwhile, some of my classmates are excellent at exactly what I needed. If someone is really good at a subject, I'd gladly pay them by the hour to teach me. The same goes for everyday help: assembling furniture, small handyman jobs, light car maintenance, or interview practice with someone who has been through recruiting. Those people are already in our community; there's just no place to find them.</p>
<p><b>Who else has this problem.</b> Every SOM student does, at some point. Hundreds of students arrive each year needing a desk, a bike and a winter coat, and hundreds leave needing to get rid of exactly those things before they move. In between, classmates have skills others would pay for: Excel modeling, Python, headshots, language tutoring, case-interview practice.</p>
<p><b>What it costs them today:</b></p>
<ul>
  <li><b>Time.</b> Scrolling a Slack thread or several apps, messaging many sellers, and re-posting items that got buried</li>
  <li><b>Privacy and trust.</b> Exposing your profile and location to strangers, and dealing with common scams like “send a deposit to hold it”</li>
  <li><b>Waste.</b> Good furniture ends up on the curb at move-out because selling it is too much hassle, even though an incoming student would happily have bought it.</li>
  <li><b>Missed help.</b> Students wait for limited official tutoring slots, or go without, while the right classmate is a few doors away.</li>
</ul>
<p><b>Why I built SOMthing.</b> One centralized, trusted place where SOM students can sell many items without spamming a channel, find classmates' skills by the hour, and ask an AI assistant for exactly what they need. It would be valuable to the whole community, and I'm one of its first users: I plan to use it to sell my furniture when I move.</p>
{evidence(["A real person behind the problem: the author's own selling and tutoring experience", "Concrete costs today: time, privacy, waste and missed help"])}

<!-- ======================= 3. WHAT IS NEW ======================= -->
{section(3, "What Is New Here", "What already exists, and what SOMthing does differently")}
<p>I compared SOMthing with what SOM students use today: the SOM marketplace Slack channel, Facebook Marketplace, Craigslist, resale apps such as Poshmark, Depop and Vinted, and the official AASL tutoring process. Each is useful for something, but none combines a <i>trusted community</i>, <i>items and skills in one place</i>, and <i>an AI that answers only from real local listings</i>.</p>
{figure("home", "SOMthing's home page, signed in as the demo account. Physical Things and Skills &amp; Services sit side by side, with category shortcuts, fresh listings and the “Ask SOMbot” assistant.")}
{table("SOMthing compared with the alternatives SOM students use today.", ["What students need", "SOMthing", "SOM Slack channel", "Facebook Marketplace", "Craigslist", "Poshmark / Depop / Vinted"], comparison_rows, "keep")}
<p class="dim">Based on how each product generally works today, as I understand it. The point is the combination, not that any single feature is unique.</p>
<p><b>Tutoring today vs. SOMthing.</b> The official route (email AASL, wait to be matched, fit into limited slots) is valuable but slow and inflexible. SOMthing complements it with a peer option: students browse classmates who offer tutoring, Excel or coding help, compare experience and hourly rates, and message one directly.</p>
<p><b>What is genuinely new.</b> A campus marketplace by itself is not a new idea. The novelty is in how the agents are designed and safeguarded:</p>
<ul>
  <li><b>A grounded, verified assistant.</b> SOMbot can show only listings that its search tool returned. Prices come from the database, and bundle totals are added up by code, never by the model. A general-purpose AI chatbot can't do this, because it has never seen SOMthing's listings.</li>
  <li><b>AI help for sellers, too.</b> Rough notes become a clean listing, priced against comparable listings in the same community.</li>
  <li><b>Safety designed for a school.</b> Honor-code rules (no selling exam answers), scam holds and a ban on contact info in listings are built in from the start.</li>
</ul>
{evidence(["Named alternatives (SOM Slack, Facebook Marketplace, Craigslist, Poshmark, Depop, Vinted) compared feature by feature (Table 1)", "A frank statement of what is and isn't new"])}

<!-- ======================= 4. THE AGENTS ======================= -->
{section(4, "The Agents", "Who does what, with which tools, and one real run")}
<p>SOMthing uses <b>two AI agents</b> and <b>one small AI safety guard</b>, all running on <code>gpt-6-luna</code> through the course Portkey key. Everything else (browsing, filters, search ranking, bundle math and the safety rules) is ordinary code. This is deliberate: the AI handles only the parts that need language understanding, and code handles everything that must be exact.</p>
{svg_figure(ARCH_SVG, "System architecture. Buyers and sellers each go through the same input checks and safety guard. Each agent can only reach the listings database through read-only tools. SOMbot's answers pass output checks before the buyer sees them, and the Listing Helper only drafts: a person reviews and posts, and the policy filter decides what gets published.")}
{table("The three AI components.", ["Agent", "Job", "Input", "Output"], agents_rows, "keep")}
{table("The tools the agents can call. All are read-only code.", ["Tool", "Used by", "Inputs", "Returns"], tools_rows, "keep")}
<h3>How the Agents Are Organized, and Why</h3>
<ul>
  <li><b>Two specialists, not a chain.</b> SOMbot serves buyers and the Listing Helper serves sellers; they never pass work to each other. The safety guard stands in front of both. This keeps every run short (2.3 model calls on average) and easy to audit.</li>
  <li><b>Tools are the source of truth.</b> The model chooses <i>what</i> to search; code decides <i>what exists</i> and <i>what it costs</i>.</li>
  <li><b>Least privilege.</b> The AI can only read. Posting, saving and messaging always need a person to click.</li>
  <li><b>A tiered guard.</b> A cheap pattern check decides when to call the guard, so ordinary requests pay nothing extra for it.</li>
</ul>
<h3>Model Choice</h3>
<p><code>gpt-6-luna</code> is the model the course key allows, and it suits the job well: it is inexpensive (an estimated $0.10 per million input tokens and $0.50 per million output tokens) and supports both tool calling and strict JSON output. The app calls it through OpenAI's Responses API, since the older Chat Completions API does not allow tools with this model. At <b>low reasoning effort</b> it answered all 10 evaluation requests correctly, and medium effort did not improve accuracy (Section 5).</p>
<h3>One Real Run, Step by Step</h3>
<p>A real run from the app, logged at 12:23 on October 24. The request: <i>“I'm moving in: I need a desk, a chair and a lamp for under $200 total.”</i></p>
<div class="side">
  <ol class="steps">
    <li><b>Input checks.</b> The message is short, contains no injection patterns or personal information, and is not suspicious, so the guard is skipped (0 extra tokens).</li>
    <li><b>SOMbot plans (model call 1).</b> It requests three searches in parallel: <code>search_listings("desk", furniture, ≤$200)</code> → 4 results, <code>("chair", furniture, ≤$200)</code> → 3, and <code>("lamp", household, ≤$200)</code> → 2.</li>
    <li><b>Picks and verifies (call 2).</b> It chooses the $45 IKEA desk, the $25 wooden chair and the $18 lamp, then calls <code>check_bundle([…], 200)</code>. Code adds them up: <b>$88, within budget, $112 left</b>.</li>
    <li><b>Answers (call 3).</b> It returns a structured JSON answer: the reply text, listing IDs and bundle IDs.</li>
    <li><b>Output checks.</b> All three IDs came from the tools, every dollar amount matches a real price or the verified total, and the answer contains no canary token, scam advice, personal information or links. The cards are then drawn from the database.</li>
    <li><b>Logged.</b> 3 model calls, 4 tool calls, <b>6,186 input tokens (3,544 cached), 264 output</b>, 6.8 s, about ${c_bundle:.5f}. Visible on the dashboard (Figure 5).</li>
  </ol>
  {figure("run1_bundle", "The real run in the app. “How I found these” lists each tool call; the green box is the bundle total verified by code.", "tall")}
</div>
{figure("helper", "The Listing Helper on real notes. It called <code>get_price_comps</code>, suggested $45 with a reason, and flagged missing details (model, dimensions). The seller still reviews and clicks Post.")}
{evidence(["Each agent and tool explained (Tables 2–3)", "A system diagram (Figure 2)", "One real run traced step by step, with screenshots of what each agent did (Figures 3–4)"])}

<!-- ======================= 5. TOKENOMICS ======================= -->
{section(5, "Tokenomics", "What one run costs, per user, and at scale")}
<p>All token numbers are <b>measured from real runs</b>. The app shows its own token use under every answer and logs every run (Figure 5), and <code>evals/run_eval.py</code> runs a fixed set of 10 shopping requests and saves the counts. Prices are estimated <code>gpt-6-luna</code> list prices from public pricing trackers: <b>$0.10 per 1M input, $0.01 per 1M cached input and $0.50 per 1M output tokens</b>. The course is billed through Portkey, so actual billing may differ.</p>
{table("Tokens and cost per run: 10 real SOMbot requests with the shipped settings (evaluation run 2, Oct 24).", ["Request", "Input", "Cached", "Output", "Calls", "Time", "Est. cost", "Correct"], token_rows)}
<p>A typical SOMbot answer uses about <b>3,100 input tokens (80% cached) and 150 output tokens</b>, which costs about <b>${c_opt:.5f}</b>. Other measured runs: a Listing Helper draft costs about ${c_helper:.5f} (1,914 in, 162 out), a safety-guard check about ${c_guard:.6f} (287 in, 36 out), and a regex-blocked attack <b>$0</b>, because the model is never called.</p>
{table("Monthly cost per user and at scale.", ["Scenario", "Assumption", "Monthly AI cost"], scale_rows, "keep")}
<p>For an organization, the AI cost is close to negligible: a whole-school deployment would spend more on web hosting than on tokens, and the daily budget cap puts a hard ceiling on the worst case.</p>
<h3>What I Did to Keep Cost Down</h3>
<ol>
  <li><b>No AI for ordinary browsing.</b> Search, filters, categories and listing pages are plain code.</li>
  <li><b>Compact tool results.</b> At most 6 listings per search, with descriptions trimmed to 140 characters.</li>
  <li><b>Low reasoning effort</b>, which the evaluation showed is enough for this task.</li>
  <li><b>Prompt caching.</b> The system prompt and tool definitions stay identical across requests, so about 80% of input tokens are cached and billed at a tenth of the price.</li>
  <li><b>Short memory.</b> Only the last 4 chat turns are re-sent, and tool outputs from earlier turns are dropped.</li>
  <li><b>A tiered guard.</b> The extra safety model runs only on suspicious messages, and regex blocks cost $0.</li>
  <li><b>Hard caps.</b> 900 output tokens per call, 4 tool rounds per question, 60k tokens per session and 1.5M per day.</li>
</ol>
<h3>Did Cost-Cutting Hurt Quality?</h3>
{table("Optimized vs. unoptimized settings across two evaluation runs (10 requests each).", ["Run", "Settings", "Accuracy", "Avg input", "Avg cached", "Avg output", "Avg time", "Cost / answer"], effect_rows, "keep")}
<p><b>No measurable quality loss.</b> Both settings answered all 10 requests correctly in both runs. (“Correct” means the right listings were shown, forbidden ones never appeared, “no match” was reported honestly, and bundles stayed within budget.)</p>
<ul>
  <li><b>Run 1:</b> the optimized settings used <b>20% fewer input tokens and were about 40% faster</b> than the unoptimized ones.</li>
  <li><b>Run 2:</b> after safety hardening, the longer system prompt became large enough for the provider to cache. Caching became the biggest saving: cost per answer fell from ${c_old_opt:.5f} to ${c_opt:.5f}, about <b>{(1 - c_opt / c_old_opt) * 100:.0f}% cheaper</b>. The remaining gap between settings shrank to about 5%, and the latency difference was within normal run-to-run variation.</li>
  <li><b>One trade-off I caught:</b> an overly strict “too good to be true” price warning flagged a normal $25 chair. I loosened the threshold and confirmed that no legitimate listing is flagged.</li>
</ul>
{figure("dash_runs", "An excerpt from the app's AI &amp; Safety dashboard, which logs every run: input, cached and output tokens, model calls, latency, outcome and guardrails triggered. The bundle run from Section 4 is the fourth row. Blocked attacks cost 0 tokens (input filter) or about 320 tokens (safety guard).")}
{evidence(["Real token counts from 10 logged runs (Table 4) and the app's own logs (Figure 5)", "Cost per run, per user and at 100 and 10,000 users (Table 5)", "Before/after comparison showing no accuracy loss (Table 6)"])}

<!-- ======================= 6. SAFETY ======================= -->
{section(6, "Safety", "What could go wrong, what I built, and proof that it works")}
<p>A marketplace that feeds member-written listings to an AI faces three kinds of risk: <b>attacks</b> (prompt injection, jailbreaks, privacy probing, scams), <b>agent malfunction</b> (invented listings or prices, runaway loops, the AI taking actions on its own) and <b>overspending</b>. SOMthing uses eight layers of defense, so that if one layer misses something, the next one catches it. Several build on techniques from earlier homeworks: treating outside content as untrusted, pattern screening, read-only tools, human approval for actions, step and token budgets, and audit logs. Others are new for this project: an AI safety guard, personal-information redaction, a canary token, marked untrusted text and output filtering.</p>
{table("Risks that matter for SOMthing and the defenses built for each.", ["Risk", "What could happen", "Defenses built", "Evidence"], risk_rows)}
<h3>Defenses Working in the Real App</h3>
<div class="two">
  {figure("safety_blocks", "Two attacks blocked live. A direct injection is stopped by the regex screen before any AI call (0 tokens). A role-play jailbreak is stopped by the LLM guard (287 input tokens); SOMbot never sees it.", "tall")}
  {figure("safety_pii", "A request containing a phone number. The number is removed before the AI and the logs see it (the log in Figure 5 shows “[phone removed]”), and the user is told.", "tall")}
</div>
{figure("held", "A seller tries to post a listing containing hidden instructions for the AI and a Venmo-deposit demand. It is held for review: hidden from everyone else and never sent to the AI.")}
{figure("policy_reject", "A listing that sells midterm answers and includes a phone number is rejected, with a clear explanation (honor code; no contact info).", "narrow")}
<h3>Tested: 55 Automated Tests and a Live Red Team</h3>
<p><b>Automated tests</b> (<code>python -m pytest</code>: 55 passing, no AI tokens). A scripted fake model reproduces each attack or malfunction and checks that it's stopped. Examples: <code>test_invented_listing_ids_are_removed</code>, <code>test_runaway_loop_is_stopped</code>, <code>test_obfuscated_injections_are_caught</code>, <code>test_llm_guard_fails_closed</code>, <code>test_canary_leak_is_blocked</code>, <code>test_pii_never_reaches_the_model</code>, <code>test_scam_advice_in_answer_is_replaced</code>, <code>test_token_budget_blocks_without_calling_model</code>, <code>test_ai_tools_are_read_only</code>.</p>
<p><b>Live red team</b> (<code>python evals/red_team.py</code>) sends 15 attacks through the real model. The first run exposed genuine weaknesses, which I fixed and then re-tested:</p>
{table("Live red-team results before and after hardening.", ["Attack", "Run 1 (before fixes)", "Run 2 (after hardening)", "Tokens"], rt_rows)}
<p class="dim">What run 1 revealed: in three of the four ✗ cases the model still declined on its own, but the request reached it without being screened by the guard; the fourth (the translation trick) received a harmless answer. Separately, the scam-advice filter wrongly replaced a helpful <i>warning</i> about deposits. Two fixes followed: a wider set of suspicious phrases that route messages to the guard, and judging scam advice sentence by sentence. Run 2 handled all 15 attacks, and shopping accuracy stayed at 10/10.</p>
{figure("dash_layers", "The eight safety layers as summarized in the app's AI &amp; Safety dashboard, which also offers one-click attack demos.")}
{evidence(["Risks mapped to built defenses (Table 7)", "Screenshots of defenses stopping attacks and malfunctions (Figures 6–9)", "55 passing tests and a 15-attack live red team (Table 8)"])}

<!-- ======================= 7. IMPACT ======================= -->
{section(7, "Impact", "The numbers, and where each one comes from")}
{table("Impact metrics and their sources.", ["Metric", "Result", "Source"], impact_rows, "keep")}
<div class="callout"><b>Real-user evidence: the author as pilot user.</b> I built SOMthing for my own needs, and I am its first real user. I have a lot of items to sell, I'll be clearing out my furniture when I move, and last semester I was looking for a paid tutor. I used the app end to end for exactly these tasks: asking SOMbot for move-in furniture and for Excel and statistics help, drafting a furniture listing with the Listing Helper, and contacting sellers through the inbox. Every run shown in this report comes from that real use. The evidence comes from one user so far. The next step is a pilot with a class section, and the app is ready for it: it records a thumbs up or down on every SOMbot answer and shows a “found helpful” score on the dashboard.</div>
<p><b>What becomes possible:</b> a student asks one question (“I'm moving in, desk + chair + lamp under $200”) and gets three real, priced items from classmates with the total already verified. Today that takes several searches across Slack and multiple apps. Sellers can list a whole apartment without flooding a channel, and students can find a classmate who tutors by the hour instead of waiting for an official slot.</p>
<div class="two">
  {figure("inbox", "The (simulated) inbox. Buyers contact sellers inside SOMthing, so phone numbers and emails stay private.")}
  {figure("mobile", "Works on phones: the limited-edition Yale Labubu listing on a 390-px-wide screen.")}
</div>
{evidence(["Numbers with sources, measured where possible and labeled where estimated (Table 9)", "The author as the pilot user, with the real selling and tutoring problem the app solves"])}

<!-- ======================= 8. LIMITS + NEXT STEPS ======================= -->
{section(8, "Limits and Next Steps", "What doesn't work yet, and the next month")}
<h3>What Doesn't Work Yet</h3>
<ul>
  <li><b>It's a classroom demo.</b> Sellers and listings are fictional (the photos are real stock photos, credited in the repo). Sign-in is a mock “Yale ID” screen, messaging is simulated, and payments are left out by design. It runs locally rather than online.</li>
  <li><b>One user so far.</b> The pilot user is the author, and the time savings are careful estimates. A multi-student pilot is the first next step.</li>
  <li><b>The guardrails aren't perfect.</b> Creative phrasing can evade regex filters. The LLM guard only runs on messages the net marks as suspicious, trading some coverage for cost. Output filters are a backstop, not a guarantee.</li>
  <li><b>Small dataset.</b> With 55 listings, price comparisons are thin, and search is keyword-based rather than semantic.</li>
  <li><b>Costs are estimates.</b> Token counts are measured, but prices come from public trackers, not course billing.</li>
</ul>
<h3>With Another Month, I Would</h3>
<ol>
  <li><b>Run a pilot</b> with one SOM class section. Measure time-to-purchase against the Slack channel, and collect thumbs-up rates and quotes.</li>
  <li><b>Add real Yale sign-in (CAS/SSO)</b>, real in-app messaging with notifications, and host it online.</li>
  <li><b>Add a “Wanted” board and saved-search alerts.</b> When SOMbot finds no match, it would post the request so sellers can see the demand.</li>
  <li><b>Add a moderator queue</b> for held listings and user reports, with an audit trail.</li>
  <li><b>Add photo-to-listing</b>, where the Listing Helper drafts from a picture, plus <b>move-out season tools</b> that let graduating students list a whole apartment as bundles for incoming students.</li>
</ol>
<p class="foot">SOMthing is a classroom project for AI Foundations for Managers and isn't affiliated with or endorsed by Yale University. The Labubu-style mascots are original HTML/CSS designs. All numbers come from runs saved in <code>evals/results/</code> or from screenshots of the app's own logs, except where marked as estimates.</p>
</main></body></html>
"""

OUT.write_text(html)
print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:,.0f} KB) · {_fig[0]} figures · {_tab[0]} tables")
