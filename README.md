# SOMthing 🛍️

**A marketplace for the Yale School of Management community, with an AI shopping assistant that only recommends listings that actually exist.**

SOM students and community members can buy and sell **Physical Things** (furniture, electronics, bikes, cars, clothing, books, sports gear) and offer **Skills & Services** (tutoring, Excel/coding help, headshots, repairs, résumé and interview prep, music and language lessons).

Two AI agents run on `gpt-6-luna` through the course Portkey key:

| Agent | What it does | Tools |
|---|---|---|
| **SOMbot** (shopping assistant) | Understands requests like *"a desk under $100"*, *"I need help with Excel"*, or *"desk + chair + lamp under $200 total"* and returns real listings with real prices and sellers | `search_listings`, `get_listing_details`, `check_bundle` |
| **Listing Helper** | Turns a seller's rough notes into a complete listing, with a price based on similar SOMthing listings | `get_price_comps` |

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
7. **AI & Safety dashboard** (account menu): live token usage per run, guardrail events, held listings, and one-click attack demos.
8. **Reset demo data** (account menu) returns everything to the starting state.

---

## Safety guardrails (all built and tested)

| Risk | Defense | Where |
|---|---|---|
| Prompt injection typed into the chat | Pattern filter blocks it **before** any AI call (0 tokens spent) | `somthing/safety.py` |
| Prompt injection or scams hidden in listings | Listings are scanned when posted. Flagged ones are **held**: hidden from browsing and never sent to the AI. The tools also mark listing text as untrusted data. | `safety.py`, `store.py`, `agents.py` |
| AI invents listings | Every ID the AI returns must have come from its own tool results, otherwise it's removed. Cards are drawn from the database, never from AI text. | `agents.chat` |
| AI invents prices / bad math | Every `$` amount in a reply is checked against real prices. Bundle totals are computed by code (`check_bundle`). | `agents.py`, `search.py` |
| Agent loops forever | At most 4 tool rounds and 8 tool calls, then a forced answer or a fallback to real search results | `run_tool_loop` |
| Overspending | 60k tokens per session, 1.5M per day, 8 AI requests per minute, 500-character messages, 900 output tokens per call | `config.py` |
| Bad AI drafts | The Listing Helper's output is validated: section/category consistency, units, price range, lengths | `validate_draft` |
| Cross-site scripting | All user text is HTML-escaped in the browser | `static/js/app.js` |
| Leaking secrets | Key only on the server; `.env` is gitignored; `/api/health` reports *where* the key was found, never its value | `config.py` |

### Run the tests (no AI tokens used)
```bash
python -m pytest -q
```
35 tests use a scripted fake model to reproduce attacks and malfunctions (invented listings, runaway loops, injection, budget exhaustion, provider outages) and check that each one is stopped. They also test browsing, posting, favorites, inquiries, and loading `.env` from the parent folder.

### Live evaluation (uses the course key, about 70k tokens)
```bash
python evals/run_eval.py
```
Runs 10 real requests through SOMbot twice: once with the shipped, cost-optimized settings and once unoptimized. It scores accuracy and records tokens. Results are saved in `evals/results/`.

| Settings | Accuracy | Avg input tokens | Avg output tokens | Avg latency |
|---|---|---|---|---|
| **Optimized** (compact tool results, 6 results, low reasoning effort) | **10/10** | **2,806** | **145** | **4.2 s** |
| Unoptimized (full listing text, 12 results, medium effort) | 10/10 | 3,510 | 168 | 6.9 s |

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
