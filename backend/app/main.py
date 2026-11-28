import csv
import io
import logging
import os
import re
import urllib.parse
from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from . import db, llm, security, stt
from .parser import parse
from .replies import say, inr, when_label

VERSION = "1.2.0"
ENV_SHOP_NAME = os.getenv("SHOP_NAME", "Singh General Store")
FRONTEND = os.getenv("FRONTEND_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
DOCS = os.getenv("ENABLE_API_DOCS", "false").lower() == "true"
log = logging.getLogger("bolo_khata")

Lang = Literal["hi", "mr", "en"]
# ASCII control chars + zero-width + bidi override/isolate chars (Trojan-Source style tricks).
# Written as escapes so the source file itself never contains them.
CONTROL = re.compile("[\\x00-\\x1f\\x7f\\u200b-\\u200f\\u202a-\\u202e\\u2066-\\u2069]")


def clean(s: Optional[str], max_len: int) -> Optional[str]:
    """Strip control / bidi-override characters, trim, and bound length."""
    if s is None:
        return None
    s = CONTROL.sub("", str(s)).strip()
    return s[:max_len] or None


@asynccontextmanager
async def lifespan(_app):
    db.get()
    yield


app = FastAPI(title="Bolo Khata", version=VERSION, lifespan=lifespan,
              docs_url="/docs" if DOCS else None, redoc_url=None,
              openapi_url="/openapi.json" if DOCS else None)
app.add_middleware(security.SecurityMiddleware)


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    log.exception("unhandled error on %s", request.url.path)
    return JSONResponse({"detail": "Something went wrong. Please try again."}, 500)


@app.exception_handler(RequestValidationError)
async def _invalid(request: Request, exc: RequestValidationError):
    # don't echo the submitted values back
    fields = sorted({".".join(str(p) for p in e.get("loc", [])[1:]) for e in exc.errors()})
    return JSONResponse({"detail": "Invalid input", "fields": fields}, 422)


# ---------------------------------------------------------------- models
class Context(BaseModel):
    awaiting: Optional[Literal["amount", "name", "confirm"]] = None
    name: Optional[str] = Field(None, max_length=60)
    amount: Optional[float] = Field(None, gt=0, le=10_000_000)
    type: Optional[Literal["credit", "payment"]] = None
    type_defaulted: Optional[bool] = False
    note: Optional[str] = Field(None, max_length=120)
    transcript: Optional[str] = Field(None, max_length=300)
    promise_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    model_config = {"extra": "ignore"}


class InterpretIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=300)
    lang: Lang = "hi"
    context: Optional[Context] = None


class EntryIn(BaseModel):
    customer_id: Optional[int] = Field(None, gt=0)
    name: Optional[str] = Field(None, max_length=60)
    amount: float = Field(..., gt=0, le=10_000_000)
    type: Literal["credit", "payment"]
    note: Optional[str] = Field(None, max_length=120)
    transcript: Optional[str] = Field(None, max_length=300)
    lang: Lang = "hi"
    source: Literal["voice", "typed", "offline", "manual"] = "voice"
    promise_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")

    @field_validator("promise_date")
    @classmethod
    def _promise(cls, v):
        return _check_promise(v)


def _check_promise(v):
    """A promise must be a real date between today and a year ahead (or empty to clear it)."""
    if v in (None, ""):
        return None
    try:
        d = date.fromisoformat(v)
    except ValueError:
        raise ValueError("promise_date must be YYYY-MM-DD")
    if not (date.today() <= d <= date.today() + timedelta(days=366)):
        raise ValueError("promise_date must be within the next year")
    return d.isoformat()


PHONE_RE = re.compile(r"^\+?[0-9][0-9 \-]{6,18}$")


class CustomerIn(BaseModel):
    name: Optional[str] = Field(None, max_length=60)
    phone: Optional[str] = Field(None, max_length=20)
    promise_date: Optional[str] = Field(None, max_length=10)

    @field_validator("promise_date")
    @classmethod
    def _promise(cls, v):
        return _check_promise(v)

    @field_validator("phone")
    @classmethod
    def _phone(cls, v):
        if v in (None, ""):
            return v
        if not PHONE_RE.match(v.strip()):
            raise ValueError("phone must be 7-15 digits")
        return v.strip()


