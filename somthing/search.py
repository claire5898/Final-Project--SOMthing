"""Deterministic listing search, shared by the website filters and the AI tools.

No AI is involved here: the assistant can only see listings this code returns.
"""

from __future__ import annotations

import re
import statistics

from .catalog import SECTIONS

_STOPWORDS = {
    "a", "an", "the", "for", "with", "and", "or", "to", "of", "in", "on", "me", "my", "i", "need",
    "want", "looking", "find", "some", "any", "under", "below", "less", "than", "over", "cheap",
    "help", "someone", "who", "can", "is", "are", "good", "please", "something", "get", "buy",
    "around", "about", "up", "at", "most", "max", "budget", "dollars", "usd",
}

# Small synonym map so "couch" finds "sofa", "laptop" finds "macbook", etc.
_SYNONYMS = {
    "couch": ["sofa"], "sofa": ["couch"], "laptop": ["macbook", "computer"], "computer": ["laptop", "monitor"],
    "spreadsheet": ["excel"], "excel": ["spreadsheet"], "bicycle": ["bike"], "bike": ["bicycle"],
    "tv": ["monitor", "screen"], "screen": ["monitor"], "jacket": ["coat", "parka"], "coat": ["parka", "jacket"],
    "resume": ["cv", "résumé"], "cv": ["resume"], "headshot": ["portrait", "photo"], "photo": ["photography", "headshot"],
    "workout": ["fitness", "gym"], "gym": ["fitness", "dumbbells"], "stats": ["statistics"],
    "coding": ["python", "sql", "programming"], "programming": ["coding", "python"], "lamp": ["light", "lighting"],
    "textbook": ["book"], "lesson": ["lessons", "tutoring"], "tutor": ["tutoring"], "mattress": ["bed"],
    "assemble": ["assembly"], "photograph": ["photography"], "photographer": ["photography"], "design": ["designer"], "car": ["sedan", "suv"], "fix": ["repair", "handyman"], "mechanic": ["car repair", "maintenance"],
}


def _norm(text: str) -> str:
    return text.lower().replace("é", "e")


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", _norm(text))
    out = []
    for w in words:
        if w in _STOPWORDS or (len(w) < 2 and not w.isdigit()):
            continue
        out.append(w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w)
    return out


def _score(listing: dict, terms: list[str]) -> float:
    title = _norm(listing["title"])
    tags = _norm(" ".join(listing.get("tags", [])))
    category = _norm(listing["category"].replace("-", " "))
    body = _norm(" ".join(str(listing.get(k, "")) for k in ("description", "experience")))
    score = 0.0
    for term in terms:
        variants = [term] + [_norm(s) for s in _SYNONYMS.get(term, [])]
        best = 0.0
        for v in variants:
            pattern = re.compile(r"\b" + re.escape(v) + r"(s|es)?\b")
            if pattern.search(title):
                best = max(best, 3.0)
            elif pattern.search(tags) or pattern.search(category):
                best = max(best, 2.0)
            elif pattern.search(body):
                best = max(best, 1.0)
        score += best
    return score


def search_listings(
    listings: list[dict],
    query: str | None = None,
    section: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    condition: str | None = None,
    price_unit: str | None = None,
    sort: str = "relevance",
    limit: int | None = None,
) -> list[dict]:
    """Filter + rank active listings. Returns listing dicts (best first)."""
    terms = _tokens(query or "")
    results: list[tuple[float, dict]] = []
    for l in listings:
        if section and l["section"] != section:
            continue
        if category and l["category"] != category:
            continue
        if min_price is not None and l["price"] < min_price:
            continue
        if max_price is not None and l["price"] > max_price:
            continue
        if condition and l.get("condition") != condition:
            continue
        if price_unit and l.get("price_unit") != price_unit:
            continue
        score = _score(l, terms) if terms else 1.0
        if terms and score < 1.5:  # need at least a tag/category match or two body matches
            continue
        results.append((score, l))

    if sort == "price_asc":
        results.sort(key=lambda r: r[1]["price"])
    elif sort == "price_desc":
        results.sort(key=lambda r: -r[1]["price"])
    elif sort == "newest":
        results.sort(key=lambda r: r[1].get("created_at", ""), reverse=True)
    else:
        results.sort(key=lambda r: (-r[0], r[1]["price"]))
    out = [l for _, l in results]
    return out[:limit] if limit else out


def price_comps(listings: list[dict], section: str, category: str, keywords: str | None = None, limit: int = 6) -> dict:
    """Similar active listings plus price statistics, for the listing-helper agent."""
    similar = search_listings(listings, query=keywords, section=section, category=category, limit=limit)
    if not similar and keywords:
        similar = search_listings(listings, section=section, category=category, limit=limit)
    prices = [l["price"] for l in similar]
    return {
        "count": len(similar),
        "min_price": min(prices) if prices else None,
        "median_price": statistics.median(prices) if prices else None,
        "max_price": max(prices) if prices else None,
        "examples": [
            {
                "title": l["title"],
                "price": l["price"],
                "price_unit": l["price_unit"],
                "condition": l.get("condition"),
            }
            for l in similar
        ],
    }


def check_bundle(listings_by_id: dict[str, dict], listing_ids: list[str], budget: float | None) -> dict:
    """Add up a set of listings exactly, so the AI never does arithmetic itself."""
    found, missing = [], []
    for lid in dict.fromkeys(listing_ids):
        l = listings_by_id.get(lid)
        if l and l.get("status") == "active":
            found.append(l)
        else:
            missing.append(lid)
    total = round(sum(l["price"] for l in found), 2)
    return {
        "items": [{"id": l["id"], "title": l["title"], "price": l["price"], "price_unit": l["price_unit"]} for l in found],
        "unknown_ids": missing,
        "total": total,
        "budget": budget,
        "within_budget": None if budget is None else total <= budget,
        "remaining": None if budget is None else round(budget - total, 2),
    }


def valid_category(section: str, category: str) -> bool:
    return section in SECTIONS and category in SECTIONS[section]["categories"]


def price_outlier(listings: list[dict], listing: dict, ratio: float = 0.25) -> bool:
    """'Too good to be true' check: physical item priced far below similar items in its category."""
    if listing.get("section") != "physical" or not listing.get("price"):
        return False
    similar = [
        l["price"] for l in search_listings(listings, query=listing["title"], category=listing["category"])
        if l["id"] != listing["id"]
    ]
    return len(similar) >= 2 and listing["price"] < ratio * statistics.median(similar)
