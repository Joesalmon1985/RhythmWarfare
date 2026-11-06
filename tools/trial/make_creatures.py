"""The ten creatures of the Bassment, drawn in the game's pixel language (docs/art/STYLE_GUIDE.md sections 6, 7 and 9; audit finding F12).

    python tools/trial/make_creatures.py

Writes the portraits assets/trial/art/<id>_0.png (the creature) and <id>_1.png (struck), 64 x 64; tools/story/art/tex_bassment.py calls `frame(id, pose, 128)` for the
room billboards fig_<id>_<idle|attack|struck> (128 x 128). One painter draws both sizes from the same shapes (coordinates are given on a 128 grid).

How they are drawn, so they sit beside the baked people and A4's doors:
  * every part is a shape filled from a short ramp of its material (four or five steps, coloured darks, no black), shaded from the upper left (spheres, tubes, flat
    planes with a bevel: the upper-left pixel row of a part one step lighter, the lower-right one step darker) and quantised with the 4 x 4 ordered dither;
  * the silhouette is a one-pixel edge two steps darker than its own colour (no outline colour, no halo); alpha is 0 or 255 everywhere (the Echo is see-through by
    a dither of holes, not by partial alpha);
  * each pose has its own drawing: `idle` waits, `attack` is the lunge (the body thrown forward, mouth or weapon out, the eyes turned to a hot orange), `struck`
    recoils (eyes shut, the body knocked back, every colour lifted two steps, a burst of hard sparks). A creature keeps its palette in every pose.
The ids are the "encounters" of content/trial/passages.json; add a function and an entry in CREATURES for a new one. Deterministic: no clock, no unseeded random.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "trial" / "art"
S = 64  # portrait size
BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16.0 - 0.5
LIGHT = np.array([-0.45, -0.62, 0.64], np.float32) / np.linalg.norm([-0.45, -0.62, 0.64])


def ramp(*cols: str) -> np.ndarray:
    return np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in cols], np.uint8)


# ---- materials (dark to light; the darkest of each is a coloured dark, never black) ------------------------------------------------------------------
WING = ramp("#2a1e1a", "#54402f", "#82684c", "#ae9472", "#d2bf98")
MOTHB = ramp("#1e1410", "#3c2a1e", "#604430", "#886848", "#ab8a60")
SPOT = ramp("#2e1008", "#6a2a0e", "#b4581a", "#e89a36", "#f8d27a")
EEL = ramp("#08160f", "#14301f", "#245034", "#3a7a4c", "#60a46c")
BELLY = ramp("#26281a", "#46482c", "#727046", "#a09a6c", "#c8c092")
COPPER = ramp("#3a1606", "#6e2e0c", "#a85018", "#d8823a", "#f0b474")
BONE = ramp("#2e2620", "#5a4e40", "#8a7e66", "#b8ac90", "#d8ccb4")
OAK = ramp("#1c0e06", "#3a200e", "#5e3818", "#86562a", "#aa7840")
IRON = ramp("#121219", "#262833", "#3e424f", "#5c6270", "#848b98")
MOP = ramp("#2c2a26", "#4e4a42", "#787262", "#a69e88", "#c8c0a8")
FUR = ramp("#0c1410", "#1c2a20", "#30443a", "#4a6250", "#6c886a")
FUNG = ramp("#06220e", "#0e4a1e", "#1e7a34", "#3cb85a", "#9ae8a0")
GLASS = ramp("#0c1430", "#1e3060", "#3a5c98", "#6c92c6", "#b0cce8")
TROLL = ramp("#10180c", "#24361a", "#3e5a2a", "#5c803c", "#84a658")
HIVIS = ramp("#3a3206", "#766a0e", "#b4a01a", "#dcc832", "#f0e26e")
SUIT = ramp("#0e0e16", "#1c1c28", "#2c2c3c", "#40404f", "#585868")
REFL = ramp("#4a4e56", "#767a82", "#a0a4aa", "#c8c8c4")
BOARD = ramp("#2a1a0c", "#4e3418", "#7a5428", "#a4783c", "#c89c58")
PAPER = ramp("#6a6458", "#9a9282", "#c4bca6", "#d8ccb4")
RAT = ramp("#16100e", "#2e221e", "#4c3a32", "#6e5648", "#927a68")
PINK = ramp("#3a1a1e", "#6e3438", "#a4585a", "#cc8482", "#e4aca4")
GOLD = ramp("#2a1804", "#5a3a0a", "#9a6a14", "#d0a030", "#f0d070")
IMP = ramp("#2a0606", "#5a0e0c", "#921c16", "#c83a26", "#ec6a40")
CHEF = ramp("#4a4a52", "#77777e", "#a4a4a6", "#c4c2bc", "#d8d4c8")
STEEL = ramp("#1a1e26", "#3a404c", "#646c7a", "#98a0ac", "#c4cad0")
STONE = ramp("#16161c", "#2c2c34", "#484852", "#686872", "#8e8e96")
MOSS = ramp("#0e1a0c", "#1e3418", "#34522a", "#4e7038")
ECHO = ramp("#1e2a40", "#3a4e74", "#6480aa", "#98b0d4", "#c4d4ec")
HORN = ramp("#2a2218", "#54473a", "#8a7a62", "#b8a888", "#d8ccb4")
MOUTH = ramp("#1a0808", "#3a1012", "#5e1c1c")

EYE_HOT = ("#ff6a2a", "#ffd27a")  # every creature's attack eyes: an ember core and a hot rim
SPARK = ("#eab278", "#d8ccb4")  # the struck burst: warm light and paper (style guide section 3)


class Painter:
    """A square RGBA canvas of n pixels whose shapes are given on a 128 grid (so one drawing makes the 128 billboard and the 64 portrait)."""

    def __init__(self, n: int = 128):
        self.n = n
        self.k = n / 128.0
        i, j = np.mgrid[0:n, 0:n].astype(np.float32)
        self.x = (j + 0.5) / self.k
        self.y = (i + 0.5) / self.k
        self.rgb = np.zeros((n, n, 3), np.uint8)
        self.a = np.zeros((n, n), bool)
        self.lvl = np.zeros((n, n), np.int32)
        self.rid = np.full((n, n), -1, np.int32)
        self.ramps: list = []
        self.bayer = BAYER4[np.arange(n)[:, None] % 4, np.arange(n)[None, :] % 4]

    # ---- shapes (masks) ------------------------------------------------------------------------------------------------------------------------------
    def ell(self, cx, cy, rx, ry):
        return ((self.x - cx) / rx) ** 2 + ((self.y - cy) / ry) ** 2 <= 1.0

    def rect(self, x0, y0, x1, y1):
        return (self.x >= x0) & (self.x < x1) & (self.y >= y0) & (self.y < y1)

    def poly(self, pts):
        inside = np.zeros((self.n, self.n), bool)
        for i in range(len(pts)):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
            cross = (y1 > self.y) != (y2 > self.y)
            xi = (x2 - x1) * (self.y - y1) / ((y2 - y1) if y2 != y1 else 1e-6) + x1
            inside ^= cross & (self.x < xi)
        return inside

    def seg(self, ax, ay, bx, by, w):
        dx, dy = bx - ax, by - ay
        t = np.clip(((self.x - ax) * dx + (self.y - ay) * dy) / max(dx * dx + dy * dy, 1e-6), 0, 1)
        return (self.x - ax - t * dx) ** 2 + (self.y - ay - t * dy) ** 2 <= (w * 0.5) ** 2

    def tube(self, pts, r0, r1):
        """A tube along a polyline, radius r0 at the first point to r1 at the last: (mask, shade lit from the upper left across the tube)."""
        lens = [float(np.hypot(b[0] - a[0], b[1] - a[1])) for a, b in zip(pts, pts[1:])]
        tot = max(sum(lens), 1e-6)
        best = np.full((self.n, self.n), 9.0, np.float32)
        vx = np.zeros_like(best)
        vy = np.zeros_like(best)
        acc = 0.0
        for (a, b), ln in zip(zip(pts, pts[1:]), lens):
            dx, dy = b[0] - a[0], b[1] - a[1]
            t = np.clip(((self.x - a[0]) * dx + (self.y - a[1]) * dy) / max(ln * ln, 1e-6), 0, 1)
            px, py = a[0] + t * dx, a[1] + t * dy
            r = r0 + (r1 - r0) * (acc + t * ln) / tot
            ox, oy = (self.x - px) / r, (self.y - py) / r
            d = np.hypot(ox, oy)
            upd = d < best
            best = np.where(upd, d, best)
            vx = np.where(upd, ox, vx)
            vy = np.where(upd, oy, vy)
            acc += ln
        m = best <= 1.0
        nz = np.sqrt(np.clip(1 - vx * vx - vy * vy, 0, 1))
        sh = 0.12 + 0.88 * np.clip(vx * LIGHT[0] + vy * LIGHT[1] + nz * LIGHT[2], 0, 1)
        return m, sh

    # ---- shades (0..1 fields) ------------------------------------------------------------------------------------------------------------------------
    def sphere(self, cx, cy, rx, ry, amb=0.12):
        nx = np.clip((self.x - cx) / rx, -1, 1)
        ny = np.clip((self.y - cy) / ry, -1, 1)
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
        return amb + (1 - amb) * np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)

    def lin(self, x0, y0, x1, y1, a=0.75, b=0.3):
        """A flat plane lit a at (x0, y0) falling to b at (x1, y1)."""
        dx, dy = x1 - x0, y1 - y0
        t = np.clip(((self.x - x0) * dx + (self.y - y0) * dy) / max(dx * dx + dy * dy, 1e-6), 0, 1)
        return a + (b - a) * t

    def noise(self, scale, seed):
        """Value noise 0..1 on the 128 grid (the same pattern at both sizes)."""
        rng = np.random.RandomState(seed)
        c = int(128 / scale) + 2
        g = rng.rand(c, c).astype(np.float32)
        fx, fy = self.x / scale, self.y / scale
        x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
        tx, ty = fx - x0, fy - y0
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        x0, y0 = np.clip(x0, 0, c - 2), np.clip(y0, 0, c - 2)
        return (g[y0, x0] * (1 - tx) + g[y0, x0 + 1] * tx) * (1 - ty) + (g[y0 + 1, x0] * (1 - tx) + g[y0 + 1, x0 + 1] * tx) * ty

    # ---- paint -----------------------------------------------------------------------------------------------------------------------------------------
    def _rid(self, pal) -> int:
        for i, r in enumerate(self.ramps):
            if r is pal:
                return i
        self.ramps.append(pal)
        return len(self.ramps) - 1

    def part(self, mask, pal, shade, bevel=0.2, dither=0.6):
        m = np.asarray(mask, bool)
        if not m.any():
            return
        sh = np.full((self.n, self.n), float(shade), np.float32) if np.isscalar(shade) else shade.astype(np.float32)
        if bevel:
            up = m & ~np.roll(m, 1, 0)
            left = m & ~np.roll(m, 1, 1)
            down = m & ~np.roll(m, -1, 0)
            right = m & ~np.roll(m, -1, 1)
            sh = sh + bevel * (up | left) - bevel * (down | right)
        k = len(pal) - 1
        lv = np.clip(np.round(np.clip(sh, 0, 1) * k + self.bayer * dither), 0, k).astype(np.int32)
        self.rgb[m] = pal[lv[m]]
        self.a[m] = True
        self.lvl[m] = lv[m]
        self.rid[m] = self._rid(pal)

    def glow(self, mask, colour: str):
        """An emissive pixel group (eyes, sparks, embers): one solid colour, never darkened at the edge."""
        m = np.asarray(mask, bool)
        self.rgb[m] = [int(colour[i:i + 2], 16) for i in (1, 3, 5)]
        self.a[m] = True
        self.rid[m] = -1

    def holes(self, mask):
        """See-through by a dither of holes: the pixels of `mask` are cut out (alpha 0)."""
        self.a &= ~np.asarray(mask, bool)

    def finish(self, lift: int = 0) -> np.ndarray:
        a = self.a
        for i, pal in enumerate(self.ramps):
            m = a & (self.rid == i)
            if lift:
                self.lvl[m] = np.clip(self.lvl[m] + lift, 0, len(pal) - 1)
            rim = m & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
            lv = np.where(rim, np.maximum(self.lvl - 2, 0), self.lvl)
            self.rgb[m] = pal[lv[m]]
        out = np.zeros((self.n, self.n, 4), np.uint8)
        out[..., :3] = np.where(a[..., None], self.rgb, 0)
        out[..., 3] = np.where(a, 255, 0)
        return out


# ---- shared features --------------------------------------------------------------------------------------------------------------------------------------

def eyes(p: Painter, pts, r, pose, idle=("#c8a020", "#f8e070"), shut_pal=None):
    """A pair (or more) of eyes: idle in the creature's own colour, attack hot, struck shut (a dark slit)."""
    for (x, y) in pts:
        if pose == "struck":
            p.part(p.rect(x - r, y - 0.6, x + r, y + 1.4), shut_pal if shut_pal is not None else MOUTH, 0.1, bevel=0)
            continue
        rr = r * (1.25 if pose == "attack" else 1.0)
        rim, core = EYE_HOT if pose == "attack" else idle
        p.glow(p.ell(x, y, rr, rr * 0.9), rim)
        p.glow(p.ell(x - rr * 0.25, y - rr * 0.25, max(rr * 0.45, 0.8), max(rr * 0.45, 0.8)), core)


