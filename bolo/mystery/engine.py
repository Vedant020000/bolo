"""Khooni Monday — game engine: state, interrogation, verdict, audio."""

from __future__ import annotations

import json
import os
import pathlib
import random
import re

from .. import audio, config, render, sarvam
from . import content

ASSETS_DIR = pathlib.Path(__file__).resolve().parent / "assets"

CLUE_KEYS = {
    "trophy (हथियार)": ["trophy", "ट्रॉफ़ी", "ट्रॉफी", "हथियार"],
    "door log (9:12 / 9:41)": ["door", "log", "दरवाज़ा", "9:12", "9:41"],
    "slack message (9:44)": ["slack", "message", "deploy"],
    "staging force-push": ["staging", "branch", "push"],
    "alibis": ["alibi", "कहाँ", "kahan"],
}


def clean_reply(t: str) -> str:
    t = re.sub(r"\([^)]*\)", "", t)
    t = re.sub(r"[*_#`]+", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


class Assets:
    """Pre-rendered audio for scripted scenes (falls back to live TTS)."""

    def __init__(self):
        try:
            self.manifest = json.loads((ASSETS_DIR / "manifest.json").read_text())
        except Exception:
            self.manifest = {}

    def lines(self, scene: str):
        spec = content.all_scenes().get(scene, [])
        clips = self.manifest.get(scene, [])
        out = []
        for i, line in enumerate(spec):
            path = None
            if i < len(clips):
                p = ASSETS_DIR / clips[i]
                if p.exists():
                    path = p
            out.append((line, path))
        return out


class Game:
    def __init__(self):
        self.cfg = config.load()
        self.assets = Assets()
        forced = os.environ.get("BOLO_CULPRIT", "").strip()
        if forced in content.CULPRIT_POOL:
            self.culprit = forced
        else:
            self.culprit = random.choice(content.CULPRIT_POOL)
        self.history: dict[str, list[dict]] = {sid: [] for sid in content.SUSPECTS}
        self.current: str | None = None
        self.intros_done: set[str] = set()
        self.clues: list[str] = []
        self.player = audio.Player()
        self.noise_floor = 120
        self.over = False
        self.won = False

    # ---------------------------------------------------------- playback ---

    def _speak(self, text: str, voice: str, ui, who: str, color: str) -> None:
        ui.say(who, text, color)
        try:
            wav = sarvam.tts(
                text, key=self.cfg["api_key"], voice=voice, language=render.lang_for(text)
            )
        except Exception as e:
            ui.note(f"(audio unavailable: {e})")
            return
        self.player.play(wav)
        self.player.wait()

    def play_scene(self, scene: str, ui) -> None:
        sid = scene.split(".", 1)[1] if "." in scene else None
        s = content.SUSPECTS.get(sid) if sid else None
        color = s.color if s else "dim"
        who = s.name if s else "NARRATOR"
        for line, path in self.assets.lines(scene):
            if path is not None:
                ui.say(who, line["text"], color)
                self.player.play(path.read_bytes())
                self.player.wait()
            else:
                self._speak(line["text"], line["voice"], ui, who, color)

    def say_live(self, text: str, ui) -> None:
        s = content.SUSPECTS[self.current]
        self._speak(text, s.voice, ui, s.name, s.color)

    # ------------------------------------------------------- interrogation ---

    def select(self, sid: str, ui) -> None:
        self.current = sid
        s = content.SUSPECTS[sid]
        if sid not in self.intros_done:
            self.intros_done.add(sid)
            self.play_scene(f"intro.{sid}", ui)
        else:
            ui.note(f"({s.name} फिर सामने आ गया/गई)")

    def ask(self, question: str) -> str:
        sid = self.current
        s = content.SUSPECTS[sid]
        msgs = [{"role": "system", "content": content.system_prompt(s, sid == self.culprit)}]
        msgs += self.history[sid][-10:]
        msgs.append({"role": "user", "content": question})
        reply = sarvam.chat(
            msgs,
            key=self.cfg["api_key"],
            model=self.cfg.get("mystery_model", "sarvam-105b-conversations"),
        )
        reply = clean_reply(reply)
        self.history[sid] += [
            {"role": "user", "content": question},
            {"role": "assistant", "content": reply},
        ]
        self._track_clues(question)
        return reply

    def _track_clues(self, q: str) -> None:
        low = q.lower()
        for label, keys in CLUE_KEYS.items():
            if any(k in low for k in keys) and label not in self.clues:
                self.clues.append(label)

    # ------------------------------------------------------------ verdict ---

    def verdict(self, sid: str, ui) -> None:
        self.over = True
        if sid == self.culprit:
            self.won = True
            self.play_scene(f"confess.{sid}", ui)
            self.play_scene("win", ui)
        else:
            self.play_scene("wrong", ui)
            self.play_scene(f"taunt.{self.culprit}", ui)
            self.play_scene(f"reveal.{self.culprit}", ui)
