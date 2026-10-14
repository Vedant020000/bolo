"""bolo configuration — ~/.config/bolo/config.json (0600)."""

from __future__ import annotations

import json
import os
import pathlib

CONFIG_HOME = pathlib.Path(
    os.environ.get("XDG_CONFIG_HOME") or pathlib.Path.home() / ".config"
)
STATE_HOME = pathlib.Path(
    os.environ.get("XDG_STATE_HOME") or pathlib.Path.home() / ".local" / "state"
)

CONFIG_PATH = CONFIG_HOME / "bolo" / "config.json"
STATE_DIR = STATE_HOME / "bolo"

DEFAULTS: dict = {
    # --- Sarvam ---
    "api_key": "",
    "model": "bulbul:v4-flash",
    "voice": "simran_enhi_companion",  # a persona id, or "" to use the API default
    "language": "auto",  # "auto" picks en-IN / hi-IN per segment
    "pace": 1.0,
    "sample_rate": 24000,
    # --- daemon ---
    "port": 47825,
    "max_chars": 800,  # spoken cap for long replies ("...more on screen")
    "interrupt": True,  # new speech interrupts current speech
    # --- listening ---
    "stt_model": "saaras:v4",
    "stt_mode": "codemix",  # transcribe | codemix | translit  (codemix = best for Hinglish)
    "record_device": "default",
    "mic_setup": [],  # shell commands run at startup to fix mic gain (e.g. amixer lines)
    # --- chat mode (hands-free conversation with barge-in) ---
    "chat_barge_in": True,
    "chat_silence_ms": 1100,  # silence that ends one utterance
    "chat_max_utterance_s": 20,
    "speech_floor": 380,  # base mic RMS threshold; auto-calibrated up from room noise
    # --- voice loop -> agent ---
    # {prompt} is replaced with the spoken question. Tested with Letta Code headless.
    "agent_cmd": ["letta", "-p", "{prompt}", "--output-format", "json"],
    "voice_prefix": "[voice mode] Answer in 1-3 short spoken sentences, no markdown or code: ",
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except FileNotFoundError:
        pass
    except Exception:
        pass
    if os.environ.get("SARVAM_API_KEY"):
        cfg["api_key"] = os.environ["SARVAM_API_KEY"]
    return cfg


def save(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(tmp, 0o600)
    tmp.replace(CONFIG_PATH)


# --- narration toggle (checked by hooks) -------------------------------------


def enabled_file() -> pathlib.Path:
    return STATE_DIR / "enabled"


def is_enabled() -> bool:
    return enabled_file().exists()


def set_enabled(value: bool) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if value:
        enabled_file().touch()
    else:
        try:
            enabled_file().unlink()
        except FileNotFoundError:
            pass


def pack_file() -> pathlib.Path:
    return STATE_DIR / "pack"


def get_pack() -> str | None:
    try:
        name = pack_file().read_text().strip()
        return name or None
    except Exception:
        return None


def set_pack(pack: str | None) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if pack:
        pack_file().write_text(pack)
    else:
        try:
            pack_file().unlink()
        except FileNotFoundError:
            pass


def log_path() -> pathlib.Path:
    return STATE_DIR / "daemon.log"


def pid_path() -> pathlib.Path:
    return STATE_DIR / "daemon.pid"
