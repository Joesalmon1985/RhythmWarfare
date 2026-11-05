"""Import a batch of Ableton exports (MIDI patterns and the WAVs recorded from them) into the loop library.

    python tools/content/import_ableton.py content/imports/first_watch.json          # write the clips
    python tools/content/import_ableton.py content/imports/first_watch.json --check  # report only, write nothing

A manifest names a folder of exports (never modified: the originals stay as they are) and the clips to make from them.
For every clip it writes content/library/<id>/clip.json, one <part>.mid per cued part (the first `bars` of the exported
MIDI, rescaled to 960 PPQ with the 174 BPM tempo written in, note lengths and velocities kept) and one
<part>__<sound>.wav per recording (resampled to 48 kHz stereo 16-bit with the SoX resampler, never time-stretched, cut
to the clip's bars plus whatever tail still sounds within one bar, gain-staged, and faded over the last few
milliseconds when the recording is cut mid-note so the loop never clicks). The clip declares the sounds it was
recorded with ("sounds"), so the build pairs each pattern only with its own recordings. Sounds the manifest introduces
are added to content/sounds.json. Then run `python tools/content/build.py`.

Manifest:
{
 "source_dir": "ToAddTry1",                 relative to the project (or absolute); a relative folder that is not inside the project is looked for
                                            in the project's parent folders (the owner's ToAddTry folders sit beside the checkout)
 "bars": 8,                                 clip length (a clip may say its own "bars"); the MIDI's first bars are used, the WAV must cover them
 "tail_bars": 1,                            at most this much of a render's release is kept after the clip's last bar (a clip or render may say 0:
                                            a render longer than its clip is then cut at the last bar with a short fade, nothing past it is a "tail")
 "levels": {"kick": {"peak_db": -4}, "bass": {"peak_db": -4, "rms_db": -17}, ...},
                                            gain per family: the largest gain that keeps the peak under peak_db and
                                            (when given) brings the RMS to rms_db, so one family's sounds match
 "trim_db": -3,                             added to every render after the family rule (headroom for the full mix)
 "end_fade_ms": 10,                         fade applied to a render whose end is not already silent
 "sounds": [{"id": "bass_sub_deep", "family": "bass", "name": "Deep Sub"}, ...],
 "clips": [
  {"id": "bass_sub_line", "kind": "bass", "name": "Sub Line", "key": "F minor", "note": "...",
   "parts": {"bass": {"midi": "Bass1.mid", "renders": {"bass_sub_deep": "bass1a.wav", "bass_sub_pure": {"file": "bass1b.wav", "gain_db": -9}}}}},
  {"id": "acc_hats_busy", "kind": "accompaniment", "name": "Busy Hats", "key": "F minor", "audio_only": true,
   "parts": {"other": {"renders": {"hats_busy": "Other2.wav"}}}}
 ]
}
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (BPM, CONTENT, LIBRARY, PPQ, ROOT, SAMPLE_RATE, TAIL_BARS, TICKS_PER_BAR, ContentError,  # noqa: E402
                    bars_to_frames, read_json, read_midi, rel, sha256_file, write_json, write_midi, write_wav)
from library import ID_RE, KINDS  # noqa: E402

SILENCE = 0.001  # -60 dBFS: below this a tail is over
FAMILIES = ("kick", "snare", "bass", "other")


def db(x: float) -> float:
    return -math.inf if x <= 0 else 20.0 * math.log10(x)


def read_any_wav(path: Path) -> tuple[np.ndarray, int]:
    """Decode a WAV of any rate, width or channel count through ffmpeg to float32 frames x 2 at its own rate."""
    import wave
    with wave.open(str(path), "rb") as wf:
        rate = wf.getframerate()
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "x.f32"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-ac", "2", "-f", "f32le", "-acodec", "pcm_f32le",
                        str(raw)], check=True)
        data = np.frombuffer(raw.read_bytes(), dtype="<f4").reshape(-1, 2).copy()
    return data, rate


def resample(frames: np.ndarray, rate: int) -> np.ndarray:
    """44.1 kHz (or any rate) -> 48 kHz with ffmpeg's SoX resampler at its highest precision. Timing and pitch are
    preserved exactly (the ratio is 160/147 for 44.1 kHz); the same input gives the same output on every run."""
    if rate == SAMPLE_RATE:
        return frames
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "in.f32"
        dst = Path(tmp) / "out.f32"
        src.write_bytes(frames.astype("<f4").tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(rate), "-ac", "2", "-i", str(src),
                        "-af", f"aresample=resampler=soxr:precision=33:osr={SAMPLE_RATE}:dither_method=none",
                        "-f", "f32le", "-acodec", "pcm_f32le", str(dst)], check=True)
        return np.frombuffer(dst.read_bytes(), dtype="<f4").reshape(-1, 2).copy()


def trim_to_clip(frames: np.ndarray, bars: int, tail_bars: int = TAIL_BARS) -> tuple[np.ndarray, dict]:
    """The clip's bars plus the part of the tail that still sounds (at most `tail_bars`, one by default). Nothing inside the bars changes."""
    musical = bars_to_frames(bars)
    longest = bars_to_frames(bars + tail_bars)
    info = {"frames_in": int(len(frames)), "musical_frames": int(musical)}
    if len(frames) < musical - 2:
        raise ContentError(f"{len(frames)} frames at 48 kHz is shorter than {bars} bars ({musical}); the recording must cover the clip")
    if len(frames) < musical:
        frames = np.vstack([frames, np.zeros((musical - len(frames), 2), dtype=np.float32)])
    tail = frames[musical:]
    loud = np.nonzero(np.abs(tail).max(axis=1) > SILENCE)[0]
    keep = int(loud[-1]) + 1 if len(loud) else 0
    if keep < SAMPLE_RATE // 1000:  # under a millisecond of tail is resampling spill, not a release
        keep = 0
    if keep > longest - musical:
        info["tail_cut_while_sounding"] = tail_bars > 0  # tail_bars 0: the render is cut at the clip's end on purpose, not a tail
        keep = longest - musical
    out = frames[:musical + keep].copy()
    info["tail_frames"] = int(keep)
    info["dropped_frames"] = int(len(frames) - len(out))
    return out, info


