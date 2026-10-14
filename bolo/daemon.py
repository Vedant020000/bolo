"""bolo daemon — the voice service. One local process that speaks and listens.

Control plane: HTTP on 127.0.0.1:<port>.

  POST /say    {text, voice?, language?, pace?, interrupt?}   queue speech, return instantly
  POST /stop   cancel everything currently speaking/queued
  POST /ask    toggle push-to-talk: record -> transcribe -> your agent -> speak the reply
  POST /chat   toggle hands-free conversation mode (with barge-in)
  POST /play   {pack} activate a character pack (cricket, news, trailer, documentary, dost, hype)
  POST /event  {type, detail} report an event to the active character pack
  POST /reload reload config
  GET  /status
"""

from __future__ import annotations

import json
import os
import queue
import signal
import subprocess
import tempfile
import threading
import time
import wave
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__, audio, characters, config, render, sarvam
from . import agent as agent_mod

RATE = 16000
FRAME_MS = 100
FRAME_BYTES = RATE * 2 * FRAME_MS // 1000  # 16-bit mono, 100ms

STOP_PHRASES = {
    "stop",
    "stop listening",
    "stop chat",
    "bye",
    "goodbye",
    "exit",
    "quit",
    "band karo",
    "bas",
    "बस",
    "रुको",
    "स्टॉप",
    "बंद करो",
}


