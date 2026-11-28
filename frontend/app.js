/* Bolo Khata: voice-first udhaar ledger. Plain JS, no build step. */
(() => {
  "use strict";

  // ------------------------------------------------------------ strings
  const UI = {
    nav_home: { hi: "बोलो", mr: "बोला", en: "Speak" },
    nav_khata: { hi: "खाता", mr: "खाते", en: "Ledger" },
    today_given: { hi: "आज उधार दिया", mr: "आज उधार दिले", en: "Credit given today" },
    today_got: { hi: "आज जमा हुआ", mr: "आज जमा झाले", en: "Collected today" },
    pending: { hi: "कुल बाकी", mr: "एकूण बाकी", en: "Total pending" },
    from_n: { hi: "{n} ग्राहकों से", mr: "{n} ग्राहकांकडून", en: "from {n} customers" },
    tap: { hi: "दबाइए और बोलिए", mr: "दाबा आणि बोला", en: "Tap and speak" },
    listening: { hi: "सुन रहा हूँ…", mr: "ऐकत आहे…", en: "Listening…" },
    thinking: { hi: "समझ रहा हूँ…", mr: "समजत आहे…", en: "Working it out…" },
    examples: {
      hi: "<q>रमेश ने 250 का सामान लिया</q> <q>सुनीता ने 500 जमा किए</q> <q>रमेश का कितना बाकी है?</q>",
      mr: "<q>रमेशने 250 रुपयांचे सामान घेतले</q> <q>सुनीताने 500 जमा केले</q> <q>रमेशचे किती बाकी आहे?</q>",
      en: "<q>Ramesh took 250 on credit</q> <q>Sunita paid 500</q> <q>How much does Ramesh owe?</q>",
    },
    type_here: { hi: "या यहाँ लिखें…", mr: "किंवा इथे लिहा…", en: "Or type here…" },
    go: { hi: "भेजें", mr: "पाठवा", en: "Send" },
    recent: { hi: "हाल की एंट्री", mr: "अलीकडील नोंदी", en: "Recent entries" },
    no_entries: { hi: "अभी कोई एंट्री नहीं। माइक दबाकर पहली एंट्री बोलिए।", mr: "अजून नोंद नाही. माइक दाबून पहिली नोंद बोला.", en: "No entries yet. Tap the mic and say the first one." },
    credit: { hi: "उधार", mr: "उधार", en: "Credit" },
    payment: { hi: "जमा", mr: "जमा", en: "Paid" },
    save: { hi: "हाँ, सेव करें", mr: "हो, सेव्ह करा", en: "Yes, save" },
    cancel: { hi: "नहीं", mr: "नाही", en: "No" },
    swap_to_payment: { hi: "यह जमा था? बदलें", mr: "हे जमा होते? बदला", en: "This was a payment? Switch" },
    swap_to_credit: { hi: "यह उधार था? बदलें", mr: "हे उधार होते? बदला", en: "This was credit? Switch" },
    say_haan: { hi: "\"हाँ\" या \"नहीं\" बोलिए। 5 सेकंड में अपने-आप सेव होगा।", mr: "\"हो\" किंवा \"नाही\" बोला. 5 सेकंदात आपोआप सेव्ह होईल.", en: "Say \"yes\" or \"no\". Saves by itself in 5 seconds." },
    new_cust: { hi: "नया ग्राहक", mr: "नवीन ग्राहक", en: "New customer" },
    heard: { hi: "सुना", mr: "ऐकले", en: "Heard" },
    undo: { hi: "वापस लें", mr: "परत घ्या", en: "Undo" },
    undone: { hi: "एंट्री रद्द की गई", mr: "नोंद रद्द केली", en: "Entry cancelled" },
    search: { hi: "नाम खोजें", mr: "नाव शोधा", en: "Search a name" },
    customers: { hi: "ग्राहक खाते", mr: "ग्राहक खाते", en: "Customer accounts" },
    owes: { hi: "बाकी", mr: "बाकी", en: "owes" },
    clear: { hi: "हिसाब साफ़", mr: "हिशोब पूर्ण", en: "All clear" },
    advance: { hi: "एडवांस", mr: "आगाऊ", en: "Advance" },
    back: { hi: "← वापस", mr: "← मागे", en: "← Back" },
    remind: { hi: "WhatsApp पर याद दिलाएँ", mr: "WhatsApp वर आठवण करा", en: "Remind on WhatsApp" },
    phone: { hi: "मोबाइल नंबर", mr: "मोबाईल नंबर", en: "Mobile number" },
    save_phone: { hi: "सेव", mr: "सेव्ह", en: "Save" },
    history: { hi: "पूरा हिसाब", mr: "संपूर्ण हिशोब", en: "Full history" },
    cancel_entry: { hi: "रद्द करें", mr: "रद्द करा", en: "Cancel" },
    which: { hi: "कौन से ग्राहक?", mr: "कोणते ग्राहक?", en: "Which customer?" },
    new_with_name: { hi: "नया ग्राहक बनाएँ: {name}", mr: "नवीन ग्राहक: {name}", en: "New customer: {name}" },
    offline: { hi: "इंटरनेट नहीं है। एंट्री फ़ोन में रखी है, नेटवर्क आते ही भेज देंगे ({n})", mr: "इंटरनेट नाही. नोंदी फोनमध्ये ठेवल्या आहेत ({n})", en: "No internet. Entries are kept on this phone and sent when you're back online ({n})" },
    no_speech: { hi: "इस ब्राउज़र में आवाज़ नहीं चलती। Chrome खोलें या नीचे लिखें।", mr: "या ब्राउझरमध्ये आवाज चालत नाही. Chrome वापरा किंवा खाली लिहा.", en: "Voice isn't supported in this browser. Use Chrome, or type below." },
    mic_denied: { hi: "माइक की अनुमति दीजिए।", mr: "माइकची परवानगी द्या.", en: "Please allow microphone access." },
    didnt_hear: { hi: "कुछ सुनाई नहीं दिया। फिर से दबाइए।", mr: "काही ऐकू आले नाही. पुन्हा दाबा.", en: "Didn't catch anything. Tap again." },
    tz_today: { hi: "आज", mr: "आज", en: "Today" },
    nav_settings: { hi: "सेटिंग", mr: "सेटिंग", en: "Settings" },
    lock_title: { hi: "PIN डालिए", mr: "PIN टाका", en: "Enter PIN" },
    lock_wrong: { hi: "गलत PIN", mr: "चुकीचा PIN", en: "Wrong PIN" },
    lock_wait: { hi: "बहुत बार गलत PIN। {s} सेकंड बाद कोशिश करें।", mr: "खूप वेळा चुकीचा PIN. {s} सेकंदांनी प्रयत्न करा.", en: "Too many wrong PINs. Try again in {s} seconds." },
    unlock: { hi: "खोलें", mr: "उघडा", en: "Open" },
    set_shop: { hi: "दुकान का नाम", mr: "दुकानाचे नाव", en: "Shop name" },
    set_shop_help: { hi: "WhatsApp याद-संदेश में यही नाम जाएगा।", mr: "WhatsApp आठवणीत हेच नाव जाईल.", en: "Used in WhatsApp reminders." },
    set_pin: { hi: "PIN लॉक", mr: "PIN लॉक", en: "PIN lock" },
    set_pin_off: { hi: "अभी कोई PIN नहीं है। कोई भी इस फ़ोन/लिंक से खाता देख सकता है। 4–8 अंकों का PIN लगाइए।", mr: "सध्या PIN नाही. 4–8 अंकी PIN लावा.", en: "No PIN yet: anyone with this phone or link can open the ledger. Set a 4–8 digit PIN." },
    set_pin_on: { hi: "PIN चालू है। बदलने या हटाने के लिए पुराना PIN चाहिए।", mr: "PIN चालू आहे. बदलण्यासाठी जुना PIN लागेल.", en: "PIN is on. Changing or removing it needs the current PIN." },
    cur_pin: { hi: "पुराना PIN", mr: "जुना PIN", en: "Current PIN" },
    new_pin: { hi: "नया PIN", mr: "नवीन PIN", en: "New PIN" },
    pin_set: { hi: "PIN लगाएँ", mr: "PIN लावा", en: "Set PIN" },
    pin_change: { hi: "PIN बदलें", mr: "PIN बदला", en: "Change PIN" },
    pin_remove: { hi: "PIN हटाएँ", mr: "PIN काढा", en: "Remove PIN" },
    lock_now: { hi: "अभी लॉक करें", mr: "आता लॉक करा", en: "Lock now" },
    saved_ok: { hi: "सेव हो गया", mr: "सेव्ह झाले", en: "Saved" },
    pin_bad: { hi: "PIN 4 से 8 अंकों का होना चाहिए", mr: "PIN 4 ते 8 अंकी हवा", en: "PIN must be 4 to 8 digits" },
    set_export: { hi: "हिसाब डाउनलोड करें", mr: "हिशोब डाउनलोड करा", en: "Download your ledger" },
    set_export_help: { hi: "पूरा हिसाब CSV फ़ाइल में (Excel में खुलता है)। आपका डेटा आपका है।", mr: "संपूर्ण हिशोब CSV फाइलमध्ये (Excel मध्ये उघडते).", en: "Every entry as a CSV file that opens in Excel. Your data stays yours." },
    export_btn: { hi: "CSV डाउनलोड", mr: "CSV डाउनलोड", en: "Download CSV" },
    set_privacy: { hi: "निजता", mr: "गोपनीयता", en: "Privacy" },
    set_privacy_help: { hi: "आवाज़ रिकॉर्ड या सेव नहीं होती, सिर्फ़ लिखा हुआ वाक्य। सारा डेटा आपके अपने सर्वर पर रहता है।", mr: "आवाज रेकॉर्ड होत नाही, फक्त लिहिलेले वाक्य. सर्व डेटा तुमच्या सर्व्हरवर राहतो.", en: "Audio is never recorded or stored, only the recognised sentence. All data stays on your own server." },

    promises_title: { hi: "देने के वादे", mr: "देण्याची वचने", en: "Promised payments" },
    p_overdue: { hi: "तारीख निकल गई", mr: "तारीख उलटली", en: "Overdue" },
    p_today: { hi: "आज", mr: "आज", en: "Today" },
    promise_line: { hi: "वादा: {when}", mr: "वचन: {when}", en: "Promised: {when}" },
    set_when: { hi: "कब देंगे?", mr: "कधी देणार?", en: "When will they pay?" },
    clear_promise: { hi: "हटाएँ", mr: "काढा", en: "Remove" },
    welcome_title: { hi: "स्वागत है! तीन कदम:", mr: "स्वागत! तीन पावले:", en: "Welcome! Three steps:" },
    welcome_1: { hi: "माइक दबाइए (पहली बार ब्राउज़र पूछे तो \"अनुमति दें\")", mr: "माइक दाबा (ब्राउझरने विचारल्यास \"परवानगी द्या\")", en: "Tap the mic (allow the microphone when the browser asks)" },
    welcome_2: { hi: "बोलिए: “रमेश ने 250 का सामान लिया, कल देगा”", mr: "बोला: “रमेशने 250 रुपयांचे सामान घेतले, उद्या देईल”", en: "Say: “Ramesh took 250 on credit, will pay tomorrow”" },
    welcome_3: { hi: "\"हाँ\" बोलिए, या 5 सेकंड रुकिए। सेव हो जाएगा। गलती हो तो \"वापस लें\"।", mr: "\"हो\" बोला, किंवा 5 सेकंद थांबा. सेव्ह होईल. चूक झाल्यास \"परत घ्या\".", en: "Say “yes”, or wait 5 seconds, and it saves. Made a mistake? Tap Undo." },
    got_it: { hi: "समझ गया", mr: "समजले", en: "Got it" },
    demo_banner: { hi: "ये नमूना खाते हैं, आपकी दुकान के नहीं।", mr: "ही नमुना खाती आहेत, तुमच्या दुकानाची नाहीत.", en: "These are sample accounts, not your shop's." },
    demo_clear: { hi: "नमूना हटाकर अपनी दुकान शुरू करें", mr: "नमुना काढून तुमचे दुकान सुरू करा", en: "Clear samples and start my shop" },
    demo_sure: { hi: "पक्का? नमूना खाते हट जाएँगे। आपकी अपनी एंट्री नहीं हटेंगी।", mr: "नक्की? नमुना खाती जातील. तुमच्या स्वतःच्या नोंदी राहतील.", en: "Sure? Sample accounts will go. Anything you entered yourself stays." },
    yes_clear: { hi: "हाँ, हटाएँ", mr: "हो, काढा", en: "Yes, clear them" },
    keep: { hi: "नहीं, रहने दें", mr: "नाही, राहू द्या", en: "No, keep them" },
    tap_stop: { hi: "बोल चुके? फिर दबाइए", mr: "बोलून झाले? पुन्हा दाबा", en: "Done speaking? Tap again" },
    set_privacy_stt: { hi: "इस सर्वर पर आवाज़ की पहचान चालू है: बोलते समय आपकी आवाज़ पहचान सेवा को भेजी जाती है, सेव नहीं होती।", mr: "या सर्व्हरवर आवाज ओळख चालू आहे: बोलताना आवाज ओळख सेवेला पाठवला जातो, सेव्ह होत नाही.", en: "Speech recognition is on for this server: while you speak, your voice is sent to the recognition service. It is not stored." },
  };
  const SPEECH_LANG = { hi: "hi-IN", mr: "mr-IN", en: "en-IN" };
  const MONTHS = {
    hi: ["जन", "फ़र", "मार्च", "अप्रै", "मई", "जून", "जुल", "अग", "सित", "अक्टू", "नव", "दिस"],
    mr: ["जाने", "फेब्रु", "मार्च", "एप्रि", "मे", "जून", "जुलै", "ऑग", "सप्टें", "ऑक्टो", "नोव्हें", "डिसें"],
    en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  };
  const REL = { hi: ["आज", "कल", "परसों"], mr: ["आज", "उद्या", "परवा"], en: ["today", "tomorrow", "day after tomorrow"] };

  // ------------------------------------------------------------ state
  const S = {
    lang: localStorage.getItem("bk_lang") || "hi",
    ctx: null,              // follow-up context for the parser
    pendingEntry: null,     // entry waiting for confirmation
    timer: null,
    rec: null,
    listening: false,
    config: {},
  };
  const $ = (s, r = document) => r.querySelector(s);
  const t = (k, vars = {}) => (UI[k]?.[S.lang] ?? UI[k]?.hi ?? k).replace(/\{(\w+)\}/g, (_, v) => vars[v] ?? "");
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  function dayDiff(iso) {
    const d = new Date(iso + "T00:00:00"), n = new Date(); n.setHours(0, 0, 0, 0);
    return Math.round((d - n) / 864e5);
  }
  function whenLabel(iso) {
    const diff = dayDiff(iso), d = new Date(iso + "T00:00:00");
    return diff >= 0 && diff <= 2 ? REL[S.lang][diff] : `${d.getDate()} ${MONTHS[S.lang][d.getMonth()]}`;
  }
  const inr = (x) => "₹" + Math.round(Math.abs(+x || 0)).toLocaleString("en-IN");

  // ------------------------------------------------------------ api
  async function api(path, opts = {}) {
    const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts,
      body: opts.body ? JSON.stringify(opts.body) : undefined });
    if (r.status === 401 && !path.startsWith("/api/auth/")) { showLock(); throw new Error("locked"); }
    if (!r.ok) {
      let detail = r.statusText;
      try { const j = await r.json(); detail = j.detail || detail; if (j.retry_after) detail += "|" + j.retry_after; } catch (_) {}
      const err = new Error(detail); err.status = r.status; throw err;
    }
    return r.json();
  }

  // ------------------------------------------------------------ speech out
  let voices = [];
  const loadVoices = () => { voices = window.speechSynthesis ? speechSynthesis.getVoices() : []; };
  if (window.speechSynthesis) { loadVoices(); speechSynthesis.onvoiceschanged = loadVoices; }
  function speak(text) {
    return new Promise((resolve) => {
      if (!window.speechSynthesis || !text) return resolve();
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      const want = SPEECH_LANG[S.lang];
      u.lang = want;
      u.voice = voices.find((v) => v.lang === want) || voices.find((v) => v.lang === "hi-IN") ||
        voices.find((v) => v.lang?.startsWith("en-IN")) || null;
      u.rate = 1.02;
      let done = false;
      const fin = () => { if (!done) { done = true; resolve(); } };
      u.onend = fin; u.onerror = fin;
      setTimeout(fin, Math.min(12000, 1500 + text.length * 90)); // never hang the flow
      speechSynthesis.speak(u);
    });
  }

  // ------------------------------------------------------------ speech in
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  function listen({ onInterim, short = false } = {}) {
    return new Promise((resolve, reject) => {
      if (!SR) return canRecord() ? listenRecorded().then(resolve, reject) : reject(new Error("nospeech"));
      stopListening();
      const rec = new SR();
      rec.lang = SPEECH_LANG[S.lang];
      rec.interimResults = true;
      rec.continuous = false;
      rec.maxAlternatives = 1;
      let finalText = "";
      rec.onresult = (ev) => {
        let interim = "";
        for (let i = ev.resultIndex; i < ev.results.length; i++) {
          const r = ev.results[i];
          if (r.isFinal) finalText += r[0].transcript; else interim += r[0].transcript;
        }
        onInterim && onInterim(finalText + interim);
      };
      rec.onerror = (ev) => { S.listening = false; setMic(false); reject(new Error(ev.error)); };
      rec.onend = () => { S.listening = false; setMic(false); resolve(finalText.trim()); };
      S.rec = rec; S.listening = true;
      if (!short) setMic(true);
      try { rec.start(); } catch (e) { reject(e); }
    });
  }
  // Browsers without built-in speech recognition (Safari, Firefox, iPhone): record a short clip and
  // let the server transcribe it. Only offered when the server has STT_API_KEY set.
  const canRecord = () => !!(S.config.stt && window.MediaRecorder && navigator.mediaDevices?.getUserMedia);
  const canListen = () => !!SR || canRecord();

  async function listenRecorded() {
    stopListening();
    let stream;
    try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); }
    catch (e) { throw new Error(e.name === "NotAllowedError" || e.name === "SecurityError" ? "not-allowed" : "audio-capture"); }
    const mime = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"].find((m) => MediaRecorder.isTypeSupported(m)) || "";
    const rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    const chunks = [];
    S.recorder = rec; S.recDiscard = false; S.listening = true; setMic(true);
    const hint = $("#micHint"); if (hint) hint.textContent = t("tap_stop");
    // stop by itself after about a second of quiet (or 9 s at most), so the shop owner just talks
    let ac, timer;
    const t0 = Date.now(); let spoke = false, quietSince = Date.now();
    try {
      ac = new (window.AudioContext || window.webkitAudioContext)();
      const an = ac.createAnalyser(); an.fftSize = 512;
      ac.createMediaStreamSource(stream).connect(an);
      const buf = new Uint8Array(an.fftSize);
      timer = setInterval(() => {
        an.getByteTimeDomainData(buf);
        let sum = 0; for (const v of buf) sum += ((v - 128) / 128) ** 2;
        const loud = Math.sqrt(sum / buf.length) > 0.03, now = Date.now();
        if (loud) { spoke = true; quietSince = now; }
        if ((spoke && now - quietSince > 1200) || (!spoke && now - t0 > 6000) || now - t0 > 9000) { if (rec.state !== "inactive") rec.stop(); }
      }, 100);
    } catch (_) { timer = setTimeout(() => { if (rec.state !== "inactive") rec.stop(); }, 6000); }
    return new Promise((resolve, reject) => {
      rec.ondataavailable = (ev) => { if (ev.data && ev.data.size) chunks.push(ev.data); };
      rec.onerror = () => reject(new Error("audio-capture"));
      rec.onstop = async () => {
        clearInterval(timer); clearTimeout(timer);
        stream.getTracks().forEach((tr) => tr.stop()); try { ac && ac.close(); } catch (_) {}
        S.recorder = null; S.listening = false; setMic(false);
        const blob = new Blob(chunks, { type: rec.mimeType || mime || "audio/webm" });
        if (S.recDiscard || blob.size < 1500) return resolve("");
        const h = $("#micHint"); if (h) h.textContent = t("thinking");
        try {
          const r = await fetch(`/api/transcribe?lang=${S.lang}`, { method: "POST", headers: { "Content-Type": blob.type }, body: blob });
          if (r.status === 401) { showLock(); return reject(new Error("locked")); }
          if (!r.ok) return resolve("");
          resolve(((await r.json()).text || "").trim());
        } catch (_) { reject(new Error("network")); }
        finally { const h2 = $("#micHint"); if (h2) h2.textContent = t("tap"); }
      };
      rec.start();
    });
  }

  function stopListening() {
    if (S.rec) { try { S.rec.abort(); } catch (_) {} S.rec = null; }
    if (S.recorder && S.recorder.state !== "inactive") { S.recDiscard = true; try { S.recorder.stop(); } catch (_) {} }
    S.listening = false; setMic(false);
  }
  function setMic(on) {
    const m = $("#mic"); if (!m) return;
    m.classList.toggle("listening", on);
    m.setAttribute("aria-pressed", on ? "true" : "false");
    const h = $("#micHint"); if (h) h.textContent = on ? t("listening") : t("tap");
  }

  // ------------------------------------------------------------ offline queue
  const Q_KEY = "bk_queue";
  const queue = () => JSON.parse(localStorage.getItem(Q_KEY) || "[]");
  const setQueue = (q) => { localStorage.setItem(Q_KEY, JSON.stringify(q)); renderOffline(); };
  function renderOffline() {
    const q = queue(); const el = $("#offline");
    if (!navigator.onLine || q.length) { el.hidden = false; el.textContent = t("offline", { n: q.length }); }
    else el.hidden = true;
  }
  async function flushQueue() {
    if (!navigator.onLine) return;
    const q = queue(); if (!q.length) return;
    setQueue([]);
    for (const item of q) { await handleText(item.text, { source: "offline" }); await waitForSheetClose(); }
  }
  function waitForSheetClose() {
    return new Promise((res) => { const iv = setInterval(() => { if ($("#sheet").hidden) { clearInterval(iv); res(); } }, 300); });
  }
  addEventListener("online", () => { renderOffline(); flushQueue(); });
  addEventListener("offline", renderOffline);

  // ------------------------------------------------------------ core flow
  async function onMic() {
    if (S.listening && S.recorder) { S.recorder.stop(); return; }      // tap again = done speaking, send it
    if (S.listening) { stopListening(); return; }
    if (!canListen()) { showReply(t("no_speech")); $("#typeInput")?.focus(); return; }
    speechSynthesis?.cancel();
    $("#heard").textContent = "";
    try {
      const text = await listen({ onInterim: (s) => { $("#heard").textContent = s; } });
      if (!text) { showReply(t("didnt_hear")); return; }
      $("#heard").textContent = "“" + text + "”";
      await handleText(text);
    } catch (e) {
      if (e.message === "locked") return;
      if (e.message === "not-allowed" || e.message === "audio-capture") showReply(t("mic_denied"));
      else if (e.message === "network" && !navigator.onLine) showReply(t("offline", { n: queue().length }));
      else if (e.message !== "aborted" && e.message !== "no-speech") showReply(t("didnt_hear"));
      else if (e.message === "no-speech") showReply(t("didnt_hear"));
    }
  }

  async function handleText(text, opts = {}) {
    S.lastSource = opts.source || "voice";
    text = (text || "").trim();
    if (!text) return;
    if (!navigator.onLine) { setQueue([...queue(), { text, at: Date.now(), lang: S.lang }]); showReply(t("offline", { n: queue().length })); return; }
    const hint = $("#micHint"); if (hint) hint.textContent = t("thinking");
    let res;
    try {
      res = await api("/api/interpret", { method: "POST", body: { text, lang: S.lang, context: S.ctx } });
    } catch (e) {
      if (e.message === "locked") return;
      if (e.status && e.status < 500) { showReply(t("didnt_hear")); return; }
      setQueue([...queue(), { text, at: Date.now(), lang: S.lang }]);
      showReply(t("offline", { n: queue().length }));
      return;
    } finally { if (hint) hint.textContent = t("tap"); }
    await route(res, text);
  }

  async function route(res, text) {
    switch (res.kind) {
      case "confirm":
        S.ctx = null;
        return openConfirm(res.entry, res.say);
      case "clarify":
        S.ctx = { awaiting: res.awaiting, ...res.pending };
        showReply(res.say);
        await speak(res.say);
        return followUp();
      case "choose":
        S.ctx = null;
        return openChoose(res);
      case "promise":
        S.ctx = null;
        showReply(res.say); refreshHome(); return speak(res.say);
      case "undone":
        S.ctx = null;
        showReply(res.say); refreshHome(); return speak(res.say);
      case "answer":
        S.ctx = null;
        showReply(res.say); return speak(res.say);
      default:
        S.ctx = null;
        showReply(res.say || t("didnt_hear")); return speak(res.say);
    }
  }

  async function followUp() {
    // ask the missing piece and listen right away, hands-free
    if (!canListen()) { $("#typeInput")?.focus(); return; }
    try {
      $("#heard").textContent = "";
      const text = await listen({ onInterim: (s) => { $("#heard").textContent = s; } });
      if (text) { $("#heard").textContent = "“" + text + "”"; await handleText(text); }
      else S.ctx = null;
    } catch (_) { /* user can tap the mic again; context is kept */ }
  }

  // ------------------------------------------------------------ confirmation sheet
  function slipHTML(e) {
    return `<div class="slip">
      ${e.is_new ? `<div class="newbadge">${t("new_cust")}</div>` : ""}
      <div class="s-name">${esc(e.name)}</div>
      <div class="s-amt num ${e.type}">${inr(e.amount)}</div>
      <span class="tag ${e.type}">${t(e.type)}</span>
      ${e.note ? `<div class="s-note">${esc(e.note)}</div>` : ""}
      ${e.promise_date && e.type === "credit" ? `<div class="s-promise">📅 ${esc(t("promise_line", { when: whenLabel(e.promise_date) }))}</div>` : ""}
      ${e.transcript ? `<div class="s-heard">${t("heard")}: “${esc(e.transcript)}”</div>` : ""}
    </div>`;
  }

  async function openConfirm(entry, sayText) {
    S.pendingEntry = entry;
    const card = $("#sheetCard");
    card.innerHTML = `${slipHTML(entry)}
      <div class="countdown" aria-hidden="true"><i id="cd"></i></div>
      <div class="listen-note">${t("say_haan")}</div>
      <div class="sheet-actions">
        <button class="no" id="noBtn">${t("cancel")}</button>
        <button class="yes" id="yesBtn">${t("save")}</button>
      </div>
      <button class="swap" id="swapBtn">${entry.type === "credit" ? t("swap_to_payment") : t("swap_to_credit")}</button>`;
    $("#toast").hidden = true;                       // never let the previous entry's Undo bar cover Yes/No
    $("#sheet").hidden = false;
    $("#yesBtn").onclick = () => saveEntry();
    $("#noBtn").onclick = () => rejectEntry();
    $("#swapBtn").onclick = async () => {
      clearTimer(); stopListening();
      entry.type = entry.type === "credit" ? "payment" : "credit";
      entry.type_defaulted = false;
      if (entry.type === "payment") entry.promise_date = null;      // a payment is not a promise
      const r = await api("/api/confirm-text", { method: "POST", body: { entry, lang: S.lang } });
      openConfirm(entry, r.say);
    };
    $("#yesBtn").focus();
    await speak(sayText);
    if (S.pendingEntry !== entry) return;
    startCountdown(entry);
    listenYesNo(entry);
  }

  function startCountdown(entry) {
    clearTimer();
    const bar = $("#cd"); const total = 5000; const start = Date.now();
    S.timer = setInterval(() => {
      const left = Math.max(0, total - (Date.now() - start));
      if (bar) bar.style.width = (left / total * 100) + "%";
      if (left <= 0) { clearTimer(); if (S.pendingEntry === entry) saveEntry(); }
    }, 100);
  }
  function clearTimer() { if (S.timer) { clearInterval(S.timer); S.timer = null; } }

  async function listenYesNo(entry) {
    if (!SR) return;
    try {
      const text = await listen({ short: true });
      if (S.pendingEntry !== entry || !text) return;
      const r = await api("/api/interpret", { method: "POST", body: { text, lang: S.lang, context: { awaiting: "confirm" } } });
      if (S.pendingEntry !== entry) return;
      if (r.kind === "yes") saveEntry();
      else if (r.kind === "no") rejectEntry(r.say);
      else if (r.kind === "confirm" || r.kind === "clarify") { // user corrected themselves
        clearTimer(); closeSheet(); route(r, text);
      }
    } catch (_) { /* countdown still runs */ }
  }

  async function saveEntry() {
    const e = S.pendingEntry; if (!e) return;
    S.pendingEntry = null; clearTimer(); stopListening(); closeSheet();
    try {
      const r = await api("/api/entries", { method: "POST", body: {
        customer_id: e.customer_id, name: e.name, amount: e.amount, type: e.type,
        note: e.note, transcript: e.transcript, lang: S.lang, source: S.lastSource || "voice",
        promise_date: e.type === "credit" ? (e.promise_date || null) : null } });
      showReply(r.say);
      toast(r.say, async () => {
        await api(`/api/entries/${r.entry.id}/cancel`, { method: "POST" });
        showReply(t("undone")); refreshAll();
      });
      refreshAll();
      speak(r.say);
    } catch (err) {
      if (err.message === "locked") return;
      setQueue([...queue(), { text: e.transcript || `${e.name} ${e.amount} ${e.type === "credit" ? "udhaar" : "jama"}`, at: Date.now() }]);
      showReply(t("offline", { n: queue().length }));
    }
  }
  function rejectEntry(sayText) {
    S.pendingEntry = null; clearTimer(); stopListening(); closeSheet();
    const msg = sayText || { hi: "ठीक है, सेव नहीं किया।", mr: "ठीक आहे, सेव्ह केले नाही.", en: "Okay, not saved." }[S.lang];
    showReply(msg); speak(msg);
  }
  function closeSheet() { $("#sheet").hidden = true; $("#sheetCard").innerHTML = ""; }
  $("#sheet").addEventListener("click", (ev) => { if (ev.target.id === "sheet") { S.pendingEntry = null; clearTimer(); stopListening(); closeSheet(); } });
  addEventListener("keydown", (ev) => { if (ev.key === "Escape" && !$("#sheet").hidden) { S.pendingEntry = null; clearTimer(); stopListening(); closeSheet(); } });

  // ------------------------------------------------------------ choose sheet
  async function openChoose(res) {
    const card = $("#sheetCard");
    const pending = res.pending;
    card.innerHTML = `<div class="sheet-q">${esc(res.say)}</div>
      <div class="choices">
        ${res.candidates.map((c) => `<button data-id="${c.id}"><span>${esc(c.name)}</span><span class="num">${inr(c.balance)}</span></button>`).join("")}
        ${res.for === "entry" ? `<button data-new="1"><span>${esc(t("new_with_name", { name: pending.name }))}</span><span>＋</span></button>` : ""}
      </div>`;
    $("#toast").hidden = true;
    $("#sheet").hidden = false;
    card.querySelectorAll("button").forEach((b) => b.onclick = async () => {
      closeSheet();
      if (res.for === "balance") { location.hash = `#/c/${b.dataset.id}`; return; }
      const c = res.candidates.find((x) => String(x.id) === b.dataset.id);
      const entry = b.dataset.new ? { ...pending, customer_id: null, is_new: true }
        : { ...pending, customer_id: c.id, name: c.name, is_new: false };
      const r = await api("/api/confirm-text", { method: "POST", body: { entry, lang: S.lang } });
      openConfirm(entry, r.say);
    });
    speak(res.say);
  }

  // ------------------------------------------------------------ toast + reply
  let toastTimer;
  function toast(msg, onUndo) {
    const el = $("#toast");
    el.innerHTML = `<span>${esc(msg)}</span>${onUndo ? `<button id="undoBtn">${t("undo")}</button>` : ""}`;
    el.hidden = false;
    if (onUndo) $("#undoBtn").onclick = () => { el.hidden = true; onUndo(); };
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { el.hidden = true; }, 30000); // 30s undo window
  }
  function showReply(msg) {
    const el = $("#reply"); if (!el) return;
    el.textContent = msg; el.hidden = !msg;
  }

  // ------------------------------------------------------------ views
  const micSVG = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M8.5 21h7"/></svg>`;

  function when(ts) {
    const d = new Date(ts.replace(" ", "T"));
    const today = new Date();
    const time = d.toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit" });
    if (d.toDateString() === today.toDateString()) return `${t("tz_today")}<br>${time}`;
    return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" }) + `<br>${time}`;
  }
  function rowHTML(e, showName = true) {
    return `<li class="${e.status === "cancelled" ? "cancelled" : ""}">
      <span class="when num">${when(e.created_at)}</span>
      <span class="who">${showName ? `<a href="#/c/${e.customer_id}">${esc(e.customer_name)}</a>` : t(e.type)}
        <small>${showName ? t(e.type) : ""}${e.note ? (showName ? " · " : "") + esc(e.note) : ""}
        ${!showName && e.status === "active" ? `<button class="mini-undo" data-cancel="${e.id}">${t("cancel_entry")}</button>` : ""}</small></span>
      <span class="val num ${e.type}">${e.type === "credit" ? "+" : "−"}${inr(e.amount)}</span>
    </li>`;
  }

  async function viewHome() {
    const welcome = localStorage.getItem("bk_welcomed") ? "" : `
      <section class="welcome" id="welcome" aria-label="welcome">
        <h2>${t("welcome_title")}</h2>
        <ol><li>${t("welcome_1")}</li><li>${t("welcome_2")}</li><li>${t("welcome_3")}</li></ol>
        <button class="btn primary" id="welcomeOk">${t("got_it")}</button>
      </section>`;
    const demo = S.config.demo ? `
      <section class="demo-banner" id="demoBanner">
        <p>${t("demo_banner")}</p>
        <button class="btn ghost" id="demoClear">${t("demo_clear")}</button>
      </section>` : "";
    $("#view").innerHTML = `${welcome}${demo}
      <section class="today" aria-label="today">
        <div><div class="lbl">${t("today_given")}</div><div class="amt credit num" id="tGiven">—</div></div>
        <div><div class="lbl">${t("today_got")}</div><div class="amt payment num" id="tGot">—</div></div>
      </section>
      <p class="pending-line" id="pendingLine"></p>
      <section class="mic-wrap">
        <button class="mic" id="mic" aria-label="${t("tap")}" aria-pressed="false">${micSVG}</button>
        <div class="mic-hint" id="micHint">${t("tap")}</div>
        <div class="heard" id="heard"></div>
        <div class="examples">${UI.examples[S.lang]}</div>
        <form class="typebox" id="typeForm" autocomplete="off">
          <input id="typeInput" maxlength="300" placeholder="${t("type_here")}" aria-label="${t("type_here")}">
          <button>${t("go")}</button>
        </form>
      </section>
      <div class="reply" id="reply" hidden role="status"></div>
      <section class="promises" id="promises" hidden></section>
      <h2>${t("recent")}</h2>
      <ul class="ledger" id="recent"></ul>`;
    $("#mic").onclick = onMic;
    if ($("#welcomeOk")) $("#welcomeOk").onclick = () => { localStorage.setItem("bk_welcomed", "1"); $("#welcome").remove(); };
    if ($("#demoClear")) $("#demoClear").onclick = () => demoClearFlow($("#demoBanner"));
    $("#typeForm").onsubmit = (ev) => {
      ev.preventDefault();
      const v = $("#typeInput").value; $("#typeInput").value = "";
      $("#heard").textContent = v ? "“" + v + "”" : ""; handleText(v, { source: "typed" });
    };
    if (!canListen()) showReply(t("no_speech"));
    refreshHome();
  }

  function demoClearFlow(host) {
    host.innerHTML = `<p>${t("demo_sure")}</p>
      <div class="set-row"><button class="btn primary" id="demoYes">${t("yes_clear")}</button><button class="btn ghost" id="demoNo">${t("keep")}</button></div>`;
    $("#demoNo").onclick = () => router();
    $("#demoYes").onclick = async () => {
      try { await api("/api/demo/clear", { method: "POST", body: {} }); S.config.demo = false; }
      catch (e) { if (e.message === "locked") return; }
      router();
    };
  }

  async function refreshHome() {
    if (!$("#recent")) return;
    try {
      const s = await api("/api/summary");
      $("#tGiven").textContent = inr(s.today_given);
      $("#tGot").textContent = inr(s.today_collected);
      $("#pendingLine").innerHTML = `${t("pending")}: <b class="num">${inr(s.outstanding)}</b>, ${S.lang === "en" && s.customers_due === 1 ? "from 1 customer" : t("from_n", { n: s.customers_due })}`;
      const box = $("#promises");
      if (box) {
        box.hidden = !s.promises.length;
        box.innerHTML = s.promises.length ? `<h2>${t("promises_title")}</h2><ul class="ledger plist">${s.promises.map((x) => `
          <li><a class="who" href="#/c/${x.customer_id}">${esc(x.name)}
              <small class="chip c-${x.state}">${x.state === "overdue" ? t("p_overdue") + " · " + esc(whenLabel(x.promise_date)) : x.state === "today" ? t("p_today") : esc(whenLabel(x.promise_date))}</small></a>
            <span class="val num credit">${inr(x.balance)}</span></li>`).join("")}</ul>` : "";
      }
      $("#recent").innerHTML = s.recent.length ? s.recent.map((e) => rowHTML(e)).join("") : `<li class="empty empty-row">${t("no_entries")}</li>`;
    } catch (_) { /* offline: keep what is shown */ }
  }

  async function viewCustomers() {
    $("#view").innerHTML = `<h2 class="h-tight">${t("customers")}</h2>
      <input class="search" id="search" maxlength="60" placeholder="${t("search")}" aria-label="${t("search")}">
      <ul class="ledger list-gap" id="clist"></ul>`;
    const render = async (q) => {
      const list = await api("/api/customers" + (q ? `?q=${encodeURIComponent(q)}` : ""));
      $("#clist").innerHTML = list.map((c) => `<li class="cust"><a href="#/c/${c.id}" class="who">${esc(c.name)}
        <small>${c.last_at ? when(c.last_at).replace("<br>", ", ") : ""}</small></a>
        <span class="val num ${c.balance > 0 ? "credit" : "payment"}">${c.balance > 0 ? inr(c.balance) : (c.balance < 0 ? t("advance") + " " + inr(c.balance) : t("clear"))}</span></li>`).join("");
    };
    $("#search").oninput = (ev) => render(ev.target.value.trim());
    render();
  }

  async function viewCustomer(id) {
    const c = await api(`/api/customers/${id}?lang=${S.lang}`);
    const due = c.balance > 0;
    $("#view").innerHTML = `
      <button class="back" id="backBtn">${t("back")}</button>
      <div class="cust-head">
        <h1>${esc(c.name)}</h1>
        <div class="bal num ${due ? "due" : "clear"}">${due ? inr(c.balance) : (c.balance < 0 ? t("advance") + " " + inr(c.balance) : t("clear"))}</div>
        ${due ? `<div class="lbl">${t("owes")}</div>` : ""}
      </div>
      <div class="actions">
        ${due ? `<a class="btn wa" href="${esc(c.whatsapp_url)}" target="_blank" rel="noopener noreferrer">💬 ${t("remind")}</a>` : ""}
      </div>
      ${due ? `<section class="promise-box" aria-label="${t("set_when")}">
        <div class="lbl">${t("set_when")}</div>
        ${c.promise_date ? `<div class="p-now ${dayDiff(c.promise_date) < 0 ? "overdue" : ""}">📅 ${esc(t("promise_line", { when: whenLabel(c.promise_date) }))}${dayDiff(c.promise_date) < 0 ? " · " + t("p_overdue") : ""}</div>` : ""}
        <form class="set-row" id="promiseForm">
          <input type="date" id="pDate" required min="${new Date().toLocaleDateString("en-CA")}" value="${esc(c.promise_date || "")}" aria-label="${t("set_when")}">
          <button class="btn ghost">${t("save_phone")}</button>
          ${c.promise_date ? `<button type="button" class="btn ghost" id="pClear">${t("clear_promise")}</button>` : ""}
        </form></section>` : ""}
      <form class="phone" id="phoneForm">
        <input id="phone" inputmode="tel" maxlength="20" pattern="\\+?[0-9][0-9 \\-]{6,18}" placeholder="${t("phone")}" value="${esc(c.phone || "")}" aria-label="${t("phone")}">
        <button class="btn ghost">${t("save_phone")}</button>
      </form>
      <h2>${t("history")}</h2>
      <ul class="ledger">${c.entries.map((e) => rowHTML(e, false)).join("") || `<li class="empty empty-row">—</li>`}</ul>`;
    $("#backBtn").onclick = () => history.back();
    $("#phoneForm").onsubmit = async (ev) => {
      ev.preventDefault();
      try {
        await api(`/api/customers/${id}`, { method: "PATCH", body: { phone: $("#phone").value.trim() } });
        viewCustomer(id);
      } catch (e) { if (e.message !== "locked") { $("#phone").setCustomValidity(t("phone")); $("#phone").reportValidity(); } }
    };
    if ($("#promiseForm")) {
      const setP = async (v) => { try { await api(`/api/customers/${id}`, { method: "PATCH", body: { promise_date: v } }); viewCustomer(id); } catch (e) { if (e.message !== "locked") { $("#pDate").setCustomValidity(t("set_when")); $("#pDate").reportValidity(); } } };
      $("#promiseForm").onsubmit = (ev) => { ev.preventDefault(); setP($("#pDate").value); };
      if ($("#pClear")) $("#pClear").onclick = () => setP("");
    }
    $("#view").querySelectorAll("[data-cancel]").forEach((b) => b.onclick = async () => {
      await api(`/api/entries/${b.dataset.cancel}/cancel`, { method: "POST" });
      viewCustomer(id);
    });
  }

  // ------------------------------------------------------------ lock screen
  function showLock() {
    stopListening(); closeSheet();
    S.locked = true;
    document.querySelector(".tabs").hidden = true;
    let pin = "";
    $("#view").innerHTML = `<section class="lock">
      <h1>🔒 ${t("lock_title")}</h1>
      <div class="dots" id="dots" aria-hidden="true"></div>
      <div class="lock-msg" id="lockMsg" role="alert"></div>
      <div class="keypad">
        ${[1,2,3,4,5,6,7,8,9].map((n) => `<button data-k="${n}">${n}</button>`).join("")}
        <button data-k="del" aria-label="delete">⌫</button><button data-k="0">0</button>
        <button data-k="go" class="k-go">${t("unlock")}</button>
      </div></section>`;
    const draw = () => { $("#dots").innerHTML = Array.from({ length: Math.max(4, pin.length) }, (_, i) => `<i class="${i < pin.length ? "on" : ""}"></i>`).join(""); };
    const submit = async () => {
      if (pin.length < 4) return;
      try {
        await api("/api/auth/login", { method: "POST", body: { pin } });
        S.locked = false; document.querySelector(".tabs").hidden = false; location.hash = "#/"; router(); flushQueue();
      } catch (e) {
        const [msg, wait] = String(e.message).split("|");
        $("#lockMsg").textContent = e.status === 429 || (wait && +wait > 0) ? t("lock_wait", { s: wait || 60 }) : t("lock_wrong");
        pin = ""; draw();
      }
    };
    $("#view").querySelectorAll("[data-k]").forEach((b) => b.onclick = () => {
      const k = b.dataset.k;
      if (k === "del") pin = pin.slice(0, -1);
      else if (k === "go") return submit();
      else if (pin.length < 8) pin += k;
      draw();
    });
    S.lockKeys = (ev) => {
      if (!S.locked) return;
      if (/^\d$/.test(ev.key) && pin.length < 8) { pin += ev.key; draw(); }
      else if (ev.key === "Backspace") { pin = pin.slice(0, -1); draw(); }
      else if (ev.key === "Enter") submit();
    };
    draw();
  }
  addEventListener("keydown", (ev) => S.lockKeys && S.lockKeys(ev));

  // ------------------------------------------------------------ settings
  async function viewSettings() {
    const s = await api("/api/settings");
    $("#view").innerHTML = `<h2 class="h-tight">${t("nav_settings")}</h2>
      <section class="set-block">
        <h3>${t("set_shop")}</h3><p>${t("set_shop_help")}</p>
        <form class="set-row" id="shopForm"><input id="shopIn" maxlength="60" value="${esc(s.shop_name)}" aria-label="${t("set_shop")}"><button class="btn ghost">${t("save_phone")}</button></form>
        <div class="set-msg" id="shopMsg" role="status"></div>
      </section>
      <section class="set-block">
        <h3>🔒 ${t("set_pin")}</h3><p>${s.pin_enabled ? t("set_pin_on") : t("set_pin_off")}</p>
        <form class="set-row" id="pinForm">
          ${s.pin_enabled ? `<input id="curPin" type="password" inputmode="numeric" autocomplete="current-password" maxlength="8" placeholder="${t("cur_pin")}" aria-label="${t("cur_pin")}">` : ""}
          <input id="newPin" type="password" inputmode="numeric" autocomplete="new-password" maxlength="8" placeholder="${t("new_pin")}" aria-label="${t("new_pin")}">
          <button class="btn primary">${s.pin_enabled ? t("pin_change") : t("pin_set")}</button>
        </form>
        ${s.pin_enabled ? `<div class="set-row list-gap"><button class="btn ghost" id="pinRemove">${t("pin_remove")}</button><button class="btn ghost" id="lockNow">${t("lock_now")}</button></div>` : ""}
        <div class="set-msg" id="pinMsg" role="status"></div>
      </section>
      <section class="set-block">
        <h3>${t("set_export")}</h3><p>${t("set_export_help")}</p>
        <a class="btn ghost" href="/api/export.csv" download>⬇ ${t("export_btn")}</a>
      </section>
      ${s.demo ? `<section class="set-block" id="demoBlock"><h3>${t("demo_banner")}</h3>
        <button class="btn ghost" id="demoClear2">${t("demo_clear")}</button></section>` : ""}
      <section class="set-block">
        <h3>${t("set_privacy")}</h3><p>${t("set_privacy_help")}</p>
        ${s.stt ? `<p>${t("set_privacy_stt")}</p>` : ""}
      </section>
      <div class="version">Bolo Khata v${esc(s.version)}</div>`;
    if ($("#demoClear2")) $("#demoClear2").onclick = () => demoClearFlow($("#demoBlock"));
    const msg = (id, text, err) => { const el = $(id); el.textContent = text; el.classList.toggle("err", !!err); };
    $("#shopForm").onsubmit = async (ev) => {
      ev.preventDefault();
      const r = await api("/api/settings", { method: "PATCH", body: { shop_name: $("#shopIn").value } });
      $("#shopName").textContent = r.shop_name; msg("#shopMsg", t("saved_ok"));
    };
    const pinCall = async (body) => {
      try { await api("/api/auth/pin", { method: "POST", body }); viewSettings(); }
      catch (e) { if (e.message !== "locked") msg("#pinMsg", e.status === 422 ? t("pin_bad") : (e.status === 429 ? t("lock_wait", { s: String(e.message).split("|")[1] || 60 }) : t("lock_wrong")), true); }
    };
    $("#pinForm").onsubmit = (ev) => {
      ev.preventDefault();
      const np = $("#newPin").value.trim();
      if (!/^\d{4,8}$/.test(np)) return msg("#pinMsg", t("pin_bad"), true);
      pinCall({ current: $("#curPin")?.value.trim() || null, new: np });
    };
    if (s.pin_enabled) {
      $("#pinRemove").onclick = () => {
        const cur = $("#curPin").value.trim();
        if (!/^\d{4,8}$/.test(cur)) return msg("#pinMsg", t("pin_bad"), true);
        pinCall({ current: cur, new: null });
      };
      $("#lockNow").onclick = async () => { await api("/api/auth/logout", { method: "POST", body: {} }); showLock(); };
    }
  }

  function refreshAll() {
    const h = location.hash;
    if (h.startsWith("#/c/")) viewCustomer(h.split("/")[2]);
    else if (h === "#/customers") viewCustomers();
    else refreshHome();
  }

  // ------------------------------------------------------------ router + chrome
  function router() {
    stopListening();
    const h = location.hash || "#/";
    document.querySelectorAll(".tabs a").forEach((a) => a.classList.toggle("on",
      (a.dataset.tab === "home" && (h === "#/" || h === "")) || (a.dataset.tab === "settings" && h === "#/settings") ||
      (a.dataset.tab === "customers" && (h === "#/customers" || h.startsWith("#/c/")))));
    if (S.locked) return showLock();
    if (h.startsWith("#/c/")) return viewCustomer(h.split("/")[2]).catch(() => {});
    if (h === "#/customers") return viewCustomers().catch(() => {});
    if (h === "#/settings") return viewSettings().catch(() => {});
    return viewHome();
  }
  function applyLang() {
    document.documentElement.lang = S.lang === "en" ? "en" : S.lang;
    document.querySelectorAll(".langs button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.lang === S.lang)));
    document.querySelectorAll("[data-t]").forEach((el) => { el.textContent = t(el.dataset.t); });
    renderOffline();
  }
  document.querySelectorAll(".langs button").forEach((b) => b.onclick = () => {
    S.lang = b.dataset.lang; localStorage.setItem("bk_lang", S.lang); applyLang(); router();
  });

  // Space bar = press the mic (handy on a counter laptop)
  addEventListener("keydown", (ev) => {
    if (ev.code === "Space" && !S.locked && document.activeElement?.tagName !== "INPUT" && document.activeElement?.tagName !== "BUTTON" && $("#mic") && $("#sheet").hidden) { ev.preventDefault(); onMic(); }
  });

  addEventListener("hashchange", router);
  (async () => {
    try { S.config = await api("/api/config"); $("#shopName").textContent = S.config.shop_name; } catch (_) {}
    if (!localStorage.getItem("bk_lang") && S.config.default_lang) S.lang = S.config.default_lang;
    applyLang();
    try { const st = await api("/api/auth/status"); if (!st.unlocked) { showLock(); } else { router(); flushQueue(); } }
    catch (_) { router(); }
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
  })();

  // exposed for automated UI tests only
  window.BoloKhata = Object.freeze({ handleText });
})();
