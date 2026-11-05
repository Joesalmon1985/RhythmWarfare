#!/usr/bin/env python3
"""List what a Godot 4 .pck (or an exe with an embedded pck) contains: the packed size by top-level folder and extension.

    python3 tools/pck_list.py build/windows/RhythmWarfare.pck [--files] [--top N]

Reads the Godot 4.x pack directory (format 2 and 3). `--files` prints every packed path with its size. Used by docs/REPO_SIZE.md
to measure what an export filter keeps; it does not run the game.
"""
import collections
import os
import struct
import sys


def read_pck(path):
    with open(path, "rb") as f:
        data_start = 0
        magic = f.read(4)
        if magic != b"GDPC":  # embedded in an exe: the pack ends with GDPC + a trailing 8-byte size
            f.seek(-12, 2)
            tail = f.read(12)
            size = struct.unpack("<Q", tail[:8])[0]
            if tail[8:] != b"GDPC":
                raise SystemExit("not a pck")
            data_start = os.path.getsize(path) - size - 12
            f.seek(data_start)
            f.read(4)
        fmt, vmaj, vmin, vpat = struct.unpack("<4I", f.read(16))
        flags, file_base = struct.unpack("<IQ", f.read(12))
        dir_off = None
        if fmt >= 3:
            dir_off = struct.unpack("<Q", f.read(8))[0]
        f.read(16 * 4)
        if dir_off is not None:
            f.seek(data_start + dir_off)
        count = struct.unpack("<I", f.read(4))[0]
        out = []
        for _ in range(count):
            n = struct.unpack("<I", f.read(4))[0]
            name = f.read(n).rstrip(b"\0").decode("utf8")
            off, size = struct.unpack("<QQ", f.read(16))
            f.read(16)  # md5
            f.read(4)  # flags
            out.append((name, size))
        return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    entries = read_pck(args[0])
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 25
    total = sum(s for _, s in entries)
    print(f"{len(entries)} files, {total / 2**20:.1f} MiB")
    by_dir, by_ext = collections.Counter(), collections.Counter()
    for n, s in entries:
        p = n.replace("res://", "").split("/")
        by_dir["/".join(p[:2]) if len(p) > 2 else p[0]] += s
        by_ext[os.path.splitext(n)[1].lower()] += s
    print("--- by folder")
    for k, v in by_dir.most_common(top):
        print(f"{v / 2**20:9.1f} MiB  {k}")
    print("--- by extension")
    for k, v in by_ext.most_common(15):
        print(f"{v / 2**20:9.1f} MiB  {k or '(none)'}")
    if "--files" in sys.argv:
        for n, s in sorted(entries):
            print(f"{s:10d} {n}")


if __name__ == "__main__":
    main()
