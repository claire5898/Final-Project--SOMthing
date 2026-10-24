"""Build slides.html: a reveal.js deck (loaded from a CDN) with every image embedded.

Run from the repo root:  python docs/build_slides.py
Numbers come from the same evals/results/*.json files as the report.
"""

import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "report_images"
OUT = ROOT / "slides.html"
REVEAL = "https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist"

P_IN, P_CACHED, P_OUT = 0.10, 0.01, 0.50


def cost(i, c, o):
    return ((i - c) * P_IN + c * P_CACHED + o * P_OUT) / 1e6


def img(name, cls=""):
    data = base64.b64encode((IMG / f"{name}.jpg").read_bytes()).decode()
    return f'<img class="{cls}" src="data:image/jpeg;base64,{data}" alt="{name}" />'


ev_new = json.loads((ROOT / "evals/results/eval_20261024_120407.json").read_text())["results"]
ev_old = json.loads((ROOT / "evals/results/eval_20261024_104221.json").read_text())["results"]
opt = ev_new["optimized"]
c_opt = cost(opt["avg_input"], opt["avg_cached"], opt["avg_output"])
c_old = cost(ev_old["optimized"]["avg_input"], ev_old["optimized"]["avg_cached"], ev_old["optimized"]["avg_output"])
per_user = 30 * c_opt + 4 * cost(1914, 0, 162) + 3 * cost(287, 0, 36)

# Reuse the architecture diagram from the report so both stay identical.
report_src = (ROOT / "docs" / "build_report.py").read_text()
ARCH_SVG = re.search(r'ARCH_SVG = """(.*?)"""', report_src, re.S).group(1)

