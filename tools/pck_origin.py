#!/usr/bin/env python3
"""Attribute a .pck's imported payload (.godot/imported/*) to the source folders it came from.

    python3 tools/pck_origin.py build/RhythmWarfare.pck [--depth 2]

Reads every `*.import` under the project (run from the repo root) to map `path="res://.godot/imported/<x>"` back to the source file,
then sums the packed sizes per source folder. Companion of tools/pck_list.py; used by docs/REPO_SIZE.md.
"""
import collections
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pck_list import read_pck  # noqa: E402

PATH_RE = re.compile(r'^(?:path(?:\.[a-z0-9_]+)?|dest_files)=.*$')
RES_RE = re.compile(r'res://\.godot/imported/[^"\]]+')


def main():
    pck = sys.argv[1]
    depth = int(sys.argv[sys.argv.index("--depth") + 1]) if "--depth" in sys.argv else 2
    sizes = {(n if n.startswith("res://") else "res://" + n): s for n, s in read_pck(pck)}
    root = os.getcwd()
    owner = {}
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in (".git", ".godot", "build")]
        for f in fn:
            if f.endswith(".import"):
                rel = os.path.relpath(os.path.join(dp, f[:-7]), root).replace(os.sep, "/")
                for line in open(os.path.join(dp, f), encoding="utf8", errors="ignore"):
                    if PATH_RE.match(line):
                        for m in RES_RE.findall(line):
                            owner[m] = rel
    by = collections.Counter()
    for n, s in sizes.items():
        if n in owner:
            src = owner[n]
        else:
            src = n.replace("res://", "")
        p = src.split("/")
        by["/".join(p[:depth])] += s
    total = sum(by.values())
    print(f"{total / 2**20:.1f} MiB in {len(sizes)} files")
    for k, v in by.most_common(40):
        print(f"{v / 2**20:9.1f} MiB  {k}")


if __name__ == "__main__":
    main()
