import os
import tempfile

import pytest

os.environ["SEED_DEMO"] = "true"


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    from app import db
    d = tempfile.mkdtemp()
    db.reset_for_tests(os.path.join(d, "t.db"))
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_health_and_summary(client):
    assert client.get("/api/health").json() == {"ok": True}
    s = client.get("/api/summary").json()
    assert s["customers_total"] == 10


def test_voice_entry_full_flow(client):
    r = client.post("/api/interpret", json={"text": "Mohan ne 250 ka saman liya", "lang": "hi"}).json()
    assert r["kind"] == "confirm"
    e = r["entry"]
    assert e["name"] == "Mohan Lal" and e["amount"] == 250 and e["type"] == "credit"
    before = client.get(f"/api/customers/{e['customer_id']}").json()["balance"]
    saved = client.post("/api/entries", json={**{k: e[k] for k in ("customer_id", "name", "amount", "type")}, "lang": "hi"}).json()
    assert saved["customer"]["balance"] == before + 250
    assert "250" not in saved["say"] or "बाकी" in saved["say"]
    # undo by voice
    u = client.post("/api/interpret", json={"text": "pichli entry cancel karo", "lang": "hi"}).json()
    assert u["kind"] == "undone"
    assert client.get(f"/api/customers/{e['customer_id']}").json()["balance"] == before


def test_new_customer(client):
    r = client.post("/api/interpret", json={"text": "Vikram ne 100 ka saman liya", "lang": "en"}).json()
    assert r["kind"] == "confirm" and r["entry"]["is_new"]
    saved = client.post("/api/entries", json={"name": "Vikram", "amount": 100, "type": "credit", "lang": "en"}).json()
    assert saved["customer"]["balance"] == 100


def test_devanagari_matches_latin_customer(client):
    r = client.post("/api/interpret", json={"text": "मोहन ने 50 जमा किए", "lang": "hi"}).json()
    assert r["kind"] == "confirm" and r["entry"]["name"] == "Mohan Lal" and r["entry"]["type"] == "payment"


def test_ambiguous_name(client):
    client.post("/api/customers", json={"name": "Ramesh"})
    r = client.post("/api/interpret", json={"text": "Ramesh ne 250 ka saman liya", "lang": "hi"}).json()
    assert r["kind"] == "choose" and len(r["candidates"]) == 2


def test_balance_and_reminder(client):
    r = client.post("/api/interpret", json={"text": "Pappu ka kitna baaki hai", "lang": "hi"}).json()
    assert r["kind"] == "answer" and "Pappu" in r["say"]
    c = client.get(f"/api/customers/{r['customer']['id']}?lang=hi").json()
    assert c["whatsapp_url"].startswith("https://wa.me/")


def test_clarify_amount(client):
    r = client.post("/api/interpret", json={"text": "Mohan ne saman liya", "lang": "hi"}).json()
    assert r["kind"] == "clarify" and r["awaiting"] == "amount"
    r2 = client.post("/api/interpret", json={"text": "300", "lang": "hi", "context": {"awaiting": "amount", **r["pending"]}}).json()
    assert r2["kind"] == "confirm" and r2["entry"]["amount"] == 300 and r2["entry"]["name"] == "Mohan Lal"


def test_today_top_total(client):
    for q, kind in [("aaj kis kis ka udhaar hai", "answer"), ("sabse zyada kiska baaki hai", "answer"), ("kul kitna baaki hai", "answer")]:
        assert client.post("/api/interpret", json={"text": q}).json()["kind"] == kind


def test_frontend_served(client):
    assert "बोलो खाता" in client.get("/").text