CSS = """
:root { --navy:#00356b; --navy2:#1f4e8c; --dark:#0b2a55; --ink:#1f2a3c; --muted:#6b6457; --soft:#efe6d6; --line:#e2d7c4; --paper:#fffdf8; --beige:#f6f0e4; --green:#2f7a3d; }
.reveal-viewport { background: var(--beige) !important; }
.reveal { font-family: -apple-system, "Segoe UI", Inter, Helvetica, Arial, sans-serif; color: var(--ink); font-size: 30px; }
.reveal .slides { text-align: left; }
.reveal .slides section { height: 100%; padding: 0; }
.reveal h1, .reveal h2, .reveal h3 { font-family: inherit; color: var(--dark); text-transform: none; letter-spacing: -0.02em; }
.reveal h2 { font-size: 1.55em; margin: 0 0 6px; }
.reveal p, .reveal li { line-height: 1.4; }
.kicker { font-size: .5em; letter-spacing: .16em; text-transform: uppercase; color: var(--navy2); font-weight: 700; margin-bottom: 4px; }
.sub { font-size: .72em; color: var(--muted); margin: 0 0 18px; }
.bar { position: absolute; left: 0; right: 0; bottom: -30px; display: flex; justify-content: space-between; font-size: .38em; color: #8a9bb5; }
/* title */
section.title-slide { color: #fff; }
.title-wrap { display: grid; grid-template-columns: 1.05fr .95fr; gap: 40px; align-items: center; height: 100%; }
.title-wrap h1 { color: #fff; font-size: 3.3em; margin: 0; letter-spacing: -0.03em; }
.title-wrap h1 span { color: #a9c4ea; }
.pitch { font-size: .92em; color: #dbe6f6; margin: 14px 0 24px; line-height: 1.35; }
.who { font-size: .6em; color: #a9c4ea; line-height: 1.6; }
.who b { color: #fff; }
.shot { border-radius: 14px; box-shadow: 0 18px 40px rgba(0,0,0,.35); border: 1px solid rgba(255,255,255,.25); }
.reveal img { margin: 0; max-width: 100%; }
/* cards */
.cards { display: grid; gap: 18px; }
.c3 { grid-template-columns: repeat(3, 1fr); } .c4 { grid-template-columns: repeat(4, 1fr); } .c2 { grid-template-columns: 1fr 1fr; }
.card { background: var(--paper); border: 1px solid var(--line); border-top: 5px solid var(--navy); border-radius: 12px; padding: 20px 22px; font-size: .74em; line-height: 1.4; }
.card h3 { font-size: 1.25em; margin: 0 0 6px; }
.card ul { margin: 0; padding-left: 1.1em; } .card li { margin: 8px 0; }
.quote { margin-top: 20px; background: var(--soft); border-left: 6px solid var(--navy); border-radius: 10px; padding: 18px 24px; font-size: .74em; font-style: italic; color: #2b3b57; }
.quote b { font-style: normal; color: var(--dark); }
/* table */
table.cmp { width: 100%; border-collapse: collapse; font-size: .68em; }
table.cmp th { background: var(--navy); color: #fff; padding: 9px 10px; text-align: center; font-weight: 600; border: none; }
table.cmp th:first-child, table.cmp td:first-child { text-align: left; }
table.cmp td { padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: center; }
table.cmp td { background: var(--paper); }
table.cmp tr:nth-child(even) td { background: #f9f4ea; }
td.y { color: var(--green); font-weight: 800; } td.txt { font-size: .85em; color: #4a4336; } td.n { color: #c4b9a6; } td.som { background: #e9eef6 !important; }
.pill { display: inline-block; background: var(--paper); border: 1px solid var(--line); color: var(--dark); border-radius: 999px; padding: 8px 16px; font-size: .6em; margin: 18px 8px 0 0; }
.pill b { color: var(--navy); }
/* diagram */
.diagram svg { width: 100%; height: 500px; border: 1px solid var(--line); border-radius: 12px; background: var(--paper); padding: 6px; }
.note { font-size: .6em; color: var(--muted); margin-top: 12px; }
/* demo */
.demo { display: grid; grid-template-columns: auto 1fr; gap: 30px; align-items: start; }
.demo .tallimg { max-height: 540px; width: auto; }
.demo .wideimg { max-height: 410px; width: auto; }
.demo img { border: 1px solid var(--line); border-radius: 10px; box-shadow: 0 6px 18px rgba(11,42,85,.12); }
.cap { font-size: .52em; color: var(--muted); margin-top: 6px; }
.steps { font-size: .62em; margin: 10px 0 0; padding-left: 1.2em; } .steps li { margin: 8px 0; }
/* numbers */
.big { font-size: 2.1em; font-weight: 800; color: var(--navy); line-height: 1.05; display: block; margin-bottom: 4px; letter-spacing: -0.02em; }
.stat { background: var(--paper); border: 1px solid var(--line); border-radius: 12px; padding: 20px 22px; font-size: .64em; line-height: 1.4; color: var(--muted); }
.stat b { color: var(--dark); }
.stat.dark { background: var(--navy); border-color: var(--navy); color: #c9d8ee; } .stat.dark .big { color: #fff; }
.split { display: grid; grid-template-columns: 1.1fr .9fr; gap: 28px; align-items: start; }
ul.tight { font-size: .7em; margin: 0; padding-left: 1.1em; } ul.tight li { margin: 10px 0; }
.layers { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.safeimg { max-height: 540px; width: auto; display: block; margin: 0 auto; border: 1px solid var(--line); border-radius: 10px; }
.layer { background: var(--soft); border-left: 5px solid var(--navy); border-radius: 8px; padding: 10px 13px; font-size: .54em; line-height: 1.3; }
.layer b { color: var(--dark); display: block; font-size: 1.12em; }
.rt { display: flex; align-items: center; gap: 14px; margin-top: 12px; }
.rt .from { font-size: 1.4em; font-weight: 800; color: #b91c1c; } .rt .to { font-size: 1.4em; font-weight: 800; color: var(--green); }
.rt span { font-size: .58em; color: var(--muted); }
.reveal .progress { color: var(--navy); }
.foot { position: absolute; left: 0; right: 120px; bottom: -18px; display: flex; justify-content: space-between; font-size: 13px; color: #9a8f7c; letter-spacing: .04em; }
.reveal img { background: #fff; }
/* ===== classic polished overrides ===== */
.reveal h1, .reveal h2, .reveal h3 { font-family: Georgia, "Times New Roman", serif; letter-spacing: 0; font-weight: 700; }
.reveal h2 { font-size: 1.4em; padding-bottom: 10px; border-bottom: 2px solid var(--navy); margin-bottom: 14px; }
.kicker { font-family: Georgia, serif; font-variant: small-caps; text-transform: lowercase; letter-spacing: .08em; font-size: .62em; color: #8a7a5c; font-weight: 400; }
.sub { font-style: italic; font-family: Georgia, serif; margin-bottom: 14px; }
.card, .stat, .layer, .quote, .pill, table.cmp, .diagram svg, .reveal img, .shot, .demo img, .safeimg, .rowimg { border-radius: 2px !important; box-shadow: none !important; }
.card { border: 1px solid var(--line); border-top: 3px solid var(--navy); padding: 16px 20px; }
.card h3 { font-size: 1.12em; border-bottom: 1px solid var(--line); padding-bottom: 6px; margin-bottom: 8px; }
.stat { border: 1px solid var(--line); border-top: 3px solid var(--navy); }
.stat.dark { border-top-color: #c9a227; }
.big { font-family: Georgia, serif; font-weight: 700; letter-spacing: 0; }
.quote { border-left: 3px solid #c9a227; background: var(--paper); font-family: Georgia, serif; }
.pill { background: transparent; border: none; padding: 0; margin: 14px 26px 0 0; font-size: .6em; }
.pill b::before { content: "■ "; color: #c9a227; font-size: .8em; }
.layer { border-left: 3px solid var(--navy); background: var(--paper); border-top: 1px solid var(--line); border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.layer b { font-family: Georgia, serif; }
.rt .from, .rt .to { font-family: Georgia, serif; }
table.cmp th { font-weight: 600; letter-spacing: .02em; }
.reveal .safeimg { max-height: 455px; }
.reveal .demo .tallimg { max-height: 510px; }
.reveal .demo .wideimg { max-height: 380px; }
.reveal .diagram svg { height: 470px; }
.title-wrap h1 { font-family: Georgia, serif; font-size: 3.1em; }
.title-rule { width: 90px; height: 3px; background: #c9a227; margin: 16px 0 4px; }
.pitch { font-family: Georgia, serif; font-style: italic; }

.shots-row { display: flex; gap: 18px; margin-top: 16px; align-items: flex-start; }
.reveal .rowimg { max-height: 260px; width: auto; border: 1px solid var(--line); border-radius: 10px; }
.reveal .slide-number { background: transparent; color: #8a9bb5; font-size: 14px; }
"""

