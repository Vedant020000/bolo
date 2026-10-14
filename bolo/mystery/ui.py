"""Terminal UI for Khooni Monday — noir, minimal, captioned."""

from __future__ import annotations

import textwrap

C = {
    "reset": "\033[0m",
    "dim": "\033[2m",
    "bold": "\033[1m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "magenta": "\033[35m",
    "white": "\033[97m",
    "bred": "\033[91m",
}


def _c(text: str, *names: str) -> str:
    return "".join(C.get(n, "") for n in names) + text + C["reset"]


def clear() -> None:
    print("\033[2J\033[H", end="", flush=True)


_ART = {
    "K": ["██╗  ██╗", "██║ ██╔╝", "█████╔╝ ", "██╔═██╗ ", "██║  ██╗", "╚═╝  ╚═╝"],
    "H": ["██╗  ██╗", "██║  ██║", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "O": [" ██████╗ ", "██╔═══██╗", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    "N": ["███╗   ██╗", "████╗  ██║", "██╔██╗ ██║", "██║╚██╗██║", "██║ ╚████║", "╚═╝  ╚═══╝"],
    "I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
    "M": ["███╗   ███╗", "████╗ ████║", "██╔████╔██║", "██║╚██╔╝██║", "██║ ╚═╝ ██║", "╚═╝     ╚═╝"],
    "D": ["██████╗ ", "██╔══██╗", "██║  ██║", "██║  ██║", "██████╔╝", "╚═════╝ "],
    "A": [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "Y": ["██╗   ██╗", "╚██╗ ██╔╝", " ╚████╔╝ ", "  ╚██╔╝  ", "   ██║   ", "   ╚═╝   "],
}


def _word(word: str, sep: str = " ") -> list[str]:
    return [sep.join(_ART[ch][i] for ch in word) for i in range(6)]


def banner() -> None:
    print()
    for row in _word("KHOONI"):
        print("  " + _c(row, "bred", "bold"))
    for row in _word("MONDAY"):
        print("  " + _c(row, "red"))
    print()
    print(_c("  एक AI murder mystery · आवाज़ से खेलो · ChaiStack, Mumbai", "dim"))
    print(_c("  एक कातिल · पाँच झूठ · तुम्हारी आवाज़ ही तुम्हारा हथियार है", "dim"))
    print()


def say(who: str, text: str, color: str = "white") -> None:
    name = _c(f"{who}:", color, "bold")
    wrapped = textwrap.fill(text, width=86, subsequent_indent=" " * (len(who) + 4))
    print(f"  {name} {wrapped}", flush=True)


def note(text: str) -> None:
    print(_c(f"  · {text}", "dim"), flush=True)


def casefile(game) -> None:
    print(_c("  ── CASE FILE ──────────────────────────────────────────────", "dim"))
    print(_c("  Victim:  ", "dim") + "Arjun Mehta, CTO — ChaiStack (Andheri East)")
    print(_c("  Found:   ", "dim") + "server room, Tuesday morning · death ~Monday 9:15–9:30 PM")
    print(_c("  Weapon:  ", "dim") + "\"Best Deploy\" trophy (wiped clean)")
    print(_c("  Door:    ", "dim") + "server room opened 9:12 PM and 9:41 PM")
    print(_c("  Strange: ", "dim") + "\"deploy कर दिया\" sent from Arjun's laptop at 9:44 PM — after he died")
    print()
    print(_c("  ── SUSPECTS ───────────────────────────────────────────────", "dim"))
    for sid, s in game.SUSPECTS.items() if hasattr(game, "SUSPECTS") else _suspects(game):
        mark = "▸" if sid == game.current else " "
        print(
            f"  {_c(mark, 'bred')} {_c(s.name.ljust(11), s.color, 'bold')} "
            f"{_c(s.role.ljust(20), 'dim')} {s.blurb}"
        )
    print()
    note("commands: talk <name> · <type a question> · [Enter] to speak · accuse <name> · notes · help")
    print()


def _suspects(game):
    from . import content

    return content.SUSPECTS.items()


def notes(game) -> None:
    if game.clues:
        note("जो अब तक पता चला: " + " · ".join(game.clues))
    else:
        note("अभी तक कोई clue नहीं — सवाल पूछो: trophy, door log, slack, staging…")


def help_screen() -> None:
    print(_c("  ── HELP ───────────────────────────────────────────────────", "dim"))
    for line in [
        "talk <name>      — किसी suspect से बात करो (rohan, priya, vikram, kamla, general)",
        "<question>       — टाइप करके सवाल पूछो (current suspect से)",
        "[Enter]          — 🎙 बोलकर सवाल पूछो (बोलना बंद करो, अपने आप रुक जाएगा)",
        "accuse <name>    — आरोप लगाओ (एक ही मौका!)",
        "notes            — अब तक के clues",
        "suspects         — case file दोबारा देखो",
        "quit             — खेल छोड़ो",
    ]:
        print(f"  {line}")
    print()


def prompt(current: str | None) -> str:
    label = f"[{current}] " if current else ""
    return input(_c(f"  {label}🧐 > ", "bred"))


def confirm(question: str) -> bool:
    ans = input(_c(f"  {question} (haan/nahi) > ", "yellow")).strip().lower()
    return ans in ("haan", "ha", "y", "yes", "हाँ", "हां")


def end_screen(won: bool, culprit_name: str) -> None:
    print()
    if won:
        print(_c("  ╔══════════════════════════════════╗", "green"))
        print(_c("  ║        CASE  CLOSED  ✓           ║", "green", "bold"))
        print(_c("  ╚══════════════════════════════════╝", "green"))
        print(_c(f"  {culprit_name} was the murderer. ChaiStack can sleep again.", "dim"))
    else:
        print(_c("  ╔══════════════════════════════════╗", "bred"))
        print(_c("  ║     THE KILLER WALKED FREE       ║", "bred", "bold"))
        print(_c("  ╚══════════════════════════════════╝", "bred"))
        print(_c(f"  असली कातिल: {culprit_name}. अगली बार, detective.", "dim"))
    print()
