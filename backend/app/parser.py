"""Rules-based parser for one spoken shop-counter sentence.

Works with no API key. Handles Hindi (Devanagari or romanised), Hinglish,
Marathi and English, e.g.
    "Ramesh ne 250 ka saman liya udhaar"
    "रमेश ने 250 का सामान लिया"
    "Sunita ne 500 jama kiye"
    "Pappu ko 3 packet doodh diya 90 rupaye"
    "Ramesh ka kitna baaki hai?"
    "aaj kis kis ka udhaar hai"
"""
import re
from dataclasses import dataclass, field, asdict
from typing import Optional

from .lang import norm, transliterate, HONORIFICS

# ---------------------------------------------------------------- numbers
UNITS = {
    # Hindi / Marathi (normalised keys)
    "ek": 1, "do": 2, "don": 2, "tin": 3, "char": 4, "pach": 5, "panch": 5, "pac": 5,
    "chah": 6, "sat": 7, "sath": 60, "ath": 8, "nau": 9, "nav": 9,
    "das": 10, "dah": 10, "giarah": 11, "giara": 11, "barah": 12, "bara": 12,
    "terah": 13, "tera": 13, "chodah": 14, "chauda": 14, "pandrah": 15, "pandra": 15,
    "solah": 16, "sola": 16, "satrah": 17, "atharah": 18, "unis": 19, "bis": 20,
    "pachis": 25, "tis": 30, "pentis": 35, "chalis": 40, "paintalis": 45,
    "pachas": 50, "pachpan": 55, "satar": 70, "pachatar": 75, "asi": 80, "nabe": 90,
    "dedh": 1.5, "derh": 1.5, "dhai": 2.5, "adhai": 2.5,
    # English
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15,
    "twenti": 20, "twenty": 20, "thirti": 30, "forti": 40, "fifti": 50, "sixti": 60,
    "seventi": 70, "eighti": 80, "nineti": 90, "half": 0.5,
}
MULT = {"sau": 100, "sav": 100, "hundred": 100, "hajar": 1000,
        "hajaar": 1000, "thousand": 1000, "lak": 100000, "lakh": 100000, "lac": 100000}
FRACT_PREFIX = {"sade": 0.5, "sadhe": 0.5, "sarhe": 0.5, "sava": 0.25, "pone": -0.25, "paune": -0.25}