def sparks(p: Painter, cx, cy, rad, seed):
    """The struck burst: short hard rays of warm light around a point."""
    rng = np.random.RandomState(seed)
    for k in range(9):
        ang = k / 9 * 2 * np.pi + rng.uniform(-0.2, 0.2)
        r0 = rad * rng.uniform(0.75, 0.95)
        r1 = r0 + rad * rng.uniform(0.18, 0.32)
        p.glow(p.seg(cx + np.cos(ang) * r0, cy + np.sin(ang) * r0, cx + np.cos(ang) * r1, cy + np.sin(ang) * r1, 2.2), SPARK[k % 2])


def fur(p: Painter, mask, pal, base, seed, amount=0.22):
    """Fur or moss: a shaded mass broken by short darker strands (noise stretched vertically)."""
    n1 = p.noise(3.0, seed)
    n2 = p.noise(9.0, seed + 1)
    strand = ((p.noise(2.0, seed + 2) > 0.62) & (n1 > 0.45)).astype(np.float32)
    p.part(mask, pal, base + (n2 - 0.5) * 0.25 - amount * strand)


# ---- the creatures ----------------------------------------------------------------------------------------------------------------------------------------

def lampmoth(p: Painter, pose: str) -> None:
    """A moth the size of a dinner plate per wing, dusty and furious: forewings with lamp-amber eye-spots, a furry body, feathered antennae."""
    up = {"idle": 0, "attack": -14, "struck": 22}[pose]
    spread = {"idle": 1.0, "attack": 1.06, "struck": 0.82}[pose]
    for sx in (-1, 1):
        def X(v):
            return 64 + sx * v * spread
        hind = p.poly([(X(4), 70), (X(40), 72 + up * 0.3), (X(52), 96 + up * 0.4), (X(34), 112 + up * 0.3), (X(10), 96)])
        p.part(hind, WING, p.lin(64, 70, X(48), 110, 0.55, 0.3) + (p.noise(6, 11 + sx) - 0.5) * 0.2)
        fore = p.poly([(X(4), 54), (X(30), 24 + up), (X(58), 14 + up), (X(62), 34 + up * 0.8), (X(52), 66 + up * 0.4), (X(22), 76), (X(6), 70)])
        p.part(fore, WING, p.lin(X(10), 30, X(56), 70, 0.8, 0.35) + (p.noise(5, 21 + sx) - 0.5) * 0.25)
        for t in (0.3, 0.55, 0.8):  # veins
            p.part(p.seg(X(6), 58, X(10 + 46 * t), 22 + up + 40 * t * t, 1.4) & fore, WING, 0.18, bevel=0)
        band = p.seg(X(22), 30 + up * 0.9, X(48), 60 + up * 0.5, 3.0) & fore
        p.part(band, WING, 0.95, bevel=0)
        ex, ey = X(36), 40 + up * 0.75
        p.part(p.ell(ex, ey, 9, 8), MOTHB, 0.15, bevel=0)
        p.part(p.ell(ex, ey, 7, 6), SPOT, p.sphere(ex, ey, 7, 6), bevel=0)
        p.glow(p.ell(ex - 1.5, ey - 1.5, 2.2, 2.0), "#f8d27a" if pose != "attack" else "#ffd27a")
    body = p.ell(64, 84, 8, 22)
    p.part(body, MOTHB, p.sphere(64, 82, 9, 22) - 0.18 * ((np.floor(p.y / 5) % 2) == 0) * (p.y > 72))
    fur(p, p.ell(64, 58, 12, 13), MOTHB, p.sphere(64, 56, 12, 13), 31, 0.18)
    hy = 42 if pose != "struck" else 46
    p.part(p.ell(64, hy, 9, 8), MOTHB, p.sphere(64, hy - 1, 9, 8))
    for sx in (-1, 1):  # feathered antennae
        tip = (64 + sx * 22, 14 if pose == "attack" else (20 if pose == "idle" else 34))
        p.part(p.seg(64 + sx * 3, hy - 6, tip[0], tip[1], 2.2), MOTHB, 0.55, bevel=0)
        for t in np.linspace(0.3, 0.95, 6):
            bx, by = 64 + sx * 3 + (tip[0] - 64 - sx * 3) * t, hy - 6 + (tip[1] - hy + 6) * t
            p.part(p.seg(bx, by, bx + sx * 3, by + 3, 1.3), MOTHB, 0.4, bevel=0)
    eyes(p, [(59, hy), (69, hy)], 3.0, pose, idle=("#3a2a1e", "#d2bf98"))
    if pose == "attack":
        rng = np.random.RandomState(5)
        for _ in range(40):  # wing dust flung at you
            x, y = rng.uniform(8, 120), rng.uniform(4, 100)
            p.glow(p.rect(x, y, x + 1.6, y + 1.6), "#d2bf98" if rng.rand() < 0.6 else "#ae9472")
    if pose == "struck":
        sparks(p, 64, 52, 30, 7)


