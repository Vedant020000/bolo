# bolo — give any agent a voice

**One plugin. Any agent. It speaks.**

bolo gives AI coding agents a voice — **Letta Code, Codex, Claude Code, VS Code, OpenCode, Cursor, Pi**, or anything that speaks MCP. Every line is spoken by [Sarvam AI](https://sarvam.ai)'s **Bulbul V4 Flash** (200+ Indian voices, natural Hinglish); it can hear you too, via **Saaras V4**.

**The idea:** the agent decides *what to say out loud*. It calls `speak()` with the headline — a result, a question, a confirmation — while the full answer stays on screen. Your agent talks like a colleague, not like a printout.

## Install — one command

```bash
git clone https://github.com/Vedant020000/bolo && cd bolo
python3 -m bolo setup
```

```
  bolo setup · one plugin, every agent, a voice
  ─────────────────────────────────────────────

  ✓ tools      python3 · pw-play · arecord
  ✓ installed  ~/.local/bin/bolo · bolo-mcp · hook files
  ✓ harnesses  letta · codex · vscode · opencode
  ✓ api key    saved + verified
  ✓ daemon     127.0.0.1:47825
  ✓ voice      "bolo is ready." — did you hear it?
```

`setup` checks your tools, installs the shims, wires **every harness it finds** (MCP + auto-speak hooks), verifies your Sarvam API key, starts the daemon, and says hello out loud.

- Needs: Python 3, an audio player (`pw-play`/`paplay`/`aplay`), `arecord` — **zero pip dependencies**
- Something feels off later? `bolo doctor` finds it and prints the exact fix
- API key from [dashboard.sarvam.ai](https://dashboard.sarvam.ai) — `setup` asks for it once

## Install as a plugin (Claude Code / Codex)

This repo doubles as a plugin marketplace for both:

**Claude Code**
```
/plugin marketplace add Vedant020000/bolo
/plugin install bolo@bolo
```

**Codex**
```
codex plugin marketplace add Vedant020000/bolo
codex plugin add bolo@bolo
```

The plugin ships the `speak` / `listen` / `stop_speaking` tools plus the auto-speak hooks. Run `python3 -m bolo setup` once first — the plugin wires the tools, the engine does the talking.

## What agents can do

| tool | what it does |
|---|---|
| `speak(text, voice?)` | say the **headline** out loud (1–2 sentences) — full answer stays in text |
| `listen(max_seconds?)` | record until you stop talking → transcript (Hinglish-aware) |
| `stop_speaking()` | silence, immediately |

## Every harness

`bolo setup` wires these automatically — or add one JSON block anywhere:

| harness | mechanism | auto-wired |
|---|---|---|
| **Letta Code** | MCP + Stop hook | ✓ |
| **Codex** | plugin / MCP + notify | ✓ |
| **VS Code (Copilot)** | MCP | ✓ |
| **OpenCode** | MCP | ✓ |
| **Pi** | MCP | ✓ |
| **Cursor · Claude Desktop · Claude Code** | MCP / plugin | when installed |
| **anything MCP** | `{ "mcpServers": { "bolo": { "command": "bolo-mcp", "args": [] } } }` | — |

Hooks make agent replies **speak automatically** — off by default, toggle with `bolo on` / `bolo off`.

## CLI — for humans and scripts

```bash
bolo say "build finished"     # speak anything (scripts, CI, Makefiles)
bolo ask                      # push-to-talk: record → your agent → spoken reply
bolo chat                     # hands-free conversation with barge-in
bolo run -- pytest -q         # run a command; it reports the result out loud
bolo voices                   # 200+ Bulbul personas; --audition <id> to hear one
bolo status · bolo doctor · bolo setup
```

## Voices

200+ personas across 11 Indian languages — companions, narrators, news anchors, sports, late-night calm. Devanagari text is spoken as `hi-IN` automatically, so Hinglish comes out natural.

## Config — `~/.config/bolo/config.json` (0600)

| key | default | what |
|---|---|---|
| `api_key` | — | Sarvam API key |
| `voice` | `simran_enhi_companion` | default persona |
| `language` | `auto` | `auto` / `en-IN` / `hi-IN` / … |
| `interrupt` | `true` | new speech interrupts current speech |
| `mic_setup` | `[]` | commands re-applied at startup to keep the mic sane |

## Extras

- **Character packs** — `bolo play cricket` commentates your computer (cricket, news, trailer, documentary, dost, hype, maa)

## Credits

Voice, ears and brains by [Sarvam AI](https://sarvam.ai): **Bulbul V4 Flash** (TTS), **Saaras V4** (STT). Built for the Sarvam Discord Community Challenge.

## License

MIT
