"""In-memory marketplace data with a small JSON file for demo changes.

Seed data (fictional users and listings) lives in data/*.json and is never modified.
Anything a demo user does (post, favorite, inquire) is saved to data/runtime/state.json
so it survives a restart, and "Reset demo" wipes it.
"""

from __future__ import annotations

import copy
import json
import threading
import uuid
from datetime import date, datetime
from pathlib import Path

from . import config
from .catalog import SECTIONS
from .safety import scan_text

PUBLIC_LISTING_FIELDS = (
    "id", "section", "category", "title", "description", "price", "price_unit", "condition",
    "experience", "location", "availability", "seller_id", "emoji", "tags", "created_at",
    "image", "photo_credit", "status", "is_demo_post",
)

PHOTO_DIR = config.STATIC_DIR / "img" / "photos"
_PHOTO_CREDITS_FILE = config.DATA_DIR / "photo_credits.json"
PHOTO_CREDITS: dict = json.loads(_PHOTO_CREDITS_FILE.read_text()) if _PHOTO_CREDITS_FILE.is_file() else {}


def photo_for(key: str, fallback: str) -> str:
    """Real photo if we have one (static/img/photos/<key>.jpg), otherwise the illustration."""
    return f"/static/img/photos/{key}.jpg" if (PHOTO_DIR / f"{key}.jpg").is_file() else fallback


