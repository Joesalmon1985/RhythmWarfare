#!/usr/bin/env python3
"""Stitches the acting shots (tools/run/capture.sh --acting) into one strip per character hotspot and one contact sheet per world.

    python3 tools/run/contact_acting.py <raw dir> <out dir>

<raw dir> holds <hotspot name>__<state>.png for the five states (available, selected, committed, success, failure; the person framed by the camera at about twice an ordinary size).
<out dir>/<hotspot name>.jpg is the five states side by side (the middle of each picture, the stage only, never the pads); <out dir>/contact_acting_<world>.jpg stacks the strips of a world.
The captions on the proof images are for the reader of the shots, they are not in the game.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import acting_frames  # noqa: E402

STATES = ["available", "selected", "committed", "success", "failure"]
CROP = (420, 0, 860, 460)  # the stage of a 1280 x 720 window: the camera faces the person, so they are in the middle; the pads are below
PW, PH = 440, 460  # one panel in the strip (the crop at full size: the faces are about 20 pixels)


def strip(raw: Path, name: str, label: str) -> Image.Image | None:
    panels = []
    for st in STATES:
        p = raw / f"{name}__{st}.png"
        panels.append(Image.open(p).convert("RGB").crop(CROP) if p.exists() else None)
    if all(p is None for p in panels):
        return None
    im = Image.new("RGB", (PW * len(STATES), PH + 16), (14, 10, 22))
    dr = ImageDraw.Draw(im)
    for i, p in enumerate(panels):
        if p is not None:
            im.paste(p, (i * PW, 16))
        dr.text((i * PW + 5, 3), (label + "   " if i == 0 else "") + STATES[i], fill=(235, 225, 255))
    return im


def main() -> None:
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    by_world: dict = {}
    for world, hid, scene, actor, flags, cam in acting_frames.frames():
        name = hid.replace(".", "_")
        im = strip(raw, name, f"{hid} ({actor})")
        if im is None:
            continue
        im.save(out / f"{name}.jpg", quality=80)
        print(out / f"{name}.jpg")
        by_world.setdefault(world, []).append(im)
    for world, ims in by_world.items():
        sheet = Image.new("RGB", (ims[0].width, sum(i.height for i in ims)), (14, 10, 22))
        y = 0
        for i in ims:
            sheet.paste(i, (0, y))
            y += i.height
        sheet.save(out / f"contact_acting_{world}.jpg", quality=80)
        print(out / f"contact_acting_{world}.jpg")


if __name__ == "__main__":
    main()
