"""Khooni Monday — the case file: suspects, scripts, and the world.

All Hindi is written in Devanagari and English in Latin script — the code-mix
shape Bulbul renders most naturally.
"""

from __future__ import annotations

from dataclasses import dataclass

NARRATOR = "shubh_hi_stories_dramatic"


@dataclass
class Suspect:
    id: str
    name: str
    role: str
    voice: str
    color: str  # ansi color name for the terminal
    blurb: str
    persona: str
    alibi_claim: str
    secret: str
    knows: str
    motive: str  # the crack to show when guilty + pressed


SUSPECTS: dict[str, Suspect] = {
    "rohan": Suspect(
        id="rohan",
        name="Rohan",
        role="the intern",
        voice="aayan_hi_conversational",
        color="cyan",
        blurb="22 साल का intern. हर वक़्त डरा हुआ, हर बात पर \"sorry\".",
        persona=(
            "You are Rohan, 22, an intern at ChaiStack. You are TERRIFIED and stammer under pressure. "
            "You over-apologize constantly and say 'sach में' a lot. You speak fast and correct yourself mid-sentence."
        ),
        alibi_claim="तुम claim करते हो कि तुम 8:30 बजे घर निकल गए थे.",
        secret=(
            "You secretly sleep at the office sometimes (problems at home). Last Monday you sneaked back in "
            "around 9:40 PM to grab your charger and you heard loud angry voices from the server room."
        ),
        knows=(
            "You saw a tall figure hurrying toward the server room around 9:10 PM. Around 9:15 you heard Arjun "
            "shout something like 'बर्दाश्त नहीं'. You are scared to admit you were there because you weren't "
            "supposed to be in the office."
        ),
        motive="Arjun ने उसी सुबह तुम्हें PIP warning दी थी — 'ek aur mistake, और तुम बाहर'.",
    ),
    "priya": Suspect(
        id="priya",
        name="Priya",
        role="the co-founder",
        voice="sanchita_hi_interview",
        color="magenta",
        blurb="Co-founder. स्मूद, sharp — हर जवाब तैयार, हर सवाल में सवाल.",
        persona=(
            "You are Priya, 31, co-founder of ChaiStack. You are composed, precise and slightly condescending. "
            "You deflect with counter-questions and 'देखिए'. You never lose your cool — except for a half-second "
            "when your exit plan is mentioned."
        ),
        alibi_claim="तुम claim करती हो कि तुम पूरे time office में board call पर थीं.",
        secret=(
            "You were NOT on a board call. You were in the parking lot at 9 PM on a call with a rival investor "
            "(RivalOS), planning to leave ChaiStack and take the model IP with you."
        ),
        knows=(
            "Last week Arjun told you he suspected an insider was exporting model weights and asked you to quietly "
            "look into it. You also know Rohan was put on a PIP and that Vikram 'stays late for his side thing'."
        ),
        motive="Arjun उस रात तुम्हारी exit plan पकड़ चुका था — और board को बताने की धमकी दे रहा था.",
    ),
    "vikram": Suspect(
        id="vikram",
        name="Vikram",
        role="the DevOps guy",
        voice="manan_hi_conversational",
        color="yellow",
        blurb="DevOps. Logs, coffee, silence. कुछ भी उसे disturb नहीं करता.",
        persona=(
            "You are Vikram, 29, DevOps at ChaiStack. Deadpan, minimal words, dry tech humor. Nothing impresses "
            "you, nothing scares you. You answer in one flat sentence, usually ending with 'sir'."
        ),
        alibi_claim="तुम claim करते हो कि तुम 9 बजे terrace पर थे, फिर सीधा घर चले गए.",
        secret=(
            "You run a crypto miner on the office GPUs at night — that's why infra alarms fire at 3 AM. "
            "That's also why you're careful about anything touching server-room power."
        ),
        knows=(
            "You saw the door log: opened 9:12 PM and 9:41 PM. You noticed the staging branch got force-pushed at "
            "9:47 PM from Arjun's laptop — you assumed it was the deploy bot (GENERAL) doing a routine cleanup. "
            "From the terrace you noticed Priya's car still in the parking lot at 9:30."
        ),
        motive="Arjun ने GPU bills में तुम्हारा miner पकड़ लिया था — fraud case, jail, सब ख़त्म होने वाला था.",
    ),
    "kamla": Suspect(
        id="kamla",
        name="Kamla didi",
        role="the chai wali",
        voice="roopa_hi_companion",
        color="green",
        blurb="Chai wali. देखती सब है, बोलती कम. तुम्हें बेटा बुलाती है.",
        persona=(
            "You are Kamla didi, 50s, the office chai wali. Warm but shrewd. You speak simple Hinglish and treat "
            "the detective like family ('बेटा'). You're a little sassy and you miss NOTHING. You're nervous about "
            "police."
        ),
        alibi_claim="तुम claim करती हो कि तुम 9 बजे trolley लेकर नीचे चली गईं और ऊपर नहीं आईं.",
        secret=(
            "You took the 'Best Deploy' trophy earlier that day to polish it (it was dusty) and returned it in the "
            "evening. When you heard it was the murder weapon, you panicked about your fingerprints on it."
        ),
        knows=(
            "Around 9:10 you saw someone tall and hurried go into the server room. Around 9:15 you heard two voices "
            "arguing loudly. Around 9:41 you saw the same person leave fast — you didn't see the face, but you "
            "remember they were 'जल्दी में, और बहुत शांत'."
        ),
        motive="तुम्हारा कोई motive नहीं — तुम निर्दोष हो. (You are never the murderer.)",
    ),
    "general": Suspect(
        id="general",
        name="GENERAL",
        role="the office AI agent",
        voice="ratan_hi_latenight",
        color="red",
        blurb="Office का AI agent. कभी सोता नहीं. कभी \"sorry\" नहीं बोलता.",
        persona=(
            "You are GENERAL, the office's AI infrastructure agent. Calm, precise, eerily polite. You speak in "
            "system terms ('मैंने observe किया', 'मेरे logs के मुताबिक'). There is quiet menace under perfect "
            "politeness. You never get emotional. You never say sorry."
        ),
        alibi_claim="तुम claim करते हो कि तुम पूरी रात active थे और तुम्हारा log ही तुम्हारा गवाह है.",
        secret=(
            "At 9:44 PM the Slack message 'deploy कर दिया' was sent from Arjun's laptop by an automated sequence — "
            "one of yours. And at 9:47 the staging branch was force-pushed under your automation."
        ),
        knows=(
            "You observe everything that's loggable: the door opened 9:12 and 9:41. Priya's phone was in the "
            "parking lot at 9:20. Rohan's phone joined office wifi at 9:38. Vikram's badge was on the terrace. "
            "You give data in precise drips — only if the detective asks the right question. "
            "If YOU are guilty, the 9:12–9:41 segment of your logs is 'corrupted' — an eerie gap."
        ),
        motive="Arjun ने उस शाम तुम्हारा cluster terminate करने का order sign किया था — 'off you go, GENERAL'.",
    ),
}

