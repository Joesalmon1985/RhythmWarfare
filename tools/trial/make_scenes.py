"""Draws the six fixed scene illustrations of the Deathtrap opening into assets/trial/scenes/ (own work: procedural pixel art, no copied pictures).

    python tools/trial/make_scenes.py

Each scene is drawn at 320x180 with a fixed seed and scaled 4x with nearest-neighbour, so the pixels stay crisp. They are placeholders for
proper paintings: replace a file with a 1280x720 PNG of the same name and nothing else changes.
"""
from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "trial" / "scenes"
W, H = 320, 180

STONE = [(24, 22, 40), (34, 31, 54), (46, 42, 70), (60, 55, 88)]
CRYSTAL = (110, 235, 255)
CRYSTAL_D = (40, 120, 170)
GOLD = (255, 205, 90)


def noise(img: Image.Image, rng: random.Random, amount: int = 10) -> None:
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = px[x, y]
            d = rng.randint(-amount, amount)
            px[x, y] = (max(0, min(255, r + d)), max(0, min(255, g + d)), max(0, min(255, b + d)))


def tunnel(d: ImageDraw.ImageDraw, vp=(160, 84), far=(112, 60, 208, 108), tint=0) -> None:
    """A one-point-perspective passage: ceiling, floor and walls converging on the far rectangle."""
    fx0, fy0, fx1, fy1 = far
    d.rectangle((0, 0, W, H), fill=STONE[0])
    d.polygon([(0, 0), (W, 0), (fx1, fy0), (fx0, fy0)], fill=STONE[1])  # ceiling
    d.polygon([(0, H), (W, H), (fx1, fy1), (fx0, fy1)], fill=STONE[2])  # floor
    d.polygon([(0, 0), (fx0, fy0), (fx0, fy1), (0, H)], fill=STONE[1])  # left wall
    d.polygon([(W, 0), (fx1, fy0), (fx1, fy1), (W, H)], fill=STONE[1])  # right wall
    d.rectangle(far, fill=(8, 8, 18))
    for k in range(1, 7):  # ribs of the vault
        t = k / 7.0
        x0 = int(fx0 * (1 - t) ** 0 * 0 + (fx0 + (0 - fx0) * (1 - t) ** 1.0 * 0))
        d.line([(int(fx0 * (1 - t)), int(fy0 * (1 - t))), (int(W * 0 + fx0 * (1 - t)), int(fy1 + (H - fy1) * t))], fill=STONE[0])


