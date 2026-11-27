import os
import tempfile

import pytest


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    from app import db, security
    db.reset_for_tests(os.path.join(tempfile.mkdtemp(), "s.db"))
    security.LOCKOUT.__init__()
    security.API_LIMIT.hits.clear()
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_security_headers(client):
    h = client.get("/").headers
    assert "script-src 'self'" in h["content-security-policy"]
    assert "frame-ancestors 'none'" in h["content-security-policy"]
    assert h["x-frame-options"] == "DENY"
    assert h["x-content-type-options"] == "nosniff"
    assert h["referrer-policy"] == "no-referrer"
    assert "microphone=(self)" in h["permissions-policy"]
    assert client.get("/api/summary").headers["cache-control"] == "no-store"


def test_api_docs_off_by_default(client):
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_rejects_non_json_and_cross_origin(client):
    r = client.post("/api/entries", content="amount=1", headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 415
    r = client.post("/api/entries", json={"name": "X", "amount": 1, "type": "credit"}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


def test_body_size_limit(client):
    r = client.post("/api/interpret", content="{" + " " * 20000 + "}", headers={"Content-Type": "application/json"})
    assert r.status_code == 413


@pytest.mark.parametrize("payload", [
    {"name": "X", "amount": -5, "type": "credit"},
    {"name": "X", "amount": 0, "type": "credit"},
    {"name": "X", "amount": 1e9, "type": "credit"},
    {"name": "X", "amount": 10, "type": "gift"},
    {"name": "X" * 61, "amount": 10, "type": "credit"},
    {"name": "X", "amount": 10, "type": "credit", "lang": "fr"},
])
def test_entry_validation(client, payload):
    assert client.post("/api/entries", json=payload).status_code == 422


def test_interpret_text_limit(client):
    assert client.post("/api/interpret", json={"text": "a" * 301}).status_code == 422


def test_phone_validation(client):
    assert client.patch("/api/customers/1", json={"phone": "<script>"}).status_code == 422
    assert client.patch("/api/customers/1", json={"phone": "98765 43210"}).status_code == 200


def test_validation_does_not_echo_input(client):
    r = client.post("/api/entries", json={"name": "<img src=x onerror=alert(1)>", "amount": -1, "type": "credit"})
    assert r.status_code == 422 and "onerror" not in r.text


def test_control_and_bidi_chars_stripped(client):
    r = client.post("/api/entries", json={"name": "Ra‮mesh\x00", "amount": 10, "type": "credit"}).json()
    assert r["customer"]["name"] == "Ramesh"


def test_pin_lock_flow(client):
    assert client.get("/api/auth/status").json() == {"pin_enabled": False, "unlocked": True, "retry_after": 0}
    assert client.post("/api/auth/pin", json={"new": "12"}).status_code == 422
    r = client.post("/api/auth/pin", json={"new": "4826"})
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    # a fresh device is locked out of the data
    client.cookies.clear()
    assert client.get("/api/summary").status_code == 401
    assert client.get("/api/customers").status_code == 401
    assert client.get("/api/export.csv").status_code == 401
    assert client.get("/api/health").status_code == 200
    assert client.post("/api/auth/login", json={"pin": "0000"}).status_code == 401
    assert client.post("/api/auth/login", json={"pin": "4826"}).status_code == 200
    assert client.get("/api/summary").status_code == 200
    # changing / removing needs the current PIN
    assert client.post("/api/auth/pin", json={"current": "1111", "new": None}).status_code == 401
    assert client.post("/api/auth/pin", json={"current": "4826", "new": None}).json()["pin_enabled"] is False


def test_pin_bruteforce_lockout(client):
    client.post("/api/auth/pin", json={"new": "4826"})
    client.cookies.clear()
    for _ in range(5):
        client.post("/api/auth/login", json={"pin": "0000"})
    r = client.post("/api/auth/login", json={"pin": "4826"})  # right PIN, but locked
    assert r.status_code == 429 and r.json()["retry_after"] > 0


def test_pin_stored_hashed(client):
    from app import db
    client.post("/api/auth/pin", json={"new": "4826"})
    stored = db.get_setting("pin_hash")
    assert "4826" not in stored and stored.startswith("pbkdf2_sha256$")


def test_session_token_stored_hashed(client):
    from app import db
    r = client.post("/api/auth/pin", json={"new": "4826"})
    token = r.cookies.get("bk_session")
    rows = [x[0] for x in db.get().execute("SELECT token_hash FROM sessions")]
    assert token and token not in rows and len(rows) == 1


def test_csv_formula_injection_neutralised(client):
    client.post("/api/entries", json={"name": "=HYPERLINK(\"http://x\")", "amount": 10, "type": "credit"})
    body = client.get("/api/export.csv").text
    assert "'=HYPERLINK" in body
    assert "\n=HYPERLINK" not in body and ",=HYPERLINK" not in body


def test_rate_limit(client):
    from app import security
    security.API_LIMIT.per_minute = 5
    try:
        codes = [client.get("/api/health").status_code for _ in range(7)]
        assert 429 in codes
    finally:
        security.API_LIMIT.per_minute = 240


def test_llm_output_is_validated():
    from app.llm import _validated
    from app.parser import Parsed
    assert _validated(Parsed(intent="drop_tables")) is None
    p = _validated(Parsed(intent="entry", name="A" * 500, amount="-5", type="steal"))
    assert len(p.name) == 60 and p.amount is None and p.type == "credit" and p.type_defaulted
    assert _validated(Parsed(intent="entry", amount="1,250")).amount == 1250


def test_cancel_is_soft_and_audited(client):
    e = client.post("/api/entries", json={"name": "Audit Test", "amount": 50, "type": "credit"}).json()["entry"]
    client.post(f"/api/entries/{e['id']}/cancel", json={})
    from app import db
    assert db.get_entry(e["id"])["status"] == "cancelled"
    actions = [a["action"] for a in client.get("/api/audit").json()]
    assert "entry_cancelled" in actions and "entry_created" in actions