class ConfirmEntry(Context):
    is_new: bool = False


class ConfirmTextIn(BaseModel):
    entry: ConfirmEntry
    lang: Lang = "hi"
    model_config = {"extra": "ignore"}


class PinIn(BaseModel):
    pin: str = Field(..., pattern=r"^\d{4,8}$")


class PinChangeIn(BaseModel):
    current: Optional[str] = Field(None, pattern=r"^\d{4,8}$")
    new: Optional[str] = Field(None, pattern=r"^\d{4,8}$")  # None = remove PIN


class SettingsIn(BaseModel):
    shop_name: Optional[str] = Field(None, max_length=60)


def shop_name():
    return db.get_setting("shop_name") or ENV_SHOP_NAME


# ---------------------------------------------------------------- basics
@app.get("/api/health")
def health():
    return {"ok": True, "version": VERSION}


@app.get("/api/config")
def config():
    return {"shop_name": shop_name(), "llm": llm.enabled(), "stt": stt.enabled(), "demo": db.has_demo(),
            "default_lang": os.getenv("DEFAULT_LANG", "hi"), "version": VERSION}


@app.get("/api/summary")
def summary():
    return db.summary()


# ---------------------------------------------------------------- auth
@app.get("/api/auth/status")
def auth_status(request: Request):
    enabled = security.pin_enabled()
    ok = (not enabled) or security.session_valid(request.cookies.get(security.COOKIE))
    return {"pin_enabled": enabled, "unlocked": ok,
            "retry_after": security.LOCKOUT.blocked_for(security.client_ip(request))}


@app.post("/api/auth/login")
def login(body: PinIn, request: Request):
    ip = security.client_ip(request)
    wait = security.LOCKOUT.blocked_for(ip)
    if wait:
        return JSONResponse({"detail": "Too many wrong PINs", "retry_after": wait}, 429)
    stored = db.get_setting("pin_hash")
    if not stored:
        return {"ok": True}
    if not security.verify_pin(body.pin, stored):
        security.LOCKOUT.fail(ip)
        db.add_audit("login_failed", ip)
        return JSONResponse({"detail": "Wrong PIN", "retry_after": security.LOCKOUT.blocked_for(ip)}, 401)
    security.LOCKOUT.ok(ip)
    resp = JSONResponse({"ok": True})
    security.set_cookie(resp, security.new_session(), request)
    return resp


@app.post("/api/auth/logout")
def logout(request: Request):
    security.end_session(request.cookies.get(security.COOKIE))
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(security.COOKIE, path="/")
    return resp


@app.post("/api/auth/pin")
def set_pin(body: PinChangeIn, request: Request):
    """Set, change or remove the PIN. Changing/removing needs the current PIN."""
    ip = security.client_ip(request)
    stored = db.get_setting("pin_hash")
    if stored:
        wait = security.LOCKOUT.blocked_for(ip)
        if wait:
            return JSONResponse({"detail": "Too many wrong PINs", "retry_after": wait}, 429)
        if not body.current or not security.verify_pin(body.current, stored):
            security.LOCKOUT.fail(ip)
            return JSONResponse({"detail": "Current PIN is wrong"}, 401)
        security.LOCKOUT.ok(ip)
    db.clear_sessions()  # log out every other device
    if body.new:
        db.set_setting("pin_hash", security.hash_pin(body.new))
        resp = JSONResponse({"ok": True, "pin_enabled": True})
        security.set_cookie(resp, security.new_session(), request)
        return resp
    db.set_setting("pin_hash", None)
    return {"ok": True, "pin_enabled": False}


# ---------------------------------------------------------------- settings / export
@app.get("/api/settings")
def get_settings():
    return {"shop_name": shop_name(), "pin_enabled": security.pin_enabled(),
            "store_transcripts": db.STORE_TRANSCRIPTS, "llm": llm.enabled(), "stt": stt.enabled(),
            "demo": db.has_demo(), "version": VERSION}


@app.patch("/api/settings")
def patch_settings(body: SettingsIn):
    name = clean(body.shop_name, 60)
    if name:
        db.set_setting("shop_name", name)
    return get_settings()


