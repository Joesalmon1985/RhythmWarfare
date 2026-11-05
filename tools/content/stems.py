#!/usr/bin/env python3
"""The stored form of a song pack's stems: one copy per distinct sound, mono where the two channels are the same (docs/REPO_SIZE.md, Part 2).

    python3 tools/content/stems.py [--packs songs/packs] [--dry-run]     convert the packs on disk (idempotent)

Two lossless changes to how songs/packs/<pack>/loops/*.wav are stored, neither of which changes a sample of what is played:

* MONO. A stem whose left and right channels are equal in every frame (the drums, the bass and most pads of the placeholders and of the owner's
  packs are dual-mono) is stored as a 16-bit MONO WAV. Godot plays a mono stream as the same signal on both sides, so the mix is the same;
  the PCM of the one channel is exactly the PCM of both. Half the bytes in the tree, half in the export (QOA is per sample).
* SHARED. Packs with the same stem (a scene reused at another variant, the placeholders that repeat a bass or a pad) share one file:
  songs/packs/_shared/<stem>_<sha1 of the file, 12 hex>.wav, and the pack's manifest names it by a path relative to the pack:
  `"stems": {"drums": "../_shared/drums_0123456789ab.wav", ...}`. Every reader already resolves `stems[k]` against the pack's folder (RunData, RunAudio,
  the tools), `..` included; `_shared` has no pack.json, so nothing lists it as a pack. A pack's `loops` section (frames, gains, levels) is untouched.

Generators call `finish_pack(pack_dir)` after writing a pack (tools/content/make_path_placeholders.py does), then `prune_shared(packs_root)` once. Importers that write
`loops/*.wav` (beatshaper.py, import_squadron.py) are not changed: their packs stay in the plain layout (and keep working) until `python3 tools/content/stems.py` converts them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
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


def finish_pack(pack_dir: Path, shared_dir: Path | None = None, *, mono: bool = True, share: bool = True) -> dict:
    """Convert one pack in place: dual-mono stems become mono, every stem moves to the shared folder (or is dropped there if the same file is
    already there) and pack.json names it. Returns {stem: relative path}. Run on a pack whose stems are plain `loops/<stem>.wav` files, or on an
    already converted one (nothing changes)."""
    shared_dir = shared_dir or pack_dir.parent / SHARED
    pj = pack_dir / "pack.json"
    pack = json.loads(pj.read_text(encoding="utf-8"))
    stems = pack["stems"]
    out: dict = {}
    for key, rel in stems.items():
        rel_s = rel["file"] if isinstance(rel, dict) else rel
        src = (pack_dir / rel_s).resolve()
        pcm, rate, _ch = read_pcm(src)
        if mono and is_dual_mono(pcm):
            pcm = pcm[:, :1]
        data = wav_bytes(pcm, rate)
        if share:
            name = f"{key}_{hashlib.sha1(data).hexdigest()[:12]}.wav"
            dest = shared_dir / name
            shared_dir.mkdir(parents=True, exist_ok=True)
            if not dest.exists() or dest.read_bytes() != data:
                dest.write_bytes(data)
            new_rel = f"../{SHARED}/{name}"
        else:
            dest, new_rel = src, rel_s
            if src.read_bytes() != data:
                src.write_bytes(data)
        if dest.resolve() != src:
            src.unlink()
            imp = Path(str(src) + ".import")
            if imp.exists():
                imp.unlink()
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
    args = ap.parse_args()
    root = Path(args.packs)
    before = after = 0
    plan = []
    for pj in sorted(root.glob("*/pack.json")):
        for k, f in stem_files(pj.parent).items():
            before += f.stat().st_size
    if args.dry_run:
        seen = {}
        for pj in sorted(root.glob("*/pack.json")):
            for k, f in stem_files(pj.parent).items():
                pcm, rate, _ = read_pcm(f)
                if is_dual_mono(pcm):
                    pcm = pcm[:, :1]
                d = wav_bytes(pcm, rate)
                seen[hashlib.sha1(d).hexdigest()] = len(d)
        print(f"{before / 2**20:.1f} MiB now -> {sum(seen.values()) / 2**20:.1f} MiB ({len(seen)} distinct stems)")
        return 0
    n = 0
    for pj in sorted(root.glob("*/pack.json")):
        finish_pack(pj.parent)
        n += 1
    gone = prune_shared(root)
    for f in (root / SHARED).glob("*.wav"):
        after += f.stat().st_size
    print(f"{n} packs: {before / 2**20:.1f} MiB -> {after / 2**20:.1f} MiB in {len(list((root / SHARED).glob('*.wav')))} shared stems ({len(gone)} unreferenced removed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