# ---------------------------------------------------------------- keywords (normalised)
CURRENCY = {"rs", "rupe", "rupae", "rupie", "rupia", "rupai", "rupees", "rupes", "rupee", "ru", "rupaia", "rupaie", "rupaye", "inr", "rupei", "rupa", "rupaian", "rupaiache", "rupaiachi"}
PAYMENT_STRONG = {"jama", "jma", "chukaia", "chukae", "chukai", "chukaie", "vapas", "vapis", "lautae", "lautaia", "lotae", "lotaia", "paid", "pai", "pay", "paiment", "payment", "received", "recived", "receive", "return", "returned", "bhare", "bharle", "bharla", "bharli", "upi", "gpai", "gpay", "fonpe", "phonepe", "paytm", "clear", "cleared", "jmakie", "jamakie"}
GIVE_VERBS = {"die", "dia", "de", "diia", "dile", "dila", "dili", "deke", "dedie", "gave", "given"}
CREDIT_KW = {"udhar", "udhari", "udar", "udari", "udhaar", "lia", "le", "lie", "liia", "legaia", "lekar", "leke", "saman", "saaman", "maal", "mal", "credit", "took", "taken", "bought", "ghetle", "ghetla", "ghetli", "ghetale", "nele", "nela", "neli", "khata", "khate", "purchase"}
MARKERS_SUBJ = {"ne", "ni", "nin"}          # Ramesh ne ... (subject)
MARKERS_OBJ = {"ko", "la"}       # Pappu ko ... (recipient)
MARKERS_POSS = {"ka", "ki", "ke", "che", "chi", "cha", "kade", "iance", "ianche", "iancha", "ianchi"}
QUESTION = {"kitna", "kitne", "kitni", "kitana", "kitane", "kitani", "kiti", "kitni", "how", "much", "balance", "bakaia", "bakaya", "owe", "owes", "due", "batao", "bolo", "sangha", "sanga", "?"}
DUE_WORDS = {"baki", "baaki", "bakaia", "balance", "due", "owe", "owes", "pending", "outstanding", "lene", "dene", "udhar", "hisab", "hisaab"}
TODAY = {"aj", "aaj", "today"}
WHO = {"kis", "kisne", "kisko", "kon", "kaun", "kaunse", "who", "kona", "konache", "konala", "konakade", "list", "sab", "sare", "sabhi"}
TOP = {"sabse", "sabase", "jiada", "jada", "jyada", "ziada", "most", "highest", "top", "sarvat", "jast", "biggest"}
TOTAL = {"kul", "total", "overall", "ekun", "milake", "milakar"}
UNDO = {"cancel", "undo", "rad", "radd", "hatao", "hata", "delete", "galat", "mitao", "mita", "remove", "wrong", "kat", "kato", "katao", "rada", "kainsal", "kensal", "kansal"}
LAST = {"pichli", "pichla", "last", "previous", "akhri", "shevti", "magil", "abhi", "pichle", "pichali", "pichale", "pichla"}
YES = {"han", "haan", "ha", "hm", "hmm", "ji", "yes", "sahi", "thik", "thek", "barobar", "ok", "okay", "ho", "hoi", "bilkul", "correct", "right", "save"}
NO = {"nahi", "nai", "na", "no", "nako", "galat", "wrong", "cancel", "nahin", "mat", "nahi"}

# --- "kal dega" style promises: a time word + a future verb
FUTURE_VERBS = {"dega", "degi", "denge", "dengi", "dunga", "dungi", "dege", "dene", "dein", "deta", "deti", "deto", "dete",
                "diel", "deil", "deu", "denar", "denare", "dungaa", "will", "shall", "promised", "promises", "promise"}
FUTURE_SUFFIX = ("ega", "egi", "enge", "unga", "ungi", "engi")     # lautaega, chukaegi, layenge ...
T_TOMORROW = {"kal", "udia", "tomorov", "tomoro", "kl"}
T_AFTER = {"parason", "parava", "parso", "parsu", "parson", "parsoon"}
T_TODAY = {"aj", "sam", "tonight", "evening", "sanj", "sanjh", "sandhia", "tonite", "today"}
U_DAY = {"din", "divas", "dinon", "days", "day"}
U_WEEK = {"hafte", "hafta", "saptah", "week", "weeks", "athvade", "aathvade"}
U_MONTH = {"mahine", "mahina", "month", "months", "mahinia", "mahinyat"}

STOP = {
    "aj", "abhi", "kal", "sam", "subah", "subh", "rat", "se", "mein", "me", "mai", "par", "pe",
    "aur", "or", "and", "hai", "he", "ha", "tha", "the", "thi", "ho", "hua", "hue", "gaia", "gaya", "gia",
    "gai", "gae", "kar", "kie", "kia", "kiye", "kiia", "karo", "karna", "diia", "the", "a", "an", "of",
    "for", "on", "to", "has", "have", "had", "is", "was", "from", "rupe", "ka", "ki", "ke", "uska", "uske",
    "unka", "unke", "apna", "aapka", "mera", "hamara", "vala", "vale", "vali", "packet", "paket", "kilo",
    "kg", "litre", "liter", "ltr", "gram", "dabba", "bori", "bag", "pis", "piece", "pieces", "aahe",
    "ahe", "ahet", "kele", "keli", "kela", "zale", "jhale", "ata", "atta" , "tak", "liie", "liye", "lie",
    "worth", "of", "credit", "plis", "please", "bhaiia", "entri", "entry", "naam", "nam", "name",
    "customer", "grahak", "add", "dalo", "daalo", "jodo", "ab", "fir", "phir", "bhi", "does", "did", "much", "how", "what", "kitna",
}
ITEM_HINTS = {"dud", "doodh", "dudh", "ata", "atta", "chaval", "caval", "dal", "tel", "oil", "sabun", "chini", "sugar", "chai", "biskut", "biscuit", "masala", "anda", "ande", "bread", "maida", "rice", "namak", "ghi", "ghee", "surf", "saman", "maal", "mal", "sigret", "gutka", "paneer", "dahi", "makhan", "batter", "butter", "kirana", "rashan", "rasan", "gas", "kerosin"}


