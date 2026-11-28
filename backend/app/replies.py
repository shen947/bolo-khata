"""Short spoken replies in Hindi, Marathi and English.
Keep them one line: the shop owner hears them at a busy counter."""


def inr(x) -> str:
    x = float(x or 0)
    neg = x < 0
    x = abs(x)
    whole = int(round(x))
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if neg else "") + s


T = {
    "confirm_credit": {
        "hi": "{name}, {amt} रुपये उधार। सही है?",
        "mr": "{name}, {amt} रुपये उधार. बरोबर आहे?",
        "en": "{name}, {amt} rupees on credit. Is that right?",
    },
    "confirm_payment": {
        "hi": "{name} ने {amt} रुपये जमा किए। सही है?",
        "mr": "{name} यांनी {amt} रुपये जमा केले. बरोबर आहे?",
        "en": "{name} paid {amt} rupees. Is that right?",
    },
    "defaulted": {
        "hi": "उधार मान लिया है।",
        "mr": "उधार धरले आहे.",
        "en": "I've taken it as credit.",
    },
    "new_customer": {
        "hi": "नया ग्राहक: {name}।",
        "mr": "नवीन ग्राहक: {name}.",
        "en": "New customer: {name}.",
    },
    "saved": {
        "hi": "हो गया। {name} का अब {bal} रुपये बाकी है।",
        "mr": "झाले. {name} यांचे आता {bal} रुपये बाकी.",
        "en": "Saved. {name} now owes {bal} rupees.",
    },
    "saved_clear": {
        "hi": "हो गया। {name} का पूरा हिसाब साफ़ है।",
        "mr": "झाले. {name} यांचा हिशोब पूर्ण झाला.",
        "en": "Saved. {name} has nothing pending.",
    },
    "saved_advance": {
        "hi": "हो गया। {name} के {bal} रुपये एडवांस जमा हैं।",
        "mr": "झाले. {name} यांचे {bal} रुपये आगाऊ जमा आहेत.",
        "en": "Saved. {name} has {bal} rupees in advance.",
    },
    "ask_amount": {
        "hi": "{name}, कितने रुपये?",
        "mr": "{name}, किती रुपये?",
        "en": "{name}, how much?",
    },
    "ask_name": {
        "hi": "{amt} रुपये, किसके नाम पर?",
        "mr": "{amt} रुपये, कोणाच्या नावावर?",
        "en": "{amt} rupees, for which customer?",
    },
    "which": {
        "hi": "कौन से {name}?",
        "mr": "कोणते {name}?",
        "en": "Which {name}?",
    },
    "balance": {
        "hi": "{name} का {bal} रुपये बाकी है।",
        "mr": "{name} यांचे {bal} रुपये बाकी आहेत.",
        "en": "{name} owes {bal} rupees.",
    },
    "balance_zero": {
        "hi": "{name} का कुछ भी बाकी नहीं है।",
        "mr": "{name} यांचे काहीही बाकी नाही.",
        "en": "{name} owes nothing.",
    },
    "not_found": {
        "hi": "{name} नाम का कोई ग्राहक नहीं मिला।",
        "mr": "{name} नावाचा ग्राहक सापडला नाही.",
        "en": "No customer called {name}.",
    },
    "today": {
        "hi": "आज {n} लोगों ने उधार लिया, कुल {amt} रुपये: {list}।",
        "mr": "आज {n} जणांनी उधार घेतले, एकूण {amt} रुपये: {list}.",
        "en": "Today {n} people took credit, {amt} rupees in all: {list}.",
    },
    "today_none": {
        "hi": "आज अभी तक किसी ने उधार नहीं लिया।",
        "mr": "आज अजून कोणी उधार घेतले नाही.",
        "en": "No credit given today yet.",
    },
    "top": {
        "hi": "सबसे ज़्यादा बाकी: {list}।",
        "mr": "सर्वात जास्त बाकी: {list}.",
        "en": "Highest balances: {list}.",
    },
    "total": {
        "hi": "कुल {amt} रुपये बाकी हैं, {n} ग्राहकों से।",
        "mr": "एकूण {amt} रुपये बाकी आहेत, {n} ग्राहकांकडून.",
        "en": "{amt} rupees pending in total, from {n} customers.",
    },
    "undone": {
        "hi": "पिछली एंट्री रद्द की: {name}, {amt} रुपये।",
        "mr": "मागची नोंद रद्द केली: {name}, {amt} रुपये.",
        "en": "Cancelled the last entry: {name}, {amt} rupees.",
    },
    "nothing_to_undo": {
        "hi": "रद्द करने के लिए कोई एंट्री नहीं है।",
        "mr": "रद्द करण्यासाठी कोणतीही नोंद नाही.",
        "en": "There is no entry to cancel.",
    },
    "cancelled": {
        "hi": "ठीक है, सेव नहीं किया।",
        "mr": "ठीक आहे, सेव्ह केले नाही.",
        "en": "Okay, not saved.",
    },
    "unknown": {
        "hi": "माफ़ कीजिए, समझ नहीं आया। ऐसे बोलिए: रमेश ने 250 का सामान लिया।",
        "mr": "माफ करा, समजले नाही. असे बोला: रमेशने 250 रुपयांचे सामान घेतले.",
        "en": "Sorry, I didn't get that. Try: Ramesh took 250 on credit.",
    },
    "promise_with": {
        "hi": "{when} देने का वादा।",
        "mr": "{when} देण्याचे वचन.",
        "en": "Promised for {when}.",
    },
    "promise_saved": {
        "hi": "ठीक है, {name} {when} देंगे। मैं याद दिलाऊँगा।",
        "mr": "ठीक आहे, {name} {when} देतील. मी आठवण करून देईन.",
        "en": "Okay, {name} will pay {when}. I'll remind you.",
    },
    "promise_unknown": {
        "hi": "{name} नाम का कोई ग्राहक नहीं मिला। पहले उनकी एंट्री बोलिए।",
        "mr": "{name} नावाचा ग्राहक सापडला नाही. आधी त्यांची नोंद बोला.",
        "en": "No customer called {name}. Add their entry first.",
    },
    "promise_which": {
        "hi": "कई {name} हैं। पूरा नाम बोलिए।",
        "mr": "अनेक {name} आहेत. पूर्ण नाव बोला.",
        "en": "There are several {name}. Say the full name.",
    },
    "promise_nodebt": {
        "hi": "{name} का कुछ बाकी नहीं है।",
        "mr": "{name} यांचे काही बाकी नाही.",
        "en": "{name} owes nothing, so there is nothing to promise.",
    },
    "reminder_overdue": {
        "hi": "नमस्ते {name} जी, {shop} पर आपका ₹{bal} बाकी है। आपने {when} तक देने को कहा था। कृपया जमा कर दीजिए। धन्यवाद 🙏",
        "mr": "नमस्कार {name}, {shop} येथे आपले ₹{bal} बाकी आहेत. आपण {when} पर्यंत देण्याचे सांगितले होते. कृपया जमा करावे. धन्यवाद 🙏",
        "en": "Namaste {name} ji, you have ₹{bal} pending at {shop}. You had said you would pay by {when}. Please clear it soon. Thank you 🙏",
    },
    "reminder": {
        "hi": "नमस्ते {name} जी, {shop} पर आपका ₹{bal} बाकी है। सुविधा अनुसार जमा कर दीजिए। धन्यवाद 🙏",
        "mr": "नमस्कार {name}, {shop} येथे आपले ₹{bal} बाकी आहेत. सोयीनुसार जमा करावे. धन्यवाद 🙏",
        "en": "Namaste {name} ji, you have ₹{bal} pending at {shop}. Please clear it when convenient. Thank you 🙏",
    },
}