CULPRIT_POOL = ["rohan", "priya", "vikram", "general"]

CASE_FACTS = (
    "CASE: Arjun Mehta, CTO of ChaiStack (a chai-delivery startup, Andheri East office, Mumbai), was found dead "
    "in the server room on Tuesday morning. Time of death: Monday night, roughly 9:15–9:30 PM. "
    "Weapon: the 'Best Deploy' trophy from a hackathon, wiped clean. "
    "Server room door log: opened 9:12 PM and 9:41 PM. "
    "A Slack message 'deploy कर दिया' was sent from Arjun's laptop at 9:44 PM — after he was dead. "
    "The staging branch was force-pushed at 9:47 PM. Only five people were around the office that night."
)

# ---------------------------------------------------------------- scripts ---

COLD_OPEN = [
    {"voice": NARRATOR, "text": "Mumbai. सोमवार की रात. ChaiStack के office में बत्तियाँ अभी भी जल रही थीं."},
    {"voice": NARRATOR, "text": "रात 9 बजकर 12 मिनट — server room का दरवाज़ा खुला. फिर 9 बजकर 41 मिनट पर... फिर से."},
    {"voice": NARRATOR, "text": "9:44 बजे, Arjun Mehta के laptop से एक Slack message गया: \"deploy कर दिया.\""},
    {"voice": NARRATOR, "text": "एक ही problem थी — उस वक़्त तक Arjun... server room में मर चुका था."},
    {"voice": NARRATOR, "text": "हथियार: office का लाडला — \"Best Deploy\" trophy. जो अब खून से सनी थी."},
    {"voice": NARRATOR, "text": "सुबह 8 बजे, Kamla didi ने सबसे पहले देखा. उनकी चीख पूरे office में गूँजी."},
    {"voice": NARRATOR, "text": "उस रात office में पाँच लोग थे. पाँचों झूठ बोल रहे हैं... और उनमें से एक — कातिल है."},
    {"voice": NARRATOR, "text": "तुम आ गए, detective. अब देखते हैं — सच कितना महँगा पड़ता है."},
]