def _csv_safe(v):
    """Block spreadsheet formula injection (=, +, -, @, tab, CR) in exported cells."""
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + v
    return v


@app.get("/api/export.csv")
def export_csv():
    rows = db.export_rows()
    buf = io.StringIO()
    cols = ["id", "created_at", "customer", "phone", "type", "amount", "note", "status", "cancelled_at", "lang", "source"]
    w = csv.DictWriter(buf, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow({k: _csv_safe(r.get(k)) for k in cols})
    db.add_audit("export_csv", f"{len(rows)} rows")
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="bolo-khata-export.csv"'})


@app.post("/api/demo/clear")
def clear_demo():
    """Remove the sample ledger so the shop starts empty. Real entries are never touched."""
    if not db.has_demo():
        return {"removed": 0}
    return {"removed": db.clear_demo()}


# ---------------------------------------------------------------- voice
@app.post("/api/transcribe")
async def transcribe(request: Request, lang: Lang = "hi"):
    """Fallback for browsers with no built-in speech recognition. Off unless STT_API_KEY is set."""
    if not stt.enabled():
        raise HTTPException(501, "Speech-to-text is not configured")
    ctype = request.headers.get("content-type", "")
    if not stt.ext_for(ctype):
        raise HTTPException(415, "Unsupported audio type")
    data = bytearray()
    async for chunk in request.stream():          # cap the real size, not just the declared one
        data += chunk
        if len(data) > stt.MAX_BYTES:
            raise HTTPException(413, "Audio too long")
    text = await run_in_threadpool(stt.transcribe, bytes(data), ctype, lang)
    return {"text": text or ""}


def _parse(text, context):
    p = llm.parse_llm(text, context) if llm.enabled() else None
    rules = parse(text, context)
    if p is None or p.intent == "unknown":
        return rules
    p.promise_days = rules.promise_days            # dates come from the rules parser (deterministic)
    if rules.intent == "promise":
        return rules
    return p


@app.post("/api/interpret")
def interpret(body: InterpretIn):
    lang = body.lang
    ctx = body.context.model_dump() if body.context else {}
    p = _parse(clean(body.text, 300) or "", ctx)
    p.name = clean(p.name, 60)
    p.note = clean(p.note, 120)
    if p.amount is not None and not (0 < float(p.amount) <= 10_000_000):
        p.amount = None
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

    if p.intent == "balance" and p.name:
        status, matches = db.match_customers(p.name)
        if status == "new":
            return base | {"kind": "answer", "say": say("not_found", lang, name=p.name)}
        if status == "ambiguous":
            return base | {"kind": "choose", "for": "balance", "candidates": matches,
                           "say": say("which", lang, name=p.name)}
        c = matches[0]
        key = "balance" if c["balance"] > 0 else "balance_zero"
        return base | {"kind": "answer", "customer": c, "say": say(key, lang, name=c["name"], bal=c["balance"])}

    if p.intent == "promise" and p.name and p.promise_days is not None:
        status, matches = db.match_customers(p.name)
        if status == "new":
            return base | {"kind": "answer", "say": say("promise_unknown", lang, name=p.name)}
        if status == "ambiguous":
            return base | {"kind": "answer", "say": say("promise_which", lang, name=p.name)}
        c = matches[0]
        if c["balance"] <= 0:
            return base | {"kind": "answer", "say": say("promise_nodebt", lang, name=c["name"])}
        when = (date.today() + timedelta(days=p.promise_days)).isoformat()
        db.set_promise(c["id"], when)
        return base | {"kind": "promise", "customer_id": c["id"], "promise_date": when,
                       "say": say("promise_saved", lang, name=c["name"], when=when_label(when, lang))}

    if p.intent == "entry":
        promise = None
        if p.promise_days is not None and (p.type or "credit") == "credit":
            promise = (date.today() + timedelta(days=p.promise_days)).isoformat()
        elif ctx.get("promise_date"):
            promise = _check_promise_quiet(ctx["promise_date"])
        pending = {"name": p.name, "amount": p.amount, "type": p.type or "credit",
                   "type_defaulted": p.type_defaulted, "note": p.note, "transcript": clean(p.transcript, 300),
                   "promise_date": promise if (p.type or "credit") == "credit" else None}
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


def _check_promise_quiet(v):
    try:
        return _check_promise(v)
    except ValueError:
        return None


def confirm_text(e, lang):
    key = "confirm_credit" if e.get("type") == "credit" else "confirm_payment"
    parts = []
    if e.get("is_new"):
        parts.append(say("new_customer", lang, name=e.get("name") or ""))
    parts.append(say(key, lang, name=e.get("name") or "", amt=e.get("amount") or 0))
    if e.get("promise_date") and e.get("type") == "credit":
        parts.append(say("promise_with", lang, when=when_label(e["promise_date"], lang)))
    if e.get("type_defaulted"):
        parts.append(say("defaulted", lang))
    return " ".join(parts)


@app.post("/api/confirm-text")
def confirm_text_api(body: ConfirmTextIn):
    e = body.entry.model_dump()
    e["name"] = clean(e.get("name"), 60)
    return {"say": confirm_text(e, body.lang)}


# ---------------------------------------------------------------- entries / customers
@app.post("/api/entries")
def create_entry(body: EntryIn):
    cid = body.customer_id
    if cid is None:
        name = clean(body.name, 60)
        if not name:
            raise HTTPException(400, "name or customer_id required")
        cid = db.create_customer(name)["id"]
    elif not db.get_customer(cid):
        raise HTTPException(404, "customer not found")
    e = db.add_entry(cid, body.amount, body.type, clean(body.note, 120), clean(body.transcript, 300),
                     body.lang, body.source)
    c = db.get_customer(cid)
    if body.type == "credit" and body.promise_date and c["balance"] > 0:
        c = db.set_promise(cid, body.promise_date)
    elif c["balance"] <= 0 and c.get("promise_date"):
        c = db.set_promise(cid, None)               # debt cleared: drop the promise
    lang = body.lang
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
    return db.list_customers(clean(q, 60))


@app.post("/api/customers")
def new_customer(body: CustomerIn):
    name = clean(body.name, 60)
    if not name:
        raise HTTPException(400, "name required")
    return db.create_customer(name, body.phone or None)


def _wa_phone(phone):
    if not phone:
        return ""
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) == 10:
        digits = "91" + digits
    return digits


