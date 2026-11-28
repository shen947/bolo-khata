"""Security layer: optional PIN lock, sessions, brute-force lockout, rate limits,
same-origin checks for state-changing requests, and security headers.

Design notes
- The PIN is optional so the app opens straight to the main screen on first run.
  Once the owner sets one, every /api call except a small public list needs a session.
- PINs are stored as PBKDF2-HMAC-SHA256 (200k iterations, random salt). Only a
  SHA-256 hash of each session token is stored, so a copied database cannot be
  used to log in.
- Cookies are HttpOnly + SameSite=Strict (+ Secure when served over HTTPS).
- Mutating requests must be JSON and same-origin. Together with SameSite this
  blocks cross-site request forgery.
"""
import hashlib
import hmac
import os
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from . import db

COOKIE = "bk_session"
SESSION_DAYS = int(os.getenv("SESSION_DAYS", "30"))
PBKDF2_ITER = 200_000
PUBLIC_API = {"/api/health", "/api/config", "/api/auth/status", "/api/auth/login"}
MAX_BODY = 16 * 1024
STT_MAX = int(os.getenv("STT_MAX_BYTES", "700000"))   # one spoken sentence of audio

CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; "
       "img-src 'self' data:; connect-src 'self'; manifest-src 'self'; worker-src 'self'; "
       "media-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; "
       "frame-ancestors 'none'")


# ---------------------------------------------------------------- PIN
def hash_pin(pin: str, salt: bytes = None) -> str:
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, PBKDF2_ITER)
    return f"pbkdf2_sha256${PBKDF2_ITER}${salt.hex()}${dk.hex()}"


def verify_pin(pin: str, stored: str) -> bool:
    try:
        _, it, salt, dk = stored.split("$")
        test = hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt), int(it))
        return hmac.compare_digest(test.hex(), dk)
    except Exception:
        return False


def pin_enabled() -> bool:
    return bool(db.get_setting("pin_hash"))


# ---------------------------------------------------------------- sessions
def _th(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_session() -> str:
    token = secrets.token_urlsafe(32)
    exp = (datetime.now() + timedelta(days=SESSION_DAYS)).isoformat(sep=" ")
    db.add_session(_th(token), exp)
    return token


def session_valid(token: str) -> bool:
    if not token:
        return False
    return db.session_valid(_th(token), datetime.now().isoformat(sep=" "))


def end_session(token: str):
    if token:
        db.delete_session(_th(token))


def set_cookie(resp, token, request):
    secure = request.url.scheme == "https" or os.getenv("COOKIE_SECURE", "").lower() == "true"
    resp.set_cookie(COOKIE, token, max_age=SESSION_DAYS * 86400, httponly=True,
                    samesite="strict", secure=secure, path="/")


# ---------------------------------------------------------------- brute force
class Lockout:
    """5 wrong PINs -> locked 5 min; each further lock doubles (max 1h). Per client IP."""

    def __init__(self, max_fails=5, base=300, cap=3600):
        self.max_fails, self.base, self.cap = max_fails, base, cap
        self.fails = defaultdict(int)
        self.locks = defaultdict(int)
        self.until = {}

    def blocked_for(self, ip) -> int:
        u = self.until.get(ip, 0)
        return max(0, int(u - time.time()))

    def fail(self, ip):
        self.fails[ip] += 1
        if self.fails[ip] >= self.max_fails:
            self.locks[ip] += 1
            self.until[ip] = time.time() + min(self.cap, self.base * 2 ** (self.locks[ip] - 1))
            self.fails[ip] = 0

    def ok(self, ip):
        self.fails.pop(ip, None)
        self.locks.pop(ip, None)
        self.until.pop(ip, None)


LOCKOUT = Lockout()


# ---------------------------------------------------------------- rate limit
class RateLimiter:
    def __init__(self, per_minute):
        self.per_minute = per_minute
        self.hits = defaultdict(deque)

    def allow(self, key) -> bool:
        now = time.time()
        q = self.hits[key]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.per_minute:
            return False
        q.append(now)
        if len(self.hits) > 10_000:  # bound memory
            self.hits.clear()
        return True


API_LIMIT = RateLimiter(int(os.getenv("RATE_LIMIT_PER_MIN", "240")))
STT_LIMIT = RateLimiter(int(os.getenv("STT_LIMIT_PER_MIN", "20")))   # transcription costs money: keep it tight
STT_PATH = "/api/transcribe"


def client_ip(request) -> str:
    if os.getenv("TRUST_PROXY", "").lower() == "true":
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _same_origin(request) -> bool:
    origin = request.headers.get("origin")
    if not origin:
        return True  # same-origin fetch from older browsers / curl; SameSite cookie still applies
    host = request.headers.get("x-forwarded-host") if os.getenv("TRUST_PROXY", "").lower() == "true" else None
    host = host or request.headers.get("host", "")
    return origin.split("://", 1)[-1] == host


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if path.startswith("/api/"):
            ip = client_ip(request)
            if not API_LIMIT.allow(ip):
                return self._headers(JSONResponse({"detail": "Too many requests. Slow down."}, 429, headers={"Retry-After": "60"}), path)
            if request.method in ("POST", "PUT", "PATCH", "DELETE"):
                ctype = request.headers.get("content-type", "")
                is_audio = path == STT_PATH and ctype.startswith("audio/")
                if not (ctype.startswith("application/json") or is_audio):
                    return self._headers(JSONResponse({"detail": "Content-Type must be application/json"}, 415), path)
                if not _same_origin(request):
                    return self._headers(JSONResponse({"detail": "Cross-origin request blocked"}, 403), path)
                if is_audio and not STT_LIMIT.allow(ip):
                    return self._headers(JSONResponse({"detail": "Too many requests. Slow down."}, 429, headers={"Retry-After": "60"}), path)
                try:
                    if int(request.headers.get("content-length") or 0) > (STT_MAX if is_audio else MAX_BODY):
                        return self._headers(JSONResponse({"detail": "Request too large"}, 413), path)
                except ValueError:
                    return self._headers(JSONResponse({"detail": "Bad Content-Length"}, 400), path)
            if path not in PUBLIC_API and pin_enabled() and not session_valid(request.cookies.get(COOKIE)):
                return self._headers(JSONResponse({"detail": "locked"}, 401), path)
        response = await call_next(request)
        return self._headers(response, path)

    @staticmethod
    def _headers(resp, path=""):
        h = resp.headers
        h["Content-Security-Policy"] = CSP
        h["X-Content-Type-Options"] = "nosniff"
        h["X-Frame-Options"] = "DENY"
        h["Referrer-Policy"] = "no-referrer"
        h["Permissions-Policy"] = "microphone=(self), camera=(), geolocation=(), payment=(), usb=()"
        h["Cross-Origin-Opener-Policy"] = "same-origin"
        h["Cross-Origin-Resource-Policy"] = "same-origin"
        if os.getenv("COOKIE_SECURE", "").lower() == "true":
            h["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if "cache-control" not in h:
            # ledger data must never sit in shared caches; static files revalidate
            h["Cache-Control"] = "no-store" if path.startswith("/api/") else "no-cache"
        return resp