class Store:
    def __init__(self, data_dir: Path = config.DATA_DIR, runtime_dir: Path = config.RUNTIME_DIR):
        self.data_dir = data_dir
        self.runtime_dir = runtime_dir
        self.uploads_dir = runtime_dir / "uploads"
        self._lock = threading.RLock()
        self._seed_users = json.loads((data_dir / "users.json").read_text())
        self._seed_listings = json.loads((data_dir / "listings.json").read_text())
        activity = data_dir / "demo_activity.json"
        self._seed_activity = json.loads(activity.read_text()) if activity.is_file() else {}
        self.reset(save=False)
        self._load_state()

    # ----- lifecycle -------------------------------------------------------
    def reset(self, save: bool = True) -> None:
        with self._lock:
            self.users = {u["id"]: copy.deepcopy(u) for u in self._seed_users}
            self.listings: dict[str, dict] = {}
            for raw in self._seed_listings:
                listing = copy.deepcopy(raw)
                listing.setdefault("image", photo_for(listing["id"], f"/static/img/listings/{listing['id']}.svg"))
                if listing["id"] in PHOTO_CREDITS:
                    listing["photo_credit"] = PHOTO_CREDITS[listing["id"]]
                listing["is_demo_post"] = False
                # Seed listings pass through the same safety scan as new posts.
                reasons = scan_text(listing["title"], listing["description"])
                listing["status"] = "held" if reasons else "active"
                listing["safety_reasons"] = reasons
                self.listings[listing["id"]] = listing
            # Pre-filled demo activity (saved items + inquiries with simulated replies).
            self.favorites: dict[str, list[str]] = copy.deepcopy(self._seed_activity.get("favorites", {}))
            self.inquiries: list[dict] = []
            for seed in self._seed_activity.get("inquiries", []):
                inquiry = copy.deepcopy(seed)
                inquiry["listing_title"] = self.listings[inquiry["listing_id"]]["title"]
                self.inquiries.append(inquiry)
            self.posted_ids: list[str] = []
            if save:
                for f in self.uploads_dir.glob("*") if self.uploads_dir.exists() else []:
                    f.unlink()
                self._save_state()

    def _state_path(self) -> Path:
        return self.runtime_dir / "state.json"

    def _load_state(self) -> None:
        path = self._state_path()
        if not path.is_file():
            return
        try:
            state = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return
        with self._lock:
            for listing in state.get("posted", []):
                self.listings[listing["id"]] = listing
                self.posted_ids.append(listing["id"])
            self.favorites = state.get("favorites", {})
            self.inquiries = state.get("inquiries", [])

    def _save_state(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "posted": [self.listings[i] for i in self.posted_ids if i in self.listings],
            "favorites": self.favorites,
            "inquiries": self.inquiries,
        }
        self._state_path().write_text(json.dumps(state, indent=2))

    # ----- reads -------------------------------------------------------------
    def user_public(self, user_id: str) -> dict | None:
        u = self.users.get(user_id)
        if not u:
            return None
        return {k: u[k] for k in ("id", "name", "program", "class_year", "bio", "location", "member_since")}

    def seller_summary(self, user_id: str) -> dict:
        u = self.users.get(user_id, {})
        return {
            "id": user_id,
            "name": u.get("name", "Unknown"),
            "program": u.get("program", ""),
            "class_year": u.get("class_year"),
        }

    def listing_public(self, listing: dict) -> dict:
        out = {k: listing.get(k) for k in PUBLIC_LISTING_FIELDS if k in listing}
        out["seller"] = self.seller_summary(listing["seller_id"])
        if listing.get("status") == "held":
            out["safety_reasons"] = listing.get("safety_reasons", [])
        return out

    def get_listing(self, listing_id: str) -> dict | None:
        return self.listings.get(listing_id)

    def active_listings(self) -> list[dict]:
        return [l for l in self.listings.values() if l.get("status") == "active"]

    def listings_by_seller(self, user_id: str, include_held: bool = False) -> list[dict]:
        return [
            l for l in self.listings.values()
            if l["seller_id"] == user_id and (include_held or l.get("status") == "active")
        ]

    def held_listings(self) -> list[dict]:
        return [l for l in self.listings.values() if l.get("status") == "held"]

    # ----- writes ------------------------------------------------------------
    def create_listing(self, seller_id: str, fields: dict, image_url: str | None) -> dict:
        with self._lock:
            listing_id = f"P{uuid.uuid4().hex[:6].upper()}"
            section = fields["section"]
            listing = {
                "id": listing_id,
                "section": section,
                "category": fields["category"],
                "title": fields["title"],
                "description": fields["description"],
                "price": fields["price"],
                "price_unit": fields["price_unit"],
                "location": fields["location"],
                "availability": fields["availability"],
                "seller_id": seller_id,
                "emoji": _emoji_for(fields["category"]),
                "tags": fields.get("tags", []),
                "created_at": date.today().isoformat(),
                "image": image_url or photo_for(f"cat-{fields['category']}", f"/static/img/categories/{fields['category']}.svg"),
                "is_demo_post": True,
            }
            if not image_url and f"cat-{fields['category']}" in PHOTO_CREDITS:
                listing["photo_credit"] = PHOTO_CREDITS[f"cat-{fields['category']}"]
            if section == "physical":
                listing["condition"] = fields["condition"]
            else:
                listing["experience"] = fields.get("experience", "")
            reasons = scan_text(listing["title"], listing["description"], listing.get("experience"))
            listing["status"] = "held" if reasons else "active"
            listing["safety_reasons"] = reasons
            self.listings[listing_id] = listing
            self.posted_ids.append(listing_id)
            self._save_state()
            return listing

    def toggle_favorite(self, user_id: str, listing_id: str, on: bool) -> list[str]:
        with self._lock:
            favs = self.favorites.setdefault(user_id, [])
            if on and listing_id not in favs:
                favs.append(listing_id)
            if not on and listing_id in favs:
                favs.remove(listing_id)
            self._save_state()
            return list(favs)

    def add_inquiry(self, user_id: str, listing_id: str, message: str, contact_pref: str) -> dict:
        with self._lock:
            listing = self.listings[listing_id]
            inquiry = {
                "id": uuid.uuid4().hex[:8],
                "from_user_id": user_id,
                "to_user_id": listing["seller_id"],
                "listing_id": listing_id,
                "listing_title": listing["title"],
                "message": message,
                "contact_pref": contact_pref,
                "sent_at": datetime.now().isoformat(timespec="minutes"),
                "simulated": True,
            }
            self.inquiries.append(inquiry)
            self._save_state()
            return inquiry


_CATEGORY_EMOJI = {
    "electronics": "🔌", "furniture": "🪑", "household": "🏠", "cars": "🚗", "bikes": "🚲",
    "clothing": "👗", "books": "📚", "sports-hobby": "⚽", "tutoring": "🎓", "handyman": "🔧",
    "furniture-assembly": "🪛", "vehicle-repair": "🛠️", "photography": "📷", "design": "🎨",
    "resume-interview": "💼", "excel-coding": "💻", "music-lessons": "🎵", "language-tutoring": "🗣️",
}


def _emoji_for(category: str) -> str:
    return _CATEGORY_EMOJI.get(category, "✨")


def category_emoji() -> dict[str, str]:
    return dict(_CATEGORY_EMOJI)


assert set(_CATEGORY_EMOJI) == {c for s in SECTIONS.values() for c in s["categories"]}
