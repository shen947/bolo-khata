"""Language helpers: Devanagari -> Latin transliteration and a normaliser
so that "रमेश", "Ramesh" and "ramesh" all map to the same matching key.

The goal is matching, not perfect romanisation."""
import re
import unicodedata

VOWELS = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo", "ऋ": "ri",
    "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऍ": "e", "ऑ": "o",
}
MATRAS = {
    "ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo", "ृ": "ri", "े": "e",
    "ै": "ai", "ो": "o", "ौ": "au", "ॅ": "e", "ॉ": "o",
}
CONSONANTS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n", "च": "ch", "छ": "chh",
    "ज": "j", "झ": "jh", "ञ": "n", "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh",
    "ण": "n", "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n", "प": "p",
    "फ": "ph", "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l",
    "ळ": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h",
}
NUKTA_FORMS = {"क": "q", "ख": "kh", "ग": "g", "ज": "z", "ड": "r", "ढ": "rh", "फ": "f"}
VIRAMA = "्"
NUKTA = "़"
SIGNS = {"ं": "n", "ँ": "n", "ः": "h"}
DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
DEVANAGARI = re.compile(r"[ऀ-ॿ]")


def has_devanagari(text: str) -> bool:
    return bool(DEVANAGARI.search(text or ""))


def _translit_word(word: str) -> str:
    out = []  # list of (text, is_inherent_a)
    chars = list(unicodedata.normalize("NFC", word))
    # decompose precomposed nukta letters (e.g. ज़ U+095B)
    chars = list(unicodedata.normalize("NFD", "".join(chars)))
    i = 0
    while i < len(chars):
        c = chars[i]
        nxt = chars[i + 1] if i + 1 < len(chars) else ""
        if c in CONSONANTS:
            base = CONSONANTS[c]
            if nxt == NUKTA:
                base = NUKTA_FORMS.get(c, base)
                i += 1
                nxt = chars[i + 1] if i + 1 < len(chars) else ""
            out.append((base, False))
            if nxt in MATRAS:
                out.append((MATRAS[nxt], False))
                i += 1
            elif nxt == VIRAMA:
                i += 1
            else:
                out.append(("a", True))
        elif c in VOWELS:
            out.append((VOWELS[c], False))
        elif c in MATRAS:
            out.append((MATRAS[c], False))
        elif c in SIGNS:
            out.append((SIGNS[c], False))
        elif c in (NUKTA, VIRAMA, "‌", "‍"):
            pass
        else:
            out.append((c, False))
        i += 1
    # schwa deletion at the end of a word ("रमेश" -> ramesh, not ramesha)
    if len(out) > 2 and out[-1][1]:
        out.pop()
    return "".join(t for t, _ in out)


def transliterate(text: str) -> str:
    text = (text or "").translate(DEV_DIGITS)
    return " ".join(_translit_word(w) if has_devanagari(w) else w for w in text.split())


_NORM_RULES = [
    ("chh", "ch"), ("aa", "a"), ("ee", "i"), ("oo", "u"), ("ou", "u"),
    ("sh", "s"), ("ph", "f"), ("w", "v"), ("z", "j"), ("q", "k"), ("y", "i"),
]


def norm(token: str) -> str:
    """Normalise one token to a loose phonetic key."""
    t = transliterate(token).lower()
    t = re.sub(r"[^a-z0-9]", "", t)
    if t.isdigit():
        return t
    for a, b in _NORM_RULES:
        t = t.replace(a, b)
    t = re.sub(r"(.)\1+", r"\1", t)  # collapse doubled letters
    return t


HONORIFICS = {"ji", "jee", "bai", "bhai", "bhaia", "bhaiya", "sahab", "sab", "seth", "sir", "madam", "didi", "anti", "aunti", "ankal", "uncle", "tai", "kaka", "kaki", "mausi", "bhabhi", "babi"}


def name_key(name: str) -> str:
    parts = [norm(p) for p in re.split(r"\s+", name or "") if p]
    parts = [p for p in parts if p and p not in HONORIFICS] or [p for p in parts if p]
    return " ".join(parts)
