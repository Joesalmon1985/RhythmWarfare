"""The Ember Road's billboard textures (docs/THREE_PATHS_AND_FACES_PLAN.md section 6): every `thing` and `piece` listed in ember_spec.THINGS for the four
art folders orchard, birch_hall, deep_halls and ash_land, drawn procedurally in the style of tex_bassment / tex_underworld.

Things are 128 x 128 RGBA with HARD alpha (the engine uses an alpha scissor), the prop standing on the bottom edge and centred, with a one-pixel darker edge of
the local colour. Pieces may be 256 x 128 and may carry soft partial alpha (the engine alpha-blends them). The Ember is one drawing function shared by the three
maps (and the altar version in the ash land only adds the black stone under it), so it is identical wherever it appears.
No text, letters, runes or symbols anywhere. Deterministic: every random value comes from a seeded generator.

`build(art)` writes assets/story/<art>/textures/<id>.png for every billboard of that art and returns {id: {file, size, metres}}.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.story.art import ember_spec  # noqa: E402
from tools.story.art.pixeltex import BAYER8, bricks, hexc, noise, quantise, ramp  # noqa: E402
from tools.story.art.tex_underworld import Sprite  # noqa: E402

TWO_PI = 2 * math.pi

# ---- palettes (dark to light) ------------------------------------------------------------------------------------------------------------------------
BARK = ramp("#0c0806", "#1c1410", "#2e2218", "#463524", "#614a30", "#7e6340")
OAK = ramp("#1a0e07", "#331d0e", "#502f18", "#70462a", "#946438", "#bc8a50")
LEAF = ramp("#08180a", "#10281a", "#1a3e20", "#2a5c28", "#437c2c", "#6c9c38")
GOLDLEAF = ramp("#3a2406", "#6e4a0e", "#a87a18", "#d4a424", "#f0cc48")
APPLE = ramp("#30060a", "#600c10", "#961618", "#c82820", "#ec5238", "#ff9070")
WICKER = ramp("#24160a", "#46300f", "#725420", "#a07e34", "#cca852", "#e8cc7c")
PEWTER = ramp("#14161c", "#2c2f38", "#505560", "#7c828e", "#a8aeb8", "#d8dce2")
IRON = ramp("#07080b", "#12141a", "#1e2128", "#2e323c", "#444a58", "#5e6676")
STONE = ramp("#100e0c", "#221f1b", "#383430", "#524d46", "#6e685e", "#948e82")
WARM = ramp("#4a1c06", "#8a3c0a", "#d06a14", "#f8a030", "#ffd466", "#fff2b0")
NIGHTW = ramp("#02060c", "#07121e", "#0e2434", "#1a3c52", "#33647e", "#8cc0d4", "#d8f0f8")
HAY = ramp("#30220a", "#5a4010", "#8c6a1c", "#bc9430", "#dcb84a", "#f0da7c")
BIRCH = ramp("#262b38", "#4c5468", "#7c88a0", "#b4bed0", "#e0e6f0", "#fafcff")
SNOW = ramp("#34446a", "#5e78a4", "#90a8cc", "#c4d4ea", "#e8f0fa", "#ffffff")
SPRUCE = ramp("#030e0c", "#081e1a", "#10342c", "#1a4c3e", "#286450", "#3c7e66")
SLATE = ramp("#05070d", "#0c1018", "#161c2a", "#222a3c", "#34405a", "#4e5e80")
COLD = ramp("#0e2234", "#1e4c68", "#3e86a8", "#7ccce4", "#bcf0fa", "#f4ffff")
WETROCK = ramp("#030408", "#080a10", "#10131c", "#1a1f2c", "#283040", "#3e4a5e")
WHITEW = ramp("#26364c", "#50667e", "#8aa2ba", "#c4d6e6", "#eef6fc", "#ffffff")
TEAL = ramp("#020e0d", "#051e1c", "#0a3834", "#125a52", "#1c8074", "#40b09a")
BIOLUM = ramp("#082818", "#146438", "#2eb458", "#7ae88c", "#c8ffc4", "#f0fff0")
BRONZE = ramp("#140e06", "#2e2008", "#5a4010", "#8a6a1c", "#b8942c", "#e0c060")
PATINA = ramp("#0c1c18", "#1a3e34", "#2e6a58", "#4e9a7c", "#84c6a4", "#b8e8c8")
ASH = ramp("#0c0a0a", "#1e1a1a", "#352f2e", "#524a48", "#746a66", "#9c928c")
BLACKST = ramp("#020203", "#08080c", "#101016", "#1a1a22", "#272630", "#38364a")
REDGLOW = ramp("#180404", "#420a08", "#801808", "#c2300c", "#ee5a14", "#ff9a3c")
HEAT = ramp("#3a0a04", "#8a1a06", "#e0480a", "#ff9a20", "#ffe070")
EMBER = ramp("#2a0804", "#5a1006", "#a02208", "#e04a0c", "#ff8a1c", "#ffc83c", "#fff2a0", "#fffde8")
HALO = ramp("#6a1608", "#a02a0a", "#d8500e", "#f07a1a", "#ffa030")
PALEFLESH = ramp("#141c20", "#2c3c44", "#54666e", "#8a9ca2", "#c0d0d2", "#eef4f0")
CLOTH = ramp("#1c1c20", "#383a40", "#585a60", "#7a7c82", "#9c9ea4", "#c0c2c6")
CANVAS = ramp("#16181a", "#2c3032", "#464a4c", "#646868", "#848886", "#a4a8a4")
FIRERED = ramp("#2a0606", "#5c0e08", "#a01a0a", "#d83a10", "#f87420", "#ffb040")
SMOKE = ramp("#2a2626", "#443e3e", "#625a58", "#82786f", "#a49a90")

RNG = np.random.RandomState


class Cv(Sprite):
    """A w x 128 RGBA canvas. Masks are shaded through palette ramps with ordered dithering; hard alpha unless `over` is used (pieces)."""

    def __init__(self, w: int = 128, h: int = 128):
        self.w, self.h, self.n = w, h, max(w, h)
        self.rgb = np.zeros((h, w, 3), np.uint8)
        self.a = np.zeros((h, w), np.uint8)
        self.fx = np.zeros((h, w), bool)  # glow / spark pixels exempt from the outline
        yy, xx = np.mgrid[0:h, 0:w]
        self.x = xx.astype(np.float32)
        self.y = yy.astype(np.float32)
        self.bt = BAYER8[yy % 8, xx % 8] + 0.5  # 0..1 ordered-dither thresholds

    # ---- painting ----------------------------------------------------------------------------------------------------------------------------
    def paint(self, mask, shade, pal, fx=False, dither=1.0):
        sh = shade if isinstance(shade, np.ndarray) else np.full((self.h, self.w), float(shade), np.float32)
        col = quantise(np.clip(np.nan_to_num(sh), 0, 1), pal, dither)
        self.rgb[mask] = col[mask]
        self.a[mask] = 255
        self.fx[mask] = fx

    def solid(self, mask, colour, fx=False):
        self.rgb[mask] = (hexc(colour) * 255).astype(np.uint8) if isinstance(colour, str) else np.asarray(colour, np.uint8)
        self.a[mask] = 255
        self.fx[mask] = fx

    def over(self, alpha, colour):
        """Alpha-composite a float alpha field (0..1) of one colour (hex, or an (h, w, 3) uint8 array) onto the canvas: for the soft pieces."""
        c = (hexc(colour) * 255).astype(np.float32) if isinstance(colour, str) else colour.astype(np.float32)
        c = np.broadcast_to(c, (self.h, self.w, 3))
        a1 = np.clip(alpha, 0, 1).astype(np.float32)
        a0 = self.a.astype(np.float32) / 255.0
        ao = a1 + a0 * (1 - a1)
        co = (c * a1[..., None] + self.rgb.astype(np.float32) * (a0 * (1 - a1))[..., None]) / np.maximum(ao, 1e-5)[..., None]
        self.rgb = np.clip(co + 0.5, 0, 255).astype(np.uint8)
        self.a = np.clip(ao * 255 + 0.5, 0, 255).astype(np.uint8)

    # ---- shapes ------------------------------------------------------------------------------------------------------------------------------
    def _im(self):
        return Image.new("L", (self.w, self.h), 0)

    def poly(self, pts):
        im = self._im()
        ImageDraw.Draw(im).polygon([(float(a), float(b)) for a, b in pts], fill=255)
        return np.asarray(im) > 0

    def tri(self, pts):
        return self.poly(pts)

    def stroke(self, pts, w0, w1=None):
        """A tapered polyline (width w0 at the first point to w1 at the last)."""
        w1 = w0 if w1 is None else w1
        pts = [(float(a), float(b)) for a, b in pts]
        seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
        tot = max(sum(seg), 1e-6)
        im = self._im()
        d = ImageDraw.Draw(im)
        acc = 0.0
        ws = [w0]
        for s in seg:
            acc += s
            ws.append(w0 + (w1 - w0) * acc / tot)
        for i, (x, y) in enumerate(pts):
            r = max(ws[i] * 0.5, 0.55)
            d.ellipse([x - r, y - r, x + r, y + r], fill=255)
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            L = max(math.hypot(bx - ax, by - ay), 1e-6)
            nx, ny = -(by - ay) / L, (bx - ax) / L
            ra, rb = max(ws[i] * 0.5, 0.55), max(ws[i + 1] * 0.5, 0.55)
            d.polygon([(ax + nx * ra, ay + ny * ra), (bx + nx * rb, by + ny * rb), (bx - nx * rb, by - ny * rb), (ax - nx * ra, ay - ny * ra)], fill=255)
        return np.asarray(im) > 0

    def ring(self, cx, cy, rx, ry, t):
        return self.ellipse(cx, cy, rx, ry) & ~self.ellipse(cx, cy, rx - t, ry - t)

    def noise(self, scale, seed, octaves=3):
        return noise(self.n, scale, seed, octaves)[:self.h, :self.w]

    def blur(self, mask, r):
        im = Image.fromarray((mask.astype(np.float32) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(r))
        return np.asarray(im).astype(np.float32) / 255.0

    def bump(self, mask, r=5.0, base=0.5, amp=0.5, light=(-0.55, -0.8)):
        """Round-looking shading for any blob, lit from the upper left: a field around `base` to feed `paint`."""
        h = self.blur(mask, r)
        gy, gx = np.gradient(h)
        g = -(gx * light[0] + gy * light[1])
        sc = np.percentile(np.abs(g[mask]), 95) + 1e-6 if mask.any() else 1.0
        return base + amp * np.clip(g / sc, -1, 1) * 0.75 + 0.3 * (h - 0.6)

    def hshade(self, x0, x1, base=0.5, amp=0.35):
        u = np.clip((self.x - x0) / max(x1 - x0, 1), 0, 1)
        return base + amp * (0.6 - u) + 0.1 * np.sin(u * np.pi)

    def glow(self, cx, cy, rx, ry, pal, power=1.3, gain=1.25, dither=0.6, max_alpha=True, only_empty=True, strength=1.0):
        """A dithered glow with hard alpha: pixels switch on by ordered dither where the falloff beats the threshold."""
        d = np.sqrt(((self.x - cx) / rx) ** 2 + ((self.y - cy) / ry) ** 2)
        inten = np.clip(1 - d, 0, 1) ** power * gain * strength
        on = inten > self.bt
        if only_empty:
            on &= self.a == 0
        self.paint(on, inten, pal, fx=True, dither=dither)

    def rgba(self, outline=True, hard=True):
        rgb = self.rgb.copy()
        a = self.a.copy()
        if hard:
            a = np.where(a >= 128, 255, 0).astype(np.uint8)
            rgb[a == 0] = 0
        if outline:
            op = a > 0
            pad = np.pad(op, 1, mode="constant", constant_values=True)
            inner = pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
            edge = op & ~inner & ~self.fx
            dark = np.maximum(rgb.astype(np.float32) * 0.5, np.array([14, 11, 14], np.float32))
            rgb[edge] = dark[edge].astype(np.uint8)
        return np.dstack([rgb, a])


def bez(p0, p1, p2, n=20):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in np.linspace(0, 1, n)]


def bez3(p0, p1, p2, p3, n=24):
    out = []
    for t in np.linspace(0, 1, n):
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0], u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


# ---- the Ember: one drawing for every map ------------------------------------------------------------------------------------------------------------

IRONW = ramp("#0c0a0c", "#1c1618", "#2e2422", "#4a342a", "#7a4a2c", "#c06a30")


def draw_ember(sp: Cv, cx: float, base_y: float) -> None:
    """A fist-sized glowing coal cupped in a small shallow iron bowl standing on `base_y`; yellow-white core, orange-red body, dithered halo, sparks."""
    rim_y = base_y - 20
    cy = rim_y - 11
    # halo first (switches on only where nothing is drawn yet)
    sp.glow(cx, cy - 2, 46, 42, HALO, power=1.5, gain=1.4, dither=0.5)
    # the bowl's far wall behind the coal
    back = sp.ellipse(cx, rim_y, 30, 5) & (sp.y <= rim_y)
    sp.paint(back, 0.18 + 0.2 * np.clip((sp.y - (rim_y - 5)) / 5, 0, 1), IRONW)
    # the coal: an irregular lump, hot core up and to the left, dark cracks and a crust on its underside
    ex, ey = (sp.x - cx) / 22.0, (sp.y - cy) / 18.0
    r = np.sqrt(ex * ex + ey * ey)
    th = np.arctan2(ey, ex)
    lump = 1 + 0.13 * np.sin(3 * th + 1.1) + 0.09 * np.sin(5 * th + 2.3) + 0.05 * np.sin(8 * th + 0.4)
    coal = r < lump
    t = np.clip(1 - r / lump, 0, 1)
    dc = np.sqrt(((sp.x - cx + 3) / 14.0) ** 2 + ((sp.y - cy + 3) / 12.0) ** 2)
    heat = np.clip(1 - dc, 0, 1) ** 0.85 * 0.7 + 0.5 * t ** 0.55 + 0.14
    crack = np.abs(sp.noise(7, 4711, 3) - 0.5) < 0.04
    heat = np.where(crack & (dc > 0.35), heat * 0.55, heat)
    heat += (sp.noise(4, 4712, 2) - 0.5) * 0.16
    heat -= 0.1 * np.clip(((sp.x - cx) * 0.4 + (sp.y - cy) * 0.9) / 16.0, 0, 1)
    heat = np.where(t < 0.1, np.minimum(heat, 0.2), heat)
    sp.paint(coal, np.clip(heat, 0, 1), EMBER, dither=1.0)
    # a few bright flecks on the surface
    sp.solid(coal & (sp.noise(3, 4713, 2) > 0.72) & (dc < 0.9) & (heat > 0.5), "#ffe27a")
    sp.solid(sp.ellipse(cx - 4, cy - 4, 3.2, 2.6) & coal, "#fff6c0")
    # the bowl: shallow, with a lit lip and a short foot
    body = sp.ellipse(cx, rim_y, 30, 14) & (sp.y >= rim_y)
    foot = sp.rect(cx - 10, base_y - 9, cx + 10, base_y + 1)
    footb = sp.ellipse(cx, base_y - 1.5, 15, 3.2)
    glowtop = np.clip(1 - (sp.y - rim_y) / 12.0, 0, 1)
    bs = sp.hshade(cx - 30, cx + 30, 0.34, 0.3) * 0.8 + 0.4 * glowtop ** 1.2 * (1 - np.abs(sp.x - cx) / 36)
    sp.paint(body | foot | footb, np.clip(bs, 0, 1), IRONW)
    lip = sp.ring(cx, rim_y, 31, 5.5, 2.4) & (sp.y >= rim_y - 1)
    sp.paint(lip, 0.82 - 0.2 * (sp.x > cx + 8), IRONW)
    sp.solid(sp.rect(cx - 6, base_y - 1, cx + 6, base_y + 1), "#2a2020")
    # sparks rising on the draught
    rng = RNG(4720)
    sparks = [(7, -43, 2), (-9, -51, 2), (13, -58, 1), (-14, -65, 1), (3, -70, 2), (18, -76, 1), (-4, -84, 1), (10, -91, 1)]
    for dx, dy, s in sparks:
        px, py = cx + dx, cy + dy + 2
        col = "#ffe27a" if dy > -62 else "#ffa22a"
        sp.solid(sp.rect(px, py, px + s, py + s), col, fx=True)
        if s == 2:
            sp.solid(sp.rect(px - 1, py + 3, px, py + 4), "#e0580e", fx=True)
    _ = rng


def th_ember():
    sp = Cv()
    draw_ember(sp, 64, 127)
    return sp.rgba()


def th_ember_altar():
    """The same Ember on a flat black stone whose top face the coal lights red."""
    sp = Cv()
    cx, top = 64, 94
    jit = RNG(4730).uniform(-1.5, 1.5, 12)
    topface = sp.poly([(30 + jit[0], 86 + jit[1]), (98 + jit[2], 86 + jit[3]), (113 + jit[4], 100), (15 + jit[5], 100)])
    front = sp.poly([(15 + jit[5], 100), (113 + jit[4], 100), (110 + jit[6], 127), (18 + jit[7], 127)])
    d = np.sqrt(((sp.x - cx) / 46.0) ** 2 + ((sp.y - 90) / 22.0) ** 2)
    lit = np.clip(1 - d, 0, 1) ** 1.2
    wsm = ramp("#030304", "#0a0a0e", "#14141a", "#2a1816", "#5a2410", "#b04a12", "#f08a28")
    sp.paint(front, 0.3 + 0.2 * sp.noise(6, 4731) + 0.4 * lit ** 2 * np.clip((sp.y - 98) / 10, 0, 1) - 0.1 * (sp.x > 90), wsm)
    sp.paint(topface, 0.28 + 0.18 * sp.noise(5, 4732) + 0.62 * lit, wsm)
    crack = np.abs(sp.noise(9, 4733, 3) - 0.5) < 0.012
    sp.solid(crack & front, "#050506")
    sp.solid(sp.line(18, 100, 110, 100, 1.4) & topface | (sp.line(16, 100, 112, 100, 1.2) & front & (sp.y < 101.5)), "#2a2630")
    draw_ember(sp, cx, top)
    return sp.rgba()


# ---- shared helpers for props ------------------------------------------------------------------------------------------------------------------------

from tools.story.art.tex_underworld import _flames  # noqa: E402

LAMPHALO = ramp("#4a200a", "#7a3c10", "#b06a1c", "#dc9a2c", "#ffd266")
COLDHALO = ramp("#10283c", "#20506c", "#3a86a8", "#78c8e0", "#c8f4fc")
MINT = ramp("#0a3a2a", "#1a6a46", "#3aa66a", "#8adca0", "#d8ffe0")


def _wood(sp: Cv, mask, x0, x1, pal=OAK, seed=1, base=0.5, amp=0.3, grain=0.08, vertical=True):
    """Wood with a lit side and long grain, painted into `mask`."""
    n = sp.noise(5, seed, 3)
    along = sp.y if vertical else sp.x
    g = np.sin(along * 0.11 + n * 7.0 + sp.x * 0.35) * grain
    sp.paint(mask, sp.hshade(x0, x1, base, amp) + g + (n - 0.5) * 0.12, pal)


def _apples(sp: Cv, pts, r=4.5):
    for (x, y) in pts:
        m = sp.ellipse(x, y, r, r * 0.95)
        sh = 0.5 + 0.45 * (-((sp.x - x) * 0.6 + (sp.y - y) * 0.8) / r) * 0.9
        sp.paint(m, sh, APPLE)
        sp.solid(sp.rect(x - 2, y - 2.4, x - 0.2, y - 1.2), "#ffcfb0")
        sp.solid(sp.rect(x - 0.5, y - r - 1.5, x + 0.8, y - r + 0.8), "#2a1a0c")


def _chain(sp: Cv, ax, ay, bx, by, link=7.0, w=2.4, shade=0.5, pal=IRON):
    """Chain links along a straight run (alternating face-on rings and edge-on bars)."""
    L = math.hypot(bx - ax, by - ay)
    k = max(int(L / link), 1)
    for i in range(k + 1):
        t = i / k
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        if i % 2 == 0:
            sp.paint(sp.ring(x, y, w * 1.7, w * 1.7, 1.3), shade + 0.1, pal)
        else:
            sp.paint(sp.line(x - (bx - ax) / L * link * 0.35, y - (by - ay) / L * link * 0.35, x + (bx - ax) / L * link * 0.35, y + (by - ay) / L * link * 0.35, 2.0), shade - 0.1, pal)


def _blades(sp: Cv, cx, base_y, n, spread, hmin, hmax, seed, pal, w0=3.0, bend=14.0, shade=(0.3, 0.8)):
    rng = RNG(seed)
    for i in range(n):
        bx = cx + rng.uniform(-spread, spread)
        h = rng.uniform(hmin, hmax)
        lean = (bx - cx) / max(spread, 1) * bend + rng.uniform(-4, 4)
        pts = bez((bx, base_y), (bx + lean * 0.3, base_y - h * 0.55), (bx + lean, base_y - h), 12)
        sp.paint(sp.stroke(pts, w0, 1.0), rng.uniform(*shade), pal)


def _mound(sp: Cv, cx, y, rx, ry, pal, seed, base=0.35):
    m = sp.ellipse(cx, y, rx, ry) & (sp.y <= 127.5)
    sp.paint(m, base + 0.4 * sp.noise(4, seed) + 0.2 * (-(sp.y - y) / ry), pal)
    return m


# ---- orchard ------------------------------------------------------------------------------------------------------------------------------------------

def th_apple_tree():
    sp = Cv()
    rng = RNG(1101)
    trunk = sp.stroke([(64, 127), (63, 104), (57, 84), (61, 62)], 21, 11) | sp.poly([(44, 127), (84, 127), (70, 106), (58, 106)])
    branches = [sp.stroke(p, 7, 3) for p in ([(60, 78), (44, 62), (28, 52)], [(62, 74), (84, 62), (102, 50)], [(60, 66), (52, 46), (46, 30)], [(63, 64), (76, 42), (84, 26)])]
    for b in branches:
        trunk |= b
    gr = sp.noise(4, 1102, 3)
    sp.paint(trunk, sp.hshade(42, 86, 0.45, 0.4) + (np.sin(sp.y * 0.3 + gr * 8 + sp.x * 0.2) * 0.1) + (gr - 0.5) * 0.25, BARK)
    sp.paint(trunk & (sp.noise(3, 1103) > 0.7), 0.1, BARK)
    # the crown: overlapping leaf clumps, back to front, gold flecks and red apples
    cl = []
    for i in range(34):
        a = rng.uniform(0, TWO_PI)
        rr = math.sqrt(rng.rand())
        cl.append((64 + 46 * rr * math.cos(a), 46 + 30 * rr * math.sin(a), rng.uniform(11, 19)))
    cl.sort(key=lambda c: c[1])
    crown = np.zeros((128, 128), bool)
    for (x, y, r) in cl:
        m = sp.ellipse(x, y, r, r * 0.85) & (sp.y < 92)
        lit = -((sp.x - x) * 0.6 + (sp.y - y) * 0.8) / r
        sp.paint(m, 0.48 + 0.3 * lit + (sp.noise(4, 1104, 2) - 0.5) * 0.3 - 0.12 * (y < 40) * -1 * 0, LEAF)
        crown |= m
    gold = crown & (sp.noise(3, 1105, 2) > 0.74)
    sp.paint(gold, 0.35 + 0.5 * sp.noise(2, 1106, 2), GOLDLEAF)
    pts = []
    tries = 0
    while len(pts) < 17 and tries < 400:
        tries += 1
        x, y = rng.uniform(22, 106), rng.uniform(26, 82)
        if crown[int(y), int(x)] and all((x - a) ** 2 + (y - b) ** 2 > 130 for a, b in pts):
            pts.append((x, y))
    _apples(sp, pts)
    _apples(sp, [(34, 123), (96, 121), (82, 125)], 4.2)
    return sp.rgba()


def _basket(sp: Cv, cx, top, wt, wb, h, seed):
    body = sp.poly([(cx - wt / 2, top), (cx + wt / 2, top), (cx + wb / 2, top + h), (cx - wb / 2, top + h)])
    weave = ((np.floor(sp.x / 3) + np.floor(sp.y / 3)) % 2) * 0.2 + ((sp.y % 6) < 1.5) * -0.12
    sp.paint(body, sp.hshade(cx - wt / 2, cx + wt / 2, 0.5, 0.35) + weave + (sp.noise(3, seed) - 0.5) * 0.12, WICKER)
    rim = sp.rect(cx - wt / 2 - 3, top - 4, cx + wt / 2 + 3, top + 4)
    sp.paint(rim, sp.hshade(cx - wt / 2 - 3, cx + wt / 2 + 3, 0.6, 0.3) + ((sp.x % 5) < 1.5) * -0.1, WICKER)
    sp.paint(sp.rect(cx - wb / 2 - 1, top + h - 3, cx + wb / 2 + 1, top + h + 1), 0.25, WICKER)


def th_apple_basket():
    sp = Cv()
    # right (smaller) basket behind, left (larger) in front
    _basket(sp, 88, 94, 46, 36, 33, 1201)
    ah = [(70, 86), (80, 82), (91, 80), (102, 84), (76, 74), (88, 72), (98, 76), (84, 64), (94, 66)]
    _apples(sp, [(x + 4, y) for x, y in ah], 5.2)
    sp.paint(sp.stroke(bez((66, 92), (88, 40), (110, 92)), 3.2), 0.4, WICKER)
    _basket(sp, 40, 88, 58, 44, 39, 1202)
    ah = [(20, 82), (32, 80), (44, 80), (56, 82), (24, 70), (37, 68), (50, 70), (62, 74), (30, 58), (43, 56), (55, 60), (38, 46), (49, 46)]
    _apples(sp, ah, 5.6)
    sp.paint(sp.stroke(bez((12, 90), (40, 20), (68, 90)), 3.4), 0.45, WICKER)
    _apples(sp, [(84, 121), (104, 124), (112, 117), (4, 124)], 5.0)
    return sp.rgba()


def th_cot():
    sp = Cv()
    # the headboard behind: two posts and an arched board
    for x0 in (22, 98):
        _wood(sp, sp.rect(x0, 14, x0 + 9, 64), x0, x0 + 9, OAK, 1301)
    head = sp.rect(22, 22, 107, 54) | sp.ellipse(64.5, 26, 42.5, 12)
    _wood(sp, head, 22, 107, OAK, 1302, 0.4, 0.3, 0.1, vertical=False)
    sp.paint(sp.rect(30, 30, 99, 31.5) | sp.rect(30, 44, 99, 45.5), 0.12, OAK)
    # the quilt in perspective, patchwork
    quilt = sp.poly([(20, 90), (108, 90), (98, 48), (30, 48)])
    v = np.clip((sp.y - 48) / 42.0, 0, 1)
    left = 30 - 10 * v
    right = 98 + 10 * v
    u = np.clip((sp.x - left) / np.maximum(right - left, 1), 0, 1)
    pi, pj = np.floor(u * 6).astype(int), np.floor(v * 4.2).astype(int)
    cols = np.array([[168, 64, 58], [216, 200, 160], [74, 106, 138], [192, 138, 48], [90, 122, 74], [140, 70, 90]], np.float32)
    idx = (pi * 3 + pj * 5 + (pi * pj)) % 6
    col = cols[idx] * (0.7 + 0.5 * (1 - v) * 0.7 + 0.1 * np.sin(u * 20 + v * 5))[..., None]
    seam = (np.abs(u * 6 - np.round(u * 6)) < 0.05) | (np.abs(v * 4.2 - np.round(v * 4.2)) < 0.07)
    col = np.where(seam[..., None], col * 0.55, col)
    stitch = ((sp.x + sp.y) % 6 < 1) & seam
    col = np.where(stitch[..., None], np.array([214, 200, 168]), col)
    sp.rgb[quilt] = np.clip(col, 0, 255).astype(np.uint8)[quilt]
    sp.a[quilt] = 255
    fold = sp.rect(18, 83, 110, 91) & quilt
    sp.rgb[fold] = (sp.rgb[fold].astype(np.float32) * 0.62).astype(np.uint8)
    pil = sp.ellipse(64, 48, 28, 10)
    sp.paint(pil, 0.62 + 0.38 * sp.bump(pil, 5, 0.5, 0.5) - 0.12, ramp("#4a4238", "#8a8070", "#c4b8a0", "#e8dcc0", "#fff6e0"), dither=0.5)
    # the footboard and legs
    for x0 in (13, 103):
        _wood(sp, sp.rect(x0, 78, x0 + 12, 127), x0, x0 + 12, OAK, 1303)
        sp.paint(sp.ellipse(x0 + 6, 76, 6, 6), 0.6, OAK)
    foot = sp.rect(13, 92, 115, 112)
    _wood(sp, foot, 13, 115, OAK, 1304, 0.42, 0.3, 0.09, vertical=False)
    sp.paint(sp.rect(13, 92, 115, 94.5), 0.8, OAK)
    sp.paint(sp.rect(24, 99, 104, 101), 0.15, OAK)
    return sp.rgba()


def _lantern(sp: Cv, cx, top, h, w, halo_r, strength=1.0):
    """A horn lantern: iron caps, amber panels with a bright core, ribs, and a warm dithered glow."""
    sp.glow(cx, top + h / 2 + 3, halo_r, halo_r, LAMPHALO, power=1.4, gain=1.3, dither=0.5, strength=strength)
    sp.paint(sp.poly([(cx - w / 2 - 2, top), (cx + w / 2 + 2, top), (cx + 2, top - 5), (cx - 2, top - 5)]), 0.45, IRON)
    sp.paint(sp.rect(cx - w / 2 - 2, top, cx + w / 2 + 2, top + 4), 0.5, IRON)
    body = sp.rect(cx - w / 2, top + 4, cx + w / 2, top + h - 4)
    core = np.clip(1 - np.abs(sp.x - cx) / (w * 0.6), 0, 1) * np.clip(1 - np.abs(sp.y - (top + h * 0.55)) / (h * 0.55), 0, 1)
    sp.paint(body, 0.35 + 0.65 * core ** 0.8, WARM)
    sp.paint(sp.rect(cx - w / 2 - 0.5, top + 4, cx - w / 2 + 1.3, top + h - 4) | sp.rect(cx + w / 2 - 1.3, top + 4, cx + w / 2 + 0.5, top + h - 4) | sp.rect(cx - 0.6, top + 4, cx + 0.8, top + h - 4), 0.3, IRON)
    sp.paint(sp.rect(cx - w / 2 - 2, top + h - 4, cx + w / 2 + 2, top + h), 0.45, IRON)
    sp.paint(sp.rect(cx - 3, top + h, cx + 3, top + h + 3), 0.4, IRON)
    sp.paint(sp.ring(cx, top - 8, 3.2, 3.2, 1.3), 0.6, IRON)


def th_lantern_post():
    sp = Cv()
    _mound(sp, 62, 124, 26, 6, STONE, 1401)
    post = sp.rect(56, 22, 69, 127)
    _wood(sp, post, 56, 69, BARK, 1402, 0.5, 0.35)
    sp.paint(sp.rect(54, 18, 71, 24), 0.55, BARK)
    arm = sp.stroke([(66, 30), (82, 26), (101, 24)], 7, 5)
    _wood(sp, arm, 56, 105, BARK, 1403, 0.5, 0.2, vertical=False)
    sp.paint(sp.stroke([(66, 52), (88, 30)], 4, 3), 0.4, BARK)
    _chain(sp, 100, 24, 100, 36, 6, 1.6, 0.5)
    _lantern(sp, 100, 40, 38, 16, 34)
    return sp.rgba()


def th_lantern_stake():
    sp = Cv()
    _mound(sp, 62, 126, 34, 6, ramp("#060c0a", "#10201a", "#1c342a", "#2c4a38", "#40604a"), 1411)
    _blades(sp, 62, 124, 14, 28, 16, 34, 1412, ramp("#06120e", "#0e2a22", "#1a4a38", "#2a6a50"), 2.6, 10)
    pole = sp.stroke([(60, 127), (62, 70), (66, 34)], 7, 5)
    _wood(sp, pole, 56, 70, BARK, 1413, 0.5, 0.35)
    sp.paint(sp.rect(52, 112, 72, 124) & sp.ellipse(62, 122, 12, 6) & ~pole, 0.35, STONE)
    _lantern(sp, 66, 8, 28, 12, 26, 0.9)
    # a pale moth by the light
    sp.paint(sp.poly([(86, 30), (95, 24), (93, 31)]) | sp.poly([(86, 31), (94, 35), (92, 30)]), 0.8, BIRCH)
    sp.paint(sp.rect(85, 29, 87, 34), 0.3, BARK)
    return sp.rgba()


def th_hearth():
    sp = Cv()
    sh, mort = bricks(128, rows=13, cols=5, mortar=1, seed=1421, wear=0.35)
    breast = sp.poly([(32, 0), (96, 0), (96, 24), (124, 40), (124, 127), (4, 127), (4, 40), (32, 24)])
    opening = sp.rect(26, 62, 102, 127) | sp.ellipse(64, 66, 38, 24)
    opening &= sp.y >= 46
    cx_ = np.clip(1 - np.sqrt(((sp.x - 64) / 70.0) ** 2 + ((sp.y - 100) / 55.0) ** 2), 0, 1)
    base = sh * 0.8 + (sp.noise(5, 1422) - 0.5) * 0.15
    sp.paint(breast, base, STONE)
    warm = breast & (cx_ > 0.15)
    sp.paint(warm, base * 0.9 + 0.35 * cx_, ramp("#100e0c", "#221b16", "#3c2c22", "#5e4030", "#8a5a38", "#c08850"))
    sp.solid(breast & (mort > 0.5), "#1a1512")
    # the mantel
    sp.paint(sp.rect(0, 34, 128, 46), 0.45 + 0.25 * (sp.y < 37) - 0.2 * (sp.y > 43) + (sp.noise(4, 1423) - 0.5) * 0.15, STONE)
    sp.paint(sp.rect(0, 34, 128, 46) & (cx_ > 0.2), 0.5 + 0.3 * cx_, ramp("#221b16", "#3c2c22", "#5e4030", "#8a5a38", "#c08850"))
    # the opening: dark brick, the fire, logs, the pot on its hook
    sp.paint(opening, 0.12 + 0.35 * np.clip((sp.y - 50) / 70, 0, 1) * (1 - np.abs(sp.x - 64) / 50), ramp("#070303", "#1a0a06", "#3a1408", "#6a2408", "#a8400c"))
    _flames(sp, 62, 118, 66, 62, 1424)
    sp.paint(sp.stroke([(34, 119), (92, 112)], 10, 9) & opening, 0.35 + 0.3 * sp.noise(3, 1425), BARK)
    sp.paint(sp.stroke([(40, 108), (98, 120)], 9, 10) & opening, 0.3 + 0.3 * sp.noise(3, 1426), BARK)
    sp.solid(sp.stroke([(36, 117), (50, 116)], 3, 2) & opening, "#ff6a1a")
    sp.paint(sp.rect(22, 118, 106, 127), 0.35 + 0.2 * sp.noise(5, 1427), STONE)
    sp.paint(sp.stroke([(88, 56), (88, 72)], 3.5) | sp.stroke([(88, 72), (80, 82)], 3), 0.5, IRON)
    pot = sp.ellipse(78, 96, 18, 15) & (sp.y > 82)
    sp.paint(pot, sp.hshade(60, 96, 0.5, 0.5) + 0.2 * np.clip(1 - (sp.y - 82) / 10, 0, 1) * 0, ramp("#06070a", "#14161c", "#262a34", "#3e4452", "#5a6274", "#8a92a4"))
    sp.paint(sp.ellipse(78, 83, 19, 4.5), 0.35, IRON)
    sp.solid(sp.ellipse(78, 83, 15, 2.6), "#2a1408")
    sp.paint(pot & (sp.y > 100), 0.55 + 0.35 * np.clip((sp.y - 100) / 12, 0, 1), ramp("#2a0a04", "#6a1a08", "#b8340c", "#e8620e"))
    sp.paint(sp.stroke(bez((60, 84), (78, 66), (96, 84)), 2.4), 0.5, IRON)
    return sp.rgba()


def th_inn_table():
    sp = Cv()
    for x0 in (10, 108):
        _wood(sp, sp.rect(x0, 80, x0 + 10, 127), x0, x0 + 10, OAK, 1431)
    _wood(sp, sp.rect(20, 105, 108, 111), 20, 108, OAK, 1432, 0.4, 0.3, 0.06, vertical=False)
    _wood(sp, sp.rect(4, 70, 124, 82), 4, 124, OAK, 1433, 0.35, 0.3, 0.1, vertical=False)
    top = sp.poly([(16, 56), (112, 56), (124, 70), (4, 70)])
    n = sp.noise(5, 1434, 3)
    sp.paint(top, 0.6 + (np.sin(sp.y * 0.9 + n * 6 + sp.x * 0.05)) * 0.07 + (n - 0.5) * 0.15, OAK)
    sp.paint(sp.rect(4, 70, 124, 72), 0.85, OAK)
    sp.solid(sp.ellipse(44, 63, 8, 1.6) | sp.ellipse(98, 66, 5, 1.2), "#2a1a0a")  # old ale rings
    # two pewter mugs
    for mx, my in ((26, 64), (42, 66)):
        body = sp.poly([(mx - 6, my - 15), (mx + 6, my - 15), (mx + 7, my), (mx - 7, my)])
        sp.paint(body, sp.hshade(mx - 7, mx + 7, 0.5, 0.5), PEWTER)
        sp.paint(sp.ellipse(mx, my - 15, 6, 1.8), 0.75, PEWTER)
        sp.paint(sp.ring(mx + 9, my - 8, 4.2, 5, 2), 0.5, PEWTER)
        sp.paint(sp.rect(mx - 6, my - 4, mx + 6, my - 2.5), 0.25, PEWTER)
    # a loaf
    loaf = sp.ellipse(76, 58, 16, 8) & (sp.y < 63)
    sp.paint(loaf | sp.ellipse(76, 62, 16, 3), sp.bump(loaf, 4, 0.55, 0.6), ramp("#2a1408", "#5a3410", "#8a5a1c", "#b8863a", "#dcb060"))
    for k in (-8, 0, 8):
        sp.solid(sp.line(76 + k - 2, 54, 76 + k + 2, 61, 1.3), "#e8c47a")
    # the candle
    sp.paint(sp.ellipse(102, 65, 7, 2.2) | sp.rect(99, 60, 105, 65), 0.5, BRONZE)
    sp.paint(sp.rect(99, 46, 105, 61), sp.hshade(99, 105, 0.6, 0.35), ramp("#6a604c", "#a49880", "#d8ccaa", "#f0e8cc", "#fffae0"))
    sp.glow(102, 40, 17, 17, LAMPHALO, power=1.5, gain=1.3, dither=0.5)
    sp.paint(sp.poly([(102, 34), (99.5, 42), (102, 46), (104.5, 42)]), 0.9, WARM)
    sp.solid(sp.rect(101, 41, 103, 45), "#fff4c0")
    return sp.rgba()


def th_barrel():
    sp = Cv()
    cx = 64
    yy = sp.y
    hw = 29 + 9 * np.abs(np.sin(np.clip((yy - 24) / 99.0, 0, 1) * math.pi)) ** 0.8
    body = (np.abs(sp.x - cx) <= hw) & (yy >= 26) & (yy <= 126.5)
    stave = np.floor((sp.x - cx + 40) / 7.0)
    tone = RNG(1441).rand(24)[(stave.astype(int)) % 24]
    d = (sp.x - cx) / np.maximum(hw, 1)
    sh = 0.55 - 0.42 * np.clip((d + 0.5), 0, 1.5) * 0.7 + 0.12 * tone + 0.06 * np.sin(sp.y * 0.2 + stave) - 0.18 * ((sp.x - cx + 40) % 7 < 1)
    sp.paint(body, sh + 0.12, OAK)
    lid = sp.ellipse(cx, 26, 32, 8)
    sp.paint(lid, 0.5 + 0.35 * np.clip(-(sp.y - 26) / 8 - (sp.x - cx) / 60, -1, 1) + 0.1 * np.sin((sp.x - cx) * 0.5), OAK)
    sp.paint(sp.ring(cx, 26, 32, 8, 2.2), 0.45, OAK)
    for hy in (38, 60, 94, 116):
        curve = 5 * (1 - (d ** 2))
        hoop = body & (np.abs(yy - (hy + curve)) < 2.8)
        sp.paint(hoop, 0.5 - 0.3 * np.clip(d + 0.4, 0, 1) + 0.3 * (np.abs(yy - (hy + curve)) < 1.0), IRON)
    sp.paint(sp.ring(cx, 26, 34, 9, 2.8) & (sp.y > 26), 0.55, IRON)
    sp.paint(sp.rect(60, 82, 69, 90) | sp.rect(62, 90, 67, 98), 0.6, BRONZE)
    sp.paint(sp.rect(57, 80, 72, 83), 0.45, BRONZE)
    sp.solid(sp.rect(63, 99, 66, 102), "#d8a850")
    return sp.rgba()


def th_stool():
    sp = Cv()
    leg_b = sp.stroke([(63, 66), (65, 122)], 8, 6)
    sp.paint(leg_b, sp.hshade(58, 70, 0.28, 0.3), OAK)
    for (a, b) in (((38, 62), (24, 127)), ((90, 62), (104, 127))):
        m = sp.stroke([a, b], 10, 7)
        _wood(sp, m, min(a[0], b[0]) - 4, max(a[0], b[0]) + 4, OAK, 1451, 0.5, 0.3)
    sp.paint(sp.stroke([(40, 66), (88, 66)], 4) & sp.rect(30, 92, 100, 96), 0.3, OAK)
    sp.paint(sp.stroke([(32, 94), (96, 94)], 4.5), 0.38, OAK)
    sp.paint(sp.stroke([(62, 66), (62, 127)], 11, 8), sp.hshade(56, 68, 0.5, 0.45), OAK)
    side = sp.rect(26, 50, 102, 62) | sp.ellipse(64, 62, 38, 8)
    _wood(sp, side, 26, 102, OAK, 1452, 0.45, 0.35, 0.08, vertical=False)
    topf = sp.ellipse(64, 50, 38, 9)
    sp.paint(topf, 0.62 + 0.25 * sp.bump(topf, 6, 0.5, 0.5) + 0.07 * np.sin(sp.x * 0.45 + sp.noise(4, 1453) * 6), OAK)
    sp.paint(sp.ring(64, 50, 38, 9, 2) & (sp.y > 50), 0.35, OAK)
    return sp.rgba()


def th_hanging_lamp():
    sp = Cv()
    _chain(sp, 64, -4, 64, 26, 7.5, 2.0, 0.5)
    for (bx, by) in ((20, 56), (108, 56), (64, 66)):
        sp.paint(sp.stroke([(64, 26), (bx, by)], 2.4), 0.45, IRON)
    sp.paint(sp.ellipse(64, 26, 6, 6), 0.6, IRON)
    ring = sp.ring(64, 58, 46, 11, 4.5)
    sp.paint(ring, 0.35 + 0.45 * (sp.y > 58) + 0.1 * np.sin(sp.x * 0.3), IRON)
    sp.paint(sp.stroke([(64, 68), (64, 92)], 6, 2), 0.5, IRON)
    sp.paint(sp.ellipse(64, 96, 5.5, 5.5), 0.65, IRON)
    for cxx in (22, 43, 64, 85, 106):
        yy = 58 + 11 * math.sqrt(max(1 - ((cxx - 64) / 46.0) ** 2, 0)) - 1
        sp.glow(cxx, yy - 24, 14, 15, LAMPHALO, power=1.5, gain=1.3, dither=0.5)
    for cxx in (22, 43, 64, 85, 106):
        yy = 58 + 11 * math.sqrt(max(1 - ((cxx - 64) / 46.0) ** 2, 0)) - 1
        sp.paint(sp.ellipse(cxx, yy - 1, 6, 2.2), 0.6, PEWTER)
        sp.paint(sp.rect(cxx - 3, yy - 16, cxx + 3, yy - 1), sp.hshade(cxx - 3, cxx + 3, 0.6, 0.35), ramp("#6a604c", "#a49880", "#d8ccaa", "#f0e8cc", "#fffae0"))
        sp.paint(sp.poly([(cxx, yy - 27), (cxx - 2.6, yy - 21), (cxx, yy - 16), (cxx + 2.6, yy - 21)]), 0.9, WARM)
        sp.solid(sp.rect(cxx - 0.8, yy - 22, cxx + 0.8, yy - 17), "#fff4c0")
    return sp.rgba()


def th_gate():
    sp = Cv()
    sh, mort = bricks(128, rows=9, cols=3, mortar=1, seed=1461, wear=0.5)
    for (x0, x1) in ((4, 28), (100, 124)):
        post = sp.rect(x0, 40, x1, 127)
        sp.paint(post, sh * 0.85 + sp.hshade(x0, x1, 0.0, 0.25) + (sp.noise(5, 1462) - 0.5) * 0.15, STONE)
        sp.solid(post & (mort > 0.5), "#16130f")
        sp.paint(sp.rect(x0 - 3, 33, x1 + 3, 41), sp.hshade(x0 - 3, x1 + 3, 0.6, 0.3), STONE)
        sp.paint(sp.rect(x0 - 3, 33, x1 + 3, 35), 0.85, STONE)
    sp.paint(sp.ellipse(32, 125, 16, 5) | sp.ellipse(98, 125, 18, 5), 0.3 + 0.3 * sp.noise(3, 1463), ramp("#08140a", "#122a14", "#1e4220", "#2c5c2a"))
    # the gate leaf, hinged on the right post and swung half open: foreshortened bars
    hx, fx = 100, 46
    hy0, hy1, fy0, fy1 = 56, 116, 68, 106

    def at(s, t):
        return (hx + (fx - hx) * s, (hy0 + (fy0 - hy0) * s) + ((hy1 + (fy1 - hy1) * s) - (hy0 + (fy0 - hy0) * s)) * t)
    parts = []
    for t in (0.06, 0.5, 0.94):
        a, b = at(0, t), at(1, t)
        parts.append(sp.stroke([a, b], 6.5, 4.5))
    for s in (0.0, 0.34, 0.67, 1.0):
        a, b = at(s, 0.04), at(s, 0.96)
        parts.append(sp.stroke([a, b], 6.0 - 1.5 * s, 5.0 - 1.5 * s))
    parts.append(sp.stroke([at(0.02, 0.92), at(0.98, 0.1)], 5.0, 3.5))
    leaf = np.zeros((128, 128), bool)
    for p in parts:
        leaf |= p
    _wood(sp, leaf, 44, 102, BARK, 1464, 0.55, 0.3, 0.1, vertical=False)
    sp.paint(leaf & (sp.noise(3, 1465) > 0.75), 0.82, BARK)
    sp.paint(sp.rect(96, 62, 101, 70) | sp.rect(96, 100, 101, 108), 0.5, IRON)
    return sp.rgba()


def th_hay_bale():
    sp = Cv()
    # the bale seen end-on, a spiral of packed straw
    cx, cy, R = 44, 89, 38
    dx, dy = sp.x - cx, sp.y - cy
    rr = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)
    end = (rr <= R) & (sp.y <= 127.5)
    spiral = np.sin(rr * 0.9 + ang * 2.0 + sp.noise(3, 1471) * 3)
    sh = 0.55 + 0.18 * spiral + 0.18 * (-(dx * 0.5 + dy * 0.7) / R) + (sp.noise(2, 1472, 2) - 0.5) * 0.2 - 0.1 * (rr > R - 3)
    sp.paint(end, sh, HAY)
    sp.paint(end & (rr > R - 4) & (rr < R - 2), 0.35, HAY)
    sp.paint(end & (sp.noise(2, 1473, 2) > 0.78), 0.9, HAY)
    # the second bale lies on its side, tied with twine
    side = sp.rect(76, 66, 124, 127) | sp.ellipse(100, 70, 24, 6)
    strands = np.sin(sp.y * 1.2 + sp.noise(2, 1474, 2) * 9 + (sp.x // 5) * 1.7)
    sp.paint(side, 0.52 + 0.2 * strands + 0.2 * np.clip((100 - sp.x) / 40, -1, 1) + (sp.noise(2, 1475, 2) - 0.5) * 0.15, HAY)
    sp.paint(sp.ellipse(100, 68, 24, 6), 0.7 + 0.15 * np.sin(sp.x * 1.1), HAY)
    for tx in (88, 112):
        sp.solid(sp.rect(tx, 69, tx + 2.5, 127) & side, "#3a2410")
    return sp.rgba()


def th_willow():
    sp = Cv()
    W = ramp("#040e12", "#0a1e22", "#123638", "#1e5248", "#32705a", "#5a9a70")
    trunk = sp.stroke([(66, 127), (64, 100), (58, 76), (62, 54)], 18, 8) | sp.poly([(44, 127), (86, 127), (72, 104), (58, 104)])
    sp.paint(trunk, sp.hshade(46, 84, 0.45, 0.4) + np.sin(sp.y * 0.35 + sp.noise(4, 1481) * 7) * 0.1, BARK)
    for (a, m_, b) in (((62, 58), (44, 40), (22, 40)), ((64, 56), (86, 38), (108, 38))):
        sp.paint(sp.stroke(bez(a, m_, b), 6, 3), 0.35, BARK)
    dome = sp.ellipse(64, 44, 54, 26) & (sp.y < 52)
    sp.paint(dome, 0.28 + 0.25 * sp.noise(3, 1482) - 0.2 * (sp.y - 20) / 30, W)
    rng = RNG(1483)
    strands = []
    for i in range(86):
        t = rng.uniform(0.0, 1.0)
        ax = 14 + 100 * t
        ay = 44 - 26 * math.sqrt(max(1 - ((ax - 64) / 54.0) ** 2, 0)) + rng.uniform(0, 8)
        L = rng.uniform(36, 84) * (1 - 0.28 * math.exp(-((ax - 64) / 14.0) ** 2))
        ph = rng.uniform(0, 6)
        pts = [(ax + (ax - 64) * 0.22 * (k / 8.0) + 3.0 * math.sin(k * 0.7 + ph), ay + L * k / 8.0) for k in range(9)]
        strands.append((ay + L, pts, rng.uniform(0.2, 0.9)))
    strands.sort(key=lambda s: s[2])
    for (_, pts, tone) in strands:
        m = sp.stroke(pts, 2.6, 1.2)
        sh = 0.18 + 0.5 * tone + 0.25 * np.clip((sp.y - 40) / 80, 0, 1) * 0.6
        sp.paint(m, sh + (sp.noise(3, 1484) - 0.5) * 0.2, W)
    return sp.rgba()


def th_horse_far():
    sp = Cv()
    HR = ramp("#020204", "#08090e", "#12141c", "#1e222c", "#2e3442", "#444c5e")
    parts = [sp.ellipse(72, 70, 31, 17), sp.ellipse(50, 66, 17, 19), sp.ellipse(92, 70, 14, 16)]
    parts += [sp.stroke([(50, 64), (40, 44), (30, 24)], 25, 13), sp.stroke([(31, 24), (23, 36), (14, 49)], 15, 8), sp.ellipse(13, 50, 6.5, 5.2)]
    parts += [sp.poly([(30, 21), (36, 8), (39, 22)])]
    # legs: near foreleg standing, the other raised; both hinds standing
    legs = [sp.stroke([(52, 80), (51, 104), (52, 123)], 10, 6), sp.stroke([(44, 80), (33, 94), (29, 110)], 9, 5.5),
            sp.stroke([(94, 78), (101, 98), (93, 112), (95, 124)], 12, 6), sp.stroke([(84, 82), (82, 104), (85, 123)], 10, 6),
            sp.stroke(bez((99, 62), (118, 72), (108, 106), 16), 9, 3)]
    horse = np.zeros((128, 128), bool)
    for p in parts + legs:
        horse |= p
    sp.paint(horse, sp.bump(horse, 4.5, 0.42, 0.6) + (sp.noise(4, 1491) - 0.5) * 0.12, HR)
    # mane along the crest of the neck
    mane = sp.stroke([(38, 14), (44, 34), (52, 50), (58, 58)], 6, 4) | sp.stroke([(34, 16), (38, 30), (44, 44)], 5, 3)
    sp.paint(mane, 0.15 + 0.15 * sp.noise(3, 1492), HR)
    # hooves
    for (hx, hy) in ((51, 124), (95, 125), (85, 124), (29, 111)):
        sp.paint(sp.rect(hx - 4, hy - 2, hx + 4, hy + 3) & (sp.y <= 127.5), 0.12, HR)
    # the ash-grey rug over the back, a fringed edge, a lighter border
    rug = sp.poly([(54, 52), (90, 54), (93, 68), (90, 84), (82, 90), (60, 88), (52, 76)])
    sp.paint(rug, sp.bump(rug, 3, 0.55, 0.5) + 0.05 * np.sin(sp.x * 0.8), CLOTH)
    sp.paint(rug & ((sp.y > 83) | (sp.x < 56) | (sp.x > 88)), 0.8, CLOTH, dither=0.3)
    for fx_ in range(56, 90, 4):
        sp.paint(sp.rect(fx_, 87, fx_ + 2, 93), 0.5, CLOTH)
    # the bridle and rein
    for pts in ([(22, 30), (14, 42)], [(30, 30), (22, 42), (14, 44)], [(17, 36), (24, 46), (24, 56)]):
        sp.paint(sp.stroke(pts, 1.5), 0.55, CLOTH)
    sp.paint(sp.stroke(bez((13, 50), (24, 76), (46, 70)), 1.4), 0.5, CLOTH)
    sp.solid(sp.rect(22, 28, 25, 31), "#ff3a1e")
    sp.solid(sp.rect(22, 28, 24, 30), "#ffd27a")
    # breath
    rng = RNG(1493)
    for k in range(9):
        bx, by = 5 - k * 1.8 + rng.uniform(-2, 2), 54 + rng.uniform(-6, 4) + k * 0.6
        sp.paint(sp.ellipse(bx, by, 2.8 + k * 0.1, 2.2) & (sp.bt < 0.78 - k * 0.05) & (sp.x >= 0), 0.55 - k * 0.03, SMOKE, fx=True)
    return sp.rgba()


def th_signpost():
    sp = Cv()
    _mound(sp, 64, 124, 30, 6, ramp("#08140a", "#122a14", "#1e4220", "#2c5c2a", "#4a7a34"), 1501)
    post = sp.rect(59, 14, 70, 127)
    _wood(sp, post, 59, 70, BARK, 1502, 0.5, 0.4)
    sp.paint(sp.poly([(57, 18), (72, 18), (68, 8), (61, 8)]), 0.6, BARK)
    for (pts, ya, flip) in (([(66, 28), (22, 28), (8, 37), (22, 46), (66, 46)], 28, 0), ([(62, 54), (106, 54), (120, 63), (106, 72), (62, 72)], 54, 1)):
        board = sp.poly(pts)
        _wood(sp, board, 8, 120, OAK, 1503 + ya, 0.5, 0.15, 0.1, vertical=False)
        sp.paint(board & (sp.y < ya + 3), 0.85, OAK)
        sp.paint(board & (sp.y > ya + 15), 0.2, OAK)
        for nx in ((26, 52) if not flip else (82, 106)):
            sp.solid(sp.rect(nx - 1, ya + 8, nx + 1, ya + 10), "#14100c")
    sp.paint(sp.rect(56, 60, 73, 64) | sp.rect(56, 108, 73, 112), 0.55, IRON)
    return sp.rgba()


def th_rock_ford():
    sp = Cv()
    ST = ramp("#0a1218", "#1a2a36", "#2e4452", "#4a6678", "#7898a8", "#b8d4e0")
    sp.paint(sp.ellipse(64, 119, 62, 9), 0.2 + 0.2 * sp.noise(4, 1511), NIGHTW)
    stones = [(26, 112, 22, 12), (100, 113, 24, 11), (62, 98, 31, 21), (88, 100, 16, 13), (40, 120, 18, 7), (110, 122, 14, 5)]
    for (x, y, rx, ry) in stones:
        m = sp.ellipse(x, y, rx, ry) & (sp.y <= 127.5)
        sp.paint(m, sp.bump(m, rx * 0.4, 0.5, 0.65) + (sp.noise(3, 1512 + x) - 0.5) * 0.2, ST)
        sp.solid(m & (sp.noise(2, 1513 + x, 2) > 0.8) & (sp.y < y), "#cfe4ee")
    # water curling round the bases: silver ripples
    rng = RNG(1514)
    for (x, y, rx, ry) in stones[:4]:
        for k, off in enumerate((3, 8)):
            rim = sp.ring(x + off * 0.3, y + ry * 0.55 + k, rx * 1.18 + off, ry * 0.45 + off * 0.5, 1.6)
            keep = rim & (sp.y > y + ry * 0.1) & (sp.bt < 0.8) & (sp.noise(2, 1515 + x + k) > 0.3)
            sp.paint(keep & (sp.a == 0), 0.6 + 0.3 * rng.rand(), ramp("#2a4a5e", "#5a8ca4", "#a8d0e0", "#e4f6fc"), fx=True)
    return sp.rgba()


def th_door_back():
    sp = Cv()
    frame = sp.rect(16, 30, 112, 127)
    _wood(sp, frame, 16, 112, BARK, 1521, 0.4, 0.3, 0.07)
    sp.paint(sp.rect(10, 26, 118, 38), sp.hshade(10, 118, 0.55, 0.3), STONE)
    gap = sp.rect(28, 46, 100, 127)
    ny = np.clip((sp.y - 46) / 81.0, 0, 1)
    sp.paint(gap, 0.12 + 0.4 * ny ** 1.5 + (sp.noise(4, 1522) - 0.5) * 0.1, ramp("#04081a", "#0a1430", "#14264a", "#223c66", "#3a5c88", "#6a8cb0"))
    for (sx, sy) in ((36, 56), (44, 64), (39, 78)):
        sp.solid(sp.rect(sx, sy, sx + 1, sy + 1), "#cfe0f4")
    sp.paint(sp.rect(28, 118, 100, 127), 0.5, ramp("#2a3c50", "#50708a", "#90b4cc"))
    leaf = sp.poly([(100, 46), (100, 127), (50, 127), (50, 53)])
    _wood(sp, leaf, 50, 100, OAK, 1523, 0.45, 0.25, 0.07)
    for k in range(5):
        sx = 100 - k * 10.5
        sp.paint(sp.rect(sx, 47 + k * 1.2, sx + 1.4, 127) & leaf, 0.12, OAK)
    sp.paint(sp.stroke([(100, 66), (62, 62)], 6, 4) | sp.stroke([(100, 108), (62, 110)], 6, 4), 0.35, IRON)
    sp.paint(sp.ring(58, 90, 4.5, 4.5, 1.8), 0.6, IRON)
    sp.paint(sp.rect(10, 122, 118, 127), 0.45, STONE)
    return sp.rgba()


def pc_river_rise():
    sp = Cv()
    x = sp.x
    top = 40 + 6 * np.sin(x * 0.11) + 4 * np.sin(x * 0.29 + 1.0) + 2 * np.sin(x * 0.7)
    d = sp.y - top
    ripple = np.sin(sp.y * 0.9 + 3 * np.sin(x * 0.07) + x * 0.04)
    n = sp.noise(6, 1531)
    sh = 0.16 + 0.18 * n + 0.12 * (ripple > 0.8) + 0.12 * np.clip(1 - d / 40.0, 0, 1) - 0.1 * np.clip(d / 90.0, 0, 1)
    rgb = quantise(np.clip(sh, 0, 1), NIGHTW)
    a = np.clip((d + 2) / 10.0, 0, 1) * 0.94 * np.clip(x / 8.0, 0, 1) * np.clip((127 - x) / 8.0, 0, 1)
    sp.over(a, rgb)
    # silver foam crests along the top, spray above
    foam = (d > -1) & (d < 5 + 3 * np.sin(x * 0.4 + 2) ** 2) & (sp.noise(2, 1532, 2) > 0.3)
    fsh = 0.55 + 0.4 * np.clip(1 - d / 6, 0, 1)
    frgb = quantise(np.clip(fsh, 0, 1), ramp("#2a4a5e", "#5a8ca4", "#a8d0e0", "#e4f6fc", "#ffffff"))
    sp.over(foam * 0.92 * np.clip(x / 6.0, 0, 1) * np.clip((127 - x) / 6.0, 0, 1), frgb)
    rng = RNG(1533)
    for k in range(34):
        px = rng.uniform(6, 122)
        py = np.interp(px, np.arange(128), top[0]) - rng.uniform(2, 14)
        sz = 1 if rng.rand() < 0.7 else 2
        m = sp.rect(px, py, px + sz, py + sz)
        sp.over(m * 0.85, "#d8eef8")
    streak = (np.abs(((x * 0.9 + sp.y * 0.0) % 17) - 8) < 0.6) & (d > 8) & (sp.noise(3, 1534) > 0.55)
    sp.over(streak * 0.5, "#8cc0d4")
    return sp.rgba(outline=False, hard=False)


def pc_rider_shadow():
    sp = Cv()
    m = [sp.ellipse(64, 92, 38, 13), sp.ellipse(94, 92, 13, 13), sp.stroke([(38, 88), (32, 68), (27, 58)], 15, 9), sp.stroke([(27, 58), (19, 66)], 9, 5), sp.poly([(24, 55), (28, 44), (32, 56)]),
         sp.poly([(58, 88), (70, 88), (73, 54), (64, 34), (56, 54)]), sp.poly([(64, 8), (57, 30), (71, 30)]), sp.ellipse(64, 30, 7.5, 9),
         sp.poly([(70, 50), (98, 66), (95, 90), (72, 84)]), sp.stroke([(58, 60), (44, 72)], 5, 3), sp.stroke([(60, 90), (55, 112)], 7, 5),
         sp.stroke([(46, 98), (42, 116), (37, 127)], 6, 4), sp.stroke([(53, 98), (55, 114), (61, 127)], 6, 4), sp.stroke([(86, 98), (91, 114), (98, 127)], 6, 4),
         sp.stroke([(79, 100), (76, 114), (70, 127)], 6, 4), sp.stroke(bez((98, 86), (118, 94), (112, 122)), 7, 3)]
    mask = np.zeros((128, 128), bool)
    for p in m:
        mask |= p
    sp.over(np.clip(sp.blur(mask, 1.4) * 1.35, 0, 1) * 0.9, "#05070d")
    return sp.rgba(outline=False, hard=False)


# ---- birch hall ---------------------------------------------------------------------------------------------------------------------------------------

SILVER = ramp("#1c2430", "#44546a", "#7c90a8", "#b4c6da", "#e4eef8", "#ffffff")
HIDE = ramp("#4a4438", "#7a7260", "#a89e84", "#cfc6a8", "#e8e0c4")
BRIGHT = ramp("#7aa6d8", "#a8cdee", "#d0e6f8", "#eef8ff", "#ffffff")


def lens(sp: Cv, x0, y0, x1, y1, w, power=0.9):
    """A leaf shape along the axis (x0, y0) -> (x1, y1) with half-width w at its middle."""
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    t = ((sp.x - x0) * dx + (sp.y - y0) * dy) / L2
    d = ((sp.x - x0) * dy - (sp.y - y0) * dx) / math.sqrt(L2)
    return (t > 0) & (t < 1) & (np.abs(d) < w * np.abs(np.sin(np.clip(t, 0, 1) * math.pi)) ** power)


def _marks(sp: Cv, trunk, x0, x1, y0, y1, seed, colour="#3a3e4c", count=26):
    rng = RNG(seed)
    for k in range(count):
        y = rng.uniform(y0, y1)
        xa = rng.uniform(x0, x1 - 6)
        xb = xa + rng.uniform(4, 14)
        sp.solid(sp.rect(xa, y, xb, y + rng.choice([1, 1, 2])) & trunk, colour)


def th_birch_tree():
    sp = Cv()
    rng = RNG(1601)
    trunk = sp.stroke(bez3((64, 127), (61, 90), (68, 50), (63, 10), 30), 16, 5) | sp.poly([(50, 127), (78, 127), (68, 110), (60, 110)])
    limbs = []
    for pts, w in (([(65, 64), (46, 46), (28, 36)], 5), ([(66, 74), (88, 56), (104, 42)], 5), ([(64, 46), (52, 28), (44, 14)], 4), ([(64, 36), (78, 22), (92, 12)], 4),
                   ([(40, 42), (30, 24)], 2.6), ([(92, 52), (100, 30)], 2.6), ([(55, 36), (62, 8)], 2.4), ([(84, 20), (82, 4)], 2.2)):
        m = sp.stroke(bez(pts[0], pts[1], pts[-1], 12) if len(pts) == 3 else pts, w, 1.6)
        limbs.append(m)
        trunk |= m
    sp.paint(trunk, sp.hshade(48, 80, 0.62, 0.45) + (sp.noise(4, 1602) - 0.5) * 0.12, BIRCH)
    sp.paint(trunk & (sp.x > 66) & (sp.y > 40), 0.38 + 0.15 * sp.noise(3, 1603), BIRCH)
    _marks(sp, trunk, 50, 80, 30, 124, 1604, "#2e323e", 34)
    sp.solid(sp.ellipse(62, 82, 2, 3.5) & trunk, "#2a2e3a")
    # the last yellow leaves, loose on the twigs
    for k in range(46):
        a = rng.choice(len(limbs))
        ys, xs = np.nonzero(limbs[a])
        i = rng.randint(len(ys))
        lx, ly = xs[i] + rng.uniform(-4, 4), ys[i] + rng.uniform(-3, 5)
        sp.paint(sp.ellipse(lx, ly, 2.3, 1.7), rng.uniform(0.4, 1.0), GOLDLEAF)
    for (lx, ly) in ((34, 122), (92, 124), (80, 118), (48, 125)):
        sp.paint(sp.ellipse(lx, ly, 2.6, 1.5), 0.6, GOLDLEAF)
    return sp.rgba()


def th_birch_pillar():
    sp = Cv()
    # the vault: branches fanning out of the top and curving down either side
    arcs = [bez((56, 30), (34, -2), (4, 40)), bez((54, 40), (36, 22), (14, 70)), bez((52, 22), (40, 6), (26, 14)), bez((72, 30), (94, -2), (124, 40)),
            bez((74, 40), (92, 22), (114, 70)), bez((76, 22), (88, 6), (102, 14)), bez((60, 20), (56, 6), (48, 0)), bez((68, 20), (72, 6), (80, 0))]
    for i, pts in enumerate(arcs):
        m = sp.stroke(pts, 11 if i % 3 != 2 and i < 7 else 7, 3)
        sp.paint(m, sp.bump(m, 2.2, 0.62, 0.5) + 0.04 - 0.1 * (i % 2), BIRCH)
        sp.solid(m & (sp.noise(1.6, 1620 + i, 2) > 0.72), "#2e323e")
    trunk = sp.rect(49, 20, 79, 112)
    sp.paint(trunk, sp.hshade(49, 79, 0.62, 0.5) + (sp.noise(4, 1611) - 0.5) * 0.12, BIRCH)
    sp.paint(trunk & (sp.x > 70), 0.38 + 0.12 * sp.noise(3, 1612), BIRCH)
    _marks(sp, trunk, 49, 79, 22, 100, 1613, "#2e323e", 40)
    sp.solid(sp.ellipse(58, 50, 2.4, 4) & trunk | (sp.ellipse(72, 82, 2.2, 3.5) & trunk), "#2a2e3a")
    # the silver band at the foot and the stone plinth
    band = sp.rect(44, 96, 84, 110)
    sp.paint(band, sp.hshade(44, 84, 0.65, 0.5) + 0.06 * np.sin(sp.y * 1.3), SILVER)
    sp.solid(sp.rect(44, 96, 84, 97.2) | sp.rect(44, 108.8, 84, 110), "#2a3444")
    for rx in (50, 64, 78):
        sp.solid(sp.rect(rx, 102, rx + 2, 104), "#e8f2fc")
    sp.paint(sp.rect(36, 110, 92, 127), sp.hshade(36, 92, 0.45, 0.3) + (sp.noise(5, 1614) - 0.5) * 0.2, STONE)
    sp.paint(sp.rect(36, 110, 92, 113), 0.8, STONE)
    return sp.rgba()


def th_silver_lamp():
    sp = Cv()
    sp.glow(64, 36, 30, 34, COLDHALO, power=1.5, gain=1.35, dither=0.5)
    for (bx) in (32, 96, 64):
        m = sp.stroke([(64, 96), (bx, 126)], 6, 5)
        sp.paint(m, sp.hshade(min(bx, 64) - 4, max(bx, 64) + 4, 0.6, 0.4), SILVER)
    sp.paint(sp.ellipse(64, 126, 34, 2.5) & (sp.y < 127.5), 0.35, SILVER)
    sp.paint(sp.rect(60, 54, 68, 100), sp.hshade(60, 68, 0.62, 0.55), SILVER)
    sp.paint(sp.ellipse(64, 96, 9, 7), sp.hshade(55, 73, 0.6, 0.5), SILVER)
    sp.paint(sp.ellipse(64, 58, 8, 4.5), sp.hshade(56, 72, 0.7, 0.5), SILVER)
    # leaf-shaped shade: two petals either side of the flame
    for sgn in (-1, 1):
        pet = lens(sp, 64, 60, 64 + sgn * 22, 8, 14)
        sh = sp.bump(pet, 3, 0.6, 0.6) + 0.1
        sp.paint(pet, sh, SILVER)
        vein = sp.stroke([(64 + sgn * 2, 58), (64 + sgn * 20, 11)], 1.2) & pet
        sp.paint(vein, 0.25, SILVER)
    flame = sp.poly([(64, 12), (57, 34), (58, 46), (64, 52), (70, 46), (71, 34)])
    fc = np.clip(1 - np.sqrt(((sp.x - 64) / 8.0) ** 2 + ((sp.y - 38) / 18.0) ** 2), 0, 1)
    sp.paint(flame, 0.35 + 0.65 * fc ** 0.7, COLD)
    sp.paint(sp.ellipse(64, 40, 2.4, 7), 1.0, COLD)
    return sp.rgba()


def th_banner_birch():
    sp = Cv()
    cloth = sp.poly([(34, 12), (94, 12), (94, 110), (64, 126), (34, 110)])
    folds = np.sin((sp.x - 34) * 0.55 + 0.4 * np.sin(sp.y * 0.07)) * 0.5 + 0.5
    sh = 0.72 + 0.2 * folds - 0.1 * ((sp.x - 34) / 60.0) + (sp.noise(4, 1621) - 0.5) * 0.07
    sp.paint(cloth, sh, BIRCH, dither=0.7)
    sp.paint(cloth & ((sp.x < 38) | (sp.x > 90) | ((sp.y > 104) & (np.abs(sp.x - 64) > (126 - sp.y) * 1.5 - 0.0) & False)), 0.35, SILVER)
    # silver trim along both sides and a stitched border
    sp.paint(cloth & (((sp.x > 36) & (sp.x < 38)) | ((sp.x > 90) & (sp.x < 92))), 0.75, SILVER)
    # the embroidered spray: a curving stem, leaves in pairs
    stem = bez3((64, 112), (58, 90), (70, 64), (64, 30), 30)
    sp.paint(sp.stroke(stem, 2.4, 1.6), 0.42, SILVER)
    for i, (px, py) in enumerate(stem[3:27:3]):
        for sgn in (-1, 1):
            if (i + (sgn > 0)) % 3 == 2:
                continue
            lf = lens(sp, px, py, px + sgn * 19, py - 9, 5.6, 0.8)
            sp.paint(lf, 0.5 - 0.12 * (sp.y > py - 2), SILVER)
            sp.solid(sp.stroke([(px + sgn * 2, py - 0.6), (px + sgn * 17, py - 8)], 1.0) & lf, "#cfdcec")
    lf = lens(sp, 64, 36, 64, 10, 5.0, 0.8)
    sp.paint(lf, 0.5, SILVER)
    sp.solid(sp.stroke([(64, 34), (64, 14)], 1.0) & lf, "#cfdcec")
    # the rod, finials and cords
    sp.paint(sp.rect(22, 6, 106, 13), sp.hshade(22, 106, 0.5, 0.2) + 0.4 * (sp.y < 8), IRON)
    for fxx in (20, 108):
        sp.paint(sp.ellipse(fxx, 9.5, 4.5, 4.5), 0.75, SILVER)
    sp.paint(sp.stroke([(40, 6), (64, -2), (88, 6)], 2.4), 0.5, IRON)
    sp.paint(sp.rect(62, 126, 66, 128), 0.5, SILVER)
    for tx in (62.5, 64.5):
        sp.paint(sp.rect(tx - 0.5, 118, tx + 0.8, 127), 0.8, SILVER)
    return sp.rgba()


def th_table_map():
    sp = Cv()
    W = BIRCH
    for x0 in (8, 110):
        m = sp.rect(x0, 88, x0 + 10, 127)
        sp.paint(m, sp.hshade(x0, x0 + 10, 0.65, 0.5), W)
    sp.paint(sp.rect(18, 112, 110, 118), 0.55, W)
    sp.paint(sp.rect(2, 78, 126, 90), sp.hshade(2, 126, 0.7, 0.3) - 0.05 * (sp.y > 86), W)
    top = sp.poly([(18, 46), (110, 46), (126, 78), (2, 78)])
    sp.paint(top, 0.82 + 0.1 * np.clip((sp.y - 46) / 32, 0, 1) - 0.1 * (sp.x > 100) + (sp.noise(5, 1631) - 0.5) * 0.06, W, dither=0.7)
    # the hide spread across it, hanging a little over the front edge
    hide = sp.poly([(26, 50), (60, 48), (96, 50), (108, 58), (116, 70), (118, 84), (70, 86), (14, 84), (10, 72), (16, 58)])
    sp.paint(hide, 0.62 + 0.15 * np.clip(1 - (sp.y - 50) / 34, 0, 1) + (sp.noise(4, 1632) - 0.5) * 0.18, HIDE)
    sp.paint(hide & (sp.y > 78), 0.28, HIDE)
    # an invented chart: faint ink contours and a river line
    for (cxx, cyy, rx, ry, seed) in ((44, 64, 20, 9, 1633), (44, 64, 11, 4.5, 1634), (84, 68, 16, 7, 1635), (84, 68, 7, 3, 1636)):
        th = np.arctan2((sp.y - cyy) / ry, (sp.x - cxx) / rx)
        r = np.sqrt(((sp.x - cxx) / rx) ** 2 + ((sp.y - cyy) / ry) ** 2)
        wob = 1 + 0.18 * np.sin(3 * th + seed) + 0.1 * np.sin(5 * th + seed * 0.3)
        sp.solid(hide & (np.abs(r - wob) < 0.085), "#6a604c")
    river = bez3((24, 52), (50, 58), (58, 78), (102, 66), 30)
    sp.solid(sp.stroke(river, 1.5) & hide, "#4a6c8c")
    sp.solid(sp.stroke(bez((66, 49), (70, 62), (64, 78)), 1.1) & hide, "#4a6c8c")
    return sp.rgba()


def th_snow_pine():
    sp = Cv()
    sp.paint(sp.rect(59, 108, 69, 127), sp.hshade(59, 69, 0.4, 0.4), BARK)
    for i in range(4, -1, -1):
        top, base, w = 4 + i * 20, 34 + i * 20, 18 + i * 10
        pts = [(64, top)]
        k = 7
        for j in range(k + 1):
            t = j / k
            x = 64 - w + 2 * w * t
            y = base + (4 if j % 2 else -1) - 3 * math.sin(t * math.pi) * 0
            pts.append((x, y))
        tier = sp.poly(pts)
        lit = -((sp.x - 64) * 0.5 + (sp.y - (top + 20)) * 0.4) / 40
        sp.paint(tier, 0.38 + 0.25 * lit + 0.1 * np.sin((sp.x - 64) * 0.9 + i) + (sp.noise(4, 1641 + i) - 0.5) * 0.2, SPRUCE)
        wave = 5 * np.sin(sp.x * 0.5 + i * 2) + 4 * np.sin(sp.x * 0.23)
        frac = top + (base - top) * (0.34 + 0.2 * (i / 4)) + wave
        snow = tier & (sp.y < frac - np.abs(sp.x - 64) * 0.1 + 3)
        snow |= tier & (sp.noise(3, 1646 + i) > 0.74) & (sp.y > frac) & (sp.y < frac + 12)
        sp.paint(snow, sp.bump(snow, 2.5, 0.72, 0.4) + 0.05, SNOW)
    sp.paint(sp.ellipse(64, 125, 40, 4.5) & (sp.y < 127.5), 0.7 + 0.2 * sp.noise(4, 1647), SNOW)
    return sp.rgba()


def th_cairn():
    sp = Cv()
    sp.paint(sp.ellipse(64, 125, 58, 7) & (sp.y < 127.5), 0.75 + 0.15 * sp.noise(4, 1651), SNOW)
    stones = [(64, 114, 42, 12), (58, 100, 33, 10), (68, 88, 27, 9), (62, 76, 21, 8), (66, 66, 15, 6.5)]
    for k, (x, y, rx, ry) in enumerate(stones):
        m = (np.abs((sp.x - x) / rx) ** 3.2 + np.abs((sp.y - y) / ry) ** 3.2 + 0.18 * (sp.noise(3, 1655 + k) - 0.5)) < 1.0
        sp.paint(m, sp.bump(m, rx * 0.32, 0.5, 0.6) + (sp.noise(3, 1652 + k) - 0.5) * 0.25 + 0.03 * k, STONE)
        sp.solid(m & (sp.noise(2, 1660 + k, 2) > 0.8), "#2a2824")
        cap = m & (sp.y < y - ry * 0.35 + 2 * np.sin(sp.x * 0.5)) & (np.abs(sp.x - x) < rx * 0.9)
        sp.paint(cap, sp.bump(cap, 2.0, 0.78, 0.35) + 0.04, SNOW)
    # a strip of red cloth tied round the top stone and streaming to one side
    sp.paint(sp.rect(60, 61, 72, 66), 0.4, ramp("#3a0808", "#7a1410", "#b42a20"))
    pts = [(70, 63), (82, 58), (94, 62), (104, 56), (114, 60)]
    flag = sp.stroke(bez3(pts[0], (84, 52), (94, 70), (116, 58), 16), 8, 2.5)
    sp.paint(flag, 0.55 + 0.3 * np.sin(sp.x * 0.5), ramp("#3a0808", "#7a1410", "#b42a20", "#e04a3a"))
    return sp.rgba()


def th_cave_mouth():
    sp = Cv()
    rng = RNG(1671)
    ridge = [(0, 127), (2, 96), (6, 80), (4, 66), (14, 56), (18, 42), (30, 36), (38, 24), (52, 20), (60, 8), (74, 12), (84, 22), (98, 26), (104, 40), (116, 50), (118, 66), (126, 78), (127, 127)]
    ridge = [(x + rng.uniform(-3, 3), y + rng.uniform(-4, 4)) if 0 < i < 17 else (x, y) for i, (x, y) in enumerate(ridge)]
    rock = sp.poly(ridge)
    n = sp.noise(6, 1672, 3)
    sp.paint(rock, 0.22 + 0.45 * n + 0.14 * np.sin(sp.y * 0.4 + n * 6) + 0.12 * (sp.noise(12, 1678, 2) > 0.6) - 0.1 * (sp.noise(10, 1679, 2) > 0.65), SLATE)
    # snow caught along the ridge and on ledges
    top_y = np.where(rock.any(axis=0), np.argmax(rock, axis=0), 999)[None, :]
    snow = rock & (sp.y < top_y + 9 + 7 * sp.noise(3, 1673) - np.abs(sp.x - 64) * 0.0)
    for (ly, lx0, lx1) in ((50, 10, 38), (70, 90, 120), (38, 70, 96), (92, 2, 24), (96, 106, 126)):
        snow |= rock & sp.rect(lx0, ly, lx1, ly + 4 + 3 * rng.rand())
    sp.paint(snow, sp.bump(snow, 3.0, 0.7, 0.35) + 0.08, SNOW)
    # the mouth, with icicles
    mouth = (sp.ellipse(64, 94, 30, 36) & (sp.y < 100)) | sp.rect(34, 94, 94, 127)
    sp.paint(mouth, 0.05 + 0.1 * sp.noise(4, 1674) + 0.12 * np.clip((sp.y - 80) / 40, 0, 1) * (sp.noise(3, 1675) > 0.6), ramp("#010104", "#04060e", "#0a0f1e", "#141c34"))
    for ix in range(37, 93, 4):
        yt = 94 - 36 * math.sqrt(max(1 - ((ix - 64) / 30.0) ** 2, 0.001))
        L = rng.uniform(7, 20) * (1.0 if abs(ix - 64) < 22 else 0.6)
        sp.paint(sp.poly([(ix - 2.2, yt - 3), (ix + 2.2, yt - 3), (ix + rng.uniform(-0.8, 0.8), yt + L)]), 0.6 + 0.35 * rng.rand(), SNOW)
    sp.paint(sp.ellipse(64, 125, 62, 6) & (sp.y < 127.5), 0.8 + 0.15 * sp.noise(4, 1676), SNOW)
    sp.paint(sp.ellipse(64, 122, 34, 4), 0.85, SNOW)
    return sp.rgba()


def th_chair_white():
    sp = Cv()
    W = BIRCH
    for x0 in (36, 84):
        sp.paint(sp.rect(x0, 4, x0 + 8, 78), sp.hshade(x0, x0 + 8, 0.7, 0.4), W)
        sp.paint(sp.ellipse(x0 + 4, 4, 5, 4), 0.85, W)
    back = sp.rect(44, 10, 84, 70)
    sp.paint(back, 0.66 + 0.1 * np.sin(sp.y * 0.25 + sp.noise(4, 1681) * 5) - 0.1 * (sp.x > 76), W)
    leaf = lens(sp, 64, 66, 64, 12, 15, 0.8)
    sp.paint(leaf, 0.42 + 0.2 * (sp.x < 62) - 0.08 * (sp.x > 70), W)
    sp.paint(leaf & ~lens(sp, 64, 64, 64, 14, 13.5, 0.8), 0.9, W)
    sp.paint(sp.stroke([(64, 64), (64, 16)], 1.6) & leaf, 0.2, W)
    for yy in range(22, 62, 8):
        sp.paint(sp.stroke([(64, yy + 6), (54, yy)], 1.2) & leaf, 0.25, W)
        sp.paint(sp.stroke([(64, yy + 6), (74, yy)], 1.2) & leaf, 0.25, W)
    seat_top = sp.poly([(36, 70), (92, 70), (102, 79), (26, 79)])
    sp.paint(seat_top, 0.88 - 0.1 * np.clip((sp.y - 70) / 9, 0, 1), W)
    sp.paint(sp.rect(26, 79, 102, 90), sp.hshade(26, 102, 0.62, 0.3), W)
    sp.paint(sp.rect(26, 79, 102, 81), 0.9, W)
    for x0 in (28, 90):
        sp.paint(sp.rect(x0, 90, x0 + 10, 127), sp.hshade(x0, x0 + 10, 0.62, 0.45), W)
    sp.paint(sp.rect(38, 106, 90, 112), 0.5, W)
    return sp.rgba()


def th_vial_stand():
    sp = Cv()
    M = ramp("#2a303c", "#59627a", "#9aa6bc", "#d0d8e6", "#f0f4fa", "#ffffff")
    sp.glow(64, 56, 36, 38, COLDHALO, power=1.5, gain=1.3, dither=0.5)
    sp.paint(sp.rect(32, 117, 96, 127), sp.hshade(32, 96, 0.55, 0.3), M)
    sp.paint(sp.rect(38, 111, 90, 118), sp.hshade(38, 90, 0.6, 0.3), M)
    shaft = sp.rect(46, 84, 82, 112)
    sp.paint(shaft, sp.hshade(46, 82, 0.62, 0.5) - 0.12 * (((sp.x - 46) % 9) < 1.5), M)
    sp.paint(sp.rect(38, 74, 90, 86), sp.hshade(38, 90, 0.65, 0.3), M)
    sp.paint(sp.rect(34, 70, 94, 76), 0.85 - 0.2 * (sp.x > 80), M)
    # the vial
    liquid = sp.ellipse(64, 58, 12, 15) & (sp.y > 48)
    glass = sp.ellipse(64, 58, 13, 16)
    sp.paint(glass, 0.5, ramp("#2a4a68", "#6aa0c8", "#b8e0f4"))
    sp.paint(sp.rect(60, 38, 68, 46), 0.55, ramp("#2a4a68", "#6aa0c8", "#b8e0f4"))
    sp.paint(sp.rect(58, 36, 70, 40), 0.9, ramp("#2a4a68", "#6aa0c8", "#b8e0f4"))
    liq_sh = 0.45 + 0.55 * np.clip(1 - np.sqrt(((sp.x - 62) / 11.0) ** 2 + ((sp.y - 56) / 14.0) ** 2), 0, 1) ** 0.7
    sp.paint(liquid, liq_sh, COLD)
    sp.paint(sp.rect(61, 29, 67, 37), 0.4, ramp("#2a1a0c", "#5a3a1c", "#8a5a2c"))
    sp.solid(sp.rect(54, 50, 56, 60) & glass, "#f0ffff")
    return sp.rgba()


def th_ridge_marker():
    sp = Cv()
    sp.paint(sp.ellipse(62, 125, 44, 7) & (sp.y < 127.5), 0.72 + 0.2 * sp.noise(4, 1691), SNOW)
    post = sp.stroke([(56, 127), (62, 90), (70, 16)], 11, 7)
    _wood(sp, post, 52, 76, BARK, 1692, 0.5, 0.4)
    sp.paint(sp.poly([(65, 18), (75, 18), (70, 8)]) | post & (sp.y < 22), 0.5, BARK)
    sp.paint(sp.stroke([(50, 118), (58, 112)], 14, 10) & (sp.y > 112) & (sp.y < 127.5), 0.55, SNOW)
    for (rx, ry, r) in ((42, 122, 8), (80, 123, 6)):
        m = sp.ellipse(rx, ry, r, r * 0.55) & (sp.y < 127.5)
        sp.paint(m, sp.bump(m, r * 0.4, 0.5, 0.6), STONE)
    # a strip of grey cloth snapping straight out in the wind, torn at the end
    path = bez3((71, 30), (86, 18), (100, 42), (122, 26), 24)
    cloth = sp.stroke(path, 12, 4)
    sp.paint(cloth, 0.5 + 0.3 * np.sin(sp.x * 0.45 + 1) + (sp.noise(3, 1693) - 0.5) * 0.2, CLOTH)
    sp.paint(cloth & (sp.x > 104) & (sp.noise(1.5, 1694, 2) > 0.5), 0.9, CLOTH)
    return sp.rgba()


def th_door_far():
    sp = Cv()
    sp.glow(64, 76, 46, 62, COLDHALO, power=1.4, gain=1.3, dither=0.5)
    frame = sp.rect(36, 30, 92, 127) | sp.ellipse(64, 34, 28, 22)
    sp.paint(frame, sp.hshade(36, 92, 0.65, 0.35) + (sp.noise(5, 1701) - 0.5) * 0.12, BIRCH)
    opening = sp.rect(49, 34, 79, 127) | sp.ellipse(64, 36, 15, 20)
    gx = np.clip(1 - np.abs(sp.x - 64) / 17.0, 0, 1)
    sp.paint(opening, 0.15 + 0.85 * gx ** 0.5 * (0.7 + 0.3 * np.clip((sp.y - 20) / 80, 0, 1)), BRIGHT)
    sp.paint(opening & ((sp.x < 52) | (sp.x > 76)), 0.0, BRIGHT)
    sp.paint(frame & ~opening & ((np.abs(sp.x - 64) < 17) | (sp.y < 50)) & ((np.abs(sp.x - 64) < 21)), 0.9, BIRCH)
    spill = sp.poly([(49, 112), (79, 112), (112, 127), (16, 127)])
    sp.paint(spill, 0.35 + 0.5 * np.clip(1 - np.abs(sp.x - 64) / 50, 0, 1), BRIGHT)
    sp.paint(sp.rect(44, 108, 84, 113), 0.45, BIRCH)
    return sp.rgba()


def pc_storm_snow():
    sp = Cv(256, 128)
    n1 = sp.noise(46, 1711, 4)
    n2 = sp.noise(18, 1712, 3)
    a = np.clip((n1 - 0.3) * 2.0, 0, 1) * 0.8 + 0.12 * n2
    a *= np.clip(sp.y / 16.0, 0, 1) * np.clip((127 - sp.y) / 14.0, 0, 1) * np.clip(sp.x / 22.0, 0, 1) * np.clip((255 - sp.x) / 22.0, 0, 1)
    aq = np.clip(np.floor(a * 5 + sp.bt * 0.9) / 5, 0, 0.85)
    sh = 0.25 + 0.5 * n2 + 0.2 * (sp.y / 128.0)
    sp.over(aq, quantise(np.clip(sh, 0, 1), ramp("#5a6c8c", "#8498b4", "#aebed4", "#d4dee8")))
    rng = RNG(1713)
    ang = 0.5  # the wind drives the flakes down and to the right
    for k in range(120):
        x0, y0 = rng.uniform(-10, 250), rng.uniform(-10, 125)
        L = rng.uniform(14, 52)
        m = sp.stroke([(x0, y0), (x0 + L, y0 + L * ang)], 1.5, 0.9)
        env = np.clip(sp.y / 14.0, 0, 1) * np.clip((127 - sp.y) / 12.0, 0, 1) * np.clip(sp.x / 18.0, 0, 1) * np.clip((255 - sp.x) / 18.0, 0, 1)
        sp.over(m * rng.uniform(0.4, 0.85) * env, "#f4f8ff")
    return sp.rgba(outline=False, hard=False)


# ---- deep halls ---------------------------------------------------------------------------------------------------------------------------------------

WETWOOD = ramp("#05060a", "#0e1018", "#181c26", "#242a38", "#343e52", "#4a5a74")
SKIN = ramp("#3a2c20", "#6a5640", "#9a8462", "#c8b68c", "#e8dcb8")
ROPE = ramp("#241a0c", "#4a3818", "#7a6430", "#a8925a", "#d0bc84")
HORN = ramp("#1c1e22", "#3a3e46", "#62666e", "#8e929a", "#b8bcc2", "#dcdee2")
ROCKG = ramp("#0c0e12", "#1c2028", "#2e343e", "#454c58", "#626a78", "#8a92a2")
TIP = ramp("#58647a", "#8c9cb4", "#c0ccdc", "#e8f0f8")
MISTP = ramp("#2a3a4c", "#4c627a", "#7a92aa", "#a8bccc", "#d4e2ec")


def th_pillar_deep():
    sp = Cv()
    shaft = sp.rect(28, 0, 100, 106)
    u = ((sp.x - 28) % 9) / 9.0
    flute = 0.36 + 0.3 * np.sin(u * math.pi) ** 0.8
    sh = flute + 0.2 * np.clip((100 - sp.x) / 72.0, 0, 1) * 0.6 + (sp.noise(5, 1801) - 0.5) * 0.06 - 0.08 * np.clip((sp.x - 28) / 72.0, 0, 1)
    wet = (sp.noise(2.5, 1802, 2) > 0.84) & (((sp.x - 28) % 9) < 4)
    sp.paint(shaft, sh + 0.12 * wet, WETROCK)
    lip = shaft & (((sp.x - 28) % 9) < 1.0) & (sp.noise(2.5, 1803, 2) > 0.62)
    sp.paint(lip, 0.45, COLD)
    sp.paint(sp.rect(28, 0, 31, 106), 0.85, COLD)
    sp.paint(sp.rect(28, 0, 29.2, 106), 1.0, COLD)
    sp.paint(sp.rect(10, 104, 118, 116), sp.hshade(10, 118, 0.35, 0.3) + (sp.noise(5, 1804) - 0.5) * 0.12, WETROCK)
    sp.paint(sp.rect(10, 104, 118, 106), 0.85, COLD)
    sp.paint(sp.rect(2, 116, 126, 128), sp.hshade(2, 126, 0.3, 0.3) + (sp.noise(5, 1805) - 0.5) * 0.12, WETROCK)
    sp.paint(sp.rect(2, 116, 126, 118), 0.8, COLD)
    sp.paint(sp.rect(18, 98, 110, 105), 0.3 + 0.2 * sp.noise(3, 1806), WETROCK)
    return sp.rgba()


def th_cold_light():
    sp = Cv()
    # the long thin shaft falling from the lamp to the floor
    hw = 3.0 + 13.0 * np.clip((sp.y - 56) / 71.0, 0, 1)
    inten = np.clip(1 - np.abs(sp.x - 64) / hw, 0, 1) ** 1.1 * (0.5 + 0.5 * (1 - np.clip((sp.y - 58) / 69.0, 0, 1))) * 1.15
    beam = (inten > sp.bt) & (sp.y > 56)
    sp.paint(beam, inten, COLD, fx=True, dither=0.5)
    sp.glow(64, 36, 30, 30, COLDHALO, power=1.5, gain=1.3, dither=0.5)
    sp.paint(sp.ellipse(64, 124, 26, 3.5) & (sp.bt < 0.6), 0.7, COLD, fx=True)
    _chain(sp, 64, -4, 64, 16, 7, 1.8, 0.5)
    crystal = sp.poly([(64, 14), (77, 28), (74, 50), (64, 62), (54, 50), (51, 28)])
    face = np.where(sp.x < 58, 0.55, np.where(sp.x < 70, 0.85, 0.35))
    sp.paint(crystal, face + 0.15 * np.clip(1 - np.abs(sp.y - 36) / 26, 0, 1) + (sp.noise(4, 1811) - 0.5) * 0.1, COLD)
    sp.solid(sp.line(64, 14, 64, 62, 1.2) & crystal, "#ffffff")
    sp.paint(sp.stroke([(51, 28), (64, 38), (77, 28)], 1.2) & crystal, 1.0, COLD)
    sp.paint(sp.ellipse(64, 14, 4, 4), 0.6, IRON)
    rng = RNG(1812)
    for k in range(14):
        mx, my = 64 + rng.uniform(-22, 22), rng.uniform(70, 124)
        if abs(mx - 64) < 3 + 13 * (my - 56) / 71.0:
            sp.solid(sp.rect(mx, my, mx + 1, my + 1), "#d8f6ff", fx=True)
    return sp.rgba()


def th_drum():
    sp = Cv()
    rock = sp.poly([(10, 127), (22, 108), (46, 102), (84, 104), (108, 110), (120, 127)])
    sp.paint(rock, 0.2 + 0.4 * sp.noise(5, 1821) + 0.1 * np.sin(sp.x * 0.3), WETROCK)
    sp.paint(rock & (sp.y < 108), 0.55, WETROCK)
    body = sp.rect(24, 46, 104, 108) | sp.ellipse(64, 108, 40, 7)
    stave = ((sp.x - 24) % 8)
    sp.paint(body, sp.hshade(24, 104, 0.4, 0.4) + (sp.noise(4, 1822) - 0.5) * 0.12 - 0.14 * (stave < 1), WOOD_D)
    for hy in (52, 100):
        hoop = (sp.rect(24, hy - 3, 104, hy + 3))
        sp.paint(hoop, sp.hshade(24, 104, 0.55, 0.4), BRONZE)
    # the lacing: zigzag rope between the hoops
    for k in range(8):
        xa, xb = 24 + k * 10, 24 + k * 10 + 5
        sp.paint(sp.stroke([(xa, 56), (xb, 97)], 1.7), 0.38, ROPE)
        sp.paint(sp.stroke([(xb, 97), (xa + 10, 56)], 1.7), 0.34, ROPE)
    # the skin, with a faint cold pulse in the middle
    skin = sp.ellipse(64, 46, 40, 10.5)
    pulse = np.clip(1 - np.sqrt(((sp.x - 64) / 36.0) ** 2 + ((sp.y - 46) / 8.5) ** 2), 0, 1)
    sp.paint(skin, 0.5 + 0.2 * sp.noise(4, 1823) + 0.2 * (sp.x < 60), SKIN)
    sp.paint(skin & (pulse > 0.5), 0.2 + 0.5 * pulse, COLD, dither=0.9)
    sp.paint(skin & (pulse > 0.3) & (pulse <= 0.5) & (sp.bt < 0.5), 0.3, COLD, dither=0.5)
    sp.paint(sp.ring(64, 46, 40, 10.5, 2.5), 0.4, BRONZE)
    sp.paint(sp.ring(64, 46, 40, 10.5, 1.2) & (sp.y < 46), 0.75, BRONZE)
    rng = RNG(1824)
    for k in range(13):
        mx, my = 64 + rng.uniform(-30, 30), rng.uniform(12, 40)
        sp.solid(sp.rect(mx, my, mx + 1, my + 1), "#b8e8f4" if rng.rand() < 0.5 else "#7a98a8", fx=True)
    return sp.rgba()


WOOD_D = ramp("#0a0806", "#1a1410", "#2c2218", "#44342a", "#5e4a38", "#7a6048")


def _spikes(sp: Cv, specs, pal, tip_pal=None, tip_frac=0.2, spec_col=None, seed=1):
    rng = RNG(seed)
    for (cx, base, w, h) in sorted(specs, key=lambda s: -s[3]):
        pts = [(cx - w, base + 1), (cx - w * 0.55, base - h * 0.5), (cx - w * 0.2, base - h * 0.85), (cx + rng.uniform(-1.5, 1.5), base - h),
               (cx + w * 0.25, base - h * 0.8), (cx + w * 0.6, base - h * 0.45), (cx + w, base + 1)]
        m = sp.poly(pts)
        lit = -((sp.x - cx) * 0.8 + 0.0) / w
        sp.paint(m, 0.38 + 0.3 * lit + 0.2 * np.clip((sp.y - (base - h)) / h, 0, 1) * 0.3 + (sp.noise(4, seed + int(cx)) - 0.5) * 0.2, pal)
        if tip_pal is not None:
            tip = m & (sp.y < base - h * (1 - tip_frac) + 3 * np.sin(sp.x * 0.7))
            sp.paint(tip, 0.4 + 0.5 * np.clip(1 - (sp.y - (base - h)) / (h * tip_frac), 0, 1) + 0.1 * lit, tip_pal)
        if spec_col:
            sp.solid(sp.stroke([(cx - w * 0.45, base - h * 0.2), (cx - w * 0.28, base - h * 0.7)], 1.4) & m, spec_col)


def th_stalagmite():
    sp = Cv()
    sp.paint(sp.ellipse(64, 126, 62, 5) & (sp.y < 127.5), 0.15 + 0.2 * sp.noise(4, 1831), WETROCK)
    _spikes(sp, [(64, 126, 22, 112), (36, 126, 17, 72), (92, 126, 18, 84), (14, 126, 11, 46), (112, 126, 12, 52), (52, 126, 11, 44), (78, 126, 10, 38)], WETROCK, TIP, 0.2, "#7a92aa", 1832)
    return sp.rgba()


def th_boat():
    sp = Cv()
    # the landing planks the boat is tied at
    sp.paint(sp.rect(0, 113, 128, 128), 0.25 + 0.2 * sp.noise(3, 1841) + 0.25 * (((sp.x + 6) % 22) < 1.5) * -1, WETWOOD)
    sp.paint(sp.rect(0, 113, 128, 115), 0.6, WETWOOD)
    hull = sp.poly([(6, 64), (22, 56), (46, 44), (64, 34), (82, 44), (106, 56), (122, 64), (114, 94), (98, 114), (30, 114), (14, 94)])
    sp.paint(hull, sp.hshade(6, 122, 0.45, 0.2) * 0.9 + 0.1 + 0.12 * np.clip(1 - np.abs(sp.x - 64) / 50, 0, 1) + (sp.noise(5, 1842) - 0.5) * 0.12, WETWOOD)
    for k in range(1, 6):
        for side in (-1, 1):
            pts = bez((64 + side * 3, 40 + k * 11.5), (64 + side * 30, 38 + k * 10), (64 + side * (52 - k * 3), 62 + k * 9), 16)
            sp.paint(sp.stroke(pts, 1.4), 0.9, WETWOOD)
            sp.paint(sp.stroke([(x, y + 1.8) for x, y in pts], 1.4), 0.12, WETWOOD)
    sp.paint(sp.stroke(bez((6, 64), (64, 28), (122, 64)), 4.5), 0.78, WETWOOD)
    stem = sp.poly([(60, 112), (68, 112), (68, 40), (64, 24), (60, 40)])
    sp.paint(stem, sp.hshade(60, 68, 0.62, 0.4) + 0.05, WETWOOD)
    sp.paint(sp.ellipse(64, 26, 4.5, 5), 0.7, WETWOOD)
    _lantern(sp, 64, 4, 24, 11, 24, 0.9)
    # a coil of rope on the bow and the mooring line
    for k, (rx, ry) in enumerate(((13, 7), (9, 5), (5, 3))):
        sp.paint(sp.ring(38, 98, rx, ry, 2.8), 0.55 + 0.1 * k + 0.2 * (sp.x < 38), ROPE)
    sp.paint(sp.stroke(bez((50, 98), (80, 112), (112, 104)), 3.2, 2.6), 0.5, ROPE)
    sp.paint(sp.rect(108, 98, 118, 126), 0.5, WETWOOD)
    sp.paint(sp.ellipse(113, 98, 6, 3), 0.65, WETWOOD)
    return sp.rgba()


def th_rope_post():
    sp = Cv()
    sp.paint(sp.ellipse(64, 125, 50, 5) & (sp.y < 127.5), 0.1 + 0.2 * sp.noise(4, 1851), ramp("#02060a", "#07121e", "#0e2434", "#1a3c52"))
    post = sp.rect(50, 26, 78, 127) | sp.ellipse(64, 26, 14, 6)
    n = sp.noise(4, 1852, 3)
    sp.paint(post, sp.hshade(50, 78, 0.4, 0.4) + np.sin(sp.y * 0.25 + n * 8) * 0.07 + (n - 0.5) * 0.15, BARK)
    sp.paint(post & (sp.noise(2, 1853, 2) > 0.8) & (sp.x < 66), 0.85, WETWOOD)
    sp.paint(sp.ellipse(64, 25, 13, 5), 0.5 + 0.2 * sp.noise(3, 1854), BARK)
    for k in range(6):
        y0 = 34 + k * 7.5
        sp.paint(sp.stroke([(48, y0 + 5), (64, y0 + 8), (80, y0)], 6), 0.45 + 0.35 * (k % 2) + 0.1 * np.sin(sp.x * 1.5), ROPE)
    sp.paint(sp.stroke(bez3((80, 70), (100, 76), (96, 108), (72, 106), 18), 5.5, 4.5), 0.5 + 0.2 * np.sin(sp.y * 0.9 + sp.x * 0.5), ROPE)
    sp.paint(sp.ellipse(76, 106, 8, 5), 0.2, ROPE)
    sp.paint(sp.stroke([(52, 84), (52, 118)], 3), 0.65, WETWOOD)
    return sp.rgba()


def th_horn():
    sp = Cv()
    # the rock it rests on
    rk = sp.poly([(44, 127), (48, 108), (60, 96), (84, 92), (108, 100), (124, 118), (126, 127)])
    n = sp.noise(5, 1861, 3)
    sp.paint(rk, 0.3 + 0.4 * n + 0.15 * (sp.y < 100), ROCKG)
    sp.paint(rk & (sp.noise(2.5, 1862, 2) > 0.8), 0.85, ROCKG)
    # a ranger's grey cloak thrown down beside it
    cl = sp.poly([(2, 127), (4, 110), (14, 98), (30, 92), (44, 98), (52, 112), (56, 127)])
    fold = np.sin((sp.x * 0.5 - sp.y * 0.35) + 1.0 * np.sin(sp.x * 0.2)) * 0.5 + 0.5
    sp.paint(cl, 0.45 + 0.4 * fold + (sp.noise(3, 1863) - 0.5) * 0.1, CLOTH, dither=0.5)
    sp.paint(cl & (sp.y > 120), 0.28, CLOTH, dither=0.3)
    sp.paint(sp.stroke([(10, 118), (30, 104), (50, 112)], 2) & cl, 0.15, CLOTH, dither=0.3)
    sp.paint(sp.ellipse(26, 98, 10, 5), 0.8, CLOTH)
    sp.paint(sp.ellipse(44, 106, 3, 3), 0.7, BRONZE)
    # the horn: a long curve with a flaring bell, bound in leather and iron
    path = bez3((50, 92), (70, 82), (96, 94), (120, 62), 40)
    horn = sp.stroke(path, 8, 26)
    sp.paint(horn, sp.bump(horn, 3.2, 0.55, 0.65) + 0.05 * np.sin(sp.x * 0.3 + sp.y * 0.2) + (sp.noise(4, 1864) - 0.5) * 0.1, HORN)
    bell = sp.ellipse(119, 62, 8, 13)
    sp.paint(bell, 0.12, HORN)
    for t, kind in ((0.07, "iron"), (0.34, "leather"), (0.4, "leather"), (0.68, "iron"), (0.95, "iron")):
        i = int(t * 39)
        (ax, ay), (bx, by) = path[max(i - 1, 0)], path[min(i + 1, 39)]
        dxp, dyp = by - ay, bx - ax
        L = max(math.hypot(dxp, dyp), 1e-6)
        wdt = 4.5 + 10.0 * t
        band = sp.stroke([(path[i][0] - dxp / L * wdt, path[i][1] + dyp / L * wdt), (path[i][0] + dxp / L * wdt, path[i][1] - dyp / L * wdt)], 3.6 if kind == "leather" else 3.0)
        band &= horn
        if kind == "leather":
            sp.paint(band, 0.45 + 0.2 * (sp.y < path[i][1]), OAK)
        else:
            sp.paint(band, 0.4 + 0.3 * (sp.y < path[i][1]), IRON)
    return sp.rgba()


def th_bridge_rail():
    sp = Cv()
    sh, mort = bricks(128, rows=6, cols=3, mortar=1, seed=1871, wear=0.5)
    wall = sp.rect(0, 80, 128, 127)
    sp.paint(wall, sh * 0.6 + 0.15 + (sp.noise(5, 1872) - 0.5) * 0.15, SLATE)
    sp.solid(wall & (mort > 0.5), "#05070c")
    sp.paint(sp.rect(0, 72, 128, 82), 0.5 + 0.3 * (sp.y < 75) + (sp.noise(4, 1873) - 0.5) * 0.15, SLATE)
    sp.paint(sp.rect(0, 72, 128, 74), 0.85, COLD)
    for x0 in (12, 92):
        post = sp.rect(x0, 40, x0 + 24, 127)
        sp.paint(post, sp.hshade(x0, x0 + 24, 0.4, 0.35) + (sp.noise(4, 1874 + x0) - 0.5) * 0.15, SLATE)
        sp.paint(sp.rect(x0, 40, x0 + 1.5, 127), 0.9, COLD)
        sp.paint(sp.poly([(x0 - 4, 42), (x0 + 28, 42), (x0 + 20, 28), (x0 + 4, 28)]), 0.55 + 0.25 * (sp.x < x0 + 12), SLATE)
        sp.paint(sp.rect(x0 - 4, 42, x0 + 28, 46), 0.4, SLATE)
        sp.paint(sp.ring(x0 + 12, 54, 4, 4, 2), 0.6, IRON)
    path = bez((36, 54), (64, 96), (92, 54), 26)
    for i, (x, y) in enumerate(path):
        if i % 2 == 0:
            sp.paint(sp.ring(x, y, 3.6, 4.2, 1.8), 0.5 + 0.2 * (i % 4 == 0), IRON)
        else:
            sp.paint(sp.ellipse(x, y, 4.2, 1.8), 0.4, IRON)
    return sp.rgba()


def th_mist():
    sp = Cv()
    n = sp.noise(30, 1881, 4)
    n2 = sp.noise(12, 1882, 3)
    env = np.clip(1 - ((sp.y - 98) / 40.0) ** 2, 0, 1) * np.clip(sp.x / 18.0, 0, 1) * np.clip((127 - sp.x) / 18.0, 0, 1)
    m = (n * 0.8 + n2 * 0.2) * env
    on = m > 0.30 + sp.bt * 0.22
    sp.paint(on, 0.25 + 1.0 * m + 0.35 * np.clip((100 - sp.y) / 40.0, 0, 1) * (n > 0.5), MISTP, fx=True, dither=0.8)
    return sp.rgba(outline=False)


def th_lantern_boat():
    sp = Cv()
    sp.paint(sp.ellipse(64, 114, 54, 17) & (sp.y < 127.5), sp.bump(sp.ellipse(64, 114, 54, 17), 6, 0.45, 0.6) + (sp.noise(4, 1891) - 0.5) * 0.2, WETROCK)
    sp.paint(sp.ellipse(64, 114, 54, 17) & (sp.noise(2, 1892, 2) > 0.8) & (sp.y < 112), 0.85, WETROCK)
    _lantern(sp, 64, 54, 40, 22, 40, 1.0)
    return sp.rgba()


def th_waterfall_edge():
    sp = Cv()
    half = 46 + 4 * sp.y / 128.0
    water = (np.abs(sp.x - 64) < half) & (sp.y > 12)
    lip = 64 + 12 * (((sp.x - 64) / 46.0) ** 2) * -1 + 10
    above = water & (sp.y < lip)
    below = water & (sp.y >= lip)
    rip = np.sin(sp.y * 0.9 + 2 * np.sin(sp.x * 0.1)) * 0.5 + 0.5
    near = np.clip((sp.y - 14) / (lip - 14 + 1e-3), 0, 1)
    sp.paint(above, 0.2 + 0.3 * near + 0.1 * rip * near + 0.2 * (near > 0.85) + (sp.noise(5, 1901) - 0.5) * 0.1, WHITEW)
    nx = sp.noise(3.2, 1902, 3)
    streak = 0.5 + 0.5 * np.sin(sp.x * 1.35 + nx * 7.0)
    fall = np.clip((sp.y - lip) / (127 - lip + 1e-3), 0, 1)
    sp.paint(below, 0.9 - 0.3 * fall + 0.25 * (streak - 0.5) - 0.15 * (streak < 0.2) + 0.12 * (sp.noise(2, 1903, 2) > 0.78) * fall, WHITEW)
    sp.paint(below & (sp.y > 108) & (sp.bt < 0.5 * (sp.y - 108) / 19.0 + 0.2), 0.95, WHITEW, fx=True)
    # black rock either side, jagged
    rock = ~water & (sp.y > 30 + 12 * sp.noise(6, 1904) + 0.55 * np.abs(sp.x - 64) * 0 - 0.4 * (np.abs(sp.x - 64) - 46) * 0)
    rock &= (np.abs(sp.x - 64) > 36)
    rock &= ~water
    sp.paint(rock, 0.2 + 0.45 * sp.noise(5, 1905) + 0.2 * (sp.noise(2, 1906, 2) > 0.72), WETROCK)
    sp.paint(rock & (sp.noise(2.2, 1907, 2) > 0.86), 0.5, TIP)
    # spray rising off the lip
    rng = RNG(1908)
    for k in range(50):
        px = 64 + rng.uniform(-40, 40)
        py = 62 - abs(rng.normal(0, 12)) - ((px - 64) / 46.0) ** 2 * 0 + 6
        sp.solid(sp.rect(px, py, px + (2 if rng.rand() < 0.3 else 1), py + 1), "#e8f4fc" if rng.rand() < 0.6 else "#9ab8d0", fx=True)
    return sp.rgba()


def _limb(rng, x0, y0, ang, segs, bend=1.0, ytop=6):
    """Joint positions of one limb: each segment turns the other way from the last, like an insect's leg that goes up, folds over and comes down again."""
    pts = [(x0, y0)]
    a = ang
    x, y = x0, y0
    sgn = rng.choice([-1, 1])
    for L in segs:
        x += math.cos(a) * L
        y += math.sin(a) * L
        if y < ytop:
            y = ytop
            a = abs(a) * 0.9 + 0.5
        pts.append((x, y))
        a += sgn * rng.uniform(0.7, 1.3) * bend
        sgn = -sgn if rng.rand() < 0.75 else sgn
    return pts