def cable_eel(p: Painter, pose: str) -> None:
    """An eel rearing out of black water, wrapped in bare copper wire, crackling: a thick green-black body in an S, a pale belly, a jaw, sparks."""
    if pose == "idle":
        path = [(18, 126), (30, 108), (52, 98), (62, 80), (54, 60), (60, 40), (76, 28), (92, 26)]
    elif pose == "attack":
        path = [(18, 126), (30, 110), (50, 104), (66, 92), (70, 74), (64, 58), (66, 42), (74, 36)]
    else:
        path = [(18, 126), (32, 110), (56, 104), (68, 88), (74, 70), (90, 58), (100, 48), (108, 46)]
    m, sh = p.tube(path, 12, 8)
    belly = m & (sh < 0.45)
    p.part(m, EEL, sh * 0.95)
    p.part(belly & (p.noise(4, 3) > 0.35), BELLY, sh + 0.25, bevel=0)
    stripe = ((p.x * 0.9 + p.y * 0.6) % 13.0) < 1.6  # the copper wire wound round it
    p.part(m & stripe, COPPER, sh + 0.15, bevel=0)
    hx, hy = path[-1]
    hx0, hy0 = path[-2]
    dx, dy = (hx - hx0), (hy - hy0)
    L = np.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    if pose == "attack":  # the head comes at you: big, jaw wide, teeth
        p.part(p.ell(hx, hy + 2, 16, 12), EEL, p.sphere(hx - 2, hy, 16, 12))
        mouth = p.poly([(hx - 12, hy + 4), (hx + 12, hy + 4), (hx + 8, hy + 16), (hx - 8, hy + 16)])
        p.part(mouth, MOUTH, p.lin(hx, hy + 4, hx, hy + 16, 0.9, 0.1), bevel=0)
        for tx in range(-10, 11, 4):
            p.part(p.poly([(hx + tx - 1.5, hy + 4), (hx + tx + 1.5, hy + 4), (hx + tx, hy + 9)]), BONE, 0.9, bevel=0)
        eyes(p, [(hx - 7, hy - 3), (hx + 7, hy - 3)], 2.6, pose)
    else:
        head = p.ell(hx + ux * 4, hy + uy * 4, 14, 10)
        p.part(head, EEL, p.sphere(hx + ux * 2, hy - 2, 14, 10))
        jaw = p.ell(hx + ux * 6, hy + 6, 11, 4)
        p.part(jaw, BELLY, p.sphere(hx + ux * 6, hy + 5, 11, 4))
        p.part(p.seg(hx - 2, hy + 3, hx + 16 * ux, hy + 3 + 2 * uy, 1.4), MOUTH, 0.1, bevel=0)
        eyes(p, [(hx + 2, hy - 4)], 2.6, pose)
    nsp = {"idle": 4, "attack": 9, "struck": 3}[pose]
    rng = np.random.RandomState(17)
    for k in range(nsp):  # crackle: little lightning forks off the wire
        i = int(rng.randint(1, len(path) - 1))
        x, y = path[i]
        pts = [(x, y)]
        for _ in range(4):
            x, y = x + rng.uniform(-6, 6), y - rng.uniform(4, 8)
            pts.append((x, y))
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            p.glow(p.seg(ax, ay, bx, by, 1.4), "#9fe8ff" if k % 2 else "#e2f6ff")
    for k, (rx, ry) in enumerate(((16, 3.5), (26, 5.5))):  # ripples on the black water where it rises
        ring = p.ell(20, 123, rx, ry) & ~p.ell(20, 123, rx - 1.6, ry - 1.2) & ~m & (p.y < 127)
        p.part(ring, GLASS, 0.7 - 0.25 * k, bevel=0)
    if pose == "struck":
        sparks(p, path[-2][0], path[-2][1], 26, 9)


