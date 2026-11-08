"""The Copper Bar's three guides (docs/doom/scenes/bar.md): `booth` (teal hair, headphones, orange jacket; route ahead), `floor` (braids, hoop earrings, magenta sequin top, silver
sequin trousers: the owner's sprite standard; route left) and `chill` (mustard cardigan, glasses, curly hair; route right).

    python -I tools/doom/art/make_bar_guides.py       writes assets/story/doom_bar/textures/guide_<who>_<state>_<n>.png and docs/shots/doom/bar/guides_sheet.png

PLACEHOLDERS: 160 x 256 sheets (about 230 px for a 1.8 m figure, the standard's size and layout) drawn by the Warehouse guides' code (tools/doom/art/make_guides.py: capsule limbs,
dithered light, a face), with sequins and braids added; below the painterly finish of art/reference/standard/guide_floor_sprite_standard.png. Frames per state as the Warehouse's:
idle 1, available 5 (the beckon loop), selected 2, committed 2.
"""
from __future__ import annotations

import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_guides as mg  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "assets", "story", "doom_bar", "textures")
SHEET = os.path.join(ROOT, "docs", "shots", "doom", "bar", "guides_sheet.png")
W, H, CX, FEET = mg.W, mg.H, mg.CX, mg.FEET
hexc = mg.hexc

GUIDES = {
    "booth": dict(skin="#e8c0a0", hair="#27b8b0", top="#1c1f2e", jacket="#e07a20", trousers="#1c1f2e", shoes="#2a1a14", accent="#27b8b0"),
    "floor": dict(skin="#7a4a2c", hair="#1a0f0c", top="#c0188e", trousers="#8a94b4", shoes="#c0c8e0", accent="#e0b04a"),
    "chill": dict(skin="#b07848", hair="#1c1410", top="#efe6d0", jacket="#d19a2a", trousers="#2a2420", shoes="#3a2416", accent="#2a8f9a"),
}


