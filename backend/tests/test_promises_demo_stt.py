"""Promise dates ("kal dega"), demo-data clearing, and the optional speech-to-text fallback."""
import os
import tempfile
from datetime import date, timedelta

import pytest

from app.parser import parse


@pytest.fixture()
def client(monkeypatch):
    from fastapi.testclient import TestClient
    from app import db, security
    monkeypatch.setenv("SEED_DEMO", "true")
    monkeypatch.delenv("STT_API_KEY", raising=False)
    db.reset_for_tests(os.path.join(tempfile.mkdtemp(), "p.db"))
    security.LOCKOUT.__init__()
    security.API_LIMIT.hits.clear()
    security.STT_LIMIT.hits.clear()
    from app.main import app
    with TestClient(app) as c:
        yield c


def iso(days):
    return (date.today() + timedelta(days=days)).isoformat()


# ---------------------------------------------------------------- parser
@pytest.mark.parametrize("text,days", [
    ("Ramesh ne 500 ka saman liya kal dega", 1),
    ("रमेश ने 500 का सामान लिया कल देगा", 1),
    ("रमेशने 400 चे सामान घेतले उद्या देईल", 1),
    ("Ramesh took 500 on credit will pay tomorrow", 1),
    ("Sunita ne 300 ka saman liya do din mein dega", 2),
    ("Mohan ne 1000 ka udhaar liya agle hafte dega", 7),
    ("Ramesh ne saman liya parso dega 800", 2),
    ("Anil ne 700 ka maal liya shaam tak dega", 0),
])
def test_promise_is_read_from_entry(text, days):
    p = parse(text)
    assert p.intent == "entry" and p.type == "credit" and p.promise_days == days
    assert p.amount and p.name


@pytest.mark.parametrize("text", [
    "Ramesh kal dega", "Ramesh dega kal", "Ramesh will pay 500 tomorrow", "रमेश कल देगा",
])
def test_promise_only_sentence(text):
    p = parse(text)
    assert p.intent == "promise" and p.promise_days == 1 and p.name.lower().startswith(("ramesh", "रमेश"))


@pytest.mark.parametrize("text", [
    "Ramesh ne 250 ka saman liya",             # no promise
    "Ramesh kal 500 ka saman le gaya",         # "kal" = yesterday, no future verb
    "Ramesh paid 500 yesterday",
    "Geeta ne 300 jama kiye",
])
def test_no_false_promise(text):
    assert parse(text).promise_days is None


def test_promise_words_do_not_change_amount_or_type():
    # "do din" (two days) must not become the amount; "pay" inside "will pay" must not flip to payment
    p = parse("Sunita ne saman liya do din mein dega 400")
    assert p.amount == 400 and p.type == "credit" and p.promise_days == 2
    p = parse("Ramesh took 500 on credit will pay tomorrow")
    assert p.amount == 500 and p.type == "credit"


# ---------------------------------------------------------------- API flow
def test_entry_with_promise_end_to_end(client):
    r = client.post("/api/interpret", json={"text": "Mohan ne 250 ka saman liya kal dega", "lang": "hi"}).json()
    assert r["kind"] == "confirm"
    e = r["entry"]
    assert e["promise_date"] == iso(1)
    assert "कल" in r["say"]
    saved = client.post("/api/entries", json={"customer_id": e["customer_id"], "amount": e["amount"],
                                              "type": "credit", "promise_date": e["promise_date"]}).json()
    assert saved["customer"]["promise_date"] == iso(1)
    s = client.get("/api/summary").json()
    assert any(x["customer_id"] == e["customer_id"] and x["promise_date"] == iso(1) for x in s["promises"])


def test_promise_only_sentence_updates_customer(client):
    r = client.post("/api/interpret", json={"text": "Ramesh kal dega", "lang": "en"}).json()
    assert r["kind"] == "promise" and r["promise_date"] == iso(1)
    assert client.get(f"/api/customers/{r['customer_id']}").json()["promise_date"] == iso(1)


