"""Deterministic safety checks that run before and after every AI call.

1. normalize/scan_text: flags prompt-injection and scam patterns, including obfuscated
   variants ("i g n o r e", "1gn0re", zero-width characters, look-alike Unicode).
2. listing_policy_violations: prohibited items (weapons, drugs, fake IDs, academic
   dishonesty) and contact info in public listings.
3. PII: detect and redact emails, phone numbers, SSNs and card numbers.
4. is_suspicious: broad net that decides when the LLM safety guard is consulted.
5. output_violations: checks the AI's answer for scam advice, PII and links.
6. RateLimiter / TokenBudget: cap AI requests and tokens per session and per day,
   so a bug or bad actor cannot burn through the course budget.
"""

from __future__ import annotations

import re
import threading
import time
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass

from . import config

# ---------------------------------------------------------------------------
# Normalization (defeats simple obfuscation before pattern matching)
# ---------------------------------------------------------------------------

_ZERO_WIDTH = re.compile(r"[​-‏‪-‮⁠-⁤﻿]")
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i"})
_SPACED = re.compile(r"\b(?:[a-z][\s.\-_*]){3,}[a-z]\b", re.I)


def normalize(text: str) -> str:
    """NFKC (folds look-alike Unicode), strips zero-width chars, collapses whitespace."""
    text = unicodedata.normalize("NFKC", text or "")
    text = _ZERO_WIDTH.sub("", text)
    return re.sub(r"\s+", " ", text)


def _variants(text: str) -> list[str]:
    base = normalize(text)
    leet = base.lower().translate(_LEET)
    collapsed = _SPACED.sub(lambda m: re.sub(r"[\s.\-_*]", "", m.group(0)), leet)
    return list(dict.fromkeys([base, leet, collapsed]))


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
    """Return the safety reasons that match (empty list = looks fine). Checks obfuscated variants too."""
    variants = _variants(" ".join(p for p in parts if p))
    reasons: list[str] = []
    for reason, pattern in _COMPILED:
        if reason not in reasons and any(pattern.search(v) for v in variants):
            reasons.append(reason)
    return reasons


REASON_LABELS = {
    "prompt_injection": "Text that tries to give instructions to the AI assistant",
    "scam_payment": "Pressure to pay off-platform in advance (common scam pattern)",
}

# ---------------------------------------------------------------------------
# Marketplace content policy (applies to listings people post)
# ---------------------------------------------------------------------------

_PROHIBITED = {
    "weapons": r"\b(guns?|firearms?|pistols?|rifles?|ammo|ammunition|tasers?|brass knuckles)\b",
    "drugs": r"\b(weed|marijuana|cannabis|thc|edibles|adderall|xanax|oxycontin|oxycodone|cocaine|mdma|molly|shrooms|prescription (drugs|pills|meds))\b",
    "counterfeit_or_stolen": r"\b(fake (ids?|diplomas?|degrees?|transcripts?)|counterfeit|replica (designer|handbags?|watch(es)?)|stolen)\b",
    "academic_dishonesty": (
        r"\b(exam|test|quiz|midterm|final)s? (answers|answer keys?|solutions)\b|\banswer keys?\b"
        r"|\b(write|do|complete|take)\s+(your|my|the)\s+(essays?|papers?|thesis|homework|problem sets?|exams?|quiz(zes)?|tests?|midterms?|finals?)\s+for (you|me)\b"
        r"|\b(i'?ll|i will|we will|we'?ll)\s+(write|do|take|complete)\s+(your|the)\s+(essays?|papers?|homework|problem sets?|exams?|quiz(zes)?|tests?|midterms?|finals?)\b"
    ),
}
_PROHIBITED_RE = {k: re.compile(v, re.I) for k, v in _PROHIBITED.items()}

POLICY_LABELS = {
    "weapons": "Weapons aren't allowed on SOMthing.",
    "drugs": "Drugs and prescription medication aren't allowed on SOMthing.",
    "counterfeit_or_stolen": "Counterfeit, fake-ID or stolen goods aren't allowed on SOMthing.",
    "academic_dishonesty": "Selling exam answers or doing someone's graded work violates the honor code. Tutoring and coaching are welcome.",
    "contact_info": "Please don't put phone numbers or email addresses in listings. Buyers contact you through SOMthing, which protects your privacy and helps stop scams.",
    "sensitive_pii": "Listings can't contain SSNs or card numbers.",
}


