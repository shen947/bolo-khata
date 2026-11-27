import os
import random
import sqlite3
import threading
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from .lang import name_key

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "khata.db"))
_lock = threading.RLock()
STORE_TRANSCRIPTS = os.getenv("STORE_TRANSCRIPTS", "true").lower() in ("1", "true", "yes")

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  key TEXT NOT NULL,
  phone TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  amount REAL NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('credit','payment')),
  note TEXT,
  transcript TEXT,
  lang TEXT,
  source TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  cancelled_at TEXT
);
CREATE TABLE IF NOT EXISTS audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entry_id INTEGER,
  customer_id INTEGER,
  action TEXT NOT NULL,
  detail TEXT,
  at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT
);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY,
  expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_entries_customer ON entries(customer_id);
CREATE INDEX IF NOT EXISTS idx_entries_created ON entries(created_at);
"""


def now():
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def connect():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")      # crash-safe, readers don't block the writer
    con.execute("PRAGMA busy_timeout = 5000")
    con.execute("PRAGMA secure_delete = ON")      # cancelled data is overwritten on disk
    return con


CON = None


def get():
    global CON
    if CON is None:
        with _lock:
            if CON is None:
                con = connect()
                con.executescript(SCHEMA)
                if os.getenv("SEED_DEMO", "true").lower() in ("1", "true", "yes"):
                    if con.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
                        seed(con)
                CON = con
    return CON


def reset_for_tests(path):
    global CON, DB_PATH
    DB_PATH = path
    CON = None


# ------------------------------------------------------------------ customers
# Constant SQL fragment (no user input) reused by the queries below.
BALANCE_SQL = ("COALESCE(SUM(CASE WHEN e.status='active' AND e.type='credit' THEN e.amount "
               "WHEN e.status='active' AND e.type='payment' THEN -e.amount ELSE 0 END),0)")
# Both queries are assembled once, at import, from constants only. User values go through "?" params.
LIST_CUSTOMERS_SQL = ("SELECT c.id, c.name, c.phone, " + BALANCE_SQL + " AS balance, "
                      "MAX(CASE WHEN e.status='active' THEN e.created_at END) AS last_at "
                      "FROM customers c LEFT JOIN entries e ON e.customer_id=c.id "
                      "GROUP BY c.id ORDER BY balance DESC, c.name")
GET_CUSTOMER_SQL = ("SELECT c.id, c.name, c.phone, c.created_at, " + BALANCE_SQL + " AS balance "
                    "FROM customers c LEFT JOIN entries e ON e.customer_id=c.id WHERE c.id=? GROUP BY c.id")


def list_customers(q=None):
    con = get()
    rows = con.execute(
        LIST_CUSTOMERS_SQL).fetchall()
    out = [dict(r) for r in rows]
    if q:
        k = name_key(q)
        out = [r for r in out if k in name_key(r["name"]) or q.lower() in r["name"].lower()]
    return out


def get_customer(cid):
    con = get()
    r = con.execute(
        GET_CUSTOMER_SQL, (cid,)).fetchone()
    return dict(r) if r else None


def customer_entries(cid, limit=200):
    con = get()
    return [dict(r) for r in con.execute(
        "SELECT * FROM entries WHERE customer_id=? ORDER BY created_at DESC, id DESC LIMIT ?",
        (cid, limit))]


def create_customer(name, phone=None):
    con = get()
    with _lock:
        cur = con.execute("INSERT INTO customers(name, key, phone, created_at) VALUES (?,?,?,?)",
                          (name.strip(), name_key(name), phone, now()))
        con.execute("INSERT INTO audit(customer_id, action, detail, at) VALUES (?,?,?,?)",
                    (cur.lastrowid, "customer_created", name, now()))
        con.commit()
    return get_customer(cur.lastrowid)


def update_customer(cid, name=None, phone=None):
    con = get()
    with _lock:
        if name:
            con.execute("UPDATE customers SET name=?, key=? WHERE id=?", (name, name_key(name), cid))
        if phone is not None:
            con.execute("UPDATE customers SET phone=? WHERE id=?", (phone, cid))
        con.execute("INSERT INTO audit(customer_id, action, detail, at) VALUES (?,?,?,?)",
                    (cid, "customer_updated", f"name={name} phone={phone}", now()))
        con.commit()
    return get_customer(cid)


def _score(spoken_key, cust_key):
    if not spoken_key or not cust_key:
        return 0.0
    full = SequenceMatcher(None, spoken_key, cust_key).ratio()
    s_parts, c_parts = spoken_key.split(), cust_key.split()
    first = SequenceMatcher(None, s_parts[0], c_parts[0]).ratio()
    if len(s_parts) == 1:
        # "Ramesh" should match both "Ramesh" and "Ramesh Patil" strongly
        return max(full, first * (1.0 if len(c_parts) == 1 else 0.97))
    if len(c_parts) == 1:
        return max(full, first * 0.85)
    return full


def match_customers(name):
    """Return (status, matches) where status is exact|ambiguous|new."""
    k = name_key(name)
    scored = []
    for c in list_customers():
        s = _score(k, name_key(c["name"]))
        if s >= 0.72:
            scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    if not scored or scored[0][0] < 0.8:
        return "new", [c for _, c in scored[:3]]
    best = scored[0][0]
    close = [c for s, c in scored if best - s <= 0.06]
    if len(close) == 1:
        return "exact", [scored[0][1]]
    return "ambiguous", close[:4]


# ------------------------------------------------------------------ entries
def add_entry(customer_id, amount, type_, note=None, transcript=None, lang=None, source="voice", created_at=None):
    con = get()
    with _lock:
        cur = con.execute(
            """INSERT INTO entries(customer_id, amount, type, note, transcript, lang, source, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (customer_id, round(float(amount), 2), type_, note, transcript if STORE_TRANSCRIPTS else None,
             lang, source, created_at or now()))
        con.execute("INSERT INTO audit(entry_id, customer_id, action, detail, at) VALUES (?,?,?,?,?)",
                    (cur.lastrowid, customer_id, "entry_created", f"{type_} {amount}", now()))
        con.commit()
    return get_entry(cur.lastrowid)


