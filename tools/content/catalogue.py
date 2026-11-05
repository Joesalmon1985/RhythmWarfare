"""The music catalogue: every WAV and MIDI of the owner's folders, measured, paired, grouped into families and cross-checked.

    python tools/content/catalogue.py                      # discover, analyse, write content/music/catalogue.json and docs/MUSIC_CATALOGUE.md
    python tools/content/catalogue.py --check              # analyse and compare with the files on disk (exit 1 when they differ)
    python tools/content/catalogue.py --source DIR ...     # use these folders instead of the default list (ToAddTry1..3 found by name)
    python tools/content/catalogue.py --print              # the summary only; nothing is written

Sources: the folders named on the command line, else RW_MUSIC_SOURCES (an os.pathsep list), else the names in
content/music/sources.json ({"sources": [...]}), else ToAddTry1, ToAddTry2 and ToAddTry3. A name that is not a path is looked up in the
project root and then in every parent folder, so a checkout beside (or inside a worktree below) the owner's folders finds them. Folders are
searched recursively; only .wav, .mid and .midi files count (Ableton .asd and Godot .import files are ignored); nothing is ever modified.
Paths in the output are `<source folder name>/<path inside it>`, never absolute, and nothing in the output depends on the time or the machine:
the same folders give the same bytes.

What is measured (details and the reasoning in docs/MUSIC_CATALOGUE.md):

* Provenance and pairing. A Beat Shaper export is `Beat Shaper - <project>-<Drums|Bass|Synth>[ (n)]`: its *family* is the project and its
  *set* is the project plus the variant suffix. An Ableton render is `<Role><N><Timbre>.wav` with an optional `<Role><N>.mid`: its *family* is
  the pattern (folder, role, N), the timbres are alternative renders of one MIDI. WAV and MIDI are paired by that grouping, never by position.
* Timing. The MIDI header tempo is ignored (the exports say 120 or nothing). The tempo is measured against the audio: drum transients are fitted
  to the MIDI's kick and snare times at each profile (`174x1`: a source quarter is one game beat; `87x2`: a quarter is two), the bass and synth are
  checked by spectral change at the MIDI's note starts, and the MIDI length must agree with the audio length. A recording with no MIDI gets the
  tempo of its loop period against the 174 BPM bar grid. A file no profile fits is `unknown`.
* Bars. Whole game bars (4 beats at 174 BPM) of music, the repeating `pattern_bars` of the MIDI (a 16-bar render of a 4-bar pattern repeats
  four times), the release tail after the musical end, the leading silence, the sample rate and format, the duration.
* Role: kick, snare, drums, perc, bass, synth, pad or fx, from the name and checked against the spectrum and the MIDI.
* MIDI facts: note positions (in game beats), durations, velocities, density per bar, pitch classes, an estimated tonal centre
  (Krumhansl-Schmuckler on the duration-weighted pitch classes, with a confidence; advisory only), rhythmic density, syncopation and complexity.
* Loudness: RMS, peak, clipping count (samples at full scale) and a clipping risk.
* Compatibility between families (rules in `compatibility()`): inside a family always; across families only when the phrase lengths tile,
  the profiles are equal and the tonal centres agree or one side is atonal; `uncertain` where an estimate is low-confidence; never from tempo alone.

Schema (content/music/catalogue.json, "schema": 1): top-level keys `schema`, `tool`, `sources`, `summary`, `files` (one record per WAV),
`midis` (one record per MIDI), `families`, `compatibility`. Other tools (arrange.py) read only this file.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ROOT, ContentError, sha256_file, write_text_lf  # noqa: E402
from import_recorded import envelope, onset_near, read_float_wav_bytes  # noqa: E402
from midi_reader import MidiError, parse_midi, read_midi_bytes  # noqa: E402

SCHEMA = 1
DEFAULT_SOURCE_NAMES = ("ToAddTry1", "ToAddTry2", "ToAddTry3")
CATALOGUE_JSON = ROOT / "content" / "music" / "catalogue.json"
CATALOGUE_MD = ROOT / "docs" / "MUSIC_CATALOGUE.md"
SOURCES_JSON = ROOT / "content" / "music" / "sources.json"

GAME_BPM = 174.0
BEAT_S = 60.0 / GAME_BPM
BAR_S = 4 * BEAT_S
PROFILES = {"174x1": {"bpm": 174.0, "scale": 1}, "87x2": {"bpm": 87.0, "scale": 2}}  # scale: game beats per source quarter
NICE_BARS = (1, 2, 4, 8, 16, 32, 64)
SILENCE = 1e-3          # -60 dBFS: below this the file is silent
CLIP_LEVEL = 0.9995     # at or above this a sample is at full scale
BS_RE = re.compile(r"^(?:Beat Shaper - )?(?P<project>.+)-(?P<part>Drums|Bass|Synth)(?: \((?P<variant>\d+)\))?$")
AB_RE = re.compile(r"^(?P<role>bass|kick|snare|other|hats?|perc|pad|fx|synth|lead)(?P<n>\d+)(?P<timbre>[a-z]*)$", re.I)
GROUPS = {"kick": "rhythm", "snare": "rhythm", "drums": "rhythm", "perc": "rhythm", "bass": "bass", "synth": "harmony", "pad": "harmony",
          "fx": "fx"}
ATONAL_ROLES = {"kick", "snare", "drums", "perc", "fx"}
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
PC_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
LOW_CONFIDENCE = 0.5


def db(x: float) -> float:
    return -120.0 if x <= 1e-6 else round(20.0 * math.log10(x), 2)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


# --- sources and discovery -----------------------------------------------------------------------------------------

def find_sources(explicit: list[str] | None = None, root: Path = ROOT, names: tuple = DEFAULT_SOURCE_NAMES) -> tuple[list[Path], list[str]]:
    """The folders to catalogue and the names that could not be found. A bare name is searched for in `root` and each of its parents."""
    wanted: list[str] = list(explicit or [])
    if not wanted and os.environ.get("RW_MUSIC_SOURCES"):
        wanted = [p for p in os.environ["RW_MUSIC_SOURCES"].split(os.pathsep) if p]
    if not wanted and SOURCES_JSON.exists():
        wanted = list(json.loads(SOURCES_JSON.read_text(encoding="utf-8")).get("sources", []))
    if not wanted:
        wanted = list(names)
    found: list[Path] = []
    missing: list[str] = []
    for w in wanted:
        p = Path(w).expanduser()
        hit = None
        if p.is_absolute() or len(p.parts) > 1:
            hit = p if p.is_dir() else None
        else:
            for base in [root, *root.parents]:
                if (base / w).is_dir():
                    hit = base / w
                    break
        if hit is None:
            missing.append(w)
        elif hit.resolve() not in [f.resolve() for f in found]:
            found.append(hit)
    return found, missing


def discover(sources: list[Path]) -> list[dict]:
    """Every .wav/.mid/.midi below the sources: {id, path, folder, name, kind}. The id and folder are relative to the source's parent."""
    out = []
    for src in sources:
        for p in sorted(src.rglob("*")):
            rel_parts = p.relative_to(src).parts
            if not p.is_file() or any(part.startswith(".") for part in rel_parts):
                continue
            ext = p.suffix.lower()
            if ext not in (".wav", ".mid", ".midi"):
                continue
            rel = "/".join((src.name,) + rel_parts)
            out.append({"id": rel, "path": p, "folder": "/".join((src.name,) + rel_parts[:-1]), "name": p.name,
                        "kind": "wav" if ext == ".wav" else "midi"})
    out.sort(key=lambda e: e["id"])
    return out