@app.get("/api/customers/{cid}")
def customer(cid: int, lang: Lang = "hi"):
    c = db.get_customer(cid)
    if not c:
        raise HTTPException(404, "customer not found")
    if c["balance"] > 0 and c.get("promise_date") and c["promise_date"] < date.today().isoformat():
        msg = say("reminder_overdue", lang, name=c["name"], shop=shop_name(), bal=c["balance"],
                  when=when_label(c["promise_date"], lang))
    else:
        msg = say("reminder", lang, name=c["name"], shop=shop_name(), bal=max(c["balance"], 0))
    wa = f"https://wa.me/{_wa_phone(c['phone'])}?text={urllib.parse.quote(msg, safe='')}"
    return c | {"entries": db.customer_entries(cid), "reminder_text": msg, "whatsapp_url": wa}


@app.patch("/api/customers/{cid}")
def patch_customer(cid: int, body: CustomerIn):
    if not db.get_customer(cid):
        raise HTTPException(404, "customer not found")
    sent = body.model_fields_set
    if "promise_date" in sent:
        db.set_promise(cid, body.promise_date)
    if sent & {"name", "phone"}:
        return db.update_customer(cid, clean(body.name, 60), body.phone)
    return db.get_customer(cid)


@app.get("/api/audit")
def audit(limit: int = 100):
    return db.audit_log(max(1, min(limit, 500)))


# ---------------------------------------------------------------- frontend
if os.path.isdir(FRONTEND):
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

    @app.get("/sw.js", include_in_schema=False)
    def sw():
        return FileResponse(os.path.join(FRONTEND, "sw.js"), media_type="application/javascript",
                            headers={"Service-Worker-Allowed": "/"})

    @app.get("/manifest.webmanifest", include_in_schema=False)
    def manifest():
        return FileResponse(os.path.join(FRONTEND, "manifest.webmanifest"), media_type="application/manifest+json")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(os.path.join(FRONTEND, "index.html"))
else:  # pragma: no cover
    @app.get("/", include_in_schema=False)
    def index_missing():
        return JSONResponse({"error": "frontend not found"}, 500)