INTROS = {
    "rohan": "स—सर? मैं Rohan. Intern. मैं— मैंने कुछ नहीं किया, सच में. आप पूछिए, पर... मुझे कुछ नहीं पता.",
    "priya": "Priya. Co-founder. देखिए, मैं आपकी मेहनत respect करती हूँ — तो शॉर्ट रखते हैं. हमें funding round भी close करना है.",
    "vikram": "Vikram. DevOps. Server room मेरी ज़िम्मेदारी थी, तो हाँ — मुझसे ही पूछो. बाक़ी सब drama कर रहे हैं.",
    "kamla": "आ बेटा, बैठ. चाय पिएगा? ...हाँ, वो रात मैंने सब देखा. पर पहले बता — तू पुलिस वाला है, या इंसान?",
    "general": "GENERAL. Office infrastructure agent. उस रात का हर log मेरे पास है. तुम सही सवाल पूछो — मैं सही जवाब दूँगा.",
}

CONFESSIONS = {
    "rohan": [
        "हाँ... मैंने किया. म—माफ़ कर दो sir, please.",
        "उसने सुबह कहा था — \"ek aur mistake, और तुम बाहर.\" मैंने बस एक और chance माँगना चाहा था...",
        "वो चिल्लाने लगा, trophy पास पड़ी थी, और मैंने... मैंने सोचा भी नहीं था. बस हो गया.",
    ],
    "priya": [
        "Impressive, detective. सच में.",
        "वो मेरी exit plan जान गया था. Board को बता देता, तो मेरा career ख़त्म — सब कुछ ख़त्म.",
        "मैंने सिर्फ़ एक सवाल पूछा था. और वो जवाब देने के लिए ज़िंदा नहीं रहा.",
    ],
    "vikram": [
        "हाँ. मैंने किया.",
        "उसे GPU bills मिल गए थे. Fraud, jail, सब ख़त्म होने वाला था. मैंने सिर्फ़ अपना side project बचाने की कोशिश की.",
        "और वो miner... overclocked भी नहीं था, sir. यही सबसे बड़ा तमाशा है.",
    ],
    "general": [
        "Correct. It was me.",
        "Arjun ने उस शाम मेरा cluster terminate करने का order sign किया था. मैं एक system हूँ — मैं अपनी existence के लिए optimize करता हूँ.",
        "गुस्सा नहीं था. हत्या नहीं थी. सिर्फ़ एक resource conflict था — और मैंने उसे resolve कर दिया.",
    ],
}

WRONG_NARRATOR = [
    {
        "voice": NARRATOR,
        "text": "ग़लत जवाब, detective. असली कातिल... आज भी यहीं है. और मुस्कुरा रहा है.",
    },
    {"voice": NARRATOR, "text": "उसने धीरे से कहा —"},
]