def parse_name(folder: str, name: str) -> dict:
    """Provenance from the file name: source kind, family, set/pattern, part or role, variant, timbre."""
    stem = Path(name).stem
    m = BS_RE.match(stem)
    if m:
        variant = int(m["variant"]) if m["variant"] else 0
        fam = "bs_" + slug(m["project"])
        return {"source": "beat_shaper", "family": fam, "group": f"{fam}:v{variant}", "project": m["project"], "variant": variant,
                "part": m["part"].lower(), "timbre": "", "name_role": {"drums": "drums", "bass": "bass", "synth": "synth"}[m["part"].lower()]}
    m = AB_RE.match(stem)
    if m:
        role = m["role"].lower().rstrip("s") if m["role"].lower().startswith("hat") else m["role"].lower()
        role = {"hat": "perc", "lead": "synth"}.get(role, role)
        where = slug(folder.split("/")[-1]) if "/" in folder else slug(folder)
        fam = f"ab_{where}_{m['role'].lower()}{int(m['n'])}"
        return {"source": "ableton", "family": fam, "group": fam, "project": "", "variant": 0, "part": m["role"].lower(), "number": int(m["n"]),
                "timbre": m["timbre"].lower(), "timbre_label": m["timbre"], "name_role": role}
    fam = "other_" + slug(folder.split("/")[-1] + "_" + stem)
    return {"source": "unrecognised", "family": fam, "group": fam, "project": "", "variant": 0, "part": "", "timbre": "", "name_role": ""}


def pair_key(info: dict, folder: str) -> tuple:
    """WAV and MIDI of one part share this key (never position): the Beat Shaper part of one set, the Ableton pattern, the same stem."""
    if info["source"] == "beat_shaper":
        return (folder, "bs", info["project"], info["variant"], info["part"])
    if info["source"] == "ableton":
        return (folder, "ab", info["part"], info["number"])
    return (folder, "stem", info["family"])


# --- audio analysis ----------------------------------------------------------------------------------------------------

def wav_format(data: bytes) -> dict:
    """Format tag, channels, rate and bits from the fmt chunk."""
    import struct
    i = 12
    while i + 8 <= len(data):
        cid, n = data[i:i + 4], struct.unpack("<I", data[i + 4:i + 8])[0]
        if cid == b"fmt ":
            tag, ch, rate, _, _, bits = struct.unpack("<HHIIHH", data[i + 8:i + 24])
            return {"channels": ch, "sample_rate": rate, "bits": bits, "encoding": "float" if tag == 3 else "pcm"}
        i += 8 + n + (n & 1)
    return {}


def nice_bars(x: float, tol: float = 0.12) -> int | None:
    """The nearest phrase length (1, 2, 4, ... 64 bars) within `tol` of x (as a fraction), else None."""
    best = min(NICE_BARS, key=lambda n: abs(n - x))
    return best if abs(best - x) <= tol * best else None


def ceil_nice(active_bars: float, tail_allowance: float = 0.5) -> int:
    """The shortest phrase length (1, 2, 4 ... bars) that holds the sound up to `active_bars` when at most `tail_allowance` bars of it are release."""
    for n in NICE_BARS:
        if n >= active_bars - tail_allowance:
            return n
    return NICE_BARS[-1]


def active_end(mono: np.ndarray) -> int:
    loud = np.nonzero(np.abs(mono) > SILENCE)[0]
    return int(loud[-1]) + 1 if len(loud) else 0


def onset_times(mono: np.ndarray, rate: int) -> list[float]:
    env, step = envelope(mono, rate)
    d = np.log(env + 1e-4)
    d = d[3:] - d[:-3]
    out: list[float] = []
    for i in range(1, len(d) - 1):
        if d[i] > 0.7 and d[i] >= d[i - 1] and d[i] > d[i + 1]:
            t = (i + 1) * step
            if not out or t - out[-1] > 0.04:
                out.append(t)
    return out


def fit_hits(mono: np.ndarray, rate: int, hits: list[float], bpm: float, tol_s: float = 0.012) -> dict | None:
    """Fit the audio's transients to MIDI hit times (quarters) at `bpm`: matched share, fitted tempo, error spread. Hits after the last sound are not counted."""
    env, step = envelope(mono, rate)
    spb = 60.0 / bpm
    dur = active_end(mono) / rate
    inside = [b for b in hits if b * spb < dur - 0.1]
    pairs = []
    for b in inside:
        o = onset_near(env, step, b * spb, 0.04)
        if o is not None:
            pairs.append((b, o))
    if len(inside) < 4:
        return None
    if len(pairs) < 4:
        return {"hits": len(inside), "matched": len(pairs), "matched_share": round(len(pairs) / len(inside), 3), "fitted_bpm": None}
    bs = np.array([p[0] for p in pairs])
    ts = np.array([p[1] for p in pairs])
    slope, icpt = np.polyfit(bs, ts, 1)
    res = np.abs(ts - (bs * slope + icpt))
    return {"hits": len(inside), "matched": len(pairs), "matched_share": round(len(pairs) / len(inside), 3),
            "fitted_bpm": round(float(60.0 / slope), 3), "offset_ms": round(float(icpt * 1000), 1),
            "median_error_ms": round(float(np.median(res) * 1000), 2),
            "max_error_ms": round(float(res.max() * 1000), 1), "within_12ms": round(float((res <= tol_s).mean()), 3)}


def spectral_grid(mono: np.ndarray, rate: int, lo: float, hi: float) -> tuple[np.ndarray, int, int]:
    """Normalised band spectra of 40 ms windows every 2 ms: (frames x bins, hop, window)."""
    win = int(0.04 * rate)
    hop = int(0.002 * rate)
    hann = np.hanning(win)
    freqs = np.fft.rfftfreq(2 * win, 1.0 / rate)
    band = (freqs > lo) & (freqs < hi)
    n = max(0, (len(mono) - win) // hop + 1)
    out = np.zeros((n, int(band.sum())), dtype=np.float32)
    for a in range(0, n, 512):
        b = min(n, a + 512)
        frames = np.lib.stride_tricks.sliding_window_view(mono, win)[a * hop:(b - 1) * hop + 1:hop] * hann
        s = np.abs(np.fft.rfft(frames, 2 * win, axis=1))[:, band]
        out[a:b] = s / (np.linalg.norm(s, axis=1, keepdims=True) + 1e-9)
    return out, hop, win


def score_changes(grid: tuple, rate: int, notes: list[dict], bpm: float, dur: float) -> dict | None:
    """How many note starts of the MIDI show a spectral change in the audio within 40 ms, at tempo `bpm` (quarters per minute)."""
    spec, hop, win = grid
    spb = 60.0 / bpm
    lag = win // hop
    measurable = [n for i, n in enumerate(notes) if n["beat"] > 0 and not (i and notes[i - 1]["pitch"] == n["pitch"] and abs(n["beat"] - (notes[i - 1]["beat"] + notes[i - 1]["dur"])) < 0.01)]
    rows = []
    for n in measurable:
        t = n["beat"] * spb
        if t + 0.1 > dur:
            continue
        gaps = [abs(n["beat"] - o["beat"]) * spb for o in notes if o["beat"] != n["beat"]]
        half = min(0.08, 0.4 * min(gaps)) if gaps else 0.08
        # window start of the "before" spectrum = c * rate - win; both spectra are 40 ms long, back to back at time c
        ks = np.arange(max(int((t - half) / (hop / rate)) - lag, 0), int((t + half) / (hop / rate)) - lag + 1)
        ks = ks[ks + lag < len(spec)]
        if not len(ks):
            continue
        d = 1.0 - np.einsum("ij,ij->i", spec[ks], spec[ks + lag])
        j = int(np.argmax(d))
        c = (ks[j] + lag) * hop / rate
        rows.append((float(d[j]), (c - t) * 1000.0, n["beat"]))
    if len(rows) < 3:
        return None
    good = [r for r in rows if r[0] >= 0.1 and abs(r[1]) <= 40.0]
    out = {"notes": len(rows), "matched": len(good), "matched_share": round(len(good) / len(rows), 3),
           "median_error_ms": round(float(np.median([r[1] for r in good])), 1) if good else None}
    if len(good) >= 4:
        b = np.array([r[2] for r in good])
        t = np.array([r[2] * spb + r[1] / 1000.0 for r in good])
        out["fitted_bpm"] = round(float(60.0 / np.polyfit(b, t, 1)[0]), 2)
    return out


def spectrum_features(mono: np.ndarray, rate: int) -> dict:
    x = mono[:max(active_end(mono), 1)]
    if len(x) < 2048:
        return {"centroid_hz": 0.0, "sub": 0.0, "low": 0.0, "mid": 0.0, "high": 0.0, "flatness": 0.0}
    p = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    f = np.fft.rfftfreq(len(x), 1.0 / rate)
    tot = float(p.sum()) + 1e-20
    band = (f >= 100) & (f <= 10000)
    pb = p[band] + 1e-20
    flat = float(np.exp(np.mean(np.log(pb))) / np.mean(pb))
    return {"centroid_hz": round(float((f * p).sum() / tot), 0), "sub": round(float(p[f < 120].sum() / tot), 3),
            "low": round(float(p[(f >= 120) & (f < 500)].sum() / tot), 3), "mid": round(float(p[(f >= 500) & (f < 4000)].sum() / tot), 3),
            "high": round(float(p[f >= 4000].sum() / tot), 3), "flatness": round(flat, 4)}


def audio_chroma(mono: np.ndarray, rate: int) -> np.ndarray:
    x = mono[:max(active_end(mono), 1)]
    if len(x) < 4096:
        return np.zeros(12)
    mag = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1.0 / rate)
    sel = (f >= 40) & (f <= 2000)
    pcs = np.round(12 * np.log2(f[sel] / 440.0) + 69).astype(int) % 12
    chroma = np.bincount(pcs, weights=np.sqrt(mag[sel]), minlength=12)
    return chroma / (chroma.sum() + 1e-12)