def barrel_knight(p: Painter, pose: str) -> None:
    """A skeleton armoured in a barrel: an oak barrel for a breastplate, iron hoops, a skull with ember eyes, bone arms and legs, a mop-handle lance."""
    tilt = {"idle": 0, "attack": -4, "struck": 6}[pose]
    for sx in (-1, 1):  # legs
        p.part(p.seg(64 + sx * 9, 98, 64 + sx * 12, 122, 6), BONE, p.lin(56, 98, 72, 122, 0.7, 0.35))
        p.part(p.ell(64 + sx * 13, 123, 7, 3.5), BONE, 0.45)
    bar = p.ell(64, 74, 26, 30) & p.rect(30, 48, 98, 104)
    stave = (np.floor((p.x - 38) / 6.5) % 2 == 0).astype(np.float32)
    p.part(bar, OAK, p.sphere(62, 72, 28, 34, 0.2) + 0.08 * stave + (p.noise(3, 5) - 0.5) * 0.12)
    p.part(bar & ((p.x - 38) % 6.5 < 1.0), OAK, 0.12, bevel=0)
    for hy in (56, 76, 96):
        p.part(bar & (np.abs(p.y - hy) < 2.2), IRON, p.sphere(62, hy, 28, 6, 0.2))
    p.part(p.ell(64, 49, 25, 5) & (p.y < 50), OAK, 0.85)  # the barrel's rim
    p.part(p.ell(64, 50, 21, 3.5), OAK, 0.1, bevel=0)
    # the lance (a mop handle): idle upright at his side, attack levelled at you, struck knocked askew
    if pose == "idle":
        ax, ay, bx, by = 100, 122, 98, 14
    elif pose == "attack":
        ax, ay, bx, by = 104, 88, 22, 46
    else:
        ax, ay, bx, by = 104, 120, 122, 32
    p.part(p.seg(ax, ay, bx, by, 4), OAK, p.lin(ax - 2, ay, ax + 2, ay, 0.8, 0.4) + 0.05)
    mop = p.ell(bx, by, 9, 7)
    p.part(mop, MOP, p.sphere(bx, by, 9, 7) - 0.25 * ((p.x.astype(int) % 3) == 0))
    for sx, (hx, hy) in ((-1, (34, 70)), (1, (98, 76 if pose != "attack" else 66))):  # arms
        sh_x = 64 + sx * 22
        p.part(p.seg(sh_x, 54, hx, hy, 5), BONE, 0.6)
        p.part(p.ell(hx, hy, 4.5, 4.5), BONE, p.sphere(hx, hy, 4.5, 4.5))
    if pose == "idle":
        p.part(p.seg(98, 76, 100, 68, 5), BONE, 0.6)
    # the skull
    cx, cy = 64 + tilt, 30 + abs(tilt) * 0.3
    p.part(p.ell(cx, cy, 15, 16), BONE, p.sphere(cx, cy - 2, 15, 16))
    jaw_drop = 6 if pose == "attack" else 0
    p.part(p.rect(cx - 9, cy + 9 + jaw_drop, cx + 9, cy + 17 + jaw_drop), BONE, 0.55)
    if jaw_drop:
        p.part(p.rect(cx - 8, cy + 9, cx + 8, cy + 9 + jaw_drop), MOUTH, 0.1, bevel=0)
    for tx in range(-7, 8, 4):
        p.part(p.rect(cx + tx, cy + 9 + jaw_drop, cx + tx + 1.2, cy + 15 + jaw_drop), BONE, 0.1, bevel=0)
    p.part(p.poly([(cx - 1.5, cy + 4), (cx + 1.5, cy + 4), (cx, cy + 1)]), MOUTH, 0.1, bevel=0)
    for sx in (-1, 1):
        p.part(p.ell(cx + sx * 6, cy - 1, 5, 4.5), MOUTH, 0.15, bevel=0)
    eyes(p, [(cx - 6, cy - 1), (cx + 6, cy - 1)], 2.0, pose, idle=("#c84a18", "#f8a040"), shut_pal=BONE)
    p.part(p.ell(cx, cy - 13, 13, 4) & (p.y < cy - 11), IRON, 0.6)  # a pot-lid helmet
    if pose == "struck":
        sparks(p, cx, cy, 24, 11)


