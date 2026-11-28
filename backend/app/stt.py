"""Optional server-side speech-to-text, for browsers without built-in speech recognition
(e.g. Firefox). Off unless STT_API_KEY is set; the app never needs it.

Works with any OpenAI-compatible /audio/transcriptions endpoint (OpenAI, Groq, a self-hosted
faster-whisper server). The audio is forwarded and never written to disk or logged.
"""
import json
import os
import uuid
import urllib.request

MAX_BYTES = int(os.getenv("STT_MAX_BYTES", "700000"))       # ~25 s of opus; far more than one sentence
ALLOWED = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "mp4", "audio/mpeg": "mp3",
           "audio/wav": "wav", "audio/x-wav": "wav", "audio/aac": "aac"}
LANG_CODE = {"hi": "hi", "mr": "mr", "en": "en"}
# A vocabulary hint makes the model prefer ledger words over look-alikes.
PROMPT = "रमेश ने 250 का सामान उधार लिया। सुनीता ने 500 रुपये जमा किए। बाकी कितना है? Ramesh took 250 on credit."


def enabled() -> bool:
    return bool(os.getenv("STT_API_KEY"))


def base_url():
    base = os.getenv("STT_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    return base if base.startswith(("https://", "http://")) else None   # never file:// or custom schemes


def ext_for(content_type: str):
    """'audio/webm;codecs=opus' -> 'webm'; None if not an allowed audio type."""
    return ALLOWED.get((content_type or "").split(";")[0].strip().lower())


def _multipart(fields: dict, file_name: str, file_type: str, data: bytes):
    boundary = "----bk" + uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
                 f'Content-Type: {file_type}\r\n\r\n'.encode() + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return boundary, b"".join(parts)


def transcribe(audio: bytes, content_type: str, lang: str):
    """Return the recognised sentence, or None on any failure (the caller falls back to typing)."""
    ext = ext_for(content_type)
    base = base_url()
    if not (enabled() and ext and base and 0 < len(audio) <= MAX_BYTES):
        return None
    fields = {"model": os.getenv("STT_MODEL", "whisper-1"), "language": LANG_CODE.get(lang, "hi"),
              "response_format": "json", "temperature": "0", "prompt": PROMPT}
    boundary, body = _multipart(fields, f"audio.{ext}", content_type.split(";")[0], audio)
    req = urllib.request.Request(
        base + "/audio/transcriptions", data=body,
        headers={"Authorization": f"Bearer {os.getenv('STT_API_KEY')}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=float(os.getenv("STT_TIMEOUT", "10"))) as r:  # nosec B310
            text = (json.loads(r.read()).get("text") or "").strip()
        return text[:300] or None
    except Exception:
        return None
