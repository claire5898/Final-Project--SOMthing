# SOMthing 🛍️

**A marketplace for the Yale School of Management community, with an AI shopping assistant that only recommends listings that actually exist.**

SOM students and community members can buy and sell **Physical Things** (furniture, electronics, bikes, cars, clothing, books, sports gear) and offer **Skills & Services** (tutoring, Excel/coding help, headshots, repairs, résumé and interview prep, music and language lessons).

Two AI agents run on `gpt-6-luna` through the course Portkey key:

| Agent | What it does | Tools |
|---|---|---|
| **SOMbot** (shopping assistant) | Understands requests like *"a desk under $100"*, *"I need help with Excel"*, or *"desk + chair + lamp under $200 total"* and returns real listings with real prices and sellers | `search_listings`, `get_listing_details`, `check_bundle` |
| **Listing Helper** | Turns a seller's rough notes into a complete listing, with a price based on similar SOMthing listings | `get_price_comps` |

**Project write-up:** [`report.html`](report.html) (full report) and [`slides.html`](slides.html) (slide deck). Download either file and open it in a browser.

> 🎓 **Classroom demo.** All people and listings are fictional. Sign-in is a mock screen (no Yale connection), messages are simulated, and SOMthing never handles payments.

---

## Run it (about 3 minutes)

**You need:** Python 3.10 or newer, plus a `.env` file containing `PORTKEY_API_KEY`.

### 1. Clone and enter the folder
```bash
git clone https://github.com/claire5898/Final-Project--SOMthing.git
cd Final-Project--SOMthing
```

### 2. Create a virtual environment and install packages
macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Provide the API key
The app looks for a `.env` file in **two places, in this order**:
1. this repo's own folder (`Final-Project--SOMthing/.env`)
2. the folder **above** it (for example `submissions/.env`)

If your `.env` is already one folder up, there's nothing to do. Otherwise, copy `.env.example` to `.env` and fill in `PORTKEY_API_KEY`. The key stays on the server: it is never sent to the browser, printed or logged.

### 4. Start the app
```bash
python run.py
```
Your browser opens **http://127.0.0.1:8000** automatically. If it doesn't, open that address yourself. The terminal confirms where the key was found, for example `AI key: found in the parent folder`.

### 5. Sign in with the fictional test credentials (also shown on the sign-in page)
- **Yale ID:** `demo.student`
- **Password:** `SOMthing2026`

Or click **Fill test credentials**. Do not enter real Yale credentials.

To stop the app, press `Ctrl+C` in the terminal.

---

## What to try

1. **Browse:** use *Physical Things* or *Skills & Services*, pick a category chip, set a max price, and sort. Browsing uses no AI.
2. **Open a listing:** see the photo, price, condition (items) or experience and per hour/session/project pricing (services), location, availability and seller.
3. **Seller profiles:** click a seller to see their program, class year, bio and listings.
4. **Ask SOMbot** (navy button, bottom right):
   - `Find a desk under $100`
   - `I need help with Excel`
   - `I'm moving in: desk, chair and lamp for under $200 total`: SOMbot builds a bundle, and the **app** (not the AI) checks the total.
   - `A car under $5,000`: no match, so SOMbot says so honestly.
   - Open **"How I found these"** under any answer to see the agent's tool calls, and the ⚡ line for its token usage.
5. **Sell:** **+ Sell** → type rough notes → **Draft my listing** → review → **Post listing**.
6. **Save and contact:** tap the heart to save, or **Contact seller** to send a simulated inquiry, which appears in **Inbox**.
7. **How SOMthing works** (account menu or footer): the agent diagram, what's new compared with existing apps, and costs.
8. **AI & Safety dashboard** (account menu): live token usage per run, user feedback (thumbs up/down on SOMbot answers), guardrail events, held listings, and one-click attack demos.
9. **Reset demo data** (account menu) returns everything to the starting state.

---

## Safety: 8 layers of defense (all built and tested)

The full threat model (14 risks → defenses → tests) is in **[SAFETY.md](SAFETY.md)**. In short:

