#!/usr/bin/env python3
"""Contact sheet of a rave's activities (tools/engine/shoot_space_activities.gd): docs/shots/bedsit/<theme>/activities.jpg, under 1 MB.
    python3 tools/dev/space_activities_sheet.py <shots dir> [out.jpg] [theme]
Rows: the 16:9 shots (1280x720) in two rows of four, then the 20:9 shots (1600x720)."""
import os
import sys
from PIL import Image, ImageDraw

NAMES = [("cloak_1_demonstration", "cloakroom: demonstration"), ("cloak_2_midway", "cloakroom: mid-way"), ("cloak_3_payoff", "cloakroom: payoff"), ("deck_1_stuck", "deck: knob stuck"),
         ("bar_1_demonstration", "bar: demonstration"), ("bar_2_mistake", "bar: mistake"), ("bar_3_payoff", "bar: payoff"), ("deck_2_free", "deck: knob free")]
W = 480


def main(argv):
    src = argv[0]
    theme = argv[2] if len(argv) > 2 else "space"
    out = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", "docs", "shots", "bedsit", theme, "activities.jpg")
    blocks = []
    for size in ("1280x720", "1600x720"):
        imgs = []
        for n, cap in NAMES:
            p = os.path.join(src, "%s_%s.png" % (n, size))
            if os.path.exists(p):
                im = Image.open(p).convert("RGB")
                im = im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)
                ImageDraw.Draw(im).text((6, 4), "%s  %s" % (cap, "16:9" if size.startswith("1280") else "20:9"), fill=(255, 255, 255))
                imgs.append(im)
        blocks.append(imgs)
    rows = []
    for imgs in blocks:
        for i in range(0, len(imgs), 4):
            rows.append(imgs[i:i + 4])
    h = sum(max(im.height for im in r) + 4 for r in rows)
    sheet = Image.new("RGB", (4 * (W + 4), h), (12, 10, 20))
    y = 0
    for r in rows:
        x = 0
        for im in r:
            sheet.paste(im, (x, y))
            x += W + 4
        y += max(im.height for im in r) + 4
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    q = 82
    while True:
        sheet.save(out, quality=q)
        if os.path.getsize(out) < 1000000 or q < 40:
            break
        q -= 8
    print("wrote %s (%d bytes, quality %d)" % (out, os.path.getsize(out), q))


if __name__ == "__main__":
    main(sys.argv[1:])