def test_promise_only_for_unknown_customer_changes_nothing(client):
    n = client.get("/api/summary").json()["customers_total"]
    r = client.post("/api/interpret", json={"text": "Zubin kal dega", "lang": "en"}).json()
    assert r["kind"] == "answer"
    assert client.get("/api/summary").json()["customers_total"] == n


def test_full_payment_clears_the_promise(client):
    c = next(c for c in client.get("/api/customers").json() if c["balance"] > 0)
    client.patch(f"/api/customers/{c['id']}", json={"promise_date": iso(2)})
    assert client.get(f"/api/customers/{c['id']}").json()["promise_date"] == iso(2)
    client.post("/api/entries", json={"customer_id": c["id"], "amount": c["balance"], "type": "payment"})
    assert client.get(f"/api/customers/{c['id']}").json()["promise_date"] is None


def test_partial_payment_keeps_the_promise(client):
    c = next(c for c in client.get("/api/customers").json() if c["balance"] > 100)
    client.patch(f"/api/customers/{c['id']}", json={"promise_date": iso(2)})
    client.post("/api/entries", json={"customer_id": c["id"], "amount": 10, "type": "payment"})
    assert client.get(f"/api/customers/{c['id']}").json()["promise_date"] == iso(2)


@pytest.mark.parametrize("bad", ["2020-01-01", "not-a-date", "2999-01-01", "2026-13-40", "1; DROP TABLE customers"])
def test_bad_promise_dates_rejected(client, bad):
    cid = client.get("/api/customers").json()[0]["id"]
    assert client.patch(f"/api/customers/{cid}", json={"promise_date": bad}).status_code == 422
    assert client.post("/api/entries", json={"customer_id": cid, "amount": 5, "type": "credit",
                                             "promise_date": bad}).status_code == 422


def test_clear_promise_with_empty_value(client):
    cid = client.get("/api/customers").json()[0]["id"]
    client.patch(f"/api/customers/{cid}", json={"promise_date": iso(3)})
    client.patch(f"/api/customers/{cid}", json={"promise_date": ""})
    assert client.get(f"/api/customers/{cid}").json()["promise_date"] is None


def test_overdue_promise_changes_the_whatsapp_reminder(client):
    seeded = next(c for c in client.get("/api/customers").json() if c["promise_date"] and c["promise_date"] < iso(0))
    j = client.get(f"/api/customers/{seeded['id']}?lang=en").json()
    assert "had said" in j["reminder_text"]
    ok = next(c for c in client.get("/api/customers").json() if c["balance"] > 0 and not c["promise_date"])
    assert "had said" not in client.get(f"/api/customers/{ok['id']}?lang=en").json()["reminder_text"]


def test_summary_marks_overdue_today_upcoming(client):
    states = {x["state"] for x in client.get("/api/summary").json()["promises"]}
    assert {"overdue", "today", "upcoming"} <= states


def test_old_database_is_migrated(tmp_path):
    """A v1.0/1.1 database (no promise_date column) must open and keep its data."""
    import sqlite3
    from app import db
    path = str(tmp_path / "old.db")
    con = sqlite3.connect(path)
    con.executescript("""CREATE TABLE customers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        key TEXT NOT NULL, phone TEXT, created_at TEXT NOT NULL);
        INSERT INTO customers(name,key,created_at) VALUES ('Old Customer','old','2026-01-01 10:00:00');""")
    con.commit(); con.close()
    db.reset_for_tests(path)
    os.environ["SEED_DEMO"] = "false"
    try:
        assert [c["name"] for c in db.list_customers()] == ["Old Customer"]
        assert db.list_customers()[0]["promise_date"] is None
    finally:
        os.environ["SEED_DEMO"] = "true"
        db.reset_for_tests(os.path.join(tempfile.mkdtemp(), "x.db"))


# ---------------------------------------------------------------- demo data
def test_clear_demo_removes_only_sample_data(client):
    assert client.get("/api/config").json()["demo"] is True
    real = client.post("/api/entries", json={"name": "Real Customer", "amount": 120, "type": "credit"}).json()
    r = client.post("/api/demo/clear", json={}).json()
    assert r["removed"] > 0
    names = [c["name"] for c in client.get("/api/customers").json()]
    assert names == ["Real Customer"]
    assert client.get(f"/api/customers/{real['customer']['id']}").json()["balance"] == 120
    assert client.get("/api/config").json()["demo"] is False
    assert client.post("/api/demo/clear", json={}).json()["removed"] == 0     # safe to repeat


