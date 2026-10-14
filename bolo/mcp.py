"""bolo MCP server (stdio) — gives ANY MCP-capable agent a voice.

Tools:
  speak(text, voice?, language?)  — say something out loud on this machine
  stop_speaking()                 — stop the current speech immediately
  listen(max_seconds?)            — record the user's voice, return a transcript

Talks to the local bolo daemon; auto-starts it if it isn't running.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

from . import __version__, config

TOOLS = [
    {
        "name": "speak",
        "description": (
            "Speak a short line out loud on the user's speakers (Sarvam Bulbul, installed locally). "
            "This is your voice: say the ONE thing worth hearing — the headline, the result, the question — "
            "instead of your full explanation. Your complete answer stays in text; the spoken line is what "
            "a colleague would say out loud. Keep it to 1-2 conversational sentences. "
            "Optional `voice` selects a persona (e.g. shubh_enhi_companion, sanchita_hi_assistant, "
            "ratan_hi_latenight, sunny_hi_reels); default is the user's configured voice."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to speak aloud."},
                "voice": {"type": "string", "description": "Optional persona id for the voice."},
                "language": {"type": "string", "description": "Optional BCP-47 code (default: auto)."},
            },
            "required": ["text"],
        },
    },
    {
        "name": "stop_speaking",
        "description": "Stop the current speech playback immediately.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "listen",
        "description": (
            "Listen to the user through the microphone: records until they stop speaking "
            "(max ~20 seconds) and returns the transcript (Hinglish-aware). Use when the user says "
            "they will speak, or for hands-free voice input."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "max_seconds": {
                    "type": "integer",
                    "description": "Maximum seconds to listen (default 20).",
                },
            },
        },
    },
]


def _post_once(port: int, path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", data=json.dumps(payload).encode(), method="POST"
    )
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def _post(path: str, payload: dict) -> dict:
    port = int(config.load().get("port", 47825))
    try:
        return _post_once(port, path, payload)
    except Exception:
        # daemon not running — start it and retry once
        try:
            from .cli import ensure_daemon

            ensure_daemon()
        except Exception:
            pass
        return _post_once(port, path, payload)


def _listen(max_seconds: int) -> str:
    from . import audio, sarvam

    cfg = config.load()
    key = cfg.get("api_key") or ""
    if not key:
        return "(bolo: no Sarvam API key configured — run `bolo key <KEY>`)"
    device = cfg.get("record_device", "default")
    noise = audio.measure_noise(device, seconds=0.8)
    path = audio.record_until_silence(
        device, noise_floor=noise, max_s=max(3, min(60, max_seconds))
    )
    if not path:
        return "(heard nothing)"
    try:
        text = sarvam.stt(path, key=key, mode=cfg.get("stt_mode", "codemix"))
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    return text or "(heard nothing)"


def _send(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _reply(mid, result=None, error=None) -> None:
    msg = {"jsonrpc": "2.0", "id": mid}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    _send(msg)


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        mid = msg.get("id")
        method = msg.get("method")

        if method == "initialize":
            params = msg.get("params") or {}
            _reply(
                mid,
                {
                    "protocolVersion": params.get("protocolVersion") or "2025-06-18",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "bolo", "version": __version__},
                },
            )
        elif method == "notifications/initialized":
            pass
        elif method == "ping":
            _reply(mid, {})
        elif method == "tools/list":
            _reply(mid, {"tools": TOOLS})
        elif method == "tools/call":
            params = msg.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            try:
                if name == "speak":
                    _post(
                        "/say",
                        {
                            "text": args.get("text", ""),
                            "voice": args.get("voice"),
                            "language": args.get("language"),
                            "source": "mcp",
                        },
                    )
                    out = "Speaking."
                elif name == "stop_speaking":
                    _post("/stop", {})
                    out = "Stopped."
                elif name == "listen":
                    out = _listen(int(args.get("max_seconds") or 20))
                else:
                    raise ValueError(f"unknown tool: {name}")
                _reply(mid, {"content": [{"type": "text", "text": out}], "isError": False})
            except Exception as e:
                _reply(
                    mid,
                    {"content": [{"type": "text", "text": f"bolo error: {e}"}], "isError": True},
                )
        # other notifications / unknown methods: ignore (no id -> notification)
    return 0
