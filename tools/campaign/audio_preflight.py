"""Preflight for the owner's rendered stems (or the placeholders) of one schema 2 pack.

    python tools/campaign/audio_preflight.py songs/first_watch [--loadout kick_1=kick_march,snare_1=snare_guard]

Checks every render named in level.json (all of them, or only the equipped loadout with --loadout): the file exists
and decodes, its sample rate and frame count match the manifest and each other, it covers duration_ticks plus the
one-bar tail, its peak level leaves headroom (single stem and the sum of the loadout), and its source_sha256 still
matches the current MIDI files (an edited MIDI with an old render fails). It then prints the timestamps to audition:
the start, every change of input focus and the end. Matching lengths cannot prove alignment; listen at those points.
Needs ffmpeg and numpy. Exit code 0 when every check passes."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
LEVEL_DIRS = {"level_01": "level_01", "level_02": "level_02", "level_03": "level_03"}


def decode(path: Path) -> tuple[np.ndarray, int]:
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate", "-of", "default=nw=1:nk=1", str(path)],
                           capture_output=True, text=True, check=True)
    rate = int(probe.stdout.strip())
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<f4"), rate


def midi_hashes(level: dict) -> dict[str, str]:
    level_dir = ROOT / "campaign" / "First_Three" / LEVEL_DIRS[level["level_id"]]
    song = json.loads((level_dir / "song.json").read_text())
    return {p["id"]: hashlib.sha256((level_dir / p["midi"]).read_bytes()).hexdigest() for p in song["parts"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path)
    parser.add_argument("--loadout", default="", help="slot=profile,... (default: check every render in the manifest)")
    args = parser.parse_args()
    pack = args.pack.resolve()
    level = json.loads((pack / "level.json").read_text())
    hashes = midi_hashes(level)
    other_hash = hashlib.sha256("".join(hashes[p["id"]] for p in level["parts"] if p["slot_id"] is None).encode()).hexdigest()
    wanted = dict(item.split("=") for item in args.loadout.split(",") if item)
    bar_ticks = level["ticks_per_beat"] * level["time_signature"][0]
    seconds_per_tick = 60.0 / (level["bpm"] * level["ticks_per_beat"])
    need_seconds = (level["duration_ticks"] + bar_ticks) * seconds_per_tick
    failures: list[str] = []
    frames_seen: dict[str, int] = {}
    mix: np.ndarray | None = None
    for slot, profiles in level["renders"].items():
        for profile, r in profiles.items():
            if wanted and (wanted.get(slot) != profile and slot != "other"):
                continue
            label = f"{slot}/{profile}"
            path = pack / r["file"]
            if not path.is_file():
                failures.append(f"{label}: file missing {r['file']}")
                continue
            try:
                samples, rate = decode(path)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{label}: does not decode ({exc})")
                continue
            peak = float(np.max(np.abs(samples))) if len(samples) else 0.0
            expected_hash = other_hash if slot == "other" else hashes.get(slot)
            problems = []
            if rate != r["sample_rate"]:
                problems.append(f"sample rate {rate} != manifest {r['sample_rate']}")
            if len(samples) / rate + 0.005 < need_seconds:
                problems.append(f"{len(samples) / rate:.3f} s does not cover {need_seconds:.3f} s (song plus one tail bar)")
            if peak < 0.01:
                problems.append("silent file")
            if peak > 0.99:
                problems.append(f"peak {peak:.3f} leaves no headroom (clipping risk)")
            if r["source_sha256"] != expected_hash:
                problems.append("source_sha256 does not match the current MIDI (edited MIDI, stale render)")
            frames_seen[label] = len(samples)
            print(f"{'FAIL' if problems else 'ok  '} {label:28s} {len(samples):8d} frames  {len(samples) / rate:7.3f} s  peak {peak:.3f}  {'placeholder' if r.get('placeholder') else 'rendered'}")
            failures += [f"{label}: {p}" for p in problems]
            if wanted or r.get("profile_default"):
                n = len(samples)
                mix = samples.copy() if mix is None else np.pad(mix, (0, max(0, n - len(mix))))[:max(len(mix), n)] + np.pad(samples, (0, max(0, len(mix) - n)))
    spread = (max(frames_seen.values()) - min(frames_seen.values())) if frames_seen else 0
    first_rate = next(iter(level["renders"].values()))
    first_rate = next(iter(first_rate.values()))["sample_rate"]
    if spread / first_rate > 0.005:
        failures.append(f"frame counts differ by {spread} frames ({spread / first_rate * 1000:.1f} ms): export every stem from the same start")
    if mix is not None:
        print(f"sum of the {'chosen' if wanted else 'default'} loadout: peak {float(np.max(np.abs(mix))):.3f}")
        if float(np.max(np.abs(mix))) > 1.0:
            failures.append("the sum of the loadout's stems peaks above full scale: export with headroom")
    print("\nListen at these song times (stems must line up with the kicks, snares and bass notes):")
    chart = level["charts"][0]
    previous = None
    for s in chart["sections"]:
        if s["mode"] != previous:
            print(f"  {s['start_tick'] * seconds_per_tick:7.2f} s  bar {s['start_tick'] // bar_ticks + 1:3d}  {s['mode']} focus begins")
            previous = s["mode"]
    print(f"  {level['duration_ticks'] * seconds_per_tick:7.2f} s  survival deadline (the stems carry one more bar of tail to {need_seconds:.2f} s)")
    if failures:
        print("\nFAILED:")
        for f in failures:
            print("  " + f)
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