def _N(s):
    return {norm(x) if x != "?" else x for x in s}


UNITS = {norm(k): v for k, v in UNITS.items()}
MULT = {norm(k): v for k, v in MULT.items()}
FRACT_PREFIX = {norm(k): v for k, v in FRACT_PREFIX.items()}
(CURRENCY, PAYMENT_STRONG, GIVE_VERBS, CREDIT_KW, MARKERS_SUBJ, MARKERS_OBJ, MARKERS_POSS,
 QUESTION, DUE_WORDS, TODAY, WHO, TOP, TOTAL, UNDO, LAST, YES, NO, STOP, ITEM_HINTS,
 FUTURE_VERBS, T_TOMORROW, T_AFTER, T_TODAY, U_DAY, U_WEEK, U_MONTH) = map(_N, (
    CURRENCY, PAYMENT_STRONG, GIVE_VERBS, CREDIT_KW, MARKERS_SUBJ, MARKERS_OBJ, MARKERS_POSS,
    QUESTION, DUE_WORDS, TODAY, WHO, TOP, TOTAL, UNDO, LAST, YES, NO, STOP, ITEM_HINTS,
    FUTURE_VERBS, T_TOMORROW, T_AFTER, T_TODAY, U_DAY, U_WEEK, U_MONTH))
_WILL = {norm("will"), norm("shall")}
_WILL_VERBS = {norm(w) for w in ("bring", "give", "settle")}
PROMISE_WORDS = FUTURE_VERBS | T_TOMORROW | T_AFTER | T_TODAY | U_DAY | U_WEEK | U_MONTH
CURRENCY_STEMS = _N({"rupaian", "rupaia", "rupae"})


@dataclass
class Parsed:
    intent: str = "unknown"          # entry | balance | today | top | total | undo | yes | no | unknown
    name: Optional[str] = None
    amount: Optional[float] = None
    type: Optional[str] = None       # credit | payment
    type_defaulted: bool = False
    note: Optional[str] = None
    promise_days: Optional[int] = None   # "kal dega" -> 1 (days from today); None = no promise
    confidence: float = 0.0
    transcript: str = ""
    source: str = "rules"

    def dict(self):
        return asdict(self)


DEV_SUFFIXES = ["कडे", "ने", "ला", "चे", "ची", "चा", "चं", "नी"]
KEEP_WHOLE = {"कोणाला", "मला", "तुला", "त्याला", "आपला", "माझा", "उधारीचे"}


def _split_suffix(tok: str):
    """Marathi glues case markers onto names: "रमेशने" -> "रमेश", "ने"."""
    if re.search(r"[\u0900-\u097F]", tok) and tok not in KEEP_WHOLE:
        for suf in DEV_SUFFIXES:
            if tok.endswith(suf) and len(tok) - len(suf) >= 2:
                stem = tok[: -len(suf)]
                if norm(stem) not in CURRENCY_STEMS:
                    return [stem, suf]
                return [tok]
    return [tok]



