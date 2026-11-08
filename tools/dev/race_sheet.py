#!/usr/bin/env python3
"""Contact sheet of the street race (tools/engine/shoot_race.gd): docs/shots/bedsit/race/contact.jpg, under 1 MB.
    python3 tools/dev/race_sheet.py <shots dir> [out.jpg]
Rows: the 16:9 shots (1280x720), then the 20:9 shots (1600x720), four to a row."""
import os
import sys
from PIL import Image, ImageDraw

NAMES = [("race_0_hangar", "hangar: the racer"), ("race_1_grid", "grid: start lights"), ("race_2_approach", "approach: countdown, opening lit"), ("race_3_overtake", "overtake"),
         ("race_4_contact", "contact"), ("race_5a_approach_finish", "finish approach"), ("race_5_finish", "finish line"), ("race_6_back_in_the_hangar", "back in the hangar")]
W = 480


def main(argv):
    src = argv[0]
    out = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", "docs", "shots", "bedsit", "race", "contact.jpg")
    rows = []
    for size in ("1280x720", "1600x720"):
        imgs = []
        for n, cap in NAMES:
            p = os.path.join(src, "%s_%s.png" % (n, size))
            if os.path.exists(p):
                im = Image.open(p).convert("RGB")
                im = im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)
                d = ImageDraw.Draw(im)
                d.rectangle([0, 0, W, 14], fill=(0, 0, 0))
                d.text((4, 2), "%s  %s" % (cap, "16:9" if size.startswith("1280") else "20:9"), fill=(255, 255, 255))
                imgs.append(im)
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
    q = 85
    while True:
        sheet.save(out, quality=q)
        if os.path.getsize(out) < 1000000 or q < 40:
            break
        q -= 8
    print("wrote %s (%d bytes, quality %d)" % (out, os.path.getsize(out), q))


if __name__ == "__main__":
    main(sys.argv[1:])