def draw_guide(who, state, i):
    g = GUIDES[who]
    p = mg.poses(state, i)
    c = mg.Canvas()
    lean = p["lean"]
    stepdy = 4 if p["steps"] else 0
    hipy, shy = 142, 80
    hx = CX + lean * 0.4
    shx = CX + lean
    if who == "floor":  # braids behind the shoulders, down to the hips
        for k, dx in enumerate((-22, -13, 13, 22)):
            m = mg.limb([(shx + dx * 0.9, 50), (shx + dx * 1.15 + (1 if i % 2 else -1) * (k % 2), 100), (shx + dx * 1.25, 150)], [6, 6, 4])
            c.paint(m, g["hair"], seed=20 + k)
    spread = 14 + (2 if p["steps"] else 0)
    for sx_ in (-1, 1):
        top = (hx + sx_ * 9, hipy)
        lift = stepdy if sx_ == 1 else 0
        foot = (hx + sx_ * spread, FEET - 10 - lift)
        wide = 17 if who == "floor" else 13  # the flared silver trousers
        m = mg.limb([top, ((top[0] + foot[0]) / 2, (top[1] + foot[1]) / 2), foot], [13, wide - 2, wide - 8 if who == "floor" else 8])
        c.paint(m, g["trousers"], sparkle=["#ffffff", "#c8d0ec", "#6a74a0"] if who == "floor" else None, seed=1 + sx_)
        m, d = c.mask()
        d.rounded_rectangle([foot[0] - 11 + sx_ * 3, foot[1] + 2, foot[0] + 11 + sx_ * 3, foot[1] + 11 + lift], radius=4, fill=255)
        c.paint(m, g["shoes"])
    m, d = c.mask()
    if who == "floor":  # a short halter: the top half of the torso, a bare midriff, a belt of chains
        d.polygon([(shx - 22, shy - 2), (shx + 22, shy - 2), (hx + 17, shy + 30), (hx - 17, shy + 30)], fill=255)
        mw, dw = c.mask()
        dw.polygon([(shx - 21, shy + 28), (shx + 21, shy + 28), (hx + 20, hipy + 8), (hx - 20, hipy + 8)], fill=255)
        c.paint(mw, g["skin"])
        c.paint(m, g["top"], sparkle=["#ff5ac8", "#9a1070", "#ffd0f0"], seed=5)
        mb, db = c.mask()
        db.rectangle([hx - 21, hipy - 2, hx + 21, hipy + 6], fill=255)
        c.paint(mb, "#c8a040")
    else:
        d.polygon([(shx - 25, shy - 2), (shx + 25, shy - 2), (hx + 21, hipy + 6), (hx - 21, hipy + 6)], fill=255)
        c.paint(m, g["top"])
        mj, dj = c.mask()
        dj.polygon([(shx - 27, shy - 2), (shx - 7, shy - 2), (hx - 5, hipy + 8), (hx - 22, hipy + 8)], fill=255)
        dj.polygon([(shx + 27, shy - 2), (shx + 7, shy - 2), (hx + 5, hipy + 8), (hx + 22, hipy + 8)], fill=255)
        c.paint(mj, g["jacket"], seed=3)
        if who == "booth":  # lapels turned back, a zip line, the black top's neckline (the painting's orange bomber over black)
            ml, dl = c.mask()
            dl.polygon([(shx - 8, shy - 2), (shx - 16, shy - 2), (shx - 9, shy + 22)], fill=255)
            dl.polygon([(shx + 8, shy - 2), (shx + 16, shy - 2), (shx + 9, shy + 22)], fill=255)
            c.paint(ml, "#f6b060")
            c.rgb[shy + 4:hipy + 6, int(hx) - 7] = hexc("#c8c8d0")
            c.rgb[shy + 4:hipy + 6, int(hx) + 6] = hexc("#c8c8d0")
    sleeve = g["skin"] if who == "floor" else g["jacket"]
    shL, shR = (shx - 24, shy + 4), (shx + 24, shy + 4)
    for sd, sh, ang in ((-1, shL, p["la"]), (1, shR, p["ra"])):
        pts = mg.arm_pts(sd, sh, ang[0], ang[1])
        if who == "floor" and sd == -1:  # a hand on the hip
            pts = (shL, (shL[0] - 14, shL[1] + 30), (shL[0] + 8, shL[1] + 56))
        m = mg.limb(list(pts), [9, 8, 6])
        c.paint(m, sleeve, seed=7 + sd)
        hand = pts[2]
        m, d = c.mask()
        r = 7 if (sd == 1 and state != "idle") else 6
        d.ellipse([hand[0] - r, hand[1] - r - 1, hand[0] + r, hand[1] + r + 1], fill=255)
        if sd == 1 and state != "idle":
            d.rounded_rectangle([hand[0] - 5, hand[1] - r - 7, hand[0] + 5, hand[1] - r + 2], radius=3, fill=255)
        c.paint(m, g["skin"])
        if who == "floor":  # gold bangles at the elbow
            m, d = c.mask()
            d.rectangle([pts[1][0] - 7, pts[1][1] + 6, pts[1][0] + 7, pts[1][1] + 12], fill=255)
            c.paint(m, "#e0b04a")
    m, d = c.mask()
    d.rectangle([hx - 6, 62, hx + 6, shy], fill=255)
    c.paint(m, g["skin"])
    hxx = hx + p["tilt"]
    m, d = c.mask()
    d.ellipse([hxx - 17, 27, hxx + 17, 70], fill=255)
    c.paint(m, g["skin"])
    m, d = c.mask()
    if who == "chill":  # curly hair, a cap of curls
        for k in range(9):
            a = math.radians(200 + k * 17)
            d.ellipse([hxx + math.cos(a) * 17 - 6, 47 + math.sin(a) * 21 - 6, hxx + math.cos(a) * 17 + 6, 47 + math.sin(a) * 21 + 6], fill=255)
        d.ellipse([hxx - 17, 26, hxx + 17, 46], fill=255)
    elif who == "floor":  # the crown braided back
        d.chord([hxx - 19, 22, hxx + 19, 62], 180, 360, fill=255)
        d.rectangle([hxx - 19, 40, hxx - 15, 62], fill=255)
        d.rectangle([hxx + 15, 40, hxx + 19, 62], fill=255)
    else:  # booth: a teal bob to the jaw with a side fringe (stage D: the painting's cut, not a cap)
        d.chord([hxx - 20, 22, hxx + 20, 62], 180, 360, fill=255)
        d.polygon([(hxx - 20, 42), (hxx - 21, 64), (hxx - 14, 66), (hxx - 13, 44)], fill=255)
        d.polygon([(hxx + 13, 44), (hxx + 14, 66), (hxx + 21, 64), (hxx + 20, 42)], fill=255)
        d.polygon([(hxx - 18, 42), (hxx - 6, 34), (hxx + 20, 40), (hxx + 16, 48), (hxx - 2, 44)], fill=255)
    c.paint(m, g["hair"], seed=13, sparkle=["#7ff0e0", "#138078"] if who == "booth" else None)
    if who == "booth":  # headphones: a band over the head, cups at the ears
        m, d = c.mask()
        d.arc([hxx - 21, 22, hxx + 21, 66], 190, 350, fill=255, width=4)
        d.rounded_rectangle([hxx - 24, 40, hxx - 15, 60], radius=3, fill=255)
        d.rounded_rectangle([hxx + 15, 40, hxx + 24, 60], radius=3, fill=255)
        c.paint(m, "#1a1c24")
    if who == "floor":  # hoop earrings
        m, d = c.mask()
        for sx_ in (-1, 1):
            d.ellipse([hxx + sx_ * 18 - 6, 52, hxx + sx_ * 18 + 6, 68], outline=255, width=2)
        c.paint(m, "#e0b04a")
    c.outline()
    ex, ey = 7, 49
    img = c.rgb
    brow = hexc(g["hair"]) if who != "booth" else (30, 120, 120)
    for sx_ in (-1, 1):
        x0 = int(hxx + sx_ * ex)
        img[ey - 1:ey + 1, x0 - 2:x0 + 2] = (250, 250, 250)
        img[ey - 1:ey + 1, x0 - 1 + (1 if sx_ > 0 else 0):x0 + 1 + (1 if sx_ > 0 else 0)] = (30, 20, 24)
        img[ey - 5:ey - 4, x0 - 3:x0 + 3] = brow
    img[ey + 5:ey + 9, int(hxx):int(hxx) + 2] = tuple(int(v * 0.8) for v in hexc(g["skin"]))
    sm = int(round(3 * p["smile"]))
    lip = (190, 40, 100) if who == "floor" else (150, 40, 52)
    for k in range(-5, 6):
        yy = ey + 14 + (int(round(sm * (1 - (k / 5.0) ** 2))) if who == "booth" else int(round(sm * (k / 5.0) ** 2)))  # (booth, stage D: corners up, a smile)
        img[yy:yy + 1, int(hxx) + k] = lip
    if p["smile"] > 0.7:
        img[ey + 13:ey + 14, int(hxx) - 3:int(hxx) + 4] = (252, 248, 240)
    if who == "chill":
        for sx_ in (-1, 1):
            x0 = int(hxx + sx_ * ex)
            img[ey - 4:ey - 3, x0 - 4:x0 + 5] = (40, 30, 30)
            img[ey + 3:ey + 4, x0 - 4:x0 + 5] = (40, 30, 30)
            img[ey - 4:ey + 4, x0 - 4:x0 - 3] = (40, 30, 30)
            img[ey - 4:ey + 4, x0 + 4:x0 + 5] = (40, 30, 30)
    return c.image()


