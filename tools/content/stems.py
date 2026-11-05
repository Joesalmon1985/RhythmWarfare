#!/usr/bin/env python3
"""The stored form of a song pack's stems: one copy per distinct sound, played mono where the two channels are the same (docs/REPO_SIZE.md, Part 2).

    python3 tools/content/stems.py [--packs songs/packs] [--dry-run] [--mono-files]     convert the packs on disk (idempotent)

Two lossless changes to how songs/packs/<pack>/loops/*.wav are stored, neither of which changes a sample of what is played:

* SHARED. Packs with the same stem (a scene reused at another variant, the placeholders that repeat a bass or a pad) share one file:
  songs/packs/_shared/<stem>_<sha1 of the file, 12 hex>.wav, and the pack's manifest names it by a path relative to the pack:
  `"stems": {"drums": "../_shared/drums_0123456789ab.wav", ...}`. Every reader already resolves `stems[k]` against the pack's folder (RunData, RunAudio,
  the tools), `..` included; `_shared` has no pack.json, so nothing lists it as a pack. A pack's `loops` section (frames, gains, levels) is untouched.
  The file moves byte for byte, so git stores no new blob.
* MONO IN THE BUILD. A stem whose left and right channels are equal in every frame (the drums and the bass of every pack, most pads: they are dual-mono) gets
  `force/mono=true` in its Godot import file: the exported sample is one channel (half the bytes; Godot plays a mono stream as the same signal on both sides, and the mono QOA
  decode is bit-identical to each channel of the stereo one, checked). The WAV in the tree stays stereo. `--mono-files` also rewrites such a WAV as a 16-bit mono file (the tree
  is smaller by the same half, but every rewritten stem is a new blob in git: about +114 MiB in `.git` until history is rewritten, which is why it is not the default).

Generators call `finish_pack(pack_dir)` after writing a pack (tools/content/make_path_placeholders.py does), then `prune_shared(packs_root)` once. Importers that write
`loops/*.wav` (beatshaper.py, import_squadron.py) are not changed: their packs stay in the plain layout (and keep working) until `python3 tools/content/stems.py` converts them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

SHARED = "_shared"


def read_pcm(path: Path) -> tuple[np.ndarray, int, int]:
    """(frames x channels int16, sample rate, channels) of a 16-bit PCM WAV."""
    with wave.open(str(path), "rb") as w:
        assert w.getsampwidth() == 2, f"{path}: 16-bit PCM only"
        a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, w.getnchannels())
        return a, w.getframerate(), w.getnchannels()


def wav_bytes(pcm: np.ndarray, rate: int) -> bytes:
    """A canonical 16-bit PCM WAV of frames x channels int16 (the same bytes for the same samples, whatever wrote them)."""
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(pcm.shape[1])
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(np.ascontiguousarray(pcm, dtype="<i2").tobytes())
    return buf.getvalue()


def is_dual_mono(pcm: np.ndarray) -> bool:
    return pcm.shape[1] == 2 and bool(np.array_equal(pcm[:, 0], pcm[:, 1]))


def _dump(pack: dict) -> str:
    return json.dumps(pack, indent=1) + "\n"


IMPORT_DEFAULTS = """[remap]

importer="wav"
type="AudioStreamWAV"

[deps]

source_file="res://%s"

[params]