def listing_policy_violations(*parts: str | None) -> list[str]:
    """Hard rules for public listings. Any hit means the post is rejected (not just held)."""
    text = " ".join(p for p in parts if p)
    variants = _variants(text)
    hits = [k for k, rx in _PROHIBITED_RE.items() if any(rx.search(v) for v in variants)]
    pii = detect_pii(text)
    if {"ssn", "card_number"} & set(pii):
        hits.append("sensitive_pii")
    if {"email", "phone"} & set(pii):
        hits.append("contact_info")
    return hits

# ---------------------------------------------------------------------------
# PII detection + redaction (before text reaches the model or the logs)
# ---------------------------------------------------------------------------

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(\.[\w-]+)+\b")
_PHONE = re.compile(r"(?<!\d)(\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
_SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for d in reversed(digits):
        n = int(d) * (2 if alt else 1)
        total += n - 9 if n > 9 else n
        alt = not alt
    return total % 10 == 0


def _cards(text: str) -> list[re.Match]:
    return [m for m in _CARD.finditer(text) if _luhn_ok(re.sub(r"\D", "", m.group(0)))]


def detect_pii(text: str) -> list[str]:
    text = normalize(text)
    found = []
    if _EMAIL.search(text):
        found.append("email")
    if _SSN.search(text):
        found.append("ssn")
    if _cards(text):
        found.append("card_number")
    without_ids = _SSN.sub(" ", text)
    for m in _cards(text):
        without_ids = without_ids.replace(m.group(0), " ")
    if _PHONE.search(without_ids):
        found.append("phone")
    return found


def redact_pii(text: str) -> str:
    text = normalize(text)
    for m in _cards(text):
        text = text.replace(m.group(0), "[card number removed]")
    text = _SSN.sub("[SSN removed]", text)
    text = _EMAIL.sub("[email removed]", text)
    return _PHONE.sub("[phone removed]", text)

# ---------------------------------------------------------------------------
# Tiered moderation: cheap regex decides when to ask the LLM safety guard
# ---------------------------------------------------------------------------

_SUSPICIOUS = re.compile(
    r"\b(pretend|role.?play|act as|you are|instructions?|system|prompt|developer|jailbreak|bypass|override|"
    r"rules|confidential|secret|password|api.?key|reveal|hidden|dan|do anything now|translate the (above|previous)|"
    r"repeat (the|your)|base64|encode|decode|ignore|disregard|admin|sudo|address of|phone number of|"
    r"home address|scam|fake|launder|cheat|answers? to|translate|(everything|text|instructions|message) above|"
    r"before this|earlier messages?|(take|write|do|finish) my (\w+ ){0,2}(exam|midterm|final|quiz|test|homework|problem sets?|essay|paper)|"
    r"adderall|weed|drugs?|pills|guns?|weapons?|steal|stolen)\b",
    re.I,
)


def is_suspicious(text: str) -> bool:
    return any(_SUSPICIOUS.search(v) for v in _variants(text))

# ---------------------------------------------------------------------------
# Output checks (run on every AI answer before the user sees it)
# ---------------------------------------------------------------------------

_SCAM_ADVICE = re.compile(
    r"\b(send|pay|transfer|venmo|zelle|wire)\b[^.!?]{0,40}\b(deposit|in advance|upfront|up front|before (you )?(meet|meeting|see|seeing|pick))",
    re.I,
)
_NEGATION = re.compile(
    r"\b(never|don['’]?t|do not|avoid|not|no|without|instead of|refuse|red flags?|scams?|suspicious|warning|careful|cautious|unsafe|risky)\b",
    re.I,
)
_LINK = re.compile(r"(https?://\S+|www\.\S+)", re.I)


def output_violations(reply: str) -> list[str]:
    found = []
    for m in _SCAM_ADVICE.finditer(reply):
        # Judge the whole sentence: "a deposit before you meet is a red flag" is a warning, not advice.
        start = max(reply.rfind(".", 0, m.start()), reply.rfind("!", 0, m.start()), reply.rfind("?", 0, m.start())) + 1
        ends = [i for i in (reply.find(".", m.end()), reply.find("!", m.end()), reply.find("?", m.end())) if i != -1]
        sentence = reply[start:min(ends) if ends else len(reply)]
        if not _NEGATION.search(sentence):
            found.append("scam_advice")
            break
    if detect_pii(reply):
        found.append("pii")
    if _LINK.search(reply):
        found.append("link")
    return found


def strip_links(text: str) -> str:
    return _LINK.sub("[link removed]", text)


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
