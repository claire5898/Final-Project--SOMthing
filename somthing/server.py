"""FastAPI server: marketplace API, mock sign-in, AI endpoints and the static website."""

from __future__ import annotations

import secrets
import threading
import uuid

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import agents, config
from .catalog import CONDITIONS, PRICE_UNITS, SECTIONS
from .safety import POLICY_LABELS, REASON_LABELS, RateLimiter, TokenBudget, detect_pii, listing_policy_violations
from .search import price_outlier, search_listings, valid_category
from .store import Store, category_emoji
from .usage import UsageLog

SESSION_COOKIE = "somthing_session"
MAX_UPLOAD_BYTES = 3 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


def looks_like_image(data: bytes, ext: str) -> bool:
    """Check the file's magic bytes, not just the browser-supplied content type."""
    if ext == ".jpg":
        return data[:3] == b"\xff\xd8\xff"
    if ext == ".png":
        return data[:8] == b"\x89PNG\r\n\x1a\n"
    if ext == ".gif":
        return data[:4] == b"GIF8"
    if ext == ".webp":
        return data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    return False


# ----- request bodies -----
class LoginBody(BaseModel):
    yale_id: str
    password: str


class InquiryBody(BaseModel):
    listing_id: str
    message: str
    contact_pref: str = "SOMthing inbox"


class ChatBody(BaseModel):
    message: str


class DraftBody(BaseModel):
    notes: str


class AppState:
    def __init__(self, store: Store | None = None, client=None, usage_log: UsageLog | None = None, use_live_client: bool = True):
        config.load_env()
        self.store = store or Store()
        self.log = usage_log or UsageLog()
        self.guards = agents.Guards(limiter=RateLimiter(), budget=TokenBudget(), log=self.log)
        self.guards.budget.seed_daily(self.log.tokens_today())
        self.client = client if client is not None else (agents.make_client() if use_live_client else None)
        self.sessions: dict[str, dict] = {}
        self.lock = threading.Lock()


