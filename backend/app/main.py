import os
import urllib.parse
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db, llm
from .parser import parse
from .replies import say, inr

SHOP_NAME = os.getenv("SHOP_NAME", "Singh General Store")
FRONTEND = os.getenv("FRONTEND_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

app = FastAPI(title="Bolo Khata", version="1.0.0")


class InterpretIn(BaseModel):
    text: str
    lang: str = "hi"
    context: Optional[dict] = None


class EntryIn(BaseModel):
    customer_id: Optional[int] = None
    name: Optional[str] = None
    amount: float
    type: str
    note: Optional[str] = None
    transcript: Optional[str] = None
    lang: Optional[str] = "hi"
    source: Optional[str] = "voice"


class CustomerIn(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None


@app.on_event("startup")
def _startup():
    db.get()


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/config")
def config():
    return {"shop_name": SHOP_NAME, "llm": llm.enabled(),
            "default_lang": os.getenv("DEFAULT_LANG", "hi")}


@app.get("/api/summary")
def summary():
    return db.summary()


def _parse(text, context):
    p = llm.parse_llm(text, context) if llm.enabled() else None
    if p is None or p.intent == "unknown":
        p = parse(text, context)
    return p


@app.post("/api/interpret")
def interpret(body: InterpretIn):
    lang = body.lang
    ctx = body.context or {}
    p = _parse(body.text, ctx)
    base = {"parsed": p.dict()}

    if p.intent == "yes":
        return base | {"kind": "yes"}
    if p.intent == "no":
        return base | {"kind": "no", "say": say("cancelled", lang)}

    if p.intent == "undo":
        last = db.last_active_entry()
        if not last:
            return base | {"kind": "answer", "say": say("nothing_to_undo", lang)}
        db.cancel_entry(last["id"])
        return base | {"kind": "undone", "entry": last,
                       "say": say("undone", lang, name=last["customer_name"], amt=last["amount"])}

    if p.intent == "today":
        rows = db.today_credit_customers()
        if not rows:
            return base | {"kind": "answer", "say": say("today_none", lang), "list": []}
        lst = ", ".join(f"{r['name']} {inr(r['amount'])}" for r in rows[:6])
        return base | {"kind": "answer", "list": rows,
                       "say": say("today", lang, n=len(rows), amt=sum(r["amount"] for r in rows), list=lst)}

    if p.intent == "top":
        rows = [c for c in db.list_customers() if c["balance"] > 0][:5]
        lst = ", ".join(f"{r['name']} {inr(r['balance'])}" for r in rows)
        return base | {"kind": "answer", "list": rows, "say": say("top", lang, list=lst)}

    if p.intent == "total":
        s = db.summary()
        return base | {"kind": "answer", "say": say("total", lang, amt=s["outstanding"], n=s["customers_due"])}

    if p.intent == "balance":
        status, matches = db.match_customers(p.name)
        if status == "new":
            return base | {"kind": "answer", "say": say("not_found", lang, name=p.name)}
        if status == "ambiguous":
            return base | {"kind": "choose", "for": "balance", "candidates": matches,
                           "say": say("which", lang, name=p.name)}
        c = matches[0]
        key = "balance" if c["balance"] > 0 else "balance_zero"
        return base | {"kind": "answer", "customer": c, "say": say(key, lang, name=c["name"], bal=c["balance"])}

    if p.intent == "entry":
        pending = {"name": p.name, "amount": p.amount, "type": p.type,
                   "type_defaulted": p.type_defaulted, "note": p.note, "transcript": p.transcript}
        if p.amount is None:
            return base | {"kind": "clarify", "awaiting": "amount", "pending": pending,
                           "say": say("ask_amount", lang, name=p.name or "")}
        if not p.name:
            return base | {"kind": "clarify", "awaiting": "name", "pending": pending,
                           "say": say("ask_name", lang, amt=p.amount)}
        status, matches = db.match_customers(p.name)
        if status == "ambiguous":
            return base | {"kind": "choose", "for": "entry", "candidates": matches, "pending": pending,
                           "say": say("which", lang, name=p.name)}
        if status == "exact":
            c = matches[0]
            pending |= {"customer_id": c["id"], "name": c["name"], "is_new": False, "balance": c["balance"]}
        else:
            pending |= {"customer_id": None, "is_new": True, "balance": 0, "similar": matches}
        return base | {"kind": "confirm", "entry": pending, "say": confirm_text(pending, lang)}

    return base | {"kind": "unknown", "say": say("unknown", lang)}


def confirm_text(e, lang):
    key = "confirm_credit" if e["type"] == "credit" else "confirm_payment"
    parts = []
    if e.get("is_new"):
        parts.append(say("new_customer", lang, name=e["name"]))
    parts.append(say(key, lang, name=e["name"], amt=e["amount"]))
    if e.get("type_defaulted"):
        parts.append(say("defaulted", lang))
    return " ".join(parts)


@app.post("/api/confirm-text")
def confirm_text_api(body: dict):
    return {"say": confirm_text(body["entry"], body.get("lang", "hi"))}


@app.post("/api/entries")
def create_entry(body: EntryIn):
    if body.type not in ("credit", "payment"):
        raise HTTPException(400, "type must be credit or payment")
    if body.amount <= 0 or body.amount > 10_000_000:
        raise HTTPException(400, "amount out of range")
    cid = body.customer_id
    if cid is None:
        if not body.name:
            raise HTTPException(400, "name or customer_id required")
        cid = db.create_customer(body.name)["id"]
    elif not db.get_customer(cid):
        raise HTTPException(404, "customer not found")
    e = db.add_entry(cid, body.amount, body.type, body.note, body.transcript, body.lang, body.source)
    c = db.get_customer(cid)
    lang = body.lang or "hi"
    if c["balance"] > 0:
        msg = say("saved", lang, name=c["name"], bal=c["balance"])
    elif c["balance"] == 0:
        msg = say("saved_clear", lang, name=c["name"])
    else:
        msg = say("saved_advance", lang, name=c["name"], bal=-c["balance"])
    return {"entry": e, "customer": c, "say": msg}


@app.post("/api/entries/{eid}/cancel")
def cancel(eid: int):
    e = db.get_entry(eid)
    if not e:
        raise HTTPException(404, "entry not found")
    return {"entry": db.cancel_entry(eid, "manual undo")}


@app.get("/api/customers")
def customers(q: Optional[str] = None):
    return db.list_customers(q)


@app.post("/api/customers")
def new_customer(body: CustomerIn):
    if not body.name:
        raise HTTPException(400, "name required")
    return db.create_customer(body.name, body.phone)


def _wa_phone(phone):
    if not phone:
        return ""
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) == 10:
        digits = "91" + digits
    return digits


@app.get("/api/customers/{cid}")
def customer(cid: int, lang: str = "hi"):
    c = db.get_customer(cid)
    if not c:
        raise HTTPException(404, "customer not found")
    msg = say("reminder", lang, name=c["name"], shop=SHOP_NAME, bal=max(c["balance"], 0))
    wa = f"https://wa.me/{_wa_phone(c['phone'])}?text={urllib.parse.quote(msg)}"
    return c | {"entries": db.customer_entries(cid), "reminder_text": msg, "whatsapp_url": wa}


@app.patch("/api/customers/{cid}")
def patch_customer(cid: int, body: CustomerIn):
    if not db.get_customer(cid):
        raise HTTPException(404, "customer not found")
    return db.update_customer(cid, body.name, body.phone)


@app.get("/api/audit")
def audit(limit: int = 100):
    return db.audit_log(limit)


# ---------------------------------------------------------------- frontend
if os.path.isdir(FRONTEND):
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

    @app.get("/sw.js")
    def sw():
        return FileResponse(os.path.join(FRONTEND, "sw.js"), media_type="application/javascript")

    @app.get("/manifest.webmanifest")
    def manifest():
        return FileResponse(os.path.join(FRONTEND, "manifest.webmanifest"), media_type="application/manifest+json")

    @app.get("/")
    def index():
        return FileResponse(os.path.join(FRONTEND, "index.html"))
else:
    @app.get("/")
    def index_missing():
        return JSONResponse({"error": "frontend not found", "frontend_dir": FRONTEND}, 500)
