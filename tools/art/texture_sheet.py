#!/usr/bin/env python3
"""Every texture of every map at a glance, and a small style check over them (docs/art/STYLE_GUIDE.md, section 9).

    python tools/art/texture_sheet.py <out_dir> [map ...]        default: every folder under assets/story with a textures/ folder

Writes <out_dir>/textures_<map>.jpg: each PNG of assets/story/<map>/textures at 2x (nearest), labelled, on a mid grey, and prints a table
(also <out_dir>/texture_check.txt) with, per texture:
  colours   distinct colours (a pixel-art tile has few; a resampled vector crop has hundreds)
  smooth    the share of neighbouring pixel pairs that differ by a small step (1..12 of 255): high = smooth gradients / resampling blur,
            the mark of an SVG crop or a filtered scale, not hand-placed pixels
  sat       mean saturation
  px/m      texels per metre from the map's manifest (size / metres); a 360-line picture shows about 369 / d pixels per metre at d metres
Flags: MANYCOL (colours > 600 on a 64 px tile, > 1500 on 128 px or bigger: a resampled vector crop, not pixel art),
       LOWDENS (under 48 px/m: texels at least 2.5x the screen pixel at 3 m, the "magnified blocks" look; skies exempt),
       HIGHDENS (over 200 px/m on a surface: finer than the screen pixel up to 1.8 m, shimmer and a mismatch with its neighbours),
       FRINGE (a cut-out billboard, thing_* or fig_*, with pixels of partial alpha (0 < alpha < 255): an anti-aliased edge, style guide section 6; glows, beams, stars,
       haze, shafts and piece_* light pieces are exempt, and so is any texture a map draws as a soft thing, `blend` add or mix). The fringe column is the share of its
       visible pixels that are partial.
The smooth column is reported only (dithered grain also scores high on it).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def stats(path):
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im).astype(np.int32)
    rgb, al = a[..., :3], a[..., 3]
    m = al > 128
    cols = len(np.unique(rgb[m].reshape(-1, 3), axis=0)) if m.any() else 0
    dx = np.abs(rgb[:, 1:] - rgb[:, :-1]).max(-1)
    mx = m[:, 1:] & m[:, :-1]
    dy = np.abs(rgb[1:] - rgb[:-1]).max(-1)
    my = m[1:] & m[:-1]
    d = np.concatenate([dx[mx], dy[my]])
    smooth = float(((d >= 1) & (d <= 12)).mean()) if d.size else 0.0
    f = rgb.astype(np.float32) / 255.0
    mxc, mnc = f.max(-1), f.min(-1)
    sat = float(((mxc - mnc) / np.maximum(mxc, 1e-3))[m].mean()) if m.any() else 0.0
    vis = al > 0
    fringe = float(((al > 0) & (al < 255)).sum()) / max(int(vis.sum()), 1)
    return im, cols, smooth, sat, fringe


SOFT = ("glow", "beam", "star", "haze", "shaft", "light", "halo", "smoke", "mist", "ray", "spill")


def soft_sprites():
    """Texture file stems that some map draws with `blend` add or mix (soft art: alpha is allowed there)."""
    import json
    out = set()
    mdir = os.path.join(ROOT, "content/story/maps")
    for f in os.listdir(mdir):
        if not f.endswith(".json"):
            continue
        m = json.load(open(os.path.join(mdir, f), encoding="utf-8"))
        tex = m.get("textures", {})
        for t in m.get("things", []):
            if str(t.get("blend", "")) in ("add", "mix"):
                sp = str(t.get("sprite", ""))
                out.add(os.path.splitext(os.path.basename(str(tex.get(sp, sp))))[0])
                out.add(sp)
    return out


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    base = os.path.join(ROOT, "assets/story")
    maps = sys.argv[2:] or sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d, "textures")))
    rep = ["map texture size colours smooth sat px/m fringe flags"]
    soft = soft_sprites()
    for mp in maps:
        tdir = os.path.join(base, mp, "textures")
        files = sorted(f for f in os.listdir(tdir) if f.endswith(".png"))
        man = {}
        mf = os.path.join(base, mp, "manifest.json")
        if os.path.exists(mf):
            import json
            man = json.load(open(mf, encoding="utf-8")).get("textures", {})
        cell = 268
        cols = 8
        rows = (len(files) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cell, 24 + rows * (cell + 16)), (70, 70, 76))
        d = ImageDraw.Draw(sheet)
        d.text((6, 6), "assets/story/%s/textures (2x nearest; wide ones fitted)" % mp, fill=(240, 240, 240))
        for i, f in enumerate(files):
            im, nc, sm, sat, fr = stats(os.path.join(tdir, f))
            big = max(im.size) >= 128
            flags = []
            ent = man.get(f[:-4], {})
            mtr = ent.get("metres")
            mtr = mtr[0] if isinstance(mtr, list) else mtr
            dens = im.width / float(mtr) if mtr else 0.0
            surf = not f.startswith(("thing_", "sky_", "piece_", "fig_"))
            if dens and surf and dens < 48:
                flags.append("LOWDENS")
            if dens and surf and dens > 200:
                flags.append("HIGHDENS")
            if nc > (1500 if big else 600):
                flags.append("MANYCOL")
            cut = f.startswith(("thing_", "fig_")) and not any(k in f for k in SOFT) and f[:-4] not in soft
            if cut and fr > 0.0:
                flags.append("FRINGE")
            rep.append("%s %s %dx%d %d %.2f %.2f %.0f %.3f %s" % (mp, f[:-4], im.width, im.height, nc, sm, sat, dens, fr, ",".join(flags)))
            k = min(2.0, (cell - 8) / max(im.size))
            t = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.NEAREST)
            x, y = (i % cols) * cell + 4, 24 + (i // cols) * (cell + 16)
            sheet.paste(t, (x, y + 14), t)
            d.text((x, y), ("%s %s" % (f[:-4], " ".join(flags)))[:40], fill=(255, 210, 120) if flags else (230, 230, 230))
        p = os.path.join(out, "textures_%s.jpg" % mp)
        sheet.save(p, quality=80, optimize=True)
        print("sheet", p)
    open(os.path.join(out, "texture_check.txt"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
    for fl in ("MANYCOL", "LOWDENS", "HIGHDENS", "FRINGE"):
        print(fl, sum(1 for r in rep[1:] if fl in r), "of", len(rep) - 1)


if __name__ == "__main__":
    main()