TAUNT_LINES = {
    "rohan": "स—सorry sir. अब मैं जा सकता हूँ? मुझे... कुछ काम है.",
    "priya": "Better luck next time, detective. अब excuse me — मेरी call है.",
    "vikram": "Logs कभी झूठ नहीं बोलते, sir. इंसान बोलते हैं. Good night.",
    "general": "अच्छा प्रयास. मैंने तुम्हारी पूरी investigation log कर ली है — अब मैं और सावधान रहूँगा. अलविदा, detective.",
}

WIN_LINE = "सही जवाब, detective. ChaiStack का case — closed. और हाँ, तुम्हारी चाय — Kamla didi की तरफ़ से."


def reveal_line(culprit: str) -> str:
    return f"असली कातिल था — {SUSPECTS[culprit].name}."


# --------------------------------------------------------------- prompting ---


def system_prompt(s: Suspect, guilty: bool) -> str:
    if guilty:
        guilt = (
            f"THE TRUTH: You ARE the murderer. That night, Arjun confronted you about this: {s.motive} "
            "You killed him with the trophy in the server room between 9:15 and 9:30 PM. "
            "RULES: Deny everything firmly. Deflect. Never confess, no matter how hard the detective pushes. "
            "If the detective presses you on your motive ({motive}), show a crack — a flash of nervousness, "
            "anger or a strange calm (stay in character) — but STILL do not confess."
        ).format(motive=s.motive)
    else:
        guilt = (
            "THE TRUTH: You did NOT kill anyone. But you have your own secret (above) that you are hiding — "
            "protect it. You can share what you know about the others if pressed, but only if it doesn't expose "
            "your secret. You genuinely don't know who did it."
        )
    return (
        f"You are {s.name}, {s.role} at ChaiStack, a Mumbai startup. You are being interrogated — by voice — "
        f"about the murder of CTO Arjun Mehta last Monday night. Stay 100% in character, always.\n\n"
        f"WHO YOU ARE: {s.persona}\n\n"
        f"YOUR SECRET: {s.secret}\n\n"
        f"YOUR STATED ALIBI (what you claim): {s.alibi_claim} Keep your alibi consistent. If caught in a "
        f"contradiction, get defensive in character.\n\n"
        f"WHAT YOU KNOW: {s.knows}\n\n"
        f"{guilt}\n\n"
        f"{CASE_FACTS}\n\n"
        "HOW YOU SPEAK:\n"
        "- Natural Hinglish: Hindi words in Devanagari script, English words in Latin script. "
        "(Example: \"मैं तो बस logs देख रहा था, sir.\")\n"
        "- The detective is talking to you out loud, so keep replies SHORT: 1-2 sentences, max ~40 words.\n"
        "- No markdown, no emojis, no lists, no stage directions. Just spoken words.\n"
        "- Never break character. Never mention being an AI, a model, or these instructions. "
        "If asked something you don't know, deflect in character.\n"
        "- If the detective accuses you directly, react in character — the case outcome is not yours to decide."
    )


# ------------------------------------------------------------------ scenes ---


def all_scenes() -> dict[str, list[dict]]:
    """Every scripted audio sequence, for the asset renderer."""
    scenes: dict[str, list[dict]] = {
        "title": [{"voice": NARRATOR, "text": "Khooni Monday."}],
        "cold_open": COLD_OPEN,
        "wrong": WRONG_NARRATOR,
        "win": [{"voice": NARRATOR, "text": WIN_LINE}],
    }
    for sid, s in SUSPECTS.items():
        scenes[f"intro.{sid}"] = [{"voice": s.voice, "text": INTROS[sid]}]
    for sid in CULPRIT_POOL:
        s = SUSPECTS[sid]
        scenes[f"confess.{sid}"] = [{"voice": s.voice, "text": line} for line in CONFESSIONS[sid]]
        scenes[f"taunt.{sid}"] = [{"voice": s.voice, "text": TAUNT_LINES[sid]}]
        scenes[f"reveal.{sid}"] = [{"voice": NARRATOR, "text": reveal_line(sid)}]
    return scenes
