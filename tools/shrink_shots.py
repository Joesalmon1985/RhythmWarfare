#!/usr/bin/env python3
"""Shrink the proof shots under docs/shots (docs/REPO_SIZE.md, section C). Nothing in the game or the tests reads them (docs/ is .gdignore'd).

    python3 tools/shrink_shots.py [--dry-run] [folder ...]      default folder: docs/shots

Rules (idempotent: a second run changes nothing):
  * JPEG: a sheet wider than 3000 px (the face and figure sheets are 4 to 8 times zoomed pixel art, 4000 to 5000 px wide) is halved with a box
    filter (an exact 2x reduction of the zoom: heads stay pixel-sharp at 4x); anything else keeps its size. Re-saved at quality 85, 4:4:4,
    optimised and progressive; kept only if it is at least 25 % smaller.
  * PNG screenshot (RGB, no alpha): quantised to a 256-colour palette without dithering; kept only if it is at least 40 % smaller and the
    result is within 38 dB PSNR of the original (flat pixel art and UI pass; smooth light gradients fail and stay as they were).
  * Files under 60 KB, and runtime art (anything outside the given folders), are never touched.
Run it again after a capture script has written new shots, before committing them (the capture tools save full-size, high-quality files).
Needs Pillow and NumPy.
"""
import io
import os
import sys

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
MIN_BYTES = 60_000
JPEG_Q, JPEG_GAIN, SHEET_W = 85, 0.75, 3000
PNG_GAIN, PNG_PSNR = 0.60, 38.0


def psnr(a: Image.Image, b: Image.Image) -> float:
    x = np.asarray(a.convert("RGB"), dtype=np.float32)
    y = np.asarray(b.convert("RGB"), dtype=np.float32)
    mse = float(np.mean((x - y) ** 2))
    return 99.0 if mse == 0 else 10 * np.log10(255.0 * 255.0 / mse)


def shrink_jpeg(path: str):
    im = Image.open(path)
    im.load()
    w, h = im.size
    if w > SHEET_W:
        im = im.resize((w // 2, h // 2), Image.BOX)
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=JPEG_Q, optimize=True, progressive=True, subsampling=0)
    data = buf.getvalue()
    return data if len(data) <= JPEG_GAIN * os.path.getsize(path) else None


def shrink_png(path: str):
    im = Image.open(path)
    im.load()
    if im.mode not in ("RGB", "P", "L") or im.mode == "P" and "transparency" in im.info:
        return None
    if im.mode != "RGB":
        return None  # already a palette or grey file: nothing to gain
    q = im.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    if psnr(im, q) < PNG_PSNR:
        return None
    buf = io.BytesIO()
    q.save(buf, "PNG", optimize=True)
    data = buf.getvalue()
    return data if len(data) <= PNG_GAIN * os.path.getsize(path) else None


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    roots = args or ["docs/shots"]
    before = after = changed = 0
    for root in roots:
        for dp, dn, fn in os.walk(root):
            for f in sorted(fn):
                p = os.path.join(dp, f)
                low = f.lower()
                if os.path.getsize(p) < MIN_BYTES or not low.endswith((".jpg", ".jpeg", ".png")):
                    continue
                data = shrink_jpeg(p) if low.endswith((".jpg", ".jpeg")) else shrink_png(p)
                if data is None:
                    continue
                old = os.path.getsize(p)
                before += old
                after += len(data)
                changed += 1
                if not dry:
                    with open(p, "wb") as fh:
                        fh.write(data)
    print(f"{'would change' if dry else 'changed'} {changed} files: {before / 2**20:.1f} MiB -> {after / 2**20:.1f} MiB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
