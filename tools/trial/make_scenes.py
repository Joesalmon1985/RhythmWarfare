"""Draws the zone pictures of the Bassment (assets/trial/scenes/*.png, 1280x720): one per zone, plus death and victory. Own work, procedural pixel art.

    python tools/trial/make_scenes.py            # all of them
    python tools/trial/make_scenes.py hall pit   # some

Every picture is drawn at 320x180 and scaled 4x with nearest-neighbour so the pixels stay crisp. The room is a one-point-perspective box whose stone (bricks on the
walls, flagstones on the floor and ceiling) is textured per pixel with the right foreshortening; props are drawn into the albedo; then the light is computed from
the lamps of the zone (torches, crystals, a furnace) with a small ordered dither so it steps in pixel-art bands; then glowing things (flames, crystal edges, eyes) are
laid on top. Replace a file with a 1280x720 PNG of the same name and nothing else changes: the game only needs the files named in content/trial/passages.json.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "trial" / "scenes"
W, H = 320, 180
VY = 84  # horizon row
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) / 16.0


def hash2(a: np.ndarray, b: np.ndarray, seed: int = 0) -> np.ndarray:
    v = np.sin(a * 127.1 + b * 311.7 + seed * 74.7) * 43758.5453
    return v - np.floor(v)


class Room:
    """An albedo picture, a list of lights and an emissive overlay."""

    def __init__(self, stone=(86, 80, 100), floor=None, ceil=None, ambient=(0.10, 0.10, 0.14), half=48, height=0.62, rng=None, wall_style="brick", floor_style="flag", seed=1):
        self.rng = rng or random.Random(seed)
        self.seed = seed
        self.ambient = np.array(ambient, dtype=np.float32)
        self.lights: list = []
        self.img = Image.new("RGB", (W, H), (0, 0, 0))
        self.em = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.e = ImageDraw.Draw(self.em)
        self.half = half
        self.far = (160 - half, int(VY - height * half), 160 + half, int(VY + height * half))
        self.water_row = None
        self._texture(stone, floor or stone, ceil or stone, height, wall_style, floor_style)

    # --- the box -------------------------------------------------------------------------------------------------------
    def _texture(self, stone, floor, ceil, height, wall_style, floor_style) -> None:
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        dx = xs - 160.0
        dy = ys - VY
        half = float(self.half)
        out = np.zeros((H, W, 3), dtype=np.float32)
        # which surface: wall if |dx|/1 > |dy|/height, else floor (dy>0) or ceiling (dy<0)
        wall = np.abs(dx) * height >= np.abs(dy)
        with np.errstate(divide="ignore", invalid="ignore"):
            w_wall = 1.0 / np.maximum(np.abs(dx), 0.5)
            w_flat = 1.0 / np.maximum(np.abs(dy), 0.5)
            # wall: u along the tunnel, v up the wall
            u_w, v_w = w_wall * 60.0, dy * w_wall * 7.0
            # floor / ceiling: u across, v along
            u_f, v_f = dx * w_flat * 5.0, w_flat * 70.0
        sz = {"brick": (1.0, 0.5), "block": (0.7, 0.5), "flag": (1.0, 1.0)}
        for mask, (u, v), col, style in ((wall, (u_w, v_w), stone, wall_style), (~wall & (dy > 0), (u_f, v_f), floor, floor_style), (~wall & (dy <= 0), (u_f, v_f), ceil, "flag")):
            bw, bh = sz.get(style, (1.0, 0.5))
            row = np.floor(v / bh)
            colx = np.floor(u / bw + (row % 2) * 0.5) if style != "flag" else np.floor(u / bw)
            fu = (u / bw + (row % 2) * 0.5) % 1.0 if style != "flag" else (u / bw) % 1.0
            fv = (v / bh) % 1.0
            mortar = (fu < 0.07) | (fv < 0.10)
            shade = 0.68 + 0.5 * hash2(colx, row, self.seed + (3 if style == "flag" else 0))
            c = np.array(col, dtype=np.float32)
            tex = c[None, None, :] * shade[..., None]
            tex = np.where(mortar[..., None], c[None, None, :] * 0.35, tex)
            # a lit upper edge on each stone
            tex = np.where(((fv > 0.82) & ~mortar)[..., None], tex * 1.12, tex)
            out = np.where(mask[..., None], tex, out)
        self.img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        self.d = ImageDraw.Draw(self.img)
        self.d.rectangle(self.far, fill=(7, 8, 16))

    # --- lights and glow -----------------------------------------------------------------------------------------------
    def light(self, x, y, r, color=(255, 200, 120), power=1.0) -> None:
        self.lights.append((x, y, r, np.array(color, dtype=np.float32) / 255.0, power))

    def torch(self, x, y, color=(255, 190, 90), r=95, power=1.0) -> None:
        self.d.rectangle((x - 1, y + 2, x + 1, y + 11), fill=(40, 30, 24))
        self.d.rectangle((x - 3, y + 1, x + 3, y + 3), fill=(60, 50, 40))
        self.e.polygon([(x, y - 8), (x + 3, y - 2), (x + 2, y + 1), (x - 2, y + 1), (x - 3, y - 2)], fill=color + (255,))
        self.e.polygon([(x, y - 4), (x + 1, y - 1), (x, y + 1), (x - 1, y - 1)], fill=(255, 245, 190, 255))
        self.light(x, y - 2, r, color, power)

    def crystal(self, x, y, h, w=4, color=(110, 235, 255), dark=(30, 90, 140), light_r=40, power=0.6) -> None:
        self.d.polygon([(x, y), (x + w, y + h * 0.3), (x + w, y + h), (x - w, y + h), (x - w, y + h * 0.3)], fill=dark)
        self.e.polygon([(x, y + 1), (x + w - 1, y + h * 0.3), (x + w - 1, y + h - 1), (x, y + h - 1)], fill=color + (210,))
        self.e.polygon([(x, y + 1), (x - w + 1, y + h * 0.3), (x - w + 1, y + h - 1), (x, y + h - 1)], fill=tuple(int(c * 0.65) for c in color) + (210,))
        self.e.line([(x - 1, y + 3), (x - 1, y + h * 0.6)], fill=(255, 255, 255, 230))
        if light_r:
            self.light(x, y + h * 0.5, light_r, color, power)

    def render(self) -> Image.Image:
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        light = np.zeros((H, W, 3), dtype=np.float32) + self.ambient[None, None, :]
        for (lx, ly, r, col, power) in self.lights:
            dd = np.sqrt(((xs - lx) / 1.25) ** 2 + (ys - ly) ** 2) / r
            f = np.clip(1.0 - dd, 0.0, 1.0) ** 1.7 * power
            light += f[..., None] * col[None, None, :]
        # step the light in bands with a little dither
        levels = 7.0
        t = np.tile(BAYER, (H // 4 + 1, W // 4 + 1))[:H, :W]
        q = np.floor(np.clip(light, 0, 1.6) * levels + t[..., None]) / levels
        base = np.asarray(self.img, dtype=np.float32) * (q + 0.07) * 1.75
        base = np.clip(base, 0, 255)
        # a soft bloom of the lights over everything (not stepped)
        base += (light - q) * 12.0
        img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
        out = Image.alpha_composite(img, self.em).convert("RGB")
        arr = np.asarray(out, dtype=np.float32)
        # vignette
        vx = (xs - W / 2) / (W / 2)
        vy = (ys - H / 2) / (H / 2)
        k = 1.0 - np.clip((np.sqrt(vx * vx + vy * vy) - 0.7) * 0.7, 0, 0.55)
        # film grain, tiny
        g = (np.random.default_rng(self.seed).random((H, W)) - 0.5) * 7.0
        arr = arr * k[..., None] + g[..., None]
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# --- shared bits ------------------------------------------------------------------------------------------------------------

def box(d, x, y, w, h):
    d.rectangle((x, y, x + w, y + h), fill=(92, 58, 34))
    d.rectangle((x, y, x + w, y + 2), fill=(130, 88, 52))
    d.line([(x, y + h // 2), (x + w, y + h // 2)], fill=(60, 36, 20))


def barrel(d, x, y, w, h, col=(110, 70, 38)):
    d.ellipse((x, y, x + w, y + h), fill=col)
    d.rectangle((x + 1, y + h * 0.18, x + w - 1, y + h * 0.86), fill=col)
    d.ellipse((x, y, x + w, y + h * 0.3), fill=tuple(int(c * 1.25) for c in col))
    for k in (0.38, 0.7):
        d.line([(x, y + h * k), (x + w, y + h * k)], fill=(40, 34, 30), width=1)


def water(room: Room, y0: int, deep=(14, 40, 70), light=(70, 130, 190)) -> None:
    """Replaces the floor below row y0 with dark water: horizontal ripple lines."""
    rng = room.rng
    room.d.rectangle((0, y0, W, H), fill=deep)
    for k in range(40):
        y = rng.randint(y0 + 2, H - 1)
        x = rng.randint(0, W - 40)
        room.d.line([(x, y), (x + rng.randint(10, 40), y)], fill=light)


def pipe(d, pts, w=3, col=(96, 100, 112)):
    d.line(pts, fill=col, width=w)
    d.line([(x, y - 1) for x, y in pts], fill=tuple(min(255, c + 40) for c in col), width=1)
    for x, y in pts[1:-1]:
        d.rectangle((x - 2, y - 3, x + 2, y + 3), fill=(70, 74, 84))


def shelf(d, x, y, w, h, rng):
    d.rectangle((x, y, x + w, y + h), fill=(34, 30, 38))
    rows = max(1, int(h // 14))
    for r in range(rows):
        yy = y + 3 + r * (h - 4) / rows
        d.line([(x, yy + 11), (x + w, yy + 11)], fill=(70, 56, 40), width=2)
        xx = x + 2
        while xx < x + w - 3:
            bw = rng.randint(2, 4)
            col = rng.choice([(150, 60, 70), (60, 100, 160), (200, 170, 70), (80, 150, 100), (210, 210, 220), (120, 70, 150)])
            d.rectangle((xx, yy, xx + bw, yy + 10), fill=col)
            xx += bw + 1


# --- zones ------------------------------------------------------------------------------------------------------------------

def z_hatch(rng):
    r = Room(stone=(96, 74, 62), ambient=(0.07, 0.07, 0.10), half=34, seed=11)
    d = r.d
    d.rectangle((152, 4, 154, 106), fill=(120, 80, 50))
    d.rectangle((168, 4, 170, 106), fill=(120, 80, 50))
    for y in range(8, 106, 9):
        d.line([(153, y), (169, y)], fill=(110, 74, 46), width=1)
    d.ellipse((140, -6, 182, 14), fill=(24, 22, 28))
    r.light(161, 0, 120, (190, 205, 235), 1.1)  # grey daylight down the shaft
    r.e.polygon([(144, 0), (178, 0), (170, 30), (152, 30)], fill=(210, 220, 245, 70))
    for x, y, (a, b) in ((24, 70, (6, 8)), (30, 74, (8, 4)), (40, 66, (4, 10)), (52, 72, (10, 3)), (276, 62, (7, 7)), (284, 70, (3, 9))):
        r.e.line([(x, y), (x + a, y + b)], fill=(230, 230, 225, 220), width=1)
    for k in range(5):  # tally bundles
        x = 60 + k * 9
        r.e.line([(x, 90), (x, 100)], fill=(225, 225, 215, 200))
    r.torch(268, 92, r=80, power=0.8)
    return r.render()


def z_cables(rng):
    r = Room(stone=(70, 74, 90), ambient=(0.07, 0.08, 0.12), half=40, height=0.55, seed=12)
    d = r.d
    for k in range(9):
        x0 = rng.randint(-20, 340)
        pts = [(x0 + i * 22, 6 + int(26 * math.sin(i * 0.9 + k) ** 2) + k * 3) for i in range(0, 8)]
        d.line(pts, fill=(18, 18, 24), width=rng.choice([3, 4, 5]))
        d.line([(x, y - 1) for x, y in pts], fill=(60, 66, 86), width=1)
    d.rectangle((250, 56, 288, 100), fill=(54, 58, 66))
    d.rectangle((256, 62, 282, 94), fill=(30, 32, 40))
    r.light(266, 78, 110, (110, 170, 255), 1.0)
    for _ in range(14):
        x, y = 266 + rng.randint(-12, 12), 78 + rng.randint(-14, 14)
        r.e.line([(266, 78), (x, y)], fill=(180, 220, 255, 230), width=1)
    r.e.ellipse((262, 74, 270, 82), fill=(235, 245, 255, 255))
    r.light(60, 50, 70, (255, 190, 100), 0.5)
    r.e.ellipse((56, 46, 64, 54), fill=(255, 200, 110, 255))  # a bare bulb
    return r.render()


def z_cloakroom(rng):
    r = Room(stone=(82, 66, 74), ambient=(0.10, 0.08, 0.10), half=60, height=0.62, wall_style="block", seed=13)
    d = r.d
    d.rectangle((70, 40, 250, 118), fill=(64, 48, 52))
    for x in range(78, 246, 14):
        d.line([(x, 48), (x, 56)], fill=(160, 150, 140), width=1)
        col = rng.choice([(150, 60, 70), (60, 90, 150), (90, 120, 80), (170, 130, 60), (110, 80, 130)])
        d.polygon([(x - 4, 56), (x + 4, 56), (x + 6, 92), (x - 6, 92)], fill=col)
    for k in range(34):  # a heap of coats on the floor
        x = rng.randint(80, 240)
        y = rng.randint(100, 150)
        col = rng.choice([(150, 60, 70), (60, 90, 150), (90, 120, 80), (170, 130, 60), (110, 80, 130), (50, 50, 60)])
        d.ellipse((x - 14, y - 6, x + 14, y + 8), fill=col)
    r.e.ellipse((156, 36, 168, 52), fill=(255, 215, 120, 255))  # the brass lamp
    r.e.rectangle((159, 52, 165, 56), fill=(200, 150, 60, 255))
    r.light(162, 46, 150, (255, 205, 120), 1.2)
    r.e.polygon([(100, 70), (130, 66), (136, 80), (106, 86)], fill=(220, 220, 240, 150))  # the moth
    r.e.polygon([(224, 70), (194, 66), (188, 80), (218, 86)], fill=(220, 220, 240, 150))
    r.e.rectangle((159, 66, 165, 86), fill=(60, 50, 50, 255))
    return r.render()


def z_boiler(rng):
    r = Room(stone=(62, 74, 78), ambient=(0.07, 0.09, 0.11), half=44, seed=14)
    d = r.d
    water(r, 108, deep=(10, 28, 44), light=(60, 120, 150))
    for y in (16, 30, 44):
        pipe(d, [(0, y), (110, y + 4), (220, y), (W, y + 6)], w=4)
    pipe(d, [(40, 0), (40, 60), (46, 108)], w=5)
    pipe(d, [(270, 0), (270, 70), (262, 108)], w=5)
    r.torch(120, 74, r=85, power=0.8)
    pts = [(60 + i * 12, 130 + int(10 * math.sin(i * 0.8))) for i in range(18)]  # the eel
    r.e.line(pts, fill=(70, 120, 90, 255), width=7)
    r.e.line([(x, y - 2) for x, y in pts], fill=(160, 210, 150, 255), width=2)
    for i in (2, 5, 9, 13):
        r.e.line([pts[i], (pts[i][0] + 4, pts[i][1] - 10)], fill=(150, 220, 255, 255), width=1)
    r.e.ellipse((pts[-1][0] - 2, pts[-1][1] - 4, pts[-1][0] + 3, pts[-1][1]), fill=(255, 230, 90, 255))
    r.light(pts[6][0], pts[6][1], 70, (120, 200, 255), 0.55)
    for _ in range(8):
        x, y = rng.randint(30, 290), rng.randint(40, 90)
        r.e.ellipse((x, y, x + 16, y + 8), fill=(235, 240, 245, 40))  # steam
    return r.render()


def z_stacks(rng):
    r = Room(stone=(74, 70, 112), ambient=(0.10, 0.12, 0.20), half=46, seed=15)
    for x, y, h, w in ((30, 20, 120, 12), (80, 50, 90, 9), (250, 16, 126, 13), (210, 48, 94, 9), (140, 74, 40, 5), (176, 76, 38, 5)):
        r.crystal(x, y, h, w, light_r=70, power=0.7)
        for k in range(3):  # a speaker-stack look: bands across the column
            yy = y + h * (0.3 + 0.2 * k)
            r.e.line([(x - w + 2, yy), (x + w - 2, yy)], fill=(10, 30, 60, 160))
    for _ in range(14):
        r.crystal(rng.randint(10, 310), rng.randint(110, 150), rng.randint(8, 16), 3, light_r=0)
    r.light(160, 150, 120, (110, 235, 255), 0.7)
    return r.render()


def z_cellar(rng):
    r = Room(stone=(96, 62, 50), floor=(70, 64, 66), ambient=(0.09, 0.07, 0.07), half=62, wall_style="brick", seed=16)
    d = r.d
    for x in (84, 160, 236):
        d.pieslice((x - 36, 18, x + 36, 100), 180, 360, fill=(30, 22, 22))
        d.rectangle((x - 36, 58, x + 36, 112), fill=(24, 18, 20))
    barrel(d, 8, 86, 40, 52)
    barrel(d, 44, 104, 36, 44)
    barrel(d, 274, 84, 40, 54)
    barrel(d, 240, 108, 34, 42)
    d.rectangle((100, 96, 220, 108), fill=(88, 56, 34))
    d.rectangle((100, 108, 220, 130), fill=(60, 38, 24))  # the bar
    d.ellipse((150, 64, 170, 86), fill=(220, 214, 196))  # the skeleton's skull
    d.rectangle((152, 86, 168, 98), fill=(214, 208, 190))
    r.e.rectangle((154, 72, 157, 75), fill=(10, 8, 10, 255))
    r.e.rectangle((163, 72, 166, 75), fill=(10, 8, 10, 255))
    r.e.line([(176, 80), (186, 70)], fill=(190, 230, 255, 255), width=2)  # the glass
    r.torch(60, 60, r=100)
    r.torch(262, 60, r=100)
    for k in range(10):
        x, y = rng.randint(20, 300), rng.randint(140, 170)
        d.ellipse((x, y, x + 6, y + 3), fill=(200, 196, 180))  # bones on the floor
    return r.render()


def z_fungus(rng):
    r = Room(stone=(54, 80, 66), floor=(40, 70, 56), ambient=(0.07, 0.13, 0.10), half=50, seed=17)
    d = r.d
    d.ellipse((90, 120, 230, 170), fill=(18, 60, 44))
    for k in range(40):
        x = rng.randint(0, W)
        y = rng.randint(84, 175)
        s = rng.randint(3, 16) * (0.6 + (y - 80) / 120.0)
        col = rng.choice([(110, 255, 170), (90, 220, 230), (200, 255, 140), (150, 190, 255)])
        d.rectangle((x - 1, y - s, x + 1, y), fill=(190, 200, 170))
        r.e.ellipse((x - s * 0.7, y - s * 1.35, x + s * 0.7, y - s * 0.55), fill=col + (235,))
        r.e.ellipse((x - s * 0.4, y - s * 1.25, x - s * 0.1, y - s * 1.0), fill=(240, 255, 245, 255))
        if s > 9:
            r.light(x, y - s, int(s * 6), col, 0.45)
    for _ in range(40):
        r.e.point((rng.randint(0, W - 1), rng.randint(20, 150)), fill=(190, 255, 210, 255))
    return r.render()


def z_mirrors(rng):
    r = Room(stone=(80, 78, 108), floor=(120, 120, 150), ambient=(0.09, 0.09, 0.16), half=44, seed=18)
    d = r.d
    for x0, x1 in ((6, 30), (40, 58), (68, 80)):
        for xx0, xx1 in ((x0, x1), (W - x1, W - x0)):
            d.polygon([(xx0, 20 + (xx0 // 6) % 6), (xx1, 34), (xx1, 130), (xx0, 150)], fill=(150, 170, 210))
            d.line([(xx0 + 3, 40), (xx1 - 2, 120)], fill=(230, 240, 255))
            for k in range(3):  # strangers dancing in the glass
                x = int((xx0 + xx1) / 2 + (k - 1) * 4)
                d.rectangle((x - 1, 90 - k * 3, x + 1, 112), fill=(60, 50, 90))
                d.ellipse((x - 2, 84 - k * 3, x + 2, 90 - k * 3), fill=(60, 50, 90))
    d.rectangle((140, 66, 180, 112), fill=(150, 170, 210))
    d.rectangle((146, 72, 174, 108), fill=(24, 24, 40))
    r.light(160, 20, 150, (200, 210, 255), 1.0)
    r.light(70, 80, 70, (255, 120, 220), 0.5)
    r.light(250, 80, 70, (110, 220, 255), 0.5)
    r.e.rectangle((148, 84, 172, 106), fill=(235, 240, 255, 60))
    return r.render()


def z_pit(rng):
    r = Room(stone=(70, 64, 80), ambient=(0.07, 0.06, 0.10), half=64, height=0.7, seed=19)
    d = r.d
    d.ellipse((50, 104, 270, 172), fill=(58, 52, 62))  # rim
    d.ellipse((66, 110, 254, 166), fill=(2, 2, 6))
    d.ellipse((90, 120, 230, 160), fill=(0, 0, 3))
    for k in range(14):
        a = k / 14 * math.tau
        x, y = 160 + 106 * math.cos(a), 138 + 30 * math.sin(a)
        d.ellipse((x - 6, y - 3, x + 6, y + 3), fill=(80, 74, 86))
    r.e.line([(160, 0), (160, 130)], fill=(150, 110, 66, 255), width=2)  # the rope
    for y in range(6, 130, 8):
        r.e.line([(158, y), (162, y + 3)], fill=(90, 62, 36, 255))
    d.rectangle((256, 60, 304, 120), fill=(50, 46, 60))  # the ledge and its studded door
    d.rectangle((266, 66, 294, 120), fill=(44, 30, 24))
    for x in range(268, 294, 6):
        for y in range(70, 116, 8):
            r.e.point((x, y), fill=(190, 150, 80, 255))
    r.e.ellipse((66, 110, 254, 166), outline=(120, 110, 160, 230), width=2)
    r.light(160, 150, 80, (80, 100, 200), 0.5)
    r.e.ellipse((156, 150, 164, 156), fill=(200, 230, 255, 255))  # a glint far down: the fork
    r.torch(280, 52, r=80, power=0.9)
    return r.render()


def z_vaults(rng):
    r = Room(stone=(78, 76, 92), ambient=(0.09, 0.08, 0.12), half=64, height=0.6, wall_style="block", seed=20)
    d = r.d
    for x in range(8, 140, 40):
        shelf(d, x, 24, 34, 112, rng)
    for x in range(184, 316, 40):
        shelf(d, x, 24, 34, 112, rng)
    d.rectangle((126, 60, 194, 122), fill=(50, 44, 60))
    d.rectangle((136, 70, 184, 122), fill=(14, 12, 20))
    for x in (110, 210):
        d.rectangle((x, 108, x + 3, 140), fill=(200, 170, 70))
        d.ellipse((x - 1, 104, x + 4, 110), fill=(220, 190, 80))
    d.line([(112, 112), (212, 112)], fill=(150, 30, 50), width=3)  # the velvet rope
    d.rectangle((146, 90, 174, 140), fill=(60, 80, 50))  # the bouncer's vest
    d.rectangle((140, 96, 146, 128), fill=(90, 120, 80))
    d.rectangle((174, 96, 180, 128), fill=(90, 120, 80))
    d.ellipse((148, 70, 172, 92), fill=(96, 118, 84))
    r.e.rectangle((151, 80, 156, 82), fill=(255, 200, 80, 255))
    r.e.rectangle((164, 80, 169, 82), fill=(255, 200, 80, 255))
    r.e.rectangle((148, 108, 172, 114), fill=(240, 230, 90, 255))  # hi-vis stripe
    r.torch(30, 18, r=90)
    r.torch(290, 18, r=90)
    r.light(160, 60, 100, (255, 190, 120), 0.7)
    return r.render()


def z_warren(rng):
    r = Room(stone=(88, 66, 54), floor=(70, 56, 48), ambient=(0.08, 0.06, 0.06), half=44, seed=21)
    d = r.d
    for _ in range(16):
        side = rng.choice([0, 1])
        x = rng.randint(4, 74) if side == 0 else rng.randint(246, 314)
        y = rng.randint(50, 130)
        d.ellipse((x - 8, y - 5, x + 8, y + 5), fill=(6, 4, 6))
        if rng.random() < 0.7:
            r.e.point((x - 2, y), fill=(255, 80, 60, 255))
            r.e.point((x + 2, y), fill=(255, 80, 60, 255))
    d.polygon([(120, 130), (140, 92), (180, 92), (200, 130)], fill=(78, 82, 92))  # the throne of speaker foam
    for x in range(126, 196, 7):
        d.ellipse((x, 100, x + 5, 106), fill=(50, 54, 62))
    d.ellipse((146, 70, 176, 98), fill=(100, 84, 76))  # a mass of rats
    for x in (150, 160, 170):
        d.ellipse((x - 1, 64, x + 5, 70), fill=(110, 94, 84))
        r.e.point((x + 1, 66), fill=(255, 60, 50, 255))
    for k, x in enumerate((150, 158, 166, 174)):
        d.polygon([(x, 62), (x + 2, 56), (x + 4, 62)], fill=(215, 190, 90))  # bottle-top crown
    r.torch(36, 60, color=(255, 150, 70), r=90)
    r.torch(284, 60, color=(255, 150, 70), r=90)
    r.light(160, 100, 70, (255, 120, 90), 0.3)
    return r.render()


def z_kitchens(rng):
    r = Room(stone=(110, 90, 84), floor=(120, 110, 106), ambient=(0.12, 0.07, 0.05), half=66, height=0.62, wall_style="block", floor_style="flag", seed=22)
    d = r.d
    for x in (16, 98, 196, 262):
        d.rectangle((x, 66, x + 44, 124), fill=(48, 46, 52))
        d.rectangle((x + 6, 82, x + 38, 114), fill=(10, 6, 6))
        r.e.rectangle((x + 8, 90, x + 36, 112), fill=(255, 120, 40, 235))
        r.e.rectangle((x + 12, 98, x + 32, 112), fill=(255, 220, 90, 255))
        r.light(x + 22, 100, 90, (255, 120, 50), 1.1)
    for x in range(20, 300, 30):
        d.line([(x, 0), (x, 20 + (x % 7))], fill=(60, 60, 66))
        d.ellipse((x - 8, 20 + (x % 7), x + 8, 34 + (x % 7)), fill=(110, 112, 120))
    d.rectangle((140, 100, 180, 112), fill=(60, 60, 68))  # the stove with the imp
    d.ellipse((150, 78, 170, 100), fill=(170, 40, 36))
    d.polygon([(148, 78), (152, 64), (158, 78)], fill=(240, 240, 240))
    r.e.rectangle((153, 86, 156, 88), fill=(255, 240, 120, 255))
    r.e.rectangle((164, 86, 167, 88), fill=(255, 240, 120, 255))
    for k in range(3):
        r.e.line([(140 + k * 16, 70), (146 + k * 16, 56)], fill=(210, 220, 235, 255), width=1)  # the knives
    return r.render()


def z_hall(rng):
    r = Room(stone=(100, 100, 112), floor=(86, 86, 100), ambient=(0.10, 0.11, 0.15), half=40, height=0.6, wall_style="block", seed=23)
    d = r.d
    for i, sx in enumerate((8, 38, 64, 86)):
        s = 1.0 - i * 0.2
        for side in (0, 1):
            x = sx if side == 0 else W - sx - 22 * s
            h = 100 * s
            y = VY + 30 * s - h * 0.6
            d.rectangle((x, y + h * 0.35, x + 22 * s, y + h), fill=(150, 150, 160))
            d.ellipse((x + 6 * s, y + h * 0.1, x + 16 * s, y + h * 0.3), fill=(168, 168, 176))
            d.rectangle((x - 3 * s, y + h * 0.2, x + 1 * s, y + h * 0.42), fill=(160, 160, 170))
            d.rectangle((x + 21 * s, y + h * 0.2, x + 25 * s, y + h * 0.42), fill=(160, 160, 170))
    d.ellipse((126, 52, 194, 118), fill=(34, 34, 44))  # the round door at the far end
    d.ellipse((134, 60, 186, 110), fill=(52, 52, 66))
    d.polygon([(142, 44), (178, 44), (186, 62), (134, 62)], fill=(112, 112, 122))  # the gargoyle above it
    d.ellipse((150, 32, 170, 52), fill=(130, 130, 140))
    d.rectangle((158, 44, 162, 54), fill=(150, 150, 160))
    r.e.rectangle((152, 40, 155, 42), fill=(255, 120, 80, 255))
    r.e.rectangle((165, 40, 168, 42), fill=(255, 120, 80, 255))
    r.torch(110, 56, color=(170, 190, 255), r=90, power=0.9)
    r.torch(210, 56, color=(170, 190, 255), r=90, power=0.9)
    r.light(160, 150, 100, (180, 190, 255), 0.5)
    return r.render()


def z_door(rng):
    r = Room(stone=(70, 74, 92), ambient=(0.08, 0.09, 0.14), half=74, height=0.62, wall_style="block", seed=24)
    d = r.d
    d.ellipse((70, 8, 250, 172), fill=(22, 24, 32))
    d.ellipse((78, 16, 242, 164), fill=(54, 58, 72))
    for a in range(0, 360, 20):  # rivets
        x, y = 160 + 78 * math.cos(math.radians(a)), 90 + 70 * math.sin(math.radians(a))
        d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(100, 104, 120))
    d.ellipse((112, 42, 208, 138), fill=(30, 32, 42))
    for k in range(5):
        rr = 44 - k * 8
        r.e.ellipse((160 - rr, 90 - rr, 160 + rr, 90 + rr), outline=(120, 190, 255, 120 + k * 20), width=1)
    r.e.ellipse((154, 84, 166, 96), fill=(180, 230, 255, 255))
    r.light(160, 90, 140, (110, 170, 255), 1.0)
    r.torch(40, 70, color=(255, 190, 90), r=80, power=0.6)
    r.torch(280, 70, color=(255, 190, 90), r=80, power=0.6)
    return r.render()


def z_echo(rng):
    r = Room(stone=(70, 74, 86), floor=(74, 78, 94), ambient=(0.07, 0.08, 0.12), half=86, height=0.62, seed=25)
    d = r.d
    for k in range(7):  # rings spreading on the floor
        rr = 20 + k * 22
        r.e.ellipse((160 - rr * 1.4, 128 - rr * 0.35, 160 + rr * 1.4, 128 + rr * 0.35), outline=(150, 190, 255, 200 - k * 25), width=1)
    r.e.polygon([(160, 40), (172, 54), (170, 100), (178, 130), (160, 134), (142, 130), (150, 100), (148, 54)], fill=(190, 215, 255, 150))  # the Echo
    r.e.ellipse((150, 28, 170, 52), fill=(210, 230, 255, 190))
    r.e.rectangle((154, 38, 157, 41), fill=(255, 255, 255, 255))
    r.e.rectangle((163, 38, 166, 41), fill=(255, 255, 255, 255))
    r.light(160, 90, 130, (130, 170, 255), 1.0)
    return r.render()


def z_dawn(rng):
    r = Room(stone=(100, 96, 106), ambient=(0.12, 0.12, 0.16), half=38, seed=26)
    d = r.d
    for k in range(9):  # steps climbing away
        y = 150 - k * 11
        x0 = 70 + k * 6
        d.polygon([(x0, y), (W - x0, y), (W - x0 - 4, y - 8), (x0 + 4, y - 8)], fill=(120, 116, 128))
        d.line([(x0, y), (W - x0, y)], fill=(40, 38, 48))
    d.rectangle((140, 56, 180, 84), fill=(214, 224, 238))  # the grey light at the top
    d.rectangle((152, 56, 156, 84), fill=(240, 244, 250))
    r.light(160, 70, 170, (200, 215, 240), 1.3)
    r.e.polygon([(140, 84), (180, 84), (220, 170), (100, 170)], fill=(220, 230, 250, 40))
    return r.render()


def z_death(rng):
    img = Image.new("RGB", (W, H), (24, 4, 8))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(40 - 22 * t), int(6 - 3 * t), int(10 - 4 * t)))
    d.ellipse((118, 36, 202, 122), fill=(214, 208, 192))
    d.rectangle((132, 94, 188, 134), fill=(204, 198, 182))
    for x in range(138, 186, 8):
        d.line([(x, 112), (x, 134)], fill=(30, 8, 10))
    d.ellipse((134, 70, 156, 96), fill=(20, 4, 8))
    d.ellipse((164, 70, 186, 96), fill=(20, 4, 8))
    d.polygon([(160, 96), (154, 112), (166, 112)], fill=(20, 4, 8))
    d.ellipse((141, 76, 149, 86), fill=(190, 40, 30))
    d.ellipse((171, 76, 179, 86), fill=(190, 40, 30))
    for x in (40, 280):  # two candles
        d.rectangle((x - 3, 110, x + 3, 150), fill=(220, 210, 180))
        d.polygon([(x, 98), (x + 4, 108), (x - 4, 108)], fill=(255, 200, 90))
    arr = np.asarray(img, dtype=np.float32)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    for cx in (40, 280):
        f = np.clip(1 - np.sqrt(((xs - cx) / 1.3) ** 2 + (ys - 106) ** 2) / 110, 0, 1) ** 2
        arr += f[..., None] * np.array([90, 50, 15], dtype=np.float32)
    vx, vy = (xs - W / 2) / (W / 2), (ys - H / 2) / (H / 2)
    arr *= (1 - np.clip((np.sqrt(vx * vx + vy * vy) - 0.6) * 0.8, 0, 0.6))[..., None]
    arr += (np.random.default_rng(3).random((H, W, 1)) - 0.5) * 8
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def z_victory(rng):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(70 + 185 * t), int(60 + 130 * t), int(120 + 40 * t) if t < 0.62 else 110))
    d.ellipse((130, 86, 190, 146), fill=(255, 240, 200))
    d.ellipse((140, 96, 180, 136), fill=(255, 252, 235))
    d.rectangle((0, 130, W, H), fill=(60, 58, 70))  # the car park
    for x in range(20, 320, 60):
        d.polygon([(x, H), (x + 6, 140), (x + 10, 140), (x + 20, H)], fill=(190, 190, 196))
    d.rectangle((0, 70, 90, 132), fill=(34, 30, 48))  # the club's wall with its sign
    d.rectangle((10, 84, 80, 96), fill=(255, 90, 150))
    d.rectangle((230, 92, 320, 132), fill=(40, 36, 54))
    for k, x in enumerate((100, 206)):  # two parked vans
        d.rectangle((x, 114, x + 46, 136), fill=(150, 160, 190))
        d.rectangle((x + 4, 118, x + 22, 126), fill=(60, 80, 120))
    arr = np.asarray(img, dtype=np.float32)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    f = np.clip(1 - np.sqrt(((xs - 160) / 1.5) ** 2 + (ys - 116) ** 2) / 120, 0, 1) ** 2
    arr += f[..., None] * np.array([90, 60, 10], dtype=np.float32)
    arr += (np.random.default_rng(4).random((H, W, 1)) - 0.5) * 6
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


SCENES = {"hatch": z_hatch, "cables": z_cables, "cloakroom": z_cloakroom, "boiler": z_boiler, "stacks": z_stacks, "cellar": z_cellar, "fungus": z_fungus, "mirrors": z_mirrors,
          "pit": z_pit, "vaults": z_vaults, "warren": z_warren, "kitchens": z_kitchens, "hall": z_hall, "door": z_door, "echo": z_echo, "dawn": z_dawn, "death": z_death, "victory": z_victory}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wanted = sys.argv[1:] or list(SCENES)
    for name in wanted:
        img = SCENES[name](random.Random(sum(map(ord, name))))
        img.resize((W * 4, H * 4), Image.NEAREST).save(OUT / f"{name}.png", optimize=True)
        print("wrote", f"assets/trial/scenes/{name}.png")


if __name__ == "__main__":
    main()
