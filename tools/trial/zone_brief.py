#!/usr/bin/env python3
"""Prints, per zone of the Bassment, its passages and the choices that leave each (the brief a zone map is drawn from):
    python3 tools/trial/zone_brief.py [zone ...]
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
d = json.load(open(ROOT / "content/trial/passages.json"))
want = sys.argv[1:] or list(d["zones"])
for zid in want:
    z = d["zones"][zid]
    print(f"== {zid}: {z['name']} (tier {z['tier']}) - {z['look']}")
    for n, p in d["passages"].items():
        if p["zone"] != zid:
            continue
        print(f"  [{n}] {p['title']} kind={p.get('kind','normal')} side={p.get('side', False)} secret={p.get('secret', False)}")
        for i, c in enumerate(p["choices"]):
            to = c.get("to")
            tz = d["passages"][str(to)]["zone"] if to is not None else "OUT"
            tag = []
            if c.get("default"): tag.append("DEFAULT")
            if "encounter" in c: tag.append("fight " + c["encounter"])
            if "test" in c: tag.append("luck")
            if "requires" in c: tag.append("needs " + c["requires"])
            print(f"      choice {i}: {c['label']!r} -> {to} ({tz}) {' '.join(tag)}")