def _tokenise(text: str):
    text = (text or "").replace("₹", " rs ").replace(",", "")
    # split "250rs" / "rs250"
    text = re.sub(r"(\d)([^\d\s.])", r"\1 \2", text)
    text = re.sub(r"([^\d\s.])(\d)", r"\1 \2", text)
    raw = [t for t in re.split(r"[\s\.!।,;:]+|(?<=\S)\?|\?(?=\S)", text) if t]
    toks = []
    for r in raw:
        if r == "?":
            toks.append(("?", "?"))
            continue
        clean = r.strip("\"'()[]{}")
        if not clean:
            continue
        for part in _split_suffix(clean):
            n = norm(part)
            if n.endswith("ase") and n[:-3] in UNITS and re.search(r"[\u0900-\u097F]", part):
                toks.append((part, n[:-3]))      # "तीनशे" -> three hundred
                toks.append(("शे", "sau"))
            else:
                toks.append((part, n))
    if "?" in text and not any(n == "?" for _, n in toks):
        toks.append(("?", "?"))
    return toks


def _is_number_tok(n: str) -> bool:
    return bool(re.fullmatch(r"\d+(\.\d+)?", n)) or n in UNITS or n in MULT or n in FRACT_PREFIX


def _small_number(n):
    if re.fullmatch(r"\d+", n):
        return int(n)
    v = UNITS.get(n)
    return int(v) if v and float(v).is_integer() else None


def _promise(toks):
    """Find "will pay tomorrow"-style promises. Returns (days_from_today | None, token_indexes_used)."""
    norms = [n for _, n in toks]
    fut = {i for i, n in enumerate(norms) if n in FUTURE_VERBS or (len(n) >= 4 and n.endswith(FUTURE_SUFFIX))}
    if not fut:
        return None, set()
    days, used = None, set()
    for i, n in enumerate(norms):
        if n in T_AFTER:
            days, used = 2, {i}
        elif n in T_TOMORROW:
            days, used = 1, {i}
        elif n in T_TODAY and days is None:
            days, used = 0, {i}
        elif n in U_DAY | U_WEEK | U_MONTH:
            q = _small_number(norms[i - 1]) if i > 0 else None
            if q is None and n in U_DAY:
                continue                                  # a bare "din" is not a date
            q = q or 1
            days = q * (1 if n in U_DAY else 7 if n in U_WEEK else 30)
            used = {i} | ({i - 1} if i > 0 and _small_number(norms[i - 1]) is not None else set())
        if days is not None and n not in T_TODAY:
            break
    if days is None or days > 365:
        return None, set()
    used |= fut
    for i in fut:                                         # "will pay" / "will return": swallow the verb too
        if norms[i] in _WILL and i + 1 < len(norms) and norms[i + 1] in (PAYMENT_STRONG | GIVE_VERBS | _WILL_VERBS):
            used.add(i + 1)
    return days, used


def _parse_amount(toks, skip=frozenset()):
    """Return (amount, set_of_token_indexes_used). Picks the number run that is
    most likely the rupee amount (next to a currency word, else the largest)."""
    runs, i = [], 0
    while i < len(toks):
        if _is_number_tok(toks[i][1]) and i not in skip:
            j = i
            while j < len(toks) and _is_number_tok(toks[j][1]) and j not in skip:
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    best, best_score, used = None, -1, set()
    for (a, b) in runs:
        total, cur, frac = 0.0, 0.0, 0.0
        only_mult = True
        for k in range(a, b):
            n = toks[k][1]
            if re.fullmatch(r"\d+(\.\d+)?", n):
                cur += float(n) + frac; frac = 0; only_mult = False
            elif n in FRACT_PREFIX:
                frac = FRACT_PREFIX[n]
            elif n in UNITS:
                cur += UNITS[n] + frac; frac = 0; only_mult = False
            elif n in MULT:
                m = MULT[n]
                if m >= 1000:
                    total += (cur or 1) * m; cur = 0
                else:
                    cur = (cur or 1) * m
        value = total + cur
        nxt = toks[b][1] if b < len(toks) else ""
        prv = toks[a - 1][1] if a > 0 else ""
        if value <= 0:
            continue
        if only_mult and not (nxt in CURRENCY or prv in CURRENCY or nxt in MARKERS_POSS):
            continue                              # a bare "sau" is only money when it sits by "rupaye"/"ka"
        score = value / 1e6
        if nxt in CURRENCY or prv in CURRENCY:
            score += 10
        if nxt in {"ka", "ki", "ke", "ki", "cha", "che", "chi"}:
            score += 5  # "250 ka saman"
        if nxt in {"paket", "packet", "kilo", "kg", "litre", "liter", "ltr", "dabba", "bori", "pis", "piece", "pieces"}:
            score -= 8  # "3 packet" is a quantity, not money
        if score > best_score:
            best, best_score, used = value, score, set(range(a, b))
    if best is not None:
        best = round(best, 2)
        if best == int(best):
            best = int(best)
    return best, used


