"""bolo CLI — say, ask, chat, play, event, narration toggle, voices, install, daemon."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import time
import urllib.request

from . import __version__, config

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

VOICES = [
    ("simran_enhi_companion", "Simran · Hinglish companion (female) — default"),
    ("shubh_enhi_companion", "Shubh · Hinglish companion (male)"),
    ("ishita_enhi_companion", "Ishita · Hinglish companion (female)"),
    ("sanchita_en_companion", "Sanchita · English companion (female)"),
    ("shubh_en_narration", "Shubh · English narration (male)"),
    ("simran_en_narration", "Simran · English narration (female)"),
    ("neha_en_latenight", "Neha · calm late-night (female)"),
    ("simran_en_conversation", "Simran · English conversation (female)"),
    ("roopa_hi_companion", "Roopa · Hindi companion (female)"),
    ("simran_hi_assistant", "Simran · Hindi assistant (female)"),
    ("sanchita_hi_assistant", "Sanchita · Hindi assistant (female)"),
    ("shubh_hi_customer", "Shubh · Hindi customer (male)"),
]

AUDITION_TEXT = "Hi! This is what I sound like when your agent speaks. Pretty good, right?"


# ------------------------------------------------------------- http helpers ---


def _port() -> int:
    return int(config.load().get("port", 47825))


def _post(path: str, payload: dict | None = None, timeout: float = 5) -> dict:
    req = urllib.request.Request(
        f"http://127.0.0.1:{_port()}{path}",
        data=json.dumps(payload or {}).encode(),
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _get(path: str, timeout: float = 2) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{_port()}{path}", timeout=timeout) as r:
        return json.loads(r.read())


def _running() -> bool:
    try:
        _get("/status", timeout=0.5)
        return True
    except Exception:
        return False


def ensure_daemon() -> bool:
    if _running():
        return True
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    logf = open(config.log_path(), "ab")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    subprocess.Popen(
        [sys.executable, "-m", "bolo", "daemon", "run"],
        stdout=subprocess.DEVNULL,
        stderr=logf,
        start_new_session=True,
        env=env,
        cwd=str(REPO_ROOT),
    )
    for _ in range(60):
        time.sleep(0.25)
        if _running():
            return True
    return False


# ---------------------------------------------------------------- commands ---


def cmd_say(args) -> int:
    text = " ".join(args.text).strip() if args.text else ""
    if not text:
        if sys.stdin.isatty():
            print("usage: bolo say <text>   (or pipe text on stdin)", file=sys.stderr)
            return 2
        text = sys.stdin.read().strip()
    if not text:
        return 2
    if not ensure_daemon():
        print("bolo: daemon failed to start — check ~/.local/state/bolo/daemon.log", file=sys.stderr)
        return 1
    payload = {
        "text": text,
        "voice": args.voice,
        "language": args.lang,
        "pace": args.pace,
        "source": "cli",
    }
    if args.queue:
        payload["interrupt"] = False
    try:
        r = _post("/say", payload)
    except Exception as e:
        print(f"bolo: {e}", file=sys.stderr)
        return 1
    return 0 if r.get("ok") else 1


def cmd_ask(args) -> int:  # noqa: ARG001
    if not ensure_daemon():
        print("bolo: daemon failed to start", file=sys.stderr)
        return 1
    try:
        r = _post("/ask", {})
    except Exception as e:
        print(f"bolo: {e}", file=sys.stderr)
        return 1
    if r.get("state") == "recording":
        print("🎙 recording — run `bolo ask` again to send it to your agent")
    else:
        print("⏳ processing — listen for the reply")
    return 0


def cmd_chat(args) -> int:  # noqa: ARG001
    if not ensure_daemon():
        print("bolo: daemon failed to start", file=sys.stderr)
        return 1
    try:
        r = _post("/chat", {})
    except Exception as e:
        print(f"bolo: {e}", file=sys.stderr)
        return 1
    state = r.get("state")
    if state == "chat":
        print('🎧 chat mode on — just talk. Say "stop" to end.')
    elif state == "error":
        print(f"bolo: {r.get('message')}", file=sys.stderr)
        return 1
    else:
        print("chat mode off")
    return 0


def cmd_stop(args) -> int:  # noqa: ARG001
    try:
        _post("/stop")
    except Exception:
        pass
    return 0


def _speak_confirm(text: str) -> None:
    try:
        if config.load().get("api_key") and ensure_daemon():
            _post("/say", {"text": text, "source": "cli"})
    except Exception:
        pass


def cmd_on(args) -> int:  # noqa: ARG001
    config.set_enabled(True)
    print("narration: on — agents with the bolo hook will speak their replies")
    _speak_confirm("Voice narration is on.")
    return 0


def cmd_off(args) -> int:  # noqa: ARG001
    config.set_enabled(False)
    try:
        _post("/stop")
    except Exception:
        pass
    print("narration: off")
    return 0


def cmd_status(args) -> int:  # noqa: ARG001
    cfg = config.load()
    print(f"bolo {__version__}")
    if _running():
        s = _get("/status")
        print(f"daemon:    running on 127.0.0.1:{_port()}")
        print(f"speaking:  {'yes' if s.get('speaking') else 'no'}")
        print(f"recording: {'yes' if s.get('recording') else 'no'}")
        print(f"chat:      {'on' if s.get('chat') else 'off'}")
        print(f"pack:      {s.get('pack') or 'off'}")
        print(f"queued:    {s.get('queue', 0)}")
    else:
        print("daemon:    not running")
    print(f"narration: {'on' if config.is_enabled() else 'off'} (hooks speak agent replies)")
    print(f"voice:     {cfg.get('voice') or '(API default)'}")
    key = cfg.get("api_key") or ""
    if key:
        print(f"api key:   set ({key[:6]}…)")
    else:
        print("api key:   NOT set — run: bolo key <SARVAM_API_KEY>")
    return 0


def cmd_play(args) -> int:
    from . import characters

    if args.pack == "tour":
        if not ensure_daemon():
            print("bolo: daemon failed to start", file=sys.stderr)
            return 1
        for name, p in characters.PACKS.items():
            _post(
                "/say",
                {
                    "text": p["intro"],
                    "voice": p.get("voice"),
                    "language": p.get("lang", "auto"),
                    "source": "tour",
                    "interrupt": False,
                },
            )
        print("touring all packs — sit back")
        return 0
    if not args.pack or args.pack == "list":
        print("character packs — bolo play <pack>")
        for name, p in characters.PACKS.items():
            print(f"  {name:13s} {p.get('blurb', ''):40s} [{p.get('voice')}]")
        print("\n  off           stop commentating")
        return 0
    if not ensure_daemon():
        print("bolo: daemon failed to start", file=sys.stderr)
        return 1
    try:
        r = _post("/play", {"pack": args.pack})
    except Exception as e:
        print(f"bolo: {e}", file=sys.stderr)
        return 1
    if r.get("state") == "error":
        print(f"bolo: {r.get('message')}", file=sys.stderr)
        return 1
    print(f"pack: {r.get('state')}")
    return 0


def cmd_event(args) -> int:
    detail = " ".join(args.detail).strip() if args.detail else ""
    if not detail and not sys.stdin.isatty():
        detail = sys.stdin.read().strip()
    try:
        r = _post("/event", {"type": args.type, "detail": detail})
    except Exception as e:
        print(f"bolo: {e}", file=sys.stderr)
        return 1
    if not r.get("ok"):
        print(f"bolo: {r.get('reason', 'no pack active')} — try: bolo play cricket", file=sys.stderr)
        return 1
    return 0


def _classify_run(cmd: list[str], rc: int, out: str) -> tuple[str, str]:
    import re

    joined = " ".join(cmd).lower()
    low = out.lower()
    if cmd[:2] == ["git", "commit"]:
        return ("commit", "new commit") if rc == 0 else ("generic", f"git commit failed (exit {rc})")
    is_test = any(k in joined for k in ("test", "pytest", "vitest", "jest", "unittest"))
    is_build = any(k in joined for k in ("build", "make", "compile", "tsc", "cargo", "webpack", "vite"))
    if is_test:
        if rc == 0:
            m = re.search(r"(\d+)\s+passed", low) or re.search(r"ran\s+(\d+)\s+tests?", low)
            return "tests_ok", f"{m.group(1)} tests" if m else "sab tests"
        return "tests_fail", "tests failed"
    if is_build:
        return ("build_ok", "build") if rc == 0 else ("build_fail", "build failed")
    if rc == 0:
        return "generic", f"command pass — {' '.join(cmd[:3])}"
    return "generic", "command failed"


def cmd_run(args) -> int:
    cmd = list(args.command)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print("usage: bolo run -- <command...>", file=sys.stderr)
        return 2
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except FileNotFoundError:
        print(f"bolo: command not found: {cmd[0]}", file=sys.stderr)
        return 127
    lines: list[str] = []
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        lines.append(line)
    rc = proc.wait()
    etype, detail = _classify_run(cmd, rc, "".join(lines[-120:]))
    try:
        _post("/event", {"type": etype, "detail": detail})
    except Exception:
        pass
    return rc


def cmd_voices(args) -> int:
    if args.audition:
        if not ensure_daemon():
            print("bolo: daemon failed to start", file=sys.stderr)
            return 1
        _post(
            "/say",
            {"text": args.text or AUDITION_TEXT, "voice": args.audition, "source": "cli"},
        )
        print(f"auditioning: {args.audition}")
        return 0
    print("bulbul v4 flash personas — audition with: bolo voices --audition <id>")
    for vid, desc in VOICES:
        print(f"  {vid:28s} {desc}")
    print("\nfull catalog: https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/voices")
    return 0


def cmd_key(args) -> int:
    cfg = config.load()
    cfg["api_key"] = args.value.strip()
    config.save(cfg)
    print(f"saved to {config.CONFIG_PATH}")
    from . import sarvam

    try:
        sarvam.verify(cfg["api_key"])
        print("key verified ✓")
    except Exception as e:
        print(f"key check failed: {e}", file=sys.stderr)
        return 1
    if ensure_daemon():
        try:
            _post("/say", {"text": "Your Sarvam key is verified. bolo is alive.", "source": "cli"})
        except Exception:
            pass
    return 0


def cmd_daemon(args) -> int:
    if args.action == "run":
        from .daemon import run

        return run()
    if args.action == "start":
        print("started" if ensure_daemon() else "failed to start")
        return 0 if _running() else 1
    if args.action == "stop":
        if not _running():
            print("not running")
            return 0
        try:
            _post("/stop")
        except Exception:
            pass
        try:
            pid = int(config.pid_path().read_text().strip())
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
        for _ in range(40):
            time.sleep(0.1)
            if not _running():
                print("stopped")
                return 0
        print("still running — check with: bolo status", file=sys.stderr)
        return 1
    if args.action == "status":
        print("running" if _running() else "not running")
        return 0
    if args.action == "logs":
        lp = config.log_path()
        if lp.exists():
            print("\n".join(lp.read_text(errors="replace").splitlines()[-80:]))
        else:
            print("no log yet — start the daemon first")
        return 0
    return 0


def cmd_mcp(args) -> int:  # noqa: ARG001
    from . import mcp

    return mcp.main()


def cmd_mystery(args) -> int:  # noqa: ARG001
    from .mystery.game import run

    return run()


def _install_files() -> pathlib.Path:
    """Copy hook files + write CLI/MCP shims. Returns the share dir."""
    share = pathlib.Path.home() / ".local" / "share" / "bolo"
    share.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / "scripts" / "bolo-hook.py", share / "hook.py")
    shutil.copy2(REPO_ROOT / "scripts" / "codex-notify.py", share / "codex-notify.py")

    bindir = pathlib.Path.home() / ".local" / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    shim = bindir / "bolo"
    shim.write_text(
        "#!/usr/bin/env bash\n"
        f'export PYTHONPATH="{REPO_ROOT}"${{PYTHONPATH:+:$PYTHONPATH}}\n'
        'exec python3 -m bolo "$@"\n'
    )
    shim.chmod(0o755)
    mcp_shim = bindir / "bolo-mcp"
    mcp_shim.write_text(
        "#!/usr/bin/env bash\n"
        f'export PYTHONPATH="{REPO_ROOT}"${{PYTHONPATH:+:$PYTHONPATH}}\n'
        'exec python3 -m bolo mcp\n'
    )
    mcp_shim.chmod(0o755)
    return share


def _sh(ok: bool, label: str, detail: str = "") -> str:
    return f"  {'✓' if ok else '✗'} {label:10s} {detail}".rstrip()


def cmd_setup(args) -> int:
    """Guided onboarding: prereqs → files → harnesses → key → daemon → hello."""
    print()
    print("  bolo setup · one plugin, every agent, a voice")
    print("  ─────────────────────────────────────────────")
    print()

    # 1 · tools
    player = next((p for p in ("pw-play", "paplay", "aplay") if shutil.which(p)), None)
    mic = shutil.which("arecord")
    ok_tools = bool(player and mic)
    print(_sh(ok_tools, "tools", "python3 · " + " · ".join(x for x in (player, mic) if x)))
    if not ok_tools:
        print("     → install pipewire-utils (or pulseaudio-utils) + alsa-utils")

    # 2 · files
    _install_files()
    print(_sh(True, "installed", "~/.local/bin/bolo · bolo-mcp · hook files"))

    # 3 · harnesses (quiet, summarized)
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _install_hooks(["letta", "claude", "codex"])
        _install_mcp()
    wired: list[str] = []
    for ln in buf.getvalue().splitlines():
        low = ln.lower()
        if "skipped" in low or "not found" in low or "not installed" in low:
            continue
        if "added" in low or "wired" in low or "installed" in low:
            label = ln.strip().split(":", 1)[0]
            if label and label not in wired:
                wired.append(label)
    print(_sh(True, "harnesses", " · ".join(wired) if wired else "none found"))

    # 4 · api key
    key = (args.key or config.load().get("api_key") or "").strip()
    if not key:
        try:
            key = input("  Sarvam API key (dashboard.sarvam.ai) > ").strip()
        except (EOFError, KeyboardInterrupt):
            key = ""
    if key:
        cfg = config.load()
        cfg["api_key"] = key
        config.save(cfg)
        from . import sarvam

        try:
            sarvam.verify(key)
            print(_sh(True, "api key", "saved + verified"))
        except Exception as e:
            print(_sh(False, "api key", f"not working: {str(e)[:60]}"))
    else:
        print(_sh(False, "api key", "skipped — run: bolo key <KEY>"))

    # 5 · daemon + hello
    if ensure_daemon():
        print(_sh(True, "daemon", f"127.0.0.1:{_port()}"))
        try:
            _post("/say", {"text": "bolo is ready. अब आपका agent बोल सकता है।", "source": "setup"})
            print(_sh(True, "voice", '"bolo is ready." — did you hear it?'))
        except Exception:
            print(_sh(False, "voice", "couldn't play — check your audio"))
    else:
        print(_sh(False, "daemon", "failed — see ~/.local/state/bolo/daemon.log"))

    print()
    print('  next   bolo say "hello"   ·   bolo chat   ·   bolo voices')
    print("  check  bolo doctor   ·   docs: README.md")
    print()
    return 0


def cmd_doctor(args) -> int:  # noqa: ARG001
    """Health check: tools, shims, key, daemon, harness wiring, mic."""
    cfg = config.load()
    print(f"  bolo doctor · v{__version__}")
    print("  ───────────────────")
    problems = 0

    def check(label: str, ok: bool, detail: str = "", hint: str = "") -> None:
        nonlocal problems
        if not ok:
            problems += 1
        print(_sh(ok, label, detail))
        if not ok and hint:
            print(f"     → {hint}")

    player = next((p for p in ("pw-play", "paplay", "aplay") if shutil.which(p)), None)
    check("player", bool(player), player or "", "install pipewire-utils or alsa-utils")
    check("mic", bool(shutil.which("arecord")), "arecord", "install alsa-utils")
    bolo_shim = pathlib.Path.home() / ".local" / "bin" / "bolo"
    mcp_shim = pathlib.Path.home() / ".local" / "bin" / "bolo-mcp"
    check("shims", bolo_shim.exists() and mcp_shim.exists(), "", "run: bolo setup")
    key = cfg.get("api_key") or ""
    if key:
        from . import sarvam

        try:
            sarvam.verify(key)
            check("api key", True, "verified @ api.sarvam.ai")
        except Exception as e:
            check("api key", False, str(e)[:70], "run: bolo key <NEW_KEY>")
    else:
        check("api key", False, "not set", "run: bolo key <SARVAM_API_KEY>")
    daemon_up = _running()
    check(
        "daemon",
        daemon_up,
        f"127.0.0.1:{_port()}" if daemon_up else "not running",
        "run: bolo daemon start",
    )
    wired = []
    for label, path, needle in (
        ("letta", pathlib.Path.home() / ".letta" / "settings.json", "bolo"),
        ("codex", pathlib.Path.home() / ".codex" / "config.toml", "bolo"),
        ("vscode", pathlib.Path.home() / ".config" / "Code" / "User" / "mcp.json", '"bolo"'),
        ("opencode", pathlib.Path.home() / ".config" / "opencode" / "opencode.json", '"bolo"'),
    ):
        try:
            if needle in path.read_text():
                wired.append(label)
        except Exception:
            pass
    check("harnesses", bool(wired), " · ".join(wired), "run: bolo setup")
    try:
        from . import audio

        floor = audio.measure_noise(cfg.get("record_device", "default"), seconds=0.8)
        check("mic level", True, f"floor {floor}")
    except Exception as e:
        check("mic level", False, str(e)[:60], "")

    print()
    if problems == 0:
        print("  all good — your agents can speak 🎙")
    else:
        print(f"  {problems} issue(s) above — fixes are on the → lines")
    print()
    return 0


def cmd_install(args) -> int:
    _install_files()
    print("  installed  ~/.local/bin/bolo · bolo-mcp · hook files")

    if args.hooks:
        _install_hooks([h.strip() for h in args.hooks.split(",") if h.strip()])
    if getattr(args, "mcp", False):
        _install_mcp()

    print()
    print("  KDE shortcut: System Settings → Shortcuts → Custom → New")
    print("                 Command:  bolo ask        (suggested: Ctrl+Alt+Space)")
    print('  KRunner works too: Alt+Space → "bolo ask"')
    return 0


def _install_hooks(targets) -> None:
    hook_cmd = f"python3 {pathlib.Path.home()}/.local/share/bolo/hook.py"
    if "letta" in targets:
        _merge_stop_hook(pathlib.Path.home() / ".letta" / "settings.json", hook_cmd, "letta")
    if "claude" in targets:
        _merge_stop_hook(pathlib.Path.home() / ".claude" / "settings.json", hook_cmd, "claude")
    if "codex" in targets:
        _install_codex_notify()


def _merge_stop_hook(path: pathlib.Path, hook_cmd: str, label: str) -> None:
    data: dict = {}
    if path.exists():
        try:
            data = json.loads(path.read_text())
        except Exception as e:
            print(f"! could not parse {path}: {e} — skipping {label}", file=sys.stderr)
            return
        backup = path.with_name(path.name + ".bolo-backup")
        if not backup.exists():
            shutil.copy2(path, backup)
            print(f"backup     {backup}")
    hooks = data.setdefault("hooks", {})
    stop = hooks.setdefault("Stop", [])
    for entry in stop:
        try:
            if any("bolo" in (h.get("command") or "") for h in entry.get("hooks", [])):
                print(f"{label}: hook already installed")
                return
        except Exception:
            pass
    stop.append(
        {"hooks": [{"type": "command", "command": hook_cmd, "timeout": 5000, "quiet": True}]}
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"{label}: Stop hook added to {path}")


def _install_codex_notify() -> None:
    import re as _re

    cfgp = pathlib.Path.home() / ".codex" / "config.toml"
    notify_line = (
        f'notify = ["python3", "{pathlib.Path.home()}/.local/share/bolo/codex-notify.py"]'
    )
    if not cfgp.exists():
        print("codex: ~/.codex/config.toml not found — skipping")
        return
    text = cfgp.read_text()
    if "codex-notify.py" in text:
        print("codex: notify already installed")
        return
    backup = cfgp.with_name(cfgp.name + ".bolo-backup")
    if not backup.exists():
        shutil.copy2(cfgp, backup)
        print(f"backup     {backup}")
    if _re.search(r"(?m)^\s*notify\s*=", text):
        text = _re.sub(r"(?m)^\s*notify\s*=.*$", notify_line, text, count=1)
    else:
        text = notify_line + "\n" + text
    cfgp.write_text(text)
    print(f"codex: notify added to {cfgp}")


def _install_mcp() -> None:
    """Register the bolo MCP server in every harness config found on this machine."""
    command = f"{pathlib.Path.home()}/.local/bin/bolo-mcp"
    print("MCP registration:")
    print(
        _merge_json_mcp(
            pathlib.Path.home() / ".config" / "Code" / "User" / "mcp.json",
            "vscode",
            {"type": "stdio", "command": command, "args": []},
            "servers",
        )
    )
    print(
        _merge_json_mcp(
            pathlib.Path.home() / ".cursor" / "mcp.json",
            "cursor",
            {"command": command, "args": []},
            "mcpServers",
        )
    )
    print(
        _merge_json_mcp(
            pathlib.Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
            "claude-desktop",
            {"command": command, "args": []},
            "mcpServers",
        )
    )
    print(
        _merge_json_mcp(
            pathlib.Path.home() / ".config" / "opencode" / "opencode.json",
            "opencode",
            {"type": "local", "command": [command], "enabled": True},
            "mcp",
        )
    )
    print(
        _merge_json_mcp(
            pathlib.Path.home() / ".pi" / "agent" / "mcp.json",
            "pi",
            {"command": command, "args": []},
            "mcpServers",
        )
    )
    print(_merge_codex_toml(pathlib.Path.home() / ".codex" / "config.toml", command))
    claude = shutil.which("claude")
    if claude:
        try:
            r = subprocess.run(
                [claude, "mcp", "add", "bolo", "--scope", "user", "--", command],
                capture_output=True,
                text=True,
                timeout=20,
            )
            ok = r.returncode == 0
            detail = "added" if ok else ((r.stderr or r.stdout).strip().splitlines() or ["?"])[0][:90]
            print(f"  claude-code: {detail}")
        except Exception as e:
            print(f"  claude-code: failed ({e})")
    else:
        print("  claude-code: not installed — skipped (see README for the one-liner)")


def _merge_json_mcp(path: pathlib.Path, label: str, entry: dict, servers_key: str) -> str:
    if not path.exists():
        return f"  {label}: not found — skipped"
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return f"  {label}: can't parse {path} ({e}) — skipped"
    servers = data.setdefault(servers_key, {})
    if "bolo" in servers:
        return f"  {label}: already wired"
    backup = path.with_name(path.name + ".bolo-backup")
    if not backup.exists():
        shutil.copy2(path, backup)
    servers["bolo"] = entry
    path.write_text(json.dumps(data, indent=2) + "\n")
    return f"  {label}: bolo added to {path}"


def _merge_codex_toml(path: pathlib.Path, command: str) -> str:
    if not path.exists():
        return "  codex: not found — skipped"
    text = path.read_text()
    if "mcp_servers.bolo" in text:
        return "  codex: already wired"
    backup = path.with_name(path.name + ".bolo-backup")
    if not backup.exists():
        shutil.copy2(path, backup)
    text = (
        text.rstrip()
        + f'\n\n[mcp_servers.bolo]\ncommand = "{command}"\ndefault_tools_approval_mode = "approve"\n'
    )
    path.write_text(text)
    return f"  codex: bolo added to {path}"


def cmd_config(args) -> int:  # noqa: ARG001
    cfg = config.load()
    print(f"config: {config.CONFIG_PATH}")
    for k in sorted(cfg):
        v = cfg[k]
        if k == "api_key" and v:
            v = v[:6] + "…"
        print(f"  {k}: {v}")
    return 0


# -------------------------------------------------------------------- main ---


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="bolo",
        description="bolo — give any agent a voice (Sarvam Bulbul V4 Flash)",
    )
    p.add_argument("--version", action="version", version=f"bolo {__version__}")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("say", help="speak text aloud")
    sp.add_argument("text", nargs="*")
    sp.add_argument("--voice")
    sp.add_argument("--lang", dest="lang")
    sp.add_argument("--pace", type=float)
    sp.add_argument("--queue", action="store_true", help="queue instead of interrupting")
    sp.set_defaults(func=cmd_say)

    sub.add_parser(
        "ask", help="push-to-talk: toggle recording; your agent's reply is spoken"
    ).set_defaults(func=cmd_ask)
    sub.add_parser(
        "chat", help='hands-free voice conversation with your agent (say "stop" to end)'
    ).set_defaults(func=cmd_chat)
    sub.add_parser("stop", help="stop speaking").set_defaults(func=cmd_stop)
    sub.add_parser("on", help="enable voice narration for agent replies (hooks)").set_defaults(
        func=cmd_on
    )
    sub.add_parser("off", help="disable voice narration").set_defaults(func=cmd_off)
    sub.add_parser("status", help="show status").set_defaults(func=cmd_status)

    pp = sub.add_parser("play", help="character packs: your computer, commentated")
    pp.add_argument("pack", nargs="?", default="list", help="cricket | news | trailer | documentary | dost | hype | maa | tour | off | list")
    pp.set_defaults(func=cmd_play)

    ep = sub.add_parser("event", help="report an event to the active character pack")
    ep.add_argument("type", help="tests_ok | tests_fail | build_ok | build_fail | commit | agent_done | generic")
    ep.add_argument("detail", nargs="*")
    ep.set_defaults(func=cmd_event)

    rp = sub.add_parser("run", help="run a command; the active character pack commentates the result")
    rp.add_argument("command", nargs=argparse.REMAINDER, help="-- <command...>")
    rp.set_defaults(func=cmd_run)

    vp = sub.add_parser("voices", help="list voices; --audition <id> speaks a sample")
    vp.add_argument("--audition")
    vp.add_argument("--text")
    vp.set_defaults(func=cmd_voices)

    kp = sub.add_parser("key", help="set + verify your Sarvam API key")
    kp.add_argument("value")
    kp.set_defaults(func=cmd_key)

    dp = sub.add_parser("daemon", help="manage the bolo daemon")
    dp.add_argument("action", choices=["start", "stop", "run", "status", "logs"])
    dp.set_defaults(func=cmd_daemon)

    sub.add_parser("mcp", help="run the bolo MCP server (stdio)").set_defaults(func=cmd_mcp)

    sub.add_parser(
        "mystery", help="🕵️ Khooni Monday — an AI murder mystery you play by voice"
    ).set_defaults(func=cmd_mystery)

    sp2 = sub.add_parser(
        "setup", help="one-command onboarding: install, wire every harness, verify, say hello"
    )
    sp2.add_argument("--key", default="", help="Sarvam API key (optional; prompts if not set)")
    sp2.set_defaults(func=cmd_setup)

    sub.add_parser(
        "doctor", help="check everything: tools, key, daemon, harnesses, mic"
    ).set_defaults(func=cmd_doctor)

    ip = sub.add_parser("install", help="install shim + hook files (--hooks letta,claude,codex, --mcp)")
    ip.add_argument("--hooks", default="")
    ip.add_argument(
        "--mcp", action="store_true", help="register the bolo MCP server in detected harnesses"
    )
    ip.set_defaults(func=cmd_install)

    sub.add_parser("config", help="show config path + values").set_defaults(func=cmd_config)

    args = p.parse_args(argv)
    if not getattr(args, "cmd", None):
        p.print_help()
        print("\n  new here? run:  bolo setup")
        return 0
    return args.func(args) or 0
