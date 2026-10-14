# bolo — demo video script (~80 seconds)

**The pitch in one line:** one plugin → every AI agent on your computer gets a voice (Sarvam Bulbul).

## Before recording

- Quiet room. Daemon running (`bolo daemon start`). Test: `letta mcp call mcp__bolo__speak --args '{"text":"mic check"}'`
- Big terminal font, dark theme. OBS recording screen + system audio + mic.
- VS Code: reload window once (so it picks up `mcp.json`).

## Shots

### 1 — Cold open: an agent speaks (0:00–0:18)

Terminal:

```bash
codex
> use the bolo speak tool to say: "Codex here. हाँ, अब मैं बोल सकता हूँ।" in a news anchor voice
```

→ Codex calls the `speak` tool → the line plays in `simran_hi_news_breaking`.
(If Codex is slow: cut to the Letta one-liner below instead.)

### 2 — "How? One plugin." (0:18–0:35)

Show the 5-line block that did it (VS Code `mcp.json` or `~/.letta/settings.json`):

```json
"bolo": { "command": "/home/vedant/.local/bin/bolo-mcp", "args": [] }
```

Then the proof across harnesses — quick cuts:

```bash
letta mcp call mcp__bolo__speak --args '{"text":"Letta Code speaks too.","voice":"shubh_enhi_companion"}'
```

VS Code Copilot Chat: *"use bolo speak to say: VS Code can talk now."* → voice plays.

### 3 — It hears you too (0:35–0:55)

```bash
letta mcp call mcp__bolo__listen --args '{}'
```

→ speak: *"Rohan, raat nau baje tum kahan the?"* → wait → transcript appears:
`ये test बोलो पर पास हो गया, चलो चाय पीते हैं`-style codemix output.
(One live take is fine — imperfection is proof it's real.)

### 4 — 200+ voices, one model (0:55–1:10)

```bash
bolo voices --audition sunny_hi_reels
bolo voices --audition ratan_hi_latenight
bolo voices --audition roopa_hi_companion
```

Quick cuts of each voice saying hello. Caption: *all Bulbul V4 Flash*.

### 5 — End card (1:10–1:20)

```
bolo — give any agent a voice
Bulbul V4 Flash · Saaras V4 · by Sarvam
github.com/<you>/bolo
```

## Notes

- Every tool call in this video is real; nothing is mocked.
- `bolo say "text"` works anywhere if an agent isn't cooperating on camera.
- Keep it under 90s.