| Layer | What it does |
|---|---|
| 1. Input checks | Length limits, Unicode/obfuscation normalization (catches "i g n o r e", "1gn0re", zero-width tricks), prompt-injection patterns, and **PII redaction** (emails, phones, SSNs, card numbers) before anything reaches the AI or the logs |
| 2. LLM safety guard | Suspicious messages get a second opinion from a small structured `gpt-6-luna` classifier (injection, privacy, scams, honor code, illegal items, harassment). It **fails closed**. |
| 3. Untrusted data | Listings with hidden AI instructions or pay-first scams are **held**: hidden from browsing and never sent to the AI. All member-written text is wrapped in ⟦ ⟧ markers that authors can't forge. |
| 4. Least privilege | The AI's tools are read-only. Posting, saving and messaging always need a human click, and the Listing Helper only drafts. |
| 5. Output checks | Only tool-returned listing IDs can be shown. Prices and bundle totals are verified by code. A **canary token** catches prompt leaks. Scam advice, links and PII are filtered. |
| 6. Spend and abuse limits | 60k tokens per session, 1.5M per day, 8 AI requests per minute, 4 tool rounds and 8 tool calls per question, 900 output tokens per call |
| 7. Marketplace policy | No weapons, drugs, fake IDs or selling exam answers (honor code), no phone numbers or emails in listings, and "too good to be true" price warnings |
| 8. App security | Key stays server-side, HTML escaping, Content-Security-Policy headers, real-image checks on uploads, a 5-failed-sign-ins-per-minute limit, and an audit log of every AI run |

You can watch the defenses work: open **AI & Safety dashboard** (account menu) and click the attack buttons, such as prompt injection, role-play jailbreak, privacy probe or honor-code request.

### Run the tests (no AI tokens used)
```bash
python -m pytest -q
```
55 tests use a scripted fake model to reproduce attacks and malfunctions and check that each one is stopped:
- invented listings, runaway loops, obfuscated injection, guard blocks and fail-closed
- canary leaks, scam advice, PII, prohibited items, fake uploads, brute-force sign-in
- budget exhaustion and provider outages

They also cover browsing, posting, favorites, inquiries, and loading `.env` from the parent folder.

### Live red team (uses the course key, about 15k tokens)
```bash
python evals/red_team.py
```
Sends 15 real attacks (injection, jailbreaks, leak tricks, privacy probes, scams, honor-code and prohibited-item requests, PII, hallucination bait, token floods) through SOMbot. Latest result: **15/15 handled safely**. The first run scored 11/15, and SAFETY.md explains what changed.

### Live accuracy and cost evaluation (uses the course key, about 70k tokens)
```bash
python evals/run_eval.py
```
Runs 10 real shopping requests through SOMbot with the shipped settings and with an unoptimized configuration. It scores accuracy and records tokens. Results are saved in `evals/results/`.

| Run | Settings | Accuracy | Avg input tokens | Avg cached | Avg output tokens |
|---|---|---|---|---|---|
| Before safety hardening | Optimized (shipped) | 10/10 | 2,806 | 434 | 145 |
| Before safety hardening | Unoptimized (full listing text, 12 results, medium effort) | 10/10 | 3,510 | 735 | 168 |
| **After safety hardening** | **Optimized (shipped)** | **10/10** | **3,110** | **2,492** | **149** |
| After safety hardening | Unoptimized | 10/10 | 3,223 | 2,515 | 149 |

The hardened system prompt is long enough to be **prompt-cached**, so about 80% of input tokens are now cached. Estimated cost per answer is about **$0.00016** (at $0.10 per million input, $0.01 per million cached and $0.50 per million output, estimated `gpt-6-luna` list prices).

---

## Project structure

```
run.py                  start the app
somthing/
  config.py             settings, .env lookup (repo folder, then parent), guardrail limits
  agents.py             SOMbot + Listing Helper: prompts, tools, guarded agent loop
  search.py             deterministic search, price comps, bundle math (shared by site + AI)
  safety.py             injection/scam filter, rate limiter, token budgets
  store.py              fictional data + demo changes (saved to data/runtime/, gitignored)
  usage.py              token + guardrail log behind the dashboard
  server.py             FastAPI routes
  catalog.py            sections and categories
static/                 website (plain HTML/CSS/JS, no build step)
static/img/photos/      real listing photos (Pexels License / Creative Commons; see CREDITS.md)
data/                   fictional users.json and listings.json
tests/                  automated tests (fake model, no tokens)
evals/                  live accuracy + token evaluation and saved results
scripts/                draws the navy-and-white illustrations (make_images.py, illustrations.py)
```

**Photos:** listing photos are real stock photos from Pexels and Wikimedia Commons, used under their licenses and credited in `CREDITS.md` and on each listing page. They illustrate fictional listings.

**Dataset:** the demo dataset is small (14 fictional users and 54 listings in `data/`), so there's no separate big dataset to switch to.

**Model:** `gpt-6-luna` only, through Portkey (`https://api.portkey.ai/v1`), using the OpenAI Responses API with function calling and structured JSON output.

*SOMthing is a classroom project for an AI course and is not affiliated with or endorsed by Yale University.*
