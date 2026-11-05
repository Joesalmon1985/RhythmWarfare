#!/usr/bin/env python3
"""The acting shots of the Mission Count: `list` prints one line per hotspot that directs a person (hotspot id, scene, actor, RW_STORY_CAM value); `stitch <raw dir> <out dir>` joins the five states
(available, selected, committed, success, failure) of each into docs/shots/acting/squadron_<hotspot>.jpg and a contact sheet per world (see tools/run/contact_acting.py, which this reuses)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "run"))
import contact_acting  # noqa: E402

DIST, PITCH = 2.4, -7.0


def frames():
    out = []
    for fn in sorted((ROOT / "content/paths/squadron/hotspots").glob("*.json")):
        doc = json.loads(fn.read_text(encoding="utf-8"))
        for h in doc["hotspots"]:
            a = h.get("acting")
            if not a:
                continue
            actor = a.get("actor") or (h.get("anchor") or {}).get("actor")
            if actor:
                out.append((doc["world"], h["id"], h["scene"], actor, "actor:%s:%.1f:%.1f" % (actor, DIST, PITCH)))
    return out


def stitch(raw: Path, out: Path):
    from PIL import Image
    out.mkdir(parents=True, exist_ok=True)
    by_world = {}
    for world, hid, scene, actor, cam in frames():
        name = hid.replace(".", "_")
        im = contact_acting.strip(raw, name, f"{hid} ({actor})")
        if im is None:
            continue
        im.save(out / f"squadron_{name}.jpg", quality=80)
        by_world.setdefault(world, []).append(im)
    for world, ims in by_world.items():
        sheet = Image.new("RGB", (ims[0].width, sum(i.height for i in ims)), (14, 10, 22))
        y = 0
        for i in ims:
            sheet.paste(i, (0, y))
            y += i.height
        sheet.save(out / f"contact_acting_squadron_{world}.jpg", quality=80)
        print(out / f"contact_acting_squadron_{world}.jpg")


if __name__ == "__main__":
    if sys.argv[1] == "list":
        for w, hid, scene, actor, cam in frames():
            print(w, hid, scene, actor, cam)
    else:
        stitch(Path(sys.argv[2]), Path(sys.argv[3]))
