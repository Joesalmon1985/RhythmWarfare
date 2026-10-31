"""Writes the replacement fixtures under content/fixtures/ (deterministic; rerun to refresh them).

    python tools/content/make_fixtures.py

- replacement/groove_watch/kick__kick_march.wav: a stand-in for an owner render of the groove_watch kick part with the
  March Kick sound: a long 808-style kick, 48 kHz stereo 16-bit, the clip's two bars plus a half-bar release tail.
- replacement/groove_watch/kick.mid: an edited structure MIDI for the same part: the original two kicks plus one on
  beat 4 of bar 1, as an Ableton type 1 export at 96 PPQ with no tempo event (the build rescales the PPQ exactly and
  uses the recorded 174 BPM).
- example_groove/: an example asset folder to copy into content/library/ (clip.json, kick.mid, snare.mid).
- waves_fixture.json and mission_fixture.json: a short mission the tests build into a temporary folder.
tools/content/test_content.py uses all of them; nothing here is part of the shipped campaign.
"""
from __future__ import annotations

import json
from pathlib import Path

import mido
import numpy as np

from common import CONTENT, PPQ, SAMPLE_RATE, TICKS_PER_BAR, bars_to_frames, tick_to_sample, write_json, write_midi, write_wav

FIX = CONTENT / "fixtures"


def owner_kick(ticks: list[int], bars: int, tail_bars: float) -> np.ndarray:
    n = bars_to_frames(bars) + int(tail_bars * bars_to_frames(1))
    out = np.zeros((n, 2), dtype=np.float32)
    for t in ticks:
        s = tick_to_sample(t)
        m = int(0.5 * SAMPLE_RATE)
        x = np.arange(m) / SAMPLE_RATE
        f = 48.0 + 70.0 * np.exp(-x / 0.02)
        sig = np.sin(2 * np.pi * np.cumsum(f) / SAMPLE_RATE) * np.exp(-x / 0.16) * 0.6
        k = min(m, n - s)
        out[s:s + k, 0] += sig[:k] * 0.95
        out[s:s + k, 1] += sig[:k]
    return out


def write_midi_96ppq_no_tempo(path: Path, notes: list[tuple[int, int, int, int]]) -> None:
    """Notes as (tick at 960 PPQ, duration, pitch, velocity), written at 96 PPQ without a tempo event."""
    mid = mido.MidiFile(type=1, ticks_per_beat=96)
    tr = mido.MidiTrack()
    events = []
    for t, d, p, v in notes:
        events.append((t // 10, 1, mido.Message("note_on", note=p, velocity=v)))
        events.append(((t + d) // 10, 0, mido.Message("note_off", note=p, velocity=0)))
    events.sort(key=lambda e: (e[0], e[1]))
    now = 0
    for t, _, msg in events:
        msg.time = t - now
        now = t
        tr.append(msg)
    mid.tracks.append(tr)
    path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(str(path))


def main() -> None:
    rep = FIX / "replacement" / "groove_watch"
    write_wav(rep / "kick__kick_march.wav", owner_kick([0, 4800], 2, 0.5))
    write_midi_96ppq_no_tempo(rep / "kick.mid", [(0, 120, 36, 110), (2880, 120, 36, 110), (4800, 120, 36, 110)])
    ex = FIX / "example_groove"
    write_json(ex / "clip.json", {"id": "example_groove", "kind": "groove", "name": "Example Groove", "bars": 2, "tempo_bpm": 174,
                                  "note": "Copy this folder to content/library/<your_id>/, set id (= folder name) and name, replace kick.mid and "
                                          "snare.mid with your Ableton MIDI exports and add <part>__<sound_id>.wav renders.",
                                  "source": {"type": "owner"}})
    write_midi(ex / "kick.mid", [{"tick": 0, "duration_ticks": 120, "pitch": 36, "velocity": 110},
                                 {"tick": 2400, "duration_ticks": 120, "pitch": 36, "velocity": 110},
                                 {"tick": TICKS_PER_BAR, "duration_ticks": 120, "pitch": 36, "velocity": 110}], "example kick")
    write_midi(ex / "snare.mid", [{"tick": 1920, "duration_ticks": 120, "pitch": 38, "velocity": 108},
                                  {"tick": TICKS_PER_BAR + 1920, "duration_ticks": 120, "pitch": 38, "velocity": 108}], "example snare")
    write_json(FIX / "waves_fixture.json", {"note": "Test fixture only.", "rules": {"objective_hp": {"command_core": 60000}},
                                            "waves": [{"id": "wave_01", "start_bar": 1, "entry": "left", "groups": [{"actor": "e1", "count": 2}]}]})
    write_json(FIX / "mission_fixture.json", {
        "level_id": "level_fixture", "number": 99, "title": "Fixture", "pack": "fixture_mission", "bars": 8, "seed": 99,
        "note": "Test fixture: the replacement tests build it into a temporary folder.",
        "battle": {"battlefield": "defense_02", "waves": "content/fixtures/waves_fixture.json"},
        "choices": {"kick_sound": {"count": 1, "pool": ["kick_march", "kick_armour"], "default": ["kick_march"]},
                    "groove": {"count": 1, "pool": ["groove_watch", "example_groove"], "default": ["groove_watch"]}},
        "phases": [{"bars": 4, "mode": "drums", "groove": 1, "kick_sound": 1, "snare_sound": "snare_guard", "sequence_bars": 4, "rewards": ["pillbox"]},
                   {"bars": 4, "mode": "drums", "groove": 1, "kick_sound": 1, "snare_sound": "snare_guard", "sequence_bars": 4, "rewards": ["e3"]}]})
    (FIX / "README.md").write_text(__doc__.split("\n\n", 1)[1].replace("tools/content/test_content.py", "`tools/content/test_content.py`"), encoding="utf-8")
    print("fixtures written to", FIX)


if __name__ == "__main__":
    main()