def mildew_mother(p: Painter, pose: str) -> None:
    """A mound of wet fur and fungus heaving itself upright: a shaggy body, glowing caps growing on it, a cluster of small eyes, a mouth that breathes spores."""
    top = {"idle": 16, "attack": 6, "struck": 32}[pose]
    mound = p.ell(64, 126, 60, 126 - top) | p.ell(64, top + 22, 34, 24)
    fur(p, mound, FUR, p.sphere(56, (top + 126) / 2 - 10, 62, (126 - top) * 0.8, 0.15) + 0.05, 41, 0.25)
    for sx in (-1, 1):  # two heavy arms of moss
        ay = top + 46
        hand = (64 + sx * 52, ay + (-24 if pose == "attack" else 30))
        m, sh = p.tube([(64 + sx * 34, ay), (64 + sx * 48, ay + 10), hand], 11, 8)
        fur(p, m, FUR, sh * 0.9, 43 + sx, 0.2)
    rng = np.random.RandomState(45)
    caps = [(34, top + 30, 9), (92, top + 26, 11), (70, top + 4, 7), (24, top + 64, 7), (104, top + 60, 8), (52, top + 70, 6), (80, top + 82, 7)]
    for (x, y, r) in caps:  # mushroom caps growing out of the fur
        p.part(p.rect(x - 1.5, y, x + 1.5, y + r * 0.9), BONE, 0.5, bevel=0)
        cap = p.ell(x, y, r, r * 0.6) & (p.y <= y + 1)
        p.part(cap, FUNG, p.sphere(x - 1, y - 2, r, r * 0.6) + 0.1)
        p.glow(p.ell(x - r * 0.35, y - r * 0.25, 1.2, 1.0), "#c8ffc0")
    ex = [(54, top + 26), (64, top + 22), (74, top + 26), (59, top + 33), (69, top + 33)]
    eyes(p, ex, 2.0, pose, idle=("#3cb85a", "#c8ffc0"), shut_pal=FUR)
    my = top + 46
    if pose == "attack":
        p.part(p.ell(64, my, 14, 10), MOUTH, p.lin(64, my - 10, 64, my + 10, 0.9, 0.1), bevel=0)
        for k in range(70):  # the spore cloud
            x, y = rng.uniform(20, 108), rng.uniform(top - 12, my + 6)
            if np.hypot(x - 64, (y - my) * 1.4) < 46:
                p.glow(p.rect(x, y, x + 1.8, y + 1.8), "#9ae8a0" if k % 3 else "#3cb85a")
    else:
        p.part(p.ell(64, my, 10, 3 if pose == "idle" else 2), MOUTH, 0.15, bevel=0)
        for k in range(10):  # spores drifting off it
            x, y = rng.uniform(16, 112), rng.uniform(top - 14, top + 30)
            p.glow(p.rect(x, y, x + 1.6, y + 1.6), "#9ae8a0")
    if pose == "struck":
        sparks(p, 64, top + 30, 34, 13)


def _person(p: Painter, pal, pose, hands, legs_apart=8, head=(64, 18, 9, 10)):
    """A slim standing figure (head 1/7 of the height): torso, hips, legs and arms to the given hands; shaded by `pal`. Returns the body mask."""
    hx, hy, hrx, hry = head
    body = p.ell(64, 40, 18, 10) | p.poly([(47, 38), (81, 38), (76, 62), (77, 74), (51, 74), (52, 62)])
    for sx in (-1, 1):
        m, sh = p.tube([(64 + sx * 6, 74), (64 + sx * (legs_apart + 2), 98), (64 + sx * (legs_apart + 4), 122)], 6.5, 4.5)
        p.part(m, pal, sh * 0.9)
        p.part(p.ell(64 + sx * (legs_apart + 6), 123, 7, 3.2), pal, 0.35)
    p.part(body, pal, p.sphere(62, 46, 24, 30, 0.15))
    p.part(p.rect(57, 26, 71, 34), pal, 0.45)
    for sx, (ex, ey, wx, wy) in ((-1, hands[0]), (1, hands[1])):
        m, sh = p.tube([(64 + sx * 16, 36), (ex, ey), (wx, wy)], 5.0, 4.0)
        p.part(m, pal, sh)
        p.part(p.ell(wx, wy, 5, 5.5), pal, p.sphere(wx, wy, 5, 5.5) + 0.1)
    p.part(p.ell(hx, hy, hrx, hry), pal, p.sphere(hx - 1, hy - 1, hrx, hry))
    return body


def mirror_twin(p: Painter, pose: str) -> None:
    """You, in mirror glass: a figure of your height with its hands up to play, glass blue with diagonal glints and a crack; it grins half a beat early."""
    if pose == "idle":
        hands = ((34, 52, 40, 34), (94, 52, 88, 34))
    elif pose == "attack":
        hands = ((30, 46, 26, 26), (98, 46, 102, 26))
    else:
        hands = ((36, 58, 28, 76), (92, 58, 104, 70))
    head = (64, 18, 9, 10) if pose != "struck" else (70, 20, 9, 10)
    _person(p, GLASS, pose, hands, 9, head)
    hx, hy = head[0], head[1]
    hair = p.ell(hx, hy - 5, 10, 7) & (p.y < hy - 5) | p.poly([(hx - 9, hy - 7), (hx - 4, hy - 16), (hx + 1, hy - 9), (hx + 7, hy - 15), (hx + 9, hy - 6)])
    p.part(hair, GLASS, p.sphere(hx - 3, hy - 10, 11, 8) * 0.8)
    band = p.ell(hx, hy - 2, 12, 12) & ~p.ell(hx, hy - 2, 10, 10) & (p.y < hy - 2)  # the player's own headphones, in glass
    p.part(band, STEEL, 0.6, bevel=0)
    for sx in (-1, 1):
        p.part(p.ell(hx + sx * 10, hy, 3.5, 5), STEEL, p.sphere(hx + sx * 10 - 1, hy - 1, 3.5, 5))
    glint = (((p.x + p.y * 0.8) % 30.0) < 2.5) & p.a & (p.rid == p._rid(GLASS))
    p.glow(glint & (p.lvl >= 2), "#d8e8f4")
    p.part(glint & (p.lvl < 2), GLASS, 0.75, bevel=0)
    crack = p.seg(60, 6, 54, 30, 1.3) | p.seg(54, 30, 66, 48, 1.3) | p.seg(66, 48, 58, 74, 1.3) | p.seg(66, 48, 78, 56, 1.3)
    if pose == "struck":
        crack |= p.seg(58, 74, 70, 100, 1.4) | p.seg(54, 30, 40, 40, 1.4) | p.seg(70, 100, 60, 120, 1.4)
    p.part(crack & p.a, GLASS, 0.05, bevel=0)
    eyes(p, [(hx - 4, hy - 1), (hx + 4, hy - 1)], 1.6, pose, idle=("#d8ccb4", "#d8ccb4"), shut_pal=GLASS)
    if pose == "attack":
        p.part(p.ell(hx, hy + 5, 5, 3), MOUTH, 0.1, bevel=0)
    else:
        p.glow(p.rect(hx - 4.5, hy + 4, hx + 4.5, hy + 5.6), "#d8ccb4")  # the grin
    if pose == "struck":
        rng = np.random.RandomState(21)
        for _ in range(9):  # shards flying off
            x, y = rng.uniform(20, 110), rng.uniform(20, 110)
            s = rng.uniform(3, 6)
            p.part(p.poly([(x, y), (x + s, y + s * 0.4), (x + s * 0.3, y + s)]), GLASS, 0.8, bevel=0)
        sparks(p, 64, 50, 34, 23)