S = []

# 1. Title
S.append(f"""
<section class="title-slide" data-background-color="#0b2a55">
 <div class="title-wrap">
  <div>
   <div class="kicker" style="color:#a9c4ea">AI Foundations for Managers · Final Project</div>
   <h1>SOM<span>thing</span></h1>
   <div class="title-rule"></div>
   <p class="pitch">A trusted marketplace where SOM students buy, sell and swap <b>items and skills</b>, with AI agents that only recommend listings that actually exist.</p>
   <div class="who"><b>Claire Zhao</b> · October 2026<br/>github.com/claire5898/Final-Project--SOMthing</div>
  </div>
  <div>{img("home", "shot")}</div>
 </div>
<aside class="notes">Hi, I'm Claire. SOMthing is a trusted marketplace for the SOM community, for items and skills, with AI agents that only recommend listings that actually exist.</aside>
</section>""")

# 2. Problem
S.append("""
<section>
 <div class="foot"><span>SOMthing · Claire Zhao</span><span>AI Foundations for Managers · Final Project</span></div>
 <div class="kicker">The problem</div>
 <h2>SOM students have nowhere good to buy and sell with each other</h2>
 <p class="sub">I ran into all three of these myself.</p>
 <div class="cards c3">
  <div class="card"><h3>Selling is awkward</h3><ul>
    <li>Facebook Marketplace shows my profile and location to strangers</li>
    <li>The SOM Slack channel is one long message chain: no search, and posting many items feels like spam</li></ul></div>
  <div class="card"><h3>Skills are invisible</h3><ul>
    <li>Getting a tutor meant emailing AASL, waiting to be matched and fitting into limited slots</li>
    <li>Classmates who are great at Excel, coding, interviews or repairs have no place to offer it</li></ul></div>
  <div class="card"><h3>It costs everyone</h3><ul>
    <li><b>Time</b> scrolling and messaging</li><li><b>Privacy and scam</b> risk with strangers</li>
    <li><b>Waste</b>: furniture left on the curb at move-out</li></ul></div>
 </div>
 <div class="quote">“I have a lot to sell and furniture to clear when I move, and I'd gladly pay a classmate by the hour to tutor me. I wanted one trusted place for both.” <b>— Claire, SOMthing's first user</b></div>
<aside class="notes">I built SOMthing because I had this problem myself. I have a lot to sell and furniture to clear when I move, but Facebook Marketplace exposes my profile to strangers, and our SOM Slack channel is one long message chain where posting many items feels like spam. Last semester I also wanted a paid tutor, and the AASL process meant waiting to be matched into limited slots.</aside>
</section>""")