def get_entry(eid):
    r = get().execute(
        "SELECT e.*, c.name AS customer_name FROM entries e JOIN customers c ON c.id=e.customer_id WHERE e.id=?",
        (eid,)).fetchone()
    return dict(r) if r else None


def cancel_entry(eid, reason="voice undo"):
    con = get()
    with _lock:
        con.execute("UPDATE entries SET status='cancelled', cancelled_at=? WHERE id=? AND status='active'", (now(), eid))
        con.execute("INSERT INTO audit(entry_id, action, detail, at) VALUES (?,?,?,?)", (eid, "entry_cancelled", reason, now()))
        con.commit()
    return get_entry(eid)


def last_active_entry():
    r = get().execute("SELECT id FROM entries WHERE status='active' ORDER BY created_at DESC, id DESC LIMIT 1").fetchone()
    return get_entry(r["id"]) if r else None


def recent_entries(limit=8):
    return [dict(r) for r in get().execute(
        """SELECT e.*, c.name AS customer_name FROM entries e JOIN customers c ON c.id=e.customer_id
           ORDER BY e.created_at DESC, e.id DESC LIMIT ?""", (limit,))]


def summary():
    con = get()
    today = datetime.now().date().isoformat()
    t = con.execute(
        """SELECT COALESCE(SUM(CASE WHEN type='credit' THEN amount END),0) AS given,
                  COALESCE(SUM(CASE WHEN type='payment' THEN amount END),0) AS collected,
                  COUNT(*) AS n
           FROM entries WHERE status='active' AND substr(created_at,1,10)=?""", (today,)).fetchone()
    custs = list_customers()
    outstanding = sum(c["balance"] for c in custs if c["balance"] > 0)
    overdue_cut = (datetime.now() - timedelta(days=30)).isoformat(sep=" ")
    return {
        "today_given": t["given"], "today_collected": t["collected"], "today_count": t["n"],
        "outstanding": outstanding,
        "customers_due": sum(1 for c in custs if c["balance"] > 0),
        "customers_total": len(custs),
        "stale_due": sum(1 for c in custs if c["balance"] > 0 and (c["last_at"] or "") < overdue_cut),
        "recent": recent_entries(8),
    }


