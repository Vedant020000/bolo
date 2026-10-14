#!/usr/bin/env python3
"""Pre-render all scripted Khooni Monday audio with Bulbul V4 Flash.

Writes WAVs + a manifest into bolo/mystery/assets/ so the game plays its
scripted scenes (cold open, intros, confessions, taunts) instantly.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from bolo import config, render, sarvam  # noqa: E402
from bolo.mystery import content  # noqa: E402

ASSETS = pathlib.Path(__file__).resolve().parents[1] / "bolo" / "mystery" / "assets"


def main() -> int:
    cfg = config.load()
    key = cfg.get("api_key")
    if not key:
        print("no api key in config")
        return 1

    scenes = content.all_scenes()
    total = sum(len(v) for v in scenes.values())
    manifest: dict[str, list[str]] = {}
    n = 0
    for scene, lines in scenes.items():
        files: list[str] = []
        for i, line in enumerate(lines):
            out = ASSETS / scene.replace(".", "_") / f"{i}.wav"
            out.parent.mkdir(parents=True, exist_ok=True)
            if not out.exists():
                lang = render.lang_for(line["text"])
                wav = sarvam.tts(line["text"], key=key, voice=line["voice"], language=lang)
                out.write_bytes(wav)
            files.append(str(out.relative_to(ASSETS)))
            n += 1
            print(f"[{n}/{total}] {scene}[{i}] {line['text'][:60]}")
        manifest[scene] = files
    (ASSETS / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"done: {total} clips -> {ASSETS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
