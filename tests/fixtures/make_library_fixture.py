"""Writes tests/fixtures/library_fixture/ (a tiny loop library) and tests/fixtures/transport/ (two short WAV loops).

    python tests/fixtures/make_library_fixture.py

The index follows the contract of songs/library/index.json (format rhythm_warfare.library.v1). The loops are 8-bit mono
WAVs at 1 kHz, exactly eight bars at 174 BPM long; they only have to exist and have the right length for the loader.
"""
from __future__ import annotations

import json
import math
import struct
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
BAR = 3840
BAR_S = 4 * 60 / 174


def write_wav(path: Path, seconds: float, rate: int, freq: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = round(seconds * rate)
    data = bytes(128 + int(40 * math.sin(2 * math.pi * freq * i / rate)) for i in range(n))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(rate)
        w.writeframes(data)


def per_bar(offsets: list[int], pad: int, bars: int = 8) -> list[list[int]]:
    return [[b * BAR + o, 0, pad] for b in range(bars) for o in offsets]


def main() -> None:
    lib = HERE / "library_fixture"
    sounds = {
        "kick_a": {"family": "kick", "name": "Fixture Kick A", "placeholder": False, "produces": [{"reward": "rifle_squad", "share": 2}, {"reward": "grenadier_squad", "share": 1}], "blurb": "rifles twice, then a grenadier"},
        "kick_b": {"family": "kick", "name": "Fixture Kick B", "placeholder": False, "produces": [{"reward": "pillbox", "share": 1}], "blurb": "pillboxes"},
        "snare_a": {"family": "snare", "name": "Fixture Snare A", "placeholder": False, "produces": [{"reward": "grenadier_squad", "share": 1}], "blurb": "grenadiers"},
        "snare_b": {"family": "snare", "name": "Fixture Snare B", "placeholder": False, "produces": [], "blurb": "repairs"},
        "bass_a": {"family": "bass", "name": "Fixture Bass A", "placeholder": False, "produces": [{"reward": "rifle_squad", "share": 1}], "blurb": "rifles"},
        "bass_b": {"family": "bass", "name": "Fixture Bass B", "placeholder": False, "produces": [{"reward": "turret", "share": 1}], "blurb": "turrets"},
        "bass_c": {"family": "bass", "name": "Fixture Bass C", "placeholder": False, "produces": [{"reward": "flame_tower", "share": 1}], "blurb": "flame towers"},
    }
    fill_kick = [[7 * BAR + o, 0, 1] for o in (0, 960, 1920)]
    fill_snare = [[7 * BAR + 2880, 0, 4]]
    bass1 = [[b * BAR, 0, [2, 3, 1, 4][b % 4]] for b in range(8)]
    bass1 += [[2 * BAR + 1920, 1920, 2], [5 * BAR + 1920, 1920, 1]]  # holds in bars 3 and 6, each ends inside its two-bar sequence
    bass1.sort()
    clips = {
        "groove_a": {"kind": "groove", "name": "Fixture Groove A", "key": "", "bars": 8, "parts": ["kick", "snare"], "bound": True,
                     "sounds": {"kick": ["kick_a", "kick_b"], "snare": ["snare_a", "snare_b"]},
                     "cues": {"kick": per_bar([0, 1920], 1), "snare": per_bar([960, 2880], 4)}},
        "groove_b": {"kind": "groove", "name": "Fixture Groove B", "key": "", "bars": 8, "parts": ["kick", "snare"], "bound": True,
                     "sounds": {"kick": ["kick_a"], "snare": ["snare_a"]},
                     "cues": {"kick": per_bar([0], 1), "snare": per_bar([1920], 4)}},
        "fill_a": {"kind": "fill", "name": "Fixture Fill A", "key": "", "bars": 8, "parts": ["kick", "snare"], "bound": True,
                   "sounds": {"kick": ["kick_a"], "snare": ["snare_a", "snare_b"]},
                   "cues": {"kick": fill_kick, "snare": fill_snare}},
        "bass_line_1": {"kind": "bass", "name": "Fixture Line 1", "key": "C# minor", "bars": 8, "parts": ["bass"], "bound": False,
                        "sounds": {"bass": ["bass_a", "bass_b"]}, "cues": {"bass": bass1}},
        "bass_line_2": {"kind": "bass", "name": "Fixture Line 2", "key": "F minor", "bars": 8, "parts": ["bass"], "bound": False,
                        "sounds": {"bass": ["bass_c"]}, "cues": {"bass": per_bar([0, 1920], 1)}},
        "acc_a": {"kind": "backing", "name": "Fixture Backing A", "key": "", "bars": 8, "parts": ["other"], "bound": False,
                  "sounds": {}, "cues": {}},
        "acc_b": {"kind": "backing", "name": "Fixture Backing B", "key": "C# minor", "bars": 8, "parts": ["other"], "bound": False,
                  "sounds": {}, "cues": {}},
    }
    freq = 3.0
    for cid, c in clips.items():
        c["loops"] = {}
        c["peak_db"] = -6.0
        for part in c["parts"]:
            c["loops"][part] = {}
            for sound in c["sounds"].get(part, [""]):
                rel = f"loops/{cid}__{part}__{sound or 'backing'}.wav"
                # a backing's loop is keyed by "" in one clip and by its own id in the other (the loader accepts both)
                key = sound if sound or cid == "acc_a" else cid
                c["loops"][part][key] = rel
                freq += 1.5
                write_wav(lib / rel, 8 * BAR_S, 1000, freq)
    index = {"format": "rhythm_warfare.library.v1", "bpm": 174, "ticks_per_beat": 960, "loop_bars": 8,
             "defaults": {"groove": "groove_a", "fill": "", "kick_sound": "kick_a", "snare_sound": "snare_a", "bass": "bass_line_1", "bass_sound": "bass_a", "backing": "acc_a"},
             "sounds": sounds, "clips": clips}
    (lib / "index.json").write_text(json.dumps(index, indent=1) + "\n", encoding="utf-8", newline="\n")
    write_wav(HERE / "transport" / "loop_half.wav", 0.5, 8000, 220)
    write_wav(HERE / "transport" / "loop_one.wav", 1.0, 8000, 330)


if __name__ == "__main__":
    main()
