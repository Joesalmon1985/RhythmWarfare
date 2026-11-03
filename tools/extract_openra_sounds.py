#!/usr/bin/env python3
"""Extract Red Alert sound effects and EVA lines as Ogg Vorbis for the game.

Drives ``OpenRA.Utility.exe ra --extract <file>`` from the pinned OpenRA checkout
(the same invocation pattern as ``tools/extract_openra.py``: ``ENGINE_DIR`` and
``MOD_SEARCH_PATHS`` set, cwd = a scratch directory) so it reads the owner's own
Red Alert content (``sounds.mix``, ``speech.mix``, ``allies.mix``).  The Westwood
``.aud`` files are decoded by a pure-Python port of OpenRA's ``AudReader``,
``ImaAdpcmReader`` and ``WestwoodCompressedReader``, written as 16-bit PCM WAV and
encoded to Ogg with ffmpeg.  Writes ``assets/sfx/<name>.ogg``, ``sfx.json`` and
``PROVENANCE.md``.  Nothing is edited by hand.

    python tools/extract_openra_sounds.py [--check] [--engine PATH] [--out assets/sfx]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

DEFAULT_ENGINE = Path(
    r"C:\Users\joesa\Documents\Cursor\DuelMaster\DuelMasterBattle\WizardRTSHybrid\external\openra"
)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = PROJECT_ROOT / "assets" / "sfx"
DEFAULT_WORK = Path(tempfile.gettempdir()) / "openra_sfx_work"
MOD = "ra"

# (file name for --extract, source package, note).  The output name is the lowercase file
# stem, so ackno.v00 -> ackno.ogg.  Weapon reports come from mods/ra/weapons/*.yaml:
# M1Carbine gun11, M60mg pillbox1 (the plan guessed mgun2, which no weapon uses and
# sounds.mix does not hold), Vulcan gun13 (via ^HeavyMG), Grenade grenade1,
# FireballLauncher has no Report, gun5 is the sniper rifle.
SOUNDS: list[tuple[str, str, str]] = [
    ("gun5.aud", "sounds.mix", "weapon: sniper rifle report"),
    ("gun11.aud", "sounds.mix", "weapon: M1Carbine report"),
    ("gun13.aud", "sounds.mix", "weapon: Vulcan (^HeavyMG) report"),
    ("pillbox1.aud", "sounds.mix", "weapon: M60mg report"),
    ("grenade1.aud", "sounds.mix", "weapon: Grenade report"),
    ("mgun2.aud", "sounds.mix", "named in the plan; expected missing"),
    ("kaboom1.aud", "sounds.mix", "explosion"),
    ("kaboom12.aud", "sounds.mix", "explosion"),
    ("kaboom25.aud", "sounds.mix", "explosion"),
    ("kaboom30.aud", "sounds.mix", "explosion"),
    ("crmble2.aud", "sounds.mix", "building crumble"),
    *[(f"dedman{i}.aud", "sounds.mix", "infantry death") for i in range(1, 9)],
    ("girlokay.aud", "sounds.mix", "civilian"),
    ("guyokay1.aud", "sounds.mix", "civilian"),
    ("placbldg.aud", "sounds.mix", "building placed"),
    ("build5.aud", "sounds.mix", "construction"),
    ("bleep11.aud", "sounds.mix", "interface"),
    ("cashturn.aud", "sounds.mix", "interface"),
    ("unitrdy1.aud", "speech.mix", "EVA: unit ready"),
    ("enmyapp1.aud", "speech.mix", "EVA: enemy approaching"),
    ("baseatk1.aud", "speech.mix", "EVA: base under attack"),
    ("unitlst1.aud", "speech.mix", "EVA: unit lost"),
    ("misnwon1.aud", "speech.mix", "EVA: mission accomplished"),
    ("misnlst1.aud", "speech.mix", "EVA: mission failed"),
    ("reinfor1.aud", "speech.mix", "EVA: reinforcements"),
    ("ackno.v00", "allies.mix", "allied voice: acknowledged"),
    ("affirm1.v00", "allies.mix", "allied voice: affirmative"),
]

FMT_WS = 1     # Westwood compressed, 8-bit
FMT_IMA = 99   # IMA ADPCM, 16-bit
FORMAT_NAMES = {FMT_WS: "ws_adpcm", FMT_IMA: "ima_adpcm"}

# --------------------------------------------------------------------------
# AUD decoding (ports of OpenRA.Mods.Cnc AudReader, Common ImaAdpcmReader and
# WestwoodCompressedReader)
# --------------------------------------------------------------------------

IMA_INDEX_ADJUST = (-1, -1, -1, -1, 2, 4, 6, 8)
IMA_STEP_TABLE = (
    7, 8, 9, 10, 11, 12, 13, 14, 16,
    17, 19, 21, 23, 25, 28, 31, 34, 37,
    41, 45, 50, 55, 60, 66, 73, 80, 88,
    97, 107, 118, 130, 143, 157, 173, 190, 209,
    230, 253, 279, 307, 337, 371, 408, 449, 494,
    544, 598, 658, 724, 796, 876, 963, 1060, 1166,
    1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749,
    3024, 3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484,
    7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289,
    16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767,
)
WS_STEP2 = (-2, -1, 0, 1)
WS_STEP4 = (-9, -8, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 8)


def ima_decode_nibble(nibble: int, index: int, current: int) -> tuple[int, int, int]:
    """ImaAdpcmReader.DecodeImaAdpcmSample -> (sample, index, current).

    Note Westwood's variant: delta = step * b / 4 + step / 8 (integer divisions).
    """
    negative = (nibble & 8) != 0
    b = nibble & 7
    step = IMA_STEP_TABLE[index]
    delta = step * b // 4 + step // 8
    if negative:
        delta = -delta
    current = max(-32768, min(32767, current + delta))
    index = max(0, min(88, index + IMA_INDEX_ADJUST[b]))
    return current, index, current


def ws_decode_chunk(data: bytes, out_size: int) -> bytes:
    """WestwoodCompressedReader.DecodeWestwoodCompressedSample (8-bit unsigned output)."""
    if len(data) == out_size:
        return bytes(data)
    out = bytearray()
    sample = 0x80
    r = 0
    n = len(data)

    def clamp(v: int) -> int:
        return 0 if v < 0 else 255 if v > 255 else v

    while r < n:
        head = data[r]
        r += 1
        count = head & 0x3F
        mode = head >> 6
        if mode == 0:
            for _ in range(count + 1):
                code = data[r]
                r += 1
                for shift in (0, 2, 4, 6):
                    sample = clamp(sample + WS_STEP2[(code >> shift) & 3])
                    out.append(sample)
        elif mode == 1:
            for _ in range(count + 1):
                code = data[r]
                r += 1
                for shift in (0, 4):
                    sample = clamp(sample + WS_STEP4[(code >> shift) & 15])
                    out.append(sample)
        elif mode == 2 and (count & 0x20) != 0:
            delta = count & 0x1F
            if delta & 0x10:
                delta -= 0x20          # 5-bit sign extension: (sbyte)(count << 3) >> 3
            sample += delta            # OpenRA does not clamp here; the byte cast wraps
            out.append(sample & 0xFF)
        elif mode == 2:
            for _ in range(count + 1):
                out.append(data[r])
                r += 1
            sample = data[r - 1]
        else:
            out.extend(bytes([sample & 0xFF]) * (count + 1))
    return bytes(out)


class Aud:
    """A decoded AUD file: 16-bit little-endian PCM plus the header facts."""

    def __init__(self, rate: int, channels: int, fmt: int, pcm16: bytes) -> None:
        self.rate = rate
        self.channels = channels
        self.fmt = fmt
        self.pcm16 = pcm16

    @property
    def frames(self) -> int:
        return len(self.pcm16) // (2 * self.channels)

    @property
    def seconds(self) -> float:
        return self.frames / self.rate if self.rate else 0.0

    @property
    def format_name(self) -> str:
        return FORMAT_NAMES[self.fmt]


def decode_aud(blob: bytes) -> Aud:
    if len(blob) < 12:
        raise ValueError("AUD too short")
    rate, data_size, out_size, flags, fmt = struct.unpack_from("<HiiBB", blob, 0)
    channels = 2 if flags & 1 else 1
    sixteen = bool(flags & 2)
    if fmt not in FORMAT_NAMES:
        raise ValueError(f"unsupported AUD format {fmt}")
    if fmt == FMT_IMA and not sixteen:
        raise ValueError("IMA ADPCM AUD must be 16-bit")
    pos = 12
    end = len(blob)
    remaining = data_size
    pcm = bytearray()
    index = 0
    current = 0
    base_offset = 0
    while remaining > 0 and pos + 8 <= end:
        comp, outsz, magic = struct.unpack_from("<HHI", blob, pos)
        if magic != 0xDEAF:
            raise ValueError("AUD chunk header is bogus")
        pos += 8
        data = blob[pos:pos + comp]
        pos += comp
        if fmt == FMT_IMA:
            for b in data:
                s, index, current = ima_decode_nibble(b & 0x0F, index, current)
                pcm += struct.pack("<h", s)
                base_offset += 2
                if base_offset < out_size:  # possibly only half of the final byte is used
                    s, index, current = ima_decode_nibble(b >> 4, index, current)
                    pcm += struct.pack("<h", s)
                    base_offset += 2
        else:
            raw = ws_decode_chunk(data, outsz)
            if sixteen:
                pcm += raw
            else:
                pcm += b"".join(struct.pack("<h", (v - 128) << 8) for v in raw)
        remaining -= 8 + comp
    return Aud(rate, channels, fmt, bytes(pcm))


# --------------------------------------------------------------------------
# WAV and Ogg
# --------------------------------------------------------------------------

def wav_bytes(pcm16: bytes, rate: int, channels: int = 1) -> bytes:
    """A canonical 44-byte-header 16-bit PCM WAV."""
    block = channels * 2
    header = b"RIFF" + struct.pack("<I", 36 + len(pcm16)) + b"WAVE"
    header += b"fmt " + struct.pack("<IHHIIHH", 16, 1, channels, rate, rate * block, block, 16)
    header += b"data" + struct.pack("<I", len(pcm16))
    return header + pcm16


def encode_ogg(wav: Path, ogg: Path) -> None:
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-c:a", "libvorbis", "-q:a", "4", str(ogg)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not ogg.exists():
        raise RuntimeError(f"ffmpeg failed for {wav.name}: {r.stderr.strip()}")


def ogg_ok(ogg: Path) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name",
                        "-of", "csv=p=0", str(ogg)], capture_output=True, text=True)
    return r.returncode == 0 and "vorbis" in r.stdout


# --------------------------------------------------------------------------
# OpenRA.Utility driver
# --------------------------------------------------------------------------

class Utility:
    def __init__(self, engine: Path, work: Path) -> None:
        self.engine = engine
        self.work = work
        self.exe = engine / "bin" / "OpenRA.Utility.exe"
        if not self.exe.exists():
            raise SystemExit(f"utility not found: {self.exe}")
        work.mkdir(parents=True, exist_ok=True)
        self.env = dict(os.environ)
        self.env["ENGINE_DIR"] = str(engine)
        self.env["MOD_SEARCH_PATHS"] = str(engine / "mods")

    def extract(self, filename: str, force: bool = False) -> tuple[Path | None, str | None]:
        dst = self.work / filename
        if dst.exists() and not force:
            return dst, None
        cmd = [str(self.exe), MOD, "--extract", filename]
        r = subprocess.run(cmd, cwd=self.work, env=self.env, capture_output=True, text=True)
        if r.returncode != 0 or not dst.exists():
            lines = (r.stdout + r.stderr).strip().splitlines()
            return None, (lines[0] if lines else "extract failed")
        return dst, None


def sound_name(filename: str) -> str:
    return filename.lower().rsplit(".", 1)[0]


PROVENANCE = """# Sound effects provenance

