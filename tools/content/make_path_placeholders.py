"""Synthesised stand-in music for a path's scenes: songs/packs/<path>_<scene>/ at the path's tempo (docs/THREE_PATHS_AND_FACES_PLAN.md 3.5, D5).

    python tools/content/make_path_placeholders.py <path>            # every scene of content/paths/<path>/run.json that has no import
    python tools/content/make_path_placeholders.py <path> --force    # also regenerate the placeholders already written
    python tools/content/make_path_placeholders.py <path> --out DIR  # packs into DIR instead of songs/packs (tests)

For each scene it writes an 8-bar drum loop (kick, snare/clap, hats), a bass loop and a synth pad, in the pack format `beatshaper.py import` writes (pack.json with the three loops as 48 kHz stereo WAV of exactly
`loop_frames`, the tiered cues, `profile` `<path>_x1`), plus the MIDI the chart is made from (midi/drums.mid, bass.mid, synth.mid: the cues come out of these same notes through beatshaper's own
build_cues / tier_cues, so the placeholder is charted exactly like an import). pack.json carries `"path": "<id>"` (the main run never loads it, the path's run loads only its own), `"placeholder": true`
and `"temporary"` music.json entries are written for the scenes. When the owner's loop arrives, `beatshaper.py import --path <id> ...` replaces the pack and `assign --final` clears the flag. Nothing is
sampled or stretched: the sounds are numpy oscillators and noise (like make_run_effects.py), deterministic per path and scene.

Genre patterns (music.json `placeholder.genre`): house = four on the floor, claps on 2 and 4, offbeat open hats, a syncopated bass; dubstep = half time (snare on beat 3 of the bar), long sub notes with a wobble
on the upper harmonics; psytrance = four on the floor with a 16th-note rolling bass pulse between the kicks.

The mix is BASS-FORWARD and lives in music.json (`placeholder.levels_db`, RMS of each stem over the loop, dBFS; `placeholder.sub_hz`, `placeholder.sub_share_min`): the bass stem is the loudest by default
(its sub sine carries 40% or more of its energy under `sub_hz`, the rest is a harmonic stack a phone speaker can play), the drums sit under it and the pad well below; the script prints the measured levels and refuses to write a bass quieter than the pad.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import zlib
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from beatshaper import build_cues, tier_cues  # noqa: E402
from chart import load_rules  # noqa: E402
from common import PPQ, ROOT, SAMPLE_RATE, ContentError, read_json, write_json, write_wav  # noqa: E402
from import_recorded import db, fold_loop  # noqa: E402
from midi_reader import build_midi, ev_name, ev_tempo, ev_time_sig, note_events  # noqa: E402

PATHS = ROOT / "content" / "paths"
IMPORTS = ROOT / "content" / "imports"  # <path>/<scene>/Beat Shaper - <scene>-Drums|Bass|Synth .wav/.mid: the owner's drops (D5)
PACKS = ROOT / "songs" / "packs"
BARS = 8
PHRASE_BEATS = BARS * 4
STEPS = 16  # sixteenth notes per bar

DEFAULT_MIX = {
    "genre": "house",
    "key": 45,  # MIDI note of the bass root (A2); the bass sounds an octave lower
    "levels_db": {"drums": -20.0, "bass": -13.0, "other": -27.0},  # RMS of each stem over the loop, dBFS: the bass is the loudest tonal thing by 7 dB or more
    "sub_hz": 90.0,
    "sub_share_min": 0.4,  # at least this share of the bass stem's energy lies under sub_hz
    "bass_over_pad_db_min": 8.0,
}

KICK, SNARE, CHAT, OHAT = 36, 38, 42, 46

# bar patterns in sixteenth steps (0..15); `fill` replaces the last beat of bars 4 and 8
GENRES = {
    "house": {
        "kick": [0, 4, 8, 12], "snare": [4, 12], "chat": [1, 3, 5, 7, 9, 11, 13, 15], "ohat": [2, 6, 10, 14], "fill": {"snare": [12, 13, 14, 15]},
        "bass": [(0, 3, 0), (3, 1, 0), (6, 2, 0), (10, 2, 7), (12, 3, 0)],  # (step, length in steps, semitones above the bar's root)
        "roots": [0, 0, -4, -2], "wobble": 0.0, "pad_every": 2,
    },
    "dubstep": {
        "kick": [0, 10], "snare": [8], "chat": [0, 2, 4, 6, 8, 10, 12, 14], "ohat": [14], "fill": {"snare": [8, 10, 12, 13, 14, 15]},
        "bass": [(0, 7, 0), (8, 5, 0), (13, 2, 3)],
        "roots": [0, 0, -2, -4], "wobble": 1.0, "pad_every": 4,
    },
    "psytrance": {
        "kick": [0, 4, 8, 12], "snare": [4, 12], "chat": [1, 3, 5, 7, 9, 11, 13, 15], "ohat": [2, 6, 10, 14], "fill": {"snare": [12, 13, 14, 15]},
        "bass": [(s, 1, 12 if s % 8 == 3 else 0) for b in range(4) for s in (4 * b + 1, 4 * b + 2, 4 * b + 3)],
        "roots": [0, 0, -2, 0], "wobble": 0.0, "pad_every": 2,
    },
}


def rng_for(path: str, scene: str) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(f"{path}/{scene}".encode()))


# --- sounds -----------------------------------------------------------------------------------------------------------

def _t(n: int) -> np.ndarray:
    return np.arange(n) / SAMPLE_RATE


def kick() -> np.ndarray:
    t = _t(int(0.4 * SAMPLE_RATE))
    f = 44.0 + 120.0 * np.exp(-t / 0.028)
    ph = 2 * np.pi * np.cumsum(f) / SAMPLE_RATE
    env = np.minimum(1.0, t / 0.002) * np.exp(-t / 0.13)
    click = np.exp(-t / 0.002) * np.sin(2 * np.pi * 1800 * t) * 0.3
    return (np.sin(ph) * env + click) * 0.95


def _hp(x: np.ndarray, a: float = 0.92) -> np.ndarray:
    y = np.empty_like(x)
    y[0] = x[0]
    y[1:] = x[1:] - a * x[:-1]
    return y


def snare(rng: np.random.Generator) -> np.ndarray:
    t = _t(int(0.28 * SAMPLE_RATE))
    noise = _hp(rng.standard_normal(len(t)), 0.6) * np.exp(-t / 0.07)
    body = np.sin(2 * np.pi * (190 - 60 * np.minimum(t / 0.1, 1.0)) * t) * np.exp(-t / 0.05)
    clap = np.zeros(len(t))
    for off in (0.0, 0.011, 0.022):  # three quick bursts: a clap rather than a rim
        k = int(off * SAMPLE_RATE)
        n = int(0.05 * SAMPLE_RATE)
        clap[k:k + n] += _hp(rng.standard_normal(n), 0.5) * np.exp(-_t(n) / 0.02)
    return (0.55 * noise + 0.35 * body + 0.45 * clap) * 0.75


def hat(rng: np.random.Generator, open_: bool) -> np.ndarray:
    n = int((0.22 if open_ else 0.06) * SAMPLE_RATE)
    t = _t(n)
    x = _hp(_hp(rng.standard_normal(n), 0.95), 0.9) * np.exp(-t / (0.07 if open_ else 0.014))
    return x * (0.22 if open_ else 0.16)


def _partials(f: float, n: int, wobble: np.ndarray | None, rolloff: float) -> np.ndarray:
    t = _t(n)
    out = np.zeros(n)
    k = 2  # (the fundamental is the sub sine of bass_note, so the stack starts at the octave: a phone speaker plays the stack, a club plays the sub)
    while f * k < 3500 and k < 14:
        a = 1.0 / (k ** rolloff)
        if wobble is not None and k > 1:
            a = a * (0.25 + 0.75 * wobble)  # the wobble opens and closes the upper harmonics (a crude filter), the sub stays
        out += a * np.sin(2 * np.pi * f * k * t + k)
        k += 1
    return out


def bass_note(f: float, dur_s: float, wobble_hz: float, sub: float = 1.0) -> np.ndarray:
    n = int((dur_s + 0.08) * SAMPLE_RATE)
    t = _t(n)
    wob = None
    if wobble_hz > 0.0:
        wob = 0.5 + 0.5 * np.sin(2 * np.pi * wobble_hz * t - np.pi / 2)
    upper = _partials(f, n, wob, 1.0)
    subsine = np.sin(2 * np.pi * f * t)  # the sub: a plain sine at the root, under everything
    env = np.minimum(1.0, t / 0.004) * np.where(t < dur_s, 1.0, np.exp(-(t - dur_s) / 0.02)) * (0.7 + 0.3 * np.exp(-t / 0.12))
    return (1.2 * upper + sub * subsine) * env


def pad_chord(freqs: list[float], dur_s: float) -> np.ndarray:
    n = int(dur_s * SAMPLE_RATE)
    t = _t(n)
    out = np.zeros(n)
    for f in freqs:
        for detune in (-0.004, 0.0, 0.004):
            ff = f * (1.0 + detune)
            for k in (1, 2, 3, 4):
                out += np.sin(2 * np.pi * ff * k * t + k * 0.7) / (k ** 1.6)
    env = np.minimum(1.0, t / (dur_s * 0.35)) * np.minimum(1.0, (dur_s - t) / (dur_s * 0.35))
    return out * env


def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


# --- one scene ---------------------------------------------------------------------------------------------------------

def bar_pattern(genre: dict, bar: int, variant: int) -> dict:
    p = {k: list(genre[k]) for k in ("kick", "snare", "chat", "ohat")}
    if bar % 4 == 3:  # a fill every fourth bar
        p["snare"] = sorted(set([s for s in p["snare"] if s < 12] + genre["fill"]["snare"]))
        p["ohat"] = [s for s in p["ohat"] if s < 12]
    if variant == 1 and bar % 2 == 1:  # the sibling scenes differ a little: an extra offbeat kick
        p["kick"] = sorted(set(p["kick"]) | {14}) if len(genre["kick"]) > 2 else p["kick"]
    elif variant == 2 and bar % 2 == 0:
        p["chat"] = [s for s in p["chat"] if s % 4 != 1]
    return p


def build_scene(bpm: int, mix: dict, rng: np.random.Generator, variant: int) -> dict:
    genre = GENRES[mix["genre"]]
    beat_s = 60.0 / bpm
    step_s = beat_s / 4.0
    loop_frames = int(round(PHRASE_BEATS * beat_s * SAMPLE_RATE))
    tail = int(1.5 * SAMPLE_RATE)
    n = loop_frames + tail
    drums = np.zeros(n)
    bass = np.zeros(n)
    pad = np.zeros(n)
    k_snd, s_snd = kick(), snare(rng)
    h_closed = [hat(rng, False) for _ in range(3)]
    h_open = hat(rng, True)
    drum_notes: list[dict] = []
    bass_notes: list[dict] = []
    synth_notes: list[dict] = []
    key = int(mix["key"]) + (variant % 3) * 2  # a sibling scene sits a tone or two up: a different chart pack and a different colour

    def put(buf: np.ndarray, snd: np.ndarray, t: float, gain: float) -> None:
        i = int(round(t * SAMPLE_RATE))
        m = min(len(snd), len(buf) - i)
        if m > 0:
            buf[i:i + m] += snd[:m] * gain

    for bar in range(BARS):
        pat = bar_pattern(genre, bar, variant)
        t0 = bar * 4 * beat_s
        root = genre["roots"][bar % len(genre["roots"])]
        for s in pat["kick"]:
            put(drums, k_snd, t0 + s * step_s, 1.0)
            drum_notes.append({"pitch": KICK, "beat": bar * 4 + s / 4.0, "dur": 0.25, "vel": 118})
        for s in pat["snare"]:
            put(drums, s_snd, t0 + s * step_s, 0.8)
            drum_notes.append({"pitch": SNARE, "beat": bar * 4 + s / 4.0, "dur": 0.25, "vel": 108})
        for s in pat["chat"]:
            put(drums, h_closed[s % 3], t0 + s * step_s, 0.8 if s % 2 else 1.0)
            drum_notes.append({"pitch": CHAT, "beat": bar * 4 + s / 4.0, "dur": 0.1, "vel": 70})
        for s in pat["ohat"]:
            put(drums, h_open, t0 + s * step_s, 1.0)
            drum_notes.append({"pitch": OHAT, "beat": bar * 4 + s / 4.0, "dur": 0.25, "vel": 90})
        for (s, length, semi) in genre["bass"]:
            midi = key - 12 + root + semi
            dur_s = max(length * step_s * 0.92, 0.05)
            put(bass, bass_note(hz(midi), dur_s, (1.0 / (beat_s / 2.0)) if genre["wobble"] > 0.0 else 0.0), t0 + s * step_s, 1.0)
            bass_notes.append({"pitch": midi, "beat": bar * 4 + s / 4.0, "dur": length / 4.0, "vel": 112})
        if bar % int(genre["pad_every"]) == 0:
            span = int(genre["pad_every"]) * 4 * beat_s
            chord = [key + root, key + root + 3, key + root + 7, key + root + 10]
            put(pad, pad_chord([hz(m) for m in chord], span), t0, 1.0)
            for m in chord:
                synth_notes.append({"pitch": m, "beat": bar * 4.0, "dur": int(genre["pad_every"]) * 4.0, "vel": 80})
    stems = {}
    for name, buf in (("drums", drums), ("bass", bass), ("other", pad)):
        st = np.stack([buf, np.roll(buf, int(0.0004 * SAMPLE_RATE)) if name == "other" else buf], axis=1)
        loop, info = fold_loop(st, loop_frames)
        stems[name] = (loop.astype(np.float64), info)
    return {"stems": stems, "drum_notes": drum_notes, "bass_notes": bass_notes, "synth_notes": synth_notes, "loop_frames": loop_frames}


def rms_db(x: np.ndarray) -> float:
    return db(float(np.sqrt((x.astype(np.float64) ** 2).mean())) + 1e-12)


def sub_share(x: np.ndarray, sub_hz: float) -> float:
    mono = x.mean(axis=1) if x.ndim == 2 else x
    spec = np.abs(np.fft.rfft(mono)) ** 2
    f = np.fft.rfftfreq(len(mono), 1.0 / SAMPLE_RATE)
    return float(spec[f < sub_hz].sum() / max(spec.sum(), 1e-12))


def set_levels(stems: dict, mix: dict) -> dict:
    """Scales each stem to its RMS target (music.json levels_db), with a soft clip so the hot bass never goes over full scale; returns the measured numbers."""
    out = {}
    for name, (loop, _info) in stems.items():
        target = float(mix["levels_db"][name])
        cur = rms_db(loop)
        g = 10.0 ** ((target - cur) / 20.0)
        y = loop * g
        peak = float(np.abs(y).max())
        if peak > 0.9:  # soft saturation: tanh keeps the shape, the bass gets a little thicker
            y = np.tanh(y * 1.2) / math.tanh(1.2)
            y *= 10.0 ** ((target - rms_db(y)) / 20.0)
            y = np.clip(y, -0.98, 0.98)
        stems[name] = (y, _info)
        out[name] = {"rms_db": round(rms_db(y), 2), "peak_db": round(db(float(np.abs(y).max())), 2)}
    out["bass"]["sub_share"] = round(sub_share(stems["bass"][0], float(mix["sub_hz"])), 3)
    return out


def midi_bytes(notes: list[dict], name: str, bpm: int) -> bytes:
    evs = [ev_name(name), ev_tempo(bpm), ev_time_sig(4, 4)]
    evs += note_events([{"tick": int(round(n["beat"] * PPQ)), "duration_ticks": max(1, int(round(n["dur"] * PPQ))), "pitch": int(n["pitch"]), "velocity": int(n.get("vel", 100))} for n in notes])
    return build_midi(PPQ, [evs])


def write_scene_pack(out_root: Path, path_id: str, scene: str, node_id: str, title: str, bpm: int, mix: dict, variant: int) -> dict:
    pack_id = f"{path_id}_{scene}"
    built = build_scene(bpm, mix, rng_for(path_id, scene), variant)
    levels = set_levels(built["stems"], mix)
    over = levels["bass"]["rms_db"] - levels["other"]["rms_db"]
    if over < float(mix["bass_over_pad_db_min"]) or levels["bass"]["rms_db"] < levels["drums"]["rms_db"]:
        raise ContentError(f"{pack_id}: the placeholder mix is not bass-forward (bass {levels['bass']['rms_db']} dB, drums {levels['drums']['rms_db']} dB, pad {levels['other']['rms_db']} dB RMS); raise placeholder.levels_db.bass in music.json")
    if levels["bass"]["sub_share"] < float(mix["sub_share_min"]):
        raise ContentError(f"{pack_id}: only {levels['bass']['sub_share']:.0%} of the bass is under {mix['sub_hz']} Hz (placeholder.sub_share_min is {mix['sub_share_min']:.0%})")
    out = out_root / pack_id
    loops = {}
    for stem, (loop, info) in built["stems"].items():
        write_wav(out / "loops" / f"{stem}.wav", loop.astype(np.float32))
        info = dict(info)
        info.update({"gain_db": 0.0, "peak_db": levels[stem]["peak_db"], "rms_db": levels[stem]["rms_db"], "source_seconds": round(built["loop_frames"] / SAMPLE_RATE, 4), "source_file": "synthesised"})
        loops[stem] = info
    (out / "midi").mkdir(parents=True, exist_ok=True)
    for fn, notes, nm in (("drums", built["drum_notes"], "Drums"), ("bass", built["bass_notes"], "Bass"), ("synth", built["synth_notes"], "Synth")):
        (out / "midi" / f"{fn}.mid").write_bytes(midi_bytes(notes, nm, bpm))
    rules = load_rules()
    kick, snare_ = {KICK}, {SNARE, 40}
    cues = build_cues(built["drum_notes"], built["bass_notes"], 1, kick, snare_, rules, PHRASE_BEATS)
    tiers, problems = tier_cues(cues, rules, PHRASE_BEATS * PPQ)
    if problems:
        raise ContentError(f"{pack_id}: chart problems: {problems[:4]}")
    pack = {"schema": 1, "id": pack_id, "label": f"{title} - {node_id} (placeholder, {mix['genre']} {bpm})", "bpm": bpm, "phrase_beats": PHRASE_BEATS, "loop_frames": built["loop_frames"],
            "profile": f"{path_id}_x1", "stems": {k: f"loops/{k}.wav" for k in loops}, "loops": loops, "kick_notes": sorted(kick), "snare_notes": sorted(snare_), "tiers": tiers,
            "source": {"project": "placeholder", "variant": variant, "files": {"midi": {"drums": "midi/drums.mid", "bass": "midi/bass.mid", "synth": "midi/synth.mid"}}},
            "path": path_id, "placeholder": True, "genre": mix["genre"], "levels": levels}
    write_json(out / "pack.json", pack, indent=1)
    write_json(out / "timing_report.json", {"synthesised": True, "bpm": bpm, "levels": levels, "cue_counts": {t: {k: len(v) for k, v in d.items()} for t, d in tiers.items()}}, indent=1)
    return pack


# --- the path -------------------------------------------------------------------------------------------------------------

def is_import(pack_json: Path) -> bool:
    """A pack already on disk that is not one of ours (an owner's import)."""
    if not pack_json.exists():
        return False
    return not bool(read_json(pack_json).get("placeholder", False))


def has_import(path_id: str, node: dict, imports_root: Path = IMPORTS) -> bool:
    """True when the owner has dropped this scene's loops: a folder content/imports/<path>/<scene>/ (named like the scene key, the node id or the part of it after the path, case ignored) with WAVs in it.
    The real music always wins: a scene with a drop (imported yet or not) never gets a placeholder."""
    base = imports_root / path_id
    if not base.is_dir():
        return False
    names = {str(node["scene"]).lower(), str(node["id"]).lower(), str(node["id"]).lower().split(".")[-1]}
    for d in base.iterdir():
        if d.is_dir() and d.name.lower() in names and any(d.glob("*.wav")):
            return True
    return False


def generate(path_id: str, out_root: Path = PACKS, force: bool = False, paths_root: Path = PATHS, imports_root: Path = IMPORTS) -> list[str]:
    pdir = paths_root / path_id
    run = read_json(pdir / "run.json")
    music_path = pdir / "music.json"
    music = read_json(music_path) if music_path.exists() else {"schema": 1, "nodes": []}
    bpm = int(run["timing"]["bpm"])
    mix = json.loads(json.dumps(DEFAULT_MIX))
    for k, v in music.get("placeholder", {}).items():
        if isinstance(v, dict):
            mix.setdefault(k, {}).update(v)
        else:
            mix[k] = v
    if mix["genre"] not in GENRES:
        raise ContentError(f"placeholder.genre '{mix['genre']}' is not one of {sorted(GENRES)}")
    music["placeholder"] = mix
    entries = {n["id"]: n for n in music.get("nodes", [])}
    done: list[str] = []
    for i, node in enumerate(run["nodes"]):
        pack_id = f"{path_id}_{node['scene']}"
        existing = entries.get(node["id"])
        if existing is not None and not existing.get("temporary", False) and existing.get("audio") != pack_id:
            continue  # the owner's pack is assigned: not ours to touch
        if is_import(out_root / pack_id / "pack.json"):
            continue
        if has_import(path_id, node, imports_root):
            print(f"skipped {node['id']}: it has an import in content/imports/{path_id}/ (no placeholder)")
            continue
        if not force and (out_root / pack_id / "pack.json").exists() and existing is not None:
            continue
        write_scene_pack(out_root, path_id, node["scene"], node["id"], run["path"]["title"], bpm, mix, i)
        entries[node["id"]] = {"id": node["id"], "audio": pack_id, "chart": pack_id, "treatment": "none", "temporary": True}
        done.append(pack_id)
    music["nodes"] = [entries[n["id"]] for n in run["nodes"] if n["id"] in entries]
    write_json(music_path, music, indent=1)
    return done


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--out", help="packs folder (default songs/packs)")
    ap.add_argument("--imports", help="the owner's drops (default content/imports)")
    args = ap.parse_args()
    try:
        done = generate(args.path, Path(args.out) if args.out else PACKS, args.force, imports_root=Path(args.imports) if args.imports else IMPORTS)
    except ContentError as exc:
        print("ERROR", exc)
        return 1
    for d in done:
        p = read_json((Path(args.out) if args.out else PACKS) / d / "pack.json")
        lv = p["levels"]
        print(f"wrote {d}: {p['bpm']} BPM {p['genre']}, loop {p['loop_frames']} frames; RMS drums {lv['drums']['rms_db']} / bass {lv['bass']['rms_db']} / pad {lv['other']['rms_db']} dB, bass under 90 Hz {lv['bass']['sub_share']:.0%}")
    if not done:
        print("nothing to write (every scene has a pack; --force regenerates the placeholders)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
