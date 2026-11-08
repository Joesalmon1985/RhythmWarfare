#!/usr/bin/env python3
"""Contact sheet of the bedsit shots: 16:9 on the top row, 20:9 below, four facings across, under 1 MB (JPEG, the quality steps down until it fits).
    python3 tools/dev/bedsit_sheet.py <png dir> <out.jpg>
"""
import os
import sys

from PIL import Image, ImageDraw

d, out = sys.argv[1], sys.argv[2]
rows = [("1280x720", "16:9"), ("1600x720", "20:9")]
tw = 480
cells = []
for size, label in rows:
    r = []
    for f in ("hub", "approach", "deck_before", "deck_after"):
        p = os.path.join(d, f"{f}_{size}.png")
        im = Image.open(p).convert("RGB")
        im = im.resize((tw, int(im.height * tw / im.width)), Image.NEAREST)
        r.append((f, im))
    cells.append((label, r))
H = sum(max(i.height for _, i in r) + 4 for _, r in cells)
sheet = Image.new("RGB", (tw * 4 + 12, H), (24, 22, 30))
y = 0
for label, r in cells:
    x = 0
    for f, im in r:
        sheet.paste(im, (x, y))
        dr = ImageDraw.Draw(sheet)
        dr.text((x + 6, y + 4), f"{f} {label}", fill=(255, 255, 255))
        x += tw + 4
    y += max(i.height for _, i in r) + 4
for q in (88, 80, 72, 64, 56, 48):
    sheet.save(out, quality=q, optimize=True)
    if os.path.getsize(out) < 1_000_000:
        break
print(out, os.path.getsize(out), "bytes")
