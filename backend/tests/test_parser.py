import pytest

from app.parser import parse

ENTRIES = [
    # text, name, amount, type
    ("Ramesh ne 250 ka saman liya udhaar", "Ramesh", 250, "credit"),
    ("रमेश ने 250 का सामान लिया", "रमेश", 250, "credit"),
    ("Sunita ne 500 jama kiye", "Sunita", 500, "payment"),
    ("सुनीता भाभी ने 500 जमा किए", "सुनीता भाभी", 500, "payment"),
    ("Pappu ko 3 packet doodh diya 90 rupaye", "Pappu", 90, "credit"),
    ("Mohan ne dhai sau ka atta liya", "Mohan", 250, "credit"),
    ("Mohan ne do hazaar paanch sau diye", "Mohan", 2500, "payment"),
    ("Ramesh ne saade teen sau ka saman liya", "Ramesh", 350, "credit"),
    ("रमेशने 300 रुपयांचे सामान घेतले", "रमेश", 300, "credit"),
    ("सुनीताने 200 रुपये जमा केले", "सुनीता", 200, "payment"),
    ("Ramesh took 250 on credit", "Ramesh", 250, "credit"),
    ("Ramesh paid 500", "Ramesh", 500, "payment"),
    ("three hundred fifty Ramesh credit", "Ramesh", 350, "credit"),
    ("Imran bhai ne ₹1,200 UPI se bhare", "Imran Bhai", 1200, "payment"),
    ("Kavita ji 150rs udhaar", "Kavita", 150, "credit"),
]


@pytest.mark.parametrize("text,name,amount,type_", ENTRIES)
def test_entries(text, name, amount, type_):
    p = parse(text)
    assert p.intent == "entry"
    assert p.name == name
    assert p.amount == amount
    assert p.type == type_


@pytest.mark.parametrize("text,intent,name", [
    ("Ramesh ka kitna baaki hai?", "balance", "Ramesh"),
    ("रमेश का कितना बाकी है", "balance", "रमेश"),
    ("रमेशचे किती बाकी आहे", "balance", "रमेश"),
    ("How much does Ramesh owe?", "balance", "Ramesh"),
    ("aaj kis kis ka udhaar hai", "today", None),
    ("आज किस किस का उधार है", "today", None),
    ("sabse zyada kiska baaki hai", "top", None),
    ("सबसे ज़्यादा किसका बाकी है", "top", None),
    ("kul kitna udhaar baaki hai", "total", None),
    ("pichli entry cancel karo", "undo", None),
    ("पिछली एंट्री कैंसल करो", "undo", None),
])
def test_queries(text, intent, name):
    p = parse(text)
    assert p.intent == intent
    assert p.name == name


def test_missing_amount_then_followup():
    p = parse("Ramesh ne saman liya")
    assert p.intent == "entry" and p.amount is None and p.name == "Ramesh"
    p2 = parse("300", {"awaiting": "amount", "name": "Ramesh", "type": "credit"})
    assert (p2.name, p2.amount, p2.type) == ("Ramesh", 300, "credit")


def test_default_type_is_flagged():
    p = parse("Ramesh 200")
    assert p.type == "credit" and p.type_defaulted


def test_quantity_is_not_amount():
    p = parse("Pappu ko 3 packet doodh diya 90 rupaye")
    assert p.amount == 90 and "doodh" in p.note


@pytest.mark.parametrize("text,intent", [("haan", "yes"), ("हाँ सही है", "yes"), ("nahi", "no"), ("नहीं", "no"), ("yes", "yes")])
def test_confirm_words(text, intent):
    assert parse(text, {"awaiting": "confirm"}).intent == intent