def create_app(state: AppState | None = None) -> FastAPI:
    state = state or AppState()
    app = FastAPI(title="SOMthing", docs_url=None, redoc_url=None)
    login_limiter = RateLimiter(max_requests=5, window=60)  # failed sign-in attempts per client

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        return response
    app.state.somthing = state
    state.store.uploads_dir.mkdir(parents=True, exist_ok=True)

    # ----- session helpers ----------------------------------------------------
    def current_session(request: Request) -> tuple[str, dict]:
        token = request.cookies.get(SESSION_COOKIE)
        sess = state.sessions.get(token or "")
        if not sess:
            raise HTTPException(status_code=401, detail="Please sign in (demo).")
        return token, sess

    def user_id(request: Request) -> str:
        return current_session(request)[1]["user_id"]

    # ----- auth (mock) ----------------------------------------------------------
    @app.post("/api/login")
    def login(body: LoginBody, response: Response, request: Request):
        client_key = request.client.host if request.client else "unknown"
        if body.yale_id.strip().lower() != config.DEMO_LOGIN_ID or body.password != config.DEMO_LOGIN_PASSWORD:
            if not login_limiter.allow(client_key):
                raise HTTPException(status_code=429, detail="Too many failed sign-in attempts. Wait a minute and try again.")
            raise HTTPException(status_code=401, detail="Use the demo test credentials shown on this page.")
        token = secrets.token_urlsafe(24)
        with state.lock:
            state.sessions[token] = {"user_id": config.DEMO_USER_ID, "history": []}
        response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=60 * 60 * 12)
        return {"ok": True, "user": state.store.user_public(config.DEMO_USER_ID)}

    @app.post("/api/logout")
    def logout(request: Request, response: Response):
        token = request.cookies.get(SESSION_COOKIE)
        state.sessions.pop(token or "", None)
        response.delete_cookie(SESSION_COOKIE)
        return {"ok": True}

    @app.get("/api/me")
    def me(request: Request):
        token, sess = current_session(request)
        uid = sess["user_id"]
        return {
            "user": state.store.user_public(uid),
            "favorites": state.store.favorites.get(uid, []),
            "budget": state.guards.budget.status(token).__dict__,
        }

    # ----- catalog + browsing (no AI) -----------------------------------------
    @app.get("/api/meta")
    def meta():
        counts: dict[str, int] = {}
        for l in state.store.active_listings():
            counts[l["category"]] = counts.get(l["category"], 0) + 1
        return {
            "sections": SECTIONS,
            "conditions": CONDITIONS,
            "price_units": PRICE_UNITS,
            "category_emoji": category_emoji(),
            "category_counts": counts,
            "demo_login": {"yale_id": config.DEMO_LOGIN_ID, "password": config.DEMO_LOGIN_PASSWORD},
        }

    @app.get("/api/health")
    def health():
        return {
            "ok": True,
            "ai_configured": state.client is not None,
            "key_found_in": config.env_source(),  # where the key came from, never the key itself
            "model": config.MODEL_NAME,
        }

    @app.get("/api/listings")
    def list_listings(
        request: Request,
        q: str | None = None,
        section: str | None = None,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        condition: str | None = None,
        price_unit: str | None = None,
        sort: str = "newest",
    ):
        user_id(request)
        results = search_listings(
            state.store.active_listings(), query=q, section=section or None, category=category or None,
            min_price=min_price, max_price=max_price, condition=condition or None, price_unit=price_unit or None,
            sort=sort if not q or sort != "newest" else "relevance",
        )
        return {"count": len(results), "listings": [state.store.listing_public(l) for l in results]}

    @app.get("/api/listings/{listing_id}")
    def get_listing(listing_id: str, request: Request):
        uid = user_id(request)
        l = state.store.get_listing(listing_id)
        if not l or (l.get("status") != "active" and l["seller_id"] != uid):
            raise HTTPException(status_code=404, detail="Listing not found.")
        out = state.store.listing_public(l)
        out["seller"] = state.store.user_public(l["seller_id"])
        if l.get("status") == "held":
            out["safety_reason_labels"] = [REASON_LABELS.get(r, r) for r in l.get("safety_reasons", [])]
        same = [
            x for x in search_listings(state.store.active_listings(), category=l["category"], sort="newest")
            if x["id"] != l["id"]
        ][:4]
        out["similar"] = [state.store.listing_public(x) for x in same]
        if price_outlier(state.store.active_listings(), l):
            out["price_warning"] = "This price is much lower than similar listings. Inspect the item in person before paying."
        return out

    @app.get("/api/users/{uid}")
    def get_user(uid: str, request: Request):
        me_id = user_id(request)
        u = state.store.user_public(uid)
        if not u:
            raise HTTPException(status_code=404, detail="User not found.")
        listings = state.store.listings_by_seller(uid, include_held=(uid == me_id))
        u["listings"] = [state.store.listing_public(l) for l in sorted(listings, key=lambda x: x.get("created_at", ""), reverse=True)]
        return u

    # ----- posting -------------------------------------------------------------
    @app.post("/api/listings")
    async def create_listing(
        request: Request,
        section: str = Form(""),
        category: str = Form(""),
        title: str = Form(""),
        description: str = Form(""),
        price: str = Form(""),
        price_unit: str = Form(""),
        location: str = Form(""),
        availability: str = Form(""),
        condition: str | None = Form(None),
        experience: str | None = Form(None),
        tags: str | None = Form(None),
        photo: UploadFile | None = File(None),
    ):
        uid = user_id(request)
        errors = []
        try:
            price_value = float(price)
        except ValueError:
            price_value = -1.0
        if not valid_category(section, category):
            errors.append("Pick a valid section and category.")
        if price_unit not in PRICE_UNITS.get(section, []):
            errors.append("Pick a valid price unit.")
        if section == "physical" and condition not in CONDITIONS:
            errors.append("Pick the item's condition.")
        if not (3 <= len(title.strip()) <= 80):
            errors.append("Title must be 3-80 characters.")
        if not (10 <= len(description.strip()) <= 1000):
            errors.append("Description must be 10-1000 characters.")
        if not (0 <= price_value <= 100_000):
            errors.append("Price must be between $0 and $100,000.")
        if not location.strip() or len(location) > 80 or not availability.strip() or len(availability) > 80:
            errors.append("Add a location and availability (up to 80 characters each).")
        image_url = None
        if photo is not None and photo.filename:
            ext = ALLOWED_IMAGE_TYPES.get(photo.content_type or "")
            data = await photo.read()
            if not ext:
                errors.append("Photo must be a JPG, PNG, WEBP or GIF.")
            elif len(data) > MAX_UPLOAD_BYTES:
                errors.append("Photo must be under 3 MB.")
            elif not looks_like_image(data, ext):
                errors.append("That file doesn't look like a real image.")
            else:
                name = f"{uuid.uuid4().hex}{ext}"
                (state.store.uploads_dir / name).write_bytes(data)
                image_url = f"/uploads/{name}"
        policy = listing_policy_violations(title, description, experience)
        errors += [POLICY_LABELS[p] for p in policy]
        if errors:
            raise HTTPException(status_code=400, detail=" ".join(errors))
        fields = {
            "section": section, "category": category, "title": title.strip(), "description": description.strip(),
            "price": round(price_value, 2), "price_unit": price_unit, "location": location.strip(),
            "availability": availability.strip(), "condition": condition, "experience": (experience or "").strip()[:300],
            "tags": [t.strip() for t in (tags or "").split(",") if t.strip()][:6],
        }
        listing = state.store.create_listing(uid, fields, image_url)
        out = state.store.listing_public(listing)
        if listing["status"] == "held":
            out["safety_reason_labels"] = [REASON_LABELS.get(r, r) for r in listing["safety_reasons"]]
        return out

    # ----- favorites + inquiries (simulated messaging) --------------------------
    @app.get("/api/favorites")
    def favorites(request: Request):
        uid = user_id(request)
        ids = state.store.favorites.get(uid, [])
        return {"listings": [state.store.listing_public(state.store.listings[i]) for i in ids
                             if i in state.store.listings and state.store.listings[i].get("status") == "active"]}

    @app.put("/api/favorites/{listing_id}")
    def add_favorite(listing_id: str, request: Request):
        uid = user_id(request)
        if listing_id not in state.store.listings:
            raise HTTPException(status_code=404, detail="Listing not found.")
        return {"favorites": state.store.toggle_favorite(uid, listing_id, True)}

    @app.delete("/api/favorites/{listing_id}")
    def remove_favorite(listing_id: str, request: Request):
        return {"favorites": state.store.toggle_favorite(user_id(request), listing_id, False)}

    @app.post("/api/inquiries")
    def send_inquiry(body: InquiryBody, request: Request):
        uid = user_id(request)
        l = state.store.get_listing(body.listing_id)
        if not l or l.get("status") != "active":
            raise HTTPException(status_code=404, detail="Listing not found.")
        if l["seller_id"] == uid:
            raise HTTPException(status_code=400, detail="That's your own listing.")
        if {"ssn", "card_number"} & set(detect_pii(body.message)):
            raise HTTPException(status_code=400, detail="For your safety, don't send SSNs or card numbers in messages.")
        if not (2 <= len(body.message.strip()) <= 1000):
            raise HTTPException(status_code=400, detail="Message must be 2-1000 characters.")
        return state.store.add_inquiry(uid, body.listing_id, body.message.strip(), body.contact_pref[:40])

    @app.get("/api/inquiries")
    def list_inquiries(request: Request):
        uid = user_id(request)
        sent = [
            {**i, "to_name": state.store.seller_summary(i["to_user_id"])["name"],
             "listing_image": (state.store.get_listing(i["listing_id"]) or {}).get("image")}
            for i in state.store.inquiries if i["from_user_id"] == uid
        ][::-1]
        return {"sent": sent}

    # ----- AI endpoints ---------------------------------------------------------------
    @app.post("/api/assistant/chat")
    def assistant_chat(body: ChatBody, request: Request):
        token, sess = current_session(request)
        result = agents.chat(
            body.message, session_key=token, history=sess["history"], store=state.store,
            guards=state.guards, client=state.client,
        )
        if not result.get("blocked") and not result.get("error"):
            shown = ", ".join(l["id"] for l in result.get("listings", []))
            sess["history"] += [
                {"role": "user", "content": result.get("history_message", body.message.strip())},
                {"role": "assistant", "content": result["reply"] + (f" [Listings shown: {shown}]" if shown else "")},
            ]
            sess["history"] = sess["history"][-2 * config.HISTORY_TURNS:]
        result["budget"] = state.guards.budget.status(token).__dict__
        return result

    @app.post("/api/assistant/reset")
    def assistant_reset(request: Request):
        _, sess = current_session(request)
        sess["history"] = []
        return {"ok": True}

    @app.post("/api/helper/draft")
    def helper_draft(body: DraftBody, request: Request):
        token, _ = current_session(request)
        result = agents.draft_listing(body.notes, session_key=token, store=state.store, guards=state.guards, client=state.client)
        result["budget"] = state.guards.budget.status(token).__dict__
        return result

    # ----- transparency dashboard + demo reset -------------------------------------
    @app.get("/api/dashboard")
    def dashboard(request: Request):
        token, _ = current_session(request)
        summary = state.log.summary()
        summary["session_budget"] = state.guards.budget.status(token).__dict__
        summary["held_listings"] = [
            {**state.store.listing_public(l), "safety_reason_labels": [REASON_LABELS.get(r, r) for r in l.get("safety_reasons", [])]}
            for l in state.store.held_listings()
        ]
        return summary

    @app.post("/api/demo/reset")
    def demo_reset(request: Request):
        token, sess = current_session(request)
        state.store.reset()
        sess["history"] = []
        return {"ok": True}

    # ----- website ---------------------------------------------------------------------
    app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
    app.mount("/uploads", StaticFiles(directory=state.store.uploads_dir), name="uploads")

    @app.get("/")
    def index():
        return FileResponse(config.STATIC_DIR / "index.html", headers={"Cache-Control": "no-store"})

    return app