These Ogg Vorbis files were extracted by `tools/extract_openra_sounds.py` from the owner's own Red Alert content as installed for OpenRA (`%APPDATA%\\OpenRA\\Content\\ra\\v2`: `sounds.mix`, `speech.mix`, `allies.mix`); Red Alert has been freeware since 2008 and the OpenRA engine used to read the packages is GPL. Each `.aud` file is pulled out of its package with `OpenRA.Utility.exe ra --extract <file>` (pinned checkout `{engine}`), decoded to 16-bit PCM by the script's pure-Python port of OpenRA's `AudReader` (Westwood compressed and IMA ADPCM), and encoded with ffmpeg (`-c:a libvorbis -q:a 4`) at the native sample rate. Nothing was edited by hand; `sfx.json` lists the source package, AUD format, sample rate and duration of each sound.

Weapon reports come from `mods/ra/weapons/*.yaml`: M1Carbine `gun11`, M60mg `pillbox1`, Vulcan `gun13` (inherited from `^HeavyMG`), Grenade `grenade1`; the sniper rifle is `gun5`; FireballLauncher defines no report.

Commands:

```
python tools/extract_openra_sounds.py --check
python tools/extract_openra_sounds.py
python -m unittest discover -s tools -p "test_extract_openra_sounds.py"
```
"""


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="list the sounds and whether each resolves; write nothing")
    ap.add_argument("--engine", type=Path, default=DEFAULT_ENGINE, help="pinned OpenRA checkout")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory (assets/sfx)")
    ap.add_argument("--work", type=Path, default=DEFAULT_WORK, help="scratch directory the utility writes into")
    args = ap.parse_args(argv)

    work = args.work
    cleanup = False
    if args.check:
        work = Path(tempfile.mkdtemp(prefix="openra_sfx_check_"))
        cleanup = True
    util = Utility(args.engine, work)
    try:
        manifest: dict[str, dict] = {}
        missing: list[tuple[str, str]] = []
        if not args.check:
            args.out.mkdir(parents=True, exist_ok=True)
        for filename, source, note in SOUNDS:
            name = sound_name(filename)
            path, err = util.extract(filename)
            if path is None:
                print(f"MISSING  {filename:14s} [{source}] {err}")
                missing.append((filename, err or ""))
                continue
            aud = decode_aud(path.read_bytes())
            if args.check:
                print(f"ok       {filename:14s} [{source}] {aud.format_name:9s} {aud.rate} Hz "
                      f"{aud.seconds:.2f} s  {note}")
                continue
            wav = work / f"{name}.wav"
            wav.write_bytes(wav_bytes(aud.pcm16, aud.rate, aud.channels))
            ogg = args.out / f"{name}.ogg"
            encode_ogg(wav, ogg)
            if not ogg_ok(ogg):
                raise SystemExit(f"{ogg} is not a valid Ogg Vorbis file")
            manifest[name] = {"file": f"{name}.ogg", "source": source, "format": aud.format_name,
                              "rate": aud.rate, "seconds": round(aud.seconds, 2)}
            print(f"wrote    {ogg.name:14s} [{source}] {aud.format_name:9s} {aud.rate} Hz {aud.seconds:.2f} s")
        if not args.check:
            (args.out / "sfx.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
            (args.out / "PROVENANCE.md").write_text(PROVENANCE.format(engine=args.engine), encoding="utf-8")
            print(f"{len(manifest)} sounds in {args.out}; {len(missing)} unresolved")
        elif missing:
            print(f"{len(missing)} names do not resolve")
    finally:
        if cleanup:
            shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
