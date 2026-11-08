"""The three Warehouse guides (docs/doom/scenes/warehouse.md): 256 px tall billboard sprites, 160 x 256, ordered-dither shading, a face with an expression.

    python -I tools/doom/art/make_guides.py        writes assets/story/doom_warehouse/textures/guide_<who>_<state>_<n>.png and docs/shots/doom/warehouse/guides_sheet.png

PLACEHOLDER art: procedural (capsule limbs, light-from-top-left dithering, hashed sequins and patterns), at the sheet size and layout of the owner's standard
(reference/guide_floor_sprite_standard.png: about 230 px for a 1.8 m figure) but not at its painterly finish. An art pass replaces the PNGs; the file names,
sizes and frames per state are the data contract: idle 1, available 5 (the beckon loop), selected 2, committed 2.

Guides: `bar` (waistcoat, open palm; route left), `stage` (long coat, red scarf; route ahead), `lounge` (mustard cardigan, patterned cushion; route right).
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = os.path.join(ROOT, "assets", "story", "doom_warehouse", "textures")
SHEET = os.path.join(ROOT, "docs", "shots", "doom", "warehouse", "guides_sheet.png")
W, H = 160, 256
CX, FEET = 80, 251
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
FRAMES = {"idle": 1, "available": 5, "selected": 2, "committed": 2}


def hexc(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def tones(base, k=0.62):
    r, g, b = hexc(base)
    dark = (int(r * k), int(g * k * 0.95), int(min(255, b * k * 1.15 + 14)))
    light = (min(255, int(r + (255 - r) * 0.38)), min(255, int(g + (255 - g) * 0.36)), min(255, int(b + (255 - b) * 0.30)))
    return dark, (r, g, b), light


class Canvas:
    def __init__(self):
        self.rgb = np.zeros((H, W, 3), np.uint8)
        self.alpha = np.zeros((H, W), bool)

    def mask(self):
        m = Image.new("L", (W, H), 0)
        return m, ImageDraw.Draw(m)

    def paint(self, m, base, light=(-0.6, -0.7), sparkle=None, seed=0, pattern=None):
        a = np.array(m) > 127
        if not a.any():
            return
        blur = np.array(m.filter(ImageFilter.GaussianBlur(4.0))).astype(float) / 255.0
        gy, gx = np.gradient(blur)
        n = np.hypot(gx, gy) + 1e-6
        ox, oy = -gx / n, -gy / n
        lit = ox * light[0] + oy * light[1]  # outward normal against the light: -1 the shadow side .. 1 the lit side
        rim = np.clip((0.62 - blur) * 2.2, 0, 1)  # near the edge the normal counts, inside the body it is flat
        v = 0.5 + 0.5 * lit * rim
        yy, xx = np.mgrid[0:H, 0:W]
        d = v + (BAYER[yy % 4, xx % 4] - 0.5) * 0.55
        dark, mid, lite = tones(base)
        out = np.empty((H, W, 3), np.uint8)
        out[:] = mid
        out[d < 0.36] = dark
        out[d > 0.70] = lite
        if sparkle is not None:  # sequins: hashed 2 x 1 pixels in the palette
            h = ((xx // 2) * 73856093 ^ yy * 19349663 ^ seed * 83492791) % 997 / 997.0
            pal = [hexc(c) for c in sparkle]
            for i, c in enumerate(pal):
                s = (h >= i * 0.30 / len(pal)) & (h < (i + 1) * 0.30 / len(pal))
                out[s] = c
        if pattern is not None:
            pal = [hexc(c) for c in pattern]
            sel = (((xx + yy) % 9 == 0) | ((xx - yy) % 9 == 0)) & ((xx // 4 + yy // 4) % 2 == 0)
            out[sel] = pal[0]
            out[(xx % 9 == 4) & (yy % 9 == 4)] = pal[1 % len(pal)]
        self.rgb[a] = out[a]
        self.alpha |= a
        edge = a & ~(np.array(m.filter(ImageFilter.MinFilter(3))) > 127)  # the part's own boundary a shade darker
        self.rgb[edge] = (np.array(dark) * 0.8).astype(np.uint8)

    def outline(self, col="#120a22"):
        m = Image.fromarray((self.alpha * 255).astype(np.uint8))
        grown = np.array(m.filter(ImageFilter.MaxFilter(3))) > 127
        ring = grown & ~self.alpha
        self.rgb[ring] = hexc(col)
        self.alpha |= ring

    def image(self):
        out = np.zeros((H, W, 4), np.uint8)
        out[..., :3] = self.rgb
        out[..., 3] = np.where(self.alpha, 255, 0)
        return Image.fromarray(out, "RGBA")


def capsule(d, p0, p1, r0, r1):
    d.ellipse([p0[0] - r0, p0[1] - r0, p0[0] + r0, p0[1] + r0], fill=255)
    d.ellipse([p1[0] - r1, p1[1] - r1, p1[0] + r1, p1[1] + r1], fill=255)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]) + math.pi / 2
    d.polygon([(p0[0] + math.cos(ang) * r0, p0[1] + math.sin(ang) * r0), (p1[0] + math.cos(ang) * r1, p1[1] + math.sin(ang) * r1),
               (p1[0] - math.cos(ang) * r1, p1[1] - math.sin(ang) * r1), (p0[0] - math.cos(ang) * r0, p0[1] - math.sin(ang) * r0)], fill=255)


def limb(pts, radii):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for i in range(len(pts) - 1):
        capsule(d, pts[i], pts[i + 1], radii[i], radii[i + 1])
    return m


def arm_pts(side, shoulder, au, af, lu=46, lf=42):
    """side +1 = screen right. Angles from straight down, positive outward and up; returns shoulder, elbow, hand."""
    e = (shoulder[0] + side * lu * math.sin(math.radians(au)), shoulder[1] + lu * math.cos(math.radians(au)))
    h = (e[0] + side * lf * math.sin(math.radians(af)), e[1] + lf * math.cos(math.radians(af)))
    return shoulder, e, h


def poses(state, i):
    wide = {"idle": 0.5, "available": 0.8, "selected": 1.0, "committed": 0.9}[state]
    if state == "idle":
        return dict(ra=(14, 10), la=(14, 10), lean=0, tilt=0, smile=wide, steps=0)
    if state == "available":  # the beckon loop: the beckoning arm out, the forearm waving in and out
        w = [(70, 100), (74, 128), (78, 150), (74, 128), (70, 100)][i]
        return dict(ra=w, la=(14, 10), lean=1, tilt=-2 if i % 2 else 2, smile=wide, steps=0)
    if state == "selected":  # a step towards the player and the arm raised, then waving over the head
        a = [(150, 168), (158, 150)][i]
        return dict(ra=a, la=(14, 10), lean=0, tilt=2, smile=wide, steps=1)
    g = [(92, 94), (96, 96)][i]  # committed: the gesture towards the opening, the body turned into it
    return dict(ra=g, la=(14, 10), lean=3, tilt=3, smile=wide, steps=0)


GUIDES = {
    "bar": dict(skin="#c58f62", hair="#2a1a14", top="#f1ece0", vest="#8c2230", trousers="#2f2a33", shoes="#4a2c1a", curly=True, moustache=True, glasses=False, accent="#d9a441"),
    "stage": dict(skin="#e8bf9d", hair="#d9dde6", top="#2b3a4c", vest="#27384a", trousers="#1c1f2e", shoes="#15121c", curly=False, moustache=False, glasses=False, accent="#c1272d"),
    "lounge": dict(skin="#a96b45", hair="#1c1410", top="#efe6d0", vest="#d19a2a", trousers="#5a3f2a", shoes="#3a2416", curly=False, moustache=False, glasses=True, accent="#2a8f9a"),
}


def draw_guide(who, state, i):
    g = GUIDES[who]
    p = poses(state, i)
    c = Canvas()
    lean = p["lean"]
    stepdy = 4 if p["steps"] else 0
    hipy, shy = 142, 80
    hx = CX + lean * 0.4
    shx = CX + lean
    if who == "stage":  # long hair behind the shoulders
        m, d = c.mask()
        d.polygon([(shx - 22, 56), (shx + 22, 56), (shx + 26, 98), (shx + 20, 112), (shx - 20, 112), (shx - 26, 98)], fill=255)
        c.paint(m, g["hair"])
    spread = 14 + (2 if p["steps"] else 0)
    for sx_ in (-1, 1):
        top = (hx + sx_ * 9, hipy)
        lift = stepdy if sx_ == 1 else 0
        foot = (hx + sx_ * spread, FEET - 10 - lift)
        m = limb([top, ((top[0] + foot[0]) / 2, (top[1] + foot[1]) / 2), foot], [13, 11, 8])
        c.paint(m, g["trousers"])
        m, d = c.mask()
        d.rounded_rectangle([foot[0] - 11 + sx_ * 3, foot[1] + 2, foot[0] + 11 + sx_ * 3, foot[1] + 11 + lift], radius=4, fill=255)
        c.paint(m, g["shoes"])
    m, d = c.mask()
    d.polygon([(shx - 25, shy - 2), (shx + 25, shy - 2), (hx + 21, hipy + 6), (hx - 21, hipy + 6)], fill=255)
    if who == "stage":  # the long coat to the knees, open over a dark top
        m2, d2 = c.mask()
        d2.polygon([(shx - 27, shy - 2), (shx + 27, shy - 2), (hx + 31, 205), (hx - 31, 205)], fill=255)
        c.paint(m2, g["top"], light=(-0.5, -0.7))
        m3, d3 = c.mask()
        d3.polygon([(shx - 6, shy), (shx + 6, shy), (hx + 9, 205), (hx - 9, 205)], fill=255)
        c.paint(m3, "#10131f")
    elif who == "bar":
        c.paint(m, g["top"])  # shirt
        mv, dv = c.mask()
        dv.polygon([(shx - 21, shy), (shx - 6, shy), (shx - 1, hipy - 6), (hx - 19, hipy + 6), (hx - 20, hipy - 10)], fill=255)
        dv.polygon([(shx + 21, shy), (shx + 6, shy), (shx + 1, hipy - 6), (hx + 19, hipy + 6), (hx + 20, hipy - 10)], fill=255)
        c.paint(mv, g["vest"], seed=3)
        for k in range(4):  # buttons
            y0 = hipy - 40 + k * 11
            c.rgb[y0:y0 + 2, int(hx) - 1:int(hx) + 1] = hexc("#d9a441")
            c.alpha[y0:y0 + 2, int(hx) - 1:int(hx) + 1] = True
    else:  # lounge: cardigan over a white shirt
        c.paint(m, g["vest"], seed=5)
        mv, dv = c.mask()
        dv.polygon([(shx - 7, shy - 2), (shx + 7, shy - 2), (hx + 5, hipy + 4), (hx - 5, hipy + 4)], fill=255)
        c.paint(mv, g["top"])
    shL = (shx - 24, shy + 4)
    shR = (shx + 24, shy + 4)
    sleeve = g["vest"] if who == "lounge" else g["top"]
    for sd, sh, ang in ((-1, shL, p["la"]), (1, shR, p["ra"])):
        pts = arm_pts(sd, sh, ang[0], ang[1])
        if who == "lounge" and sd == -1:
            pts = (shL, (shL[0] + 8, shL[1] + 38), (shL[0] + 26, shL[1] + 46))  # the cushion held across the body
        m = limb(list(pts), [9, 8, 6])
        c.paint(m, sleeve, seed=7 + sd)
        hand = pts[2]
        m, d = c.mask()
        r = 7 if (sd == 1 and state != "idle") else 6
        d.ellipse([hand[0] - r, hand[1] - r - 1, hand[0] + r, hand[1] + r + 1], fill=255)
        if sd == 1 and state != "idle":  # open palm: the fingers
            d.rounded_rectangle([hand[0] - 5, hand[1] - r - 7, hand[0] + 5, hand[1] - r + 2], radius=3, fill=255)
        c.paint(m, g["skin"])
        if who == "bar" and sd == 1:  # rolled cuff
            m, d = c.mask()
            e = pts[1]
            d.ellipse([e[0] - 10, e[1] - 6, e[0] + 10, e[1] + 6], fill=255)
            c.paint(m, g["top"])
    if who == "lounge":  # the cushion: teal with a gold pattern
        m, d = c.mask()
        cx0, cy0 = shL[0] + 12, shL[1] + 44
        d.rounded_rectangle([cx0 - 22, cy0 - 18, cx0 + 22, cy0 + 20], radius=6, fill=255)
        c.paint(m, "#237f86", pattern=["#e0b04a", "#f2d27a"])
        m, d = c.mask()
        hand = (shL[0] + 26, shL[1] + 46)
        d.ellipse([hand[0] - 6, hand[1] - 6, hand[0] + 6, hand[1] + 6], fill=255)
        c.paint(m, g["skin"])
    if who == "stage":  # the red scarf: a tail flying out to the side, moving with the frame
        m, d = c.mask()
        d.ellipse([shx - 18, shy - 16, shx + 18, shy + 2], fill=255)
        fl = [0, 6, 10, 6, 0][i] if state == "available" else 4
        d.polygon([(shx + 8, shy - 8), (shx + 18, shy - 4), (shx + 30 + fl, shy + 12 + fl), (shx + 36 + fl, shy + 4 + fl), (shx + 20, shy - 12)], fill=255)
        d.polygon([(shx - 4, shy - 4), (shx + 8, shy), (shx + 6, shy + 40), (shx - 4, shy + 44)], fill=255)
        c.paint(m, g["accent"], seed=11)
    m, d = c.mask()
    d.rectangle([hx - 6, 62, hx + 6, shy], fill=255)
    c.paint(m, g["skin"])
    hxx = hx + p["tilt"]
    m, d = c.mask()
    d.ellipse([hxx - 17, 27, hxx + 17, 70], fill=255)
    c.paint(m, g["skin"])
    m, d = c.mask()
    if g["curly"]:
        for k in range(9):
            a = math.radians(200 + k * 17)
            d.ellipse([hxx + math.cos(a) * 17 - 6, 47 + math.sin(a) * 21 - 6, hxx + math.cos(a) * 17 + 6, 47 + math.sin(a) * 21 + 6], fill=255)
        d.ellipse([hxx - 17, 26, hxx + 17, 46], fill=255)
    elif who == "stage":
        d.chord([hxx - 19, 24, hxx + 19, 66], 180, 360, fill=255)
        d.rectangle([hxx - 19, 44, hxx - 14, 74], fill=255)
        d.rectangle([hxx + 14, 44, hxx + 19, 74], fill=255)
    else:
        d.chord([hxx - 18, 24, hxx + 18, 60], 180, 360, fill=255)
    c.paint(m, g["hair"], seed=13)
    c.outline()
    ex, ey = 7, 49  # the face, drawn after the outline so it stays crisp
    img = c.rgb
    brow = hexc(g["hair"]) if who != "stage" else (120, 120, 130)
    for sx_ in (-1, 1):
        x0 = int(hxx + sx_ * ex)
        img[ey - 1:ey + 1, x0 - 2:x0 + 2] = (250, 250, 250)
        img[ey - 1:ey + 1, x0 - 1 + (1 if sx_ > 0 else 0):x0 + 1 + (1 if sx_ > 0 else 0)] = (30, 20, 24)
        img[ey - 5:ey - 4, x0 - 3:x0 + 3] = brow
    img[ey + 5:ey + 9, int(hxx):int(hxx) + 2] = tuple(int(v * 0.8) for v in hexc(g["skin"]))
    sm = int(round(3 * p["smile"]))
    for k in range(-5, 6):  # the mouth: a curve whose depth is the smile
        yy = ey + 14 + int(round(sm * (k / 5.0) ** 2))
        img[yy:yy + 1, int(hxx) + k] = (150, 40, 52) if who != "stage" else (170, 40, 60)
    if p["smile"] > 0.7:
        img[ey + 13:ey + 14, int(hxx) - 3:int(hxx) + 4] = (252, 248, 240)  # teeth
    if g["moustache"]:
        img[ey + 10:ey + 12, int(hxx) - 6:int(hxx) + 7] = hexc(g["hair"])
    if g["glasses"]:
        for sx_ in (-1, 1):
            x0 = int(hxx + sx_ * ex)
            img[ey - 4:ey - 3, x0 - 4:x0 + 5] = (40, 30, 30)
            img[ey + 3:ey + 4, x0 - 4:x0 + 5] = (40, 30, 30)
            img[ey - 4:ey + 4, x0 - 4:x0 - 3] = (40, 30, 30)
            img[ey - 4:ey + 4, x0 + 4:x0 + 5] = (40, 30, 30)
    return c.image()


# --- crops from the paintings (stage D polish, ruling 36) ----------------------------------------------------------------------------------------------------------------
# Where a painting shows a guide 180 px tall or more, the sprite is CUT from it: a hand-traced polygon (painting pixels) round the figure is the surround's limit; inside a
# band along its edge every pixel nearer in colour to the surround (a local mean outside the polygon) than to the figure (a local mean inside) is dropped; the mask is
# cleaned with a small opening and closing; the figure is scaled nearest-neighbour so the head (crown to chin) is HEAD_FRAC of FIG_H; what the painting hides (the legs under a
# counter, a railing or the crowd) is drawn below the cut by the procedural painter in the painting's colours. The four states are small edits of that one picture.
REF = os.path.join(ROOT, "art", "reference")
FIG_H = 230  # a 1.8 m figure on the 256 sheet (feet at FEET)
HEAD_FRAC = 1 / 6.5  # the head (crown to chin) of the figure height: the paintings' people are drawn about 6.5 heads tall
WARM_RIM = (255, 214, 150)


def _blur(a, r):
    im = Image.fromarray(np.clip(a * 255.0, 0, 255).astype(np.uint8))
    return np.array(im.filter(ImageFilter.BoxBlur(r))).astype(float) / 255.0


def figure_mask(img, poly, band=7, keep=0.85):
    """img: HxWx3 uint8 painting; poly: [(x, y)] round the figure. Returns a bool mask (colour-distance refinement of the polygon's edge band)."""
    h, w = img.shape[:2]
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=255)
    inside = np.array(m) > 127
    core = np.array(m.filter(ImageFilter.MinFilter(2 * band + 1))) > 127
    ring = (np.array(m.filter(ImageFilter.MaxFilter(2 * band + 1))) > 127) & ~inside
    f = img.astype(float) / 255.0
    out_mean = np.zeros_like(f)
    in_mean = np.zeros_like(f)
    wo = _blur(ring.astype(float), 2 * band) + 1e-4
    wi = _blur(core.astype(float), 3 * band) + 1e-4
    for k in range(3):
        out_mean[..., k] = _blur(f[..., k] * ring, 2 * band) / wo
        in_mean[..., k] = _blur(f[..., k] * core, 3 * band) / wi
    d_out = np.linalg.norm(f - out_mean, axis=2)
    d_in = np.linalg.norm(f - in_mean, axis=2)
    edge = inside & ~core
    drop = edge & (d_out < d_in * keep) & (d_out < 0.16)
    mask = inside & ~drop
    mi = Image.fromarray((mask * 255).astype(np.uint8))
    mi = mi.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))  # opening: specks of surround go
    mi = mi.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))  # closing: pinholes in the figure go
    return (np.array(mi) > 127) & inside


