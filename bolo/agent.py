"""Hand a spoken question to an agent (Letta Code headless by default) and get its reply."""

from __future__ import annotations

import json
import subprocess


def ask(prompt: str, cfg: dict, timeout: int = 240) -> str:
    """Run the configured agent command and extract the assistant's reply text."""
    tpl = cfg.get("agent_cmd") or []
    if not any("{prompt}" in part for part in tpl):
        return "bolo: agent_cmd is misconfigured (missing {prompt})."
    cmd = [part.replace("{prompt}", prompt) for part in tpl]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "The agent took too long to answer."
    except FileNotFoundError:
        return f"bolo: command not found: {cmd[0]}"
    text = _extract(r.stdout or "")
    if not text:
        text = _extract(r.stderr or "")
    if not text and r.returncode != 0:
        detail = _error_detail(r.stderr or "")
        if detail:
            return f"The agent run failed: {detail}"
    if not text and (r.stdout or "").strip():
        # non-JSON output — speak it raw, minus obvious noise
        text = (r.stdout or "").strip()
    return text or "I couldn't get an answer from the agent."


def _extract(out: str) -> str:
    """Be liberal: accept text, JSON objects, or JSON lines; find assistant text."""
    out = out.strip()
    if not out:
        return ""
    data = None
    try:
        data = json.loads(out)
    except Exception:
        for line in reversed(out.splitlines()):
            line = line.strip()
            if not line.startswith(("{", "[")):
                continue
            try:
                data = json.loads(line)
                break
            except Exception:
                continue

    if isinstance(data, dict):
        for k in ("response", "text", "assistant_message", "message", "result", "content"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        for k in ("messages", "history"):
            msgs = data.get(k)
            if isinstance(msgs, list):
                text = _from_messages(msgs)
                if text:
                    return text
    elif isinstance(data, list):
        text = _from_messages(data)
        if text:
            return text

    return ""


def _from_messages(msgs: list) -> str:
    for m in reversed(msgs):
        if not isinstance(m, dict) or m.get("role") != "assistant":
            continue
        c = m.get("content")
        if isinstance(c, str) and c.strip():
            return c.strip()
        if isinstance(c, list):
            parts = [
                p.get("text", "")
                for p in c
                if isinstance(p, dict) and p.get("type") == "text"
            ]
            joined = "\n".join(parts).strip()
            if joined:
                return joined
    return ""


def _error_detail(raw: str) -> str:
    """Pull a human-readable reason out of a machine error JSON, if any."""
    try:
        data = json.loads(raw)
    except Exception:
        return ""
    found: list[str] = []

    def walk(o) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                if (
                    k in ("detail", "message", "display_message")
                    and isinstance(v, str)
                    and v.strip()
                ):
                    found.append(v.strip())
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    if not found:
        return ""
    best = max(found, key=len)
    return best if len(best) <= 240 else best[:239] + "…"
