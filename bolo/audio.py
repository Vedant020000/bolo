"""Playback + recording via pipewire/alsa tools. No Python audio deps."""

from __future__ import annotations

import os
import shlex
import shutil
import signal
import struct
import subprocess
import tempfile
import wave


def rms16(data: bytes) -> int:
    """RMS level of 16-bit little-endian mono PCM."""
    n = len(data) // 2
    if n <= 0:
        return 0
    try:
        vals = struct.unpack(f"<{n}h", data[: n * 2])
    except struct.error:
        return 0
    step = max(1, n // 800)
    vals = vals[::step]
    acc = 0
    for v in vals:
        acc += v * v
    return int((acc / len(vals)) ** 0.5)


def measure_noise(device: str = "default", seconds: float = 1.0) -> int:
    """Median mic RMS while the room is (assumed) quiet."""
    rate = 16000
    frame_bytes = rate * 2 * 100 // 1000
    proc = subprocess.Popen(
        ["arecord", "-q", "-D", device, "-f", "S16_LE", "-r", str(rate), "-c", "1", "-t", "raw"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    vals: list[int] = []
    t = 0
    try:
        while t < seconds * 1000:
            chunk = proc.stdout.read(frame_bytes)
            if not chunk:
                break
            t += 100
            vals.append(rms16(chunk))
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    return int(sorted(vals)[len(vals) // 2]) if vals else 120


def apply_mic_setup(cfg: dict) -> None:
    """Run configured mic-fix commands (e.g. amixer gain) so the mic stays sane."""
    for cmd in cfg.get("mic_setup") or []:
        try:
            subprocess.run(shlex.split(str(cmd)), capture_output=True, timeout=5)
        except Exception:
            pass


def record_until_silence(
    device: str = "default",
    noise_floor: int = 150,
    max_s: int = 25,
    silence_ms: int = 1000,
    speech_floor: int = 380,
    stats: dict | None = None,
) -> str | None:
    """Record from the mic until the speaker stops talking. Returns WAV path or None."""
    rate = 16000
    frame_ms = 100
    frame_bytes = rate * 2 * frame_ms // 1000
    speech_thresh = max(speech_floor, int(noise_floor * 2.0))
    low = max(120, int(noise_floor * 1.4))
    proc = subprocess.Popen(
        ["arecord", "-q", "-D", device, "-f", "S16_LE", "-r", str(rate), "-c", "1", "-t", "raw"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    buf = bytearray()
    pre: list[bytes] = []
    started = False
    sil = 0
    total = 0
    max_rms = 0
    try:
        while total < max_s * 1000:
            chunk = proc.stdout.read(frame_bytes) if proc.stdout else b""
            if not chunk:
                break
            total += frame_ms
            r = rms16(chunk)
            max_rms = max(max_rms, r)
            if not started:
                pre.append(chunk)
                if len(pre) > 3:
                    pre.pop(0)
                if r > speech_thresh:
                    started = True
                    for c in pre:
                        buf.extend(c)
            else:
                buf.extend(chunk)
                if r < low:
                    sil += frame_ms
                    if sil >= silence_ms:
                        break
                else:
                    sil = 0
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    if stats is not None:
        stats["max_rms"] = max_rms
        stats["started"] = started
        stats["threshold"] = speech_thresh
    if not started or len(buf) < rate:
        return None
    path = tempfile.mktemp(prefix="bolo-mic-", suffix=".wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(buf))
    return path


def _player() -> str:
    for p in ("pw-play", "paplay", "aplay"):
        if shutil.which(p):
            return p
    raise RuntimeError("no audio player found (need pw-play, paplay, or aplay)")


def notify(title: str, body: str = "", urgency: str = "normal") -> None:
    if shutil.which("notify-send"):
        try:
            subprocess.Popen(
                ["notify-send", "-a", "bolo", "-u", urgency, title, body],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


class Player:
    """Sequential WAV playback with hard-stop support."""

    def __init__(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="bolo-audio-")
        self.proc: subprocess.Popen | None = None
        self.path: str | None = None

    @property
    def speaking(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def play(self, wav: bytes) -> None:
        self.stop()
        fd, path = tempfile.mkstemp(prefix="bolo-", suffix=".wav", dir=self.tmpdir)
        with os.fdopen(fd, "wb") as f:
            f.write(wav)
        self.path = path
        self.proc = subprocess.Popen(
            [_player(), path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    def wait(self) -> None:
        if self.proc is not None:
            try:
                self.proc.wait()
            except Exception:
                pass

    def stop(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
        if self.path:
            try:
                os.unlink(self.path)
            except OSError:
                pass
        self.proc = None
        self.path = None


class Recorder:
    """Push-to-talk capture via arecord."""

    def __init__(self, device: str = "default") -> None:
        self.device = device
        self.proc: subprocess.Popen | None = None
        self.path: str | None = None

    @property
    def recording(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def start(self) -> None:
        fd, path = tempfile.mkstemp(prefix="bolo-rec-", suffix=".wav")
        os.close(fd)
        self.path = path
        self.proc = subprocess.Popen(
            [
                "arecord", "-q",
                "-D", self.device,
                "-f", "S16_LE",
                "-r", "16000",
                "-c", "1",
                path,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self) -> str | None:
        """Stop recording; return the WAV path."""
        if self.recording:
            self.proc.send_signal(signal.SIGINT)  # arecord finalizes the WAV header
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        path, self.path = self.path, None
        self.proc = None
        return path