def end_fade(frames: np.ndarray, ms: float) -> bool:
    """Fade the last `ms` in place when the file does not already end in silence. Returns whether it did."""
    n = min(int(SAMPLE_RATE * ms / 1000.0), len(frames))
    if n <= 0 or float(np.abs(frames[-n:]).max()) < SILENCE * 0.1:
        return False
    ramp = 0.5 * (1.0 + np.cos(np.linspace(0.0, math.pi, n, dtype=np.float32)))
    frames[-n:] *= ramp[:, None]
    return True


def family_gain(frames: np.ndarray, rule: dict) -> float:
    """The largest gain (dB) that keeps the peak under peak_db and, when rms_db is given, brings the RMS to it."""
    peak = float(np.abs(frames).max())
    rms = float(np.sqrt(np.mean(frames.astype(np.float64) ** 2)))
    gains = []
    if "peak_db" in rule and peak > 0:
        gains.append(float(rule["peak_db"]) - db(peak))
    if "rms_db" in rule and rms > 0:
        gains.append(float(rule["rms_db"]) - db(rms))
    return min(gains) if gains else 0.0


def resolve_source(name: str) -> Path:
    """An absolute folder as it is; a relative one in the project, else in the nearest parent folder that has it."""
    p = Path(name)
    if p.is_absolute():
        return p
    for base in (ROOT, *ROOT.parents):
        if (base / p).is_dir():
            return base / p
    return ROOT / p