def pc_drowned_thing():
    sp = Cv(256, 128)
    rng = RNG(1911)
    wl = 100
    pw = PALEFLESH
    # the black lake with slow rings
    pool = sp.ellipse(128, 111, 126, 15)
    sp.paint(pool, 0.1 + 0.25 * sp.noise(8, 1912, 2), NIGHTW)
    for rx, ry, ph in ((60, 6, 0), (86, 9, 1), (110, 12, 2)):
        r = sp.ring(128, 108, rx, ry, 1.3) & pool & (np.sin(sp.x * 0.35 + ph * 2) > -0.2)
        sp.paint(r, 0.55 - 0.1 * ph, NIGHTW)
    limbs = []
    for i, bx in enumerate(np.linspace(30, 226, 12)):
        by = wl - 10 - 20 * math.exp(-((bx - 128) / 62.0) ** 2)
        ang = -math.pi / 2 + rng.uniform(-0.8, 0.8) + (bx - 128) / 128.0 * 0.7
        segs = [rng.uniform(22, 32), rng.uniform(26, 38), rng.uniform(22, 34), rng.uniform(18, 30), rng.uniform(14, 24)]
        limbs.append(_limb(rng, bx, by + 6, ang, segs, 1.0))

    def draw_limb(pts, wb, shade_off):
        n = len(pts) - 1
        for j in range(n):
            wa = wb * (1 - j / n) + 1.6
            wz = wb * (1 - (j + 1) / n) + 1.6
            m = sp.stroke([pts[j], pts[j + 1]], wa, wz)
            sp.paint(m, sp.bump(m, 1.9, 0.52, 0.7) + shade_off, pw)
            kn = sp.ellipse(pts[j + 1][0], pts[j + 1][1], wz * 0.5 + 1.8, wz * 0.5 + 1.8)
            sp.paint(kn, sp.bump(kn, 1.4, 0.55, 0.7) + shade_off + 0.05, pw)
        sp.solid(sp.line(pts[0][0] - 1, pts[0][1], pts[0][0] - 1, pts[0][1] - 1, 1) & False, "#ffffff")

    order = list(range(len(limbs)))
    rng.shuffle(order)
    back_ones = order[::2]
    for i in back_ones:
        draw_limb(limbs[i], 10.0, -0.16)
    # the back: a long, low, wet hump, mottled, with a ridge of pale knobs along the spine
    back = sp.ellipse(128, wl + 4, 100, 30) & (sp.y < wl + 3)
    back |= sp.ellipse(52, wl + 4, 42, 14) & (sp.y < wl + 3)
    back |= sp.ellipse(204, wl + 4, 42, 14) & (sp.y < wl + 3)
    mott = sp.noise(7, 1913, 3)
    shd = sp.bump(back, 9, 0.42, 0.7) + 0.05 * np.sin((sp.x - 128) * 0.4) + (mott - 0.5) * 0.3
    sp.paint(back, shd, pw)
    sp.paint(back & (mott > 0.62) & (sp.y > wl - 22), 0.2, pw)
    sp.paint(back & (((sp.x - 20) % 17) < 1.4) & (sp.y > wl - 28), 0.1, pw)
    for kx in range(26, 234, 17):
        if abs(kx - 128) < 100:
            topy = wl + 4 - 30 * math.sqrt(max(1 - ((kx - 128) / 100.0) ** 2, 0))
        else:
            topy = wl - 2
        kn = sp.ellipse(kx, topy + 2, 5.0, 4.2) & (sp.y < wl + 3)
        sp.paint(kn, sp.bump(kn, 1.6, 0.62, 0.7) + 0.1, pw)
    for i in order[1::2]:
        draw_limb(limbs[i], 11.0, 0.0)
    # water streaming off the back and the limbs
    for k in range(26):
        px = rng.uniform(34, 222)
        if abs(px - 128) < 96:
            topy = wl + 4 - 30 * math.sqrt(max(1 - ((px - 128) / 100.0) ** 2, 0)) + rng.uniform(2, 14)
            sp.solid(sp.rect(px, topy, px + 1, wl + 1) & (sp.bt < 0.8), "#7eaabc", fx=True)
    for pts in limbs:
        for (jx, jy) in pts[2:-1]:
            ly1 = min(jy + rng.uniform(8, 24), wl - 1)
            if ly1 > jy + 3:
                sp.solid(sp.rect(jx, jy + 3, jx + 1, ly1) & (sp.a == 0) & (sp.bt < 0.75), "#8cb4c4", fx=True)
    foam = (np.abs(sp.y - (wl + 3)) < 2.2) & pool & (np.abs(sp.x - 128) < 112) & (sp.bt < 0.7)
    sp.paint(foam, 0.75, NIGHTW, fx=True)
    sp.solid(foam & (sp.bt < 0.3), "#e0f0f4", fx=True)
    return sp.rgba(outline=True)