force/8_bit=false
force/mono=true
force/max_rate=false
force/max_rate_hz=44100
edit/trim=false
edit/normalize=false
edit/loop_mode=0
edit/loop_begin=0
edit/loop_end=-1
compress/mode=2
"""


def set_import_mono(wav: Path, root: Path) -> None:
    """Make Godot import this WAV as one channel (`force/mono=true`): edit its .import file, or write the minimal one (Godot fills in the uid and the cache path on the next import)."""
    imp = Path(str(wav) + ".import")
    if imp.exists():
        t = imp.read_text(encoding="utf-8")
        t2 = re.sub(r"^force/mono=\w+", "force/mono=true", t, flags=re.M)
        if t2 != t:
            imp.write_text(t2, encoding="utf-8", newline="\n")
    else:
        rel = wav.resolve().relative_to(root.resolve()).as_posix()
        imp.write_text(IMPORT_DEFAULTS % rel, encoding="utf-8", newline="\n")


def finish_pack(pack_dir: Path, shared_dir: Path | None = None, *, mono_files: bool = False, project_root: Path | None = None) -> dict:
    """Convert one pack in place: every stem moves, byte for byte, to the shared folder (or is dropped there if the same file is already there) and pack.json names it; a
    dual-mono stem is imported as mono (`force/mono=true`, see the module doc), and with `mono_files` stored as a mono WAV. Returns {stem: relative path}. Run on a pack whose
    stems are plain `loops/<stem>.wav` files, or on an already converted one (nothing changes)."""
    shared_dir = shared_dir or pack_dir.parent / SHARED
    project_root = project_root or Path(__file__).resolve().parents[2]
    pj = pack_dir / "pack.json"
    pack = json.loads(pj.read_text(encoding="utf-8"))
    stems = pack["stems"]
    out: dict = {}
    for key, rel in stems.items():
        rel_s = rel["file"] if isinstance(rel, dict) else rel
        src = (pack_dir / rel_s).resolve()
        pcm, rate, _ch = read_pcm(src)
        dual = is_dual_mono(pcm)
        data = wav_bytes(pcm[:, :1], rate) if (mono_files and dual) else src.read_bytes()
        name = f"{key}_{hashlib.sha1(data).hexdigest()[:12]}.wav"
        dest = shared_dir / name
        shared_dir.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or dest.read_bytes() != data:
            dest.write_bytes(data)
        new_rel = f"../{SHARED}/{name}"
        if dest.resolve() != src:
            src.unlink()
            Path(str(src) + ".import").unlink(missing_ok=True)
        if dual and not (mono_files and pcm.shape[1] == 2):
            try:
                set_import_mono(dest, project_root)
            except ValueError:  # a pack outside the project (a test's scratch folder): no Godot import to steer
                pass
        out[key] = new_rel
        if isinstance(rel, dict):
            stems[key] = {**rel, "file": new_rel}
        else:
            stems[key] = new_rel
    loops = pack_dir / "loops"
    if loops.is_dir() and not any(loops.iterdir()):
        loops.rmdir()
    text = _dump(pack)
    if not pj.exists() or pj.read_text(encoding="utf-8") != text:
        pj.write_text(text, encoding="utf-8", newline="\n")
    return out


def referenced(packs_root: Path) -> set[str]:
    names: set[str] = set()
    for pj in packs_root.glob("*/pack.json"):
        for v in json.loads(pj.read_text(encoding="utf-8")).get("stems", {}).values():
            v = v["file"] if isinstance(v, dict) else v
            if v.startswith(f"../{SHARED}/"):
                names.add(v.split("/")[-1])
    return names


def prune_shared(packs_root: Path) -> list[str]:
    """Delete shared stems (and their Godot .import files) that no pack names any more. Returns the names removed."""
    sh = packs_root / SHARED
    if not sh.is_dir():
        return []
    keep = referenced(packs_root)
    gone = []
    for f in sorted(sh.glob("*.wav")):
        if f.name not in keep:
            f.unlink()
            Path(str(f) + ".import").unlink(missing_ok=True)
            gone.append(f.name)
    if not any(sh.iterdir()):
        sh.rmdir()
    return gone


def stem_files(pack_dir: Path) -> dict:
    """{stem: absolute path} of a pack, whatever layout it has."""
    pack = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
    out = {}
    for k, v in pack["stems"].items():
        v = v["file"] if isinstance(v, dict) else v
        out[k] = (pack_dir / v).resolve()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--packs", default=str(Path(__file__).resolve().parents[2] / "songs" / "packs"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--mono-files", action="store_true", help="also store dual-mono stems as mono WAV files (smaller tree, new blobs in git)")
    args = ap.parse_args()
    root = Path(args.packs)
    before = 0
    for pj in sorted(root.glob("*/pack.json")):
        for f in stem_files(pj.parent).values():
            before += f.stat().st_size
    if args.dry_run:
        seen = {}
        for pj in sorted(root.glob("*/pack.json")):
            for f in stem_files(pj.parent).values():
                pcm, rate, _ = read_pcm(f)
                d = wav_bytes(pcm[:, :1], rate) if (args.mono_files and is_dual_mono(pcm)) else f.read_bytes()
                seen[hashlib.sha1(d).hexdigest()] = len(d)
        print(f"{before / 2**20:.1f} MiB now -> {sum(seen.values()) / 2**20:.1f} MiB ({len(seen)} distinct stems)")
        return 0
    n = 0
    for pj in sorted(root.glob("*/pack.json")):
        finish_pack(pj.parent, mono_files=args.mono_files)
        n += 1
    gone = prune_shared(root)
    shared = list((root / SHARED).glob("*.wav"))
    print(f"{n} packs: {before / 2**20:.1f} MiB -> {sum(f.stat().st_size for f in shared) / 2**20:.1f} MiB in {len(shared)} shared stems ({len(gone)} unreferenced removed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