def _keyword_sets(norms):
    s = set(norms)
    # fuzzy: compound words "lelia", "legaia", "dedia"
    joined = " ".join(norms)
    return s, joined


def _extract_name(toks, used):
    norms = [n for _, n in toks]
    skip = (STOP | CURRENCY | PAYMENT_STRONG | GIVE_VERBS | CREDIT_KW | QUESTION | DUE_WORDS
            | TODAY | WHO | TOP | TOTAL | UNDO | LAST | ITEM_HINTS | MARKERS_SUBJ | MARKERS_OBJ | MARKERS_POSS
            | PROMISE_WORDS)

    def name_like(k):
        o, n = toks[k]
        return (k not in used and n and n not in skip and not (len(n) >= 4 and n.endswith(FUTURE_SUFFIX)) and not _is_number_tok(n)
                and not re.fullmatch(r"\d.*", n) and n != "?")

    # 1) token(s) right before a case marker: "Ramesh ne", "Pappu ko", "Ramesh ka"
    for k, n in enumerate(norms):
        if k > 0 and n in (MARKERS_SUBJ | MARKERS_OBJ | MARKERS_POSS):
            j = k - 1
            parts = []
            while j >= 0 and len(parts) < 3 and (name_like(j) or (parts and norms[j] in HONORIFICS)):
                parts.insert(0, toks[j][0]); j -= 1
            if parts:
                return " ".join(parts), n
    # 2) first contiguous run of name-like tokens
    for k in range(len(toks)):
        if name_like(k):
            parts = [toks[k][0]]
            j = k + 1
            while j < len(toks) and len(parts) < 3 and (name_like(j) or norms[j] in HONORIFICS):
                parts.append(toks[j][0]); j += 1
            return " ".join(parts), None
    return None, None


def _clean_name(name):
    if not name:
        return None
    parts = [p for p in name.split() if norm(p) not in {"ji", "jee"}]
    name = " ".join(parts).strip()
    if not name:
        return None
    if not re.search(r"[ऀ-ॿ]", name):
        name = " ".join(p[:1].upper() + p[1:] for p in name.split())
    return name


def _note(toks, used, name):
    name_norms = {norm(p) for p in (name or "").split()}
    items = []
    for k, (o, n) in enumerate(toks):
        if k in used or n in name_norms:
            continue
        if n in ITEM_HINTS and n not in {"saman", "maal", "mal"}:
            # keep the quantity before an item ("3 packet doodh")
            q = []
            if k >= 2 and re.fullmatch(r"\d+", toks[k - 2][1]) and toks[k - 1][1] in {"paket", "packet", "kilo", "kg", "litre", "liter", "dabba"}:
                q = [toks[k - 2][0], toks[k - 1][0]]
            elif k >= 1 and re.fullmatch(r"\d+", toks[k - 1][1]) and (k - 1) not in used:
                q = [toks[k - 1][0]]
            items.append(" ".join(q + [o]))
    return ", ".join(items) if items else None