def today_credit_customers():
    today = datetime.now().date().isoformat()
    return [dict(r) for r in get().execute(
        """SELECT c.id, c.name, SUM(e.amount) AS amount FROM entries e JOIN customers c ON c.id=e.customer_id
           WHERE e.status='active' AND e.type='credit' AND substr(e.created_at,1,10)=?
           GROUP BY c.id ORDER BY amount DESC""", (today,))]


# ------------------------------------------------------------------ settings / sessions
def get_setting(key, default=None):
    with _lock:
        r = get().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return r["value"] if r else default


def set_setting(key, value):
    con = get()
    with _lock:
        if value is None:
            con.execute("DELETE FROM settings WHERE key=?", (key,))
        else:
            con.execute("INSERT INTO settings(key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
        con.execute("INSERT INTO audit(action, detail, at) VALUES (?,?,?)", ("setting_changed", key, now()))
        con.commit()


def add_session(token_hash, expires_at):
    con = get()
    with _lock:
        con.execute("DELETE FROM sessions WHERE expires_at < ?", (now(),))
        con.execute("INSERT INTO sessions(token_hash, expires_at) VALUES (?,?)", (token_hash, expires_at))
        con.commit()


def session_valid(token_hash, at):
    with _lock:
        r = get().execute("SELECT 1 FROM sessions WHERE token_hash=? AND expires_at > ?", (token_hash, at)).fetchone()
    return bool(r)


def delete_session(token_hash):
    con = get()
    with _lock:
        con.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash,))
        con.commit()


def clear_sessions():
    con = get()
    with _lock:
        con.execute("DELETE FROM sessions")
        con.commit()


def export_rows():
    with _lock:
        return [dict(r) for r in get().execute(
            """SELECT e.id, e.created_at, c.name AS customer, c.phone, e.type, e.amount, e.note, e.status,
                      e.cancelled_at, e.lang, e.source
               FROM entries e JOIN customers c ON c.id=e.customer_id ORDER BY e.created_at, e.id""")]


def add_audit(action, detail=None):
    con = get()
    with _lock:
        con.execute("INSERT INTO audit(action, detail, at) VALUES (?,?,?)", (action, detail, now()))
        con.commit()


def audit_log(limit=100):
    return [dict(r) for r in get().execute("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (limit,))]


# ------------------------------------------------------------------ demo seed
SEED_CUSTOMERS = [
    "Ramesh Patil", "Sunita Bhabhi", "Pappu Doodhwala", "Mohan Lal", "Anita Kulkarni",
    "Imran Bhai", "Lakshmi Amma", "Raju Auto", "Kavita Joshi", "Ganesh Shinde",
]
SEED_ITEMS = ["atta 5 kg", "doodh", "tel", "chawal", "sabun", "chini", "dal", "masala", "biscuit", None]


def seed(con):
    """Realistic demo ledger: entries between 9am and 9pm over the last ~7 weeks,
    payments never exceed what the customer owed at that time."""
    rnd = random.Random(7)
    now_ = datetime.now()
    for name in SEED_CUSTOMERS:
        cur = con.execute("INSERT INTO customers(name, key, phone, created_at) VALUES (?,?,?,?)",
                          (name, name_key(name), None, (now_ - timedelta(days=60)).isoformat(sep=" ")))
        cid = cur.lastrowid
        days = sorted(rnd.sample(range(1, 50), rnd.randint(4, 8)), reverse=True)
        bal = 0
        for d in days:
            ts = (now_ - timedelta(days=d)).replace(hour=rnd.randint(9, 20), minute=rnd.randint(0, 59), second=0, microsecond=0)
            if bal > 200 and rnd.random() < 0.4:
                t, amt = "payment", min(bal, rnd.choice([100, 200, 300, 500, bal]))
                note = None
            else:
                t, amt = "credit", rnd.choice([40, 60, 90, 120, 150, 180, 250, 300, 450])
                note = rnd.choice(SEED_ITEMS)
            bal += amt if t == "credit" else -amt
            con.execute(
                """INSERT INTO entries(customer_id, amount, type, note, transcript, lang, source, created_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (cid, amt, t, note, None, "hi", "seed", ts.isoformat(sep=" ")))
    con.commit()