# 3. What is new
COMP = json.loads((ROOT / "data" / "comparison.json").read_text())


def _cell(v, k):
    if v == "yes":
        return '<td class="y som">✓</td>' if k == 0 else '<td class="y">✓</td>'
    if v == "no":
        return '<td class="n">—</td>'
    return f'<td class="txt">{v}</td>'


tr = "".join("<tr><td>" + r[0].replace("&", "&amp;") + "</td>" + "".join(_cell(v, k) for k, v in enumerate(r[1:])) + "</tr>" for r in COMP["rows"])
head = "".join(f"<th>{c}</th>" for c in COMP["columns"])
S.append(f"""
<section>
 <div class="foot"><span>SOMthing · Claire Zhao</span><span>AI Foundations for Managers · Final Project</span></div>
 <div class="kicker">What is new</div>
 <h2>A trusted community + items and skills + an AI that can't make things up</h2>
 <table class="cmp"><tr><th>What students need</th>{head}</tr>{tr}</table>
 <span class="pill"><b>Grounded:</b> only listings the search tool returned</span>
 <span class="pill"><b>Verified:</b> prices and totals come from code</span>
 <span class="pill"><b>Built for school:</b> honor code + scam rules</span>
<aside class="notes">Each existing tool solves part of this. Slack is trusted but unsearchable, Facebook Marketplace is searchable but open to strangers, and Craigslist is local but open to anyone, and resale apps like Poshmark, Depop and Vinted aren't local: everything ships. SOMthing combines a trusted community, items and skills, and an AI that can only answer from real listings, with code checking every price and total.</aside>
</section>""")

# 4. Agents
S.append(f"""
<section>
 <div class="foot"><span>SOMthing · Claire Zhao</span><span>AI Foundations for Managers · Final Project</span></div>
 <div class="kicker">How the agents work</div>
 <h2>Two gpt-6-luna agents behind one set of safety checks</h2>
 <div class="diagram">{ARCH_SVG}</div>
 <p class="note"><b>SOMbot</b> turns a buyer's request into searches and verified answers. <b>Listing Helper</b> turns a seller's notes into a priced draft. A small <b>safety guard</b> screens suspicious messages first. Tools are read-only; the AI never posts or sends.</p>
<aside class="notes">There are two agents on gpt-6-luna. SOMbot helps buyers and the Listing Helper helps sellers. Both sit behind the same input checks and a small safety guard. Their tools are read-only code over the listings database, so the AI chooses what to search but code decides what exists and what it costs. The AI never posts or sends anything.</aside>
</section>""")

# 5. Demo
S.append(f"""
<section>
 <div class="foot"><span>SOMthing · Claire Zhao</span><span>AI Foundations for Managers · Final Project</span></div>
 <div class="kicker">Demo · one real run</div>
 <h2>“I'm moving in: desk, chair and lamp under $200”</h2>
 <div class="demo">
  <div>{img("run1_bundle", "tallimg")}<div class="cap">SOMbot's answer with its tool trace</div></div>
  <div>
   {img("helper", "wideimg")}<div class="cap">The Listing Helper drafting a priced listing from rough notes</div>
   <ol class="steps">
    <li>Three parallel searches: desk → 4, chair → 3, lamp → 2 results</li>
    <li><code>check_bundle</code> adds it up in code: <b>$88, $112 under budget</b></li>
    <li>Output checks pass; cards drawn from the database · 6.8 s · 3 model calls</li>
   </ol>
  </div>
 </div>
<aside class="notes">This is a real run. I asked for a desk, chair and lamp under $200. SOMbot ran three searches in parallel, picked one listing for each item, and called check_bundle, which added the total in code: $88. Output checks confirmed every ID and price before the cards appeared. On the right, the Listing Helper drafted a priced listing from my rough notes.</aside>
</section>""")

