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


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    cols = sum(FRAMES.values())
    sheet = Image.new("RGBA", (cols * W, 3 * H), (14, 12, 34, 255))
    for r, who in enumerate(GUIDES):
        x = 0
        for state, n in FRAMES.items():
            for i in range(n):
                im = draw_guide(who, state, i)
                im.save(os.path.join(OUT, "guide_%s_%s_%d.png" % (who, state, i)))
                sheet.alpha_composite(im, (x * W, r * H))
                x += 1
    sheet.convert("RGB").resize((sheet.width // 2, sheet.height // 2), Image.NEAREST).save(SHEET)
    print("wrote %d sprites to %s and the sheet %s" % (3 * cols, OUT, SHEET))


if __name__ == "__main__":
    sys.exit(main())
