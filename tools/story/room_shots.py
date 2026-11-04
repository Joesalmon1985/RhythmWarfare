#!/usr/bin/env python3
"""One screenshot spec per room of every chapter map (docs/STORY_25D_ART_DIRECTION.md acceptance: a contact sheet per chapter where every room reads differently).

  python3 tools/story/room_shots.py list            # chapter|room|camera|bar, one per line (camera is RW_STORY_CAM syntax)
  python3 tools/story/room_shots.py sheets IN OUT   # build OUT/contact_<chapter>.jpg from IN/room_<chapter>_<room>.png

The camera stands at the room's own first waypoint when it has one, else at one end of its largest sector looking down its long axis. The bar is late enough in the
chapter that the room's crowd has arrived (perfect play).
"""
import json, sys, os, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHAPTERS = ["night_one", "mothership", "underworld", "hospital", "mental_hospital"]
BAR = {"night_one": 100, "mothership": 60, "underworld": 50, "hospital": 40, "mental_hospital": 50}


def area(poly):
    a = 0.0
    for i in range(len(poly)):
        x0, z0 = poly[i]
        x1, z1 = poly[(i + 1) % len(poly)]
        a += x0 * z1 - x1 * z0
    return abs(a) / 2


def specs():
    out = []
    for c in CHAPTERS:
        m = json.load(open(ROOT / ("content/story/maps/%s.json" % c)))
        rooms = {}
        for s in m["sectors"]:
            rooms.setdefault(s["room"], []).append(s)
        sec_room = {s["id"]: s["room"] for s in m["sectors"]}
        seen_sec = set()
        rooms_with_wp = set()
        for w in m["waypoints"]:  # one shot per place the camera is sent to (the first waypoint of each sector)
            if w["sector"] in seen_sec:
                continue
            seen_sec.add(w["sector"])
            rooms_with_wp.add(sec_room[w["sector"]])
            out.append((c, w["id"], w["id"], BAR[c]))
        for room, secs in rooms.items():  # rooms nobody is sent to: one shot from the end of the largest sector, looking along it
            if room in rooms_with_wp:
                continue
            big = max(secs, key=lambda s: area(s["polygon"]))
            xs = [p[0] for p in big["polygon"]]
            zs = [p[1] for p in big["polygon"]]
            cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
            if max(xs) - min(xs) >= max(zs) - min(zs):
                cam = "@%.1f:%.1f:-90" % (min(xs) + 0.8, cz)
            else:
                cam = "@%.1f:%.1f:0" % (cx, max(zs) - 0.8)
            out.append((c, room, cam, BAR[c]))
    return out


def sheets(indir, outdir):
    from PIL import Image, ImageDraw
    for c in CHAPTERS:
        files = [(r, Path(indir) / ("room_%s_%s.png" % (c, r))) for (cc, r, _, _) in specs() if cc == c]
        files = [(r, f) for r, f in files if f.exists()]
        if not files:
            continue
        cols = 3
        tw, th = 640, 230  # the world strip is about 2.8:1
        rows = math.ceil(len(files) / cols)
        sheet = Image.new("RGB", (cols * tw, rows * (th + 22)), (12, 12, 20))
        d = ImageDraw.Draw(sheet)
        for i, (r, f) in enumerate(files):
            im = Image.open(f).convert("RGB")
            w, h = im.size
            im = im.crop((0, 0, w, int(h * 0.64))).resize((tw, th), Image.NEAREST)  # the 3D strip above the pads
            x, y = (i % cols) * tw, (i // cols) * (th + 22)
            sheet.paste(im, (x, y + 22))
            d.text((x + 6, y + 5), "%s / %s" % (c, r), fill=(230, 230, 255))
        Path(outdir).mkdir(parents=True, exist_ok=True)
        sheet.save(Path(outdir) / ("contact_%s.jpg" % c), quality=88)
        print("contact_%s.jpg: %d rooms" % (c, len(files)))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "list":
        for c, r, cam, b in specs():
            print("%s|%s|%s|%d" % (c, r, cam, b))
    elif len(sys.argv) >= 4 and sys.argv[1] == "sheets":
        sheets(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