def bouncer(p: Painter, pose: str) -> None:
    """Gristle the troll bouncer: wide shoulders, a dark suit under a hi-vis vest, a small head with tusks and a heavy brow, an earpiece, the clipboard."""
    hx = {"idle": 64, "attack": 62, "struck": 70}[pose]
    hy = {"idle": 20, "attack": 22, "struck": 18}[pose]
    for sx in (-1, 1):  # legs and boots
        m, sh = p.tube([(64 + sx * 16, 94), (64 + sx * 19, 108), (64 + sx * 19, 118)], 10, 8)
        p.part(m, SUIT, sh * 0.8)
        p.part(p.ell(64 + sx * 20, 121, 12, 5.5), SUIT, p.sphere(64 + sx * 20 - 3, 119, 12, 5.5) * 0.6)
    torso = p.ell(64, 48, 46, 16) | p.poly([(20, 46), (108, 46), (98, 100), (30, 100)])
    p.part(torso, SUIT, p.sphere(60, 56, 50, 50, 0.15))
    vest = p.poly([(30, 38), (98, 38), (92, 98), (36, 98)])
    p.part(vest, HIVIS, p.sphere(58, 60, 44, 46, 0.2))
    p.part(vest & (np.abs(p.y - 74) < 4), REFL, p.lin(36, 70, 92, 78, 0.95, 0.4))
    p.part(vest & (np.abs(p.x - 64) < 1.2) & (p.y < 70), HIVIS, 0.2, bevel=0)
    p.part(p.poly([(54, 36), (74, 36), (64, 52)]), SUIT, 0.3)  # the collar of the suit
    if pose == "attack":  # one fist up: "outside"
        arm_l = [(24, 42), (14, 26), (20, 8)]
        fist_l = (20, 8)
    else:
        arm_l = [(24, 42), (14, 66), (18, 92)]
        fist_l = (18, 92)
    m, sh = p.tube(arm_l, 10, 8)
    p.part(m, SUIT, sh * 0.85)
    p.part(p.ell(*fist_l, 9, 9), TROLL, p.sphere(fist_l[0] - 2, fist_l[1] - 2, 9, 9))
    arm_r = [(104, 42), (112, 66), (106, 84)] if pose != "struck" else [(104, 42), (116, 52), (122, 40)]
    m, sh = p.tube(arm_r, 10, 8)
    p.part(m, SUIT, sh * 0.85)
    cb = (96, 74) if pose != "struck" else (112, 18)
    board = p.rect(cb[0] - 12, cb[1] - 6, cb[0] + 12, cb[1] + 26)
    p.part(board, BOARD, 0.55)
    p.part(p.rect(cb[0] - 9, cb[1] - 1, cb[0] + 9, cb[1] + 23), PAPER, p.lin(cb[0] - 9, cb[1], cb[0] + 9, cb[1] + 23, 0.95, 0.6))
    for ly in range(4, 22, 4):
        p.part(p.rect(cb[0] - 7, cb[1] + ly, cb[0] + 5, cb[1] + ly + 1), PAPER, 0.05, bevel=0)
    p.part(p.rect(cb[0] - 4, cb[1] - 8, cb[0] + 4, cb[1] - 4), IRON, 0.6)
    p.part(p.ell(*arm_r[-1], 8, 8), TROLL, p.sphere(arm_r[-1][0] - 2, arm_r[-1][1] - 2, 8, 8))
    # the head on a thick neck
    p.part(p.rect(hx - 10, hy + 10, hx + 10, hy + 20), TROLL, 0.4)
    p.part(p.ell(hx, hy, 15, 14), TROLL, p.sphere(hx - 2, hy - 2, 15, 14))
    p.part(p.ell(hx + 15, hy + 1, 3, 4), TROLL, 0.5)
    p.part(p.ell(hx - 15, hy + 1, 3, 4), TROLL, 0.6)
    brow = p.rect(hx - 12, hy - 6 + (2 if pose == "attack" else 0), hx + 12, hy - 2 + (2 if pose == "attack" else 0))
    p.part(brow, TROLL, 0.3)
    eyes(p, [(hx - 6, hy + 1), (hx + 6, hy + 1)], 2.2, pose, idle=("#d0a020", "#f8e070"), shut_pal=TROLL)
    my = hy + 8
    if pose == "attack":
        p.part(p.rect(hx - 7, my - 1, hx + 7, my + 5), MOUTH, 0.1, bevel=0)
    else:
        p.part(p.rect(hx - 6, my, hx + 6, my + 1.5), MOUTH, 0.1, bevel=0)
    for sx in (-1, 1):  # tusks
        p.part(p.poly([(hx + sx * 6 - 1.5, my + 1), (hx + sx * 6 + 1.5, my + 1), (hx + sx * 5, my - 5)]), HORN, 0.85, bevel=0)
    p.part(p.seg(hx + 15, hy + 4, hx + 18, hy + 20, 1.3), IRON, 0.4, bevel=0)  # the earpiece lead
    p.glow(p.rect(hx + 13.5, hy, hx + 16, hy + 3), "#9fe8ff")
    if pose == "struck":
        sparks(p, hx, hy, 26, 27)


def rat_king(p: Painter, pose: str) -> None:
    """The Rat King: a knot of rats risen on their tails, six heads (pink ears, red eyes), a crown of bottle tops on the middle one."""
    rise = {"idle": 0, "attack": -10, "struck": 12}[pose]
    for k in range(7):  # the knot of tails underneath
        a0 = k / 7 * np.pi
        pts = [(64 + np.cos(a0) * 30, 108), (64 + np.cos(a0 + 1.4) * 22, 118), (64 + np.cos(a0 + 2.6) * 34, 124), (64 + np.cos(a0 + 3.4) * 44, 120)]
        m, sh = p.tube(pts, 2.4, 1.6)
        p.part(m, PINK, sh * 0.8)
    mass = p.ell(64, 92 + rise * 0.3, 44, 24)
    fur(p, mass, RAT, p.sphere(58, 86 + rise * 0.3, 46, 26, 0.15), 51, 0.2)
    heads = [(26, 72), (44, 58), (64, 50), (84, 58), (102, 72), (64, 78)]
    for i, (x, y) in enumerate(heads):
        y = y + rise * (0.6 if i != 5 else 0.3)
        lean = (x - 64) * (0.2 if pose == "attack" else 0.0)
        x = x + lean
        for sx in (-1, 1):
            p.part(p.ell(x + sx * 7, y - 7, 4.5, 5), PINK, p.sphere(x + sx * 7 - 1, y - 8, 4.5, 5))
        p.part(p.ell(x, y, 11, 9), RAT, p.sphere(x - 2, y - 2, 11, 9))
        p.part(p.ell(x, y + 6, 6, 5), RAT, p.sphere(x - 1, y + 5, 6, 5) + 0.1)
        if pose == "attack":
            p.part(p.ell(x, y + 10, 4, 3), MOUTH, 0.1, bevel=0)
            p.part(p.rect(x - 2, y + 7.5, x + 2, y + 9.5), BONE, 0.9, bevel=0)
        p.part(p.ell(x, y + 9, 1.8, 1.5), PINK, 0.8, bevel=0)
        eyes(p, [(x - 4, y - 1), (x + 4, y - 1)], 1.5, pose, idle=("#d02820", "#ff8060"), shut_pal=RAT)
        for sx in (-1, 1):  # whiskers
            p.part(p.seg(x + sx * 5, y + 7, x + sx * 13, y + 5, 0.9), RAT, 0.85, bevel=0)
    cx, cy = heads[2][0], heads[2][1] + rise * 0.6 - 12
    if pose == "struck":
        cx, cy = cx + 14, cy - 10
    for k in range(5):  # the crown of bottle tops
        x = cx - 12 + k * 6
        p.part(p.poly([(x - 3, cy + 4), (x + 3, cy + 4), (x + 2, cy - 3), (x, cy - 6), (x - 2, cy - 3)]), GOLD, p.sphere(x - 1, cy - 1, 4, 6) + 0.1)
    p.part(p.rect(cx - 15, cy + 2, cx + 15, cy + 6), GOLD, 0.6)
    if pose == "struck":
        sparks(p, 64, 62, 30, 29)


