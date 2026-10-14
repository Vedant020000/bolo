#!/usr/bin/env python3
"""bolo adapter for Codex CLI.

Codex runs the `notify` program (from ~/.codex/config.toml) when an agent turn
completes, passing a JSON payload as the final argv argument. We extract the
assistant's message and post it to the bolo daemon when narration is enabled.

Never blocks, never fails the turn, always exits 0.
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
            f.write(f"[{time.strftime('%m-%d %H:%M:%S')}] codex: {msg}\n")
    except Exception:
        pass


def _flatten(obj) -> str:
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


def main() -> int:
    if len(sys.argv) < 2:
        _log("no payload argument")
        return 0
    raw = sys.argv[-1]
    try:
        ev = json.loads(raw)
    except Exception:
        _log(f"unparseable payload: {raw[:120]!r}")
        return 0
    if not (_state_dir() / "enabled").exists():
        return 0

    text = ""
    for key in ("last-assistant-message", "last_assistant_message", "message", "text"):
        v = ev.get(key)
        if v:
            text = _flatten(v)
            if text:
                break
    text = (text or "").strip()
    if len(text) < 2:
        _log(f"no speakable text (keys: {sorted(ev.keys())[:10]})")
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
            data=json.dumps({"text": text, "source": "codex"}).encode(),
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=1.5).read()
        _log(f"posted {len(text)} chars (type={ev.get('type')})")
    except Exception as e:
        _log(f"post failed: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
