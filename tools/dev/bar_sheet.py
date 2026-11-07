#!/usr/bin/env python3
"""One contact sheet of the bar shots (3 moments across, 16:9 on the top row, 20:9 below), under 1 MB.
    python3 tools/dev/bar_sheet.py <png dir> <out.jpg>
"""
import os
import sys

from PIL import Image, ImageDraw

d, out = sys.argv[1], sys.argv[2]
rows = [("1280x720", "16:9"), ("1600x720", "20:9")]
cols = [("demo", "demonstration"), ("mistake", "a mistake"), ("complete", "completion")]
tw = 640
cells = []
for size, label in rows:
    r = []
    for key, name in cols:
        im = Image.open(os.path.join(d, f"bar_{key}_{size}.png")).convert("RGB")
        im = im.resize((tw, int(im.height * tw / im.width)), Image.NEAREST)
        r.append((name, im))
    cells.append((label, r))
H = sum(max(i.height for _, i in r) + 4 for _, r in cells)
sheet = Image.new("RGB", (tw * 3 + 8, H), (24, 22, 30))
y = 0
for label, r in cells:
    x = 0
    for name, im in r:
        sheet.paste(im, (x, y))
        ImageDraw.Draw(sheet).text((x + 6, y + 22), f"{name} {label}", fill=(255, 255, 255))
        x += tw + 4
    y += max(i.height for _, i in r) + 4
for q in (88, 80, 72, 64, 56, 48):
    sheet.save(out, quality=q, optimize=True)
    if os.path.getsize(out) < 1_000_000:
        break
print(out, os.path.getsize(out), "bytes")
