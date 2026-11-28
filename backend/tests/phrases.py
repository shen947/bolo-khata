"""Regression phrase set: what a shopkeeper might actually say at the counter.

Each row: (spoken text, expected). `expected` may hold intent, name, amount, type.
test_accuracy.py scores the rules parser on this set and fails if it drops
below the bar in the README, so a parser change can never silently get worse.
(The first 58 rows were written first and used to find bugs: 89.7% before fixes.
The last block was written afterwards and never tuned against.)
"""

E = "entry"
PHRASES = [
    # ---------- Hindi / Hinglish, romanised
    ("Ramesh ne 250 ka saman liya", dict(intent=E, name="Ramesh", amount=250, type="credit")),
    ("Ramesh ne 250 ka saman liya udhaar", dict(intent=E, name="Ramesh", amount=250, type="credit")),
    ("Sunita ne 500 jama kiye", dict(intent=E, name="Sunita", amount=500, type="payment")),
    ("Sunita ne paanch sau rupaye diye", dict(intent=E, name="Sunita", amount=500, type="payment")),
    ("Pappu ko 3 packet doodh diya 90 rupaye", dict(intent=E, name="Pappu", amount=90, type="credit")),
    ("Mohan bhaiya ne dhai sau ka udhaar liya", dict(intent=E, name="Mohan", amount=250, type="credit")),
    ("Geeta ne saade teen sau jama kiye", dict(intent=E, name="Geeta", amount=350, type="payment")),
    ("Suresh ne 1200 rupaye wapas kiye", dict(intent=E, name="Suresh", amount=1200, type="payment")),
    ("Anil ko 75 ka tel udhaar diya", dict(intent=E, name="Anil", amount=75, type="credit")),
    ("Kavita ne ek hazaar jama karaye", dict(intent=E, name="Kavita", amount=1000, type="payment")),
    ("Raju ne dedh sau ka atta liya", dict(intent=E, name="Raju", amount=150, type="credit")),
    ("Meena ne 300 rupaye gpay kiye", dict(intent=E, name="Meena", amount=300, type="payment")),
    ("Vijay ne paytm se 450 bheje", dict(intent=E, name="Vijay", amount=450, type="payment")),
    ("Dinesh ne 2000 ka saman udhar liya", dict(intent=E, name="Dinesh", amount=2000, type="credit")),
    ("Lakshmi ne 60 rupaye ki chini li", dict(intent=E, name="Lakshmi", amount=60, type="credit")),
    ("Rahul ne pachas rupaye jama kiye", dict(intent=E, name="Rahul", amount=50, type="payment")),
    ("Ajay ne sau rupaye ka biscuit udhaar liya", dict(intent=E, name="Ajay", amount=100, type="credit")),
    ("Farida ne 800 chukaye", dict(intent=E, name="Farida", amount=800, type="payment")),
    ("Bablu ko 40 rupaye ka chai patti diya", dict(intent=E, name="Bablu", amount=40, type="credit")),
    ("Neha ne 1500 ka maal liya", dict(intent=E, name="Neha", amount=1500, type="credit")),
    # ---------- Hindi, Devanagari
    ("रमेश ने 250 का सामान लिया", dict(intent=E, name="रमेश", amount=250, type="credit")),
    ("सुनीता ने 500 जमा किए", dict(intent=E, name="सुनीता", amount=500, type="payment")),
    ("मोहन ने दो सौ रुपये उधार लिए", dict(intent=E, name="मोहन", amount=200, type="credit")),
    ("गीता ने तीन सौ रुपये वापस किए", dict(intent=E, name="गीता", amount=300, type="payment")),
    ("पप्पू को 90 रुपये का दूध दिया", dict(intent=E, name="पप्पू", amount=90, type="credit")),
    ("सुरेश ने एक हजार जमा किए", dict(intent=E, name="सुरेश", amount=1000, type="payment")),
    ("अनिल ने साढ़े चार सौ का राशन लिया", dict(intent=E, name="अनिल", amount=450, type="credit")),
    ("कविता ने पांच सौ रुपये दिए", dict(intent=E, name="कविता", amount=500, type="payment")),
    # ---------- Marathi
    ("रमेशने 250 रुपयांचे सामान घेतले", dict(intent=E, name="रमेश", amount=250, type="credit")),
    ("सुनीताने 500 जमा केले", dict(intent=E, name="सुनीता", amount=500, type="payment")),
    ("Ramesh ne 250 che saman ghetle", dict(intent=E, name="Ramesh", amount=250, type="credit")),
    ("Sunita ne 500 jama kele", dict(intent=E, name="Sunita", amount=500, type="payment")),
    ("गणेशने तीनशे रुपये उधार घेतले", dict(intent=E, name="गणेश", amount=300, type="credit")),
    ("सविताने दोनशे जमा केले", dict(intent=E, name="सविता", amount=200, type="payment")),
    # ---------- English
    ("Ramesh took 250 on credit", dict(intent=E, name="Ramesh", amount=250, type="credit")),
    ("Sunita paid 500", dict(intent=E, name="Sunita", amount=500, type="payment")),
    ("Mohan bought 120 rupees of sugar on credit", dict(intent=E, name="Mohan", amount=120, type="credit")),
    ("Geeta paid 350 rupees", dict(intent=E, name="Geeta", amount=350, type="payment")),
    ("Anil took two thousand rupees credit", dict(intent=E, name="Anil", amount=2000, type="credit")),
    ("Priya paid back 700", dict(intent=E, name="Priya", amount=700, type="payment")),
    ("Add 300 credit for Vikram", dict(intent=E, name="Vikram", amount=300, type="credit")),
    ("Kiran paid 1500 by UPI", dict(intent=E, name="Kiran", amount=1500, type="payment")),
    # ---------- balance questions
    ("Ramesh ka kitna baaki hai", dict(intent="balance", name="Ramesh")),
    ("Sunita ka kitna udhaar hai", dict(intent="balance", name="Sunita")),
    ("रमेश का कितना बाकी है", dict(intent="balance", name="रमेश")),
    ("How much does Ramesh owe", dict(intent="balance", name="Ramesh")),
    ("Mohan ka hisab batao", dict(intent="balance", name="Mohan")),
    ("रमेशचे किती बाकी आहे", dict(intent="balance", name="रमेश")),
    # ---------- shop-level questions
    ("aaj kis kis ka udhaar hai", dict(intent="today")),
    ("आज किसने उधार लिया", dict(intent="today")),
    ("sabse zyada udhaar kiska hai", dict(intent="top")),
    ("सबसे ज्यादा बाकी किसका है", dict(intent="top")),
    ("kul kitna baaki hai", dict(intent="total")),
    ("total udhaar kitna hai", dict(intent="total")),
    # ---------- undo
    ("last entry cancel karo", dict(intent="undo")),
    ("pichli entry hatao", dict(intent="undo")),
    ("undo", dict(intent="undo")),
    ("गलत हो गया, रद्द करो", dict(intent="undo")),
    # ---------- written after the fixes, never tuned against
    ("Imran ne 650 ka saman udhaar liya", dict(intent=E, name="Imran", amount=650, type="credit")),
    ("Poonam ne teen sau jama kiye", dict(intent=E, name="Poonam", amount=300, type="payment")),
    ("Harish ko 20 rupaye ki sabun udhar diya", dict(intent=E, name="Harish", amount=20, type="credit")),
    ("Shanti ne 2500 wapas kiye", dict(intent=E, name="Shanti", amount=2500, type="payment")),
    ("प्रिया ने 180 रुपये उधार लिए", dict(intent=E, name="प्रिया", amount=180, type="credit")),
    ("Nitin paid 90 rupees", dict(intent=E, name="Nitin", amount=90, type="payment")),
    ("Salim ka kitna baki hai", dict(intent="balance", name="Salim")),
    ("संजयने पाचशे रुपये जमा केले", dict(intent=E, name="संजय", amount=500, type="payment")),
    ("Komal ne 1100 ka rashan liya", dict(intent=E, name="Komal", amount=1100, type="credit")),
    ("Arjun took 45 rupees of milk", dict(intent=E, name="Arjun", amount=45, type="credit")),
    # promises ("kal dega") must not disturb name, amount or type
    ("Ramesh ne 500 ka saman liya kal dega", dict(intent=E, name="Ramesh", amount=500, type="credit", promise_days=1)),
    ("रमेश ने 500 का सामान लिया कल देगा", dict(intent=E, name="रमेश", amount=500, type="credit", promise_days=1)),
    ("Ramesh took 500 on credit will pay tomorrow", dict(intent=E, name="Ramesh", amount=500, type="credit", promise_days=1)),
    ("Sunita ne 300 ka saman liya do din mein dega", dict(intent=E, name="Sunita", amount=300, type="credit", promise_days=2)),
    ("Ramesh kal dega", dict(intent="promise", name="Ramesh", promise_days=1)),
]
