#!/usr/bin/env python3
"""Writes the zone layouts into content/trial/passages.json:  python3 tools/trial/apply_layout.py [zone ...]

A layout is content/trial/layout/<zone>.json:
  {"map": "bassment_<zone>", "passages": {"<id>": {"waypoint": "<waypoint of the map where the camera stands>", "exits": ["<waypoint or doorway id for choice 0>", ...]}}}
`exits` has one entry per choice of the passage, in order: the waypoint of the map the camera walks to when that choice is taken (a door, a ladder foot, a gap, the water's edge,
a seam). Each passage of the zone gains `map` and `waypoint`, each choice `exit_wp` (the key `exit` is taken: on a way out of the dungeon it says where to, "warehouse"). Idempotent.
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "content/trial/passages.json"
d = json.load(open(P))
zones = sys.argv[1:] or sorted(p.stem for p in (ROOT / "content/trial/layout").glob("*.json"))
for z in zones:
    lay = json.load(open(ROOT / f"content/trial/layout/{z}.json"))
    for n, p in d["passages"].items():
        if p["zone"] != z:
            continue
        e = lay["passages"].get(n)
        if e is None:
            raise SystemExit(f"layout {z}: passage {n} missing")
        if len(e["exits"]) != len(p["choices"]):
            raise SystemExit(f"layout {z}: passage {n} has {len(p['choices'])} choices but {len(e['exits'])} exits")
        p["map"] = lay["map"]
        p["waypoint"] = e["waypoint"]
        for c, x in zip(p["choices"], e["exits"]):
            c["exit_wp"] = x
    d["zones"][z]["map"] = lay["map"]
open(P, "w").write(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
print("applied", ", ".join(zones))