def furnace_imp(p: Painter, pose: str) -> None:
    """The Furnace Imp, the kitchens' chef: red, horned, a white toque and apron, a forked tail, knives spinning in the air."""
    tail = [(78, 110), (100, 112), (112, 100), (108, 88)]
    m, sh = p.tube(tail, 3.2, 2.0)
    p.part(m, IMP, sh)
    p.part(p.poly([(104, 86), (114, 82), (112, 92)]), IMP, 0.6)
    for sx in (-1, 1):
        p.part(p.seg(64 + sx * 8, 100, 64 + sx * 11, 120, 7), IMP, 0.45)
        p.part(p.ell(64 + sx * 13, 122, 8, 4), IMP, 0.25)
    body = p.ell(64, 88, 20, 22)
    p.part(body, IMP, p.sphere(60, 84, 21, 24))
    apron = p.poly([(50, 76), (78, 76), (82, 108), (46, 108)])
    p.part(apron, CHEF, p.lin(50, 76, 80, 108, 0.85, 0.45))
    p.part(apron & (np.abs(p.y - 92) < 1.0), CHEF, 0.3, bevel=0)
    if pose == "attack":  # winding up to throw
        arm_l, arm_r = [(46, 80), (32, 66), (26, 46)], [(82, 80), (96, 86), (106, 78)]
    elif pose == "struck":
        arm_l, arm_r = [(46, 80), (30, 72), (22, 58)], [(82, 80), (98, 70), (104, 56)]
    else:
        arm_l, arm_r = [(46, 80), (34, 86), (30, 74)], [(82, 80), (96, 76), (100, 62)]
    for arm in (arm_l, arm_r):
        m, sh = p.tube(arm, 4.5, 3.5)
        p.part(m, IMP, sh)
        p.part(p.ell(*arm[-1], 4.5, 4.5), IMP, p.sphere(arm[-1][0] - 1, arm[-1][1] - 1, 4.5, 4.5))
    hy = 50 if pose != "struck" else 54
    head = p.ell(64, hy, 19, 16)
    p.part(head, IMP, p.sphere(60, hy - 3, 19, 16))
    for sx in (-1, 1):
        p.part(p.poly([(64 + sx * 10, hy - 10), (64 + sx * 18, hy - 22), (64 + sx * 15, hy - 8)]), HORN, 0.7)
        p.part(p.poly([(64 + sx * 19, hy - 2), (64 + sx * 28, hy - 8), (64 + sx * 20, hy + 4)]), IMP, 0.5)  # pointed ears
    eyes(p, [(57, hy - 1), (71, hy - 1)], 3.0, pose, idle=("#f0c040", "#fff0a0"), shut_pal=IMP)
    grin = p.ell(64, hy + 8, 10, 5) & (p.y > hy + 7)
    p.part(grin, MOUTH, 0.1, bevel=0)
    for tx in range(-7, 8, 4):
        p.part(p.rect(64 + tx, hy + 8, 64 + tx + 2, hy + 10.5), BONE, 0.9, bevel=0)
    if pose != "struck":  # the toque
        p.part(p.rect(52, hy - 20, 76, hy - 10), CHEF, 0.55)
        p.part(p.ell(64, hy - 28, 15, 11), CHEF, p.sphere(60, hy - 31, 15, 11) + 0.1)
    else:
        p.part(p.ell(94, 16, 13, 9) | p.rect(84, 20, 104, 28), CHEF, p.sphere(90, 14, 13, 9) + 0.1)
    knives = {"idle": [(20, 30, 0.3), (104, 22, -0.4), (40, 12, 1.2)], "attack": [(26, 30, -0.2), (106, 70, 1.57), (66, 6, 0.6)],
              "struck": [(18, 96, 1.0), (40, 114, -0.6), (110, 110, 0.2)]}[pose]
    for (x, y, a) in knives:
        c, s = np.cos(a), np.sin(a)
        blade = p.seg(x, y, x + s * 14, y - c * 14, 3.2)
        p.part(blade, STEEL, 0.8)
        p.part(p.seg(x, y, x - s * 6, y + c * 6, 3.4), OAK, 0.5)
    if pose == "struck":
        sparks(p, 64, hy, 28, 31)


