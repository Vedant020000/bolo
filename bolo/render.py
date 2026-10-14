"""Markdown -> speakable text.

This is the difference between a machine that reads your screen out loud
and one that actually talks to you. Code blocks are dropped (not read as
punctuation soup), links keep their labels, paths become words, and long
replies get summarized with "...more on screen".
"""

from __future__ import annotations

import re

_FENCE = re.compile(r"```.*?(?:```|$)", re.S)
_IMG = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_URL = re.compile(r"https?://\S+|www\.\S+")
_TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$", re.M)
_HEAD = re.compile(r"^\s{0,3}#{1,6}\s+", re.M)
_BULLET = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+", re.M)
_CHECKBOX = re.compile(r"\[\s?[xX ]?\s?\]\s*")
_QUOTE = re.compile(r"^\s*>\s?", re.M)
_HR = re.compile(r"^\s*([-*_]\s*){3,}$", re.M)
_STRIKE = re.compile(r"~~(.+?)~~")
_BOLD = re.compile(r"(\*\*|__)(.+?)\1")
_ITAL = re.compile(r"(?<!\w)(\*|_)([^*_]+)\1(?!\w)")
_INLINE_CODE = re.compile(r"`([^`]*)`")
_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\u2190-\u21FF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200B\u200D]"
)
_DIGITS5 = re.compile(r"(?<![\d,])(\d{5,})(?![\d,])")
_PATH = re.compile(r"(?<!\d)(?:~?/[\w.@-]+)+")
_EXT = re.compile(r"\b(\w+)\.(tsx|ts|jsx|js|py|rs|md|toml|json|sh|css|html|ya?ml)\b")
_DEVANAGARI = re.compile(r"[\u0900-\u097F]")


def _clean_path(m: re.Match) -> str:
    s = m.group(0).replace("~", "").replace("/", " ").strip()
    return _EXT.sub(lambda mm: mm.group(1), s)


def to_speech(text: str, max_chars: int = 800) -> str:
    """Convert agent markdown into something a voice should actually say."""
    if not text:
        return ""
    t = text
    t = _FENCE.sub(" ", t)  # never read code blocks aloud
    t = _IMG.sub(" ", t)
    t = _LINK.sub(r"\1", t)
    t = _URL.sub(" ", t)
    t = _TABLE_LINE.sub("", t)
    t = _HEAD.sub("", t)
    t = _CHECKBOX.sub("", t)
    t = _BULLET.sub("", t)
    t = _QUOTE.sub("", t)
    t = _HR.sub("", t)
    t = _STRIKE.sub(r"\1", t)
    t = _BOLD.sub(r"\2", t)
    t = _ITAL.sub(r"\2", t)
    t = _INLINE_CODE.sub(r"\1", t)
    t = _PATH.sub(_clean_path, t)
    t = _EMOJI.sub(" ", t)
    t = _DIGITS5.sub(lambda m: f"{int(m.group(1)):,}", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{2,}", "\n", t)
    t = t.strip()

    if max_chars and len(t) > max_chars:
        cut = t[:max_chars]
        best = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"), cut.rfind("\n"))
        if best > max_chars * 0.5:
            cut = cut[: best + 1]
        t = cut.rstrip() + " ...more on screen."
    return t


def has_devanagari(text: str) -> bool:
    return bool(_DEVANAGARI.search(text))


def lang_for(text: str) -> str:
    """Pick a language code for a text chunk (auto mode)."""
    return "hi-IN" if has_devanagari(text) else "en-IN"


_SENT = re.compile(r"(?<=[.!?…])\s+|\n+")


def split_sentences(text: str, min_len: int = 12) -> list[str]:
    """Split into synthesis-sized chunks so playback can start early."""
    raw = [s.strip() for s in _SENT.split(text) if s.strip()]
    out: list[str] = []
    for s in raw:
        if out and len(s) < min_len:
            out[-1] = out[-1] + " " + s
        else:
            out.append(s)
    return out
