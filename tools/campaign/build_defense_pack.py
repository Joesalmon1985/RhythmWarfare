"""Build a schema 2 defense pack (songs/<name>/level.json plus placeholder stems) from one campaign level.

    python tools/campaign/build_defense_pack.py all        # or 1, 2, 3

Reads campaign/First_Three/level_0N/ (song.json, chart_rules*.json, Music/*.mid), verifies the part MIDI hashes
against campaign/Musical_Source_Integrity.json, compiles every chart in memory with the reference compiler (the
notes must equal the pack's player_chart*.json exactly), synthesises placeholder stems per slot and profile,
encodes Ogg Vorbis and writes level.json with source hashes and the render manifest. The MIDI is never written.
All audio produced here is synthesised placeholder sound and is marked `placeholder: true`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools"))

from compile_chart import compile_chart, read_notes  # noqa: E402
import make_song_pack as msp  # noqa: E402

IMPORTER_VERSION = 1
SAMPLE_RATE = 48000
CAMPAIGN = ROOT / "campaign"
LEVELS = {
    1: {"pack": "first_watch", "rules": ["chart_rules.json"]},
    2: {"pack": "second_pulse", "rules": ["chart_rules.json", "chart_rules.practice.json"]},
    3: {"pack": "hold_the_line", "rules": ["chart_rules.json"]},
}
NOTE_FIELDS = ("id", "tick", "button", "type", "duration_ticks", "slot_id", "part_id", "source_note_id", "family")
PLACEHOLDER_GAIN = 0.55  # each stem is limited to 0.8 by the synth; five stems must still sum below full scale
MAX_LEVEL_FOR_RENDERS = 3  # profiles unlocked by level 3 get placeholder renders for every active slot of that family


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_midi_hashes(level_dir: Path, song: dict) -> dict[str, str]:
    integrity = json.loads((CAMPAIGN / "Musical_Source_Integrity.json").read_text())["after_sha256"]
    out = {}
    for part in song["parts"]:
        path = level_dir / part["midi"]
        key = f"First_Three/{level_dir.name}/{part['midi']}"
        digest = sha256_file(path)
        if integrity.get(key) != digest:
            raise SystemExit(f"MIDI hash mismatch for {key}: file {digest}, integrity record {integrity.get(key)}")
        out[part["id"]] = digest
    return out


def compile_charts(level_dir: Path, rules_names: list[str]) -> list[dict]:
    charts = []
    for rules_name in rules_names:
        chart = compile_chart(level_dir, rules_name, "unused.json", write=False)
        reference_name = "player_chart.json" if rules_name == "chart_rules.json" else rules_name.replace("chart_rules", "player_chart")
        reference = json.loads((level_dir / reference_name).read_text())
        ours = [{k: n[k] for k in n} for n in chart["notes"]]
        if ours != reference["notes"] or chart["sections"] != reference["sections"]:
            raise SystemExit(f"{level_dir.name}: compiled chart {chart['chart_id']} differs from {reference_name}")
        notes = [{k: n[k] for k in NOTE_FIELDS if k in n} for n in chart["notes"]]
        charts.append({
            "chart_id": chart["chart_id"],
            "play_mode": chart["play_mode"],
            "progression": bool(chart["progression_enabled"]),
            "sections": [{"id": s["id"], "start_tick": s["start_tick"], "length_bars": s["length_bars"], "mode": s["mode"]} for s in chart["sections"]],
            "notes": notes,
        })
    return charts


# --- placeholder audio -----------------------------------------------------------------------------------------------
def resample(sig: np.ndarray, factor: float) -> np.ndarray:
    if factor == 1.0:
        return sig
    return np.interp(np.arange(0, len(sig) - 1, factor), np.arange(len(sig)), sig)


def render_slot(family: str, midi_notes: list[dict], total: int, seed: int, variant: int) -> np.ndarray:
    sr = SAMPLE_RATE
    rng = np.random.default_rng(seed)
    buf = np.zeros(total, dtype=np.float32)
    pitch = [1.0, 0.78, 1.3, 0.65][variant % 4]
    for n in midi_notes:
        start = msp.tick_to_sample(n["tick"], sr)
        if family == "kick":
            msp.add_at(buf, start, resample(msp.synth_kick(sr, rng, n["velocity"]), pitch))
        elif family == "snare":
            msp.add_at(buf, start, resample(msp.synth_snare(sr, rng, n["velocity"], ["snare", "clap", "rim"][variant % 3]), pitch))
        elif family == "bass":
            end = min(msp.tick_to_sample(n["tick"] + n["duration_ticks"], sr), total)
            if end > start:
                sig = msp.synth_bass_note(sr, n["midi_note"], n["velocity"], end - start)
                if variant % 2 == 1:  # a buzzier second voice so alternative bass profiles sound different
                    t = np.arange(len(sig)) / sr
                    f = msp.midi_to_hz(n["midi_note"])
                    sig = sig + 0.25 * np.sin(2 * np.pi * f * 3 * t) * msp.adsr(len(sig), sr)
                msp.add_at(buf, start, sig)
    return buf


def render_other(parts: list[tuple[dict, list[dict]]], total: int, seed: int) -> np.ndarray:
    sr = SAMPLE_RATE
    rng = np.random.default_rng(seed)
    buf = np.zeros(total, dtype=np.float32)
    for part, notes in parts:
        if part["id"].endswith("hats"):
            for n in notes:
                msp.add_at(buf, msp.tick_to_sample(n["tick"], sr), msp.synth_hat(sr, rng, n["velocity"], "closed"))
        else:  # pad: one chord per bar from the notes that start in it
            bars: dict[int, list[int]] = {}
            for n in notes:
                bars.setdefault(n["tick"] // msp.TICKS_PER_BAR, []).append(n["midi_note"])
            for bar, pitches in bars.items():
                s0, s1 = msp.tick_to_sample(bar * msp.TICKS_PER_BAR, sr), msp.tick_to_sample((bar + 1) * msp.TICKS_PER_BAR, sr)
                msp.add_at(buf, s0, msp.synth_pad_bar(sr, sorted(set(pitches))[:6], s1 - s0))
    return buf


def write_ogg(samples: np.ndarray, ogg: Path) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "x.wav"
        msp.write_wav(wav, msp.finalize(samples) * PLACEHOLDER_GAIN, SAMPLE_RATE)
        with wave.open(str(wav)) as wf:
            frames = wf.getnframes()
        msp.encode_ogg(wav, ogg, SAMPLE_RATE)
    return frames


def profiles_for(catalogue: list[dict], family: str, default_profile: str) -> list[str]:
    ids = [p["id"] for p in catalogue if p["family"] == family and int(p["available_from_level"]) <= MAX_LEVEL_FOR_RENDERS]
    if default_profile not in ids:
        ids.insert(0, default_profile)
    return ids


def travel_report(level: dict) -> None:
    """Prints how long each wave's actors need from their entry to the defense point and on to the wall opening, so a
    wave author can see when contact happens (straight-line distance at the actor's rules speed, cells per second)."""
    bf = json.loads((ROOT / "data" / "battlefields" / f"{level['battlefield']}.json").read_text())
    actors = json.loads((ROOT / "data" / "openra_rules.json").read_text())["actors"]
    entries = {e["id"]: (e["x"] + 0.5, e["y"] + 0.5) for e in bf["entries"]}
    points = {p["id"]: (p["x"] + 0.5, p["y"] + 0.5) for p in bf["defense_points"]}
    opening = (15.5, 10.0)
    seconds_per_tick = 60.0 / (level["bpm"] * level["ticks_per_beat"])
    print("  travel (seconds from spawn): wave, entry -> point, actors to the point / to the wall opening")
    for w in level["waves"]:
        a, b = entries[w["entry"]], points[w["via_defense_point"]]
        d1 = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
        d2 = ((b[0] - opening[0]) ** 2 + (b[1] - opening[1]) ** 2) ** 0.5
        bits = []
        for actor in sorted({g["actor"] for g in w["groups"]}):
            cps = actors[actor]["speed"] / 1024.0 * 25.0
            bits.append(f"{actor} {d1 / cps:.1f}s/{(d1 + d2) / cps:.1f}s")
        print(f"    {w['id']} at {w['start_tick'] * seconds_per_tick:5.1f}s  {w['entry']:>6} -> {w['via_defense_point']}: " + ", ".join(bits))


def load_waves(number: int, level_dir: Path) -> tuple[dict, Path]:
    wave_file = ROOT / "data" / "campaign" / "waves" / f"level_{number:02d}.json"
    src = wave_file if wave_file.exists() else level_dir / "waves.proposed.json"
    return json.loads(src.read_text()), src


def rewrite_waves(number: int) -> None:
    """Refresh waves and rules in an existing level.json without touching audio (for balance iteration)."""
    spec = LEVELS[number]
    path = ROOT / "songs" / spec["pack"] / "level.json"
    level = json.loads(path.read_text())
    waves, src = load_waves(number, CAMPAIGN / "First_Three" / f"level_{number:02d}")
    level["waves"] = waves["waves"]
    level["rules"] = waves.get("rules", {})
    level["battlefield"] = waves.get("battlefield", level["battlefield"])
    level["source"]["wave_source"] = src.relative_to(ROOT).as_posix()
    path.write_text(json.dumps(level, indent=1) + "\n")
    print(f"level {number}: waves refreshed from {src.relative_to(ROOT).as_posix()}")
    travel_report(level)


def build_level(number: int) -> None:
    spec = LEVELS[number]
    level_dir = CAMPAIGN / "First_Three" / f"level_{number:02d}"
    song = json.loads((level_dir / "song.json").read_text())
    catalogue = json.loads((ROOT / "data" / "instruments" / "catalogue.json").read_text())["instruments"]
    midi_hashes = verify_midi_hashes(level_dir, song)
    charts = compile_charts(level_dir, spec["rules"])
    out_dir = ROOT / "songs" / spec["pack"]
    audio_dir = out_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    bar_ticks = song["ticks_per_beat"] * song["time_signature"][0]
    duration_ticks = song["bars"] * bar_ticks
    total = int(round((song["bars"] + 1) * bar_ticks * msp.SECONDS_PER_TICK * SAMPLE_RATE))  # one-bar release tail
    midi = {p["id"]: read_notes(level_dir / p["midi"], song["ticks_per_beat"])[0] for p in song["parts"]}

    renders: dict[str, dict] = {}
    for part in song["parts"]:
        slot = part["slot_id"]
        if slot is None:
            continue
        family = part["family"]
        default = song["default_loadout"][slot]
        renders[slot] = {}
        order = [p["id"] for p in catalogue if p["family"] == family]
        for profile in profiles_for(catalogue, family, default):
            variant = order.index(profile) if profile in order else 0
            rel = f"audio/{slot}__{profile}.ogg"
            frames = write_ogg(render_slot(family, midi[part["id"]], total, number * 100 + variant, variant), out_dir / rel)
            renders[slot][profile] = {"file": rel, "source_sha256": midi_hashes[part["id"]], "sample_rate": SAMPLE_RATE,
                                      "frames": frames, "placeholder": True, "profile_default": profile == default}
    other_parts = [p for p in song["parts"] if p["slot_id"] is None]
    frames = write_ogg(render_other([(p, midi[p["id"]]) for p in other_parts], total, number * 100 + 99), audio_dir / "other.ogg")
    other_hash = hashlib.sha256("".join(midi_hashes[p["id"]] for p in other_parts).encode()).hexdigest()
    renders["other"] = {"accompaniment": {"file": "audio/other.ogg", "source_sha256": other_hash, "sample_rate": SAMPLE_RATE,
                                          "frames": frames, "placeholder": True, "profile_default": True}}

    waves, waves_src = load_waves(number, level_dir)

    level = {
        "schema_version": 2,
        "mode": "defense",
        "level_id": song["level_id"],
        "campaign_level": number,
        "title": song["title"],
        "bpm": song["bpm"],
        "time_signature": song["time_signature"],
        "ticks_per_beat": song["ticks_per_beat"],
        "song_offset_ms": 0,
        "duration_ticks": duration_ticks,
        "seed": 1000 + number,
        "battlefield": waves.get("battlefield", "defense_01"),
        "rules": waves.get("rules", {}),
        "roster": "openra_mvp_01",
        "source": {"midi_sha256": midi_hashes, "importer_version": IMPORTER_VERSION, "wave_source": waves_src.relative_to(ROOT).as_posix()},
        "parts": [{"id": p["id"], "family": p["family"], "slot_id": p["slot_id"], "render_bus": p["render_bus"]} for p in song["parts"]],
        "loadout": {"active_slots": song["active_loadout_slots"], "default": song["default_loadout"]},
        "renders": renders,
        "stems": {"other": "audio/other.ogg"},
        "charts": charts,
        "waves": waves["waves"],
    }
    (out_dir / "level.json").write_text(json.dumps(level, indent=1) + "\n")
    counts = {c["chart_id"]: len(c["notes"]) for c in charts}
    print(f"level {number} -> songs/{spec['pack']}: charts {counts}, {len(renders)} render groups, {sum(len(v) for v in renders.values())} files")
    travel_report(level)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("level", help="1, 2, 3 or all")
    parser.add_argument("--waves-only", action="store_true", help="refresh waves and rules in level.json, no audio")
    args = parser.parse_args()
    for n in (LEVELS if args.level == "all" else [int(args.level)]):
        rewrite_waves(n) if args.waves_only else build_level(n)


if __name__ == "__main__":
    main()