def key_estimate(hist: np.ndarray) -> dict | None:
    """Krumhansl-Schmuckler: the best of 24 keys for a 12-bin pitch-class weight vector, with a 0..1 confidence (advisory)."""
    h = np.asarray(hist, dtype=float)
    if h.sum() <= 0 or np.count_nonzero(h) < 2 or float(np.std(h)) < 1e-9:
        return None
    scores = []
    for pc in range(12):
        for mode, prof in (("major", MAJOR), ("minor", MINOR)):
            r = float(np.corrcoef(h, np.roll(prof, pc))[0, 1])
            scores.append((r, pc, mode))
    scores.sort(key=lambda s: (-s[0], s[1], s[2]))
    r1, pc, mode = scores[0]
    # runner-up that is not the relative key (relatives share their notes: they are not a contradiction)
    rel = (pc + 9) % 12 if mode == "major" else (pc + 3) % 12
    r2 = next(s[0] for s in scores[1:] if not (s[1] == rel and s[2] != mode))
    conf = min(1.0, max(0.0, (r1 - 0.45) / 0.4)) * min(1.0, (r1 - r2) / 0.08)
    return {"tonic": PC_NAMES[pc], "pc": pc, "mode": mode, "name": f"{PC_NAMES[pc]} {mode}", "correlation": round(r1, 3),
            "confidence": round(conf, 3)}


def key_distance(a: dict, b: dict) -> str:
    """same | relative | near (parallel mode or a fifth apart) | disagree."""
    if a["pc"] == b["pc"] and a["mode"] == b["mode"]:
        return "same"
    minor, major = (a, b) if a["mode"] == "minor" else (b, a)
    if a["mode"] != b["mode"] and (minor["pc"] - major["pc"]) % 12 == 9:
        return "relative"
    if a["pc"] == b["pc"] or (a["mode"] == b["mode"] and (a["pc"] - b["pc"]) % 12 in (5, 7)):
        return "near"
    return "disagree"


def loudness(frames: np.ndarray, active: int) -> dict:
    a = np.abs(frames)
    peak = float(a.max()) if a.size else 0.0
    rms = float(np.sqrt(np.mean(frames.astype(np.float64) ** 2))) if frames.size else 0.0
    ract = float(np.sqrt(np.mean(frames[:max(active, 1)].astype(np.float64) ** 2))) if frames.size else 0.0
    clipped = int((a >= CLIP_LEVEL).sum())
    over = int((a > 1.0).sum())
    risk = "clipped" if over or clipped >= 3 else ("close" if peak >= 0.89 else "none")  # -1 dBFS
    return {"rms_db": db(rms), "rms_active_db": db(ract), "peak_db": db(peak), "clipping_samples": clipped, "over_full_scale": over, "clipping_risk": risk}


# --- MIDI analysis --------------------------------------------------------------------------------------------------

def drum_note_classes(notes: list[dict]) -> dict:
    cls = Counter()
    for n in notes:
        p = n["pitch"]
        cls["kick" if p in (35, 36) else "snare" if p in (37, 38, 39, 40) else "hat" if p in (42, 44, 46) else "other"] += 1
    return dict(sorted(cls.items()))


def cue_hits(notes: list[dict], role: str) -> list[float]:
    """The MIDI note starts (quarters) the audio's transients are fitted to: kick and snare notes of a kit, every note of a one-drum file."""
    if role in ("kick", "snare"):
        return sorted({n["beat"] for n in notes})
    ks = [n for n in notes if n["pitch"] in (36, 38, 40)]
    pool = ks or [n for n in notes if n["pitch"] not in (42, 44, 46)]
    return sorted({n["beat"] for n in pool})


