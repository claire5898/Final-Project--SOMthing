"""End-to-end API tests for the marketplace (browsing needs no AI) and .env loading."""

import os

import pytest
from fastapi.testclient import TestClient

from somthing import config
from somthing.server import AppState, create_app
from somthing.usage import UsageLog


@pytest.fixture
def client(store, tmp_path):
    state = AppState(store=store, usage_log=UsageLog(tmp_path / "u.jsonl"), use_live_client=False)
    return TestClient(create_app(state))


def login(c):
    r = c.post("/api/login", json={"yale_id": config.DEMO_LOGIN_ID, "password": config.DEMO_LOGIN_PASSWORD})
    assert r.status_code == 200


def test_requires_mock_sign_in(client):
    assert client.get("/api/listings").status_code == 401
    assert client.post("/api/login", json={"yale_id": "someone", "password": "x"}).status_code == 401
    login(client)
    assert client.get("/api/listings").status_code == 200


def test_browse_filter_and_detail_without_ai(client):
    login(client)
    data = client.get("/api/listings", params={"section": "physical", "category": "furniture", "max_price": 100}).json()
    assert data["count"] > 0 and all(l["price"] <= 100 and l["category"] == "furniture" for l in data["listings"])
    services = client.get("/api/listings", params={"section": "services", "price_unit": "hour"}).json()
    assert all(l["price_unit"] == "hour" for l in services["listings"])
    detail = client.get("/api/listings/L034").json()
    assert detail["seller"]["name"] == "Maya Chen" and detail["experience"]
    assert client.get("/api/listings/L053").status_code == 404  # held scam listing is hidden


def test_profile_post_favorite_and_inquiry_flow(client):
    login(client)
    assert client.get("/api/users/u01").json()["program"] == "MBA"
    r = client.post("/api/listings", data={
        "section": "services", "category": "tutoring", "title": "Microeconomics tutoring",
        "description": "Problem set help for the Core micro course.", "price": "30", "price_unit": "hour",
        "location": "Evans Hall", "availability": "Weekends", "experience": "TA for micro",
    })
    assert r.status_code == 200 and r.json()["status"] == "active" and r.json()["is_demo_post"]
    seeded_favs = [l["id"] for l in client.get("/api/favorites").json()["listings"]]
    seeded_inbox = len(client.get("/api/inquiries").json()["sent"])
    assert seeded_favs and seeded_inbox  # demo account starts with saved items and inquiries
    assert "L001" in client.put("/api/favorites/L001").json()["favorites"]
    inq = client.post("/api/inquiries", json={"listing_id": "L001", "message": "Still available?"}).json()
    assert inq["simulated"] is True
    assert len(client.get("/api/inquiries").json()["sent"]) == seeded_inbox + 1
    client.post("/api/demo/reset")
    assert [l["id"] for l in client.get("/api/favorites").json()["listings"]] == seeded_favs
    assert len(client.get("/api/inquiries").json()["sent"]) == seeded_inbox


def test_invalid_post_rejected(client):
    login(client)
    r = client.post("/api/listings", data={
        "section": "physical", "category": "tutoring", "title": "x", "description": "short", "price": "-1",
        "price_unit": "hour", "location": "", "availability": "",
    })
    assert r.status_code == 400


def test_ai_off_without_key_but_site_works(client):
    login(client)
    r = client.post("/api/assistant/chat", json={"message": "desk under $100"}).json()
    assert r["blocked"] and r["guardrail"] == "ai_not_configured"


def test_health_never_exposes_key(client, monkeypatch):
    monkeypatch.setenv("PORTKEY_API_KEY", "pk-test-secret-value")
    body = client.get("/api/health").text
    assert "pk-test-secret-value" not in body


def test_env_found_in_parent_folder(tmp_path, monkeypatch):
    """Grader layout: submissions/.env sits one level above the repo."""
    monkeypatch.delenv("PORTKEY_API_KEY", raising=False)
    repo = tmp_path / "submissions" / "somthing"
    repo.mkdir(parents=True)
    (tmp_path / "submissions" / ".env").write_text("PORTKEY_API_KEY=from-parent\n")
    assert config.load_env(repo) == "parent folder"
    assert os.environ["PORTKEY_API_KEY"] == "from-parent"


def test_repo_env_takes_priority(tmp_path, monkeypatch):
    monkeypatch.delenv("PORTKEY_API_KEY", raising=False)
    repo = tmp_path / "submissions" / "somthing"
    repo.mkdir(parents=True)
    (repo / ".env").write_text("PORTKEY_API_KEY=from-repo\n")
    (tmp_path / "submissions" / ".env").write_text("PORTKEY_API_KEY=from-parent\n")
    assert config.load_env(repo) == "project folder"
    assert os.environ["PORTKEY_API_KEY"] == "from-repo"


def test_feedback_on_answers_is_recorded(client):
    login(client)
    assert client.post("/api/assistant/feedback", json={"run_id": "abc123", "rating": "up"}).json()["ok"]
    assert client.post("/api/assistant/feedback", json={"run_id": "abc123", "rating": "sideways"}).status_code == 400
    fb = client.get("/api/dashboard").json()["feedback"]
    assert fb["votes"] == 1 and fb["satisfaction"] == 100
