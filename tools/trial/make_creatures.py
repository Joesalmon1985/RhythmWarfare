"""Draws the ten creatures of the Bassment as 64x64 pixel portraits, two frames each (assets/trial/art/<id>_0.png, the creature; <id>_1.png, struck).

    python tools/trial/make_creatures.py

Own work: shapes in a few flat colours, a one-pixel dark outline, a lit edge. The struck frame is the same drawing flashed toward white with wide eyes.
The ids are the "encounters" of content/trial/passages.json; add a function and an entry in CREATURES for a new one.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "trial" / "art"
S = 64
EYE = (255, 240, 120)


def canvas():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def lighten(c, k=0.35):
    return tuple(int(v + (255 - v) * k) for v in c[:3]) + (255,)


def darken(c, k=0.45):
    return tuple(int(v * (1 - k)) for v in c[:3]) + (255,)


def finish(im: Image.Image, hit: bool) -> Image.Image:
    a = np.asarray(im).copy()
    alpha = a[..., 3] > 0
    grown = alpha.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        grown |= np.roll(np.roll(alpha, dy, 0), dx, 1)
    out = np.zeros_like(a)
    out[grown] = (14, 10, 22, 255)
    out[alpha] = a[alpha]
    if hit:
        rgb = out[..., :3].astype(np.float32)
        rgb = rgb + (255 - rgb) * 0.45
        out[..., :3] = np.where(alpha[..., None], rgb, out[..., :3]).astype(np.uint8)
    return Image.fromarray(out)


def eyes(d, pts, hit, r=2, col=EYE):
    for x, y in pts:
        rr = r + (1 if hit else 0)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(255, 255, 255, 255) if hit else col + (255,))
        if not hit:
            d.point((x, y), fill=(30, 10, 10, 255))


def lampmoth(d, hit):
    wing = (214, 196, 160, 255)
    for sx in (-1, 1):
        d.polygon([(32, 28), (32 + sx * 28, 10), (32 + sx * 30, 34), (32 + sx * 14, 44)], fill=wing)
        d.polygon([(32, 28), (32 + sx * 28, 10), (32 + sx * 18, 26)], fill=lighten(wing, 0.3))
        d.ellipse((32 + sx * 18 - 5, 20, 32 + sx * 18 + 5, 30), fill=(120, 80, 60, 255))
        d.ellipse((32 + sx * 18 - 2, 23, 32 + sx * 18 + 2, 27), fill=(255, 220, 120, 255))
    d.ellipse((26, 22, 38, 52), fill=(110, 84, 62, 255))
    d.ellipse((27, 14, 37, 26), fill=(134, 104, 78, 255))
    d.line([(29, 15), (22, 5)], fill=(90, 70, 50, 255), width=1)
    d.line([(35, 15), (42, 5)], fill=(90, 70, 50, 255), width=1)
    eyes(d, [(30, 19), (34, 19)], hit, 1)


def cable_eel(d, hit):
    body = (62, 112, 84, 255)
    pts = [(int(4 + i * 3.5), 40 + int(14 * math.sin(i * 0.55))) for i in range(15)]
    d.line(pts, fill=body, width=9)
    d.line([(x, y - 3) for x, y in pts], fill=lighten(body, 0.4), width=2)
    for i in range(1, 14, 2):  # copper wire wrapped round it
        x, y = pts[i]
        d.line([(x - 2, y - 4), (x + 2, y + 4)], fill=(224, 140, 60, 255), width=1)
    hx, hy = pts[-1]
    d.ellipse((hx - 5, hy - 6, hx + 5, hy + 4), fill=body)
    eyes(d, [(hx + 1, hy - 2)], hit, 2)
    for i in (3, 7, 11):
        x, y = pts[i]
        d.line([(x, y - 5), (x + 3, y - 12), (x - 1, y - 16)], fill=(150, 225, 255, 255), width=1)


def barrel_knight(d, hit):
    wood = (118, 74, 42, 255)
    d.rectangle((20, 34, 44, 60), fill=wood)
    d.ellipse((20, 30, 44, 38), fill=lighten(wood, 0.25))
    for y in (40, 52):
        d.line([(20, y), (44, y)], fill=(48, 38, 34, 255), width=2)
    d.rectangle((26, 36, 38, 54), fill=(200, 196, 180, 255))  # the apron
    d.ellipse((24, 10, 40, 30), fill=(224, 220, 204, 255))  # the skull
    d.rectangle((27, 26, 37, 32), fill=(214, 210, 194, 255))
    for x in (29, 32, 35):
        d.line([(x, 27), (x, 32)], fill=(40, 30, 30, 255))
    eyes(d, [(29, 19), (35, 19)], hit, 2, (255, 120, 80))
    d.line([(50, 56), (50, 8)], fill=(150, 110, 70, 255), width=2)  # the mop lance
    d.polygon([(46, 6), (54, 6), (52, 16), (48, 16)], fill=(180, 180, 170, 255))
    d.line([(44, 40), (50, 36)], fill=(214, 208, 192, 255), width=3)


def mildew_mother(d, hit):
    fur = (96, 108, 92, 255)
    d.ellipse((6, 18, 58, 62), fill=fur)
    d.ellipse((14, 10, 50, 40), fill=lighten(fur, 0.15))
    for x, y, r in ((16, 30, 5), (44, 24, 6), (30, 44, 7), (50, 46, 4), (22, 52, 4)):
        d.ellipse((x - r, y - r, x + r, y + r), fill=(110, 200, 130, 255))
    for x, y in ((24, 22), (32, 18), (40, 22), (28, 30), (36, 30)):
        eyes(d, [(x, y)], hit, 1)
    d.arc((22, 30, 42, 46), 20, 160, fill=(40, 30, 40, 255), width=2)
    for x, y in ((12, 12), (50, 8), (56, 20), (6, 22), (30, 4)):
        d.point((x, y), fill=(190, 255, 210, 255))


def mirror_twin(d, hit):
    glass = (150, 180, 224, 255)
    d.ellipse((24, 6, 40, 24), fill=glass)
    d.polygon([(18, 26), (46, 26), (50, 62), (14, 62)], fill=lighten(glass, 0.1))
    d.polygon([(14, 28), (20, 28), (16, 50), (10, 50)], fill=glass)
    d.polygon([(44, 28), (50, 28), (54, 50), (48, 50)], fill=glass)
    d.line([(32, 6), (26, 22), (34, 34), (24, 62)], fill=(40, 50, 90, 255), width=1)  # the crack
    d.line([(46, 30), (38, 40)], fill=(40, 50, 90, 255), width=1)
    d.line([(24, 8), (22, 20)], fill=(255, 255, 255, 255), width=1)
    eyes(d, [(28, 15), (36, 15)], hit, 2, (255, 255, 255))
    d.rectangle((26, 20, 38, 21), fill=(255, 255, 255, 255))  # the grin


def bouncer(d, hit):
    skin = (96, 130, 84, 255)
    d.polygon([(10, 62), (14, 28), (50, 28), (54, 62)], fill=(54, 58, 66, 255))
    d.polygon([(18, 30), (46, 30), (48, 62), (16, 62)], fill=(228, 210, 60, 255))  # the high-vis vest
    d.rectangle((18, 44, 46, 49), fill=(235, 235, 230, 255))
    d.ellipse((22, 6, 42, 28), fill=skin)
    d.rectangle((24, 22, 40, 26), fill=darken(skin, 0.2))
    d.polygon([(26, 24), (24, 30), (28, 26)], fill=(230, 226, 200, 255))  # a tusk
    d.polygon([(38, 24), (40, 30), (36, 26)], fill=(230, 226, 200, 255))
    eyes(d, [(28, 14), (36, 14)], hit, 2, (255, 200, 60))
    d.rectangle((20, 8, 44, 12), fill=darken(skin, 0.3))  # heavy brow
    d.rectangle((50, 36, 60, 54), fill=(190, 150, 90, 255))  # the clipboard
    d.rectangle((52, 40, 58, 42), fill=(40, 40, 40, 255))


def rat_king(d, hit):
    fur = (112, 94, 84, 255)
    d.ellipse((8, 26, 56, 62), fill=fur)
    for x, y in ((14, 28), (24, 20), (34, 16), (44, 20), (52, 28), (30, 30)):
        d.ellipse((x - 6, y - 5, x + 6, y + 5), fill=lighten(fur, 0.12))
        d.polygon([(x - 5, y - 3), (x - 6, y - 9), (x - 1, y - 5)], fill=(190, 140, 140, 255))
        d.polygon([(x + 5, y - 3), (x + 6, y - 9), (x + 1, y - 5)], fill=(190, 140, 140, 255))
        eyes(d, [(x - 2, y - 1), (x + 2, y - 1)], hit, 1, (255, 70, 60))
        d.point((x, y + 3), fill=(240, 180, 180, 255))
    for i in range(5):  # the crown of bottle tops
        x = 20 + i * 6
        d.polygon([(x, 12), (x + 3, 4), (x + 6, 12)], fill=(214, 184, 70, 255))
    d.line([(8, 50), (2, 44), (0, 38)], fill=(190, 140, 140, 255), width=1)


def furnace_imp(d, hit):
    red = (200, 52, 44, 255)
    d.ellipse((20, 24, 44, 56), fill=red)
    d.ellipse((22, 8, 42, 30), fill=lighten(red, 0.1))
    d.polygon([(22, 12), (18, 2), (28, 10)], fill=(240, 220, 200, 255))  # horns
    d.polygon([(42, 12), (46, 2), (36, 10)], fill=(240, 220, 200, 255))
    d.rectangle((24, 2, 40, 10), fill=(244, 244, 240, 255))  # the chef's hat
    d.ellipse((22, -2, 42, 8), fill=(250, 250, 248, 255))
    eyes(d, [(28, 18), (36, 18)], hit, 2, (255, 240, 120))
    d.arc((26, 20, 38, 30), 10, 170, fill=(40, 10, 10, 255), width=2)
    d.polygon([(32, 56), (28, 62), (36, 62)], fill=red)
    for x, y in ((12, 30), (52, 26), (8, 44)):  # knives in the air
        d.polygon([(x, y), (x + 3, y + 10), (x - 3, y + 10)], fill=(200, 210, 224, 255))
    d.line([(20, 36), (12, 44)], fill=red, width=3)
    d.line([(44, 36), (52, 30)], fill=red, width=3)


def gargoyle(d, hit):
    stone = (120, 122, 134, 255)
    for sx in (-1, 1):
        d.polygon([(32 + sx * 6, 26), (32 + sx * 30, 8), (32 + sx * 26, 34), (32 + sx * 10, 42)], fill=darken(stone, 0.15))
    d.polygon([(18, 62), (22, 30), (42, 30), (46, 62)], fill=stone)
    d.ellipse((22, 6, 42, 32), fill=lighten(stone, 0.1))
    d.polygon([(23, 10), (18, 0), (28, 8)], fill=stone)
    d.polygon([(41, 10), (46, 0), (36, 8)], fill=stone)
    eyes(d, [(28, 16), (36, 16)], hit, 2, (255, 120, 80))
    d.rectangle((30, 24, 34, 40), fill=lighten(stone, 0.25))  # the finger to its lips
    d.rectangle((26, 24, 38, 26), fill=darken(stone, 0.3))
    d.line([(24, 48), (40, 48)], fill=darken(stone, 0.3), width=1)


def echo(d, hit):
    ghost = (176, 204, 255, 200)
    d.polygon([(32, 22), (46, 30), (44, 52), (54, 62), (32, 58), (10, 62), (20, 52), (18, 30)], fill=ghost)
    d.ellipse((22, 4, 42, 28), fill=(200, 222, 255, 220))
    for k in range(3):
        d.arc((10 - k * 3, 36 - k * 3, 54 + k * 3, 60 + k * 3), 0, 360, fill=(150, 190, 255, 120 - k * 30), width=1)
    eyes(d, [(28, 14), (36, 14)], hit, 2, (255, 255, 255))
    d.rectangle((28, 20, 36, 21), fill=(60, 80, 140, 255))


CREATURES = {"lampmoth": lampmoth, "cable_eel": cable_eel, "barrel_knight": barrel_knight, "mildew_mother": mildew_mother, "mirror_twin": mirror_twin, "bouncer": bouncer,
             "rat_king": rat_king, "furnace_imp": furnace_imp, "gargoyle": gargoyle, "echo": echo}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in CREATURES.items():
        for hit in (False, True):
            im, d = canvas()
            fn(d, hit)
            finish(im, hit).save(OUT / f"{name}_{int(hit)}.png")
        print("wrote", f"assets/trial/art/{name}_0.png and _1.png")


if __name__ == "__main__":
    main()
