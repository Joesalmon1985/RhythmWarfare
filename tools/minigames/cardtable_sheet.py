#!/usr/bin/env python3
"""The card table's contact sheet (package A8b): the shots of tools/minigames/shoot_cardtable_node.gd, one row per screen size, the four moments across, labelled,
saved as a JPEG under 1 MB.

    python tools/minigames/cardtable_sheet.py <png_dir> <sheet.jpg>
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

MOMENTS = ["1_walkup", "2_hold_dealt", "3_bust", "4_payout"]
SIZES = ["1280x720", "1600x720"]
H = 300  # each shot's height on the sheet


def main() -> None:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    rows = []
    for size in SIZES:
        row = []
        for m in MOMENTS:
            p = src / f"{size}_{m}.png"
            if p.exists():
                im = Image.open(p).convert("RGB")
                row.append((f"{size} {m[2:]}", im.resize((round(im.width * H / im.height), H), Image.LANCZOS)))
        rows.append(row)
    w = max(sum(im.width + 6 for _, im in r) for r in rows if r)
    sheet = Image.new("RGB", (w, len(rows) * (H + 22)), (12, 12, 18))
    d = ImageDraw.Draw(sheet)
    y = 0
    for r in rows:
        x = 0
        for label, im in r:
            sheet.paste(im, (x, y + 18))
            d.text((x + 4, y + 3), label, fill=(230, 230, 230))
            x += im.width + 6
        y += H + 22
    out.parent.mkdir(parents=True, exist_ok=True)
    q = 88
    while True:
        sheet.save(out, quality=q, optimize=True)
        if out.stat().st_size < 1_000_000 or q <= 40:
            break
        q -= 8
    print("wrote", out, sheet.size, out.stat().st_size, "bytes, quality", q)


if __name__ == "__main__":
    main()