BAR_PAINTING = "doom_worlds/Copper Basement Bar, Three Hidden Routes-3.png"
CROPS = {  # stage D polish (ruling 36): guides the paintings show 180 px tall or more are cut from them (round 2: the Booth guide too) (tools/doom/art/make_guides.py crop_guide)
    # the Floor guide stands full length in this painting (420 px, crown to feet): her own picture, leaning on nothing (the post she leans on is left out)
    "floor": dict(src=BAR_PAINTING, top=238, chin=0, cut=660, centre_x=200, door_left=True,
                  poly=[(169, 239), (136, 270), (115, 320), (107, 387), (111, 437), (107, 462), (140, 470), (169, 470), (177, 537), (182, 603), (177, 655), (223, 659), (244, 645),
                        (257, 603), (265, 537), (244, 470), (227, 412), (223, 382), (236, 345), (265, 345), (298, 341), (313, 330), (302, 316), (282, 324), (240, 320), (215, 307),
                        (207, 287), (202, 257), (190, 239)],
                  hand=(278, 310, 316, 346, 255, 316)),
    # round 2: the Booth guide is cut from this painting too (her head is 80 px in it; crown to the desk 200 px): her picture behind the booth desk with its mixer, cut at the
    # desk's front edge; under it the desk front runs down to the floor (make_guides.parapet_down: the painting's own wood), as the painting's booth window frames her
    "booth": dict(src=BAR_PAINTING, top=219, chin=262, cut=320, centre_x=995,
                  poly=[(980, 224), (995, 218), (1012, 223), (1021, 240), (1019, 256), (1028, 268), (1042, 278), (1050, 298), (1060, 303), (1060, 320), (920, 320), (920, 302),
                        (950, 299), (955, 292), (940, 291), (921, 289), (918, 280), (935, 275), (952, 281), (960, 276), (975, 268), (972, 256), (971, 238)],
                  hand=(916, 270, 962, 296, 962, 916),
                  parapet=dict(span=(920, 1060), band_y=(320, 331))),
    # the Chill-out guide (mustard cardigan, glasses, cushion) is the same man as the Warehouse's lounge guide: the same crop (Midnight dance hall painting, 480 px), turning right
    "chill": dict(mg.CROPS["lounge"], door_left=False),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    cols = sum(mg.FRAMES.values())
    sheet = Image.new("RGBA", (cols * W, 3 * H), (14, 12, 34, 255))
    for r, who in enumerate(GUIDES):
        x = 0
        cropped = mg.crop_guide(CROPS[who]) if who in CROPS else None
        for state, n in mg.FRAMES.items():
            for i in range(n):
                im = cropped[(state, i)] if cropped else draw_guide(who, state, i)
                im.save(os.path.join(OUT, "guide_%s_%s_%d.png" % (who, state, i)))
                sheet.alpha_composite(im, (x * W, r * H))
                x += 1
    sheet.convert("RGB").resize((sheet.width // 2, sheet.height // 2), Image.NEAREST).save(SHEET)
    print("wrote %d sprites to %s and the sheet %s" % (3 * cols, OUT, SHEET))


if __name__ == "__main__":
    sys.exit(main())