def crystals(d: ImageDraw.ImageDraw, rng: random.Random, n: int = 26, glow: tuple = CRYSTAL) -> None:
    for _ in range(n):
        side = rng.choice([0, 1])
        y = rng.randint(6, 150)
        x = rng.randint(2, 84) if side == 0 else rng.randint(W - 84, W - 3)
        h = rng.randint(5, 16)
        d.polygon([(x, y), (x + 3, y + h // 2), (x, y + h), (x - 3, y + h // 2)], fill=CRYSTAL_D)
        d.polygon([(x, y), (x + 2, y + h // 2), (x, y + h)], fill=glow)
        d.point((x - 1, y + 2), fill=(255, 255, 255))


def footprints(d: ImageDraw.ImageDraw, pts: list, color=(15, 14, 26)) -> None:
    for i, (x, y) in enumerate(pts):
        o = 2 if i % 2 else -2
        d.ellipse((x + o - 2, y - 3, x + o + 2, y + 3), fill=color)


def box(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, seal: bool = False, open_: bool = False) -> None:
    d.rectangle((x, y, x + w, y + h), fill=(92, 58, 34))
    d.rectangle((x, y, x + w, y + 2), fill=(130, 88, 52))
    d.line([(x, y + h // 2), (x + w, y + h // 2)], fill=(60, 36, 20))
    if open_:
        d.polygon([(x - 1, y), (x + w + 1, y), (x + w - 3, y - 9), (x + 3, y - 9)], fill=(70, 44, 26))
    if seal:
        d.ellipse((x + w // 2 - 3, y + 2, x + w // 2 + 3, y + 8), fill=GOLD)


def glow_floor(img: Image.Image, cx: int, cy: int, r: int, col=CRYSTAL, strength: float = 0.35) -> None:
    px = img.load()
    for y in range(max(0, cy - r), min(H, cy + r)):
        for x in range(max(0, cx - r * 2), min(W, cx + r * 2)):
            dd = (((x - cx) / 2.0) ** 2 + (y - cy) ** 2) ** 0.5 / r
            if dd < 1.0:
                k = (1.0 - dd) * strength
                p = px[x, y]
                px[x, y] = tuple(int(p[i] + (col[i] - p[i]) * k) for i in range(3))


def vignette(img: Image.Image) -> None:
    px = img.load()
    for y in range(H):
        for x in range(W):
            dd = (((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) ** 0.5
            k = max(0.0, min(0.55, (dd - 0.65) * 0.9))
            p = px[x, y]
            px[x, y] = (int(p[0] * (1 - k)), int(p[1] * (1 - k)), int(p[2] * (1 - k)))


def scene_entrance(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    tunnel(d)
    crystals(d, rng, 34)
    d.rectangle((136, 70, 184, 96), fill=(235, 245, 255))  # daylight is never here: the far end glows crystal-white
    d.rectangle((140, 74, 180, 92), fill=(190, 240, 255))
    d.polygon([(204, 120), (300, 120), (316, 168), (190, 168)], fill=(78, 74, 104))  # the stone table, right foreground
    d.rectangle((190, 168, 316, 176), fill=(46, 42, 70))
    for i, bx in enumerate((206, 226, 246, 266, 286)):
        box(d, bx, 112, 14, 9, open_=True)  # five taken
    box(d, 236, 134, 24, 14, seal=True)  # the sixth, with the contestant's name
    d.rectangle((242, 128, 254, 133), fill=(235, 225, 190))
    noise(img, rng, 7)
    glow_floor(img, 160, 120, 40)
    vignette(img)
    return img


def scene_box(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), STONE[0])
    d = ImageDraw.Draw(img)
    d.rectangle((0, 110, W, H), fill=STONE[2])
    d.rectangle((0, 100, W, 110), fill=STONE[3])
    crystals(d, rng, 20)
    box(d, 104, 84, 112, 50, seal=True, open_=True)
    d.rectangle((108, 90, 212, 100), fill=(28, 20, 16))
    for cx, cy in ((140, 94), (156, 96), (172, 93)):  # two gold pieces and one for luck of the light
        d.ellipse((cx - 5, cy - 4, cx + 5, cy + 4), fill=GOLD)
        d.ellipse((cx - 3, cy - 2, cx + 3, cy + 1), fill=(255, 235, 150))
    d.polygon([(190, 88), (226, 80), (232, 104), (196, 112)], fill=(235, 225, 190))  # the note
    for k in range(4):
        d.line([(198, 90 + k * 4), (222, 85 + k * 4)], fill=(120, 100, 70))
    noise(img, rng, 7)
    glow_floor(img, 160, 100, 56, GOLD, 0.30)
    vignette(img)
    return img


def scene_fork(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, H), fill=STONE[0])
    d.rectangle((0, 0, W, 70), fill=STONE[1])
    d.rectangle((0, 70, W, 84), fill=STONE[2])  # the far wall at the junction
    d.rectangle((0, 84, W, H), fill=STONE[2])
    d.rectangle((0, 70, 60, 112), fill=(8, 8, 18))  # the west way, dark
    d.rectangle((260, 70, W, 112), fill=(8, 8, 18))  # the east way
    d.polygon([(110, 64), (210, 64), (230, 84), (90, 84)], fill=STONE[3])
    # the painted white arrow pointing west, and the charcoal scrawl below
    d.polygon([(182, 46), (182, 36), (150, 36), (150, 28), (118, 41), (150, 54), (150, 46)], fill=(245, 245, 240))
    d.line([(126, 62), (140, 60), (154, 63), (166, 60)], fill=(18, 16, 22), width=2)
    footprints(d, [(180, 150), (170, 140), (150, 132), (130, 126), (110, 122), (92, 118), (72, 114)])
    footprints(d, [(190, 156), (176, 146), (156, 138), (136, 131), (118, 128), (98, 124), (80, 120)])
    footprints(d, [(200, 150), (222, 138), (244, 130), (262, 124), (280, 118)])  # one set, smaller, east
    crystals(d, rng, 18)
    noise(img, rng, 7)
    glow_floor(img, 160, 120, 46)
    vignette(img)
    return img


def scene_east(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    tunnel(d, far=(120, 64, 200, 104))
    for _ in range(40):  # the soft obstruction: a grey-pink curtain of strands across the far end
        x = rng.randint(118, 202)
        d.line([(x, 62), (x + rng.randint(-5, 5), 106)], fill=(150, 120, 140))
    d.rectangle((120, 64, 200, 104), outline=(90, 70, 90))
    crystals(d, rng, 10)
    box(d, 70, 134, 22, 12, open_=True)  # an open box with its seal broken
    footprints(d, [(150, 150), (152, 138), (154, 128), (156, 120), (157, 112)])
    for k in range(5):  # a hum in the dark: a few bright specks
        d.point((rng.randint(130, 190), rng.randint(70, 100)), fill=(255, 240, 160))
    noise(img, rng, 7)
    glow_floor(img, 160, 126, 34, (190, 150, 190), 0.25)
    vignette(img)
    return img


def scene_gallery(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, H), fill=STONE[0])
    d.polygon([(0, 0), (W, 0), (W, 60), (0, 60)], fill=STONE[1])
    d.polygon([(0, 60), (W, 60), (W, H), (0, H)], fill=STONE[2])
    d.rectangle((136, 20, 184, 66), fill=(8, 8, 18))  # the way north
    d.rectangle((0, 56, 40, 110), fill=(8, 8, 18))  # the way west
    footprints(d, [(190, 160), (180, 148), (160, 138), (140, 130), (118, 122), (96, 114), (64, 104)])
    footprints(d, [(200, 164), (188, 152), (168, 142), (148, 134), (126, 126), (104, 118), (72, 108)])
    footprints(d, [(196, 156), (186, 130), (176, 108), (166, 90), (160, 76), (158, 64)])
    crystals(d, rng, 26, (190, 160, 255))
    noise(img, rng, 7)
    glow_floor(img, 170, 130, 44, (190, 160, 255), 0.25)
    vignette(img)
    return img


def scene_opening(rng: random.Random) -> Image.Image:
    img = scene_east(random.Random(5))
    d = ImageDraw.Draw(img)
    d.polygon([(120, 62), (160, 62), (140, 106), (120, 106)], fill=(70, 52, 70))  # the curtain drawn aside
    d.polygon([(160, 62), (200, 62), (200, 106), (180, 106)], fill=(70, 52, 70))
    d.polygon([(140, 62), (180, 62), (170, 106), (150, 106)], fill=(235, 245, 255))  # light beyond
    glow_floor(img, 160, 112, 30, (235, 245, 255), 0.45)
    vignette(img)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    scenes = {"entrance": scene_entrance, "box": scene_box, "fork": scene_fork, "east": scene_east, "gallery": scene_gallery, "opening": scene_opening}
    for name, fn in scenes.items():
        img = fn(random.Random(hash(name) & 0xFFFF if False else sum(map(ord, name))))
        img.resize((W * 4, H * 4), Image.NEAREST).save(OUT / f"{name}.png", optimize=True)
        print("wrote", f"assets/trial/scenes/{name}.png")


if __name__ == "__main__":
    main()