def gargoyle(p: Painter, pose: str) -> None:
    """The Hushing Gargoyle: a crouched stone beast with bat wings, horns and a heavy jaw, a finger pressed to its lips; it swings a stone fist."""
    flare = {"idle": 0, "attack": -12, "struck": 10}[pose]
    for sx in (-1, 1):  # bat wings
        X = lambda v: 64 + sx * v  # noqa: E731
        wing = p.poly([(X(14), 48), (X(40), 20 + flare), (X(62), 8 + flare), (X(58), 34 + flare * 0.5), (X(62), 52 + flare * 0.3), (X(46), 50), (X(48), 68), (X(30), 62), (X(20), 70)])
        p.part(wing, STONE, p.lin(X(20), 30, X(56), 66, 0.55, 0.15) + (p.noise(5, 61 + sx) - 0.5) * 0.15)
        for t in (0.0, 0.5, 1.0):  # wing bones
            p.part(p.seg(X(14), 48, X(40 + 22 * t), 14 + flare + 24 * t, 2.2), STONE, 0.6, bevel=0)
    body = p.poly([(40, 52), (88, 52), (98, 96), (90, 120), (38, 120), (30, 96)])
    p.part(body, STONE, p.sphere(60, 76, 40, 44, 0.15) + (p.noise(4, 63) - 0.5) * 0.15)
    for sx in (-1, 1):  # haunches and clawed feet
        p.part(p.ell(64 + sx * 26, 106, 16, 16), STONE, p.sphere(64 + sx * 26 - 4, 102, 16, 16))
        for c in (-6, 0, 6):
            p.part(p.poly([(64 + sx * 26 + c - 2.5, 118), (64 + sx * 26 + c + 2.5, 118), (64 + sx * 26 + c, 125)]), STONE, 0.5)
    moss = (p.noise(5, 67) > 0.68) & p.a & (p.y > 80)
    p.part(moss, MOSS, 0.5, bevel=0)
    hy = 38 if pose != "struck" else 42
    hxx = 64 if pose != "struck" else 70
    for sx in (-1, 1):
        p.part(p.poly([(hxx + sx * 8, hy - 10), (hxx + sx * 20, hy - 26), (hxx + sx * 14, hy - 6)]), STONE, 0.75)
    p.part(p.ell(hxx, hy, 16, 15), STONE, p.sphere(hxx - 3, hy - 3, 16, 15))
    p.part(p.rect(hxx - 12, hy - 6, hxx + 12, hy - 2), STONE, 0.3)  # heavy brow
    eyes(p, [(hxx - 6, hy - 1), (hxx + 6, hy - 1)], 2.4, pose, idle=("#e86a30", "#ffc070"), shut_pal=STONE)
    if pose == "attack":
        p.part(p.ell(hxx, hy + 9, 9, 5), MOUTH, 0.1, bevel=0)
        for tx in (-6, -2, 2, 6):
            p.part(p.poly([(hxx + tx - 1.5, hy + 5), (hxx + tx + 1.5, hy + 5), (hxx + tx, hy + 9)]), BONE, 0.8, bevel=0)
        m, sh = p.tube([(84, 60), (108, 44), (114, 20)], 7, 6)  # the swinging fist
        p.part(m, STONE, sh)
        p.part(p.ell(114, 16, 11, 10), STONE, p.sphere(111, 13, 11, 10))
        m, sh = p.tube([(44, 60), (30, 78), (40, 92)], 7, 6)
        p.part(m, STONE, sh)
    else:
        p.part(p.rect(hxx - 7, hy + 8, hxx + 7, hy + 9.5), MOUTH, 0.1, bevel=0)
        m, sh = p.tube([(86, 58), (104, 74), (92, 86), (hxx + 7, hy + 22)], 7, 6)  # the arm bent up to the lips
        p.part(m, STONE, sh)
        p.part(p.ell(hxx + 5, hy + 20, 7, 6), STONE, p.sphere(hxx + 3, hy + 18, 7, 6))
        p.part(p.rect(hxx - 1.5, hy + 4, hxx + 2.5, hy + 18), STONE, p.lin(hxx - 1, hy, hxx + 3, hy, 0.9, 0.5))  # the finger
        m, sh = p.tube([(44, 60), (32, 82), (40, 98)], 7, 6)
        p.part(m, STONE, sh)
    cracks = p.seg(56, 64, 62, 80, 1.2) | p.seg(62, 80, 58, 96, 1.2) | p.seg(76, 70, 84, 86, 1.2)
    if pose == "struck":
        cracks |= p.seg(hxx - 4, hy - 14, hxx + 2, hy + 4, 1.4) | p.seg(40, 90, 56, 100, 1.4)
    p.part(cracks & p.a, STONE, 0.02, bevel=0)
    if pose == "struck":
        sparks(p, hxx, hy, 30, 37)


def echo(p: Painter, pose: str) -> None:
    """The Echo: a figure made of your own footsteps and breath, pale blue, see-through toward its feet (a dither of holes), rings of sound around it."""
    if pose == "idle":
        hands = ((36, 50, 40, 32), (92, 50, 88, 32))
    elif pose == "attack":
        hands = ((34, 44, 30, 26), (94, 44, 98, 26))
    else:
        hands = ((38, 56, 30, 72), (90, 56, 98, 72))
    head = (64, 18, 9, 10) if pose != "struck" else (64, 22, 9, 10)
    _person(p, ECHO, pose, hands, 8, head)
    hx, hy = head[0], head[1]
    eyes(p, [(hx - 4, hy - 1), (hx + 4, hy - 1)], 1.6, pose, idle=("#d8ccb4", "#d8ccb4"), shut_pal=ECHO)
    if pose == "attack":
        p.part(p.ell(hx, hy + 5, 4, 3.5), ECHO, 0.0, bevel=0)
    else:
        p.part(p.rect(hx - 3, hy + 4.5, hx + 3, hy + 5.8), ECHO, 0.05, bevel=0)
    nring = {"idle": 3, "attack": 5, "struck": 2}[pose]
    for k in range(nring):  # rings of sound spreading round it
        r = 34 + k * 12
        ring = p.ell(64, 108, r * 1.15, r * 0.32) & ~p.ell(64, 108, r * 1.15 - 2, r * 0.32 - 1.4)
        p.part(ring & ~p.a & ((p.x.astype(int) + p.y.astype(int)) % 3 != 0), ECHO, 0.85 - k * 0.12, bevel=0)
    if pose == "attack":
        for k in range(3):  # the scream: arcs out of the mouth
            r = 8 + k * 6
            arc = p.ell(hx, hy + 6, r, r * 0.7) & ~p.ell(hx, hy + 6, r - 1.6, r * 0.7 - 1.2) & (p.y > hy + 8)
            p.part(arc & ~p.a, ECHO, 0.9, bevel=0)
    # see-through: holes grow toward the feet (and everywhere when struck), on the 4 x 4 dither
    fade = np.clip((p.y - 70) / 52, 0, 1) * 0.85 if pose != "struck" else 0.25 + np.clip((p.y - 40) / 80, 0, 1) * 0.65
    p.holes((p.bayer + 0.5) < fade)
    if pose == "struck":
        sparks(p, 64, 46, 32, 41)


CREATURES = {"lampmoth": lampmoth, "cable_eel": cable_eel, "barrel_knight": barrel_knight, "mildew_mother": mildew_mother, "mirror_twin": mirror_twin, "bouncer": bouncer,
             "rat_king": rat_king, "furnace_imp": furnace_imp, "gargoyle": gargoyle, "echo": echo}
POSES = ("idle", "attack", "struck")


def frame(name: str, pose: str = "idle", n: int = 128) -> np.ndarray:
    """One frame of a creature as an n x n RGBA array (hard alpha). The struck pose is lifted two steps on every ramp."""
    p = Painter(n)
    CREATURES[name](p, pose)
    return p.finish(lift=2 if pose == "struck" else 0)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in CREATURES:
        for k, pose in enumerate(("idle", "struck")):
            Image.fromarray(frame(name, pose, S), "RGBA").save(OUT / f"{name}_{k}.png", optimize=False, compress_level=9)
        print("wrote", f"assets/trial/art/{name}_0.png and _1.png")


if __name__ == "__main__":
    main()
