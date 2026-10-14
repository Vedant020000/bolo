"""Khooni Monday — main game loop: typed commands + voice interrogation."""

from __future__ import annotations

import os

from .. import audio, config, sarvam
from . import content, ui
from .engine import Game

ALIASES = {
    "rohan": "rohan",
    "intern": "rohan",
    "priya": "priya",
    "cofounder": "priya",
    "co-founder": "priya",
    "vikram": "vikram",
    "devops": "vikram",
    "dev": "vikram",
    "kamla": "kamla",
    "didi": "kamla",
    "kamla didi": "kamla",
    "chai": "kamla",
    "general": "general",
    "ai": "general",
    "agent": "general",
}


def _find_suspect(text: str) -> str | None:
    low = text.strip().lower()
    if low in ALIASES:
        return ALIASES[low]
    for word in low.replace(",", " ").replace("?", " ").split():
        if word in ALIASES:
            return ALIASES[word]
    return None


def _handle_text(text: str, game: Game, ui) -> tuple[bool, bool]:
    """Returns (handled, should_quit)."""
    low = text.strip().lower()
    if not low:
        return False, False
    if low in ("quit", "exit", "q", "band", "band karo"):
        return True, True
    if low in ("help", "?", "commands"):
        ui.help_screen()
        return True, False
    if low in ("suspects", "list", "case", "case file"):
        ui.casefile(game)
        return True, False
    if low in ("notes", "clues", "clue"):
        ui.notes(game)
        return True, False
    if low.startswith(("talk", "baat", "बात")):
        sid = _find_suspect(low)
        if sid:
            game.select(sid, ui)
        else:
            ui.note("kaun? — rohan / priya / vikram / kamla / general")
        return True, False
    if low.startswith("accuse") or low.startswith("आरोप"):
        sid = _find_suspect(low)
        if not sid:
            ui.note("kisko accuse karna hai? — accuse rohan / priya / vikram / general")
            return True, False
        s = content.SUSPECTS[sid]
        if ui.confirm(f"{s.name} को accuse करना है? ये तुम्हारा एक ही मौका है"):
            game.verdict(sid, ui)
        return True, False
    if low in ALIASES:
        game.select(ALIASES[low], ui)
        return True, False
    return False, False


def _voice_question(cfg: dict, game: Game, ui) -> str | None:
    device = cfg.get("record_device", "default")
    ui.note("🎙 बोलो… (बोलना बंद करते ही अपने आप रुक जाएगा)")
    stats: dict = {}
    path = audio.record_until_silence(device, noise_floor=game.noise_floor, stats=stats)
    ui.note(
        f"mic: level {stats.get('max_rms', '?')} · threshold {stats.get('threshold', '?')} · floor {game.noise_floor}"
    )
    if not path:
        ui.note("कुछ सुना नहीं — फिर try करो")
        return None
    try:
        text = sarvam.stt(path, key=cfg["api_key"], mode=cfg.get("stt_mode", "codemix"))
    except Exception as e:
        ui.note(f"STT fail: {e}")
        return None
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    text = (text or "").strip()
    if not text:
        ui.note("कुछ सुना नहीं")
        return None
    ui.say("You", text, "white")
    return text


def run() -> int:
    cfg = config.load()
    if not cfg.get("api_key"):
        print("bolo: no Sarvam API key — run: bolo key <YOUR_KEY>")
        return 1

    ui.clear()
    ui.banner()

    audio.apply_mic_setup(cfg)
    game = Game()
    ui.note("mic calibrating… (1 second चुप रहो)")
    game.noise_floor = audio.measure_noise(cfg.get("record_device", "default"))
    ui.note(f"noise floor: {game.noise_floor} · device: {cfg.get('record_device', 'default')}")

    try:
        game.play_scene("title", ui)
        game.play_scene("cold_open", ui)
        ui.casefile(game)

        while not game.over:
            try:
                raw = ui.prompt(game.current)
            except (EOFError, KeyboardInterrupt):
                print()
                break

            quit_now = False
            if raw.strip():
                handled, quit_now = _handle_text(raw, game, ui)
                if quit_now:
                    break
                if handled:
                    continue
                question = raw.strip()
            else:
                question = _voice_question(cfg, game, ui) or ""
                if not question:
                    continue
                handled, quit_now = _handle_text(question, game, ui)
                if quit_now:
                    break
                if handled:
                    continue

            # "priya, tum kahan thi?" → switch + ask
            first = question.lower().split()[0].strip(",.") if question.split() else ""
            if first in ALIASES and len(question.split()) > 1:
                game.select(ALIASES[first], ui)
                question = " ".join(question.split()[1:])

            if not game.current:
                ui.note("पहले किसी suspect से बात करो — जैसे: talk vikram")
                continue

            name = content.SUSPECTS[game.current].name
            ui.note(f"…{name} soch raha hai")
            try:
                reply = game.ask(question)
            except Exception as e:
                ui.note(f"reply fail: {e}")
                continue
            if not reply:
                ui.note("(koi jawab nahi aaya)")
                continue
            game.say_live(reply, ui)
    except KeyboardInterrupt:
        print()

    if game.over:
        ui.end_screen(game.won, content.SUSPECTS[game.culprit].name)
    else:
        ui.note("game छोड़ दिया. फिर मिलेंगे, detective.")
    return 0
