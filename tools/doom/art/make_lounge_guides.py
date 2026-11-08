"""The Chill-out Lounge's two new guides (docs/doom/scenes/lounge.md): `dock` (ahead, to the Dock: a broad bald man in a long green coat with a yellow armband, arm out) and `floor`
(right, back to the Floor: braids, a magenta sequin top, silver trousers, one hand on her hip, the other open), as 160 x 256 billboard sprites in the Warehouse guides' sheet layout
(idle 1, available 5, selected 2, committed 2). The third guide, the Bar's (waistcoat, open palm), is the Warehouse's `bar` sprite set, shared.

    python -I tools/doom/art/make_lounge_guides.py     writes assets/story/doom_lounge/textures/guide_<who>_<state>_<n>.png and docs/shots/doom/lounge/guides_sheet.png

PLACEHOLDER art, like the Warehouse's: procedural capsule limbs and ordered dither at the sheet's size; NOT the painterly finish of art/reference/standard/guide_floor_sprite_standard.png
(a painted 273 x 398 portrait). The painting's figures are the brief: costumes, colours and silhouettes are theirs. An art pass replaces the PNGs; names and frame counts are the contract.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_guides as mg  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = mg.ROOT
OUT = os.path.join(ROOT, "assets", "story", "doom_lounge", "textures")
SHEET = os.path.join(ROOT, "docs", "shots", "doom", "lounge", "guides_sheet.png")
W, H, CX, FEET = mg.W, mg.H, mg.CX, mg.FEET
hexc = mg.hexc

LOOK = {
    "dock": dict(skin="#6a4630", coat="#2c5a34", under="#20262c", trousers="#1c1f26", shoes="#121016", band="#d6b02a", beard=True, wide=1.28),
    "floor": dict(skin="#8a5a3c", hair="#1c1210", top="#c0287a", trousers="#b4bcd0", shoes="#3a2a30", gold="#e0b04a", wide=0.9),
}


def hand(c, pt, skin, open_=True, r=6):
    m, d = c.mask()
    d.ellipse([pt[0] - r, pt[1] - r - 1, pt[0] + r, pt[1] + r + 1], fill=255)
    if open_:
        d.rounded_rectangle([pt[0] - 5, pt[1] - r - 7, pt[0] + 5, pt[1] - r + 2], radius=3, fill=255)
    c.paint(m, skin)


def draw(who, state, i):
    g = LOOK[who]
    p = mg.poses(state, i)
    c = mg.Canvas()
    lean = p["lean"]
    wd = g["wide"]
    hipy, shy = 142, 80
    hx = mg.CX + lean * 0.4
    shx = mg.CX + lean
    stepdy = 4 if p["steps"] else 0
    if who == "floor":  # the long braids hang down her back (behind the body)
        m, d = c.mask()
        d.polygon([(shx - 20, 52), (shx + 20, 52), (shx + 26, 150), (shx + 12, 186), (shx - 12, 186), (shx - 26, 150)], fill=255)
        c.paint(m, g["hair"], seed=21)
    spread = 14 if who == "dock" else 16
    for sx in (-1, 1):  # legs: the Floor guide's trousers are baggy, the Dock guide's plain
        top = (hx + sx * 9, hipy)
        foot = (hx + sx * spread, FEET - 10 - (stepdy if sx == 1 else 0))
        rad = [15 * wd, 13 * wd, 9] if who == "dock" else [17, 17, 14]
        m = mg.limb([top, ((top[0] + foot[0]) / 2, (top[1] + foot[1]) / 2), foot], rad)
        c.paint(m, g["trousers"], sparkle=["#ffffff", "#8a90a8"] if who == "floor" else None, seed=3)
        m, d = c.mask()
        d.rounded_rectangle([foot[0] - 12 + sx * 3, foot[1] + 2, foot[0] + 12 + sx * 3, foot[1] + 11], radius=4, fill=255)
        c.paint(m, g["shoes"])
    # torso
    m, d = c.mask()
    sh = 25 * wd
    d.polygon([(shx - sh, shy - 2), (shx + sh, shy - 2), (hx + 21 * wd, hipy + 6), (hx - 21 * wd, hipy + 6)], fill=255)
    if who == "dock":
        c.paint(m, g["under"])
        m2, d2 = c.mask()
        d2.polygon([(shx - sh - 3, shy - 2), (shx + sh + 3, shy - 2), (hx + 36, 214), (hx - 36, 214)], fill=255)  # the long coat to the shins
        c.paint(m2, g["coat"], seed=5)
        m3, d3 = c.mask()
        d3.polygon([(shx - 5, shy), (shx + 5, shy), (hx + 8, 214), (hx - 8, 214)], fill=255)
        c.paint(m3, "#10201a")
    else:
        c.paint(m, g["top"], sparkle=["#ff9ad0", "#ffffff", "#7a1450"], seed=7)
        m2, d2 = c.mask()  # bare midriff
        d2.rectangle([hx - 18, 112, hx + 18, hipy + 2], fill=255)
        c.paint(m2, g["skin"])
        m3, d3 = c.mask()
        d3.rectangle([hx - 20, hipy - 4, hx + 20, hipy + 10], fill=255)  # the belt of chain
        c.paint(m3, g["gold"])
    shL, shR = (shx - 24 * wd, shy + 4), (shx + 24 * wd, shy + 4)
    sleeve = g["coat"] if who == "dock" else g["skin"]
    for sd, shp, ang in ((-1, shL, p["la"]), (1, shR, p["ra"])):
        pts = mg.arm_pts(sd, shp, ang[0], ang[1])
        if who == "floor" and sd == -1:  # a hand on the hip
            pts = (shL, (shL[0] - 14, shL[1] + 34), (shL[0] + 12, shL[1] + 54))
        m = mg.limb(list(pts), [10 * wd if who == "dock" else 7, 9 * wd if who == "dock" else 6, 6])
        c.paint(m, sleeve, seed=9 + sd)
        if who == "floor":  # gold bracelets at the wrist
            m, d = c.mask()
            wr = pts[2]
            d.ellipse([wr[0] - 6, wr[1] - 12, wr[0] + 6, wr[1] - 4], fill=255)
            c.paint(m, g["gold"])
        if who == "dock" and sd == 1:  # the yellow armband
            m, d = c.mask()
            e = pts[0]
            d.ellipse([e[0] + sd * 6 - 7, e[1] + 14, e[0] + sd * 6 + 7, e[1] + 26], fill=255)
            c.paint(m, g["band"])
        hand(c, pts[2], g["skin"], open_=(sd == 1 and state != "idle"), r=7 if who == "dock" else 6)
    m, d = c.mask()
    d.rectangle([hx - 7 * wd, 62, hx + 7 * wd, shy], fill=255)
    c.paint(m, g["skin"])
    hxx = hx + p["tilt"]
    m, d = c.mask()
    d.ellipse([hxx - 17 * (1.1 if who == "dock" else 1), 27, hxx + 17 * (1.1 if who == "dock" else 1), 70], fill=255)
    c.paint(m, g["skin"])
    m, d = c.mask()
    if who == "floor":  # braids pulled up over the head and one over the shoulder
        d.chord([hxx - 19, 22, hxx + 19, 62], 180, 360, fill=255)
        d.rectangle([hxx - 19, 42, hxx - 14, 70], fill=255)
        d.rectangle([hxx + 14, 42, hxx + 19, 66], fill=255)
        d.polygon([(hxx + 14, 56), (hxx + 22, 56), (hxx + 30, 128), (hxx + 24, 132)], fill=255)
        c.paint(m, g["hair"], seed=13)
    c.outline()
    img = c.rgb
    ex, ey = 7, 49
    for sx in (-1, 1):
        x0 = int(hxx + sx * ex)
        img[ey - 1:ey + 1, x0 - 2:x0 + 2] = (250, 250, 250)
        img[ey - 1:ey + 1, x0 - 1 + (1 if sx > 0 else 0):x0 + 1 + (1 if sx > 0 else 0)] = (30, 20, 24)
        img[ey - 5:ey - 4, x0 - 3:x0 + 3] = (40, 28, 24)
    img[ey + 5:ey + 9, int(hxx):int(hxx) + 2] = tuple(int(v * 0.8) for v in hexc(g["skin"]))
    sm = int(round(3 * p["smile"]))
    for k in range(-5, 6):
        yy = ey + 14 + int(round(sm * (k / 5.0) ** 2))
        img[yy:yy + 1, int(hxx) + k] = (150, 40, 52)
    if p["smile"] > 0.7:
        img[ey + 13:ey + 14, int(hxx) - 3:int(hxx) + 4] = (252, 248, 240)
    if who == "dock":  # a short beard
        img[ey + 11:ey + 19, int(hxx) - 8:int(hxx) + 9] = hexc("#161010")
        img[ey + 14:ey + 15, int(hxx) - 3:int(hxx) + 4] = (252, 248, 240) if p["smile"] > 0.7 else (150, 40, 52)
    if who == "floor":  # hoop earrings
        for sx in (-1, 1):
            xx = int(hxx + sx * 18)
            img[ey + 2:ey + 12, xx:xx + 1] = hexc(g["gold"])
            img[ey + 11:ey + 12, xx - 1:xx + 1] = hexc(g["gold"])
    return c.image()


LOUNGE_PAINTING = "doom_worlds/Mustard octagonal lounge of three routes-2.png"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_bar_guides as mbg  # noqa: E402
CROPS = {  # stage D polish (ruling 36): crops from the paintings (tools/doom/art/make_guides.py crop_guide)
    # the Dock guide stands full length in this painting's doorway (186 px, crown to feet)
    "dock": dict(src=LOUNGE_PAINTING, top=283, chin=0, cut=469, centre_x=808,
                 poly=[(808, 283), (800, 290), (780, 311), (772, 334), (771, 370), (772, 410), (774, 440), (786, 444), (788, 467), (832, 469), (851, 440), (849, 390), (847, 342),
                       (866, 337), (882, 335), (897, 327), (892, 319), (880, 317), (866, 321), (838, 311), (824, 300), (820, 285)],
                 hand=(866, 314, 899, 340, 850, 899)),
    # the Floor guide: her full-length picture in the Copper Bar painting (420 px), mirrored: here she stands on the right and turns to the room
    "floor": dict(mbg.CROPS["floor"], mirror=True, door_left=False),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    cols = sum(mg.FRAMES.values())
    sheet = Image.new("RGBA", (cols * W, 2 * H), (14, 12, 34, 255))
    for r, who in enumerate(LOOK):
        x = 0
        cropped = mg.crop_guide(CROPS[who]) if who in CROPS else None
        for state, n in mg.FRAMES.items():
            for i in range(n):
                im = cropped[(state, i)] if cropped else draw(who, state, i)
                im.save(os.path.join(OUT, "guide_%s_%s_%d.png" % (who, state, i)))
                sheet.alpha_composite(im, (x * W, r * H))
                x += 1
    sheet.convert("RGB").resize((sheet.width // 2, sheet.height // 2), Image.NEAREST).save(SHEET)
    print("wrote %d sprites to %s and the sheet %s" % (2 * cols, OUT, SHEET))


if __name__ == "__main__":
    sys.exit(main())