_MONTHS = {
    "hi": ["जन", "फ़र", "मार्च", "अप्रै", "मई", "जून", "जुल", "अग", "सित", "अक्टू", "नव", "दिस"],
    "mr": ["जाने", "फेब्रु", "मार्च", "एप्रि", "मे", "जून", "जुलै", "ऑग", "सप्टें", "ऑक्टो", "नोव्हें", "डिसें"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}
_REL = {"hi": ("आज", "कल", "परसों"), "mr": ("आज", "उद्या", "परवा"), "en": ("today", "tomorrow", "the day after tomorrow")}


def when_label(date_iso, lang="hi", today=None):
    """'2026-11-29' -> 'कल' / 'tomorrow' / '3 Dec'. Past dates show the date."""
    from datetime import date
    lang = lang if lang in _MONTHS else "hi"
    d = date.fromisoformat(date_iso)
    delta = (d - (today or date.today())).days
    if 0 <= delta <= 2:
        return _REL[lang][delta]
    return f"{d.day} {_MONTHS[lang][d.month - 1]}"


def say(key, lang="hi", **kw):
    lang = lang if lang in ("hi", "mr", "en") else "hi"
    for k in ("amt", "bal"):
        if k in kw and not isinstance(kw[k], str):
            kw[k] = inr(kw[k])
    return T[key][lang].format(**kw)
