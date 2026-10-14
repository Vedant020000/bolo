"""Character packs — personalities for your computer.

A pack maps an event (tests passed, build failed, commit, agent done...) to a
line spoken in a specific Bulbul persona. This is the commentary layer:
your machine's life, narrated like a broadcast.

Text rules: Hindi words in Devanagari, English words in Latin — that is the
code-mixing shape Bulbul renders best.
"""

from __future__ import annotations

PACKS: dict[str, dict] = {
    "cricket": {
        "blurb": "match commentary for your build",
        "voice": "ratan_hi_sports",
        "lang": "hi-IN",
        "intro": "नमस्कार दोस्तों! Commentary शुरू — आज देखते हैं computer क्या खेल दिखाता है!",
        "lines": {
            "tests_ok": "और ye देखो — {detail} — सब पास! ये तो चौका हो गया, दोस्तों!",
            "tests_fail": "अरे! {detail} — एक wicket गिरा! पवेलियन में मातम, दोस्तों।",
            "build_ok": "और ye build... सीधे बाउंड्री के पार! Build pass! क्या शॉट!",
            "build_fail": "और... GONE! Build fail! ये तो unexpected ball थी, दोस्तों!",
            "commit": "एक और commit! चौका! {detail}",
            "agent_done": "और umpire ने stumps उठा लिए — agent की पारी ख़त्म! {detail}",
            "generic": "देखिए क्या हो रहा है — {detail}",
        },
    },
    "news": {
        "blurb": "breaking-news bulletin for your terminal",
        "voice": "simran_hi_news_breaking",
        "lang": "hi-IN",
        "intro": "नमस्कार! मैं हूँ आपकी ख़बरों के साथ — bolo न्यूज़ बुलेटिन शुरू होता है।",
        "lines": {
            "tests_ok": "ब्रेकिंग न्यूज़! {detail} — सभी टेस्ट पास। Developer समुदाय में हर्ष की लहर।",
            "tests_fail": "ब्रेकिंग न्यूज़! {detail} — टेस्ट फ़ेल। हमारे संवाददाता टर्मिनल पर मौजूद हैं।",
            "build_ok": "ताज़ा ख़बर — build सफल। शेयर बाज़ार में उछाल।",
            "build_fail": "बड़ी ख़बर! Build फ़ेल। लाइन 42 पर एक error की पुष्टि हुई है।",
            "commit": "सूचना मिली है कि एक नया commit पुश हुआ है। {detail}",
            "agent_done": "अंतिम ख़बर — agent ने अपना काम पूरा कर लिया है। {detail}",
            "generic": "हमें ख़बर मिली है — {detail}",
        },
    },
    "trailer": {
        "blurb": "Bollywood-trailer drama for your commits",
        "voice": "mukul_hi_suspense",
        "lang": "hi-IN",
        "intro": "एक computer था। एक developer था। और एक चैलेंज... जिसे हर कोई देखेगा।",
        "lines": {
            "tests_ok": "और फिर... सभी tests पास हुए... और हर किसी ने राहत की सांस ली।",
            "tests_fail": "एक test... जो बच गया था... और एक developer... जो हार नहीं मानेगा।",
            "build_ok": "इस रात... एक build... जो जीत गया।",
            "build_fail": "एक build fail हुआ... और एक सच्चाई सामने आई... जिसने सब कुछ बदल दिया।",
            "commit": "एक commit... जिसने सब कुछ बदल दिया। {detail}",
            "agent_done": "और अब... agent ने आँखें खोलीं... और काम शुरू हुआ। {detail}",
            "generic": "कुछ ऐसा होने वाला है... जो पहले कभी नहीं हुआ...",
        },
    },
    "documentary": {
        "blurb": "nature-documentary for your terminal",
        "voice": "anand_hi_documentary",
        "lang": "hi-IN",
        "intro": "यहाँ... घने टर्मिनल के जंगल में... हम एक developer का रोज़ देखेंगे।",
        "lines": {
            "tests_ok": "और यहाँ... टर्मिनल के जंगल में... सभी tests पास हो जाते हैं। आश्चर्यजनक।",
            "tests_fail": "यहाँ... हम देखते हैं... एक test... जो टिक नहीं पाया। प्रकृति का नियम है।",
            "build_ok": "और देखिए... build... धीरे-धीरे... सफलता की ओर बढ़ता है।",
            "build_fail": "यहाँ... हम देखते हैं... एक build... अपने अंत की ओर बढ़ता हुआ।",
            "commit": "एक commit... जंगल में एक नई पगडंडी की तरह। {detail}",
            "agent_done": "और अब... agent अपनी मांद में लौटता है। {detail}",
            "generic": "यहाँ... {detail} ... मनोरम दृश्य।",
        },
    },
    "dost": {
        "blurb": "Hinglish friend who always has your back",
        "voice": "shubh_enhi_companion",
        "lang": "auto",
        "intro": "Aaja bhai! Main hoon — jo bhi ho raha hai, main sunta rehta hoon.",
        "lines": {
            "tests_ok": "Bhai, {detail} — sab pass! Chai le aa, celebrate karte hain!",
            "tests_fail": "Arre yaar, {detail} — chill, ye bhi fix ho jayega. Main hoon na.",
            "build_ok": "Ho gaya! Build pass! Proud of you, bhai.",
            "build_fail": "Oho, build gaya. Koi baat nahi — errors se hi toh seekhte hain.",
            "commit": "Naya commit push ho gaya! {detail}",
            "agent_done": "Agent aa gaya wapas! {detail} — sun na, kya kiya usne...",
            "generic": "Dekh bhai — {detail}",
        },
    },
    "hype": {
        "blurb": "hype man for your wins",
        "voice": "sunny_hi_reels",
        "lang": "hi-IN",
        "intro": "Chalo chalo chalo! Aaj toh kuch dhamaka hone wala hai!",
        "lines": {
            "tests_ok": "AAAYE! {detail} — सब pass! Kya baat hai! Full paisa vasool!",
            "build_ok": "AUR YE BUILD — PASS! Dhamaka! Full on!",
            "commit": "Ek aur commit! {detail} — chhaa gaye bhai!",
            "agent_done": "AGENT NE KAAM KAR DIYA! {detail} — legend hai legend!",
            "tests_fail": "Koi baat nahi! {detail} — comeback hoga, full filmy style mein!",
            "build_fail": "Arre arre arre... {detail} — next one mein aag laga denge!",
            "generic": "{detail} — ekdum mast!",
        },
    },
    "maa": {
        "blurb": "your mom, but for your code",
        "voice": "suman_hi_companion",
        "lang": "hi-IN",
        "intro": "Beta, main aa gayi. Ab batao — aaj kya banaya?",
        "lines": {
            "tests_ok": "Shabaash beta! {detail} — sab pass! Ab thoda aaram bhi kar lo.",
            "tests_fail": "Koi baat nahi beta. {detail} — hota hai. Chai pee lo, phir dekh lenge.",
            "build_ok": "Wah beta! Build pass! Dekha, maine kaha tha na — tum kar loge.",
            "build_fail": "Beta, phir se build fail? Khana kha lo pehle, sab theek ho jayega.",
            "commit": "Achha kaam, beta! {detail} — Maa ko hamesha pata hota hai.",
            "agent_done": "Beta, tumhara agent kaam karke aa gaya. {detail}",
            "generic": "Sun beta — {detail}",
        },
    },
}


def get(pack: str) -> dict | None:
    return PACKS.get(pack)


def intro(pack: str) -> dict | None:
    p = PACKS.get(pack)
    if not p or not p.get("intro"):
        return None
    return {"text": p["intro"], "voice": p.get("voice"), "lang": p.get("lang", "auto")}


def line_for(pack: str, etype: str, detail: str = "") -> dict | None:
    p = PACKS.get(pack)
    if not p:
        return None
    lines = p.get("lines") or {}
    tpl = lines.get(etype) or lines.get("generic")
    if not tpl:
        return None
    try:
        text = tpl.format(detail=detail) if detail else tpl.replace("{detail}", "").replace("  ", " ").strip()
    except Exception:
        text = tpl
    if not text:
        return None
    return {"text": text, "voice": p.get("voice"), "lang": p.get("lang", "auto")}
