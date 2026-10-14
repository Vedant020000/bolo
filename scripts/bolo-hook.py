#!/usr/bin/env python3
"""bolo hook — speaks an agent's reply when voice narration is enabled (`bolo on`).

Works with Letta Code and Claude Code hook dialects:
  - Letta Code Stop event: carries `assistant_message`.
  - Claude Code Stop event: carries `transcript_path`; we read the last
    assistant text from the JSONL transcript.

Contract: never blocks, never fails the turn, always exits 0. Reads hook JSON
from stdin, posts the text to the bolo daemon, returns immediately.
"""

import json
import os
import pathlib
import sys
import time
import urllib.request


def _state_dir() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("XDG_STATE_HOME", pathlib.Path.home() / ".local" / "state")
    ) / "bolo"


def _log(msg: str) -> None:
    try:
        d = _state_dir()
        d.mkdir(parents=True, exist_ok=True)
        p = d / "hook.log"
        if p.exists() and p.stat().st_size > 200_000:
            p.unlink()
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def _state_enabled() -> bool:
    return (_state_dir() / "enabled").exists()


def _flatten(obj) -> str:
    """Tolerate string / dict / list shapes for message content."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        for k in ("content", "text", "message"):
            if k in obj:
                s = _flatten(obj[k])
                if s:
                    return s
    if isinstance(obj, list):
        parts = [_flatten(o) for o in obj]
        return "\n".join(p for p in parts if p)
    return ""


def _last_assistant_from_transcript(path: str) -> str:
    text = ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("type") != "assistant" or rec.get("isSidechain"):
                    continue
                msg = rec.get("message") or {}
                content = msg.get("content")
                flat = _flatten(content)
                if flat.strip():
                    text = flat
    except OSError:
        return ""
    return text.strip()


def main() -> int:
    raw = sys.stdin.read()
    try:
        ev = json.loads(raw)
    except Exception:
        _log("unparseable hook input")
        return 0
    etype = ev.get("event_type") or ev.get("hook_event_name") or "?"
    if not _state_enabled():
        return 0

    text = _flatten(ev.get("assistant_message") or ev.get("last_assistant_message") or "")
    source = "assistant_message"
    if not text and ev.get("transcript_path"):
        text = _last_assistant_from_transcript(str(ev["transcript_path"]))
        source = "transcript"
    text = (text or "").strip()
    if len(text) < 2:
        _log(f"{etype}: fired but no speakable text (keys: {sorted(ev.keys())[:12]})")
        return 0

    port = 47825
    try:
        cfgp = pathlib.Path(
            os.environ.get("XDG_CONFIG_HOME", pathlib.Path.home() / ".config")
        ) / "bolo" / "config.json"
        port = int(json.loads(cfgp.read_text()).get("port", port))
    except Exception:
        pass
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/say",
            data=json.dumps({"text": text, "source": "hook"}).encode(),
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=1.5).read()
        _log(f"{etype}: posted {len(text)} chars via {source}")
    except Exception as e:
        _log(f"{etype}: post failed: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
