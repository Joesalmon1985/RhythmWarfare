#!/usr/bin/env python3
"""Stage E build step: re-encode the track packs for the phone and put them where the Android export picks them up.

    python tools/audio_import/build_android_packs.py [--src DIR] [--dest DIR] [--quality 4] [--ids a,b,c | --limit N] [--jobs 4] [--dry-run]

Reads   <src>/<id>/track.json and the stems it names (the voices and the backing; nothing else is read)
Writes  <dest>/<id>/track.json (copied unchanged) and <dest>/<id>/stems/<key>.ogg (48 kHz stereo Ogg Vorbis, -q:a <quality>)
        plus a `<stem>.ogg.import` file saying importer="keep", so the editor does not import the file and the exporter
        ships the original bytes (AudioStreamOggVorbis.load_from_file reads them from the APK).
Leaves out previews, reports, .made_from files and any stem track.json does not name.

Defaults: src = $RW_AUDIO_WORK/packs (else C:/Users/joesa/rw-audio-work/packs), dest = <repo>/track_packs, which Git ignores.
NEVER commit <dest>: it is other artists' music. The loader (RunTrackScenes.packs_root) finds it as res://track_packs.
Needs ffmpeg with libvorbis on PATH. Stems keep their length to the sample (the pack contract allows 5 ms).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IMPORT_KEEP = '[remap]\n\nimporter="keep"\n'


def default_src() -> Path:
    base = os.environ.get("RW_AUDIO_WORK") or "C:/Users/joesa/rw-audio-work"
    return Path(base) / "packs"


def stems_of(track_json: Path) -> list:
    j = json.loads(track_json.read_text(encoding="utf-8"))
    return [v["stem"] for v in j.get("voices", [])] + [b["stem"] for b in j.get("backing", [])]


def encode(src: Path, dst: Path, quality: int) -> int:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + ".part")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-c:a", "libvorbis", "-q:a", str(quality),
           "-ar", "48000", "-ac", "2", "-f", "ogg", str(tmp)]
    subprocess.run(cmd, check=True)
    os.replace(tmp, dst)
    dst.with_name(dst.name + ".import").write_bytes(IMPORT_KEEP.encode("ascii"))
    return dst.stat().st_size


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=default_src())
    ap.add_argument("--dest", type=Path, default=REPO / "track_packs")
    ap.add_argument("--quality", type=int, default=4)
    ap.add_argument("--ids", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    ids = [i for i in a.ids.split(",") if i] or sorted(p.name for p in a.src.iterdir() if (p / "track.json").is_file())
    if a.limit:
        ids = ids[: a.limit]
    jobs = []
    before = 0
    for i in ids:
        tj = a.src / i / "track.json"
        if not tj.is_file():
            print("no track.json for", i, file=sys.stderr)
            return 2
        for s in stems_of(tj):
            f = a.src / i / s
            if not f.is_file():
                print("missing stem", f, file=sys.stderr)
                return 2
            before += f.stat().st_size
            jobs.append((f, a.dest / i / s))
    print("%d packs, %d stems, %.1f MB in" % (len(ids), len(jobs), before / 1e6))
    if a.dry_run:
        return 0
    for i in ids:
        (a.dest / i).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(a.src / i / "track.json", a.dest / i / "track.json")
    with ThreadPoolExecutor(a.jobs) as ex:
        sizes = list(ex.map(lambda sd: encode(sd[0], sd[1], a.quality), jobs))
    print("%.1f MB out at -q:a %d (%.0f%% of the input) in %s" % (sum(sizes) / 1e6, a.quality, 100.0 * sum(sizes) / before, a.dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
