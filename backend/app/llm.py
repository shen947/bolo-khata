"""Optional LLM parser. Used only when LLM_API_KEY is set; any failure falls back
to the rules parser, so the app always works without keys.

Works with any OpenAI-compatible chat completions endpoint
(OpenAI, Groq, OpenRouter, Sarvam, a local Ollama, ...)."""
import json
import os
import urllib.request

from .parser import Parsed

SYSTEM = """You parse ONE sentence spoken by an Indian kirana shop owner into JSON.
Sentences may be Hindi (Devanagari or romanised), Marathi, English or mixed.
Return ONLY a JSON object with keys:
 intent: one of entry | balance | today | top | total | undo | yes | no | unknown
 name: customer name exactly as spoken (no honorific "ji"), or null
 amount: rupee amount as a number, or null. Quantities like "3 packet" are NOT the amount.
 type: "credit" if the shop gave goods/money on udhaar to the customer, "payment" if the customer paid back; null if not an entry
 type_defaulted: true if the sentence did not say clearly and you assumed credit
 note: items mentioned (e.g. "3 packet doodh"), or null
 confidence: 0..1
Intents: balance = asking how much one customer owes; today = who took credit today;
top = who owes the most; total = total pending; undo = cancel the last entry."""


INTENTS = {"entry", "balance", "today", "top", "total", "undo", "yes", "no", "unknown"}


def _validated(p):
    """Never trust model output: coerce and bound every field, else reject."""
    if p.intent not in INTENTS:
        return None
    if p.amount is not None:
        try:
            p.amount = float(str(p.amount).replace(",", ""))
        except ValueError:
            return None
        if not (0 < p.amount <= 10_000_000):
            p.amount = None
        elif p.amount == int(p.amount):
            p.amount = int(p.amount)
    if p.type not in (None, "credit", "payment"):
        p.type = None
    if p.name is not None:
        p.name = "".join(ch for ch in str(p.name) if ch.isprintable())[:60].strip() or None
    if p.note is not None:
        p.note = "".join(ch for ch in str(p.note) if ch.isprintable())[:120].strip() or None
    p.confidence = max(0.0, min(1.0, float(p.confidence or 0)))
    if p.intent == "entry" and p.type is None:
        p.type, p.type_defaulted = "credit", True
    return p


def enabled() -> bool:
    return bool(os.getenv("LLM_API_KEY"))


def parse_llm(text: str, context=None):
    if not enabled():
        return None
    base = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    if not base.startswith(("https://", "http://")):
        return None  # only http(s); never file:// or custom schemes
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    user = text if not context else f"Context from previous turn: {json.dumps(context, ensure_ascii=False)}\nSentence: {text}"
    body = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
    }
    req = urllib.request.Request(
        base + "/chat/completions", data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {os.getenv('LLM_API_KEY')}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=float(os.getenv("LLM_TIMEOUT", "6"))) as r:  # nosec B310
            data = json.loads(r.read())
        obj = json.loads(data["choices"][0]["message"]["content"])
        p = Parsed(
            intent=obj.get("intent") or "unknown",
            name=obj.get("name"),
            amount=obj.get("amount"),
            type=obj.get("type"),
            type_defaulted=bool(obj.get("type_defaulted")),
            note=obj.get("note"),
            confidence=float(obj.get("confidence") or 0.7),
            transcript=text,
            source="llm",
        )
        return _validated(p)
    except Exception:
        return None
