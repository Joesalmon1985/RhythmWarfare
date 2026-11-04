"""Beat Shaper / Ableton export packs for the continuous story run: scan, check, import.

    python tools/content/beatshaper.py scan   <zip|folder>                    # list the sets found, paired and ambiguous files
    python tools/content/beatshaper.py check  <zip|folder> --set "Lv1 Warehouse" [--variant 1]
                                                                              # verify tempo/timing/cues of one set, write nothing
    python tools/content/beatshaper.py import <zip|folder> --set "Lv1 Warehouse" [--variant 1] --id warehouse
                                                                              # write songs/packs/<id>/ (loops, pack.json, report)
    python tools/content/beatshaper.py validate                               # every pack in songs/packs and content/story/music.json

A *set* is the three files an export writes for one project: `Beat Shaper - <project>-Drums|Bass|Synth` as .wav and .mid. A numbered
copy `... (1)` is another variant of the same project; the three files of a variant share the suffix. Files are grouped by
project name and variant suffix, never by position, so `(1)` and `(2)` stay with their own stems. The sources (a ZIP is only read
in memory, a folder only read) are never modified: decoded, folded and gain-staged copies go to songs/packs/<id>/.

What import does (details in docs/MUSIC_IMPORT.md):

1. Pairs Drums/Bass/Synth WAV with MIDI; reports missing or ambiguous pairs.
2. Tempo. The MIDI headers say 120 BPM but the recordings are not rendered at it. Each candidate *profile* (a recorded tempo
   and how many game beats one source quarter is) is tried; the one the drum transients agree with (within 0.25 BPM, every hit within
   `max_error_ms`) is used, the audio is never stretched, and bass note changes are checked against the bass MIDI. If no profile
   verifies the import stops and says so. Profiles: `beat_shaper_87x2` (verified on the Lv1 Warehouse export: 87 BPM, two game
   beats per source quarter) and `beat_shaper_174x1` (recorded at the game tempo: Lv2 Alien Spaceship).
3. Loops. Every stem becomes one WAV of exactly the phrase (MIDI length in game beats) with the release tail folded onto the start.
4. Cues. Kick and snare notes from the Drum MIDI (notes configurable), bass notes from the Bass MIDI as holds (pads by pitch), thinned
   per difficulty tier by `thin()`; every kept cue keeps its source timing.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import re
import sys
import zipfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mido  # noqa: E402

from chart import check_cues, load_rules, pitch_pads  # noqa: E402
from common import PPQ, ROOT, SAMPLE_RATE, ContentError, read_json, write_json, write_wav  # noqa: E402
from import_recorded import db, envelope, fold_loop, onset_near, read_float_wav_bytes  # noqa: E402

PACKS = ROOT / "songs" / "packs"
MUSIC_JSON = ROOT / "content" / "story" / "music.json"
BPM = 174
PARTS = ("Drums", "Bass", "Synth")
NAME_RE = re.compile(r"^(?:Beat Shaper - )?(?P<project>.+)-(?P<part>Drums|Bass|Synth)(?: \((?P<variant>\d+)\))?\.(?P<ext>wav|mid)$")
PROFILES = {
    "beat_shaper_87x2": {"source_bpm": 87.0, "scale": 2, "verified_on": "Lv1 Warehouse"},
    "beat_shaper_174x1": {"source_bpm": 174.0, "scale": 1, "verified_on": "Lv2 Alien Spaceship"},
}
TIER_MIN_GAP = {"drums": {1: 1.0, 2: 0.75, 3: 0.5, 4: 0.5}, "bass": {1: 2.0, 2: 1.5, 3: 1.0, 4: 0.75}}  # beats between two cue times of a family group, per difficulty tier
PHASE_BEATS = 64
BLOCK_BEATS = 16
CUE_SPAN_BEATS = 12.0  # cues may sit in beats 0..12 of a block; the last four beats are cue-free


# --- reading an export (ZIP or folder) ----------------------------------------------------------------------------

class Source:
    """A folder or ZIP of exports: names -> bytes, read only."""

    def __init__(self, path: Path):
        self.path = path
        self.files: dict[str, bytes] = {}
        if path.is_dir():
            for p in sorted(path.iterdir()):
                if p.suffix.lower() in (".wav", ".mid"):
                    self.files[p.name] = p.read_bytes()
        elif zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                for n in sorted(z.namelist()):
                    if n.lower().endswith((".wav", ".mid")) and not n.endswith("/"):
                        self.files[Path(n).name] = z.read(n)
        else:
            raise ContentError(f"{path}: not a folder or a ZIP")

    def groups(self) -> tuple[dict, list[str]]:
        """{(project, variant): {part: {ext: name}}} and the names that match no export pattern."""
        out: dict = {}
        odd: list[str] = []
        for name in self.files:
            m = NAME_RE.match(name)
            if not m:
                odd.append(name)
                continue
            key = (m["project"], int(m["variant"]) if m["variant"] else 0)
            out.setdefault(key, {}).setdefault(m["part"], {})[m["ext"]] = name
        return out, odd


def set_status(parts: dict) -> list[str]:
    miss = []
    for p in PARTS:
        for ext in ("wav", "mid"):
            if ext not in parts.get(p, {}):
                miss.append(f"{p}.{ext}")
    return miss


def slug(project: str, variant: int) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", project.lower()).strip("_")
    return s + (f"_v{variant}" if variant else "")


def read_midi_bytes(data: bytes) -> dict:
    mid = mido.MidiFile(file=io.BytesIO(data))
    notes, tempos = [], []
    for tr in mid.tracks:
        t = 0
        on: dict = {}
        for msg in tr:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                on.setdefault((msg.channel, msg.note), []).append((t, msg.velocity))
            elif msg.type in ("note_off", "note_on") and on.get((msg.channel, msg.note)):
                s, v = on[(msg.channel, msg.note)].pop(0)
                notes.append({"beat": s / mid.ticks_per_beat, "dur": (t - s) / mid.ticks_per_beat, "pitch": msg.note, "velocity": v})
            elif msg.type == "set_tempo":
                tempos.append(mido.tempo2bpm(msg.tempo))
    notes.sort(key=lambda n: (n["beat"], n["pitch"]))
    end = max((n["beat"] + n["dur"] for n in notes), default=0.0)
    return {"notes": notes, "header_bpm": tempos[0] if tempos else None, "end_beat": end}


# --- timing -------------------------------------------------------------------------------------------------------

def fit_drums(mono: np.ndarray, hits_beats: list[float], bpm: float, tol_s: float) -> dict | None:
    env, step = envelope(mono, SAMPLE_RATE)
    spb = 60.0 / bpm
    pairs = []
    for b in hits_beats:
        o = onset_near(env, step, b * spb, 0.04)
        if o is not None:
            pairs.append((b, o))
    if len(pairs) < 0.8 * len(hits_beats) or len(pairs) < 4:
        return None
    bs = np.array([p[0] for p in pairs])
    ts = np.array([p[1] for p in pairs])
    slope, icpt = np.polyfit(bs, ts, 1)
    err = ts - bs * spb
    return {"hits": len(hits_beats), "matched": len(pairs), "fitted_bpm": round(float(60.0 / slope), 3), "fitted_offset_ms": round(float(icpt * 1000), 2),
            "max_abs_ms": round(float(np.abs(err).max() * 1000), 2), "mean_ms": round(float(err.mean() * 1000), 2)}


def check_bass(mono: np.ndarray, notes: list[dict], bpm: float) -> list[dict]:
    """Note changes of the (wobbling) bass show as jumps in the low spectrum; compare 40 ms before and after candidate times."""
    rate = SAMPLE_RATE
    win = int(0.04 * rate)
    hann = np.hanning(win)
    band = (np.fft.rfftfreq(8 * win, 1 / rate) > 40) & (np.fft.rfftfreq(8 * win, 1 / rate) < 400)

    def spec(end_s: float) -> np.ndarray:
        i = int(round(end_s * rate)) - win
        if i < 0 or i + win > len(mono):
            return np.zeros(int(band.sum()))
        s = np.abs(np.fft.rfft(mono[i:i + win] * hann, 8 * win))[band]
        return s / (np.linalg.norm(s) + 1e-9)

    rows = []
    first = np.nonzero(np.abs(mono) > 1e-3)[0]
    prev = None
    for n in notes:
        t = n["beat"] * 60.0 / bpm
        if n["beat"] == 0:
            e = float(first[0]) / rate * 1000 if len(first) else None
            rows.append({"beat": 0.0, "pitch": n["pitch"], "error_ms": None if e is None else round(e, 1), "how": "first sound in the file"})
        elif prev is not None and n["pitch"] == prev["pitch"] and abs(n["beat"] - (prev["beat"] + prev["dur"])) < 0.01:
            rows.append({"beat": n["beat"], "pitch": n["pitch"], "error_ms": None, "how": "same pitch legato: not measurable"})
        else:
            gaps = [abs(n["beat"] - o["beat"]) * 60.0 / bpm for o in notes if o is not n and o["beat"] != n["beat"]]
            half = min(0.08, 0.4 * min(gaps)) if gaps else 0.08  # fast lines: stay inside the neighbouring notes
            cand = np.arange(max(t - half, 0.05), t + half, 0.002)
            d = [1.0 - float(np.dot(spec(c), spec(c + 0.04))) for c in cand]
            j = int(np.argmax(d))
            rows.append({"beat": n["beat"], "pitch": n["pitch"], "error_ms": round((float(cand[j]) - t) * 1000, 1), "how": "largest spectral change near the note start"})
        prev = n
    return rows


def detect_profile(drums_mono: np.ndarray, drum_notes: list[dict], tol_ms: float, forced: str | None = None) -> tuple[str, dict, dict]:
    """`drum_notes` are the notes that become cues (kick and snare): hats and toms have soft transients that the detector cannot place, so they
    do not decide the tempo."""
    hits = sorted({n["beat"] for n in drum_notes})
    tried = {}
    for name, p in PROFILES.items():
        if forced and name != forced:
            continue
        fit = fit_drums(drums_mono, hits, p["source_bpm"], tol_ms / 1000.0)
        tried[name] = fit
        if fit and abs(fit["fitted_bpm"] - p["source_bpm"]) <= 0.25 and fit["max_abs_ms"] <= tol_ms:
            return name, p, fit
    raise ContentError("no tempo profile verifies against the drum recording (" + json.dumps(tried) + "); the tempo override is only applied to a verified profile, "
                       "add one to PROFILES after measuring the export")


# --- cues ---------------------------------------------------------------------------------------------------------

def thin(cues: list[list], tier: int, group: str, beat_ticks: int = PPQ) -> list[list]:
    """Pick the cues of a difficulty tier from the full list [tick, duration, pad, family]. Whole-beat cues are preferred (low syncopation), a chord
    (several pads on one tick) is kept or dropped as one, and consecutive kept times are at least TIER_MIN_GAP[group][tier] beats apart. Selected cues
    keep their source ticks; a hold is shortened to end 240 ticks before the next cue (a tap when that leaves less than a hold)."""
    gap = TIER_MIN_GAP[group].get(tier, 0.5) * beat_ticks
    slots: dict[int, list] = {}
    for c in cues:
        slots.setdefault(c[0], []).append(c)

    def prio(tick: int) -> tuple:
        frac = (tick % beat_ticks) / beat_ticks
        return (0 if frac == 0 else (1 if abs(frac - 0.5) < 1e-6 else 2), tick)

    keep: list[int] = []
    for tick in sorted(slots, key=prio):
        if all(abs(tick - k) >= gap for k in keep):
            keep.append(tick)
    keep.sort()
    out = []
    for i, t in enumerate(keep):
        nxt = keep[i + 1] if i + 1 < len(keep) else None
        for c in slots[t]:
            c = list(c)
            if c[1] and nxt is not None and t + c[1] > nxt - 240:
                c[1] = max(0, nxt - 240 - t)
                if c[1] < 480:
                    c[1] = 0
            out.append(c)
    return out


def build_cues(drum_notes: list[dict], bass_notes: list[dict], scale: int, kick: set, snare: set, rules: dict, phrase_beats: int) -> dict:
    ticks = PPQ * scale
    drums: list[list] = []
    for n in drum_notes:
        tick = int(round(n["beat"] * ticks))
        if n["pitch"] in kick:
            drums.append([tick, 0, 1, "kick"])
        elif n["pitch"] in snare:
            drums.append([tick, 0, 4, "snare"])
    pads = pitch_pads(n["pitch"] for n in bass_notes) if bass_notes else {}
    bass: list[list] = []
    hold_min = rules["chart"]["hold_min_ticks"]
    block = BLOCK_BEATS * PPQ
    for n in sorted(bass_notes, key=lambda n: n["beat"]):
        tick, dur = int(round(n["beat"] * ticks)), int(round(n["dur"] * ticks))
        end = (tick // block + 1) * block  # a hold ends inside its 16-beat block; the sound rings on
        dur = min(dur, end - tick)
        bass.append([tick, dur if dur >= hold_min else 0, pads[n["pitch"]], "bass"])
    return {"drums": sorted(drums), "bass": sorted(bass)}


def tier_cues(cues: dict, rules: dict, phrase_ticks: int) -> tuple[dict, list[str]]:
    out: dict = {}
    problems: list[str] = []
    for tier in (1, 2, 3, 4):
        d = thin(cues["drums"], tier, "drums")
        b = thin(cues["bass"], tier, "bass")
        # a cue-free guard at the end of every 16-beat block (hold tails and hit windows resolve before focus switches)
        out[str(tier)] = {"drums": d, "bass": b}
        for lab, lst in (("drums", d), ("bass", b)):
            for msg in check_cues([c[:3] for c in lst], rules):
                problems.append(f"tier {tier} {lab}: {msg}")
    return out, problems


# --- import -------------------------------------------------------------------------------------------------------

def load_set(src: Source, project: str, variant: int):
    groups, _ = src.groups()
    parts = groups.get((project, variant))
    if not parts:
        have = sorted({f"{p}" + (f" ({v})" if v else "") for p, v in groups})
        raise ContentError(f"no set '{project}' variant {variant or 'unsuffixed'} in {src.path.name}; found: {', '.join(have)}")
    miss = set_status(parts)
    if miss:
        raise ContentError(f"set '{project}' ({variant}) is missing {', '.join(miss)}")
    audio, midi = {}, {}
    for p in PARTS:
        frames, rate = read_float_wav_bytes(src.files[parts[p]["wav"]], parts[p]["wav"])
        if rate != SAMPLE_RATE:
            raise ContentError(f"{parts[p]['wav']}: {rate} Hz; imports take {SAMPLE_RATE} Hz so the audio is never resampled or stretched")
        if frames.shape[1] == 1:
            frames = np.repeat(frames, 2, axis=1)
        audio[p] = frames
        midi[p] = read_midi_bytes(src.files[parts[p]["mid"]])
    return parts, audio, midi


def analyse(src: Source, project: str, variant: int, opts: dict) -> dict:
    parts, audio, midi = load_set(src, project, variant)
    mono = {p: audio[p].mean(axis=1) for p in PARTS}
    tol = float(opts.get("max_error_ms", 12.0))
    kick = set(opts.get("kick_notes", [36]))
    snare = set(opts.get("snare_notes", [38, 40]))
    dn = [n for n in midi["Drums"]["notes"] if n["pitch"] in kick | snare]
    if not dn:
        pitches = sorted({n["pitch"] for n in midi["Drums"]["notes"]})
        raise ContentError(f"the Drum MIDI has no kick {sorted(kick)} or snare {sorted(snare)} notes (it has {pitches}); pass --kick/--snare notes for this set")
    name, prof, fit = detect_profile(mono["Drums"], dn, tol, opts.get("profile"))
    scale = prof["scale"]
    phrase_beats = int(round(midi["Drums"]["end_beat"] * scale))
    if phrase_beats not in (16, 32, 64):
        raise ContentError(f"the phrase is {phrase_beats} game beats; packs take 16, 32 or 64")
    loop_frames = int(round(phrase_beats * 60.0 / BPM * SAMPLE_RATE))
    bass_rows = check_bass(mono["Bass"], midi["Bass"]["notes"], prof["source_bpm"])
    meas = [r for r in bass_rows if r["error_ms"] is not None]
    bad = [r for r in meas if abs(r["error_ms"]) > max(tol, 12.0)]
    warnings = []
    med = float(np.median([abs(r["error_ms"]) for r in meas])) if meas else 0.0
    if bad and med > max(tol, 12.0):
        raise ContentError("the bass note changes are out of line with the bass MIDI at this tempo (median error %.1f ms): " % med + json.dumps(bad))
    if bad:
        warnings.append("bass: some note changes could not be placed within the limit (the detector reads a wobbling bass loosely): " + json.dumps(bad))
    rules = load_rules()
    cues = build_cues(dn, midi["Bass"]["notes"], scale, kick, snare, rules, phrase_beats)
    tiers, problems = tier_cues(cues, rules, phrase_beats * PPQ)
    return {"parts": parts, "audio": audio, "midi": midi, "profile": name, "fit": fit, "bass": bass_rows, "phrase_beats": phrase_beats,
            "loop_frames": loop_frames, "warnings": warnings, "cues": cues, "tiers": tiers, "problems": problems, "scale": scale,
            "kick": sorted(kick), "snare": sorted(snare), "header_bpm": midi["Drums"]["header_bpm"]}


def write_pack(src: Source, project: str, variant: int, pack_id: str, a: dict, gains: dict, label: str, out_root: Path = PACKS) -> Path:
    out = out_root / pack_id
    loops = {}
    for stem, part in (("drums", "Drums"), ("bass", "Bass"), ("other", "Synth")):
        folded, info = fold_loop(a["audio"][part].astype(np.float64) * 10.0 ** (gains[stem] / 20.0), a["loop_frames"])
        peak = float(np.abs(folded).max())
        if peak >= 0.999:
            raise ContentError(f"{stem}: {gains[stem]:+.1f} dB clips")
        info.update({"gain_db": gains[stem], "peak_db": round(db(peak), 2), "rms_db": round(db(float(np.sqrt((folded.astype(np.float64) ** 2).mean()))), 2),
                     "source_seconds": round(len(a["audio"][part]) / SAMPLE_RATE, 4), "source_file": a["parts"][part]["wav"]})
        write_wav(out / "loops" / f"{stem}.wav", folded)
        loops[stem] = info
    pack = {"schema": 1, "id": pack_id, "label": label, "bpm": BPM, "phrase_beats": a["phrase_beats"], "loop_frames": a["loop_frames"],
            "profile": a["profile"], "stems": {k: f"loops/{k}.wav" for k in loops}, "loops": loops,
            "kick_notes": a["kick"], "snare_notes": a["snare"], "tiers": a["tiers"],
            "source": {"project": project, "variant": variant, "files": a["parts"]}}
    write_json(out / "pack.json", pack, indent=1)
    report = {"timing": {"header_bpm": a["header_bpm"], "profile": a["profile"], "drum_fit": a["fit"], "bass": a["bass"]}, "loops": loops,
              "cue_counts": {t: {k: len(v) for k, v in d.items()} for t, d in a["tiers"].items()}, "chart_problems": a["problems"]}
    write_json(out / "timing_report.json", report, indent=1)
    return out


def describe(a: dict, project: str, variant: int) -> str:
    f = a["fit"]
    lines = [f"{project}" + (f" ({variant})" if variant else ""),
             f"  header {a['header_bpm']} BPM; profile {a['profile']}: drums fit {f['fitted_bpm']} BPM, {f['matched']}/{f['hits']} hits, max {f['max_abs_ms']} ms, offset {f['fitted_offset_ms']} ms",
             f"  phrase {a['phrase_beats']} game beats, loop {a['loop_frames']} frames ({a['loop_frames'] / SAMPLE_RATE:.4f} s)",
             "  bass: " + ", ".join(f"beat {r['beat']:g} {('%+.1f ms' % r['error_ms']) if r['error_ms'] is not None else r['how']}" for r in a["bass"])]
    for t, d in a["tiers"].items():
        lines.append(f"  tier {t}: {len(d['drums'])} drum cues, {len(d['bass'])} bass cues")
    for w in a["warnings"]:
        lines.append("  WARNING " + w)
    for p in a["problems"]:
        lines.append("  CHART PROBLEM " + p)
    return "\n".join(lines)


# --- validate -----------------------------------------------------------------------------------------------------

def validate(packs_dir: Path = PACKS, music_path: Path = MUSIC_JSON) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []
    packs: dict = {}
    seen = set()
    for pj in sorted(packs_dir.glob("*/pack.json")):
        p = read_json(pj)
        pid = p.get("id")
        if pid != pj.parent.name:
            errors.append(f"{pj}: id '{pid}' must equal the folder name")
        if pid in seen:
            errors.append(f"duplicate pack id {pid}")
        seen.add(pid)
        packs[pid] = p
        for k, rel_ in p["stems"].items():
            f = pj.parent / rel_
            if not f.exists():
                errors.append(f"{pid}: stem {k} file {rel_} is missing")
                continue
            import wave
            with wave.open(str(f), "rb") as w:
                if w.getnframes() != p["loop_frames"] or w.getframerate() != SAMPLE_RATE:
                    errors.append(f"{pid}: {k} is {w.getnframes()} frames at {w.getframerate()} Hz, the loop is {p['loop_frames']} at {SAMPLE_RATE}")
        if p["phrase_beats"] not in (16, 32, 64) or PHASE_BEATS % p["phrase_beats"]:
            errors.append(f"{pid}: phrase of {p['phrase_beats']} beats does not tile a {PHASE_BEATS}-beat phase")
        phrase_ticks = p["phrase_beats"] * PPQ
        guarded: dict = {}
        for t, d in p["tiers"].items():
            for fam in ("drums", "bass"):
                for c in d[fam]:
                    if not (0 <= c[0] < phrase_ticks) or c[0] + c[1] > phrase_ticks + BLOCK_BEATS * PPQ or c[2] not in (1, 2, 3, 4):
                        errors.append(f"{pid}: tier {t} {fam} cue {c} is outside the phrase or on a bad pad")
                # playable range: cues in the last 4 beats of a 16-beat block are not charted (the guard), counted here
                guard = [c for c in d[fam] if (c[0] % (BLOCK_BEATS * PPQ)) / PPQ > CUE_SPAN_BEATS + 1e-6]
                if guard:
                    guarded[(t, fam)] = len(guard)
        notes.append(f"pack {pid}: {p['label']}, {p['phrase_beats']}-beat phrase, profile {p['profile']}; cues in the block guard (not charted): " + (", ".join(f"tier {t} {f} {n}" for (t, f), n in sorted(guarded.items())) or "none"))
    if music_path.exists():
        m = read_json(music_path)
        ids = [n["id"] for n in m["nodes"]]
        if len(ids) != len(set(ids)):
            errors.append("music.json: duplicate node ids")
        for n in m["nodes"]:
            for key in ("audio", "chart"):
                if n[key] not in packs:
                    errors.append(f"music.json: node {n['id']} {key} pack '{n[key]}' does not exist (packs: {', '.join(sorted(packs))})")
            if n["audio"] in packs and n["chart"] in packs and packs[n["audio"]]["phrase_beats"] != packs[n["chart"]]["phrase_beats"]:
                errors.append(f"music.json: node {n['id']} audio '{n['audio']}' and chart '{n['chart']}' have different phrase lengths")
        notes.append(f"music.json: {len(ids)} nodes assigned")
    else:
        errors.append("content/story/music.json is missing")
    return errors, notes


# --- cli ----------------------------------------------------------------------------------------------------------

def cmd_scan(args) -> int:
    src = Source(Path(args.source))
    groups, odd = src.groups()
    print(f"{src.path}: {len(src.files)} files, {len(groups)} sets")
    for (project, variant), parts in sorted(groups.items()):
        miss = set_status(parts)
        print(f"  {slug(project, variant):28s} {project}" + (f" ({variant})" if variant else "") + ("  MISSING " + ", ".join(miss) if miss else "  paired"))
    for o in odd:
        print("  not an export file name:", o)
    return 1 if odd or any(set_status(p) for p in groups.values()) else 0


def _opts(args) -> dict:
    o: dict = {}
    if args.kick:
        o["kick_notes"] = [int(x) for x in args.kick.split(",")]
    if args.snare:
        o["snare_notes"] = [int(x) for x in args.snare.split(",")]
    if args.profile:
        o["profile"] = args.profile
    return o


def cmd_check(args) -> int:
    src = Source(Path(args.source))
    a = analyse(src, args.set, args.variant, _opts(args))
    print(describe(a, args.set, args.variant))
    return 1 if a["problems"] else 0


def cmd_import(args) -> int:
    src = Source(Path(args.source))
    a = analyse(src, args.set, args.variant, _opts(args))
    print(describe(a, args.set, args.variant))
    if a["problems"]:
        return 1
    gains = {"drums": args.drums_db, "bass": args.bass_db, "other": args.synth_db}
    out = write_pack(src, args.set, args.variant, args.id, a, gains, args.label or f"{args.set}" + (f" ({args.variant})" if args.variant else ""))
    print("written", out.relative_to(ROOT).as_posix())
    return 0


def cmd_validate(args) -> int:
    errors, notes = validate()
    for n in notes:
        print(n)
    for e in errors:
        print("ERROR", e)
    print("OK" if not errors else f"{len(errors)} problem(s)")
    return 1 if errors else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("source")
    for name in ("check", "import"):
        c = sub.add_parser(name)
        c.add_argument("source")
        c.add_argument("--set", required=True, help="project name as in the file names, e.g. 'Lv1 Warehouse'")
        c.add_argument("--variant", type=int, default=0, help="the (n) suffix; 0 = unsuffixed")
        c.add_argument("--kick", help="kick MIDI notes, comma separated (default 36)")
        c.add_argument("--snare", help="snare MIDI notes (default 38,40)")
        c.add_argument("--profile", choices=sorted(PROFILES), help="force one tempo profile (it must still verify)")
        if name == "import":
            c.add_argument("--id", required=True, help="stable pack id (folder under songs/packs)")
            c.add_argument("--label")
            c.add_argument("--drums-db", type=float, default=0.0)
            c.add_argument("--bass-db", type=float, default=3.0)
            c.add_argument("--synth-db", type=float, default=10.0)
    sub.add_parser("validate")
    args = ap.parse_args()
    try:
        return {"scan": cmd_scan, "check": cmd_check, "import": cmd_import, "validate": cmd_validate}[args.cmd](args)
    except ContentError as exc:
        print(f"ERROR {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
