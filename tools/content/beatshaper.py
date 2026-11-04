"""Beat Shaper / Ableton export packs for the continuous story run: scan, check, import.

    python tools/content/beatshaper.py scan   <zip|folder>                    # list the sets found, paired and ambiguous files
    python tools/content/beatshaper.py check  <zip|folder> --set "Lv1 Warehouse" [--variant 1]
                                                                              # verify tempo/timing/cues of one set, write nothing
    python tools/content/beatshaper.py import <zip|folder> --set "Lv1 Warehouse" [--variant 1] --id warehouse
                                                                              # write songs/packs/<id>/ (loops, pack.json, report)
    python tools/content/beatshaper.py survey <zip|folder>                    # every set: what was measured, decided automatically, or why it is refused
    python tools/content/beatshaper.py validate                               # every pack in songs/packs and content/story/music.json
    python tools/content/beatshaper.py apply  <zip|folder> --node ward --set "Lv3 Ward" --id lv3_ward [--audio-only]
                                                                              # import one set and give it to a level (music.json), no code changes
    python tools/content/beatshaper.py assign --node ward --audio lv3_ward    # re-point a level at packs that are already imported

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

try:  # mido is optional: without it a small built-in reader parses the exports' MIDI (type 0/1 files, note on/off, set_tempo)
    import mido  # noqa: E402
except ImportError:  # pragma: no cover - depends on the machine
    mido = None

from chart import check_cues, load_rules, pitch_pads  # noqa: E402
from common import PPQ, ROOT, SAMPLE_RATE, ContentError, read_json, write_json, write_wav  # noqa: E402
from import_recorded import db, envelope, fold_loop, onset_near, read_float_wav_bytes  # noqa: E402

PACKS = ROOT / "songs" / "packs"
MUSIC_JSON = ROOT / "content" / "story" / "music.json"
RUN_JSON = ROOT / "content" / "run" / "run.json"
TRIAL_JSON = ROOT / "content" / "trial" / "passages.json"
BPM = 174
PARTS = ("Drums", "Bass", "Synth")
NAME_RE = re.compile(r"^(?:Beat Shaper - )?(?P<project>.+)-(?P<part>Drums|Bass|Synth)(?: \((?P<variant>\d+)\))?\.(?P<ext>wav|mid)$")
PROFILES = {
    "beat_shaper_87x2": {"source_bpm": 87.0, "scale": 2, "verified_on": "Lv1 Warehouse"},
    "beat_shaper_174x1": {"source_bpm": 174.0, "scale": 1, "verified_on": "Lv2 Alien Spaceship"},
}
# Difficulty tiers are nested: tier 1 is the sparse base set (cues at least BASE_GAP beats apart, whole beats first); tier 4 is everything the chart rules
# allow (FULL_GAP, 0.5 beat); tier 2 and 3 add 1/3 and 2/3 of the cues that tier 4 has over tier 1 (every k-th extra cue in time order). Every tier is a
# subset of the next, so density rises with depth in every pack whose MIDI has syncopation to give (docs/CONTINUOUS_RUN.md, "Difficulty").
BASE_GAP = {"drums": 1.0, "bass": 2.0}   # beats between two cue times of a family group at tier 1
FULL_GAP = 0.5                           # the chart rules' floor between cues (480 ticks): tier 4
TIER_SHARE = {1: 0.0, 2: 1.0 / 3.0, 3: 2.0 / 3.0, 4: 1.0}  # share of the extra cues (tier 4 over tier 1) a tier keeps
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


def fatal_missing(parts: dict) -> list[str]:
    """What stops an import: everything but the Synth files (a missing Synth.wav is replaced by silence, Synth.mid is never read)."""
    return [m for m in set_status(parts) if not m.startswith("Synth")]


def slug(project: str, variant: int) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", project.lower()).strip("_")
    return s + (f"_v{variant}" if variant else "")


def _vlq(data: bytes, i: int) -> tuple[int, int]:
    v = 0
    while True:
        b = data[i]
        i += 1
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            return v, i


def _read_midi_builtin(data: bytes) -> dict:
    """Minimal Standard MIDI File reader used when mido is not installed. Same result as the mido path."""
    if data[:4] != b"MThd":
        raise ContentError("not a MIDI file (no MThd header)")
    ntrk, division = int.from_bytes(data[10:12], "big"), int.from_bytes(data[12:14], "big")
    if division & 0x8000:
        raise ContentError("SMPTE time division is not supported")
    pos = 8 + int.from_bytes(data[4:8], "big")
    notes, tempos = [], []
    for _ in range(ntrk):
        if data[pos:pos + 4] != b"MTrk":
            break
        end = pos + 8 + int.from_bytes(data[pos + 4:pos + 8], "big")
        i, t, status = pos + 8, 0, 0
        on: dict = {}
        while i < end:
            d, i = _vlq(data, i)
            t += d
            if data[i] & 0x80:
                status = data[i]
                i += 1
            if status == 0xFF:
                typ = data[i]
                ln, i = _vlq(data, i + 1)
                if typ == 0x51 and ln == 3:
                    tempos.append(60000000.0 / int.from_bytes(data[i:i + 3], "big"))
                i += ln
            elif status in (0xF0, 0xF7):
                ln, i = _vlq(data, i)
                i += ln
            else:
                kind, ch = status & 0xF0, status & 0x0F
                n_args = 1 if kind in (0xC0, 0xD0) else 2
                a = data[i:i + n_args]
                i += n_args
                if kind == 0x90 and a[1] > 0:
                    on.setdefault((ch, a[0]), []).append((t, a[1]))
                elif kind in (0x80, 0x90) and on.get((ch, a[0])):
                    s0, v = on[(ch, a[0])].pop(0)
                    notes.append({"beat": s0 / division, "dur": (t - s0) / division, "pitch": a[0], "velocity": v})
        pos = end
    notes.sort(key=lambda n: (n["beat"], n["pitch"]))
    return {"notes": notes, "header_bpm": tempos[0] if tempos else None, "end_beat": max((n["beat"] + n["dur"] for n in notes), default=0.0)}


def read_midi_bytes(data: bytes) -> dict:
    if mido is None:
        return _read_midi_builtin(data)
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
    res = np.abs(ts - (bs * slope + icpt))  # distance from the fitted line: a global offset is not an error
    within = float((res <= tol_s).mean())
    worst = sorted(zip(bs.tolist(), (ts - bs * spb).tolist()), key=lambda x: -abs(x[1] - float(np.median(err))))[:3]
    return {"hits": len(hits_beats), "matched": len(pairs), "fitted_bpm": round(float(60.0 / slope), 3), "fitted_offset_ms": round(float(icpt * 1000), 2),
            "max_abs_ms": round(float(np.abs(err).max() * 1000), 2), "mean_ms": round(float(err.mean() * 1000), 2),
            "median_ms": round(float(np.median(err) * 1000), 2), "within_limit": round(within, 3),
            "worst_hits": [{"beat": round(b, 3), "error_ms": round(e * 1000, 1)} for b, e in worst]}


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


LOOSE_MIN_WITHIN = 0.85   # a profile also verifies when this share of the cue hits sit within the limit of the fitted line ...
LOOSE_MAX_MS = 40.0        # ... and no hit is further than this from where the MIDI puts it (a soft or ghosted snare transient)


def detect_profile(drums_mono: np.ndarray, drum_notes: list[dict], tol_ms: float, forced: str | None = None, auto_mapped: bool = False) -> tuple[str, dict, dict, list[dict]]:
    """`drum_notes` are the notes that become cues (kick and snare): hats and toms have soft transients that the detector cannot place, so they
    do not decide the tempo. A profile verifies *strictly* (every hit inside the limit) or *loosely* (the fitted tempo is within 0.25 BPM, at
    least 85% of the hits are inside the limit and none is further than 40 ms: single soft transients are reported, not fatal). The best
    verifying profile wins (strict before loose, then the smaller typical error). When the kick/snare notes were chosen automatically (claps and
    toms have softer attacks) the loose share is 70% but the fitted tempo must be within 0.1 BPM of the profile. Returns (name, profile, fit, every profile tried)."""
    min_within, bpm_tol = (0.70, 0.10) if auto_mapped else (LOOSE_MIN_WITHIN, 0.25)
    hits = sorted({n["beat"] for n in drum_notes})
    tried: list[dict] = []
    good = []
    for name, p in PROFILES.items():
        if forced and name != forced:
            continue
        fit = fit_drums(drums_mono, hits, p["source_bpm"], tol_ms / 1000.0)
        row = {"profile": name, "fit": fit, "verified": None}
        tried.append(row)
        if not fit or abs(fit["fitted_bpm"] - p["source_bpm"]) > (0.25 if fit and fit["max_abs_ms"] <= tol_ms else bpm_tol):
            continue
        if fit["max_abs_ms"] <= tol_ms:
            row["verified"] = "strict"
        elif fit["within_limit"] >= min_within and fit["max_abs_ms"] <= LOOSE_MAX_MS:
            row["verified"] = "loose"
        else:
            continue
        good.append((0 if row["verified"] == "strict" else 1, fit["max_abs_ms"] if row["verified"] == "strict" else (1.0 - fit["within_limit"], fit["mean_ms"]), name, p, fit, row))
    if good:
        good.sort(key=lambda g: (g[0], g[1] if isinstance(g[1], tuple) else (0.0, g[1])))
        _k, _m, name, p, fit, _row = good[0]
        return name, p, fit, tried
    raise ContentError("no tempo profile verifies against the drum recording (" + json.dumps([{"profile": t["profile"], **(t["fit"] or {"fit": None})} for t in tried]) + "); "
                       "the tempo is never assumed. Either the render is at another tempo (add a profile to PROFILES after measuring the export) or the kick/snare notes "
                       "in the drum MIDI are not the ones sounding in the recording (pass --kick/--snare)")


# --- cues ---------------------------------------------------------------------------------------------------------

def _greedy(slots: dict, gap: float, beat_ticks: int) -> list[int]:
    def prio(tick: int) -> tuple:
        frac = (tick % beat_ticks) / beat_ticks
        return (0 if frac == 0 else (1 if abs(frac - 0.5) < 1e-6 else 2), tick)

    keep: list[int] = []
    g = gap * beat_ticks
    for tick in sorted(slots, key=prio):  # whole beats first (low syncopation), then half beats, then the rest
        if all(abs(tick - k) >= g for k in keep):
            keep.append(tick)
    return sorted(keep)


def thin(cues: list[list], tier: int, group: str, beat_ticks: int = PPQ) -> list[list]:
    """Pick the cues of a difficulty tier from the full list [tick, duration, pad, family]. The base set (tier 1) keeps whole-beat cues first, at least
    BASE_GAP[group] beats apart; tier 4 keeps everything FULL_GAP apart; tiers 2 and 3 add TIER_SHARE of the extra cues between the two (every k-th, in
    time order), so each tier contains the one below. A chord (several pads on one tick) is kept or dropped as one. Selected cues keep their source
    ticks; a hold is shortened to end 240 ticks before the next cue (a tap when that leaves less than a hold)."""
    slots: dict[int, list] = {}
    for c in cues:
        slots.setdefault(c[0], []).append(c)
    base = _greedy(slots, BASE_GAP[group], beat_ticks)
    full = _greedy(slots, FULL_GAP, beat_ticks)
    share = TIER_SHARE.get(tier, 1.0)
    extras = [t for t in full if t not in set(base)]
    chosen = [t for i, t in enumerate(extras) if int((i + 1) * share + 1e-9) > int(i * share + 1e-9)]
    chosen = [t for t in chosen if all(abs(t - b) >= FULL_GAP * beat_ticks for b in base)]  # never closer to a base cue than the chart rules allow
    keep = sorted(set(base) | set(chosen))
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

def drum_note_choice(notes: list[dict], opts: dict) -> tuple[set, set, dict]:
    """Which MIDI notes are the kick and the snare. Explicit --kick/--snare always win. Otherwise 36 is the kick and 38/40 the snare; when none of
    those are in the drum MIDI the set is mapped by what it plays: hats (42, 44, 46) and cymbals (49 and up) are never cues, the most common
    note of the lower half of the remaining distinct pitches is the kick and the most common of the upper half the snare. A set with a lone
    candidate note charts it as the kick if it is below 38 and as the snare otherwise. Returns (kick, snare, how)."""
    counts: dict[int, int] = {}
    for n in notes:
        counts[n["pitch"]] = counts.get(n["pitch"], 0) + 1
    explicit_k, explicit_s = opts.get("kick_notes"), opts.get("snare_notes")
    if explicit_k or explicit_s:
        return set(explicit_k or [36]), set(explicit_s or [38, 40]), {"mode": "explicit", "counts": counts, "why": "--kick/--snare given"}
    kick, snare = {36}, {38, 40}
    if any(p in kick | snare for p in counts):
        present_k, present_s = sorted(kick & set(counts)), sorted(snare & set(counts))
        why = "the standard notes: kick 36, snare 38/40" + ("" if present_k else "; no kick note (36) in this set, the chart has snare cues only") + ("" if present_s else "; no snare note (38/40) in this set, the chart has kick cues only")
        return set(kick), set(snare), {"mode": "standard", "counts": counts, "why": why}
    cand = {p: c for p, c in counts.items() if p not in (42, 44, 46) and p < 49}
    if not cand:
        cand = dict(counts)
    ordered = sorted(cand)
    if len(ordered) == 1:
        only = ordered[0]
        k, sn = ({only}, set()) if only < 38 else (set(), {only})
        return k, sn, {"mode": "auto", "counts": counts, "why": f"only one candidate note ({only}); hats and cymbals are not cues"}
    half = len(ordered) // 2
    low, high = ordered[:half], ordered[half:]
    kp = max(low, key=lambda p: (cand[p], -p))
    sp = max(high, key=lambda p: (cand[p], -p))
    return {kp}, {sp}, {"mode": "auto", "counts": counts, "why": f"none of 36/38/40 in the drum MIDI (notes {dict(sorted(counts.items()))}); hats 42/44/46 and cymbals skipped; "
                      f"most common low note {kp} = kick, most common mid note {sp} = snare"}


def load_set(src: Source, project: str, variant: int, report: dict | None = None):
    """Reads a set. The Drums and Bass WAV+MIDI are needed (the tempo comes from the drums, the cues from both MIDI files); a missing Synth is
    replaced by silence (reported) and the Synth MIDI is never read for cues. Everything else that is missing stops the import, naming the files."""
    groups, _ = src.groups()
    parts = groups.get((project, variant))
    if not parts:
        have = sorted({f"{p}" + (f" ({v})" if v else "") for p, v in groups})
        raise ContentError(f"no set '{project}' variant {variant or 'unsuffixed'} in {src.path.name}; found: {', '.join(have)}")
    miss = set_status(parts)
    report = report if report is not None else {}
    report["missing"] = miss
    fatal = [m for m in miss if m != "Synth.mid" and not (m == "Synth.wav")]
    if fatal:
        have_wav = [p for p in PARTS if "wav" in parts.get(p, {})]
        hint = ""
        if all(f"{p}.mid" in fatal for p in ("Drums", "Bass")):
            hint = (f" The set has {'/'.join(have_wav)} audio but no MIDI for the drums and bass: the cues are charted from the MIDI (the importer places nothing from the audio alone), "
                    "so export Drums.mid and Bass.mid (the Synth MIDI is not needed).")
        raise ContentError(f"set '{project}' ({variant or 'unsuffixed'}) is missing {', '.join(fatal)}; needed: Drums.wav/.mid and Bass.wav/.mid (Synth.wav is optional: a silent backing is used).{hint}")
    audio, midi = {}, {}
    for p in PARTS:
        if "wav" not in parts.get(p, {}):
            continue
        frames, rate = read_float_wav_bytes(src.files[parts[p]["wav"]], parts[p]["wav"])
        if rate != SAMPLE_RATE:
            raise ContentError(f"{parts[p]['wav']}: {rate} Hz; imports take {SAMPLE_RATE} Hz so the audio is never resampled or stretched")
        if frames.shape[1] == 1:
            frames = np.repeat(frames, 2, axis=1)
        audio[p] = frames
        if "mid" in parts.get(p, {}) and p != "Synth":
            midi[p] = read_midi_bytes(src.files[parts[p]["mid"]])
    if "Synth" not in audio:
        audio["Synth"] = np.zeros_like(audio["Drums"])
        parts = {**parts, "Synth": {"wav": "(silent backing: no Synth export)"}}
        report.setdefault("notes", []).append("Synth.wav is missing: the backing is silent (the drums and bass play as they are)")
    return parts, audio, midi


def analyse(src: Source, project: str, variant: int, opts: dict) -> dict:
    """Measures one set and builds its cues. `a["report"]` says what was measured, what was chosen automatically and what was loosened.

    `opts`: kick_notes, snare_notes (override the note mapping), profile (force a tempo profile; it must still verify), max_error_ms (default 12),
    trust_midi (chart the bass from the MIDI timing without requiring the audio bass detector to agree; `a["report"]["bass_timing"]["mode"]`
    records "midi_flag"; when the detector disagrees by itself the same happens automatically and is recorded as "midi_fallback")."""
    report: dict = {"set": project + (f" ({variant})" if variant else ""), "decisions": [], "rejected": []}
    try:
        parts, audio, midi = load_set(src, project, variant, report)
    except ContentError as exc:
        raise ContentError(f"{report['set']}: {exc}") from None
    report["decisions"] += report.pop("notes", [])
    mono = {p: audio[p].mean(axis=1) for p in PARTS}
    tol = float(opts.get("max_error_ms", 12.0))
    kick, snare, how = drum_note_choice(midi["Drums"]["notes"], opts)
    report["drum_notes"] = {"counts": {str(k): v for k, v in sorted(how["counts"].items())}, "mode": how["mode"], "kick": sorted(kick), "snare": sorted(snare), "why": how["why"]}
    if how["mode"] == "auto":
        report["decisions"].append("drum notes chosen automatically: " + how["why"])
    elif "no kick" in how["why"] or "no snare" in how["why"]:
        report["decisions"].append(how["why"])
    dn = [n for n in midi["Drums"]["notes"] if n["pitch"] in kick | snare]
    if not dn:
        pitches = sorted({n["pitch"] for n in midi["Drums"]["notes"]})
        raise ContentError(f"{report['set']}: the Drum MIDI has no kick {sorted(kick)} or snare {sorted(snare)} notes (it has {pitches}); pass --kick/--snare notes for this set")
    try:
        name, prof, fit, tried = detect_profile(mono["Drums"], dn, tol, opts.get("profile"), how["mode"] == "auto")
    except ContentError as exc:
        raise ContentError(f"{report['set']}: {exc}") from None
    report["tempo"] = {"profile": name, "verified": next(t["verified"] for t in tried if t["profile"] == name), "tried": tried}
    if report["tempo"]["verified"] == "loose":
        w = [h for h in fit["worst_hits"] if abs(h["error_ms"] - fit["median_ms"]) > tol]
        report["decisions"].append(f"tempo verified loosely: {fit['within_limit'] * 100:.0f}% of the cue hits are within {tol:g} ms, outliers {json.dumps(w)} (max {fit['max_abs_ms']} ms)")
    scale = prof["scale"]
    # the phrase: 16 quarter notes of music; a MIDI that ends a quarter short (15.75) or long (16.5) is still that phrase
    quarters = max(midi["Drums"]["end_beat"], midi["Bass"]["end_beat"])
    q = round(quarters / 4.0) * 4
    if abs(quarters - q) > 1.0 or q * scale not in (16, 32, 64):
        raise ContentError(f"{report['set']}: the phrase is {quarters:g} quarter notes ({quarters * scale:g} game beats); packs take 16, 32 or 64 game beats")
    phrase_beats = int(q * scale)
    if abs(quarters - q) > 0.01:
        report["decisions"].append(f"the MIDI ends at quarter {quarters:g}: taken as the {q}-quarter ({phrase_beats} game beat) phrase")
    loop_frames = int(round(phrase_beats * 60.0 / BPM * SAMPLE_RATE))
    bass_rows = check_bass(mono["Bass"], midi["Bass"]["notes"], prof["source_bpm"])
    meas = [r for r in bass_rows if r["error_ms"] is not None]
    bad = [r for r in meas if abs(r["error_ms"]) > max(tol, 12.0)]
    warnings = []
    med = float(np.median([abs(r["error_ms"]) for r in meas])) if meas else 0.0
    mode, why = "audio_checked", "the audio bass detector agrees with the bass MIDI (median %.1f ms)" % med
    if opts.get("trust_midi"):
        mode, why = "midi_flag", "--trust-midi: the bass is charted from the MIDI timing; the audio detector was measured (median %.1f ms) but not required to agree" % med
        if bad:
            warnings.append(f"bass: charted from the MIDI timing (--trust-midi); the detector disagreed on {len(bad)} of {len(meas)} notes")
    elif bad and med > max(tol, 12.0):
        mode, why = "midi_fallback", "the bass detector could not place the notes within %g ms (median %.1f ms over %d notes); charted from the MIDI timing instead" % (max(tol, 12.0), med, len(meas))
        warnings.append("bass: " + why + ": " + json.dumps(bad[:6]))
    elif bad:
        warnings.append("bass: some note changes could not be placed within the limit (the detector reads a wobbling bass loosely): " + json.dumps(bad))
    report["bass_timing"] = {"mode": mode, "why": why, "median_error_ms": round(med, 1), "notes_measured": len(meas), "notes_out_of_line": len(bad)}
    rules = load_rules()
    cues = build_cues(dn, midi["Bass"]["notes"], scale, kick, snare, rules, phrase_beats)
    over = {fam: [c for c in lst if c[0] >= phrase_beats * PPQ] for fam, lst in cues.items()}
    if any(over.values()):  # notes that start after the loop's end (a MIDI that runs past its 16 quarters) are not part of the phrase
        cues = {fam: [c for c in lst if c[0] < phrase_beats * PPQ] for fam, lst in cues.items()}
        report["decisions"].append("cues past the end of the %d-beat phrase were left out: %s" % (phrase_beats, ", ".join(f"{fam} {[c[0] / PPQ for c in v]}" for fam, v in over.items() if v)))
    tiers, problems = tier_cues(cues, rules, phrase_beats * PPQ)
    for w in warnings:
        report["decisions"].append("WARNING " + w)
    report["rejected"] = [] if not problems else ["chart rules: " + "; ".join(problems[:4])]
    report["files"] = {p: parts[p] for p in PARTS}
    report["header_bpm"] = midi["Drums"]["header_bpm"]
    return {"parts": parts, "audio": audio, "midi": midi, "profile": name, "fit": fit, "bass": bass_rows, "phrase_beats": phrase_beats,
            "loop_frames": loop_frames, "warnings": warnings, "cues": cues, "tiers": tiers, "problems": problems, "scale": scale,
            "kick": sorted(kick), "snare": sorted(snare), "header_bpm": midi["Drums"]["header_bpm"], "report": report}


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
    report = {"timing": {"header_bpm": a["header_bpm"], "profile": a["profile"], "drum_fit": a["fit"], "bass": a["bass"],
                         "tempo_verified": a["report"]["tempo"]["verified"], "bass_timing": a["report"]["bass_timing"]},
              "import_report": {k: a["report"][k] for k in ("set", "drum_notes", "decisions", "rejected", "tempo")}, "loops": loops,
              "cue_counts": {t: {k: len(v) for k, v in d.items()} for t, d in a["tiers"].items()}, "chart_problems": a["problems"]}
    write_json(out / "timing_report.json", report, indent=1)
    return out


def describe(a: dict, project: str, variant: int) -> str:
    f = a["fit"]
    r = a["report"]
    dnote = r["drum_notes"]
    lines = [f"{project}" + (f" ({variant})" if variant else ""),
             f"  drum MIDI notes {json.dumps(dnote['counts'])}: kick {dnote['kick']}, snare {dnote['snare']} ({dnote['mode']})",
             f"  header {a['header_bpm']} BPM; profile {a['profile']} ({r['tempo']['verified']}): drums fit {f['fitted_bpm']} BPM, {f['matched']}/{f['hits']} hits, max {f['max_abs_ms']} ms, offset {f['fitted_offset_ms']} ms",
             f"  phrase {a['phrase_beats']} game beats, loop {a['loop_frames']} frames ({a['loop_frames'] / SAMPLE_RATE:.4f} s)",
             "  bass: " + ", ".join(f"beat {r['beat']:g} {('%+.1f ms' % r['error_ms']) if r['error_ms'] is not None else r['how']}" for r in a["bass"])]
    for t, d in a["tiers"].items():
        lines.append(f"  tier {t}: {len(d['drums'])} drum cues, {len(d['bass'])} bass cues")
    lines.append(f"  bass timing: {r['bass_timing']['mode']}: {r['bass_timing']['why']}")
    for d in r["decisions"]:
        if not d.startswith("WARNING"):
            lines.append("  note: " + d)
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
        run = read_json(RUN_JSON) if RUN_JSON.exists() else {"nodes": []}
        # a scene is a 64-beat phase at a place in a world; its difficulty tier is its world's depth (capped at 4)
        depth_of_world = {w["id"]: min(int(w["depth"]), 4) for w in run.get("worlds", [])}
        scene_world = {n["id"]: n["world"] for n in run["nodes"]}
        chart_of = {n["id"]: n["chart"] for n in m["nodes"]}
        for n in m["nodes"]:
            if n["id"] not in scene_world:
                errors.append(f"music.json: node {n['id']} is not in run.json")
            if n["audio"] != n["chart"] and n["audio"] in packs and n["chart"] in packs:
                if packs[n["audio"]]["tiers"] != packs[n["chart"]]["tiers"]:
                    errors.append(f"music.json: node {n['id']} plays the recordings of '{n['audio']}' under the chart of '{n['chart']}', but their MIDI differs; "
                                  "an alternate render must be exported from the same MIDI (or give the scene the new chart)")
        for n in run["nodes"]:  # sibling scenes: the routes of one scene that chart different packs fall under the route lock
            charts = {chart_of[r["to"]] for r in n["next"] if r["to"] in chart_of}
            if len(charts) > 1:
                dp = depth_of_world.get(n["world"], 1)
                temp = any(x.get("temporary") for x in m["nodes"] if x["id"] in {r["to"] for r in n["next"]})
                notes.append(f"WARNING scene {n['id']} (tier {dp}): its routes chart {', '.join(sorted(charts))}; the route lock applies between them"
                             + ("; one of them is a temporary stand-in" if temp else ""))
        for n in run["nodes"]:
            if n["id"] not in ids:
                errors.append(f"run.json node {n['id']} has no music.json entry")
        notes.append(f"music.json: {len(ids)} nodes assigned")
    else:
        errors.append("content/story/music.json is missing")
    trial = TRIAL_JSON
    if trial.exists():  # the dungeon opening's phrases play a pack too
        tm = read_json(trial).get("music", {})
        for key in ("audio", "chart"):
            if tm.get(key) not in packs:
                errors.append(f"content/trial/passages.json: music.{key} pack '{tm.get(key)}' does not exist")
        notes.append(f"trial: music {tm.get('audio')} / chart {tm.get('chart')}")
    return errors, notes


# --- cli ----------------------------------------------------------------------------------------------------------

def cmd_scan(args) -> int:
    src = Source(Path(args.source))
    groups, odd = src.groups()
    print(f"{src.path}: {len(src.files)} files, {len(groups)} sets")
    for (project, variant), parts in sorted(groups.items()):
        miss, fatal = set_status(parts), fatal_missing(parts)
        state = "paired" if not miss else ("NOT IMPORTABLE, missing " + ", ".join(fatal) if fatal else "importable, missing " + ", ".join(miss) + " (silent backing)")
        print(f"  {slug(project, variant):28s} {project}" + (f" ({variant})" if variant else "") + "  " + state)
    for o in odd:
        print("  not an export file name:", o)
    return 1 if odd or any(fatal_missing(p) for p in groups.values()) else 0


def cmd_survey(args) -> int:
    """Measure every set in a source and say, per set, what was found, what was decided automatically and why a set was refused. Writes nothing."""
    src = Source(Path(args.source))
    groups, _ = src.groups()
    only = {s_.strip().lower() for s_ in args.only.split(",")} if args.only else None
    bad = 0
    for (project, variant), parts in sorted(groups.items()):
        sid = slug(project, variant)
        if only and sid not in only:
            continue
        print(f"== {sid}: {project}" + (f" ({variant})" if variant else ""))
        try:
            a = analyse(src, project, variant, _opts(args))
        except ContentError as exc:
            bad += 1
            print("  REFUSED:", exc)
            continue
        print("\n".join(describe(a, project, variant).splitlines()[1:]))
        if a["problems"]:
            bad += 1
    return 1 if bad else 0


def _opts(args) -> dict:
    o: dict = {}
    if args.kick:
        o["kick_notes"] = [int(x) for x in args.kick.split(",")]
    if args.snare:
        o["snare_notes"] = [int(x) for x in args.snare.split(",")]
    if args.profile:
        o["profile"] = args.profile
    if getattr(args, "trust_midi", False):
        o["trust_midi"] = True
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


def assign(node: str, audio: str | None, chart: str | None, treatment: str | None, temporary: bool | None, music_path: Path = MUSIC_JSON) -> None:
    """Point a node at other packs without touching code. Node ids never change."""
    m = read_json(music_path)
    for n in m["nodes"]:
        if n["id"] == node:
            if audio:
                n["audio"] = audio
            if chart:
                n["chart"] = chart
            if treatment:
                n["treatment"] = treatment
            if temporary is not None:
                n["temporary"] = temporary
            write_json(music_path, m, indent=1)
            return
    raise ContentError(f"no node '{node}' in music.json (nodes: {', '.join(x['id'] for x in m['nodes'])})")


def cmd_assign(args) -> int:
    assign(args.node, args.audio, args.chart, args.treatment, False if args.final else None)
    errors, _ = validate()
    for e in errors:
        print("ERROR", e)
    print("assigned" if not errors else "assigned, but the data now has problems (above)")
    return 1 if errors else 0


def cmd_apply(args) -> int:
    """import + assign in one go: the usual way to give a level its recordings."""
    code = cmd_import(args)
    if code:
        return code
    chart = None if args.audio_only else args.id
    assign(args.node, args.id, chart, args.treatment, False)
    errors, _ = validate()
    for e in errors:
        print("ERROR", e)
    print(f"node {args.node} now plays {args.id}" + ("" if args.audio_only else " and charts it") if not errors else "assigned, but validation failed (above)")
    return 1 if errors else 0


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
        c.add_argument("--trust-midi", action="store_true", help="chart the bass from the MIDI timing even if the audio bass detector disagrees (recorded in timing_report.json; "
                       "the same happens automatically, with a warning, when the detector cannot place the notes)")
        if name == "import":
            c.add_argument("--id", required=True, help="stable pack id (folder under songs/packs)")
            c.add_argument("--label")
            c.add_argument("--drums-db", type=float, default=0.0)
            c.add_argument("--bass-db", type=float, default=3.0)
            c.add_argument("--synth-db", type=float, default=10.0)
    a = sub.add_parser("assign", help="point a node at already imported packs (edits content/story/music.json)")
    a.add_argument("--node", required=True)
    a.add_argument("--audio", help="pack whose recordings play")
    a.add_argument("--chart", help="pack whose cues are charted (shared by every node at the same depth)")
    a.add_argument("--treatment", help="a name from run.json treatments")
    a.add_argument("--final", action="store_true", help="mark the node's music as final (not temporary)")
    ap2 = sub.add_parser("apply", help="import one set and assign it to a node")
    ap2.add_argument("source")
    ap2.add_argument("--node", required=True)
    ap2.add_argument("--set", required=True)
    ap2.add_argument("--variant", type=int, default=0)
    ap2.add_argument("--id", required=True)
    ap2.add_argument("--audio-only", action="store_true", help="use the recordings only; the chart stays the depth's shared one (alternate render of the same MIDI)")
    ap2.add_argument("--treatment")
    ap2.add_argument("--label")
    ap2.add_argument("--kick")
    ap2.add_argument("--snare")
    ap2.add_argument("--profile", choices=sorted(PROFILES))
    ap2.add_argument("--trust-midi", action="store_true")
    ap2.add_argument("--drums-db", type=float, default=0.0)
    ap2.add_argument("--bass-db", type=float, default=3.0)
    ap2.add_argument("--synth-db", type=float, default=10.0)
    sv = sub.add_parser("survey", help="measure every set of a source, report per set what was decided or why it was refused (writes nothing)")
    sv.add_argument("source")
    sv.add_argument("--only", help="comma separated set slugs, e.g. lv4_hospital,lv4_hospital_v1")
    sv.add_argument("--kick")
    sv.add_argument("--snare")
    sv.add_argument("--profile", choices=sorted(PROFILES))
    sv.add_argument("--trust-midi", action="store_true")
    sub.add_parser("validate")
    args = ap.parse_args()
    try:
        return {"scan": cmd_scan, "check": cmd_check, "import": cmd_import, "validate": cmd_validate, "assign": cmd_assign, "apply": cmd_apply, "survey": cmd_survey}[args.cmd](args)
    except ContentError as exc:
        print(f"ERROR {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
