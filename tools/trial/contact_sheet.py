#!/usr/bin/env python3
"""Builds contact_bassment.jpg from zone_<zone>.png in a folder:  python3 tools/trial/contact_sheet.py [dir]
`--list` prints "<zone> <first passage>" per zone (what capture.sh shoots)."""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
data = json.load(open(ROOT / "content/trial/passages.json"))
zones = list(data["zones"])

if sys.argv[1:] == ["--list"]:
    first = {}
    for n, p in data["passages"].items():
        if int(n) != 0:
            first.setdefault(p["zone"], int(n))
    for z in zones:
        print(z, first[z])
    raise SystemExit(0)

d = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/shots/trial"
W, H, cols = 480, 270, 4
rows = (len(zones) + cols - 1) // cols
sheet = Image.new("RGB", (cols * W, rows * (H + 18)), (14, 10, 22))
dr = ImageDraw.Draw(sheet)
for i, z in enumerate(zones):
    p = d / f"zone_{z}.png"
    x, y = (i % cols) * W, (i // cols) * (H + 18)
    if p.exists():
        sheet.paste(Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS), (x, y))
    dr.text((x + 6, y + H + 3), z, fill=(220, 210, 240))
sheet.save(d / "contact_bassment.jpg", quality=86)
print(d / "contact_bassment.jpg")