# 6. Cost
S.append(f"""
<section>
 <div class="foot"><span>SOMthing · Claire Zhao</span><span>AI Foundations for Managers · Final Project</span></div>
 <div class="kicker">Cost to run</div>
 <h2>Under a cent per user per month</h2>
 <p class="sub">Measured token counts × estimated gpt-6-luna prices ($0.10 / $0.01 cached / $0.50 per 1M tokens).</p>
 <div class="cards c4">
  <div class="stat dark"><span class="big">${c_opt:.5f}</span>per SOMbot answer<br/>≈3,100 input (80% cached) + 150 output tokens</div>
  <div class="stat"><span class="big">${per_user:.3f}</span><b>per user / month</b><br/>30 questions + 4 drafts</div>
  <div class="stat"><span class="big">${100 * per_user:.2f}</span><b>100 users / month</b><br/>about one class section</div>
  <div class="stat"><span class="big">${10000 * per_user:,.0f}</span><b>10,000 users / month</b><br/>roughly all of Yale</div>
 </div>
 <div class="split" style="margin-top:28px">
  <ul class="tight">
   <li><b>No AI for browsing</b>: search and filters are plain code</li>
   <li><b>Compact tool results</b> + <b>low reasoning effort</b></li>
   <li><b>Prompt caching</b>: 80% of input tokens cached</li>
   <li><b>Hard caps</b>: 60k tokens/session, 1.5M/day</li>
  </ul>
  <div class="stat"><span class="big" style="font-size:1.5em">{(1 - c_opt / c_old) * 100:.0f}% cheaper</span>per answer after optimization (${c_old:.5f} → ${c_opt:.5f}), with accuracy unchanged at <b>10/10</b></div>
 </div>
<aside class="notes">Every number here comes from measured token counts. A typical answer costs about $0.00016, which is under a cent per user per month, or about $61 a month for 10,000 users. The biggest savings came from prompt caching, compact tool results and low reasoning effort, and accuracy stayed at 10 out of 10.</aside>
</section>""")

# 7. Safety
S.append(f"""
<section>
 <div class="foot"><span>SOMthing · Claire Zhao</span><span>AI Foundations for Managers · Final Project</span></div>
 <div class="kicker">Safety</div>
 <h2>Eight layers, proven against real attacks</h2>
 <div class="split">
  <div>
   <div class="layers">
    <div class="layer"><b>1 · Input checks</b>injection patterns, obfuscation, PII redaction</div>
    <div class="layer"><b>2 · AI safety guard</b>second opinion on suspicious messages</div>
    <div class="layer"><b>3 · Untrusted data</b>scam/injection listings held from the AI</div>
    <div class="layer"><b>4 · Least privilege</b>read-only tools; humans post and send</div>
    <div class="layer"><b>5 · Output checks</b>real IDs, verified prices, canary token</div>
    <div class="layer"><b>6 · Spend limits</b>token budgets, rate and step limits</div>
    <div class="layer"><b>7 · Marketplace policy</b>honor code, no weapons/drugs/contact info</div>
    <div class="layer"><b>8 · App security</b>key server-side, CSP, upload checks</div>
   </div>
   <div class="rt"><div class="from">11/15</div><div style="font-size:.9em">→</div><div class="to">15/15</div>
    <span>live red-team attacks handled, before → after fixes<br/><b style="color:var(--dark)">55 automated tests</b> passing</span></div>
  </div>
  <div>{img("safety_blocks", "safeimg")}<div class="cap">An injection blocked before the AI (0 tokens) and a jailbreak stopped by the guard</div></div>
 </div>
<aside class="notes">Because members write the listings, injection and scams are real risks. There are eight layers, and I tested them live: the first red-team run handled 11 of 15 attacks, I fixed the gaps, and the second run handled all 15. There are also 55 automated tests. On the right, one attack is blocked before reaching the AI, and a jailbreak is stopped by the guard.</aside>
</section>""")

