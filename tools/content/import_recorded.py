"""Import one recorded Beat Shaper / Ableton export set (a Drums, a Bass and a Synth WAV with their MIDI) as the music of a
story chapter. The originals are only read; everything written is derived and goes to the chapter's pack folder.

    python tools/content/import_recorded.py content/imports/story_warehouse.json            # write the pack
    python tools/content/import_recorded.py content/imports/story_warehouse.json --check    # verify timing, write nothing

What it does, in order (all numbers land in <pack>/timing_report.json):

1. Reads each WAV (16/24/32-bit PCM or 32-bit float, any channel count, 48 kHz) and each MIDI.
2. Timing. The MIDI headers say 120 BPM but the recordings were rendered at `source_bpm` (87). The importer does not take
   that on trust: it measures the drum transients against the MIDI hit times (best-fit tempo and offset, per-hit error),
   and the bass re-attacks against the bass MIDI note starts, and refuses to continue when the measured tempo is not the
   declared one or a hit lies further out than `max_error_ms`. The MIDI beat positions are then mapped onto the 174 BPM
   game grid with `game_beats_per_source_beat` (2: 87 x 2 = 174), so a source beat is two game beats and a 16-beat
   loop is exactly 8 game bars. The audio is never time-stretched: it plays at its recorded speed and only the MIDI
   ticks are rescaled.
3. Loops. Every stem becomes one WAV of exactly the loop's length (8 bars = 529655 frames at 48 kHz). A recording that is
   longer than the loop (an Ableton render keeps the release tails, and the three stems end at different times) has
   the part beyond the loop folded onto the loop's start, so a tail rings into the next lap instead of being cut or
   drifting. Stems are gain-staged by `gain_db` (the originals' balance is kept apart from that).
4. Cues. Kick (`kick_notes`) -> pad 1 taps, snare (`snare_notes`) -> pad 4 taps, bass -> its distinct pitches spread over
   the pads by pitch (as the loop library does) as holds, each hold shortened to end inside its two-bar sequence.
   Every cue list is checked with the library's chart rules (tools/content/chart.py).
5. Writes <pack>/level.json (the base mission pack named by `base_pack`, with a "recorded_music" block: stems, families,
   the phase each stem sounds in, the cues), <pack>/loops/*.wav and <pack>/timing_report.json.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (BPM, PPQ, ROOT, SAMPLE_RATE, TICKS_PER_BAR, ContentError, bars_to_frames, read_json, read_midi, rel,  # noqa: E402
                    sha256_file, write_json, write_wav)
from chart import check_cues, load_rules, pitch_pads  # noqa: E402

LOOP_BARS = 8
SEQUENCE_TICKS = 2 * TICKS_PER_BAR


def read_float_wav(path: Path) -> tuple[np.ndarray, int]:
    """Frames x channels float32 and the sample rate, from a RIFF WAV of PCM 16/24/32 or IEEE float 32."""
    b = path.read_bytes()
    if b[:4] != b"RIFF" or b[8:12] != b"WAVE":
        raise ContentError(f"{rel(path)}: not a RIFF WAV file")
    i, fmt = 12, None
    while i + 8 <= len(b):
        cid, n = b[i:i + 4], struct.unpack("<I", b[i + 4:i + 8])[0]
        if cid == b"fmt ":
            fmt = struct.unpack("<HHIIHH", b[i + 8:i + 24])
        elif cid == b"data":
            if fmt is None:
                raise ContentError(f"{rel(path)}: data chunk before fmt chunk")
            tag, ch, rate, _, _, bits = fmt
            raw = b[i + 8:i + 8 + n]
            if tag == 3 and bits == 32:
                a = np.frombuffer(raw[:len(raw) // 4 * 4], "<f4").astype(np.float32)
            elif tag in (1, 0xFFFE) and bits == 16:
                a = np.frombuffer(raw[:len(raw) // 2 * 2], "<i2").astype(np.float32) / 32768.0
            elif tag in (1, 0xFFFE) and bits == 24:
                x = np.frombuffer(raw[:len(raw) // 3 * 3], np.uint8).reshape(-1, 3).astype(np.int32)
                v = x[:, 0] | (x[:, 1] << 8) | (x[:, 2] << 16)
                a = (np.where(v >= 1 << 23, v - (1 << 24), v) / 8388608.0).astype(np.float32)
            elif tag in (1, 0xFFFE) and bits == 32:
                a = (np.frombuffer(raw[:len(raw) // 4 * 4], "<i4") / 2147483648.0).astype(np.float32)
            else:
                raise ContentError(f"{rel(path)}: unsupported WAV format tag {tag}, {bits} bit")
            return a.reshape(-1, ch), rate
        i += 8 + n + (n & 1)
    raise ContentError(f"{rel(path)}: no data chunk")


def db(x: float) -> float:
    return -math.inf if x <= 0 else 20.0 * math.log10(x)


def envelope(x: np.ndarray, rate: int, hop_ms: float = 1.0) -> tuple[np.ndarray, float]:
    hop = max(1, int(rate * hop_ms / 1000.0))
    n = len(x) // hop
    return np.sqrt((x[:n * hop].reshape(n, hop).astype(np.float64) ** 2).mean(1)), hop / rate


def onset_near(env: np.ndarray, step: float, t: float, win_s: float) -> float | None:
    """The sharpest rise of the envelope within +-win_s of t (the time its log-envelope climbs fastest), in seconds."""
    a = max(int((t - win_s) / step), 1)
    b = min(int((t + win_s) / step), len(env) - 2)
    if b <= a:
        return None
    seg = np.log(env[a - 1:b + 1] + 1e-4)
    d = seg[3:] - seg[:-3]  # rise over 3 hops
    if len(d) == 0 or d.max() < 0.35:
        return None
    return (a + int(np.argmax(d))) * step


def verify_timing(m: dict, mono: dict, midi: dict, errors: list, warnings: list) -> dict:
    """Measure the recordings against the MIDI at the declared tempo. Returns the report block."""
    rate = SAMPLE_RATE
    src_bpm = float(m["source_bpm"])
    spb = 60.0 / src_bpm
    tol = float(m.get("max_error_ms", 12.0)) / 1000.0
    report: dict = {"declared_source_bpm": src_bpm, "midi_header_bpm": {k: v["tempo_bpm"] for k, v in midi.items()},
                    "game_bpm": BPM, "game_beats_per_source_beat": m["game_beats_per_source_beat"]}
    # --- drums: every distinct hit time (hats included) against the sharpest envelope rise near it
    env, step = envelope(mono["drums"], rate)
    hits = sorted({n["tick"] / PPQ for n in midi["drums"]["notes"]})  # source beats (960 ticks per source beat)
    pairs = []
    for b in hits:
        t = b * spb
        o = onset_near(env, step, t, 0.04)
        if o is not None:
            pairs.append((b, t, o))
    if len(pairs) < 0.8 * len(hits):
        errors.append(f"drums: only {len(pairs)} of {len(hits)} MIDI hits have a transient within 40 ms at {src_bpm} BPM")
    bs = np.array([p[0] for p in pairs])
    ts = np.array([p[2] for p in pairs])
    slope, intercept = np.polyfit(bs, ts, 1)
    fit_bpm = 60.0 / slope
    err = ts - bs * spb
    report["drums"] = {"hits": len(hits), "matched": len(pairs), "fitted_bpm": round(float(fit_bpm), 3), "fitted_offset_ms": round(float(intercept * 1000), 2),
                       "error_ms_at_declared": {"mean": round(float(err.mean() * 1000), 2), "median": round(float(np.median(err) * 1000), 2),
                                                "max_abs": round(float(np.abs(err).max() * 1000), 2), "p95_abs": round(float(np.percentile(np.abs(err), 95) * 1000), 2)}}
    if abs(fit_bpm - src_bpm) > 0.1:
        errors.append(f"drums: the transients fit {fit_bpm:.3f} BPM, not the declared {src_bpm}")
    if float(np.abs(err).max()) > tol:
        errors.append(f"drums: a hit lies {np.abs(err).max() * 1000:.1f} ms from the MIDI at {src_bpm} BPM (limit {tol * 1000:.0f} ms)")
    # the alternative the headers suggest: 120 BPM puts every transient far off (shown for the record)
    hdr = float(next(iter(report["midi_header_bpm"].values())))
    alt = [onset_near(env, step, b * 60.0 / hdr, 0.04) for b in hits]
    report["drums"]["hits_matched_if_header_tempo"] = int(sum(1 for a, b in zip(alt, hits) if a is not None and abs(a - b * 60.0 / hdr) < tol))
    # --- bass: the recording is a wobbling reese, so its amplitude envelope says little. A note change shows as a jump in
    # the low spectrum: compare the 40 ms before and after each candidate time near the MIDI note start, take the biggest.
    x = mono["bass"]
    win = int(0.04 * rate)
    hann = np.hanning(win)
    freqs = np.fft.rfftfreq(8 * win, 1 / rate)
    band = (freqs > 40) & (freqs < 400)

    def spec(end_s: float) -> np.ndarray:
        i = int(round(end_s * rate)) - win
        s = np.abs(np.fft.rfft(x[i:i + win] * hann, 8 * win))[band]
        return s / (np.linalg.norm(s) + 1e-9)

    rows = []
    first = np.nonzero(np.abs(x) > 1e-3)[0]
    for n in sorted(midi["bass"]["notes"], key=lambda n: n["tick"]):
        t = n["tick"] / PPQ * spb
        if n["tick"] == 0:
            rows.append({"beat": 0.0, "pitch": n["pitch"], "midi_s": 0.0, "audio_s": round(float(first[0]) / rate, 4) if len(first) else None,
                         "error_ms": round(float(first[0]) / rate * 1000, 1) if len(first) else None, "how": "first sound in the file"})
            continue
        cand = np.arange(max(t - 0.08, 0.05), t + 0.08, 0.002)
        d = [1.0 - float(np.dot(spec(c), spec(c + 0.04))) for c in cand]
        j = int(np.argmax(d))
        rows.append({"beat": n["tick"] / PPQ, "pitch": n["pitch"], "midi_s": round(t, 4), "audio_s": round(float(cand[j]), 4),
                     "error_ms": round((float(cand[j]) - t) * 1000, 1), "how": "largest spectral change within 80 ms"})
    report["bass"] = {"notes": rows}
    errs = [abs(r["error_ms"]) for r in rows if r["error_ms"] is not None]
    if len(errs) < len(rows) or max(errs) > max(tol * 1000, 12.0):
        errors.append("bass: a note change lies further from its MIDI start than the limit: " + json.dumps(rows))
    return report


def fold_loop(frames: np.ndarray, loop_frames: int) -> tuple[np.ndarray, dict]:
    """Exactly loop_frames long: shorter is padded with silence, longer has the part beyond the loop added onto the start
    (as many laps as it takes). Returns the loop and a description of what was done."""
    n = len(frames)
    info = {"frames_in": int(n), "loop_frames": int(loop_frames), "tail_frames": max(0, int(n - loop_frames)), "padded_frames": max(0, int(loop_frames - n))}
    out = np.zeros((loop_frames, frames.shape[1]), dtype=np.float64)
    pos = 0
    while pos < n:
        seg = frames[pos:pos + loop_frames]
        out[:len(seg)] += seg
        pos += loop_frames
    nz = np.nonzero(np.abs(frames[loop_frames:]).max(axis=1) > 0.001)[0] if n > loop_frames else []
    info["tail_audible_s"] = round(float((nz[-1] + 1) / SAMPLE_RATE), 3) if len(nz) else 0.0
    info["laps_folded"] = max(0, int(math.ceil(n / loop_frames)) - 1)
    return out.astype(np.float32), info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--check", action="store_true", help="verify the timing and print the report; write nothing")
    args = ap.parse_args()
    mpath = Path(args.manifest)
    m = read_json(mpath)
    src = Path(m["source_dir"])
    src = src if src.is_absolute() else ROOT / src
    errors: list[str] = []
    warnings: list[str] = []
    loop_frames = bars_to_frames(LOOP_BARS)
    scale = int(m["game_beats_per_source_beat"])
    prefix = m["prefix"]
    stems = m["stems"]  # name -> {"wav": suffix, "midi": suffix | None, "gain_db": x, ...}
    audio: dict[str, np.ndarray] = {}
    mono: dict[str, np.ndarray] = {}
    midi: dict[str, dict] = {}
    src_hash: dict[str, str] = {}
    try:
        for name, spec in stems.items():
            wav = src / f"{prefix}{spec['file']}.wav"
            if not wav.exists():
                raise ContentError(f"{rel(wav)} is missing")
            frames, rate = read_float_wav(wav)
            if rate != SAMPLE_RATE:
                raise ContentError(f"{rel(wav)}: {rate} Hz; this importer takes {SAMPLE_RATE} Hz (no resampling, so no speed change)")
            if frames.shape[1] == 1:
                frames = np.repeat(frames, 2, axis=1)
            audio[name] = frames
            mono[name] = frames.mean(axis=1)
            src_hash[wav.name] = sha256_file(wav)
            mid = src / f"{prefix}{spec['file']}.mid"
            if mid.exists():
                midi[name] = read_midi(mid, default_bpm=120.0)
                src_hash[mid.name] = sha256_file(mid)
        timing = verify_timing(m, mono, midi, errors, warnings)
        if errors:
            for e in errors:
                print("ERROR " + e)
            print(json.dumps(timing, indent=1))
            return 1
        # --- cues from the MIDI, source beats -> game ticks
        rules = load_rules()
        span = scale * PPQ  # game ticks per source beat
        total = int(max(n["tick"] + n["duration_ticks"] for n in midi["drums"]["notes"]) / PPQ * span)
        if abs(total - LOOP_BARS * TICKS_PER_BAR) > span // 8:
            raise ContentError(f"the drum MIDI covers {total} game ticks, a {LOOP_BARS}-bar loop is {LOOP_BARS * TICKS_PER_BAR}")
        kick_notes, snare_notes = set(m["kick_notes"]), set(m["snare_notes"])
        cues: dict[str, list] = {"kick": [], "snare": [], "bass": []}
        for n in midi["drums"]["notes"]:
            tick = n["tick"] * scale
            if n["pitch"] in kick_notes:
                cues["kick"].append([tick, 0, 1])
            elif n["pitch"] in snare_notes:
                cues["snare"].append([tick, 0, 4])
        pads = pitch_pads(n["pitch"] for n in midi["bass"]["notes"])
        for n in sorted(midi["bass"]["notes"], key=lambda n: n["tick"]):
            tick, dur = n["tick"] * scale, n["duration_ticks"] * scale
            seq_end = (tick // SEQUENCE_TICKS + 1) * SEQUENCE_TICKS
            hold = min(dur, seq_end - tick)  # a hold ends inside its two-bar sequence; the sound rings on
            cues["bass"].append([tick, hold if hold >= rules["chart"]["hold_min_ticks"] else 0, pads[n["pitch"]]])
        for k in cues:
            cues[k].sort()
        drum_cues = sorted(cues["kick"] + cues["snare"], key=lambda c: (c[0], c[2]))
        problems = check_cues(drum_cues, rules) + check_cues(cues["bass"], rules)
        if problems:
            raise ContentError("the cues break the chart rules:\n  " + "\n  ".join(problems))
        # --- loops
        loops: dict[str, dict] = {}
        out_dir = ROOT / m["pack_dir"]
        for name, spec in stems.items():
            gain = float(spec.get("gain_db", 0.0))
            folded, info = fold_loop(audio[name].astype(np.float64) * 10.0 ** (gain / 20.0), loop_frames)
            peak = float(np.abs(folded).max())
            if peak >= 0.999:
                raise ContentError(f"{name}: {gain:+.1f} dB clips (peak {db(peak):.1f} dBFS)")
            info.update({"gain_db": gain, "peak_db": round(db(peak), 2), "rms_db": round(db(float(np.sqrt((folded.astype(np.float64) ** 2).mean()))), 2),
                         "source_seconds": round(len(audio[name]) / SAMPLE_RATE, 4), "source_peak_db": round(db(float(np.abs(audio[name]).max())), 2),
                         "file": f"loops/{name}.wav"})
            seam = float(np.abs(folded[-1] - folded[0]).max())
            info["seam_step"] = round(seam, 5)
            loops[name] = {"info": info, "frames": folded}
        report = {"source_dir": rel(src), "sources_sha256": src_hash, "timing": timing, "loops": {k: v["info"] for k, v in loops.items()},
                  "loop": {"bars": LOOP_BARS, "frames": loop_frames, "seconds": round(loop_frames / SAMPLE_RATE, 6),
                           "source_beats": LOOP_BARS * 4 / scale, "note": "16 source beats at 87 BPM = 32 game beats at 174 BPM = 8 bars; audio is not stretched"},
                  "cues": {k: len(v) for k, v in cues.items()}, "warnings": warnings}
        print(json.dumps(report, indent=1))
        if args.check:
            return 0
        base = read_json(ROOT / m["base_pack"] / "level.json")
        base["recorded_music"] = {
            "source": m["source_label"], "loop_bars": LOOP_BARS,
            "stems": {name: {"file": f"loops/{name}.wav", "mode": spec["mode"], "families": spec.get("families", [])} for name, spec in stems.items()},
            "cues": cues,
        }
        for key in ("title", "level_id"):
            if key in m:
                base[key] = m[key]
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, v in loops.items():
            write_wav(out_dir / v["info"]["file"], v["frames"])
        write_json(out_dir / "level.json", base, indent=1, depth=1)
        write_json(out_dir / "timing_report.json", report, indent=1)
        print("written " + rel(out_dir))
    except ContentError as exc:
        print(f"ERROR {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
