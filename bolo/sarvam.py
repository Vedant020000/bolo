"""Sarvam API client — Bulbul V4 Flash (text-to-speech) + Saaras V4 (speech-to-text).

Deliberately zero-dependency (urllib only) so bolo runs anywhere Python does.
"""

from __future__ import annotations

import base64
import io
import json
import os
import time
import urllib.error
import urllib.request
import uuid

BASE = "https://api.sarvam.ai"


class SarvamError(Exception):
    pass


def _post_json(path: str, body: dict, key: str, timeout: float = 60) -> dict:
    raw = json.dumps(body).encode()
    last: Exception | None = None
    for attempt in (0, 1):
        req = urllib.request.Request(BASE + path, data=raw, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("api-subscription-key", key)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode(errors="replace")[:400]
            except Exception:
                pass
            if attempt == 0 and (e.code == 429 or e.code >= 500):
                time.sleep(0.9)
                last = SarvamError(f"Sarvam HTTP {e.code}: {detail}")
                continue
            raise SarvamError(f"Sarvam HTTP {e.code}: {detail}") from None
        except Exception as e:  # timeouts, connection resets
            if attempt == 0:
                time.sleep(0.7)
                last = SarvamError(f"Sarvam request failed: {e}")
                continue
            raise SarvamError(f"Sarvam request failed: {e}") from None
    raise last or SarvamError("Sarvam request failed")


def tts(
    text: str,
    *,
    key: str,
    voice: str | None = None,
    language: str = "en-IN",
    model: str = "bulbul:v4-flash",
    pace: float = 1.0,
    sample_rate: int = 24000,
    timeout: float = 60,
) -> bytes:
    """Synthesize text -> WAV bytes via Bulbul."""
    body = {
        "text": text,
        "language_code": language,
        "model": model,
        "pace": pace,
        "speech_sample_rate": sample_rate,
    }
    if voice:
        body["speaker"] = voice
    data = _post_json("/text-to-speech", body, key, timeout=timeout)
    audios = data.get("audios") or []
    if not audios:
        raise SarvamError(f"Sarvam returned no audio: {str(data)[:200]}")
    return base64.b64decode("".join(audios))


def stt(
    audio_path: str,
    *,
    key: str,
    model: str = "saaras:v4",
    mode: str = "transcribe",
    language: str | None = None,
    timeout: float = 60,
) -> str:
    """Transcribe a short (<=30s) audio file via Saaras. Returns transcript text."""
    boundary = uuid.uuid4().hex
    buf = io.BytesIO()

    def part(name: str, value: str) -> None:
        buf.write(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode()
        )

    part("model", model)
    part("mode", mode)
    if language and language != "auto":
        part("language_code", language)

    fname = os.path.basename(audio_path)
    buf.write(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'
        f"Content-Type: audio/wav\r\n\r\n".encode()
    )
    with open(audio_path, "rb") as f:
        buf.write(f.read())
    buf.write(b"\r\n")
    buf.write(f"--{boundary}--\r\n".encode())

    req = urllib.request.Request(BASE + "/speech-to-text", data=buf.getvalue(), method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("api-subscription-key", key)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode(errors="replace")[:400]
        except Exception:
            pass
        raise SarvamError(f"Sarvam STT HTTP {e.code}: {detail}") from None
    except Exception as e:
        raise SarvamError(f"Sarvam STT failed: {e}") from None
    return (data.get("transcript") or "").strip()


def verify(key: str) -> None:
    """Cheap round-trip to check a key actually works with Bulbul v4 Flash."""
    tts("ok", key=key)


def chat(
    messages: list,
    *,
    key: str,
    model: str = "sarvam-105b-conversations",
    max_tokens: int = 220,
    temperature: float = 0.8,
    timeout: float = 45,
) -> str:
    """Chat completion via Sarvam (sarvam-105b / sarvam-105b-conversations)."""
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "reasoning_effort": None,
    }
    data = _post_json("/v1/chat/completions", body, key, timeout=timeout)
    try:
        return (data["choices"][0]["message"]["content"] or "").strip()
    except Exception:
        raise SarvamError(f"unexpected chat response: {str(data)[:200]}")