def cut_figure(src, poly, top, chin, cut, centre_x):
    """The figure as RGBA at sprite scale: (rgba array, scale, x offset of the painting's centre_x in it, the cut row in sprite pixels)."""
    im = np.array(Image.open(os.path.join(REF, src)).convert("RGB"))
    mask = figure_mask(im, poly)
    xs = [p[0] for p in poly]
    x0, x1 = int(min(xs)) - 1, int(max(xs)) + 2
    y0, y1 = int(top), int(cut)
    rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    rgba[..., :3] = im[y0:y1, x0:x1]
    rgba[..., 3] = np.where(mask[y0:y1, x0:x1], 255, 0)
    s = FIG_H * HEAD_FRAC / float(chin - top) if chin > 0 else FIG_H / float(cut - top)  # chin 0: the whole figure is in the painting, feet at `cut`
    nw, nh = max(1, int(round((x1 - x0) * s))), max(1, int(round((y1 - y0) * s)))
    small = np.array(Image.fromarray(rgba, "RGBA").resize((nw, nh), Image.NEAREST))
    small[..., 3] = np.where(small[..., 3] > 127, 255, 0)
    return small, s, (centre_x - x0) * s, nh


def continue_down(c, fig, ox, oy, s, spec):
    """What the painting hides under the cut, continued from the painting's own pixels: the bottom rows of the cut (columns `src_span`, painting x) are repeated downward
    (mirror-tiled, darkening toward the floor) over a span that tapers from `hip` (sprite px either side of CX) to the ankles, split into two legs below `split` (0..1 of the
    way down); a coat (`coat_to`, 0..1) keeps the full span to that point. Shoes are painted. Pure pixels of the painting: no new colours but the shoes and the shadow."""
    h = fig.shape[0]
    top = oy + h
    ground = FEET - 10
    def grab(spans, rows=None):  # the band of the cut (or of painting rows) under the painting columns of `spans` ((x0, x1) or (x0, x1, y0, y1)), side by side
        if isinstance(spans[0], (int, float)):
            spans = [spans]
        parts = []
        for sp in spans:
            rr = rows if len(sp) < 4 else sp[2:4]
            r0, r1 = (h - 8, h) if rr is None else (int(round((rr[0] - spec["_top"]) * s)), int(round((rr[1] - spec["_top"]) * s)))
            q = fig[r0:r1, int(round((sp[0] - spec["_x0"]) * s)):int(round((sp[1] - spec["_x0"]) * s))]
            if q.shape[0] and q.shape[1]:
                parts.append(q if not parts else np.array(Image.fromarray(q, "RGBA").resize((q.shape[1], parts[0].shape[0]), Image.NEAREST)))
        return np.concatenate(parts, axis=1)

    band = grab(spec["src_span"], spec.get("band_y"))
    bh, bw = band.shape[:2]
    if bw < 2:
        return
    hs = spec.get("hip_span", spec["src_span"] if isinstance(spec["src_span"][0], (int, float)) else (spec["src_span"][0][0], spec["src_span"][-1][1]))
    hl = ox + int(round((hs[0] - spec["_x0"]) * s)) - CX
    hr = ox + int(round((hs[1] - spec["_x0"]) * s)) - CX
    ank = spec.get("ankle", 6)
    stance = spec.get("stance", 10)
    split = spec.get("split", 0.0)
    coat_to = spec.get("coat_to", 0.0)
    leg_band = None
    if spec.get("leg_span"):
        leg_band = grab(spec["leg_span"], spec.get("leg_y"))
    for y in range(top, ground + 1):
        t = (y - top) / float(max(1, ground - top))
        k = (y - top) % (2 * bh)
        r = bh - 1 - (k if k < bh else 2 * bh - 1 - k)
        shade = 1.0 - 0.22 * t
        if coat_to and t <= coat_to:  # the coat skirt: the whole span, narrowing toward the knee
            nar = (hr - hl) * 0.22 * (t / coat_to)
            L, R = CX + hl + nar, CX + hr - nar
            spans = [(L, R, band)]
        else:
            u = (t - coat_to) / max(1e-6, 1.0 - coat_to) if coat_to else t
            gap = 0 if u < split else min(4.0, (u - split) * 14)
            src = leg_band if (leg_band is not None and leg_band.shape[1] >= 2) else band
            mid = CX + (hl + hr) / 2.0
            lo_l, lo_r = mid - stance - ank, mid - stance + ank
            ro_l, ro_r = mid + stance - ank, mid + stance + ank
            if coat_to:  # legs out from under a coat: they start at their own width, not the skirt's
                hl, hr = mid - CX - stance - ank - 3, mid - CX + stance + ank + 3
            L1 = CX + hl + (lo_l - CX - hl) * u
            R1 = mid - gap / 2 + (lo_r - mid + gap / 2) * u * 0.6
            L2 = mid + gap / 2 + (ro_l - mid - gap / 2) * u * 0.6
            R2 = CX + hr + (ro_r - CX - hr) * u
            if gap <= 0:
                spans = [(L1, R2, src)]
            else:
                spans = [(L1, R1, src[:, :max(1, src.shape[1] // 2)]), (L2, R2, src[:, src.shape[1] // 2:])]
        for (L, R, sb) in spans:
            L, R = int(round(L)), int(round(R))
            if R <= L:
                continue
            for X in range(L, R + 1):
                if not (0 <= X < W and 0 <= y < H) or c.alpha[y, X]:
                    continue
                sx = int((X - L) / float(max(1, R - L)) * (sb.shape[1] - 1))
                px = sb[min(r, sb.shape[0] - 1), sx]
                if px[3] == 0:
                    px = sb[:, sx][sb[:, sx, 3] > 0][0] if (sb[:, sx, 3] > 0).any() else None
                    if px is None:
                        continue
                c.rgb[y, X] = (np.array(px[:3], float) * shade).astype(np.uint8)
                c.alpha[y, X] = True
    mid = CX + (hl + hr) / 2.0
    for sx_ in (-1, 1):
        fx = mid + sx_ * stance + sx_ * 2
        m, d = c.mask()
        d.rounded_rectangle([fx - 9, ground - 1, fx + 9, ground + 8], radius=4, fill=255)
        c.paint(m, spec.get("shoes", "#2a1a14"))


def rim(rgb, alpha, strength, col=WARM_RIM, side=(-1, -1)):
    """A lamp-lit rim: the figure's pixels whose upper-left neighbours are empty, pulled toward the lamp colour; dithered so it reads as light, not a line."""
    a = alpha
    edge = np.zeros_like(a)
    for dy, dx in ((side[1], 0), (0, side[0]), (side[1], side[0])):
        sh = np.zeros_like(a)
        ys = slice(max(0, -dy), a.shape[0] - max(0, dy)) if dy else slice(None)
        ys2 = slice(max(0, dy), a.shape[0] - max(0, -dy)) if dy else slice(None)
        xs = slice(max(0, -dx), a.shape[1] - max(0, dx)) if dx else slice(None)
        xs2 = slice(max(0, dx), a.shape[1] - max(0, -dx)) if dx else slice(None)
        sh[ys2, xs2] = a[ys, xs]
        edge |= a & ~sh
    grown = edge | (np.roll(edge, 1, 1) & a) | (np.roll(edge, 1, 0) & a)
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    dith = BAYER[yy % 4, xx % 4]
    sel = (edge & (dith < 0.4 + strength * 0.6)) | (grown & (dith < strength * 0.5))
    out = rgb.astype(float)
    out[sel] = out[sel] * (1 - strength * 0.7) + np.array(col) * strength * 0.7
    return np.clip(out, 0, 255).astype(np.uint8)


def shear(rgb, alpha, box, dy_max):
    """Lifts the region `box` (x0, y0, x1, y1; xa the column that stays, xb the column lifted by dy_max) column by column: a hand raised from the wrist."""
    x0, y0, x1, y1, xa, xb = box
    r2, a2 = rgb.copy(), alpha.copy()
    for x in range(min(x0, x1), max(x0, x1) + 1):
        if not 0 <= x < rgb.shape[1]:
            continue
        f = (x - xa) / float(xb - xa) if xb != xa else 1.0
        dy = int(round(dy_max * max(0.0, min(1.0, f))))
        if dy == 0:
            continue
        for y in range(max(0, y0 - dy_max - 1), min(rgb.shape[0], y1 + 1)):
            sy = y + dy
            if y0 - dy <= y <= y1 and 0 <= sy < rgb.shape[0]:
                r2[y, x], a2[y, x] = rgb[sy, x], alpha[sy, x]
    return r2, a2


def crop_guide(spec):
    """Every frame of a cropped guide: {(state, i): RGBA Image}. spec: src, poly, top, hip, cut, centre_x, legs{...}, hand (painting box x0,y0,x1,y1,xa,xb)."""
    fig, s, cx_off, cut_row = cut_figure(spec["src"], spec["poly"], spec["top"], spec["chin"], spec["cut"], spec["centre_x"])
    base = Canvas()
    ox = int(round(CX - cx_off))
    oy = FEET - FIG_H
    h, w = fig.shape[:2]
    for y in range(h):
        Y = oy + y
        if not 0 <= Y < H:
            continue
        row = fig[y]
        for x in range(w):
            X = ox + x
            if 0 <= X < W and row[x, 3]:
                base.rgb[Y, X] = row[x, :3]
                base.alpha[Y, X] = True
    if spec.get("legs"):
        lg = dict(spec["legs"])
        lg["_x0"] = int(min(p[0] for p in spec["poly"])) - 1
        lg["_top"] = spec["top"]
        continue_down(base, fig, ox, oy, s, lg)
    m = Image.fromarray((base.alpha * 255).astype(np.uint8))  # the one-pixel edge a step darker than the local colour (style guide section 6), not a black line
    grown = np.array(m.filter(ImageFilter.MaxFilter(3))) > 127
    ring = grown & ~base.alpha
    dark = np.array(Image.fromarray(base.rgb).filter(ImageFilter.MaxFilter(3))).astype(float)
    base.rgb[ring] = (dark[ring] * 0.32 + np.array(hexc("#120a22")) * 0.68).astype(np.uint8)
    base.alpha |= ring
    hb = None
    if spec.get("hand"):
        x0, y0, x1, y1, xa, xb = spec["hand"]
        tx = lambda x: int(round(ox + (x - (spec["centre_x"] - cx_off / s)) * s))  # noqa: E731
        ty = lambda y: int(round(oy + (y - spec["top"]) * s))  # noqa: E731
        hb = (tx(x0), ty(y0), tx(x1), ty(y1), tx(xa), tx(xb))
    if spec.get("mirror"):  # the painting's figure faces the other way from where this scene needs her
        base.rgb, base.alpha = base.rgb[:, ::-1].copy(), base.alpha[:, ::-1].copy()
        if hb:
            hb = (W - 1 - hb[0], hb[1], W - 1 - hb[2], hb[3], W - 1 - hb[4], W - 1 - hb[5])
    frames = {}
    for state, n in FRAMES.items():
        for i in range(n):
            rgb, al = base.rgb.copy(), base.alpha.copy()
            if state == "idle":
                rgb = (rgb.astype(float) * 0.86).astype(np.uint8)
            elif state == "available":
                lift = [0, 1, 2, 1, 0][i]
                if hb:
                    rgb, al = shear(rgb, al, hb, lift)
                rgb = rim(rgb, al, [0.35, 0.5, 0.65, 0.5, 0.35][i])
            elif state == "selected":
                if hb:
                    rgb, al = shear(rgb, al, hb, [4, 6][i])
                rgb = np.clip(rgb.astype(float) * 1.08, 0, 255).astype(np.uint8)
                rgb = rim(rgb, al, 0.9)
            else:  # committed: turned toward the doorway (mirrored), the front in shadow, a step on
                rgb, al = rgb[:, ::-1].copy(), al[:, ::-1].copy()
                k = 2 + 2 * i
                rgb = np.roll(rgb, -k if spec.get("door_left", True) else k, 1)
                al = np.roll(al, -k if spec.get("door_left", True) else k, 1)
                rgb = (rgb.astype(float) * 0.78).astype(np.uint8)
                rgb = rim(rgb, al, 0.5, side=(1, -1))
            out = np.zeros((H, W, 4), np.uint8)
            out[..., :3] = rgb
            out[..., 3] = np.where(al, 255, 0)
            frames[(state, i)] = Image.fromarray(out, "RGBA")
    return frames


MID = "doom_worlds/Midnight dance hall with three guides-1.png"
CROPS = {  # painting polygons (pixels of the painting), read by eye over a grid (docs/doom/scenes/warehouse.md: guides)
    "bar": dict(src=MID, top=192, chin=322, cut=700, centre_x=190,
                poly=[(150, 205), (185, 192), (230, 195), (262, 215), (275, 250), (262, 290), (240, 320), (232, 335), (255, 345), (275, 385), (290, 450), (298, 488), (340, 478),
                      (372, 466), (395, 470), (410, 490), (400, 505), (365, 512), (330, 520), (300, 545), (290, 580), (292, 640), (296, 700), (80, 700), (82, 640), (85, 590),
                      (60, 565), (35, 540), (25, 500), (28, 440), (40, 395), (60, 365), (95, 340), (130, 325), (150, 310), (125, 270), (128, 230)],
                hand=(330, 455, 412, 525, 320, 412),
                legs=dict(src_span=(200, 290), hip_span=(160, 290), shoes="#3a2416", stance=9, ankle=6)),
    "stage": dict(src=MID, top=25, chin=127, cut=293, centre_x=812,
                  poly=[(757, 45), (773, 31), (830, 24), (863, 40), (874, 70), (863, 100), (863, 120), (897, 183), (930, 190), (967, 187), (980, 170), (1007, 151), (1048, 173),
                        (1030, 185), (997, 198), (973, 208), (950, 218), (943, 233), (950, 293), (686, 293), (686, 273), (692, 220), (706, 162), (730, 137), (740, 105), (737, 80)],
                  hand=(965, 145, 1050, 212, 940, 1050),
                  legs=dict(src_span=[(708, 770, 200, 240), (800, 850, 281, 292), (708, 770, 200, 240)], hip_span=(712, 925), leg_span=(815, 845), leg_y=(281, 292), coat_to=0.5, shoes="#15121c", stance=8, ankle=5)),
    "lounge": dict(src=MID, top=218, chin=335, cut=697, centre_x=1490, door_left=False,
                   poly=[(1430, 225), (1480, 218), (1525, 238), (1545, 280), (1540, 315), (1580, 345), (1615, 372), (1640, 420), (1665, 500), (1668, 580), (1658, 640), (1662, 665),
                         (1612, 672), (1582, 682), (1582, 697), (1405, 697), (1400, 620), (1385, 580), (1380, 520), (1350, 497), (1305, 487), (1298, 472), (1340, 455), (1370, 463),
                         (1400, 440), (1412, 415), (1432, 378), (1448, 330), (1428, 262)],
                   hand=(1296, 440, 1385, 500, 1395, 1296),
                   legs=dict(src_span=(1412, 1540), hip_span=(1412, 1575), split=0.2, shoes="#3a2416", stance=10, ankle=7)),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    cols = sum(FRAMES.values())
    sheet = Image.new("RGBA", (cols * W, 3 * H), (14, 12, 34, 255))
    for r, who in enumerate(GUIDES):
        x = 0
        cropped = crop_guide(CROPS[who]) if who in CROPS else None
        for state, n in FRAMES.items():
            for i in range(n):
                im = cropped[(state, i)] if cropped else draw_guide(who, state, i)
                im.save(os.path.join(OUT, "guide_%s_%s_%d.png" % (who, state, i)))
                sheet.alpha_composite(im, (x * W, r * H))
                x += 1
    sheet.convert("RGB").resize((sheet.width // 2, sheet.height // 2), Image.NEAREST).save(SHEET)
    print("wrote %d sprites to %s and the sheet %s" % (3 * cols, OUT, SHEET))


if __name__ == "__main__":
    sys.exit(main())
