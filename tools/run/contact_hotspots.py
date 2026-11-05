#!/usr/bin/env python3
"""One contact sheet per world of the hotspot window of each of its scenes: contact_hotspots_<world>.jpg from hotspots_<scene>.jpg in a folder (default docs/shots/run).
   python3 tools/run/contact_hotspots.py [dir]"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
run = json.load(open(ROOT / "content/run/run.json"))
d = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/shots/run"
worlds: dict = {}
for n in run["nodes"]:
    worlds.setdefault(n["world"], []).append(n["id"])
W, H, cols = 480, 270, 3
for w, nodes in worlds.items():
    rows = (len(nodes) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * W, rows * (H + 18)), (14, 10, 22))
    dr = ImageDraw.Draw(sheet)
    for i, n in enumerate(nodes):
        p = d / ("hotspots_%s.jpg" % n.replace(".", "_"))
        x, y = (i % cols) * W, (i // cols) * (H + 18)
        if p.exists():
            sheet.paste(Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS), (x, y))
        dr.text((x + 6, y + H + 3), n, fill=(220, 210, 240))
    out = d / ("contact_hotspots_%s.jpg" % w)
    sheet.save(out, quality=86)
    print(out)