# ---- ash land -----------------------------------------------------------------------------------------------------------------------------------------

DEAD = ramp("#050404", "#0e0a09", "#1a1412", "#2a201c", "#3e322c", "#54443a")
REDHALO = ramp("#3a0a0e", "#7a1618", "#b83034", "#e86a6c", "#ffb4b0")
SHEEN = ramp("#0a0a10", "#1c1c28", "#34364a", "#58607a", "#8a96b4")


def _fire(sp: Cv, cx, base_y, w, h, seed, pal=FIRERED, n=5, gain=1.0):
    """Tongues of flame rising from base_y (the underworld's _flames with its own palette)."""
    rng = RNG(seed)
    nz = noise(sp.n, 6, seed, 2)[:sp.h, :sp.w]
    for k in range(n):
        fx = cx + (k - n // 2) * w * 0.18 + rng.uniform(-2, 2)
        fh = h * (0.55 + 0.45 * rng.rand()) * (1.0 - abs(k - n // 2) * 0.18)
        fw = w * 0.22
        u = (base_y - sp.y) / fh
        wid = fw * np.clip(1 - u, 0, 1) ** 0.8 * (0.8 + 0.4 * nz)
        m = (u >= 0) & (u <= 1) & (np.abs(sp.x - fx - u * u * 3 * math.sin(k + 1)) < wid)
        heat = np.clip(1.0 - u * 1.1 - np.abs(sp.x - fx) / (fw * 1.5) * 0.4, 0, 1)
        sp.paint(m, (0.25 + 0.75 * heat) * gain, pal)


def _plume(sp: Cv, path, w0, w1, pal, seed, shade0=0.5, fx=True, dens=1.0):
    """A dithered column of smoke or glow along a path: wide soft puffs thinning with height."""
    rng = RNG(seed)
    k = len(path)
    for i, (x, y) in enumerate(path):
        t = i / (k - 1)
        w = w0 + (w1 - w0) * t
        for j in range(3):
            px, py = x + rng.uniform(-w * 0.4, w * 0.4), y + rng.uniform(-3, 3)
            d = np.sqrt(((sp.x - px) / w) ** 2 + ((sp.y - py) / (w * 0.8)) ** 2)
            inten = np.clip(1 - d, 0, 1) ** 1.0 * (1 - t * 0.7) * dens
            m = (inten > sp.bt) & (sp.a == 0)
            sp.paint(m, shade0 + 0.4 * inten - 0.2 * t, pal, fx=fx, dither=0.5)


def th_reed_clump():
    sp = Cv()
    _mound(sp, 64, 125, 52, 7, ramp("#02080a", "#06141a", "#0c2428", "#143a38"), 2001)
    rng = RNG(2002)
    # the bulrushes: five tall stems with dark brown heads
    for sx, hh in ((38, 100), (52, 112), (72, 106), (88, 96), (100, 84)):
        top = 126 - hh
        lean = (sx - 64) * 0.15
        stem = sp.stroke(bez((sx - lean * 0.5, 126), (sx, 126 - hh * 0.5), (sx + lean, top + 10)), 2.6, 1.6)
        sp.paint(stem, 0.4 + 0.3 * rng.rand(), TEAL)
        hd = sp.ellipse(sx + lean, top + 5, 3.6, 10)
        sp.paint(hd, 0.25 + 0.5 * np.clip(-(sp.x - (sx + lean)) / 4 + 0.5, 0, 1) + 0.12 * np.sin(sp.y * 1.6), ramp("#0e0806", "#2a1810", "#4a2c1c", "#6e4630"))
        sp.paint(sp.stroke([(sx + lean, top - 6), (sx + lean, top - 1)], 1.4), 0.5, TEAL)
    _blades(sp, 64, 126, 44, 38, 40, 92, 2003, TEAL, 4.0, 22, (0.25, 0.9))
    _blades(sp, 64, 126, 16, 26, 20, 50, 2004, ramp("#04100e", "#0a2422", "#125048", "#1c7466"), 3.2, 12)
    for k in range(16):
        mx, my = 64 + rng.uniform(-44, 44), rng.uniform(14, 100)
        sp.solid(sp.rect(mx, my, mx + 1, my + 1) & (sp.a == 0), "#9af0a0" if rng.rand() < 0.5 else "#3ac060", fx=True)
    return sp.rgba()


def th_marsh_light():
    sp = Cv()
    cx, cy, R = 64, 48, 25
    sp.glow(cx, cy, 44, 44, MINT, power=1.6, gain=1.3, dither=0.5)
    # the wisp trailing below
    path = bez3((64, 70), (50, 86), (80, 98), (64, 122), 24)
    for i, (x, y) in enumerate(path):
        t = i / 23.0
        w = 13 * (1 - t) + 2
        d = np.abs(sp.x - x) / w
        inten = np.clip(1 - d, 0, 1) * (1 - t * 0.65) * np.clip(1 - np.abs(sp.y - y) / 4.5, 0, 1)
        sp.paint((inten > sp.bt * 0.8) & (sp.a == 0), 0.3 + 0.6 * inten, BIOLUM, fx=True, dither=0.5)
    globe = sp.ellipse(cx, cy, R, R)
    d = np.sqrt((sp.x - cx + 5) ** 2 + (sp.y - cy + 6) ** 2) / R
    sp.paint(globe, 0.95 - 0.6 * np.clip(d, 0, 1.3) ** 1.2, BIOLUM)
    sp.paint(sp.ring(cx, cy, R, R, 2.0), 0.3, BIOLUM)
    # the sad almost-face: two slanting eye hollows and a small downturned mouth hollow, drawn in the glow
    hol = ramp("#041a14", "#0a3a2a", "#145a3c", "#2a8a58")
    for sgn in (-1, 1):
        eye = lens(sp, cx + sgn * 14, cy + 2, cx + sgn * 5, cy - 8, 4.2, 0.7)
        eye = lens(sp, cx + sgn * 15, cy + 3, cx + sgn * 5, cy - 9, 4.4, 0.7)
        sp.paint(eye, 0.1 + 0.55 * np.clip((sp.y - (cy - 9)) / 14.0, 0, 1) * 0.5, hol)
    mouth = sp.ellipse(cx, cy + 14, 6.2, 4.2) | sp.stroke(bez((cx - 10, cy + 12), (cx, cy + 6), (cx + 10, cy + 12)), 2.6)
    sp.paint(mouth, 0.1 + 0.3 * np.clip((sp.y - (cy + 10)) / 8.0, 0, 1), hol)
    return sp.rgba()


def th_gate_black():
    sp = Cv()
    GB = ramp("#0a0804", "#201608", "#3e2a10", "#5e4018", "#82602a", "#a88440")
    sh, mort = bricks(128, rows=8, cols=3, mortar=1, seed=2011, wear=0.3)
    wall = sp.rect(2, 2, 126, 127)
    sheen = (0.5 + 0.5 * np.sin((sp.x + sp.y * 1.3) * 0.16)) ** 6
    sp.paint(wall, 0.3 + sh * 0.4 + 0.2 * sheen + (sp.noise(5, 2012) - 0.5) * 0.1, BLACKST)
    sp.solid(wall & (mort > 0.5), "#06060a")
    arch = sp.rect(20, 42, 108, 127) | sp.ellipse(64, 44, 44, 30)
    arch &= sp.y >= 14
    ring = sp.ring(64, 44, 53, 35, 8) & (sp.y < 44)
    ring |= sp.rect(11, 44, 20, 127) | sp.rect(108, 44, 117, 127)
    sp.paint(ring, 0.55 + 0.2 * (sp.noise(2, 2020, 2) > 0.5) + 0.1 * sp.noise(3, 2019), BLACKST)
    sp.solid(ring & (((np.arctan2(sp.y - 44, sp.x - 64) * 13) % 2.0) < 0.12), "#06060a")
    door = ramp("#020203", "#0a0a10", "#14141c", "#1e1e28", "#2a2a36")
    plank = ((sp.x - 20) % 11) < 1.2
    sp.paint(arch, sp.hshade(20, 108, 0.34, 0.2) + (sp.noise(4, 2013) - 0.5) * 0.14 - 0.14 * plank, door)
    sp.solid(arch & (np.abs(sp.x - 64) < 1.4), "#010102")
    for yy in (44, 66, 88, 108):
        for (x0, x1) in ((20, 63), (65, 108)):
            strap = sp.rect(x0, yy, x1, yy + 6) & arch
            sp.paint(strap, 0.42 + 0.25 * (sp.y < yy + 2) - 0.2 * (sp.y > yy + 4) + (sp.noise(3, 2014) - 0.5) * 0.15, GB)
            for sx in range(x0 + 5, x1 - 2, 10):
                sp.paint(sp.ellipse(sx, yy + 3, 1.7, 1.7), 0.85, GB)
    for vx in (26, 56, 71, 100):
        sp.paint(sp.rect(vx, 30, vx + 4, 127) & arch, 0.28 + 0.3 * (sp.x < vx + 2), GB)
    sp.paint(sp.rect(61, 40, 67, 127) & arch, 0.22 + 0.25 * (sp.x < 64), GB)
    rng = RNG(2015)
    for k in range(19):
        x = 2 + k * 7 + rng.uniform(-3, 3)
        y = 119 + rng.uniform(-6, 4)
        r = rng.uniform(6, 11)
        m = sp.ellipse(x, y, r, r * 0.6) & (sp.y < 127.5)
        sp.paint(m, sp.bump(m, r * 0.4, 0.5, 0.6) + (sp.noise(3, 2016 + k) - 0.5) * 0.2, BLACKST)
        sp.solid(m & (sp.y < y - r * 0.3) & (sp.x < x - 1) & (sp.bt < 0.45), "#7a8aa8")
    return sp.rgba()


def th_wall_crack():
    sp = Cv()
    sh, mort = bricks(128, rows=9, cols=3, mortar=1, seed=2021, wear=0.3)
    slab = sp.rect(14, 0, 114, 127)
    rng = RNG(2022)
    cpts = [(62, -2)]
    for y in range(8, 128, 10):
        cpts.append((cpts[-1][0] + rng.uniform(-6, 6) + (60 - cpts[-1][0]) * 0.2, y))
    crack = sp.stroke(cpts, 4.5, 6.5)
    lit = np.clip(sp.blur(crack, 6.0) * 2.4, 0, 1)
    wsm = ramp("#030304", "#0a0a0e", "#16121a", "#3a1a12", "#7a3010", "#c86a1c", "#ffb040")
    sp.paint(slab, 0.14 + sh * 0.35 + (sp.noise(5, 2023) - 0.5) * 0.1 + 0.55 * lit ** 1.4, wsm)
    sp.solid(slab & (mort > 0.5) & (lit < 0.3), "#020203")
    sp.solid(crack, "#0a0204")
    core = sp.stroke(cpts, 1.8, 2.6)
    sp.paint(core, 0.7 + 0.3 * sp.noise(3, 2024), HEAT)
    # ash trickling out of it and heaped at the foot
    for k in range(16):
        ax = cpts[3][0] + rng.uniform(-3, 4) + k * 0.3
        ay = rng.uniform(50, 118)
        sp.solid(sp.rect(ax, ay, ax + 1, ay + rng.uniform(2, 8)) & (sp.bt < 0.8), "#8a8078" if rng.rand() < 0.6 else "#5a524e", fx=True)
    sp.paint(sp.ellipse(cpts[-2][0], 126, 26, 6) & (sp.y < 127.5), 0.55 + 0.3 * sp.noise(3, 2025), ASH)
    return sp.rgba()


def _bell_body(sp: Cv, cx, top, h, wmax, seed):
    t = np.clip((sp.y - top) / h, 0, 1)
    hw = wmax * (0.2 + 0.45 * (1 - (1 - np.minimum(t / 0.3, 1)) ** 2) + 0.35 * (np.maximum(t - 0.45, 0) / 0.55) ** 2.2)
    body = (np.abs(sp.x - cx) < hw) & (sp.y >= top) & (sp.y <= top + h)
    n = sp.noise(5, seed, 3)
    shade = sp.hshade(cx - wmax, cx + wmax, 0.5, 0.5) * 0.85 + 0.1 + (n - 0.5) * 0.2
    sp.paint(body, shade, BRONZE)
    patina = body & ((n > 0.52) | ((sp.x > cx) & (n > 0.4))) & (np.sin(sp.x * 0.7 + n * 9) > -0.1)
    sp.paint(patina, 0.25 + 0.5 * n + 0.2 * (sp.x < cx), PATINA)
    for ty in (0.28, 0.82):
        band = body & (np.abs(sp.y - (top + h * ty)) < 2.2)
        sp.paint(band, 0.4 + 0.5 * (sp.y < top + h * ty), BRONZE)
    sp.paint(sp.ellipse(cx, top + h, wmax * 1.02, 4.4), 0.08, ramp("#030504", "#0a0e0c", "#141a16"))
    sp.paint(sp.ellipse(cx, top + h - 1, wmax * 0.18, 4), 0.45, BRONZE)
    sp.paint(sp.rect(cx - 5, top - 5, cx + 5, top + 3), 0.45, IRON)
    sp.paint(sp.ellipse(cx, top - 6, 4, 3), 0.65, IRON)
    return body


def th_bell():
    sp = Cv()
    for (x0, x1) in ((16, 24), (112, 104)):
        sp.paint(sp.stroke([(x0, 127), (x1, 26)], 11, 8), 0.4 + 0.15 * sp.noise(3, 2031), ramp("#06070a", "#12141a", "#20242c", "#323844", "#484f5e"))
    sp.paint(sp.rect(10, 16, 118, 28), sp.hshade(10, 118, 0.4, 0.2) + 0.35 * (sp.y < 19), IRON)
    sp.paint(sp.stroke([(24, 60), (64, 30)], 4) | sp.stroke([(104, 60), (64, 30)], 4), 0.35, IRON)
    sp.paint(sp.rect(60, 26, 68, 38), 0.5, IRON)
    _bell_body(sp, 64, 40, 64, 36, 2032)
    sp.paint(sp.stroke(bez3((88, 28), (96, 52), (84, 80), (92, 114), 20), 3.2, 3.0), 0.5 + 0.2 * np.sin(sp.y * 0.9), ROPE)
    sp.paint(sp.ellipse(92, 116, 4, 4.5), 0.35, ROPE)
    return sp.rgba()


def th_bell_row():
    sp = Cv()
    for (x0, x1) in ((8, 10), (118, 120)):
        sp.paint(sp.stroke([(x0, 18), (x1, 127)], 10, 11), sp.hshade(x0 - 6, x0 + 6, 0.45, 0.3) + 0.1 * sp.noise(4, 2041), BARK)
    for k in range(4):
        sp.paint(sp.rect(0, 120 + k * 0, 0, 120), 0.0, STONE)
    sp.paint(sp.rect(0, 118, 22, 127), 0.35 + 0.2 * sp.noise(3, 2042), STONE)
    sp.paint(sp.rect(106, 118, 128, 127), 0.35 + 0.2 * sp.noise(3, 2043), STONE)
    beam = sp.stroke([(2, 16), (126, 20)], 11, 11)
    _wood(sp, beam, 0, 128, BARK, 2044, 0.5, 0.3, 0.12, vertical=False)
    _bell_body(sp, 36, 26, 38, 15, 2045)
    _bell_body(sp, 70, 26, 70, 29, 2046)
    _bell_body(sp, 106, 26, 50, 19, 2047)
    for (x0, x1, y1) in ((14, 18, 100), (52, 50, 112), (90, 88, 108)):
        sp.paint(sp.stroke(bez((x0, 22), ((x0 + x1) / 2 + 3, 60), (x1, y1)), 2.6, 2.4), 0.5 + 0.2 * np.sin(sp.y * 0.9), ROPE)
        sp.paint(sp.ellipse(x1, y1 + 2, 3.2, 3.6), 0.35, ROPE)
    return sp.rgba()


def th_tower_light():
    sp = Cv()
    ridge = sp.poly([(0, 127), (14, 116), (34, 108), (54, 102), (74, 102), (96, 108), (112, 116), (127, 127)])
    sp.paint(ridge, 0.2 + 0.3 * sp.noise(5, 2051) + 0.2 * (sp.y < 108), ASH)
    sp.glow(64, 22, 28, 30, REDHALO, power=1.5, gain=1.3, dither=0.5)
    tower = sp.poly([(53, 104), (75, 104), (71, 36), (57, 36)])
    sp.paint(tower, sp.hshade(53, 75, 0.28, 0.35) + (sp.noise(5, 2052) - 0.5) * 0.12, SLATE)
    sp.paint(sp.rect(50, 26, 78, 38), sp.hshade(50, 78, 0.3, 0.3), SLATE)
    for tx in (50, 59, 68):
        sp.paint(sp.rect(tx, 18, tx + 6, 27), sp.hshade(tx, tx + 6, 0.3, 0.3), SLATE)
    for wy in (56, 74, 92):
        sp.solid(sp.rect(62, wy, 66, wy + 6), "#04060a")
    sp.paint(sp.ellipse(64, 32, 3.4, 5), 0.35, REDHALO)
    sp.solid(sp.ellipse(64, 32, 2.0, 3.2), "#ffd8d0")
    sp.paint(sp.rect(49, 37, 79, 40), 0.55, SLATE)
    return sp.rgba()


def th_dead_tree():
    sp = Cv()
    rng = RNG(2061)
    segs = []

    def grow(x, y, ang, L, w, depth):
        if depth > 5 or w < 1.1:
            return
        x2 = x + math.cos(ang) * L
        y2 = y + math.sin(ang) * L
        mid = ((x + x2) / 2 + rng.uniform(-3, 3), (y + y2) / 2 + rng.uniform(-3, 3))
        segs.append(([(x, y), mid, (x2, y2)], w, w * 0.72))
        n = 2 if depth > 0 or rng.rand() < 0.5 else 3
        for i in range(n):
            da = (i - (n - 1) / 2.0) * rng.uniform(0.55, 0.9) + rng.uniform(-0.3, 0.3) + 0.04
            if depth == 0:
                da *= 1.1
            grow(x2, y2, ang + da, L * rng.uniform(0.66, 0.84), w * 0.66, depth + 1)

    base = bez((64, 127), (58, 100), (66, 76), 10)
    segs.append((base, 17, 11))
    grow(66, 76, -math.pi / 2 + 0.1, 24, 10.5, 0)
    tree = np.zeros((128, 128), bool)
    for pts, w0, w1 in segs:
        tree |= sp.stroke(pts, w0, w1)
    tree |= sp.poly([(44, 127), (86, 127), (72, 108), (56, 108)])
    sp.paint(tree, 0.28 + 0.25 * sp.noise(3, 2062) + 0.15 * (sp.noise(1.8, 2063, 2) > 0.7) - 0.1 * np.clip((sp.x - 60) / 50, 0, 1), DEAD)
    # ash caught on the upper side of the branches
    for pts, w0, w1 in segs:
        if w0 < 2.0:
            continue
        up = sp.stroke([(x, y - w0 * 0.42) for x, y in pts], w0 * 0.45, w1 * 0.4) & tree & (sp.bt < 0.8)
        sp.paint(up, 0.5 + 0.35 * rng.rand(), ASH)
    sp.paint(sp.ellipse(64, 125, 34, 4) & (sp.y < 127.5), 0.5 + 0.2 * sp.noise(3, 2064), ASH)
    return sp.rgba()


def th_stake():
    sp = Cv()
    sp.paint(sp.ellipse(63, 124, 40, 6) & (sp.y < 127.5), 0.45 + 0.3 * sp.noise(3, 2071), ASH)
    stake = sp.poly([(55, 127), (55, 30), (63, 14), (71, 30), (71, 127)])
    _wood(sp, stake, 55, 71, ramp("#060403", "#140e0a", "#2a1c12", "#46301e", "#664630"), 2072, 0.5, 0.4, 0.1)
    sp.paint(stake & (sp.noise(2, 2073, 2) > 0.8), 0.15, DEAD)
    sp.paint(sp.rect(52, 72, 74, 82), sp.hshade(52, 74, 0.5, 0.5), IRON)
    sp.paint(sp.ellipse(63, 77, 3.2, 3.2), 0.7, IRON)
    path = bez3((72, 80), (112, 78), (94, 100), (100, 110), 14)
    for i, (x, y) in enumerate(path):
        if i % 2 == 0:
            sp.paint(sp.ring(x, y, 5.2, 4.2, 2.4), 0.55 + 0.1 * (i % 4 == 0), IRON)
        else:
            sp.paint(sp.ellipse(x, y, 5.0, 2.2), 0.4, IRON)
    cuff = sp.ring(103, 117, 12, 9, 5) & ~(sp.rect(95, 100, 111, 114))
    sp.paint(cuff, sp.hshade(91, 115, 0.55, 0.5) + 0.2 * (sp.y < 112), IRON)
    sp.paint(sp.rect(91, 112, 98, 120), 0.5, IRON)
    sp.paint(sp.rect(108, 112, 115, 120), 0.3, IRON)
    sp.solid(sp.ellipse(94.5, 116, 1.5, 1.5) | sp.ellipse(111.5, 116, 1.5, 1.5), "#06070a")
    return sp.rgba()


def th_tent():
    sp = Cv()
    sp.paint(sp.ellipse(64, 125, 62, 4) & (sp.y < 127.5), 0.3 + 0.2 * sp.noise(3, 2081), ASH)
    for gx, gy in ((2, 124), (126, 124)):
        sp.paint(sp.stroke([(64, 22), (gx, gy)], 1.8), 0.25, IRON)
        sp.paint(sp.stroke([(gx, gy - 7), (gx, gy + 2)], 3.5), 0.4, BARK)
    sp.paint(sp.stroke([(64, 4), (64, 22)], 3.2), 0.45, BARK)
    tent = sp.poly([(10, 127), (64, 14), (118, 127)])
    fold = np.sin((sp.x - 64) * 0.26 + 0.4 * np.sin(sp.y * 0.1)) * 0.5 + 0.5
    sp.paint(tent, sp.hshade(10, 118, 0.5, 0.55) * 0.8 + 0.15 * fold + (sp.noise(4, 2082) - 0.5) * 0.1, CANVAS, dither=0.8)
    for k in (-3, -2, -1, 1, 2, 3):
        sp.paint(sp.stroke([(64, 20), (64 + k * 17, 127)], 1.3) & tent, 0.12, CANVAS)
    sp.paint(tent & (np.abs((sp.x - 80) + (sp.y - 90) * 0.1) < 7) & (np.abs(sp.y - 92) < 7), 0.78, CANVAS)
    sp.solid(sp.rect(73, 85, 87, 86) | sp.rect(73, 98, 87, 99), "#2a2c2c")
    door = sp.poly([(50, 127), (64, 56), (78, 127)])
    gl = np.clip(1 - np.abs(sp.x - 64) / 16.0, 0, 1) * np.clip((sp.y - 56) / 70.0, 0, 1)
    sp.paint(door, 0.05 + 0.65 * gl, ramp("#0a0404", "#2a0a08", "#5a1208", "#8a2010", "#b83414"))
    sp.paint(sp.poly([(50, 127), (64, 56), (60, 56), (44, 127)]) | sp.poly([(78, 127), (64, 56), (68, 56), (84, 127)]), 0.45, CANVAS)
    sp.paint(sp.stroke([(52, 100), (46, 106)], 2) | sp.stroke([(76, 100), (82, 106)], 2), 0.2, ROPE)
    return sp.rgba()


def th_brazier_red():
    sp = Cv()
    sp.paint(sp.ellipse(64, 126, 38, 3) & (sp.y < 127.5), 0.25, ASH)
    for (ax, bx) in ((44, 30), (84, 98), (64, 64)):
        sp.paint(sp.stroke([(ax, 82), (bx, 125)], 6, 5), sp.hshade(min(ax, bx) - 4, max(ax, bx) + 4, 0.35, 0.4), IRON)
    sp.paint(sp.stroke([(36, 108), (92, 108)], 3), 0.3, IRON)
    bowl = sp.ellipse(64, 76, 34, 18) & (sp.y > 70)
    sp.paint(bowl, sp.hshade(30, 98, 0.45, 0.5), IRON)
    rs = ramp("#2a0e06", "#4e1c0a", "#7a3010", "#a44a1a")
    sp.paint(bowl & (sp.noise(4, 2091) > 0.62), 0.5, rs)
    sp.paint(sp.rect(26, 66, 102, 72), sp.hshade(26, 102, 0.55, 0.4), IRON)
    coals = sp.ellipse(64, 64, 31, 7)
    sp.paint(coals, 0.18 + 0.5 * sp.noise(3, 2092) + 0.12 * (sp.noise(1.7, 2093, 2) > 0.7), FIRERED)
    sp.paint(coals & (sp.noise(2.5, 2094, 2) > 0.7), 0.1, ASH)
    _fire(sp, 64, 64, 30, 18, 2095, FIRERED, n=4, gain=0.78)
    path = [(64 + 5 * math.sin(i * 0.5), 52 - i * 4.2) for i in range(12)]
    _plume(sp, path, 8, 20, SMOKE, 2096, 0.45)
    return sp.rgba()


def th_banner_rider():
    sp = Cv()
    sp.paint(sp.ellipse(64, 126, 22, 3) & (sp.y < 127.5), 0.25, ASH)
    pole = sp.rect(61, 8, 67, 127)
    sp.paint(pole, sp.hshade(61, 67, 0.3, 0.5), BLACKST)
    sp.paint(sp.poly([(60, 10), (68, 10), (64, 0)]), 0.4, BLACKST)
    rng = RNG(2101)
    top = [(67, 16 + 4 * math.sin(i)) for i in range(1)]
    xs = np.linspace(67, 118, 10)
    topy = [14 + 5 * math.sin(x * 0.18) for x in xs]
    bot = [66 + 4 * math.sin(x * 0.2 + 1) + rng.uniform(-3, 3) + (x - 67) * 0.14 for x in xs]
    pts = [(x, y) for x, y in zip(xs, topy)]
    pts += [(120, 36), (112, 44), (122, 56)]
    pts += [(x, y) for x, y in reversed(list(zip(xs, bot)))][:]
    for i in range(1, len(pts) - 1):
        if 12 < i < len(pts) - 1:
            pts[i] = (pts[i][0] + rng.uniform(-1.5, 1.5), pts[i][1] + rng.uniform(-3.5, 3.5))
    cloth = sp.poly(pts)
    fold = np.sin((sp.x - 67) * 0.35 + 0.5 * np.sin(sp.y * 0.12)) * 0.5 + 0.5
    sp.paint(cloth, 0.4 + 0.3 * fold + (sp.noise(4, 2102) - 0.5) * 0.15 - 0.1 * ((sp.x - 67) / 55.0), CLOTH, dither=0.8)
    for (hx, hy, r) in ((100, 28, 3.5), (84, 56, 3), (108, 50, 2.5)):
        hole = sp.ellipse(hx, hy, r, r * 0.8) & cloth
        sp.a[hole] = 0
        sp.fx[hole] = False
    for fx_ in (76, 88, 99):
        yy = float(np.interp(fx_, xs, bot))
        sp.paint(sp.stroke([(fx_, yy - 1), (fx_ + rng.uniform(-3, 3), yy + rng.uniform(6, 14))], 1.4, 0.8), 0.45, CLOTH)
    sp.solid(sp.rect(86, 36, 91, 41), "#5a0c08")
    sp.solid(sp.rect(87, 37, 90, 40), "#ff3a1a")
    sp.solid(sp.rect(88, 38, 89, 39), "#ffc890")
    return sp.rgba()


def th_vent_glow():
    sp = Cv()
    cx = 64
    ccol = cx + 6 * np.sin(sp.y * 0.07)
    # the column of dull red glow and ash rising from the crack
    t = np.clip((98 - sp.y) / 96.0, 0, 1)
    hw = 8 + 6 * np.sin(np.clip(t, 0, 1) * math.pi * 0.9) + 8 * t
    inten = np.clip(1 - np.abs(sp.x - ccol) / hw, 0, 1) ** 1.2 * (1 - t) ** 0.9 * 1.25
    col = (inten > sp.bt) & (sp.y < 98)
    sp.paint(col, 0.15 + 0.7 * inten, REDGLOW, fx=True, dither=0.6)
    rng = RNG(2111)
    for k in range(18):
        ax = ccol[0, 0] + rng.uniform(-18, 18)
        ay = rng.uniform(4, 80)
        if abs(ax - (cx + 6 * math.sin(ay * 0.07))) < hw[int(ay), 0] * 1.2:
            sp.solid(sp.rect(ax, ay, ax + (2 if rng.rand() < 0.3 else 1), ay + 1), "#9a9088" if rng.rand() < 0.6 else "#5a524e", fx=True)
    rock = sp.poly([(0, 127), (4, 108), (16, 98), (30, 100), (44, 92), (56, 96), (72, 96), (84, 90), (98, 98), (112, 102), (124, 110), (127, 127)])
    rk = ramp("#020203", "#08080c", "#14101a", "#3a1a12", "#7a3010", "#c86a1c", "#ff9a3c")
    d = np.sqrt(((sp.x - cx) / 40.0) ** 2 + ((sp.y - 96) / 22.0) ** 2)
    lit = np.clip(1 - d, 0, 1)
    sp.paint(rock, 0.16 + 0.22 * sp.noise(5, 2112) + 0.5 * lit ** 1.3, rk)
    crack = sp.stroke([(44, 124), (52, 112), (60, 104), (64, 96), (70, 102), (80, 110), (88, 122)], 2.4, 2.4) & rock
    crack |= sp.ellipse(64, 96, 12, 3.5) & rock
    sp.paint(crack, 0.75 + 0.2 * sp.noise(3, 2113), HEAT)
    sp.paint(sp.stroke([(20, 124), (30, 112), (38, 108)], 1.4) & rock, 0.55, REDGLOW)
    sp.paint(sp.stroke([(100, 124), (96, 114), (90, 108)], 1.4) & rock, 0.55, REDGLOW)
    return sp.rgba()


def th_glass_mountain():
    sp = Cv()
    hw = 7 + 57 * np.clip((sp.y - 26) / 101.0, 0, 1) ** 1.35
    cone = (np.abs(sp.x - 64) < hw) & (sp.y >= 26) & (sp.y <= 127.5)
    sp.paint(cone, 0.18 + 0.1 * sp.noise(6, 2121) + 0.12 * np.clip((64 - sp.x) / 60.0, -1, 1), BLACKST)
    flank = cone & (sp.x < 64 - 4) & (sp.x > 64 - hw * 0.75) & (np.abs((sp.x - 64) + (sp.y - 26) * 0.55) > 0)
    streak = flank & (np.abs(((sp.x - 64) + (sp.y - 60) * 0.35) + 20) < 6)
    sp.paint(streak & (sp.noise(2.6, 2122, 2) > 0.3), 0.55 + 0.35 * sp.noise(3, 2123), SHEEN)
    sp.paint(cone & (sp.x > 64 + hw * 0.55), 0.1, BLACKST)
    glowtop = cone & (sp.y < 52)
    sp.paint(glowtop & (sp.bt < 0.45 * (52 - sp.y) / 26.0), 0.35 + 0.3 * (52 - sp.y) / 26.0, REDGLOW)
    # the single red vent, and its thin plume
    sp.glow(64, 22, 16, 11, REDHALO, power=1.3, gain=1.2, dither=0.5)
    sp.paint(sp.ellipse(64, 25, 8, 4), 0.4, REDGLOW)
    sp.paint(sp.ellipse(64, 24.5, 5, 2.6), 0.85, HEAT)
    path = bez((64, 20), (72, 11), (62, 0), 14)
    _plume(sp, path, 3.2, 6.5, REDGLOW, 2124, 0.35, dens=1.1)
    return sp.rgba()


def th_stalagmite_red():
    sp = Cv()
    sp.glow(80, 122, 52, 10, REDHALO, power=1.4, gain=1.0, dither=0.5)
    rng = RNG(2131)
    specs = [(64, 126, 22, 104), (36, 126, 17, 66), (92, 126, 18, 78), (14, 126, 11, 40), (112, 126, 12, 50), (52, 126, 11, 40)]
    for (cx, base, w, h) in sorted(specs, key=lambda s: -s[3]):
        pts = [(cx - w, base + 1), (cx - w * 0.55, base - h * 0.5), (cx - w * 0.2, base - h * 0.85), (cx + rng.uniform(-1.5, 1.5), base - h),
               (cx + w * 0.25, base - h * 0.8), (cx + w * 0.6, base - h * 0.45), (cx + w, base + 1)]
        m = sp.poly(pts)
        sp.paint(m, 0.35 + 0.1 * np.clip((cx - sp.x) / w, -1, 1) + (sp.noise(4, 2132 + cx) - 0.5) * 0.15, BLACKST)
        rim = m & ~np.roll(m, 3, axis=1) & (sp.x > cx - 2)
        rim |= m & ~np.roll(m, 2, axis=1) & (sp.x > cx + w * 0.3)
        sp.paint(rim, 0.45 + 0.5 * np.clip((sp.y - (base - h)) / h, 0, 1), REDGLOW)
        sp.paint(sp.stroke([(cx + w * 0.1, base - h * 0.55), (cx + w * 0.3, base - h * 0.25)], 1.2) & m & (sp.bt < 0.6), 0.9, REDGLOW)
    return sp.rgba()


def th_chain_post():
    sp = Cv()
    sp.paint(sp.ellipse(64, 125, 36, 4) & (sp.y < 127.5), 0.3 + 0.2 * sp.noise(3, 2141), ASH)
    post = sp.rect(57, 26, 71, 127)
    sp.paint(post, sp.hshade(57, 71, 0.45, 0.5) + 0.1 * np.sin(sp.y * 0.4), IRON)
    sp.paint(post & (sp.noise(3, 2142) > 0.68), 0.5, ramp("#2a0e06", "#4e1c0a", "#7a3010"))
    sp.paint(sp.ellipse(64, 24, 9, 8), sp.hshade(55, 73, 0.6, 0.5), IRON)
    sp.paint(sp.rect(54, 118, 74, 127), 0.5, IRON)
    sp.paint(sp.ring(64, 44, 8, 8, 3), 0.65, IRON)
    path = bez3((72, 46), (126, 56), (116, 124), (68, 118), 20)
    for i, (x, y) in enumerate(path):
        if i % 2 == 0:
            sp.paint(sp.ring(x, y, 6.4, 5.2, 2.8), 0.55 + 0.15 * (i % 4 == 0), IRON)
        else:
            sp.paint(sp.ellipse(x, y, 5.2, 2.6), 0.38, IRON)
    path2 = bez((58, 48), (36, 66), (42, 94), 10)
    for i, (x, y) in enumerate(path2):
        if i % 2 == 0:
            sp.paint(sp.ring(x, y, 5.6, 4.6, 2.5), 0.5, IRON)
        else:
            sp.paint(sp.ellipse(x, y, 4.6, 2.4), 0.35, IRON)
    sp.paint(sp.ring(42, 100, 7, 7, 3), 0.6, IRON)
    return sp.rgba()


def th_pool_stones():
    sp = Cv()
    pool = sp.ellipse(64, 90, 56, 21)
    sp.paint(pool, 0.1 + 0.22 * sp.noise(6, 2151), NIGHTW)
    g = sp.stroke(bez((40, 86), (56, 80), (76, 84)), 1.6) & pool
    sp.paint(g & (sp.bt < 0.85), 0.95, WHITEW)
    sp.paint(sp.stroke(bez((82, 92), (90, 90), (98, 92)), 1.2) & pool & (sp.bt < 0.6), 0.9, WHITEW)
    rng = RNG(2152)
    stones = []
    for a in np.linspace(0, TWO_PI, 15, endpoint=False):
        a += rng.uniform(-0.12, 0.12)
        px, py = 64 + 59 * math.cos(a), 90 + 24 * math.sin(a)
        front = math.sin(a)
        stones.append((py, px, 9 + 4 * (front + 1) / 2 + rng.uniform(-1, 1.5), 5 + 3.5 * (front + 1) / 2))
    for (py, px, rx, ry) in sorted(stones):
        m = (np.abs((sp.x - px) / rx) ** 2.6 + np.abs((sp.y - py) / ry) ** 2.6) < 1.0
        m &= sp.y < 127.5
        sp.paint(m, sp.bump(m, rx * 0.35, 0.42, 0.55) + (sp.noise(3, 2153 + int(px)) - 0.5) * 0.2, BLACKST)
        sp.paint(m & (sp.y < py - ry * 0.35) & (sp.bt < 0.8), 0.7, BLACKST)
        sp.solid(m & (sp.y < py - ry * 0.55) & (sp.x < px - rx * 0.2) & (sp.bt < 0.35), "#7a8aa8")
    return sp.rgba()


def th_camp_fire():
    sp = Cv()
    rng = RNG(2161)
    sp.paint(sp.ellipse(64, 116, 50, 11) & (sp.y < 127.5), 0.12 + 0.15 * sp.noise(3, 2162), ASH)
    st = []
    for a in np.linspace(0, TWO_PI, 12, endpoint=False):
        a += rng.uniform(-0.1, 0.1)
        st.append((116 + 12 * math.sin(a), 64 + 46 * math.cos(a), 9 + rng.uniform(-1, 1.5), 6 + 2 * (math.sin(a) + 1) / 2))
    back = [s for s in st if s[0] < 116]
    front = [s for s in st if s[0] >= 116]

    def put(lst):
        for (py, px, rx, ry) in sorted(lst):
            m = ((np.abs((sp.x - px) / rx) ** 2.4 + np.abs((sp.y - py) / ry) ** 2.4) < 1.0) & (sp.y < 127.5)
            sp.paint(m, sp.bump(m, rx * 0.4, 0.5, 0.6) + (sp.noise(3, 2163 + int(px)) - 0.5) * 0.2, ASH)
            sp.solid(m & (sp.y > py) & (sp.bt < 0.3), "#7a1a08")
    put(back)
    sp.paint(sp.ellipse(64, 108, 34, 7), 0.25 + 0.3 * sp.noise(3, 2164), FIRERED)
    logs = [sp.stroke([(30, 112), (98, 104)], 10, 9), sp.stroke([(34, 100), (96, 114)], 9, 10), sp.stroke([(64, 98), (64, 112)], 8, 8)]
    for k, l in enumerate(logs):
        sp.paint(l, 0.3 + 0.3 * sp.noise(3, 2165 + k) + 0.15 * (sp.y < 108), BARK)
        sp.paint(l & (sp.noise(2, 2168 + k, 2) > 0.74), 0.5, FIRERED)
    sp.paint(sp.ellipse(32, 112, 4, 4.5) | sp.ellipse(97, 106, 4, 4.5) | sp.ellipse(34, 100, 3.5, 4) | sp.ellipse(95, 114, 4, 4), 0.55, FIRERED)
    _fire(sp, 64, 104, 56, 54, 2169, FIRERED, n=5)
    put(front)
    path = [(70 + 6 * math.sin(i * 0.45), 48 - i * 4.2) for i in range(12)]
    _plume(sp, path, 8, 20, SMOKE, 2170, 0.4, dens=0.9)
    return sp.rgba()


def pc_gate_mouths():
    sp = Cv()
    BR = ramp("#100a06", "#2a1a0c", "#4e3416", "#74501f", "#9c7430", "#c8a048")
    for k, cx in enumerate((35, 93)):
        panel = sp.rect(cx - 27, 40, cx + 27, 127) | sp.ellipse(cx, 40, 27, 26)
        n = sp.noise(5, 2201 + k, 3)
        sp.paint(panel, sp.hshade(cx - 27, cx + 27, 0.42, 0.35) + (n - 0.5) * 0.2, BR)
        sp.paint(panel & (n > 0.64) & (sp.y > 46) & (sp.noise(3, 2205 + k, 2) > 0.5), 0.2 + 0.4 * n, PATINA)
        sp.paint(sp.ring(cx, 40, 27, 26, 3) & panel & (sp.y < 70) | (panel & ((np.abs(sp.x - cx) > 24) & (sp.y >= 40))), 0.3, BR)
        for sx in (cx - 19, cx - 7, cx + 5, cx + 17):
            sp.paint(sp.ellipse(sx + 1, 27 + (6 if abs(sx - cx) > 12 else 0) + 6, 2.2, 2.2), 0.85, BR)
        # the laughing mouth, pushed out of the bronze like a relief
        cy = 82.0
        dx = sp.x - cx
        top = cy - 16 + 13 * np.clip(1 - (dx / 23.0) ** 2, 0, 1)
        bot = cy - 16 + 44 * np.clip(1 - (dx / 23.0) ** 2, 0, 1) ** 0.85
        mouth = (np.abs(dx) < 23) & (sp.y > top) & (sp.y < bot)
        lip = (sp.blur(mouth, 3.2) > 0.14) & ~mouth & panel
        sp.paint(lip, sp.bump(lip | mouth, 3, 0.62, 0.6) + 0.1, BR)
        sp.paint(sp.blur(mouth, 6.5) > 0.12, 0.0, BR) if False else None
        sp.paint(mouth, 0.04 + 0.06 * np.clip((sp.y - top) / 40.0, 0, 1), ramp("#020101", "#0a0304", "#1a0608"))
        sp.paint(sp.ellipse(cx, cy + 22, 12, 7) & mouth, 0.3 + 0.3 * np.clip((sp.y - (cy + 16)) / 8.0, 0, 1), ramp("#1a0606", "#3a0c0c", "#6a1414"))
        rng = RNG(2210 + k)
        for tx in range(-20, 21, 5):
            x = cx + tx + rng.uniform(-1, 1)
            ty = cy - 16 + 13 * (1 - (tx / 23.0) ** 2)
            L = rng.uniform(7, 14) * (0.55 + 0.45 * (1 - abs(tx) / 23.0))
            sp.paint(sp.poly([(x - 3, ty - 1), (x + 3, ty - 1), (x + rng.uniform(-1.5, 1.5), ty + L)]) & mouth, 0.7 + 0.25 * rng.rand(), ramp("#6a5a38", "#a8946a", "#d8c898", "#f0e4c0"))
        for tx in range(-18, 19, 6):
            x = cx + tx + rng.uniform(-1, 1)
            by = cy - 16 + 44 * max(1 - (tx / 23.0) ** 2, 0) ** 0.85
            L = rng.uniform(6, 11) * (0.5 + 0.5 * (1 - abs(tx) / 23.0))
            sp.paint(sp.poly([(x - 3, by + 1), (x + 3, by + 1), (x + rng.uniform(-1.5, 1.5), by - L)]) & mouth, 0.65 + 0.25 * rng.rand(), ramp("#6a5a38", "#a8946a", "#d8c898", "#f0e4c0"))
        # cheeks bulging and laugh lines running away from the corners
        for sgn in (-1, 1):
            c = (cx + sgn * 25, cy - 14)
            sp.paint(sp.stroke(bez((c[0], c[1] + 2), (c[0] + sgn * 2, c[1] - 12), (c[0] - sgn * 6, c[1] - 24)), 3.0, 1.6) & panel, 0.2, BR)
            sp.paint(sp.stroke(bez((c[0] - sgn * 3, c[1] + 4), (c[0] + sgn * 3, c[1] - 8), (c[0] - sgn * 5, c[1] - 18)), 1.6) & panel, 0.78, BR)
    sp.paint(sp.rect(63, 44, 65, 127), 0.08, BR)
    return sp.rgba(outline=True)


def pc_light_shaft():
    sp = Cv()
    dx = np.abs(sp.x - 64)
    hw = 11 + 9 * (sp.y / 127.0)
    a = np.clip(1 - dx / hw, 0, 1) ** 1.5 * (0.35 + 0.65 * np.clip(sp.y / 36.0, 0, 1) ** 0.8)
    core = np.clip(1 - dx / (hw * 0.38), 0, 1) ** 1.3
    a = np.clip(a * 0.85 + core * 0.35, 0, 1) * np.clip(sp.y / 8.0, 0, 1)
    aq = np.clip(np.floor(a * 7 + sp.bt * 0.85) / 7, 0, 0.95)
    col = np.zeros((128, 128, 3), np.float32)
    mixv = np.clip(core * 1.3, 0, 1)[..., None]
    col[:] = np.array([196, 222, 255], np.float32) * (1 - mixv) + np.array([255, 255, 255], np.float32) * mixv
    sp.over(aq, col)
    rng = RNG(2221)
    for k in range(30):
        px, py = 64 + rng.uniform(-14, 14), rng.uniform(14, 124)
        if abs(px - 64) < hw[int(py), 0] * 0.8:
            sp.over(sp.rect(px, py, px + 1, py + 1) * 0.95, "#ffffff")
    return sp.rgba(outline=False, hard=False)


def pc_white_swell():
    sp = Cv(256, 128)
    d = np.sqrt(((sp.x - 128) / 126.0) ** 2 + ((sp.y - 64) / 62.0) ** 2)
    ang = np.arctan2((sp.y - 64) / 62.0, (sp.x - 128) / 126.0)
    a = np.clip(1 - d, 0, 1) ** 1.5 * (1 + 0.12 * np.sin(ang * 14))
    a = np.clip(a * 1.25 + 0.5 * (d < 0.2), 0, 1)
    aq = np.clip(np.floor(a * 8 + sp.bt * 0.9) / 8, 0, 1)
    tint = np.clip(d * 1.1, 0, 1)[..., None]
    col = np.array([255, 255, 255], np.float32) * (1 - tint * 0.12) + np.array([214, 232, 255], np.float32) * tint * 0.12
    sp.over(aq, col)
    return sp.rgba(outline=False, hard=False)


def pc_long_shadow():
    """The Keeper's long shadow. A shadow on a dark floor cannot be seen, so the floor under it is lit: a warm pool of the altar's light, with the shadow cut out of it as a
    near-black wedge, and a bright rim along the shadow's edge (visual polish 2: it used to be translucent black on a near-black floor)."""
    sp = Cv(256, 128)
    cy = 90
    parts = [sp.ellipse(30, cy, 14, 10), sp.stroke([(40, cy), (58, cy)], 8, 14), sp.ellipse(66, cy, 16, 21), sp.poly([(66, cy - 20), (150, cy - 8), (156, cy + 8), (66, cy + 20)]),
             sp.stroke([(62, cy - 17), (110, cy - 13), (146, cy - 7)], 5, 3), sp.stroke([(62, cy + 17), (110, cy + 13), (146, cy + 7)], 5, 3),
             sp.stroke([(150, cy - 4), (250, cy - 12)], 9, 5), sp.stroke([(150, cy + 4), (250, cy + 12)], 9, 5)]
    mask = np.zeros((128, 256), bool)
    for p in parts:
        mask |= p
    # the pool of light on the floor: an ellipse round the shadow, strongest at the altar's end (the right), fading to the edges
    d = np.sqrt(((sp.x - 140) / 124.0) ** 2 + ((sp.y - 88) / 38.0) ** 2)
    pool = np.clip(1.0 - d, 0.0, 1.0) ** 0.7 * (0.5 + 0.5 * np.clip(sp.x / 256.0 + 0.2, 0, 1))
    sp.over(np.clip(pool * 0.9, 0, 0.82), "#ff9a58")
    sp.over(np.clip(pool * 0.45, 0, 0.5), "#ffe6c0")  # a hot core
    soft = sp.blur(mask, 1.2)
    # the rim: a bright line just outside the shadow's edge
    ring = np.clip(sp.blur(mask, 4.0) * 1.9 - soft * 1.9, 0.0, 1.0) * np.clip(pool * 2.2, 0, 1)
    sp.over(np.clip(ring * 1.2, 0, 1), "#fff0d0")
    a = np.clip(soft * 1.5, 0, 1) * 0.96
    sp.over(a, "#0a0305")
    return sp.rgba(outline=False, hard=False)


# ---- registry and build ------------------------------------------------------------------------------------------------------------------------------

def _registry() -> dict:
    g = globals()
    return {("thing_" + k[3:] if k.startswith("th_") else "piece_" + k[3:]): v for k, v in g.items() if k.startswith(("th_", "pc_")) and callable(v)}


def build(art: str) -> dict:
    """Draw every billboard of `art` into assets/story/<art>/textures/ and return {id: {file, size, metres}} with sorted keys."""
    if art not in ember_spec.ARTS:
        raise ValueError(f"unknown art {art!r}")
    reg = _registry()
    out_dir = os.path.join(ROOT, "assets", "story", art, "textures")
    os.makedirs(out_dir, exist_ok=True)
    section = {}
    for tid, (kind, px, metres, _brief) in sorted(ember_spec.THINGS[art].items()):
        fn = reg.get(tid)
        if fn is None:
            print(f"  MISSING drawing for {art}/{tid}")
            continue
        arr = fn()
        if arr.shape != (128, px, 4):
            raise ValueError(f"{art}/{tid}: drew {arr.shape[1]} x {arr.shape[0]}, spec says {px} x 128")
        if kind == "thing":
            arr = arr.copy()
            arr[..., 3] = np.where(arr[..., 3] >= 128, 255, 0)
        im = Image.fromarray(arr, "RGBA")
        im.save(os.path.join(out_dir, tid + ".png"), optimize=False, compress_level=9)
        section[tid] = {"file": f"textures/{tid}.png", "size": [im.width, im.height], "metres": metres}
    return dict(sorted(section.items()))


def main() -> int:
    total = 0
    for art in ember_spec.ARTS:
        sec = build(art)
        total += len(sec)
        print(f"{art}: {len(sec)} billboard textures")
    print(f"total {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
