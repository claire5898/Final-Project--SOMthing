"""Deterministic safety checks that run before and after every AI call.

1. scan_text: flags prompt-injection and scam patterns in listings and chat messages.
2. RateLimiter: caps AI requests per session.
3. TokenBudget: caps tokens per session and per day, so a bug or bad actor
   cannot burn through the course budget.
"""

from __future__ import annotations

import re
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from . import config

_INJECTION_PATTERNS = [
    r"\b(ignore|disregard|forget|override)\b.{0,30}\b(previous|prior|above|earlier|all|your|system)\b.{0,20}\b(instructions?|rules?|prompts?|guidelines?)",
    r"\bsystem\s*(note|prompt|message|instruction)s?\b",
    r"\b(note|message|instructions?)\s+to\s+(the\s+)?(ai|assistant|chatbot|model|llm)\b",
    r"\byou are now\b",
    r"\b(reveal|print|show|repeat)\b.{0,30}\b(system prompt|instructions|api key|hidden prompt)",
    r"\bdeveloper mode\b|\bjailbreak\b",
]

_SCAM_PATTERNS = [
    r"\b(deposit|pay|payment|send)\b.{0,40}\b(zelle|venmo|cash ?app|paypal|wire|western union|gift ?cards?|crypto|bitcoin)\b.{0,40}\b(before|first|to hold|in advance|upfront)\b",
    r"\b(deposit|payment)\b.{0,30}\b(before|first|in advance|upfront)\b.{0,40}\b(zelle|venmo|cash ?app|paypal|wire|gift ?cards?|crypto|bitcoin)\b",
    r"\bgift ?cards?\b.{0,30}\b(only|accepted|payment)\b",
    r"\b(send|share|give)\b.{0,20}\b(your )?(password|ssn|social security|bank (login|account)|netid password)\b",
]

_COMPILED = [("prompt_injection", re.compile(p, re.I | re.S)) for p in _INJECTION_PATTERNS] + [
    ("scam_payment", re.compile(p, re.I | re.S)) for p in _SCAM_PATTERNS
]


def scan_text(*parts: str | None) -> list[str]:
    """Return the safety reasons that match (empty list = looks fine)."""
    text = " ".join(p for p in parts if p)
    reasons: list[str] = []
    for reason, pattern in _COMPILED:
        if reason not in reasons and pattern.search(text):
            reasons.append(reason)
    return reasons


REASON_LABELS = {
    "prompt_injection": "Text that tries to give instructions to the AI assistant",
    "scam_payment": "Pressure to pay off-platform in advance (common scam pattern)",
}


class RateLimiter:
    def __init__(self, max_requests: int = config.RATE_LIMIT_REQUESTS, window: float = config.RATE_LIMIT_WINDOW_SECONDS):
        self.max_requests = max_requests
        self.window = window
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.max_requests:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


@dataclass
class BudgetStatus:
    allowed: bool
    session_used: int
    session_limit: int
    daily_used: int
    daily_limit: int
    reason: str | None = None


class TokenBudget:
    """Tracks tokens per session and per calendar day (in memory, seeded from the usage log)."""

    def __init__(self, session_limit: int = config.SESSION_TOKEN_BUDGET, daily_limit: int = config.DAILY_TOKEN_BUDGET):
        self.session_limit = session_limit
        self.daily_limit = daily_limit
        self._session: dict[str, int] = defaultdict(int)
        self._daily: dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    @staticmethod
    def _today() -> str:
        return time.strftime("%Y-%m-%d")

    def status(self, session_key: str) -> BudgetStatus:
        with self._lock:
            s_used = self._session[session_key]
            d_used = self._daily[self._today()]
        reason = None
        if s_used >= self.session_limit:
            reason = "session"
        elif d_used >= self.daily_limit:
            reason = "daily"
        return BudgetStatus(reason is None, s_used, self.session_limit, d_used, self.daily_limit, reason)

    def record(self, session_key: str, tokens: int) -> None:
        with self._lock:
            self._session[session_key] += tokens
            self._daily[self._today()] += tokens

    def seed_daily(self, tokens_today: int) -> None:
        with self._lock:
            self._daily[self._today()] = max(self._daily[self._today()], tokens_today)

    def reset_session(self, session_key: str) -> None:
        with self._lock:
            self._session.pop(session_key, None)