def parse(text: str, context: Optional[dict] = None) -> Parsed:
    p = Parsed(transcript=text or "")
    toks = _tokenise(text)
    if not toks:
        return p
    norms = [n for _, n in toks]
    s, joined = _keyword_sets(norms)
    context = context or {}

    # --- confirmation replies ("haan" / "nahi") while a card is open
    if context.get("awaiting") == "confirm" and len(norms) <= 4:
        if s & NO and not (s & {"sahi"}):
            p.intent, p.confidence = "no", 0.9
            return p
        if s & YES:
            p.intent, p.confidence = "yes", 0.9
            return p

    promise_days, promise_idx = _promise(toks)
    amount, used = _parse_amount(toks, skip=promise_idx)
    used = used | promise_idx
    name, marker = _extract_name(toks, used)
    name = _clean_name(name)

    # --- commands and questions
    if s & UNDO and (s & LAST or len(norms) <= 5 or "entri" in s or "entry" in s):
        p.intent, p.confidence = "undo", 0.9
        return p
    is_question = bool(s & QUESTION) or "?" in s
    if (s & TODAY) and (s & WHO) and amount is None:
        p.intent, p.confidence = "today", 0.85
        return p
    if (s & TOP) and amount is None and (s & DUE_WORDS or s & WHO or s & QUESTION):
        p.intent, p.confidence = "top", 0.85
        return p
    if (s & TOTAL) and amount is None and not name:
        p.intent, p.confidence = "total", 0.85
        return p
    if amount is None and name and (is_question or s & DUE_WORDS) and not (s & PAYMENT_STRONG):
        p.intent, p.name, p.confidence = "balance", name, 0.85
        return p
    if amount is None and not name and (s & DUE_WORDS) and (s & TOTAL or is_question):
        p.intent, p.confidence = "total", 0.6
        return p

    # "Ramesh kal dega" / "Ramesh will pay 500 tomorrow" (no new purchase): only the promise date changes
    if promise_days is not None and name:
        words = {n for k, n in enumerate(norms) if k not in promise_idx}
        if not (words & (CREDIT_KW | PAYMENT_STRONG | GIVE_VERBS)):
            p.intent, p.name, p.promise_days, p.confidence = "promise", name, promise_days, 0.8
            return p

    # --- ledger entry (promise words are not part of what was bought or paid)
    s = {n for k, n in enumerate(norms) if k not in promise_idx}
    joined = " ".join(n for k, n in enumerate(norms) if k not in promise_idx)
    credit_hits = s & CREDIT_KW or any(w in joined for w in ("lelia", "legaia", "lekegaia", "udhar"))
    pay_hits = s & PAYMENT_STRONG
    give_hits = s & GIVE_VERBS
    t, defaulted = None, False
    if pay_hits and not (s & {"udhar", "udhari", "udar", "udhaar"}):
        t = "payment"
    elif marker in MARKERS_OBJ and (give_hits or credit_hits):
        t = "credit"                     # "Pappu ko doodh diya" -> we gave on credit
    elif credit_hits:
        t = "credit"
    elif give_hits and marker in MARKERS_SUBJ:
        t = "payment"                    # "Sunita ne 500 diye" -> she paid
    elif context.get("type"):
        t = context["type"]
    else:
        t, defaulted = "credit", True

    # merge with context from a follow-up question ("Kitne rupaye?")
    if context.get("awaiting") in ("amount", "name"):
        if amount is None and context.get("amount") is not None:
            amount = context["amount"]
        if not name and context.get("name"):
            name = context["name"]
        if context.get("type") and not (pay_hits or credit_hits or give_hits):
            t, defaulted = context["type"], context.get("type_defaulted", False)

    p.name, p.amount, p.type, p.type_defaulted = name, amount, t, defaulted
    p.promise_days = promise_days if t == "credit" else None
    p.note = _note(toks, used, name)
    if amount is not None or name:
        p.intent = "entry"
        conf = 0.4
        if amount is not None:
            conf += 0.3
        if name:
            conf += 0.2
        if not defaulted:
            conf += 0.1
        p.confidence = round(min(conf, 1.0), 2)
    return p


def describe(text: str):
    """Debug helper."""
    return parse(text).dict() | {"latin": transliterate(text)}