class Importer:
    def __init__(self, manifest: Path, check: bool = False, library: Path = LIBRARY, sounds_path: Path = CONTENT / "sounds.json"):
        self.manifest_path = manifest
        self.m = read_json(manifest)
        self.check = check
        self.library = library
        self.sounds_path = sounds_path
        self.source = resolve_source(self.m["source_dir"])
        self.bars = int(self.m.get("bars", 8))
        self.levels = self.m.get("levels", {})
        self.trim_db = float(self.m.get("trim_db", 0.0))
        self.fade_ms = float(self.m.get("end_fade_ms", 10.0))
        self.tail_bars = int(self.m.get("tail_bars", TAIL_BARS))
        self.rows: list[dict] = []
        self.warnings: list[str] = []
        self.sounds = {s["id"]: s for s in read_json(sounds_path)["sounds"]} if sounds_path.exists() else {}

    def run(self) -> None:
        if not self.source.is_dir():
            raise ContentError(f"source_dir {rel(self.source)} is not a folder")
        for s in self.m.get("sounds", []):
            if not ID_RE.match(s["id"]) or s.get("family") not in FAMILIES:
                raise ContentError(f"sound {s}: needs an id (lower case, digits, _) and a family in {FAMILIES}")
            cur = self.sounds.get(s["id"])
            if cur is not None and cur["family"] != s["family"]:
                raise ContentError(f"sound {s['id']} already exists as a {cur['family']} sound")
            self.sounds[s["id"]] = {**(cur or {}), "id": s["id"], "family": s["family"], "name": s.get("name", s["id"])}
        clips = self.m.get("clips", [])
        if not clips:
            raise ContentError("the manifest lists no clips")
        for c in clips:
            self._clip(c)
        if not self.check:
            write_json(self.sounds_path, {**read_json(self.sounds_path), "sounds": list(self.sounds.values())} if self.sounds_path.exists()
                       else {"sounds": list(self.sounds.values())})

    def _clip(self, c: dict) -> None:
        cid = c["id"]
        kind = c.get("kind", "")
        if not ID_RE.match(cid):
            raise ContentError(f"clip id '{cid}' must be lower case letters, digits and _")
        if kind not in KINDS:
            raise ContentError(f"clip {cid}: kind must be one of {sorted(KINDS)}")
        audio_only = bool(c.get("audio_only", False))
        parts = c.get("parts", {})
        if set(parts) != set(KINDS[kind]):
            raise ContentError(f"clip {cid}: a {kind} clip has the parts {list(KINDS[kind])}, the manifest gives {sorted(parts)}")
        folder = self.library / cid
        bars = int(c.get("bars", self.bars))
        tail_bars = int(c.get("tail_bars", self.tail_bars))
        clip_json = {"id": cid, "kind": kind, "name": c.get("name", cid), "bars": bars, "tempo_bpm": BPM}
        if c.get("key"):
            clip_json["key"] = c["key"]
        if c.get("note"):
            clip_json["note"] = c["note"]
        if audio_only:
            clip_json["audio_only"] = True
        if c.get("atonal"):
            clip_json["atonal"] = True
        clip_json["sounds"] = {}
        source_dir = self.m["source_dir"] if not Path(self.m["source_dir"]).is_absolute() else rel(self.source)
        source = {"type": "imported", "manifest": rel(self.manifest_path), "source_dir": source_dir, "parts": {}, "renders": {}}
        for part, spec in parts.items():
            if not audio_only:
                if "midi" not in spec:
                    raise ContentError(f"clip {cid}: part {part} needs a midi file (or the clip is audio_only)")
                source["parts"][part] = self._midi(cid, part, folder, spec["midi"], bars)
            renders = spec.get("renders", {})
            if not renders:
                raise ContentError(f"clip {cid}: part {part} lists no renders")
            for sid, r in renders.items():
                snd = self.sounds.get(sid)
                if snd is None or snd["family"] != part:
                    raise ContentError(f"clip {cid}: render sound '{sid}' is not a {part} sound (add it to the manifest's sounds)")
                r = {"file": r} if isinstance(r, str) else dict(r)
                source["renders"][f"{part}__{sid}"] = self._render(cid, part, sid, folder, r, spec, bars, int(r.get("tail_bars", spec.get("tail_bars", tail_bars))))
                clip_json["sounds"].setdefault(part, []).append(sid)
        clip_json["source"] = source
        if not self.check:
            write_json(folder / "clip.json", clip_json)

    def _midi(self, cid: str, part: str, folder: Path, name: str, bars: int) -> dict:
        src = self.source / name
        if not src.exists():
            raise ContentError(f"clip {cid}: {rel(src)} is missing")
        info = read_midi(src)
        if info["tempo_bpm"] and abs(info["tempo_bpm"] - BPM) > 0.01:
            raise ContentError(f"{rel(src)}: tempo {info['tempo_bpm']:.2f} BPM; the library is {BPM} BPM")
        end = bars * TICKS_PER_BAR
        notes = []
        for n in info["notes"]:
            if n["tick"] >= end:
                continue
            m = dict(n)
            m["duration_ticks"] = min(m["duration_ticks"], end - m["tick"])
            notes.append(m)
        if not notes:
            raise ContentError(f"{rel(src)}: no notes in its first {bars} bars")
        total_bars = max(n["tick"] + n["duration_ticks"] for n in info["notes"]) / TICKS_PER_BAR
        row = {"clip": cid, "part": part, "file": name, "kind": "midi", "notes": len(notes), "of": len(info["notes"]),
               "bars_in": round(total_bars, 2), "ppq": info["ppq"], "tempo": info["tempo_source"]}
        self.rows.append(row)
        if not self.check:
            write_midi(folder / f"{part}.mid", notes, f"{cid} {part}")
        return {"midi": name, "sha256": sha256_file(src), "bars": [1, bars], "notes_kept": len(notes), "notes_in_file": len(info["notes"]),
                "ppq": info["ppq"], "tempo_source": info["tempo_source"]}

    def _render(self, cid: str, part: str, sid: str, folder: Path, r: dict, spec: dict, bars: int, tail_bars: int) -> dict:
        src = self.source / r["file"]
        if not src.exists():
            raise ContentError(f"clip {cid}: {rel(src)} is missing")
        frames, rate = read_any_wav(src)
        peak_in = float(np.abs(frames).max())
        frames = resample(frames, rate)
        frames, trim = trim_to_clip(frames, bars, tail_bars)
        rule = self.levels.get(part, {})
        gain = float(r["gain_db"]) if "gain_db" in r else (float(spec["gain_db"]) if "gain_db" in spec else family_gain(frames, rule))
        gain += self.trim_db
        frames *= 10.0 ** (gain / 20.0)
        faded = end_fade(frames, self.fade_ms)
        peak = float(np.abs(frames).max())
        rms = float(np.sqrt(np.mean(frames.astype(np.float64) ** 2)))
        if peak >= 1.0:
            raise ContentError(f"{rel(src)}: {gain:+.1f} dB would clip (peak {db(peak):.1f} dBFS); lower its gain")
        if peak < SILENCE:
            raise ContentError(f"{rel(src)}: silent")
        if trim.get("tail_cut_while_sounding"):
            self.warnings.append(f"{rel(src)}: still sounding one bar after the clip's end; the tail was cut there")
        out = folder / f"{part}__{sid}.wav"
        row = {"clip": cid, "part": part, "file": r["file"], "kind": "wav", "rate_in": rate, "bars_in": round(trim["frames_in"] / bars_to_frames(1), 3),
               "tail_frames": trim["tail_frames"], "dropped_frames": trim["dropped_frames"], "peak_in_db": round(db(peak_in), 2),
               "gain_db": round(gain, 2), "peak_db": round(db(peak), 2), "rms_db": round(db(rms), 2), "faded": faded, "out": rel(out)}
        self.rows.append(row)
        if not self.check:
            write_wav(out, frames)
        out_info = {"file": r["file"], "sha256": sha256_file(src), "sample_rate_in": rate, "gain_db": round(gain, 3),
                    "tail_frames": trim["tail_frames"], "end_fade_ms": self.fade_ms if faded else 0}
        if trim["dropped_frames"] > 0:  # nothing is discarded silently: what was left of the recording is recorded here
            out_info["frames_in"] = trim["frames_in"]
            out_info["dropped_frames"] = trim["dropped_frames"]
            out_info["bars_in"] = round(trim["frames_in"] / bars_to_frames(1), 3)
        if r.get("note") or spec.get("note"):
            out_info["note"] = r.get("note", spec.get("note"))
        return out_info

    def report(self) -> str:
        lines = [f"{'clip':22s} {'part':6s} {'source':14s} {'kind':4s} {'in':>10s} {'gain':>7s} {'peak':>7s} {'rms':>7s} {'tail':>6s} fade"]
        for r in self.rows:
            if r["kind"] == "midi":
                lines.append(f"{r['clip']:22s} {r['part']:6s} {r['file']:14s} midi {r['bars_in']:>6.2f} bars  kept {r['notes']} of {r['of']} notes, "
                             f"{r['ppq']} PPQ, tempo {r['tempo']}")
            else:
                lines.append(f"{r['clip']:22s} {r['part']:6s} {r['file']:14s} wav  {r['bars_in']:>6.3f} bars {r['gain_db']:>+7.2f} {r['peak_db']:>7.2f} "
                             f"{r['rms_db']:>7.2f} {r['tail_frames']:>6d} {'yes' if r['faded'] else 'no'}   ({r['rate_in']} Hz, peak in {r['peak_in_db']:.2f} dBFS)")
        return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--check", action="store_true", help="report what would be written; write nothing")
    args = ap.parse_args()
    imp = Importer(Path(args.manifest), args.check)
    try:
        imp.run()
    except ContentError as exc:
        print(f"ERROR {exc}")
        return 1
    print(imp.report())
    for w in imp.warnings:
        print("WARNING " + w)
    print(f"{'checked' if args.check else 'written'}: {len([r for r in imp.rows if r['kind'] == 'wav'])} renders, "
          f"{len([r for r in imp.rows if r['kind'] == 'midi'])} MIDI parts, {len(imp.m.get('clips', []))} clips")
    return 0


if __name__ == "__main__":
    sys.exit(main())
