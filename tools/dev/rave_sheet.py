#!/usr/bin/env python3
"""Contact sheet of a new rave's map shots (tools/dev/shoot_rave.sh): three views across, two rows per size, 16:9 then 20:9, under 1 MB (JPEG).
    python3 tools/dev/rave_sheet.py <png dir> <out.jpg>"""
import os
import sys

from PIL import Image, ImageDraw

d, out = sys.argv[1], sys.argv[2]
names = ["hub", "approach", "deck_before", "deck_after", "cloak", "bar"]
tw = 560
rows = []
for size, label in (("1280x720", "16:9"), ("1600x720", "20:9")):
    cells = []
    for f in names:
        p = os.path.join(d, f"{f}_{size}.png")
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            cells.append((f"{f} {label}", im.resize((tw, int(im.height * tw / im.width)), Image.NEAREST)))
    for i in range(0, len(cells), 3):
        rows.append(cells[i:i + 3])
H = sum(max(i.height for _, i in r) + 4 for r in rows)
sheet = Image.new("RGB", (tw * 3 + 8, H), (24, 22, 30))
y = 0
for r in rows:
    x = 0
    for label, im in r:
        sheet.paste(im, (x, y))
        ImageDraw.Draw(sheet).text((x + 6, y + 4), label, fill=(255, 255, 255))
        x += tw + 4
    y += max(i.height for _, i in r) + 4
os.makedirs(os.path.dirname(out), exist_ok=True)
for q in (88, 80, 72, 64, 56, 48):
    sheet.save(out, quality=q, optimize=True)
    if os.path.getsize(out) < 1_000_000:
        break
print(out, os.path.getsize(out), "bytes")