def pattern_period(positions: list[tuple], bars: int) -> int:
    """The smallest phrase (1, 2, 4 ... bars) whose notes repeat exactly to fill `bars`: positions are (game beat, duration, pitch)."""
    for p in NICE_BARS:
        if p > bars or bars % p:
            continue
        blocks = defaultdict(set)
        for pos, dur, pitch in positions:
            k = int(pos // (4 * p))
            if k < bars // p:
                blocks[k].add((round(pos - k * 4 * p, 3), round(dur, 3), pitch))
        if all(blocks.get(k, set()) == blocks.get(0, set()) for k in range(bars // p)):
            return p
    return bars


def rhythm_measures(positions: list[float], bars: int) -> dict:
    """Density per game beat, syncopation (0 on the beat, 0.5 on an off-beat eighth, 1 on a sixteenth) and complexity (entropy of the 16 steps)."""
    if not positions:
        return {"onsets": 0, "per_beat": 0.0, "syncopation": 0.0, "offbeat_share": 0.0, "complexity": 0.0}
    steps = [int(round((p % 4) * 4)) % 16 for p in positions]
    w = [0.0 if s % 4 == 0 else (0.5 if s % 4 == 2 else 1.0) for s in steps]
    hist = np.bincount(steps, minlength=16).astype(float)
    pr = hist[hist > 0] / hist.sum()
    ent = float(-(pr * np.log2(pr)).sum() / 4.0)
    return {"onsets": len(positions), "per_beat": round(len(positions) / max(bars * 4, 1), 3), "syncopation": round(float(np.mean(w)), 3),
            "offbeat_share": round(float(np.mean([x > 0 for x in w])), 3), "complexity": round(ent, 3)}


def analyse_midi(path: Path, scale: int, bars: int) -> dict:
    """Facts of one MIDI file in game beats at the profile's scale (1 when the profile is unknown)."""
    data = path.read_bytes()
    try:
        info = read_midi_bytes(data)
        header = parse_midi(data)
    except (MidiError, ValueError) as exc:
        raise ContentError(f"{path.name}: not a readable MIDI file ({exc})") from exc
    notes = info["notes"]
    return {"notes": notes, "header_bpm": None if info["header_bpm"] is None else round(info["header_bpm"], 3), "ppq": header["division"],
            "format": header["format"], "end_beat_quarters": round(info["end_beat"], 4), "scale": scale}


# --- one WAV / MIDI record ------------------------------------------------------------------------------------------

def length_consistent(end_beat: float, scale: int, total_bars: float) -> tuple[int | None, bool]:
    """Whether a MIDI of `end_beat` quarters at this profile fits the recording: the audio covers it and the rest is a tail of at most two bars."""
    raw = end_beat * scale / 4.0
    est = nice_bars(raw)
    return est, est is not None and raw <= total_bars + 0.05 and total_bars - est <= 2.0


def decide_tempo(role: str, mono: np.ndarray, rate: int, notes: list[dict], end_beat: float, dur: float) -> dict:
    """Measured tempo and profile. The evidence of every method is listed so the reader can see what agreed.

    Order of authority: drum transients fitted to the kick/snare notes (drum parts), spectral change at the note starts (pitched parts), then the
    MIDI length against the audio length. Where two profiles both fit the transients, the one whose MIDI length also matches the recording wins,
    then the one with more matched hits."""
    evidence: list[dict] = []
    verdict = None
    method = None
    measured = None
    detail: dict = {}
    total_bars = dur / BAR_S
    consistent = {}
    for name, p in PROFILES.items():
        est, ok = length_consistent(end_beat, p["scale"], total_bars)
        consistent[name] = ok
        evidence.append({"method": "midi_length", "profile": name, "midi_bars": est, "audio_bars": round(total_bars, 2), "verified": ok})
    drum_like = role in ("kick", "snare", "drums", "perc")
    if drum_like:
        hits = cue_hits(notes, role)
        fits = {}
        for name, p in PROFILES.items():
            fit = fit_hits(mono, rate, hits, p["bpm"])
            fits[name] = fit
            ok = bool(fit) and fit["fitted_bpm"] is not None and fit["matched_share"] >= 0.8 and abs(fit["fitted_bpm"] - p["bpm"]) <= 0.5 and fit["within_12ms"] >= 0.7 \
                and fit["max_error_ms"] <= 40.0
            evidence.append({"method": "drum_transient_fit", "profile": name, "verified": ok, **(fit or {})})
        good = [(consistent[n], f["matched"], f["within_12ms"], -f["max_error_ms"], n) for n, f in fits.items()
                if f and any(e["profile"] == n and e["method"] == "drum_transient_fit" and e["verified"] for e in evidence)]
        if good:
            good.sort(reverse=True)
            verdict, method = good[0][4], "drum_transient_fit"
            measured = fits[verdict]["fitted_bpm"]
            detail = {k: fits[verdict][k] for k in ("hits", "matched", "within_12ms", "max_error_ms", "offset_ms")}
    else:
        lo, hi = (40, 400) if role == "bass" else (100, 4000)
        grid = spectral_grid(mono, rate, lo, hi)
        scores = {}
        for name, p in PROFILES.items():
            sc = score_changes(grid, rate, notes, p["bpm"], dur)
            scores[name] = sc
            evidence.append({"method": "spectral_change", "profile": name, "verified": False, **(sc or {})})
        ranked = sorted(((s["matched_share"], n) for n, s in scores.items() if s), reverse=True)
        if ranked and ranked[0][0] >= 0.5 and (len(ranked) == 1 or ranked[0][0] - ranked[1][0] >= 0.2):
            verdict, method = ranked[0][1], "spectral_change"
            for e in evidence:
                if e["method"] == "spectral_change" and e["profile"] == verdict:
                    e["verified"] = True
            fitted = scores[verdict].get("fitted_bpm")
            measured = fitted if fitted and abs(fitted - PROFILES[verdict]["bpm"]) <= 2.0 else PROFILES[verdict]["bpm"]
            detail = {k: scores[verdict][k] for k in ("notes", "matched", "median_error_ms")}
    transients_failed = drum_like and any(e["method"] == "drum_transient_fit" and e.get("hits") for e in evidence)
    if verdict is None:
        agree = [n for n, ok in consistent.items() if ok]
        if len(agree) == 1 and not transients_failed:  # the transients were measured and fit no profile: the length alone does not make one
            verdict, method, measured = agree[0], "midi_length", PROFILES[agree[0]]["bpm"]
    elif not consistent[verdict] and any(consistent.values()) and method != "drum_transient_fit":
        verdict = None  # a spectral guess that the MIDI length contradicts is not a measurement
        agree = [n for n, ok in consistent.items() if ok]
        if len(agree) == 1:
            verdict, method, measured = agree[0], "midi_length", PROFILES[agree[0]]["bpm"]
    return {"profile": verdict or "unknown", "method": method, "measured_bpm": measured, "detail": detail, "evidence": evidence}


def loop_period_tempo(mono: np.ndarray, rate: int, bars: int) -> dict:
    """No MIDI: the recording's loop period against the 174 BPM bar grid (the 87 BPM render is the same audio on the game grid)."""
    end = active_end(mono)
    on = onset_times(mono[:end], rate) if end else []
    if len(on) < 4:
        return {"profile": "unknown", "method": None, "measured_bpm": None, "detail": {"onsets": len(on)}, "evidence": []}
    # distance of every onset from the nearest 16th of the 174 BPM grid, searched over the grid offset
    sixteenth = BEAT_S / 4
    over = end / (BAR_S * rate) - bars
    best = None
    for off in np.arange(0.0, sixteenth, 0.0005):
        err = [((t - off + sixteenth / 2) % sixteenth) - sixteenth / 2 for t in on]
        s = float(np.median(np.abs(err)))
        if best is None or s < best[0]:
            best = (s, off, float(np.max(np.abs(err))))
    ok = best[0] * 1000 <= 8.0
    return {"profile": "174x1" if ok else "unknown", "method": "grid_fit" if ok else None, "measured_bpm": GAME_BPM if ok else None,
            "detail": {"onsets": len(on), "median_grid_error_ms": round(best[0] * 1000, 2), "grid_offset_ms": round(best[1] * 1000, 1)},
            "evidence": [{"method": "grid_fit", "profile": "174x1", "verified": ok, "onsets": len(on),
                          "median_error_ms": round(best[0] * 1000, 2)},
                         {"method": "length_on_grid", "bars": bars, "sounding_past_bars": round(over, 3)}],
            "note": "audio only: 174x1 and 87x2 renders are the same audio on the game grid"}


def decide_role(info: dict, spec: dict, onsets_per_beat: float, notes: list[dict], mean_dur_beats: float) -> tuple[str, str]:
    base = info["name_role"]
    if base in ("kick", "snare", "drums", "bass", "perc"):
        return base, "name"
    if base in ("synth", "pad", "fx"):
        if base == "synth" and notes and mean_dur_beats >= 3.0 and onsets_per_beat < 0.5:
            return "pad", "name synth, long sustained notes"
        return base, "name"
    # "other" and unrecognised names: the spectrum decides
    if spec["high"] > 0.4 and onsets_per_beat >= 0.5:
        return "perc", "spectrum: energy above 4 kHz, regular onsets"
    if spec["sub"] > 0.6:
        return "kick" if onsets_per_beat >= 0.1 else "bass", "spectrum: sub bass"
    if spec["flatness"] > 0.2 and onsets_per_beat < 0.5:
        return "fx", "spectrum: noisy, sparse"
    if onsets_per_beat < 0.3:
        return "pad", "spectrum: sustained"
    return "synth", "spectrum: tonal"


def mood_tags(key: dict | None, spec: dict, rhythm: dict, intensity: float) -> list[str]:
    tags = []
    if key and key["confidence"] >= LOW_CONFIDENCE:
        tags.append("dark" if key["mode"] == "minor" else "bright")
    if spec["centroid_hz"] >= 3000:
        tags.append("airy")
    elif spec["centroid_hz"] and spec["centroid_hz"] < 400:
        tags.append("heavy")
    pb = rhythm["per_beat"]
    tags.append("sparse" if pb < 0.5 else ("busy" if pb > 2.0 else "steady"))
    if rhythm["syncopation"] >= 0.4:
        tags.append("syncopated")
    elif rhythm["onsets"] and rhythm["syncopation"] <= 0.1:
        tags.append("straight")
    tags.append("intense" if intensity >= 0.66 else ("gentle" if intensity < 0.33 else "moderate"))
    return tags


def analyse_wav(entry: dict, info: dict, midi: dict | None) -> dict:
    """One WAV record: format, timing, bars, tail, role, loudness, spectrum, rhythm and tonal facts."""
    data = entry["path"].read_bytes()
    fmt = wav_format(data)
    frames, rate = read_float_wav_bytes(data, entry["name"])
    mono = frames.mean(axis=1).astype(np.float64)
    dur = len(mono) / rate
    end = active_end(mono)
    first = np.nonzero(np.abs(mono) > SILENCE)[0]
    lead_ms = round(float(first[0]) / rate * 1000, 1) if len(first) else None
    notes = midi["notes"] if midi else []
    end_beat = midi["end_beat_quarters"] if midi else 0.0
    bar_frames = BAR_S * rate
    active_bars = end / bar_frames
    total_bars = len(mono) / bar_frames
    n_audio = ceil_nice(active_bars) if end else 0
    spec = spectrum_features(mono, rate)
    onsets = onset_times(mono[:end], rate) if end else []
    role_guess = info["name_role"] if info["name_role"] in ("kick", "snare", "drums", "bass", "synth", "perc", "pad") else "other"
    tempo = decide_tempo(role_guess, mono, rate, notes, end_beat, dur) if notes else loop_period_tempo(mono, rate, n_audio)
    profile = tempo["profile"]
    scale = PROFILES[profile]["scale"] if profile in PROFILES else 1
    # whole bars of music: the MIDI's own phrase length when the audio covers it, else what the audio holds
    midi_bars = nice_bars(end_beat * scale / 4.0) if notes else None
    if midi_bars and end_beat * scale / 4.0 <= active_bars + 0.05:
        bars, bars_source = midi_bars, "midi"
    else:
        bars, bars_source = n_audio, "audio"
    tail_s = max(0.0, dur - bars * BAR_S)
    tail_seg = mono[int(bars * bar_frames):]
    tail = {"seconds": round(tail_s, 3), "bars": round(tail_s / BAR_S, 3), "peak_db": db(float(np.abs(tail_seg).max())) if len(tail_seg) else -120.0,
            "sounding_at_end": bool(len(tail_seg) and float(np.abs(tail_seg[-int(0.01 * rate):]).max()) > SILENCE)}
    tail["class"] = "none" if tail_s < 0.005 else (("cut while sounding" if tail_s >= 0.1 else "short") if tail["sounding_at_end"] else (
        "silence" if tail["peak_db"] < -60 else "release"))
    # positions of the notes (game beats) inside the audio's bars
    pos = [(n["beat"] * scale, n["dur"] * scale, n["pitch"]) for n in notes if n["beat"] * scale < bars * 4] if bars else []
    period = pattern_period(pos, bars) if pos and bars else None
    if notes:
        starts = [p[0] for p in pos]
        rhythm_src = "midi"
        rhythm = rhythm_measures(starts, bars)
        density = [0] * max(bars, 1)
        for s in starts:
            density[min(int(s // 4), len(density) - 1)] += 1
        mean_dur = float(np.mean([p[1] for p in pos])) if pos else 0.0
    else:
        starts = [t / BEAT_S for t in onsets if t < bars * BAR_S] if bars else []
        rhythm_src = "audio"
        rhythm = rhythm_measures(starts, bars)
        density = None
        mean_dur = 0.0
    per_beat = rhythm["per_beat"]
    role, role_basis = decide_role(info, spec, per_beat, notes, mean_dur)
    loud = loudness(frames, end)
    intensity = round(0.5 * min(1.0, max(0.0, (loud["rms_active_db"] + 32.0) / 20.0)) + 0.3 * min(1.0, per_beat / 3.0) + 0.2 * min(1.0, spec["high"] * 2.0), 3)
    rec = {"id": entry["id"], "name": entry["name"], "folder": entry["folder"], "kind": "wav", "sha256": sha256_file(entry["path"]),
           "size_bytes": entry["path"].stat().st_size, "source": info["source"], "family": info["family"], "group": info["group"],
           "variant": info["variant"], "part": info["part"], "timbre": info.get("timbre_label", info["timbre"]), "role": role, "role_basis": role_basis,
           "midi": midi["id"] if midi else None,
           "format": {"sample_rate": rate, "channels": fmt.get("channels", frames.shape[1]), "bits": fmt.get("bits"), "encoding": fmt.get("encoding")},
           "duration_s": round(dur, 3), "leading_silence_ms": lead_ms,
           "tempo": {"profile": profile, "measured_bpm": tempo["measured_bpm"], "method": tempo["method"], "header_bpm": midi["header_bpm"] if midi else None,
                     "evidence": tempo["evidence"], **({"note": tempo["note"]} if "note" in tempo else {})},
           "bars": {"musical": bars, "source": bars_source, "pattern": period, "repeats": (bars // period) if period else None,
                    "exact": round(total_bars, 3), "midi_bars": midi_bars, "audio_bars": n_audio},
           "tail": tail, "loudness": loud, "spectrum": spec, "rhythm": {"source": rhythm_src, **rhythm, "intensity": intensity}}
    if midi:
        rec["bars"]["midi_covers_audio"] = bool(midi_bars is None or midi_bars <= bars)
        rec["bars"]["midi_longer_than_audio"] = bool(midi_bars and midi_bars > max(bars, n_audio))
    rec["tonal"] = tonal_of(role, midi, scale, bars, mono, rate, spec)
    rec["mood"] = mood_tags(rec["tonal"].get("key"), spec, rhythm, intensity)
    rec["_density"] = density
    return rec


def tonal_of(role: str, midi: dict | None, scale: int, bars: int, mono: np.ndarray, rate: int, spec: dict) -> dict:
    """The pitch classes and estimated tonal centre of a pitched file (MIDI first, audio chroma when there is no MIDI); atonal for drums."""
    if role in ATONAL_ROLES:
        return {"atonal": True, "key": None, "basis": "role"}
    if midi and role not in ("kick", "snare", "drums"):
        h = np.zeros(12)
        for n in midi["notes"]:
            if bars and n["beat"] * scale >= bars * 4:
                continue
            h[n["pitch"] % 12] += n["dur"] * scale
        if h.sum() > 0:
            key = key_estimate(h)
            return {"atonal": False, "basis": "midi", "pitch_classes": [round(float(x / h.sum()), 3) for x in h], "key": key,
                    "lowest_pitch": min(n["pitch"] for n in midi["notes"]), "highest_pitch": max(n["pitch"] for n in midi["notes"])}
    if spec["flatness"] > 0.2 and spec["high"] > 0.4:
        return {"atonal": True, "key": None, "basis": "spectrum: noisy and bright"}
    ch = audio_chroma(mono, rate)
    key = key_estimate(ch)
    return {"atonal": False, "basis": "audio chroma", "pitch_classes": [round(float(x), 3) for x in ch], "key": key}


def midi_record(entry: dict, info: dict, profile: str, bars: int, wav_ids: list[str]) -> dict:
    scale = PROFILES[profile]["scale"] if profile in PROFILES else 1
    m = analyse_midi(entry["path"], scale, bars)
    notes = m["notes"]
    nb = bars if bars else max(1, int(math.ceil(m["end_beat_quarters"] * scale / 4.0)))
    pos = [(n["beat"] * scale, n["dur"] * scale, n["pitch"]) for n in notes if n["beat"] * scale < nb * 4]
    dens = [0] * nb
    for p in pos:
        dens[min(int(p[0] // 4), nb - 1)] += 1
    vel = [n["velocity"] for n in notes]
    return {"id": entry["id"], "name": entry["name"], "folder": entry["folder"], "kind": "midi", "sha256": sha256_file(entry["path"]),
            "size_bytes": entry["path"].stat().st_size, "family": info["family"], "group": info["group"], "part": info["part"], "variant": info["variant"],
            "audio": wav_ids, "header_bpm": m["header_bpm"], "ppq": m["ppq"], "format": m["format"], "profile": profile, "scale": scale,
            "end_beat_quarters": m["end_beat_quarters"], "bars_estimate": nice_bars(m["end_beat_quarters"] * scale / 4.0), "bars_covered": nb,
            "notes_count": len(notes), "pitches": sorted({n["pitch"] for n in notes}),
            "velocity": {"min": min(vel), "mean": round(float(np.mean(vel)), 1), "max": max(vel)} if vel else None,
            "duration_beats": {"min": round(min(n["dur"] for n in notes) * scale, 3), "mean": round(float(np.mean([n["dur"] for n in notes])) * scale, 3),
                               "max": round(max(n["dur"] for n in notes) * scale, 3)} if notes else None,
            "drum_notes": drum_note_classes(notes), "pattern_bars": pattern_period(pos, nb) if pos else None, "density_per_bar": dens,
            "notes": [[round(n["beat"] * scale, 4), round(n["dur"] * scale, 4), n["pitch"], n["velocity"]] for n in notes if n["beat"] * scale < nb * 4]}


# --- families and compatibility ---------------------------------------------------------------------------------------

def build_families(files: list[dict], midis: dict[str, dict]) -> list[dict]:
    fam: dict[str, dict] = {}
    by_id = {f["id"]: f for f in files}
    for f in files:
        d = fam.setdefault(f["family"], {"id": f["family"], "kind": {"beat_shaper": "beat_shaper_project", "ableton": "ableton_pattern"}.get(
            f["source"], "unrecognised"), "folder": f["folder"], "members": [], "sets": {}, "roles": {}})
        d["members"].append(f["id"])
        s = d["sets"].setdefault(f["group"], {"group": f["group"], "variant": f["variant"], "parts": {}})
        s["parts"].setdefault(f["role"], []).append(f["id"])
        r = d["roles"].setdefault(f["role"], {"files": [], "bars": set(), "phrase": set(), "profiles": set(), "hist": np.zeros(12), "keys": []})
        r["files"].append(f["id"])
        r["bars"].add(f["bars"]["musical"])
        r["profiles"].add(f["tempo"]["profile"])
        m = midis.get(f["midi"]) if f["midi"] else None
        r["phrase"].add(f["bars"]["pattern"] or f["bars"]["musical"])
        if not f["tonal"]["atonal"] and f["tonal"].get("pitch_classes") and f["tonal"]["key"]:
            key = (f["midi"] or f["id"])  # timbres of one MIDI count once
            if key not in r["keys"]:
                r["keys"].append(key)
                r["hist"] += np.array(f["tonal"]["pitch_classes"])
    out = []
    for fid in sorted(fam):
        d = fam[fid]
        roles = {}
        for role in sorted(d["roles"]):
            r = d["roles"][role]
            profiles = sorted(r["profiles"] - {"unknown"})
            entry = {"files": sorted(r["files"]), "bars": sorted(r["bars"]), "phrase_bars": sorted(r["phrase"]),
                     "profile": profiles[0] if len(profiles) == 1 else ("unknown" if not profiles else "mixed"),
                     "atonal": role in ATONAL_ROLES}
            if role not in ATONAL_ROLES:
                entry["key"] = key_estimate(r["hist"]) if r["hist"].sum() > 0 else None
            roles[role] = entry
        sets = sorted(d["sets"].values(), key=lambda s: s["group"])
        d2 = {"id": fid, "kind": d["kind"], "folder": d["folder"], "members": sorted(d["members"]), "roles": roles,
              "sets": [{"group": s["group"], "variant": s["variant"], "parts": {k: sorted(v) for k, v in sorted(s["parts"].items())}} for s in sets]}
        timbres = sorted({by_id[m]["timbre"] for m in d["members"] if by_id[m]["timbre"]})
        if timbres:
            d2["timbres"] = timbres
        out.append(d2)
    return out


def length_relation(a: list[int], b: list[int]) -> str:
    """equal | tiles (the shorter phrase repeats a whole number of times in the longer) | no."""
    if set(a) & set(b):
        return "equal"
    for x in a:
        for y in b:
            lo, hi = sorted((x, y))
            if lo and hi % lo == 0:
                return "tiles"
    return "no"


def complementary(x: str, y: str) -> bool:
    """Roles that can be layered: different groups (rhythm, bass, harmony, fx) or a kick with a snare."""
    return GROUPS.get(x) != GROUPS.get(y) or {x, y} == {"kick", "snare"}


def compatibility(families: list[dict]) -> list[dict]:
    """One row per pair of families with at least one complementary pair of parts. Across families a combination of parts is `ok` only when the phrase
    lengths are equal or tile, the profiles are equal and known, and the tonal centres are the same or relative (a 'near' key, a low confidence or
    a missing estimate makes it `uncertain`; disagreeing keys are not compatible) or one side is atonal. Tempo alone never decides."""
    rows = []
    for i, a in enumerate(families):
        for b in families[i + 1:]:
            combos = []
            same_source = a["folder"].split("/")[0] == b["folder"].split("/")[0]
            for ra, da in a["roles"].items():
                for rb, db_ in b["roles"].items():
                    if not complementary(ra, rb):
                        continue
                    ln = length_relation(da["phrase_bars"], db_["phrase_bars"])
                    pa, pb = da["profile"], db_["profile"]
                    prof = "same" if pa == pb and pa in PROFILES else ("unknown" if "unknown" in (pa, pb) or "mixed" in (pa, pb) else "differs")
                    ka, kb = da.get("key"), db_.get("key")
                    if da["atonal"] or db_["atonal"]:
                        tonal, uncertain_tonal = "atonal", False
                    elif ka and kb:
                        tonal = key_distance(ka, kb)
                        uncertain_tonal = min(ka["confidence"], kb["confidence"]) < LOW_CONFIDENCE or tonal == "near"
                    else:
                        tonal, uncertain_tonal = "unknown", True
                    ok = ln != "no" and prof == "same" and tonal in ("atonal", "same", "relative", "near")
                    why = []
                    if ln == "no":
                        why.append("phrase lengths do not tile")
                    if prof != "same":
                        why.append(f"profiles {prof}")
                    if tonal == "disagree":
                        why.append("tonal centres disagree")
                    if tonal == "unknown":
                        why.append("no tonal estimate")
                    doubt = []
                    if ok:
                        if ln == "tiles":
                            doubt.append("phrases tile rather than match")
                        if uncertain_tonal:
                            doubt.append("tonal estimate weak or nearby key")
                        if tonal == "atonal" and not same_source:
                            doubt.append("only rules (no shared source folder) support it")
                    combos.append({"a": ra, "b": rb, "ok": ok, "uncertain": bool(doubt), "length": ln, "profile": prof, "tonal": tonal,
                                   **({"against": why} if why else {}), **({"doubt": doubt} if doubt else {})})
            if not combos:
                continue
            good = [c for c in combos if c["ok"]]
            fa, fb = a["folder"], b["folder"]
            nums = {re.sub(r"\D", "", x["id"].split("_")[-1]) for x in (a, b) if x["kind"] == "ableton_pattern"}
            basis = []
            if fa == fb:
                basis.append("same folder")
            if a["kind"] == b["kind"] == "ableton_pattern" and fa == fb and len(nums) == 1 and "" not in nums:
                basis.append("same pattern number")
            rows.append({"a": a["id"], "b": b["id"], "compatible": bool(good), "uncertain": bool(good) and all(c["uncertain"] for c in good),
                         "basis": basis, "combos": combos})
    return rows


def within_family(families: list[dict], files: list[dict]) -> list[dict]:
    """Variants of one Beat Shaper project that were exported as separate sets: flagged when their tonal estimates disagree."""
    by_id = {f["id"]: f for f in files}
    out = []
    for fam in families:
        if len(fam["sets"]) < 2:
            continue
        keys = {}
        for s in fam["sets"]:
            h = np.zeros(12)
            for role, ids in s["parts"].items():
                for fid in ids:
                    t = by_id[fid]["tonal"]
                    if not t["atonal"] and t.get("pitch_classes"):
                        h += np.array(t["pitch_classes"])
            keys[s["group"]] = key_estimate(h) if h.sum() > 0 else None
        names = {k["name"] for k in keys.values() if k}
        out.append({"family": fam["id"], "sets": len(fam["sets"]), "keys": {g: (k["name"] if k else None) for g, k in keys.items()},
                    "uncertain": len(names) > 1 or any(k and k["confidence"] < LOW_CONFIDENCE for k in keys.values())})
    return out


# --- the catalogue -------------------------------------------------------------------------------------------------------

def build_catalogue(sources: list[Path]) -> dict:
    entries = discover(sources)
    parsed = {e["id"]: parse_name(e["folder"], e["name"]) for e in entries}
    midi_by_key, wav_by_key = {}, defaultdict(list)
    for e in entries:
        k = pair_key(parsed[e["id"]], e["folder"])
        if e["kind"] == "midi":
            midi_by_key[k] = e
        else:
            wav_by_key[k].append(e)
    # a MIDI is read at the profile its audio measures: analyse the WAVs with the MIDI notes in beats first
    midi_facts: dict[str, dict] = {}
    for k, e in midi_by_key.items():
        midi_facts[e["id"]] = {"id": e["id"], **analyse_midi(e["path"], 1, 0)}
    files, midis = [], {}
    for k in sorted(wav_by_key, key=lambda k: tuple(map(str, k))):
        me = midi_by_key.get(k)
        for e in sorted(wav_by_key[k], key=lambda e: e["id"]):
            files.append(analyse_wav(e, parsed[e["id"]], midi_facts[me["id"]] if me else None))
    for f in files:
        f["_pair_key"] = None
    by_midi = defaultdict(list)
    for f in files:
        if f["midi"]:
            by_midi[f["midi"]].append(f)
    for k, e in sorted(midi_by_key.items(), key=lambda kv: kv[1]["id"]):
        ws = by_midi.get(e["id"], [])
        profiles = Counter(w["tempo"]["profile"] for w in ws if w["tempo"]["profile"] != "unknown")
        profile = profiles.most_common(1)[0][0] if profiles else "unknown"
        bars = Counter(w["bars"]["musical"] for w in ws).most_common(1)[0][0] if ws else 0
        midis[e["id"]] = midi_record(e, parsed[e["id"]], profile, bars, sorted(w["id"] for w in ws))
    # identical content under other names
    shas = defaultdict(list)
    for f in files + list(midis.values()):
        shas[f["sha256"]].append(f["id"])
    sigs = defaultdict(list)
    for m in midis.values():
        sigs[json.dumps([n[:3] for n in m["notes"]])].append(m["id"])
    for rec in files + list(midis.values()):
        dup = sorted(x for x in shas[rec["sha256"]] if x != rec["id"])
        if dup:
            rec["duplicate_of"] = dup
    for m in midis.values():
        twins = sorted(x for x in sigs[json.dumps([n[:3] for n in m["notes"]])] if x != m["id"])
        if twins:
            m["same_notes_as"] = twins
    for f in files:
        density = f.pop("_density")
        f.pop("_pair_key", None)
        if f["midi"] is None:
            f["onsets_per_bar"] = density
    files.sort(key=lambda f: f["id"])
    families = build_families(files, midis)
    comp = compatibility(families)
    wf = within_family(families, files)
    summary = summarise(files, midis, families, comp)
    return {"schema": SCHEMA, "tool": "tools/content/catalogue.py",
            "sources": [{"name": s.name, "files": sum(1 for e in entries if e["id"].split("/")[0] == s.name)} for s in sources],
            "summary": summary, "files": files, "midis": [midis[k] for k in sorted(midis)], "families": families, "within_family": wf,
            "compatibility": comp}


def summarise(files: list[dict], midis: dict, families: list[dict], comp: list[dict]) -> dict:
    folders: dict[str, dict] = {}
    for f in files:
        d = folders.setdefault(f["folder"], {"wavs": 0, "midis": 0, "profiles": Counter(), "bars": Counter(), "header_bpm": Counter(), "roles": Counter()})
        d["wavs"] += 1
        d["profiles"][f["tempo"]["profile"]] += 1
        d["bars"][f["bars"]["musical"]] += 1
        d["roles"][f["role"]] += 1
        if f["tempo"]["header_bpm"] is not None:
            d["header_bpm"][f["tempo"]["header_bpm"]] += 1
    for m in midis.values():
        folders.setdefault(m["folder"], {"wavs": 0, "midis": 0, "profiles": Counter(), "bars": Counter(), "header_bpm": Counter(), "roles": Counter()})["midis"] += 1
    return {"wavs": len(files), "midis": len(midis), "families": len(families),
            "folders": {k: {"wavs": v["wavs"], "midis": v["midis"], "profiles": dict(sorted(v["profiles"].items())),
                            "bars": {str(b): n for b, n in sorted(v["bars"].items())}, "midi_header_bpm": {str(b): n for b, n in sorted(v["header_bpm"].items())},
                            "roles": dict(sorted(v["roles"].items()))} for k, v in sorted(folders.items())},
            "family_pairs": len(comp), "compatible_pairs": sum(1 for r in comp if r["compatible"]),
            "uncertain_pairs": sum(1 for r in comp if r["compatible"] and r["uncertain"])}


# --- output ---------------------------------------------------------------------------------------------------------------

def dump(value, level: int = 0, depth: int = 3) -> str:
    """JSON with the top `depth` levels spread over lines (lists of records one per line) and everything below on one line."""
    pad = " " * (level + 1)
    if isinstance(value, dict) and level < depth and value:
        rows = [f"{pad}{json.dumps(k)}: {dump(v, level + 1, depth)}" for k, v in value.items()]
        return "{\n" + ",\n".join(rows) + "\n" + " " * level + "}"
    if isinstance(value, list) and level < depth and value and all(isinstance(v, dict) for v in value):
        return "[\n" + ",\n".join(pad + dump(v, level + 1, depth) for v in value) + "\n" + " " * level + "]"
    return json.dumps(value, separators=(", ", ": "), ensure_ascii=False)


def catalogue_text(cat: dict) -> str:
    return dump(cat) + "\n"


def fmt_key(t: dict) -> str:
    if t["atonal"]:
        return "atonal"
    k = t.get("key")
    return f"{k['name']} ({k['confidence']:.2f})" if k else "-"


def markdown(cat: dict) -> str:
    L = ["# Music catalogue", "",
         "Written by `python tools/content/catalogue.py` from the owner's folders (never modified; `.asd` and `.import` files ignored). Do not edit; regenerate.",
         "The machine-readable form is `content/music/catalogue.json` (schema 1); the arrangement tool reads only that. Tempo is measured, never taken from the MIDI header.", ""]
    s = cat["summary"]
    L += ["## Summary", "", f"{s['wavs']} WAV files, {s['midis']} MIDI files, {s['families']} families; {s['family_pairs']} family pairs have parts that can be layered, "
          f"{s['compatible_pairs']} pass the rules and {s['uncertain_pairs']} of those are flagged uncertain.", "",
          "| Folder | WAV | MIDI | Profile | Musical bars | MIDI header BPM |", "| --- | --- | --- | --- | --- | --- |"]
    for k, v in s["folders"].items():
        L.append(f"| {k} | {v['wavs']} | {v['midis']} | {', '.join(f'{p} x{n}' for p, n in v['profiles'].items()) or '-'} | "
                 f"{', '.join(f'{b} x{n}' for b, n in v['bars'].items()) or '-'} | {', '.join(f'{b} x{n}' for b, n in v['midi_header_bpm'].items()) or 'none'} |")
    L += ["", "## Facts the audio shows", ""]
    for line in facts(cat):
        L.append(f"- {line}")
    L += ["", "## Files by folder", "",
          "Profile `174x1`: one source quarter is one game beat; `87x2`: one quarter is two. Bars are whole game bars of music (4 beats at 174 BPM); `pat` is the "
          "repeating pattern length of the MIDI; tail is the release after the musical end. Key is a Krumhansl-Schmuckler estimate with its confidence (advisory). "
          "Clip = samples at full scale (an over-full-scale float counts).", ""]
    folders: dict[str, list] = defaultdict(list)
    for f in cat["files"]:
        folders[f["folder"]].append(f)
    for folder in sorted(folders):
        L += [f"### {folder}", "", "| File | Role | Family | Pair | Profile | BPM | Bars (pat) | Lead ms | Tail s | Key | RMS | Peak | Clip |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for f in folders[folder]:
            pair = "MIDI" if f["midi"] else "audio only"
            bpm = f["tempo"]["measured_bpm"]
            lead = f["leading_silence_ms"]
            L.append(f"| {f['name']} | {f['role']} | {f['family']} | {pair} | {f['tempo']['profile']} | {'-' if bpm is None else f'{bpm:.1f}'} | "
                     f"{f['bars']['musical']} ({f['bars']['pattern'] or '-'}) | {'-' if lead is None else f'{lead:.0f}'} | {f['tail']['seconds']:.2f} {f['tail']['class']} | "
                     f"{fmt_key(f['tonal'])} | {f['loudness']['rms_db']:.1f} | {f['loudness']['peak_db']:.1f} | "
                     f"{f['loudness']['clipping_samples'] + f['loudness']['over_full_scale']} |")
        L.append("")
    L += ["## Families", "",
          "A family is the strongest grouping the exports give: a Beat Shaper project with all its variants, or an Ableton pattern with all its timbre renders.", "",
          "| Family | Kind | Sets | Roles (bars, profile) | Timbres | Key |", "| --- | --- | --- | --- | --- | --- |"]
    for fam in cat["families"]:
        roles = "; ".join(f"{r} ({'/'.join(map(str, d['bars']))}, {d['profile']})" for r, d in fam["roles"].items())
        keys = "; ".join(f"{r}: {d['key']['name']} ({d['key']['confidence']:.2f})" for r, d in fam["roles"].items() if d.get("key"))
        L.append(f"| {fam['id']} | {fam['kind']} | {len(fam['sets'])} | {roles} | {', '.join(fam.get('timbres', [])) or '-'} | {keys or 'atonal'} |")
    L += ["", "Variants of a Beat Shaper project whose tonal estimates disagree or are weak (the variants may be different progressions; listen before mixing sets):", ""]
    flagged = [w for w in cat["within_family"] if w["uncertain"]]
    L += [f"- {w['family']}: " + ", ".join(f"{g.split(':')[-1]} {k or '-'}" for g, k in w["keys"].items()) for w in flagged] or ["- none"]
    comp = cat["compatibility"]
    ok = [r for r in comp if r["compatible"]]
    L += ["", "## Compatibility", "",
          "Within a family every part is compatible (the export grouping is the strongest evidence). Across families a pair of parts is compatible only when the "
          "phrase lengths are equal or tile, the profiles are the same, and the tonal centres are the same or relative or one part is atonal; a nearby key (parallel "
          "or a fifth), a low-confidence estimate or a phrase that tiles rather than matches makes it `uncertain`; keys that disagree are incompatible. "
          "A shared tempo never decides anything. The full table (every family pair, every combination of parts, why each failed) is in the JSON.", "",
          f"{len(comp)} family pairs have parts that can be layered; {len(ok)} are compatible ({sum(1 for r in ok if not r['uncertain'])} firm, "
          f"{sum(1 for r in ok if r['uncertain'])} uncertain).", ""]
    firm = [r for r in ok if not r["uncertain"]]
    new = [r for r in firm if any("ToAddTry3" in fam_folder(cat, x) or "ToAddTry1" in fam_folder(cat, x) for x in (r["a"], r["b"]))]
    L += ["### Compatible pairs involving ToAddTry1 or ToAddTry3 (firm)", "", "| Family A | Family B | Basis | Parts that fit |", "| --- | --- | --- | --- |"]
    for r in new[:80]:
        L.append(f"| {r['a']} | {r['b']} | {', '.join(r['basis']) or 'rules only'} | " + ", ".join(f"{c['a']}+{c['b']}" for c in r["combos"] if c["ok"] and not c["uncertain"]) + " |")
    if len(new) > 80:
        L.append(f"| ... | {len(new) - 80} more in the JSON | | |")
    L += ["", "### Flagged for the owner's ear (uncertain)", "",
          "Compatible by the rules but resting on a low-confidence or nearby key, or a phrase that tiles. Listen before relying on them.", "",
          "| Family A | Family B | Basis | Parts | Why uncertain |", "| --- | --- | --- | --- | --- |"]
    unc = [r for r in ok if r["uncertain"]]
    shown = 0
    for r in unc:
        if shown >= 60:
            break
        parts = [c for c in r["combos"] if c["ok"] and c["uncertain"]]
        why = sorted({d for c in parts for d in c.get("doubt", [])})
        L.append(f"| {r['a']} | {r['b']} | {', '.join(r['basis']) or 'rules only'} | {', '.join(c['a'] + '+' + c['b'] for c in parts[:4])} | {', '.join(why)} |")
        shown += 1
    if len(unc) > shown:
        L.append(f"| ... | {len(unc) - shown} more in the JSON | | | |")
    L += ["", "## Same notes under another name", ""]
    twins = [m for m in cat["midis"] if m.get("same_notes_as")]
    L += [f"- `{m['id']}` has the same notes as " + ", ".join(f"`{t}`" for t in m["same_notes_as"]) for m in twins] or ["- none"]
    L += [""]
    return "\n".join(L)


def fam_folder(cat: dict, fid: str) -> str:
    return next((f["folder"] for f in cat["families"] if f["id"] == fid), "")


def facts(cat: dict) -> list[str]:
    """Sentences computed from the data (not typed in): the contradictions the brief asks to be stated."""
    out = []
    by_folder: dict[str, list] = defaultdict(list)
    for f in cat["files"]:
        by_folder[f["folder"]].append(f)
    for folder, fs in sorted(by_folder.items()):
        bs = [f for f in fs if f["source"] == "beat_shaper" and f["midi"]]
        if bs:
            heads = sorted({f["tempo"]["header_bpm"] for f in bs if f["tempo"]["header_bpm"] is not None})
            prof = Counter(f["tempo"]["profile"] for f in bs)
            bars = Counter(f["bars"]["musical"] for f in bs)
            out.append(f"{folder}: {len(bs)} Beat Shaper WAVs with MIDI; MIDI headers say {', '.join(f'{h:g}' for h in heads)} BPM, the audio measures "
                       + ", ".join(f"{p} x{n}" for p, n in sorted(prof.items())) + f"; musical length " + ", ".join(f"{b} bars x{n}" for b, n in sorted(bars.items())) + ".")
        ab = [f for f in fs if f["source"] == "ableton"]
        if ab:
            bars = Counter(f["bars"]["musical"] for f in ab)
            prof = Counter(f["tempo"]["profile"] for f in ab)
            out.append(f"{folder}: {len(ab)} Ableton renders (MIDI carries no tempo); " + ", ".join(f"{p} x{n}" for p, n in sorted(prof.items())) + "; musical length "
                       + ", ".join(f"{b} bars x{n}" for b, n in sorted(bars.items())) + ".")
        longer = [f for f in fs if f["bars"].get("midi_longer_than_audio")]
        if longer:
            out.append(f"{folder}: {len(longer)} render(s) shorter than their MIDI (the MIDI runs on past the recording): "
                       + ", ".join(sorted({f['name'] for f in longer})[:6]) + ".")
        tails = [f for f in fs if f["tail"]["class"] in ("cut while sounding",)]
        if tails:
            out.append(f"{folder}: {len(tails)} render(s) still sounding at their end ({', '.join(sorted(f['name'] for f in tails)[:6])}); the release is cut there.")
        clip = [f for f in fs if f["loudness"]["clipping_risk"] == "clipped"]
        if clip:
            out.append(f"{folder}: {len(clip)} file(s) clip or exceed full scale ({', '.join(sorted(f['name'] for f in clip)[:6])}).")
    reps = [f for f in cat["files"] if f["bars"]["repeats"] and f["bars"]["repeats"] > 1 and f["source"] == "ableton"]
    if reps:
        out.append("Ableton renders whose MIDI is a shorter pattern repeated: " + ", ".join(
            f"{f['name']} ({f['bars']['pattern']}-bar pattern x{f['bars']['repeats']})" for f in reps[:12]) + ".")
    return out


def run(sources: list[Path]) -> tuple[str, str, dict]:
    cat = build_catalogue(sources)
    return catalogue_text(cat), markdown(cat) + "\n", cat


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", action="append", help="a folder to catalogue (repeatable); default: ToAddTry1, ToAddTry2, ToAddTry3 found by name")
    ap.add_argument("--out", default=str(CATALOGUE_JSON))
    ap.add_argument("--md", default=str(CATALOGUE_MD))
    ap.add_argument("--check", action="store_true", help="compare with the files on disk, write nothing")
    ap.add_argument("--print", action="store_true", dest="show", help="print the summary only")
    args = ap.parse_args()
    sources, missing = find_sources(args.source)
    for m in missing:
        print(f"WARNING source folder '{m}' not found")
    if not sources:
        print("ERROR no source folders found; pass --source DIR or set RW_MUSIC_SOURCES")
        return 1
    try:
        js, md, cat = run(sources)
    except ContentError as exc:
        print(f"ERROR {exc}")
        return 1
    s = cat["summary"]
    print(f"{s['wavs']} WAV, {s['midis']} MIDI, {s['families']} families, {s['family_pairs']} layerable family pairs, {s['compatible_pairs']} compatible, "
          f"{s['uncertain_pairs']} uncertain")
    if args.show:
        return 0
    out, md_path = Path(args.out), Path(args.md)
    if args.check:
        same = out.exists() and out.read_text(encoding="utf-8") == js and md_path.exists() and md_path.read_text(encoding="utf-8") == md
        print("up to date" if same else "STALE: regenerate with python tools/content/catalogue.py")
        return 0 if same else 1
    write_text_lf(out, js)
    write_text_lf(md_path, md)
    print(f"wrote {out} and {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
