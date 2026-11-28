# Security

Bolo Khata holds a shop's credit ledger: customer names, phone numbers and who owes what. That is personal and financial data, so the app is built to be safe by default even though it runs on a shop owner's own machine.

## Reporting a vulnerability

Please **don't open a public issue**. Email **shubhamsingh78882@gmail.com** with the steps to reproduce. You'll get a reply within 72 hours, and a fix or mitigation plan within 14 days for confirmed issues.

## Threat model

| Who | What they might try | What stops it |
|---|---|---|
| Someone else on the shop Wi-Fi | Open the URL and read or change the ledger | **PIN lock** (Settings → PIN lock). Every API call except health/config/login needs a session once a PIN is set |
| Someone guessing the PIN | Brute force | 5 wrong tries → 5-minute lock per device, doubling up to 1 hour. PIN stored as PBKDF2-SHA256 (200k iterations, random salt) |
| Someone who copies the database file | Log in with stolen sessions | Only SHA-256 hashes of session tokens are stored; tokens are 256-bit random |
| A malicious website the owner visits | Make the browser send requests to Bolo Khata (CSRF) | Cookies are `HttpOnly; SameSite=Strict`; every state-changing request must be `application/json` and same-origin, so cross-site forms and simple requests are rejected |
| A crafted customer name or spoken sentence | Inject script into the page (XSS) | All dynamic text is HTML-escaped; a strict **Content-Security-Policy** (`script-src 'self'`, no inline scripts or styles, no third-party origins) blocks injected script even if escaping were missed |
| A crafted sentence sent to the optional LLM | Prompt injection to write junk into the ledger | Model output is treated as untrusted: intent must be in an allow-list, amounts are bounded, names and notes are stripped of control/bidi characters and length-capped. Every entry still needs the owner's spoken or tapped confirmation |
| A crafted name exported to Excel | Formula injection (`=HYPERLINK(...)`) | Cells starting with `= + - @` tab or CR are prefixed with `'` in CSV export |
| Someone abusing the audio endpoint | Run up the speech-to-text bill or upload junk | Endpoint exists only when `STT_API_KEY` is set (else 501). Only `audio/*` types, a 700 KB cap enforced on the bytes actually received, a separate 20 requests/min/IP limit, same-origin and PIN checks like every other write |
| A bad promise date | Store garbage or a far-future date | Must parse as a real date between today and one year ahead, else 422 |
| A flood of requests | Exhaust the server | Per-IP rate limit (240/min by default), 16 KB request body cap, text inputs length-capped |
| A container breakout attempt | Escalate from the app process | Runs as non-root UID 10001, read-only root filesystem, all Linux capabilities dropped, `no-new-privileges`, memory and PID limits |
| A shared or stolen phone | Read balances from browser storage | The service worker caches only the app shell, never `/api/*` data. Locking clears the session cookie |

## Controls in the code

- `backend/app/security.py`: PIN hashing, sessions, lockout, rate limiting, origin and content-type checks, security headers (CSP, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy` allowing only the microphone, COOP/CORP, HSTS when `COOKIE_SECURE=true`).
- `backend/app/main.py`: Pydantic validation on every input (lengths, enums, ranges, phone format); generic error messages with no stack traces or echoed input; API docs off unless `ENABLE_API_DOCS=true`.
- `backend/app/db.py`: parameterised SQL only; SQLite in WAL mode with `secure_delete`; entries are never hard-deleted (cancellations are soft and logged); an audit table records entries, cancellations, setting changes, failed logins and exports.
- Every dependency version is pinned. CI runs tests, **bandit** (static analysis) and **pip-audit** (known CVEs) on every push. Dependabot keeps pip, Docker and Actions up to date.

## Privacy

- **Audio is never stored.** By default speech recognition runs in the browser (Chrome's Web Speech API); the browser vendor processes the audio to return text, as with any Chrome voice input. If the owner turns on the optional speech-to-text fallback (`STT_API_KEY`), a short clip from browsers without built-in recognition is sent through this server to the provider they chose, held in memory only, and discarded. Settings says so when it is on.
- Only the recognised sentence is kept with an entry (for resolving disputes). Set `STORE_TRANSCRIPTS=false` to keep none.
- All data lives in one SQLite file in the `khata-data` Docker volume on the owner's own machine. Nothing is sent anywhere else unless the owner sets `LLM_API_KEY`, in which case only the sentence text goes to that provider.
- The owner can download everything as CSV at any time (Settings → Download your ledger).
- Offline entries wait in the browser's local storage only until the network returns, and are removed once sent.

## Deploying beyond one shop

- Put it behind HTTPS (Caddy or nginx) and set `COOKIE_SECURE=true`. Set `TRUST_PROXY=true` only if the proxy is yours.
- Set `SEED_DEMO=false` for a real shop.
- Back up the volume: `docker run --rm -v bolo-khata_khata-data:/d -v "$PWD":/b alpine cp /d/khata.db /b/`.

## Known limitations

- A single PIN per shop. There are no separate staff accounts yet.
- The rate limiter and lockout live in memory, so they reset when the app restarts. That's fine for a single-shop deployment; a multi-tenant version would move them to Redis.
- Speech-to-text depends on the browser vendor's service, or on the provider you configure for the fallback. An on-device engine is on the roadmap.
