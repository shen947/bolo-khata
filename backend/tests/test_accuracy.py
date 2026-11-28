"""Measured accuracy of the rules parser on tests/phrases.py (no network, no keys)."""
from app.lang import name_key
from app.parser import parse

from phrases import PHRASES

BAR = 0.92   # keep in sync with the number quoted in README.md


def _ok(text, want):
    p = parse(text)
    problems = []
    for k, v in want.items():
        got = getattr(p, k)
        if k == "name":
            if name_key(got or "") != name_key(v):
                problems.append(f"name {got!r} != {v!r}")
        elif got != v:
            problems.append(f"{k} {got!r} != {v!r}")
    return problems


def test_phrase_accuracy():
    failures = []
    for text, want in PHRASES:
        bad = _ok(text, want)
        if bad:
            failures.append((text, bad))
    score = 1 - len(failures) / len(PHRASES)
    report = "\n".join(f"  {t!r}: {', '.join(b)}" for t, b in failures)
    assert score >= BAR, f"accuracy {score:.1%} < {BAR:.0%} on {len(PHRASES)} phrases\n{report}"


def test_every_entry_phrase_has_all_fields():
    """A phrase that parses to an entry must never silently drop the amount or the name."""
    for text, want in PHRASES:
        if want.get("intent") == "entry":
            p = parse(text)
            assert p.intent == "entry", text
            assert p.amount and p.name, text
