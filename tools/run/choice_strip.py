"""A choice-clarity strip (docs/shots/choice): the stage area of each shot (the pads cropped off), side by side in two rows, each labelled with its state underneath.
    python tools/run/choice_strip.py out.jpg a.jpg b.jpg ...   (a shot's state is the last _part of its file name)"""
import os
import sys

from PIL import Image, ImageDraw

out, files = sys.argv[1], sys.argv[2:]
files = [f if f.endswith(".jpg") else f + ".jpg" for f in files]
ims = [Image.open(f).convert("RGB") for f in files if os.path.exists(f)]
names = [os.path.basename(f)[:-4].rsplit("_", 1)[-1] for f in files if os.path.exists(f)]
w, h = ims[0].size
stage_h = int(h * 0.64)  # the picture above the pads at 844 x 390
cols = 3 if len(ims) > 3 else len(ims)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * (stage_h + 22)), (12, 10, 20))
d = ImageDraw.Draw(sheet)
for i, (im, nm) in enumerate(zip(ims, names)):
    x, y = (i % cols) * w, (i // cols) * (stage_h + 22)
    sheet.paste(im.crop((0, 0, w, stage_h)), (x, y))
    d.text((x + 8, y + stage_h + 5), nm, fill=(235, 235, 235))
sheet.save(out, quality=88)