def test_clear_demo_keeps_a_sample_customer_who_got_a_real_entry(client):
    c = client.get("/api/customers").json()[0]
    client.post("/api/entries", json={"customer_id": c["id"], "amount": 77, "type": "credit"})
    client.post("/api/demo/clear", json={})
    kept = client.get(f"/api/customers/{c['id']}").json()
    assert kept["balance"] == 77 and len(kept["entries"]) == 1


def test_clear_demo_requires_json_and_pin(client):
    assert client.post("/api/demo/clear", content=b"x", headers={"content-type": "text/plain"}).status_code == 415
    client.post("/api/auth/pin", json={"new": "4821"})
    client.post("/api/auth/logout", json={})
    assert client.post("/api/demo/clear", json={}).status_code == 401


# ---------------------------------------------------------------- speech-to-text fallback
AUDIO = {"content-type": "audio/webm;codecs=opus"}


def test_transcribe_not_configured_is_501_and_app_still_works(client):
    assert client.get("/api/config").json()["stt"] is False
    assert client.post("/api/transcribe?lang=hi", content=b"\x1a\x45\xdf\xa3", headers=AUDIO).status_code == 501
    assert client.get("/api/health").json()["ok"] is True


def test_transcribe_rejects_non_audio_and_oversize(client, monkeypatch):
    monkeypatch.setenv("STT_API_KEY", "test-key")
    assert client.post("/api/transcribe", content=b"<?php", headers={"content-type": "text/html"}).status_code == 415
    big = b"0" * 800_000
    assert client.post("/api/transcribe", content=big, headers=AUDIO).status_code == 413


def test_transcribe_cross_origin_blocked(client, monkeypatch):
    monkeypatch.setenv("STT_API_KEY", "test-key")
    r = client.post("/api/transcribe", content=b"abc", headers={**AUDIO, "origin": "https://evil.example"})
    assert r.status_code == 403


def test_transcribe_rate_limited(client, monkeypatch):
    monkeypatch.setenv("STT_API_KEY", "test-key")
    from app import stt
    monkeypatch.setattr(stt, "transcribe", lambda *a, **k: "ok")
    codes = [client.post("/api/transcribe", content=b"abc", headers=AUDIO).status_code for _ in range(25)]
    assert codes[:20] == [200] * 20 and 429 in codes[20:]


def test_transcribe_forwards_audio_and_returns_text(client, monkeypatch):
    monkeypatch.setenv("STT_API_KEY", "test-key")
    monkeypatch.setenv("STT_BASE_URL", "https://stt.example/v1")
    seen = {}

    class Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"text": " Ramesh ne 250 ka saman liya "}'

    def fake_urlopen(req, timeout=0):
        seen["url"], seen["auth"], seen["body"] = req.full_url, req.headers.get("Authorization"), req.data
        return Resp()

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    r = client.post("/api/transcribe?lang=hi", content=b"RIFFfakeaudio", headers=AUDIO)
    assert r.json() == {"text": "Ramesh ne 250 ka saman liya"}
    assert seen["url"] == "https://stt.example/v1/audio/transcriptions"
    assert seen["auth"] == "Bearer test-key"
    assert b"RIFFfakeaudio" in seen["body"] and b'name="language"' in seen["body"]


def test_transcribe_failure_returns_empty_text_not_an_error(client, monkeypatch):
    monkeypatch.setenv("STT_API_KEY", "test-key")
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError("down")))
    r = client.post("/api/transcribe", content=b"abc", headers=AUDIO)
    assert r.status_code == 200 and r.json() == {"text": ""}


def test_stt_refuses_non_http_base_url(monkeypatch):
    from app import stt
    monkeypatch.setenv("STT_API_KEY", "k")
    monkeypatch.setenv("STT_BASE_URL", "file:///etc/passwd")
    assert stt.base_url() is None and stt.transcribe(b"abc", "audio/webm", "hi") is None
