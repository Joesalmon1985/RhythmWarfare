#!/usr/bin/env python3
"""Contact sheet of the shots tools/doom/shoot_scene.sh wrote: python3 tools/doom/shoot_scene.py <out_dir>  ->  <out_dir>/contact_16x9.jpg and contact_20x9.jpg (labelled, 3 columns)."""
import glob
import os
import sys

from PIL import Image, ImageDraw


def main(out):
    for asp in ("16x9", "20x9"):
        files = sorted(glob.glob(os.path.join(out, "*_%s.jpg" % asp)))
        files = [f for f in files if not os.path.basename(f).startswith("contact")]
        if not files:
            continue
        ref = [f for f in files if os.path.basename(f).startswith("ref_")]
        files = ref + [f for f in files if f not in ref]
        w = 560
        ims = [Image.open(f).convert("RGB") for f in files]
        h = int(w * ims[0].height / ims[0].width)
        cols = 3
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * w, rows * (h + 16)), (12, 12, 20))
        d = ImageDraw.Draw(sheet)
        for i, (f, im) in enumerate(zip(files, ims)):
            x, y = (i % cols) * w, (i // cols) * (h + 16)
            sheet.paste(im.resize((w, h)), (x, y + 16))
            d.text((x + 4, y + 2), os.path.basename(f).replace("_%s.jpg" % asp, ""), fill=(230, 230, 240))
        sheet.save(os.path.join(out, "contact_%s.jpg" % asp), quality=80)
        print("contact sheet", asp, len(files), "shots")


if __name__ == "__main__":
    main(sys.argv[1])
