#!/usr/bin/env python3
"""Check a track pack against docs/TRACK_PACK_FORMAT.md. Needs only numpy and ffmpeg/ffprobe.

    python3 tools/audio_import/validate_track.py /home/joe/rw-audio-work/packs/<id> [--recording FILE]
        [--sum-tol-db -24] [--quick]

Exits 1 on any violation, 0 otherwise, after printing every problem found and per-voice cue counts and
densities. The recording (for the 'stems sum to the recording' and alignment checks) is taken from
--recording or from source.input_path in track.json; if neither can be read that check is reported as skipped.
--quick skips decoding the audio (header, voices, sections and charts only).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_io import PACK_RATE, db, decode, frame_rms, probe  # noqa: E402

FORMAT = "rhythm_warfare.track.v1"
KEY_RE = re.compile(r"^[a-z0-9_]+$")
ROLES = {"intro", "build", "drop", "breakdown", "outro", "other"}
EPS = 1e-6  # same float slack as the game loader (src/track/track_pack.gd): a gap of exactly half a beat is allowed
LEN_TOL = 0.005
# a cue must sit on sound in its own voice: within this many dB of the voice's loud level (95th percentile of
# 10 ms frames) and of the whole track at that moment
CUE_OWN_DB = -35.0
CUE_REL_DB = -30.0


def playability_violations(cues: list[dict], bpm: float) -> list[tuple[int, str]]:
    """Every broken playability rule as (index of the later cue, message). cues must be sorted by t."""
    B = 60.0 / bpm
    out: list[tuple[int, str]] = []
    maxdur = max((float(c.get("dur", 0) or 0) for c in cues), default=0.0)
    span = maxdur + B
    lo = 0
    for i, c in enumerate(cues):
        t, p, d = c["t"], c["pad"], c["dur"]
        if d > 0 and d < 0.5 * B - EPS:
            out.append((i, f"hold {d:.3f}s shorter than 0.5 beat ({0.5 * B:.3f}s)"))
        while cues[lo]["t"] < t - span:
            lo += 1
        active_pads = {p}
        for j in range(lo, i):
            o = cues[j]
            gap = t - o["t"]
            end = o["t"] + o["dur"]
            if o["pad"] == p:
                if gap < 0.5 * B - EPS:
                    out.append((i, f"same pad {p} cues {gap:.3f}s apart (< 0.5 beat)"))
                if o["dur"] > 0 and t < end + 0.25 * B - EPS:
                    out.append((i, f"pad {p} cue at {t:.3f} inside or within 0.25 beat after its own hold ending {end:.3f}"))
            elif (o["pad"] - 1) // 2 == (p - 1) // 2:
                if gap < 0.5 * B - EPS:
                    out.append((i, f"same thumb pads {o['pad']} and {p} {gap:.3f}s apart (< 0.5 beat)"))
                if o["dur"] > 0 and t <= end + EPS:
                    out.append((i, f"pad {p} at {t:.3f} while same-thumb pad {o['pad']} is held until {end:.3f}"))
            if gap <= max(o["dur"], 0.03):
                active_pads.add(o["pad"])
        if len(active_pads) > 2:
            out.append((i, f"{len(active_pads)} pads at once at {t:.3f}"))
    return out


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notes: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def check_structure(pack: Path, tj: dict, r: Report) -> None:
    if tj.get("format") != FORMAT:
        r.err(f"format is {tj.get('format')!r}, expected {FORMAT!r}")
    tid = tj.get("id")
    if not isinstance(tid, str) or not KEY_RE.match(tid):
        r.err(f"id {tid!r} is not lower case letters, digits and underscores")
    elif tid != pack.name:
        r.err(f"id {tid!r} differs from the folder name {pack.name!r}")
    dur = tj.get("duration_s")
    if not _num(dur) or dur <= 0:
        r.err(f"duration_s {dur!r} is not > 0")
    voices = tj.get("voices")
    backing = tj.get("backing", [])
    if not isinstance(voices, list) or len(voices) != 4:
        r.err(f"voices must have exactly 4 entries, has {len(voices) if isinstance(voices, list) else voices!r}")
        voices = voices if isinstance(voices, list) else []
    pads = [v.get("pad") for v in voices if isinstance(v, dict)]
    if sorted(p for p in pads if isinstance(p, int)) != [1, 2, 3, 4] or len(pads) != 4:
        r.err(f"voice pads are {pads}, must be 1, 2, 3 and 4 once each")
    if not isinstance(backing, list):
        r.err("backing must be a list")
        backing = []
    keys = []
    for kind, lst in (("voice", voices), ("backing", backing)):
        for v in lst:
            if not isinstance(v, dict):
                r.err(f"{kind} entry {v!r} is not an object")
                continue
            k = v.get("key")
            keys.append(k)
            if not isinstance(k, str) or not KEY_RE.match(k):
                r.err(f"{kind} key {k!r} is not lower case letters, digits and underscores")
            if kind == "voice":
                lab = v.get("label")
                if not isinstance(lab, str) or not lab or len(lab) > 24:
                    r.err(f"voice {k}: label {lab!r} must be a short non-empty string")
            g = v.get("gain", 1.0)
            if not _num(g) or not 0 <= g <= 2:
                r.err(f"{kind} {k}: gain {g!r} not in 0..2")
            s = v.get("stem")
            if not isinstance(s, str) or s.startswith("/") or ".." in Path(s).parts or not s:
                r.err(f"{kind} {k}: stem path {s!r} must be relative inside the pack")
            elif not (pack / s).is_file():
                r.err(f"{kind} {k}: stem file {s} missing")
            elif not s.lower().endswith(".ogg"):
                r.err(f"{kind} {k}: stem {s} is not an .ogg file")
    if len(set(keys)) != len(keys):
        r.err(f"keys are not unique across voices and backing: {keys}")
    tempo = tj.get("tempo", {})
    if not isinstance(tempo, dict) or not _num(tempo.get("bpm")) or tempo["bpm"] <= 0:
        r.err(f"tempo.bpm {tempo.get('bpm') if isinstance(tempo, dict) else tempo!r} is not > 0")
        tempo = {"bpm": 120.0}
    if not _num(tempo.get("first_downbeat_s", 0)) or tempo.get("first_downbeat_s", 0) < 0:
        r.err("tempo.first_downbeat_s must be >= 0")
    if tempo.get("beats_per_bar", 4) != 4:
        r.err("tempo.beats_per_bar must be 4")
    c = tempo.get("confidence", 0)
    if not _num(c) or not 0 <= c <= 1:
        r.err("tempo.confidence must be 0..1")
    secs = tj.get("sections", [])
    prev_end = 0.0
    if not isinstance(secs, list):
        r.err("sections must be a list")
        secs = []
    for s in secs:
        a, b = s.get("start_s"), s.get("end_s")
        if not (_num(a) and _num(b)) or a >= b:
            r.err(f"section {s.get('id')}: bad times {a}..{b}")
            continue
        if s.get("role") not in ROLES:
            r.err(f"section {s.get('id')}: role {s.get('role')!r} not one of {sorted(ROLES)}")
        if a < prev_end - EPS:
            r.err(f"section {s.get('id')} starts at {a} before the previous section ends ({prev_end}) or out of order")
        if a < -EPS or (_num(dur) and b > dur + EPS):
            r.err(f"section {s.get('id')} {a}..{b} not inside the track")
        prev_end = b
    rules = tj.get("rules", {})
    if not isinstance(rules, dict) or not _num(rules.get("restore_after_idle_beats", 8)) or rules.get("restore_after_idle_beats", 8) <= 0:
        r.err("rules.restore_after_idle_beats must be a positive number")
    charts = tj.get("charts")
    if not isinstance(charts, dict) or tj.get("default_chart") not in charts:
        r.err(f"default_chart {tj.get('default_chart')!r} not among charts {list(charts) if isinstance(charts, dict) else charts!r}")
        charts = charts if isinstance(charts, dict) else {}
    if "source" in tj and not isinstance(tj["source"], dict):
        r.err("source must be an object")
    for name, cues in charts.items():
        if not isinstance(cues, list):
            r.err(f"chart {name} is not a list")
            continue
        ok = True
        for i, cu in enumerate(cues):
            if not isinstance(cu, dict) or not all(_num(cu.get(k)) for k in ("t", "pad", "dur", "conf")):
                r.err(f"chart {name} cue {i}: needs numeric t, pad, dur, conf: {cu!r}")
                ok = False
                continue
            if cu["pad"] not in (1, 2, 3, 4):
                r.err(f"chart {name} cue {i}: pad {cu['pad']} not 1..4")
                ok = False
            if cu["dur"] < 0:
                r.err(f"chart {name} cue {i}: dur < 0")
            if not 0 <= cu["conf"] <= 1:
                r.err(f"chart {name} cue {i}: conf {cu['conf']} not 0..1")
            if cu["t"] < 1.0 - 1e-9:
                r.err(f"chart {name} cue {i}: t {cu['t']} is in the first second")
            if _num(dur) and cu["t"] + cu["dur"] > dur - 0.5 + 1e-9:
                r.err(f"chart {name} cue {i}: ends at {cu['t'] + cu['dur']:.3f}, after duration - 0.5 s")
            if i and cu["t"] < cues[i - 1]["t"]:
                r.err(f"chart {name} cue {i}: not sorted by t ({cu['t']} after {cues[i - 1]['t']})")
                ok = False
        if ok:
            for i, msg in playability_violations(cues, tempo["bpm"]):
                r.err(f"chart {name} cue {i} (t={cues[i]['t']:.3f}): {msg}")


def check_audio(pack: Path, tj: dict, r: Report, recording: str | None, sum_tol_db: float) -> dict:
    """Stem format, length, alignment, sum against the recording, and that every cue sits on sound."""
    entries = [(v, True) for v in tj["voices"]] + [(b, False) for b in tj.get("backing", [])]
    total = None
    lengths = {}
    monos = {}
    for v, is_voice in entries:
        f = pack / v["stem"]
        info = probe(f)
        if info["codec"] != "vorbis":
            r.err(f"{v['key']}: codec {info['codec']} is not Vorbis")
        if info["rate"] != PACK_RATE:
            r.err(f"{v['key']}: {info['rate']} Hz, expected {PACK_RATE}")
        if info["channels"] != 2:
            r.err(f"{v['key']}: {info['channels']} channels, expected 2")
        x, _ = decode(f, rate=PACK_RATE)
        x *= float(v.get("gain", 1.0))
        lengths[v["key"]] = len(x)
        if is_voice:
            monos[v["key"]] = x.mean(1)
        if total is None:
            total = x.astype(np.float64)
        else:
            n = min(len(total), len(x))
            total = total[:n] + x[:n]
    n_all = list(lengths.values())
    spread = (max(n_all) - min(n_all)) / PACK_RATE
    if spread > LEN_TOL:
        r.err(f"stem lengths differ by {spread * 1000:.1f} ms (> 5 ms): {lengths}")
    dur_files = max(n_all) / PACK_RATE
    if abs(dur_files - tj["duration_s"]) > LEN_TOL:
        r.err(f"duration_s {tj['duration_s']} but stems are {dur_files:.4f} s")
    r.note(f"stems: {len(entries)} files, {PACK_RATE} Hz stereo Vorbis, length {dur_files:.3f} s, spread {spread * 1000:.2f} ms")
    stats = {"lengths": lengths}
    rec_path = recording or tj.get("source", {}).get("input_path")
    if rec_path and Path(rec_path).is_file():
        rec, _ = decode(rec_path, rate=PACK_RATE)
        n = min(len(rec), len(total))
        if abs(len(rec) - len(total)) / PACK_RATE > LEN_TOL:
            r.err(f"recording is {len(rec) / PACK_RATE:.3f} s, stems {len(total) / PACK_RATE:.3f} s")
        err = total[:n] - rec[:n]
        e_db = 10 * np.log10((err ** 2).sum() / max((rec[:n].astype(np.float64) ** 2).sum(), 1e-12))
        stats["sum_error_db"] = round(float(e_db), 2)
        # worst 1 s window, relative to that window
        w = PACK_RATE
        k = n // w
        ew = (err[:k * w] ** 2).reshape(k, w, -1).sum((1, 2))
        rw = (rec[:k * w].astype(np.float64) ** 2).reshape(k, w, -1).sum((1, 2))
        loud = rw > rw.max() * 1e-4
        worst = float(10 * np.log10(ew[loud] / rw[loud]).max()) if loud.any() else float("nan")
        stats["sum_error_worst_1s_db"] = round(worst, 2)
        (r.err if e_db > sum_tol_db else r.note)(
            f"stems sum to the recording within {e_db:.1f} dB (tolerance {sum_tol_db} dB; worst loud second {worst:.1f} dB)")
        # alignment: every stem against what the recording leaves for it, at three places, lag in samples
        lags = {}
        for v, is_voice in entries:
            x, _ = decode(pack / v["stem"], rate=PACK_RATE)
            x = x[:n].mean(1) * float(v.get("gain", 1.0))
            target = rec[:n].mean(1) - (total[:n].mean(1) - x)
            best = []
            for c in (0.3, 0.55, 0.8):
                a = int(c * n)
                seg_x = x[a:a + 4 * PACK_RATE]
                seg_t = target[a:a + 4 * PACK_RATE]
                L = 96
                if np.abs(seg_x).max() < 1e-4:
                    continue
                cc = [float(np.dot(seg_x[L:-L], seg_t[L + l:len(seg_t) - L + l])) for l in range(-L, L + 1)]
                best.append(int(np.argmax(cc)) - L)
            lags[v["key"]] = best
            if any(abs(b) > 1 for b in best):
                r.err(f"{v['key']}: stem is offset from the recording by {best} samples")
        stats["align_lags"] = lags
        r.note(f"alignment lags (samples at 3 points) per stem: {lags}")
    else:
        r.note("SKIPPED: stems-sum-to-recording and alignment (no readable recording; pass --recording)")
    # every cue on sound in its own voice
    mix_db = db(frame_rms(total.mean(1), PACK_RATE, 0.01, 0.02))
    pad_key = {v["pad"]: v["key"] for v in tj["voices"]}
    vdb = {k: db(frame_rms(m, PACK_RATE, 0.01, 0.02)) for k, m in monos.items()}
    loud = {k: float(np.percentile(e, 95)) for k, e in vdb.items()}
    stats["silent_cues"] = {}
    for name, cues in tj["charts"].items():
        bad = 0
        for i, c in enumerate(cues):
            k = pad_key.get(c["pad"])
            if k is None:
                continue
            e = vdb[k]
            a = max(0, int((c["t"] - 0.02) / 0.01))
            b = int((c["t"] + 0.08) / 0.01) + 1
            lv = float(e[a:b].max())
            rel = lv - float(mix_db[a:b].max())
            problem = None
            if lv < loud[k] + CUE_OWN_DB:
                problem = f"{lv - loud[k]:.1f} dB under the voice's loud level"
            elif rel < CUE_REL_DB:
                problem = f"{rel:.1f} dB under the whole track"
            elif c["dur"] > 0:
                h = e[int(c["t"] / 0.01):int((c["t"] + c["dur"]) / 0.01)]
                if len(h) and np.median(h) < loud[k] + CUE_OWN_DB - 5:
                    problem = f"hold over near-silence (median {np.median(h) - loud[k]:.1f} dB)"
            if problem:
                bad += 1
                r.err(f"chart {name} cue {i} (t={c['t']:.3f}, pad {c['pad']} {k}): voice silent there: {problem}")
        stats["silent_cues"][name] = bad
    return stats


def densities(tj: dict) -> list[str]:
    bpm = tj["tempo"]["bpm"]
    dur = tj["duration_s"]
    beats = dur * bpm / 60
    lines = []
    keys = {v["pad"]: v["key"] for v in tj["voices"]}
    for name, cues in tj["charts"].items():
        lines.append(f"chart {name}{' (default)' if name == tj.get('default_chart') else ''}: {len(cues)} cues, "
                     f"{len(cues) / dur:.2f}/s, {len(cues) / beats:.3f}/beat")
        for p in (1, 2, 3, 4):
            cs = [c for c in cues if c["pad"] == p]
            holds = sum(1 for c in cs if c["dur"] > 0)
            lines.append(f"  pad {p} {keys.get(p, '?'):<10} {len(cs):4d} cues ({holds} holds) "
                         f"{len(cs) / dur * 60:6.1f}/min {len(cs) / beats:.3f}/beat")
        if len(cues) > 1:
            ts = np.array([c["t"] for c in cues])
            together = int(np.sum(np.diff(ts) < 0.03))
            lines.append(f"  two pads together: {together} times")
    return lines


def validate(pack: str | Path, recording: str | None = None, sum_tol_db: float = -24.0,
             quick: bool = False) -> tuple[Report, dict]:
    pack = Path(pack).resolve()
    r = Report()
    tjp = pack / "track.json"
    if not tjp.is_file():
        r.err(f"{tjp} missing")
        return r, {}
    try:
        tj = json.loads(tjp.read_text())
    except json.JSONDecodeError as e:
        r.err(f"track.json is not JSON: {e}")
        return r, {}
    check_structure(pack, tj, r)
    stats: dict = {}
    if not quick and not r.errors:
        stats = check_audio(pack, tj, r, recording, sum_tol_db)
    elif not quick:
        r.note("audio checks skipped because the structure is broken")
    try:
        for line in densities(tj):
            r.note(line)
    except (KeyError, TypeError, ZeroDivisionError):
        pass
    return r, stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pack")
    ap.add_argument("--recording", help="the original recording (default: source.input_path)")
    ap.add_argument("--sum-tol-db", type=float, default=-24.0,
                    help="max energy of (sum of stems - recording) relative to the recording, dB (default -24)")
    ap.add_argument("--quick", action="store_true", help="no audio decoding")
    a = ap.parse_args(argv)
    r, stats = validate(a.pack, a.recording, a.sum_tol_db, a.quick)
    for n in r.notes:
        print(n)
    for e in r.errors[:200]:
        print("VIOLATION:", e)
    if len(r.errors) > 200:
        print(f"... and {len(r.errors) - 200} more")
    print(f"{'FAIL' if r.errors else 'OK'}: {len(r.errors)} violation(s)")
    return 1 if r.errors else 0


if __name__ == "__main__":
    sys.exit(main())