# 8. Impact
S.append(f"""
<section>
 <div class="foot"><span>SOMthing · Claire Zhao</span><span>AI Foundations for Managers · Final Project</span></div>
 <div class="kicker">Impact</div>
 <h2>Minutes instead of an hour, safely, for cents</h2>
 <div class="cards c4">
  <div class="stat dark"><span class="big">{opt['avg_latency_s']} s</span>average time to a verified, priced answer (measured)</div>
  <div class="stat"><span class="big">2–3 min</span><b>to find a move-in bundle</b><br/>vs. ~30–60 min across Slack and apps (estimate)</div>
  <div class="stat"><span class="big">1 min</span><b>to list an item</b><br/>vs. ~10 min writing and price-checking (draft took 7 s)</div>
  <div class="stat"><span class="big">10/10</span><b>requests answered correctly</b><br/>0 invented listings shown</div>
 </div>
 <div class="quote"><b>Pilot user:</b> I built SOMthing for my own selling and tutoring needs and used it end to end: finding move-in furniture, drafting a listing for my own furniture, and searching for Excel and statistics help. A class-section pilot is next, and the app already collects thumbs up/down on every answer.</div>
 <div class="shots-row">{img("inbox", "rowimg")}{img("mobile", "rowimg")}</div>
<aside class="notes">An answer takes about 5 seconds. A move-in bundle that would take 30 to 60 minutes across Slack and apps takes 2 to 3 minutes, and a listing goes from about 10 minutes to about 1. I'm the pilot user and used it end to end for my own needs. A class-section pilot is next, and the app already collects ratings.</aside>
</section>""")

# 9. Next
S.append("""
<section>
 <div class="foot"><span>SOMthing · Claire Zhao</span><span>AI Foundations for Managers · Final Project</span></div>
 <div class="kicker">What's next</div>
 <h2>From classroom demo to a real SOM tool</h2>
 <div class="cards c2">
  <div class="card" style="font-size:.8em"><h3>With another month</h3><ul>
   <li><b>Pilot</b> with one class section: time vs. Slack, collect ratings</li>
   <li><b>Yale sign-in</b>, real messaging with notifications, online hosting</li>
   <li><b>“Wanted” board</b> and saved-search alerts</li>
   <li><b>Moderator queue</b> for held listings and reports</li>
   <li><b>Move-out bundles</b> and photo-to-listing drafts</li></ul></div>
  <div class="card" style="font-size:.8em"><h3>Honest limits today</h3><ul>
   <li>Fictional sellers and listings; mock sign-in; simulated messages</li>
   <li>One pilot user so far; time savings partly estimated</li>
   <li>Pattern filters can be evaded; the guard and output checks are the backstop</li>
   <li>Prices are estimates; token counts are measured</li></ul></div>
 </div>
 <p class="note" style="margin-top:22px">Press <b>S</b> for speaker notes. Try it: clone the repo, run <code>python run.py</code>, and sign in with demo.student / SOMthing2026.</p>
<aside class="notes">Next I'd pilot it with a class section, add Yale sign-in and real messaging, and host it online. Today's limits are fictional listings, simulated messaging, and one user so far. You can try it by cloning the repo and running python run.py.</aside>
</section>""")

html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>SOMthing · Claire Zhao</title>
<link rel="stylesheet" href="{REVEAL}/reveal.css" />
<link rel="stylesheet" href="{REVEAL}/theme/white.css" />
<style>{CSS}</style></head>
<body><div class="reveal"><div class="slides">
{''.join(S)}
</div></div>
<script src="{REVEAL}/reveal.js"></script>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/notes/notes.js"></script>
<script>Reveal.initialize({{ hash: true, slideNumber: "c/t", width: 1280, height: 720, margin: 0.06, center: false, transition: "fade", controls: true, progress: true, plugins: [RevealNotes] }});</script>
</body></html>
"""

OUT.write_text(html)
print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:,.0f} KB) · {len(S)} slides")
