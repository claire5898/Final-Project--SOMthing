"""App settings, API-key loading, and AI guardrail limits.

The Portkey key is read from a .env file, checked in two places in order:
  1. this repo's own folder
  2. the folder above the repo (where the teaching staff keep their .env)
The key is only ever used server-side and is never logged or sent to the browser.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

REPO_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_DIR / "data"
RUNTIME_DIR = DATA_DIR / "runtime"  # demo state, uploads and usage logs (gitignored)
STATIC_DIR = REPO_DIR / "static"

# --- Model: the course key may only be used with gpt-6-luna -----------------
MODEL_NAME = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
REASONING_EFFORT = "low"  # cost control; see evals/ for the quality comparison
# Canary token placed in the system prompts; if it ever appears in an answer, the
# prompt leaked and the answer is blocked. New random value every time the app starts.
CANARY = "SOMT-CANARY-" + secrets.token_hex(4).upper()

# --- Guardrails ------------------------------------------------------------
MAX_MESSAGE_CHARS = 500          # longest chat message we accept
MAX_NOTES_CHARS = 800            # longest "draft my listing" notes we accept
MAX_TOOL_ROUNDS = 4              # model <-> tool round trips per question
MAX_TOOL_CALLS = 8               # total tool executions per question
MAX_OUTPUT_TOKENS = 900          # per model call
HISTORY_TURNS = 4                # previous chat turns sent back to the model
SEARCH_RESULT_LIMIT = 6          # listings returned to the model per search
SESSION_TOKEN_BUDGET = 60_000    # per signed-in session
DAILY_TOKEN_BUDGET = 1_500_000   # whole app, per calendar day
RATE_LIMIT_REQUESTS = 8          # AI requests ...
RATE_LIMIT_WINDOW_SECONDS = 60   # ... per this many seconds, per session
REQUEST_TIMEOUT_SECONDS = 60

# --- Pricing (USD per 1M tokens) used for cost estimates ---------------------
# Estimates: published gpt-6-luna list prices as reported by pricing aggregators
# (October 2026). The course key is billed through Portkey, so actual cost may differ.
PRICE_INPUT_PER_M: float | None = 0.10
PRICE_CACHED_INPUT_PER_M: float | None = 0.01
PRICE_OUTPUT_PER_M: float | None = 0.50

# --- Mock sign-in (classroom demo only, not real Yale authentication) -------
DEMO_LOGIN_ID = "demo.student"
DEMO_LOGIN_PASSWORD = "SOMthing2026"
DEMO_USER_ID = "u00"

_env_source: str | None = None


def load_env(repo_dir: Path = REPO_DIR) -> str | None:
    """Load .env from the repo folder first, then its parent folder.

    Returns a description of where PORTKEY_API_KEY came from (never the value).
    Values already set win, so the repo's own .env takes priority over the parent's.
    """
    global _env_source
    if _env_source and os.getenv("PORTKEY_API_KEY") and repo_dir == REPO_DIR:
        return _env_source  # already loaded (run.py and the server both call this)
    candidates = [("project folder", repo_dir / ".env"), ("parent folder", repo_dir.parent / ".env")]
    source = "environment" if os.getenv("PORTKEY_API_KEY") else None
    for label, path in candidates:
        if path.is_file():
            had_key = bool(os.getenv("PORTKEY_API_KEY"))
            load_dotenv(path, override=False)
            if not had_key and os.getenv("PORTKEY_API_KEY"):
                source = label
    _env_source = source
    return source


def portkey_key() -> str | None:
    return os.getenv("PORTKEY_API_KEY") or None


def env_source() -> str | None:
    return _env_source


def estimate_cost(input_tokens: int, cached_tokens: int, output_tokens: int) -> float | None:
    """Dollar cost for one run, or None if prices are not configured."""
    if None in (PRICE_INPUT_PER_M, PRICE_CACHED_INPUT_PER_M, PRICE_OUTPUT_PER_M):
        return None
    uncached = max(input_tokens - cached_tokens, 0)
    return (
        uncached * PRICE_INPUT_PER_M
        + cached_tokens * PRICE_CACHED_INPUT_PER_M
        + output_tokens * PRICE_OUTPUT_PER_M
    ) / 1_000_000