def log(msg: str) -> None:
    line = f"[bolo {time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        config.STATE_DIR.mkdir(parents=True, exist_ok=True)
        lp = config.log_path()
        if lp.exists() and lp.stat().st_size > 1_000_000:
            lp.unlink()
        with open(lp, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


class Job:
    __slots__ = ("text", "voice", "lang", "pace", "source")

    def __init__(self, text, voice=None, language=None, pace=None, source="api"):
        self.text = text
        self.voice = voice
        self.lang = language
        self.pace = pace
        self.source = source


class Daemon:
    def __init__(self):
        self.cfg = config.load()
        self.player = audio.Player()
        self.recorder = audio.Recorder(self.cfg.get("record_device", "default"))
        self.q: queue.Queue[Job] = queue.Queue()
        self.pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="bolo-synth")
        self.epoch = 0
        self.chat_active = False
        self.noise_floor = 120
        self.echo_floor = 0
        self._pending: str | None = None
        self.pack = config.get_pack()
        threading.Thread(target=self._worker, daemon=True, name="bolo-speak").start()

    # ------------------------------------------------------------- speech ---

    def say(self, job: Job, interrupt: bool = True) -> None:
        if interrupt and self.cfg.get("interrupt", True):
            self.cancel()
        self.q.put(job)

    def cancel(self) -> None:
        self.epoch += 1
        while True:
            try:
                self.q.get_nowait()
            except queue.Empty:
                break
        self.player.stop()

    def _worker(self) -> None:
        while True:
            job = self.q.get()
            try:
                self._speak(job)
            except Exception as e:
                log(f"say failed: {e}")

    def _speak(self, job: Job) -> None:
        cfg = config.load()
        self.cfg = cfg
        speech = render.to_speech(job.text, max_chars=int(cfg.get("max_chars", 800)))
        if not speech:
            log("nothing speakable in text")
            return
        if not cfg.get("api_key"):
            log("no api_key — set one with: bolo key <SARVAM_API_KEY>")
            audio.notify("bolo", "No Sarvam API key yet. Run: bolo key <SARVAM_API_KEY>")
            return

        sentences = render.split_sentences(speech)
        lang = job.lang or cfg.get("language") or "auto"
        voice = job.voice if job.voice is not None else cfg.get("voice")
        pace = job.pace if job.pace is not None else cfg.get("pace", 1.0)
        epoch = self.epoch
        log(f"speak ({len(sentences)} chunk(s), voice={voice or 'default'}): {speech[:90]!r}")

        fut = self.pool.submit(self._synth, sentences[0], cfg, voice, lang, pace)
        for i, s in enumerate(sentences):
            if epoch != self.epoch:
                return
            try:
                wav = fut.result()
            except Exception as e:
                log(f"synth failed for {s[:40]!r}: {e}")
                if i + 1 < len(sentences):
                    fut = self.pool.submit(self._synth, sentences[i + 1], cfg, voice, lang, pace)
                continue
            if epoch != self.epoch:
                return
            if i + 1 < len(sentences):  # prefetch the next chunk while this one plays
                fut = self.pool.submit(self._synth, sentences[i + 1], cfg, voice, lang, pace)
            self.player.play(wav)
            self.player.wait()

    def _synth(self, text: str, cfg: dict, voice, lang, pace) -> bytes:
        language = render.lang_for(text) if lang in (None, "", "auto") else lang
        return sarvam.tts(
            text,
            key=cfg["api_key"],
            voice=voice or None,
            language=language,
            model=cfg.get("model", "bulbul:v4-flash"),
            pace=pace,
            sample_rate=int(cfg.get("sample_rate", 24000)),
        )

    # ----------------------------------------------------------- listening ---

    def ask_toggle(self) -> dict:
        if self.recorder.recording:
            path = self.recorder.stop()
            audio.notify("bolo", "got it — thinking…")
            threading.Thread(target=self._answer, args=(path,), daemon=True).start()
            return {"state": "processing"}
        self.cfg = config.load()
        self.recorder = audio.Recorder(self.cfg.get("record_device", "default"))
        self.recorder.start()
        audio.notify("bolo 🎙", "Listening — run `bolo ask` again to send it")
        return {"state": "recording"}

    def _answer(self, wav_path: str | None) -> None:
        cfg = config.load()
        self.cfg = cfg
        try:
            if not wav_path:
                audio.notify("bolo", "recording failed")
                return
            if not cfg.get("api_key"):
                audio.notify("bolo", "No Sarvam API key yet.")
                return
            text = self._transcribe(wav_path, cfg)
            log(f"heard: {text!r}")
            if not text:
                audio.notify("bolo", "I heard nothing.")
                return
            audio.notify("bolo", f"“{text[:70]}”")
            reply = agent_mod.ask(str(cfg.get("voice_prefix", "")) + text, cfg)
            log(f"agent reply: {reply[:120]!r}")
            self.say(Job(reply, source="voice"), interrupt=True)
        except Exception as e:
            log(f"ask failed: {e}")
            audio.notify("bolo", f"ask failed: {e}")
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass

    def _transcribe(self, wav_path: str, cfg: dict) -> str:
        return sarvam.stt(
            wav_path,
            key=cfg["api_key"],
            model=cfg.get("stt_model", "saaras:v4"),
            mode=cfg.get("stt_mode", "codemix"),
        )

    # ---------------------------------------------------- character packs ---

    def play_pack(self, pack: str | None) -> dict:
        if not pack or pack == "off":
            self.pack = None
            config.set_pack(None)
            return {"state": "off"}
        if characters.get(pack) is None:
            return {"state": "error", "message": f"unknown pack: {pack}"}
        self.pack = pack
        config.set_pack(pack)
        intro = characters.intro(pack)
        if intro:
            self.say(
                Job(intro["text"], voice=intro["voice"], language=intro["lang"], source="pack"),
                interrupt=True,
            )
        return {"state": pack}

    def commentate(self, etype: str, detail: str) -> dict:
        if not self.pack:
            return {"ok": False, "reason": "no pack active"}
        line = characters.line_for(self.pack, etype or "generic", (detail or "").strip())
        if not line:
            return {"ok": False, "reason": "no line for that event"}
        self.say(
            Job(line["text"], voice=line["voice"], language=line["lang"], source="event"),
            interrupt=True,
        )
        return {"ok": True, "text": line["text"]}

    # --------------------------------------------------------- chat mode ---

    def chat_toggle(self) -> dict:
        if self.chat_active:
            self.chat_active = False
            self.player.stop()
            audio.notify("bolo", "chat mode off")
            return {"state": "idle"}
        self.cfg = config.load()
        if not self.cfg.get("api_key"):
            audio.notify("bolo", "No Sarvam API key yet.")
            return {"state": "error", "message": "no api key"}
        self.chat_active = True
        self._pending = None
        threading.Thread(target=self._chat_loop, daemon=True, name="bolo-chat").start()
        audio.notify("bolo 🎧", 'chat mode on — just talk. Say "stop" to end.')
        return {"state": "chat"}

    def _chat_loop(self) -> None:
        try:
            self._calibrate()
            log(f"chat: noise floor {self.noise_floor}")
            while self.chat_active:
                try:
                    cfg = config.load()
                    self.cfg = cfg
                    path = self._pending
                    self._pending = None
                    if not path:
                        path = self._capture_utterance()
                    if not self.chat_active:
                        return
                    if not path:
                        continue
                    try:
                        text = self._transcribe(path, cfg)
                    finally:
                        try:
                            os.unlink(path)
                        except OSError:
                            pass
                    text = text.strip()
                    log(f"chat heard: {text!r}")
                    if not text:
                        continue
                    if text.lower().strip(" .!?,") in STOP_PHRASES:
                        self._speak_chat(Job("Okay — chat mode off.", source="chat"))
                        return
                    audio.notify("bolo", f"“{text[:70]}”")
                    reply = agent_mod.ask(str(cfg.get("voice_prefix", "")) + text, cfg)
                    log(f"chat reply: {reply[:120]!r}")
                    barge = self._speak_chat(Job(reply, source="chat"))
                    if barge:
                        self._pending = barge  # user interrupted — treat as next question
                except Exception as e:
                    log(f"chat: error: {e}")
                    time.sleep(0.4)
        finally:
            self.chat_active = False
            log("chat: ended")

    def _mic_stream(self) -> subprocess.Popen:
        device = str(self.cfg.get("record_device", "default"))
        return subprocess.Popen(
            ["arecord", "-q", "-D", device, "-f", "S16_LE", "-r", str(RATE), "-c", "1", "-t", "raw"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

    def _close_stream(self, proc: subprocess.Popen) -> None:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def _write_wav(self, pcm: bytes) -> str:
        path = tempfile.mktemp(prefix="bolo-chat-", suffix=".wav")
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(pcm)
        return path

    def _calibrate(self, seconds: float = 1.2) -> None:
        proc = self._mic_stream()
        vals: list[int] = []
        t = 0
        try:
            while t < seconds * 1000:
                chunk = proc.stdout.read(FRAME_BYTES)
                if not chunk:
                    break
                t += FRAME_MS
                vals.append(audio.rms16(chunk))
        finally:
            self._close_stream(proc)
        self.noise_floor = int(sorted(vals)[len(vals) // 2]) if vals else 120
        self.echo_floor = 0

    def _thresholds(self) -> tuple[int, int]:
        cfg = self.cfg
        floor = int(cfg.get("speech_floor", 380))
        speech = max(floor, self.noise_floor * 3)
        low = max(150, self.noise_floor * 2)
        return speech, low

    def _capture_utterance(self, max_s: int | None = None) -> str | None:
        """Record until end of speech after a start. Returns WAV path or None."""
        cfg = self.cfg
        max_s = max_s or int(cfg.get("chat_max_utterance_s", 20))
        silence_needed = int(cfg.get("chat_silence_ms", 1100))
        speech_thresh, low = self._thresholds()
        proc = self._mic_stream()
        buf = bytearray()
        pre: deque[bytes] = deque(maxlen=3)
        started = False
        sil = 0
        total = 0
        try:
            while total < max_s * 1000:
                if not self.chat_active:
                    break
                chunk = proc.stdout.read(FRAME_BYTES) if proc.stdout else b""
                if not chunk:
                    break
                total += FRAME_MS
                if self.player.speaking:  # ignore our own playback
                    continue
                r = audio.rms16(chunk)
                if not started:
                    pre.append(chunk)
                    if r > speech_thresh:
                        started = True
                        for c in pre:
                            buf.extend(c)
                else:
                    buf.extend(chunk)
                    if r < low:
                        sil += FRAME_MS
                        if sil >= silence_needed:
                            break
                    else:
                        sil = 0
        finally:
            self._close_stream(proc)
        if not started or len(buf) < RATE:
            return None
        return self._write_wav(bytes(buf))

    def _finish_capture(self, mic: subprocess.Popen, captured: bytearray) -> str | None:
        _, low = self._thresholds()
        sil = 0
        total = 0
        while total < 15000:
            chunk = mic.stdout.read(FRAME_BYTES) if mic.stdout else b""
            if not chunk:
                break
            total += FRAME_MS
            captured.extend(chunk)
            if audio.rms16(chunk) < low:
                sil += FRAME_MS
                if sil >= 900:
                    break
            else:
                sil = 0
        if len(captured) < RATE:
            return None
        return self._write_wav(bytes(captured))

    def _speak_chat(self, job: Job) -> str | None:
        """Speak with barge-in. Returns WAV path of a user interruption, if any."""
        cfg = config.load()
        self.cfg = cfg
        speech = render.to_speech(job.text, max_chars=int(cfg.get("max_chars", 800)))
        if not speech:
            return None
        if not cfg.get("api_key"):
            audio.notify("bolo", "No Sarvam API key yet.")
            return None
        if not cfg.get("chat_barge_in", True):
            self._speak(job)
            return None

        sentences = render.split_sentences(speech)
        lang = job.lang or cfg.get("language") or "auto"
        voice = job.voice if job.voice is not None else cfg.get("voice")
        pace = job.pace if job.pace is not None else cfg.get("pace", 1.0)
        epoch = self.epoch
        log(f"chat speak ({len(sentences)} chunk(s)): {speech[:90]!r}")

        fut = self.pool.submit(self._synth, sentences[0], cfg, voice, lang, pace)
        mic = self._mic_stream()
        speech_thresh, _ = self._thresholds()
        barge_thresh = max(speech_thresh * 2, int(self.echo_floor * 2.8))
        try:
            for i, s in enumerate(sentences):
                if epoch != self.epoch or not self.chat_active:
                    return None
                try:
                    wav = fut.result()
                except Exception as e:
                    log(f"chat synth failed for {s[:40]!r}: {e}")
                    if i + 1 < len(sentences):
                        fut = self.pool.submit(self._synth, sentences[i + 1], cfg, voice, lang, pace)
                    continue
                if i + 1 < len(sentences):
                    fut = self.pool.submit(self._synth, sentences[i + 1], cfg, voice, lang, pace)
                self.player.play(wav)

                hit = 0
                caps: bytearray | None = None
                sil = 0
                warm = 0
                while self.player.speaking:
                    if not self.chat_active:
                        self.player.stop()
                        return None
                    chunk = mic.stdout.read(FRAME_BYTES) if mic.stdout else b""
                    if not chunk:
                        break
                    r = audio.rms16(chunk)
                    if caps is None:
                        # learn our own echo level during the first frames
                        if warm < 6:
                            warm += 1
                            self.echo_floor = max(self.echo_floor, r)
                            barge_thresh = max(
                                speech_thresh * 2, int(self.echo_floor * 2.8)
                            )
                            continue
                        if r > barge_thresh:
                            hit += 1
                            if hit >= 3:  # ~300ms sustained speech
                                self.player.stop()
                                caps = bytearray(chunk)
                        else:
                            hit = 0
                    else:
                        caps.extend(chunk)
                        if r < max(150, self.noise_floor * 2):
                            sil += FRAME_MS
                            if sil >= 900:
                                break
                        else:
                            sil = 0
                if caps is not None:
                    log("chat: barge-in detected")
                    return self._finish_capture(mic, caps)
            return None
        finally:
            self._close_stream(mic)


class Handler(BaseHTTPRequestHandler):
    daemon: "Daemon"

    def log_message(self, fmt, *args):  # quiet
        pass

    def _send(self, obj, code: int = 200) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path == "/status":
            d = self.daemon
            self._send(
                {
                    "ok": True,
                    "speaking": d.player.speaking,
                    "recording": d.recorder.recording,
                    "chat": d.chat_active,
                    "pack": d.pack,
                    "queue": d.q.qsize(),
                    "enabled": config.is_enabled(),
                    "version": __version__,
                }
            )
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):  # noqa: N802
        try:
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b"{}"
            try:
                body = json.loads(raw or b"{}")
            except Exception:
                body = {}
            d = self.daemon
            if self.path == "/say":
                text = (body.get("text") or "").strip()
                if not text:
                    self._send({"error": "empty text"}, 400)
                    return
                d.say(
                    Job(
                        text,
                        voice=body.get("voice"),
                        language=body.get("language"),
                        pace=body.get("pace"),
                        source=body.get("source") or "api",
                    ),
                    interrupt=bool(body.get("interrupt", True)),
                )
                self._send({"ok": True})
            elif self.path == "/stop":
                d.cancel()
                self._send({"ok": True})
            elif self.path == "/ask":
                self._send({"ok": True, **d.ask_toggle()})
            elif self.path == "/chat":
                self._send({"ok": True, **d.chat_toggle()})
            elif self.path == "/play":
                self._send({"ok": True, **d.play_pack(body.get("pack"))})
            elif self.path == "/event":
                self._send(
                    {"ok": True, **d.commentate(body.get("type") or "generic", body.get("detail") or "")}
                )
            elif self.path == "/reload":
                d.cfg = config.load()
                self._send({"ok": True})
            else:
                self._send({"error": "not found"}, 404)
        except Exception as e:
            log(f"http error: {e}")
            try:
                self._send({"error": str(e)}, 500)
            except Exception:
                pass


def run() -> int:
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    cfg = config.load()
    audio.apply_mic_setup(cfg)
    port = int(cfg.get("port", 47825))
    daemon = Daemon()
    Handler.daemon = daemon
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as e:
        log(f"cannot bind 127.0.0.1:{port}: {e}")
        return 1

    def _shutdown(signum, frame):  # noqa: ARG001
        log("shutting down")
        daemon.chat_active = False
        daemon.cancel()
        threading.Thread(target=srv.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    config.pid_path().write_text(str(os.getpid()))
    log(f"daemon listening on 127.0.0.1:{port} (pid {os.getpid()})")
    try:
        srv.serve_forever()
    finally:
        try:
            config.pid_path().unlink()
        except OSError:
            pass
    return 0
