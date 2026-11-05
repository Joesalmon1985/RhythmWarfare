"""The Mission Count, airfield world, second half: the bomber's nose, the Surgeon's office, the Quartermaster's store, the hospital tent and the field's odd props.

Billboards (`thing_*`), drawn with the Sprite class of the Underworld (masks shaded by a palette ramp with ordered dither, hard alpha) in khaki #b4a474, olive #6e7048,
dust orange #b8803a, warm bulb #ffd890 and instrument green #60ff90. Light from the upper left; every silhouette gets a darker edge of its own colour.
`DRAW = {id: fn}`; each fn() returns a uint8 RGBA array (128, 128, 4), or (128, 256, 4) for the truck. Deterministic: seeded generators only.
"""
from __future__ import annotations

import numpy as np

from .pixeltex import BAYER8, noise, quantise, ramp
from .tex_underworld import Sprite

# ---- palettes (dark to light) -----------------------------------------------------------------------------------------------------------------
KHAKI = ramp("#2a2618", "#524a30", "#7a6e44", "#9c8e5c", "#b4a474", "#d0c490", "#e8dcae")
OLIVE = ramp("#10120a", "#22261a", "#363a24", "#4c5030", "#6e7048", "#8a8c5c")
DUST = ramp("#2e1a0a", "#5a3414", "#8a5a22", "#b8803a", "#d8a458", "#f0c880")
IRON = ramp("#07090a", "#12181a", "#1e2826", "#2e3c36", "#445248", "#64726a")
STEEL = ramp("#14161a", "#2a2e34", "#444a52", "#68707a", "#929aa0", "#c0c6c8")
WOOD = ramp("#1a1008", "#32200e", "#523416", "#744c22", "#9a6a34", "#bc8a4c")
BRASS = ramp("#2a1c06", "#5e4210", "#9a7420", "#c89c34", "#e8c860", "#fff0a0")
PAPER = ramp("#5a5238", "#8a8058", "#b4aa80", "#d4cca0", "#ece4c0", "#fff8dc")
CANVAS = ramp("#2a2c2a", "#4a4c46", "#6c6e64", "#8e9084", "#aeb09e", "#cccdb8")
TARP = ramp("#1c2014", "#2e3320", "#434a2c", "#5c6438", "#7a8048", "#9a9c64")
GREENLIT = ramp("#021008", "#0a2c14", "#14582a", "#28a050", "#60ff90", "#c8ffd8")
BULB = ramp("#7a4a14", "#c88830", "#ffc060", "#ffd890", "#fff4d0")
REDP = ramp("#2a0808", "#5a1210", "#8a2418", "#b83a24", "#d85a38")
SKYW = ramp("#9a9a8c", "#c0c0b0", "#dcdccc", "#f2f2e6", "#ffffff")
NIGHT = ramp("#010206", "#040812", "#09132a", "#122340", "#1e3658")
FIRE = ramp("#5a1806", "#b84a10", "#f08a20", "#ffcc50", "#fff4c0")
SKIN = ramp("#5a3a28", "#8a5c40", "#b88a68", "#d8aa84")
GLASS = ramp("#0a1614", "#1a2e2a", "#2c4a44", "#4a7068", "#86a89c")


# ---- helpers ------------------------------------------------------------------------------------------------------------------------------------

class Wide(Sprite):
    """A 256 x 128 canvas (the truck)."""

    def __init__(self):
        self.n = 128
        self.w, self.h = 256, 128
        self.rgb = np.zeros((128, 256, 3), np.uint8)
        self.a = np.zeros((128, 256), np.uint8)
        self.x, self.y = np.mgrid[0:128, 0:256][::-1].astype(np.float32)

    def paint(self, mask, shade, pal):
        sh = shade if isinstance(shade, np.ndarray) else np.full(self.a.shape, float(shade), np.float32)
        col = quantise(np.clip(sh, 0, 1), pal)
        self.rgb[mask] = col[mask]
        self.a[mask] = 255

    def tri(self, pts):
        return poly(self, pts)


def poly(sp, pts):
    """Any polygon (even-odd rule) as a mask."""
    m = np.zeros(sp.a.shape, bool)
    k = len(pts)
    px, py = sp.x + 0.5, sp.y + 0.5
    for i in range(k):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % k]
        if ay == by:
            continue
        cond = ((ay <= py) & (by > py)) | ((by <= py) & (ay > py))
        xi = ax + (py - ay) / (by - ay) * (bx - ax)
        m ^= cond & (px < xi)
    return m


def nz(sp, seed, scale=4.0, octaves=2):
    """Noise 0..1 over the sprite (cropped from a square tile)."""
    w = sp.a.shape[1]
    return noise(w, scale, seed, octaves)[: sp.a.shape[0], :]


def bev(sp, x0, y0, x1, y1, base=0.5, k=0.16, seed=1, gr=0.12, edge=2):
    """A box's shade: highlight top and left, shadow bottom and right, a little grain."""
    sh = np.full(sp.a.shape, base, np.float32)
    sh += k * ((sp.y - y0) < edge) + k * ((sp.x - x0) < edge) - k * ((y1 - 1 - sp.y) < edge) - k * ((x1 - 1 - sp.x) < edge)
    sh += (nz(sp, seed, 3.0) - 0.5) * gr * 2
    return sh


def cyl(sp, x0, x1, base=0.5, amp=0.4, seed=0, gr=0.08):
    """A vertical cylinder: bright left of centre, dark right."""
    u = np.clip((sp.x - x0) / max(x1 - x0, 1), 0, 1)
    sh = base + amp * (0.45 - u) + 0.08 * np.sin(u * np.pi)
    if seed:
        sh = sh + (nz(sp, seed, 3.0) - 0.5) * gr * 2
    return sh


def sphere(sp, cx, cy, r, base=0.55, amp=0.45):
    d = np.sqrt((sp.x - cx) ** 2 + (sp.y - cy) ** 2) / r
    lx = (sp.x - cx + (sp.y - cy)) / (r * 1.6)
    return base - amp * lx * 0.5 - 0.15 * np.clip(d - 0.6, 0, 1)


def outline(sp, amt=0.5):
    """Darken the pixels on the silhouette's edge (the local colour, darker). Canvas borders do not count as edges."""
    a = sp.a > 0
    p = np.pad(a, 1, constant_values=True)
    edge = a & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    sp.rgb[edge] = (sp.rgb[edge].astype(np.float32) * amt).astype(np.uint8)


def glow(sp, cx, cy, r, pal, power=1.6, tint=0.0, lo=0):
    """A hard-alpha dithered halo around a lamp: sparse light pixels that thin out with distance."""
    d = np.sqrt((sp.x - cx) ** 2 + (sp.y - cy) ** 2) / r
    f = np.clip(1 - d, 0, 1) ** power
    ny, nx = sp.a.shape
    b = BAYER8[np.arange(ny)[:, None] % 8, np.arange(nx)[None, :] % 8] + 0.5
    on = f * 0.9 > b * 0.9
    k = len(pal) - 1
    idx = np.clip((f * (k + 0.4)).astype(int), lo, k)
    col = (pal[idx] * 255).astype(np.uint8)
    empty = on & (sp.a == 0)
    sp.rgb[empty] = col[empty]
    sp.a[empty] = 255
    if tint > 0:  # lighten the solid pixels near the lamp too
        solid = on & (sp.a > 0) & ~empty & (b < tint)
        sp.rgb[solid] = (sp.rgb[solid] * 0.5 + col[solid] * 0.5).astype(np.uint8)


def rope(sp, pts, w, pal, shade=0.5):
    m = np.zeros(sp.a.shape, bool)
    for (a, b) in zip(pts[:-1], pts[1:]):
        m |= sp.line(a[0], a[1], b[0], b[1], w)
    sp.paint(m, shade, pal)
    return m


def rivets(sp, pts, r=1.3, colour=0.85, pal=None):
    pal = IRON if pal is None else pal
    for (x, y) in pts:
        sp.paint(sp.ellipse(x, y, r, r), colour, pal)


# ---- the boarding ladder ------------------------------------------------------------------------------------------------------------------------

def thing_ladder():
    """A short wooden boarding ladder leaning against a dark hatch in a riveted green-black bulkhead."""
    sp = Sprite()
    # bulkhead plate with the hatch cut out of it
    plate = sp.rect(6, 6, 122, 126)
    sp.paint(plate, bev(sp, 6, 6, 122, 126, 0.42, 0.14, 11, 0.12), IRON)
    for yy in (40, 92):
        sp.paint(sp.rect(6, yy, 122, yy + 1), 0.15, IRON)
    pts = [(x, y) for x in (12, 116) for y in (12, 46, 98, 120)]
    rivets(sp, pts, 1.4, 0.75)
    # hatch: round-topped opening with a heavy rim
    hatch_o = sp.rect(26, 28, 100, 126) | sp.ellipse(63, 36, 37, 22)
    hatch_i = sp.rect(34, 32, 92, 126) | sp.ellipse(63, 38, 29, 16)
    sp.paint(hatch_o, bev(sp, 26, 28, 100, 126, 0.55, 0.14, 12, 0.1), IRON)
    dark = np.clip(0.02 + 0.12 * nz(sp, 13, 5.0) + 0.1 * np.clip((sp.y - 90) / 40, 0, 1), 0, 1)
    sp.paint(hatch_i, dark, GREENLIT)
    # a faint lit crew ledge inside
    sp.paint(sp.rect(40, 96, 88, 99) & hatch_i, 0.28, GREENLIT)
    sp.paint(sp.ellipse(76, 64, 3, 3), 0.8, GREENLIT)
    # dogs (clamps) down the right of the rim and hinges on the left
    for yy in (44, 70, 96):
        sp.paint(sp.rect(91, yy, 100, yy + 6), 0.7, IRON)
        sp.paint(sp.rect(27, yy, 34, yy + 7), 0.65, IRON)
    # the ladder: two wooden rails converging towards the top, ten rungs
    lx0, lx1, ly0 = (22, 54), (36, 66), 125
    top = 30
    for side in (0, 1):
        a = (lx0[side], ly0)
        b = (lx1[side], top)
        sp.paint(sp.line(a[0], a[1], b[0], b[1], 6), 0.55 - 0.12 * side + 0.1 * nz(sp, 20 + side, 3.0), WOOD)
        sp.paint(sp.line(a[0] - 1.5, a[1], b[0] - 1.5, b[1], 1.5), 0.85 - 0.1 * side, WOOD)
    for k in range(11):
        t = (k + 0.5) / 11
        y = ly0 - t * (ly0 - top)
        xa = lx0[0] + t * (lx1[0] - lx0[0])
        xb = lx0[1] + t * (lx1[1] - lx0[1])
        sp.paint(sp.rect(xa, y - 2, xb, y + 2), 0.5 + 0.3 * (sp.y < y - 0.5) + 0.1 * nz(sp, 30 + k, 2.0), WOOD)
    # lashing at the top rail ends
    sp.paint(sp.rect(33, top - 2, 39, top + 4), 0.6, DUST)
    sp.paint(sp.rect(63, top - 2, 69, top + 4), 0.45, DUST)
    outline(sp)
    glow(sp, 76, 64, 26, GREENLIT, 2.2, lo=2)
    return sp.rgba()


# ---- the hanging bulb ---------------------------------------------------------------------------------------------------------------------------

def thing_lamp_hang():
    """A bare bulb on a flex under a tin shade, a warm glow round it (hangs from the top edge)."""
    sp = Sprite()
    sp.paint(sp.rect(63, 0, 66, 58), 0.3, IRON)  # the flex
    sp.paint(sp.rect(62, 0, 67, 5), 0.5, KHAKI)  # ceiling rose
    sp.paint(sp.rect(60, 56, 68, 62), 0.6, STEEL)  # lamp holder
    shade = poly(sp, [(60, 58), (68, 58), (96, 86), (32, 86)])
    sh = 0.62 - 0.55 * np.clip((sp.x - 32) / 64, 0, 1) + 0.1 * np.sin((sp.x - 32) / 64 * np.pi)
    sp.paint(shade, sh + (nz(sp, 41, 3.0) - 0.5) * 0.2, STEEL)
    sp.paint(sp.rect(33, 84, 96, 88), 0.82, STEEL)  # rolled rim
    sp.paint(sp.rect(33, 87, 96, 89), 0.2, STEEL)
    sp.paint(sp.ellipse(36, 70, 2, 6) & shade, 0.9, STEEL)
    # the bulb under the shade
    sp.paint(sp.ellipse(64, 96, 9, 11), 0.55 + 0.45 * np.clip(1 - np.hypot(sp.x - 62, sp.y - 94) / 9, 0, 1), BULB)
    sp.paint(sp.ellipse(64, 96, 3, 4), 1.0, BULB)
    sp.paint(sp.line(62, 90, 66, 100, 1), 0.6, BULB)  # filament
    outline(sp)
    glow(sp, 64, 98, 56, BULB, 1.7, tint=0.5)
    return sp.rgba()


# ---- the caged green lamp -----------------------------------------------------------------------------------------------------------------------

def thing_lamp_red():
    """A small caged bulkhead lamp glowing dim green (the name is the old one: the lamp is green in the bomber)."""
    sp = Sprite()
    sp.paint(sp.rect(36, 2, 92, 16), bev(sp, 36, 2, 92, 16, 0.5, 0.16, 51), IRON)  # mounting plate
    rivets(sp, [(42, 9), (86, 9)], 1.4, 0.8)
    sp.paint(sp.rect(52, 16, 76, 28), cyl(sp, 52, 76, 0.55, 0.4, 52), IRON)  # collar
    dome = (np.abs((sp.x - 64) / 28) ** 3 + np.abs((sp.y - 56) / 30) ** 2 <= 1) & (sp.y > 26) & (sp.y < 86)
    sp.paint(dome, 0.55 + 0.45 * np.clip(1 - np.hypot((sp.x - 64) / 28, (sp.y - 58) / 30), 0, 1), GREENLIT)
    sp.paint(sp.ellipse(64, 58, 14, 17), 0.9, GREENLIT)  # the lit bulb
    sp.paint(sp.ellipse(64, 58, 8, 11), 1.0, GREENLIT)
    sp.paint(sp.ellipse(64, 58, 3, 5), 1.0, GREENLIT)
    # the cage: three wire ribs and two hoops, dark, over the glow
    for dx in (-17, 0, 17):
        xs = np.abs((sp.x - 64) - dx * np.sqrt(np.clip(1 - ((sp.y - 56) / 32) ** 2, 0, 1)))
        sp.paint(dome & (xs < 1.5), 0.2, IRON)
    for yy in (44, 70):
        sp.paint(dome & (np.abs(sp.y - yy) < 1.5), 0.2, IRON)
    sp.paint(sp.ellipse(64, 86, 31, 4), 0.5, IRON)  # bottom ring
    sp.paint(sp.rect(60, 86, 68, 92), 0.4, IRON)
    outline(sp)
    glow(sp, 64, 58, 62, GREENLIT, 2.0, tint=0.35, lo=2)
    return sp.rgba()


# ---- the Quartermaster's ledger ----------------------------------------------------------------------------------------------------------------

def _bil(p00, p10, p01, p11, u, v):
    """Bilinear point on a quad (u across, v down)."""
    top = (p00[0] + (p10[0] - p00[0]) * u, p00[1] + (p10[1] - p00[1]) * u)
    bot = (p01[0] + (p11[0] - p01[0]) * u, p01[1] + (p11[1] - p01[1]) * u)
    return (top[0] + (bot[0] - top[0]) * v, top[1] + (bot[1] - top[1]) * v)


def thing_ledger():
    """An enormous open ledger on a lectern: ruled columns of tiny figures, a pen in an inkwell, a green-shaded lamp."""
    sp = Sprite()
    # lectern: a post, a foot, a deep slanted top
    sp.paint(sp.rect(54, 88, 78, 118), cyl(sp, 54, 78, 0.55, 0.45, 61, 0.1), WOOD)
    sp.paint(sp.rect(34, 114, 98, 127), bev(sp, 34, 114, 98, 127, 0.5, 0.16, 62), WOOD)
    sp.paint(sp.rect(46, 104, 86, 108), 0.62, WOOD)
    top = poly(sp, [(4, 90), (128, 90), (116, 40), (16, 40)])
    sp.paint(top, 0.5 + 0.3 * (sp.y < 44) + (nz(sp, 63, 3.0) - 0.5) * 0.2, WOOD)
    sp.paint(sp.rect(4, 90, 128, 97), bev(sp, 4, 90, 128, 97, 0.42, 0.12, 64, 0.1, 1), WOOD)  # the lip
    # the open book: two big pages on the slope with a bulging spine
    L = [(16, 44), (64, 40), (62, 88), (10, 88)]
    R = [(66, 40), (114, 44), (122, 88), (68, 88)]
    pl, pr = poly(sp, L), poly(sp, R)
    sp.paint(pl, 0.8 - 0.1 * np.clip((sp.x - 40) / 24, 0, 1) + (nz(sp, 65, 4.0) - 0.5) * 0.2, PAPER)
    sp.paint(pr, 0.8 - 0.1 * np.clip((90 - sp.x) / 24, 0, 1) + (nz(sp, 66, 4.0) - 0.5) * 0.2, PAPER)
    sp.paint(poly(sp, [(62, 38), (66, 38), (68, 90), (62, 90)]), 0.28, PAPER)  # gutter
    # page edges, a stack of leaves, on the lower front
    sp.paint(poly(sp, [(10, 88), (62, 88), (62, 92), (8, 92)]), 0.5, PAPER)
    sp.paint(poly(sp, [(68, 88), (122, 88), (124, 92), (68, 92)]), 0.4, PAPER)
    # ruled columns and rows of tiny figures (lines only, no letters)
    rng = np.random.RandomState(70)
    for q in (L, R):
        p00, p10, p01, p11 = q[0], q[1], q[3], q[2]
        cols = [0.08, 0.30, 0.52, 0.74, 0.94]
        for u in cols:
            a, b = _bil(p00, p10, p01, p11, u, 0.05), _bil(p00, p10, p01, p11, u, 0.95)
            sp.paint(sp.line(a[0], a[1], b[0], b[1], 1.0), 0.15, PAPER)
        for r in range(11):
            v = 0.1 + r * 0.08
            a, b = _bil(p00, p10, p01, p11, 0.08, v), _bil(p00, p10, p01, p11, 0.94, v)
            sp.paint(sp.line(a[0], a[1], b[0], b[1], 1.0), 0.35, PAPER)
            for ci in range(4):
                u0 = cols[ci] + 0.03
                ln = rng.uniform(0.07, 0.17)
                a, b = _bil(p00, p10, p01, p11, u0, v - 0.03), _bil(p00, p10, p01, p11, u0 + ln, v - 0.03)
                sp.paint(sp.line(a[0], a[1], b[0], b[1], 1.0), 0.0, PAPER)
        # red entry marks in the margin
        for v in (0.18, 0.42, 0.7):
            a, b = _bil(p00, p10, p01, p11, 0.02, v), _bil(p00, p10, p01, p11, 0.06, v)
            sp.paint(sp.line(a[0], a[1], b[0], b[1], 1.5), 0.6, REDP)
    # the inkwell and pen on the left lip
    sp.paint(sp.rect(10, 82, 24, 96), cyl(sp, 10, 24, 0.35, 0.4), IRON)
    sp.paint(sp.ellipse(17, 82, 7, 2.5), 0.08, IRON)
    sp.paint(sp.line(18, 82, 8, 14, 2), 0.7, WOOD)  # the pen standing in the well
    sp.paint(sp.tri([(6, 16), (10, 16), (7, 8)]), 0.95, PAPER)
    # the green-shaded lamp on the right: a brass foot and arm, a green glass shade
    sp.paint(sp.rect(98, 88, 120, 94), 0.55, BRASS)
    sp.paint(sp.line(110, 90, 110, 44, 3), 0.55, BRASS)
    sp.paint(sp.line(110, 44, 92, 28, 3), 0.55, BRASS)
    shade = poly(sp, [(76, 20), (98, 30), (106, 38), (72, 38)])
    sp.paint(shade, 0.72 - 0.5 * np.clip((sp.x - 72) / 34, 0, 1) + 0.1 * (sp.y < 25), GREENLIT)
    sp.paint(sp.rect(72, 37, 106, 39), 0.3, GREENLIT)
    sp.paint(sp.ellipse(88, 42, 6, 3.5), 1.0, BULB)
    outline(sp)
    glow(sp, 88, 50, 30, BULB, 2.2, tint=0.5, lo=1)
    return sp.rgba()


# ---- the bomber's nose glass --------------------------------------------------------------------------------------------------------------------

def thing_nose_glass():
    """The glazed nose from inside: a curved frame of dark struts round black night glass, flak flashes and orange tracer, an instrument-lit rim."""
    sp = Sprite()
    cx, cy = 64.0, 66.0
    outer = (((sp.x - cx) / 62) ** 2 + ((sp.y - cy) / 62) ** 2 <= 1) & (sp.y < 118)
    inner = (((sp.x - cx) / 52) ** 2 + ((sp.y - cy) / 52) ** 2 <= 1) & (sp.y < 108)
    ring = outer & ~inner
    sp.paint(ring, 0.45 + 0.3 * ((sp.x + sp.y) < 90) - 0.25 * ((sp.x + sp.y) > 150) + (nz(sp, 81, 3.0) - 0.5) * 0.2, IRON)
    # struts: three meridians and two hoops
    struts = np.zeros(sp.a.shape, bool)
    for k in (-1, 0, 1):
        a = [(cx + k * 6, 16), (cx + k * 26, 50), (cx + k * 40, 80), (cx + k * 48, 108)]
        for p, q in zip(a[:-1], a[1:]):
            struts |= sp.line(p[0], p[1], q[0], q[1], 4.5)
    struts |= np.abs(sp.y - (48 + ((sp.x - cx) / 52) ** 2 * 8)) < 2.2
    struts |= np.abs(sp.y - (82 + ((sp.x - cx) / 52) ** 2 * 14)) < 2.2
    struts &= inner | ring
    # the night glass
    glass = inner & ~struts
    gsh = 0.1 + 0.35 * np.clip((sp.y - 20) / 90, 0, 1) ** 2 + (nz(sp, 82, 6.0) - 0.5) * 0.25
    sp.paint(glass, gsh, NIGHT)
    # distant fires on the horizon: a dithered orange smear low left
    horizon = glass & (sp.y > 86) & (np.abs(sp.y - 100 + 6 * np.sin(sp.x * 0.15)) < 10)
    hz = np.clip(1 - np.abs(sp.y - 100) / 10, 0, 1) * (0.5 + 0.5 * nz(sp, 83, 5.0))
    b = BAYER8[sp.y.astype(int) % 8, sp.x.astype(int) % 8] + 0.5
    sp.paint(horizon & (hz * (1.2 - sp.x / 200) > b * 0.9), 0.3, FIRE)
    sp.paint(struts & inner, 0.35 + 0.3 * ((sp.x + sp.y) % 7 < 2), IRON)
    sp.paint(struts & inner & (nz(sp, 84, 3.0) > 0.7), 0.7, IRON)
    # flak flashes
    for (fx, fy, r) in ((36, 38, 8), (92, 58, 6), (78, 26, 4), (52, 70, 3)):
        d = np.hypot(sp.x - fx, sp.y - fy)
        spokes = np.abs(np.sin(np.arctan2(sp.y - fy, sp.x - fx) * 4 + fx)) > 0.7
        burst = glass & ((d < r * 0.55) | ((d < r * 1.6) & spokes & (d > r * 0.4)))
        sp.paint(burst, np.clip(1.0 - d / (r * 1.6) + 0.15, 0, 1), FIRE)
        sp.paint(glass & (d < r * 0.3), 1.0, FIRE)
    # tracer lines: dashed orange streaks climbing to the upper right
    for (x0, y0, x1, y1) in ((44, 104, 70, 56), (72, 106, 88, 78), (56, 100, 62, 86)):
        seg = sp.line(x0, y0, x1, y1, 1.6)
        L = np.hypot(sp.x - x0, sp.y - y0)
        sp.paint(seg & glass & ((L % 9) < 5), 0.8, FIRE)
    # instrument-lit rim: green lamps and a console strip along the bottom
    sp.paint(sp.rect(14, 108, 114, 124) & (((sp.x - cx) / 62) ** 2 <= 1), bev(sp, 14, 108, 114, 124, 0.3, 0.16, 85), IRON)
    sp.paint(sp.rect(18, 109, 110, 111), 0.18, IRON)
    for dx in (24, 44, 84, 104):
        sp.paint(sp.ellipse(dx, 117, 5, 5), 0.25, IRON)
        sp.paint(sp.ellipse(dx, 117, 3.4, 3.4), 0.65, GREENLIT)
        sp.paint(sp.rect(dx - 0.5, 114, dx + 0.5, 117), 1.0, GREENLIT)
    for k in range(11):
        ang = np.pi * (0.1 + 0.8 * k / 10)
        px, py = cx + 50 * np.cos(ang + np.pi), cy + 50 * np.sin(ang + np.pi)
    for ang in np.linspace(np.pi * 0.62, np.pi * 0.98, 6):
        px, py = cx + 56 * np.cos(ang), cy + 56 * np.sin(ang) * 0.98
        sp.paint(sp.ellipse(px, py, 1.5, 1.5), 0.85, GREENLIT)
    outline(sp)
    glow(sp, 64, 116, 40, GREENLIT, 2.4, tint=0.0, lo=2)
    return sp.rgba()


# ---- the bomb release lever ---------------------------------------------------------------------------------------------------------------------

def thing_release_lever():
    """A red-knobbed iron lever on a dark box with a dial and a toggle, lit by a small green lamp."""
    sp = Sprite()
    box = sp.rect(14, 66, 114, 126)
    sp.paint(box, bev(sp, 14, 66, 114, 126, 0.42, 0.16, 91), IRON)
    rivets(sp, [(20, 72), (108, 72), (20, 120), (108, 120)], 1.5, 0.75)
    # the dial: round glass face, ticks, a needle
    sp.paint(sp.ellipse(42, 96, 17, 17), 0.35, STEEL)
    sp.paint(sp.ellipse(42, 96, 14, 14), 0.06, GREENLIT)
    ang = np.arctan2(sp.y - 96, sp.x - 42)
    d = np.hypot(sp.x - 42, sp.y - 96)
    ticks = (d > 10) & (d < 13.5) & (np.abs(np.sin(ang * 6)) < 0.18) & (np.abs(ang + np.pi / 2) > 0.2)
    sp.paint(ticks, 0.75, GREENLIT)
    sp.paint(sp.line(42, 96, 50, 87, 1.6), 1.0, GREENLIT)
    sp.paint(sp.ellipse(42, 96, 2, 2), 0.6, STEEL)
    sp.paint(sp.ellipse(42, 96, 14, 14) & (sp.x + sp.y < 124) & (d > 12), 0.5, STEEL)
    # a toggle switch with its little guard
    sp.paint(sp.rect(76, 90, 92, 106), cyl(sp, 76, 92, 0.5, 0.3), STEEL)
    sp.paint(sp.line(84, 98, 84, 80, 4), 0.75, STEEL)
    sp.paint(sp.ellipse(84, 79, 3, 3), 0.9, STEEL)
    sp.paint(sp.rect(96, 98, 108, 102), 0.35, IRON)
    sp.paint(sp.rect(70, 108, 104, 112), 0.25, IRON)
    sp.paint(sp.rect(72, 109, 80, 111), 0.9, GREENLIT)
    # the lever: a slotted quadrant, an iron arm leaning to the left, a red ball
    sp.paint(poly(sp, [(56, 66), (74, 66), (78, 56), (52, 56)]), 0.3, IRON)
    sp.paint(sp.rect(60, 58, 64, 66), 0.05, IRON)
    sp.paint(sp.line(62, 64, 44, 14, 6), 0.55 + 0.1 * (sp.x < 53), STEEL)
    sp.paint(sp.line(60.5, 64, 42.5, 14, 1.5), 0.9, STEEL)
    sp.paint(sp.ellipse(62, 64, 6, 6), 0.7 - 0.2 * (sp.x > 62), STEEL)
    sp.paint(sp.ellipse(42, 10, 8, 8), sphere(sp, 42, 10, 8, 0.62, 0.9), REDP)
    sp.paint(sp.ellipse(39, 7, 2, 2), 1.0, REDP)
    # small green lamp on the box's top-right corner
    sp.paint(sp.rect(94, 54, 108, 66), cyl(sp, 94, 108, 0.45, 0.3), IRON)
    sp.paint(sp.ellipse(101, 54, 8, 8) & (sp.y < 58), 0.7 + 0.3 * ((sp.x - 101) < 0), GREENLIT)
    sp.paint(sp.ellipse(101, 54, 3.5, 3.5), 1.0, GREENLIT)
    outline(sp)
    glow(sp, 101, 54, 34, GREENLIT, 2.2, tint=0.4, lo=2)
    return sp.rgba()


# ---- the sandbag wall --------------------------------------------------------------------------------------------------------------------------

def _bag(sp, cx, cy, rx, ry, tone, seed):
    m = (np.abs((sp.x - cx) / rx) ** 3 + np.abs((sp.y - cy) / ry) ** 2) <= 1.0
    lx = (sp.x - cx) / rx
    ly = (sp.y - cy) / ry
    sh = tone - 0.22 * ly - 0.12 * lx + 0.12 * np.exp(-((ly + 0.6) ** 2) * 6) * (1 - np.abs(lx))
    sh += (nz(sp, seed, 2.0) - 0.5) * 0.28
    weave = ((sp.x.astype(int) + sp.y.astype(int)) % 2 == 0) * 0.04
    sp.paint(m, sh + weave, KHAKI)
    sp.paint(m & (np.abs(sp.y - (cy - ry * 0.05)) < 0.7) & (np.abs(lx) < 0.7), sh - 0.25, KHAKI)  # the tied-end seam
    return m


def thing_sandbags():
    """A low wall of sandbags, a lazy stack of ammunition boxes on top."""
    sp = Sprite()
    rng = np.random.RandomState(101)

    def crate(pts, base, seed):
        m = poly(sp, pts)
        sp.paint(m, base + (nz(sp, seed, 2.5) - 0.5) * 0.25 + 0.14 * ((sp.y - pts[0][1]) < 3), OLIVE)
        return m

    def band(pts, shade, pal=DUST):
        sp.paint(poly(sp, pts), shade, pal)

    # lower box (sits on the wall)
    crate([(12, 50), (62, 48), (64, 76), (14, 78)], 0.5, 111)
    band([(12, 50), (62, 48), (62, 52), (12, 54)], 0.84, OLIVE)
    band([(18, 62), (58, 61), (58, 65), (18, 66)], 0.78)  # painted bars (no letters)
    band([(18, 69), (42, 68.5), (42, 72), (18, 72.5)], 0.78)
    sp.paint(sp.line(28, 49.5, 50, 49, 3), 0.1, OLIVE)  # the handle slot
    # upper box, tilted off to one side
    crate([(22, 24), (70, 14), (74, 40), (26, 50)], 0.46, 112)
    band([(22, 24), (70, 14), (71, 18), (23, 28)], 0.86, OLIVE)
    band([(30, 33), (62, 26), (63, 30), (31, 37)], 0.75)
    band([(30, 40), (50, 36), (51, 39), (31, 43)], 0.75)
    # an open box on the right with its lid propped up
    crate([(82, 36), (118, 44), (114, 74), (80, 68)], 0.4, 113)
    band([(82, 36), (118, 44), (117, 48), (82, 40)], 0.8, OLIVE)
    band([(88, 52), (110, 56), (109, 60), (88, 56)], 0.7)
    sp.paint(poly(sp, [(86, 38), (112, 44), (112, 52), (88, 46)]) & (sp.y < 40), 0.05, OLIVE)
    # the wall: a dark backing so no gaps show, then four rows of bags, offset like brickwork
    sp.paint(sp.rect(0, 66, 128, 124), 0.12 + (nz(sp, 119, 3.0) - 0.5) * 0.1, KHAKI)
    rows = [(118, 9, 26, 0), (103, 9, 26, 13), (88, 9, 26, 0), (73, 9, 26, 13)]
    for ri, (cy, ry, w, off) in enumerate(rows):
        x = -4 + off - (13 if off else 0)
        while x < 132:
            _bag(sp, x + w / 2, cy + rng.randint(-1, 2), w / 2 + 1.5, ry, 0.36 + rng.rand() * 0.22, 120 + ri * 9 + int(x))
            x += w - 1
    # spilled sand at the foot
    for k in range(18):
        x, y = rng.randint(2, 126), rng.randint(123, 127)
        sp.paint(sp.rect(x, y, x + 2, y + 1), 0.45, DUST)
    outline(sp)
    return sp.rgba()


# ---- the shop scale ----------------------------------------------------------------------------------------------------------------------------

def thing_scales():
    """A brass shop balance on a counter: a sack of flour on one pan, brass weights on the other."""
    sp = Sprite()
    # counter
    sp.paint(sp.rect(2, 98, 126, 108), bev(sp, 2, 98, 126, 108, 0.62, 0.16, 131, 0.1), WOOD)
    sp.paint(sp.rect(6, 108, 122, 126), bev(sp, 6, 108, 122, 126, 0.32, 0.1, 132, 0.12), WOOD)
    for x in (34, 64, 94):
        sp.paint(sp.rect(x, 109, x + 1, 126), 0.1, WOOD)
    # the base, the post and the finial
    sp.paint(sp.ellipse(64, 97, 20, 5), cyl(sp, 44, 84, 0.6, 0.4), BRASS)
    sp.paint(sp.rect(44, 93, 84, 97), cyl(sp, 44, 84, 0.55, 0.4), BRASS)
    sp.paint(sp.rect(60, 34, 68, 94), cyl(sp, 60, 68, 0.6, 0.5), BRASS)
    sp.paint(sp.ellipse(64, 28, 5, 5), sphere(sp, 64, 28, 5, 0.7, 0.8), BRASS)
    # the beam: tilted, left end low
    lx, ly, rx, ry = 20.0, 42.0, 108.0, 26.0
    sp.paint(sp.line(lx, ly, rx, ry, 4), 0.7 - 0.15 * (sp.y > 36), BRASS)
    sp.paint(sp.line(lx, ly - 1.2, rx, ry - 1.2, 1.2), 0.95, BRASS)
    sp.paint(sp.ellipse(64, 34, 5, 5), sphere(sp, 64, 34, 5, 0.65, 0.8), BRASS)
    for (ex, ey) in ((lx, ly), (rx, ry)):
        sp.paint(sp.ellipse(ex, ey, 3, 3), 0.85, BRASS)
    # chains and pans
    pans = []
    for (ex, ey) in ((lx, ly), (rx, ry)):
        py = ey + 44
        pans.append((ex, py))
        for ox in (-17, 17):
            sp.paint(sp.line(ex, ey, ex + ox, py, 1.4), 0.5, BRASS)
        sp.paint(sp.line(ex - 17, py, ex + 17, py, 1.4), 0.6, BRASS)
        bowl = sp.ellipse(ex, py - 1, 19, 8) & (sp.y >= py)
        sp.paint(bowl, 0.7 - 0.5 * (sp.x - ex + 19) / 38 + 0.2 * (sp.y < py + 2), BRASS)
    # flour sack on the left pan
    (fx, fy), (wx, wy) = pans
    sack = (np.abs((sp.x - fx) / 13) ** 2.4 + np.abs((sp.y - (fy - 12)) / 12) ** 2) <= 1
    sp.paint(sack & (sp.y > fy - 20), 0.82 - 0.35 * (sp.x - fx + 13) / 26 + (nz(sp, 133, 2.0) - 0.5) * 0.18, PAPER)
    sp.paint(poly(sp, [(fx - 5, fy - 24), (fx + 5, fy - 24), (fx + 7, fy - 19), (fx - 7, fy - 19)]), 0.55, PAPER)
    sp.paint(sp.rect(fx - 6, fy - 21, fx + 6, fy - 19), 0.25, DUST)  # the tie
    sp.paint(sp.rect(fx - 9, fy - 14, fx - 7, fy - 5), 0.95, PAPER)
    # brass weights on the right pan
    for k, (w, h) in enumerate(((16, 8), (12, 7), (9, 6))):
        top = wy - 1 - sum(hh for _, hh in ((16, 8), (12, 7), (9, 6))[:k + 1]) - k
        sp.paint(sp.rect(wx - w / 2, top, wx + w / 2, top + h), cyl(sp, wx - w / 2, wx + w / 2, 0.58, 0.45), BRASS)
        sp.paint(sp.rect(wx - w / 2, top, wx + w / 2, top + 1), 0.98, BRASS)
    sp.paint(sp.ellipse(wx, wy - 26, 3, 2.5), 0.85, BRASS)
    # a loose small weight on the counter
    sp.paint(sp.rect(98, 90, 110, 98), cyl(sp, 98, 110, 0.55, 0.4), BRASS)
    sp.paint(sp.ellipse(104, 89, 3, 2.5), 0.85, BRASS)
    outline(sp)
    return sp.rgba()


# ---- the hospital screen ----------------------------------------------------------------------------------------------------------------------

def thing_screen_cloth():
    """A folding hospital screen: three grey cloth panels in a wooden frame, zig-zagged, stained at the foot."""
    sp = Sprite()
    xs = [10, 40, 70, 100]
    tops = [14, 8, 14]
    shades = [0.7, 0.45, 0.62]
    for i in range(3):
        x0, x1 = xs[i] + (0 if i == 0 else 0), xs[i + 1]
        x1 = x1 + 14 if i == 2 else x1
        top = tops[i]
        # a panel: wooden stiles and rails, cloth between
        sp.paint(sp.rect(x0, top, x1, 124), bev(sp, x0, top, x1, 124, 0.5, 0.15, 141 + i), WOOD)
        sp.paint(sp.rect(x0 + 3, top + 3, x1 - 3, 121), shades[i] + (nz(sp, 144 + i, 2.5) - 0.5) * 0.25 + 0.06 * (((sp.x + sp.y) % 2) == 0), CANVAS)
        # cloth sags and folds
        sp.paint(sp.rect(x0 + 3, top + 3, x1 - 3, top + 5), shades[i] + 0.15, CANVAS)
        for fx in (x0 + 10, x0 + 19):
            sp.paint(sp.rect(fx, top + 5, fx + 1, 118) & ((nz(sp, 150 + i, 5.0) > 0.4)), shades[i] - 0.28, CANVAS)
        sp.paint(sp.rect(x0 + 3, top + 40, x1 - 3, top + 43), shades[i] - 0.15, CANVAS)  # a mid rail shadow
        sp.paint(sp.rect(x0, top + 38, x1, top + 41), 0.55, WOOD)
        # stains near the floor
        st = (nz(sp, 160 + i, 6.0) > 0.58) & (sp.y > 90) & (sp.x > x0 + 3) & (sp.x < x1 - 3) & (sp.y < 121)
        sp.paint(st, 0.4 + 0.0 * sp.x, CANVAS)
    # the fold lines are darker stiles
    for x in xs[1:3]:
        sp.paint(sp.rect(x - 1, 8, x + 1, 124), 0.18, WOOD)
    # a rusty spot and small feet
    for x in (xs[0] + 2, xs[1], xs[2], xs[3] + 12):
        sp.paint(sp.rect(x - 1, 124, x + 5, 127), 0.35, WOOD)
    outline(sp)
    return sp.rgba()


# ---- the store shelves -------------------------------------------------------------------------------------------------------------------------

def thing_shelves_tins():
    """Tall metal shelving packed with tins, jars, boots and blankets, price tags as small coloured squares."""
    sp = Sprite()
    # uprights and shelf boards
    sp.paint(sp.rect(4, 2, 10, 127) | sp.rect(118, 2, 124, 127), cyl(sp, 4, 124, 0.5, 0.0) + (nz(sp, 171, 3.0) - 0.5) * 0.2, STEEL)
    sp.paint(sp.rect(4, 2, 7, 127) | sp.rect(118, 2, 121, 127), 0.78, STEEL)
    shelves = [25, 49, 73, 97, 121]
    tag_cols = [REDP, GREENLIT, DUST, BULB]
    rng = np.random.RandomState(172)
    rows = ["tins", "jars", "blankets", "boots", "tins2"]
    for ri, sy in enumerate(shelves):
        kind = rows[ri]
        x = 12
        top = sy - 21
        if kind in ("tins", "tins2"):
            while x < 112:
                w = int(rng.choice([8, 10, 12]))
                h = int(rng.choice([12, 15, 18]))
                if kind == "tins2":
                    h = int(rng.choice([8, 11]))
                body = sp.rect(x, sy - h, x + w, sy)
                tone = [0.55, 0.45, 0.7][rng.randint(0, 3)]
                sp.paint(body, cyl(sp, x, x + w, tone, 0.45), STEEL)
                lab_cols = [(DUST, 0.6), (OLIVE, 0.75), (REDP, 0.55), (PAPER, 0.7)]
                lp, ls = lab_cols[rng.randint(0, 4)]
                sp.paint(sp.rect(x, sy - h + 3, x + w, sy - 3), cyl(sp, x, x + w, ls, 0.4) , lp)
                sp.paint(sp.rect(x, sy - h, x + w, sy - h + 1), 0.9, STEEL)
                x += w + 1
        elif kind == "jars":
            while x < 112:
                w = int(rng.choice([10, 12, 14]))
                h = int(rng.choice([14, 17, 20]))
                body = sp.rect(x, sy - h, x + w, sy)
                col = [(DUST, 0.55), (REDP, 0.5), (OLIVE, 0.7), (BULB, 0.45)][rng.randint(0, 4)]
                sp.paint(body, cyl(sp, x, x + w, col[1], 0.4, 176 + x, 0.1), col[0])
                sp.paint(sp.rect(x + 1, sy - h + 1, x + 2, sy - 2), 0.95, SKYW)
                sp.paint(sp.rect(x + 1, sy - h - 3, x + w - 1, sy - h), 0.5, STEEL)  # lid
                x += w + 2
        elif kind == "blankets":
            cols = [(OLIVE, 0.6), (CANVAS, 0.6), (KHAKI, 0.55), (OLIVE, 0.45), (DUST, 0.5)]
            for sx0, sx1 in ((12, 52), (56, 110)):
                yy = sy
                for k in range(4):
                    h = int(rng.randint(5, 7))
                    p, tn = cols[rng.randint(0, 5)]
                    sp.paint(sp.rect(sx0 + rng.randint(0, 3), yy - h, sx1 - rng.randint(0, 3), yy), 0.7 * tn + 0.12 * ((sp.y - (yy - h)) < 1.5) + (nz(sp, 180 + k + sx0, 2.0) - 0.5) * 0.25 + 0.2, p)
                    sp.paint(sp.rect(sx0 + 2, yy - h + 2, sx1 - 2, yy - h + 3) & ((k % 2) == 0), 0.2, p)
                    yy -= h
        elif kind == "boots":
            x = 14
            for k in range(5):
                sp.paint(poly(sp, [(x, sy - 18), (x + 8, sy - 18), (x + 8, sy - 6), (x + 17, sy - 6), (x + 17, sy), (x, sy)]), 0.4 + (nz(sp, 190 + k, 2.0) - 0.5) * 0.3 + 0.14 * (sp.x < x + 3), WOOD)
                sp.paint(sp.rect(x, sy - 3, x + 17, sy), 0.12, WOOD)
                sp.paint(sp.rect(x, sy - 19, x + 8, sy - 17), 0.15, IRON)
                x += 19
            sp.paint(sp.rect(106, sy - 14, 114, sy), 0.5, TARP)  # a rolled mat
        # the shelf board and its price tags
        sp.paint(sp.rect(8, sy, 120, sy + 3), 0.55, STEEL)
        sp.paint(sp.rect(8, sy, 120, sy + 1), 0.9, STEEL)
        for tx in range(16, 112, 17):
            tp = tag_cols[rng.randint(0, 4)]
            sp.paint(sp.rect(tx + rng.randint(0, 5), sy + 1, tx + 5 + rng.randint(0, 5), sy + 4), 0.75, tp)
    # cross bracing at the back left
    outline(sp)
    return sp.rgba()


# ---- the store's painted sign ----------------------------------------------------------------------------------------------------------------

def thing_sign_ledgerless():
    """A hand-painted board over the store door: a crate, a coin and a plain star (pictures only), hung on two ropes."""
    sp = Sprite()
    # chains/ropes to the top edge
    for x in (20, 108):
        sp.paint(sp.rect(x - 1, 0, x + 2, 30), 0.4 + 0.2 * (np.floor((sp.y) / 2) % 2), WOOD)
    # the board
    sp.paint(sp.rect(4, 26, 124, 108), bev(sp, 4, 26, 124, 108, 0.55, 0.12, 201, 0.14), WOOD)
    # paint plane: chalky khaki, inset
    pane = sp.rect(10, 32, 118, 102)
    sp.paint(pane, 0.72 + (nz(sp, 202, 4.0) - 0.5) * 0.35 + 0.0 * sp.x, PAPER)
    for yy in (44, 56, 68, 80, 92):  # plank joints
        sp.paint(sp.rect(10, yy, 118, yy + 1), 0.35 + 0.0, PAPER) if False else None
    sp.paint(sp.rect(10, 32, 118, 34) | sp.rect(10, 100, 118, 102) | sp.rect(10, 32, 12, 102) | sp.rect(116, 32, 118, 102), 0.1, WOOD)
    # worn flaking
    flake = (nz(sp, 203, 3.0, 3) > 0.7) & pane
    sp.paint(flake, 0.55, PAPER)
    # the crate: a box with slats and a lid band
    sp.paint(sp.rect(16, 52, 48, 88), bev(sp, 16, 52, 48, 88, 0.5, 0.2, 204), WOOD)
    for yy in (60, 70, 80):
        sp.paint(sp.rect(16, yy, 48, yy + 1), 0.15, WOOD)
    sp.paint(sp.line(17, 53, 47, 87, 2.2) | sp.line(47, 53, 17, 87, 2.2), 0.7, WOOD)
    sp.paint(sp.rect(16, 52, 48, 55), 0.82, WOOD)
    # the coin: a gold disc with a raised rim and a stamped dot
    sp.paint(sp.ellipse(76, 70, 18, 18), sphere(sp, 76, 70, 18, 0.6, 0.7), BRASS)
    sp.paint(sp.ellipse(76, 70, 18, 18) & ~sp.ellipse(76, 70, 14.5, 14.5), 0.9 - 0.4 * (sp.x > 76), BRASS)
    sp.paint(sp.ellipse(76, 70, 7, 7), 0.5 + 0.3 * (sp.y < 70), BRASS)
    sp.paint(sp.ellipse(76, 70, 3, 3), 0.9, BRASS)
    # the star (five points, no crown above it)
    pts = []
    for k in range(10):
        r = 15 if k % 2 == 0 else 6.5
        a = -np.pi / 2 + k * np.pi / 5
        pts.append((104 + r * np.cos(a), 70 + r * np.sin(a)))
    st = poly(sp, pts)
    sp.paint(st, 0.65 - 0.15 * (sp.x > 104), REDP)
    sp.paint(st & (np.hypot(sp.x - 104, sp.y - 70) < 5), 0.95, REDP)
    # a drip of paint below the board
    sp.paint(sp.rect(60, 108, 62, 116) | sp.rect(88, 108, 90, 112), 0.25, WOOD)
    sp.paint(sp.rect(10, 104, 118, 108), 0.18, WOOD)
    outline(sp)
    return sp.rgba()


# ---- the Registrar's stamp ---------------------------------------------------------------------------------------------------------------------

def thing_stamp_big():
    """A huge rubber stamp on a stand beside an ink pad: its face is a plain red bar, larger than life."""
    sp = Sprite()
    # the wooden handle: a turned knob and neck above the block
    sp.paint(sp.rect(34, 6, 58, 20), cyl(sp, 34, 58, 0.6, 0.5, 213), WOOD)
    sp.paint(sp.ellipse(46, 12, 14, 9), sphere(sp, 46, 12, 14, 0.64, 0.9), WOOD)
    sp.paint(sp.rect(40, 20, 52, 52), cyl(sp, 40, 52, 0.55, 0.5, 214), WOOD)
    sp.paint(sp.rect(36, 40, 56, 46), cyl(sp, 36, 56, 0.5, 0.45), WOOD)
    sp.paint(sp.ellipse(46, 54, 11, 4), 0.4, WOOD)
    # the stamp block: a deep wooden back
    sp.paint(sp.rect(8, 56, 86, 94), bev(sp, 8, 56, 86, 94, 0.55, 0.18, 215, 0.14, 3), WOOD)
    sp.paint(sp.rect(8, 56, 86, 60), 0.92, WOOD)
    # the rubber face: black rubber with a plain red bar
    sp.paint(sp.rect(8, 94, 86, 120), bev(sp, 8, 94, 86, 120, 0.22, 0.1, 216, 0.1), IRON)
    sp.paint(sp.rect(14, 98, 80, 116), 0.32 + (nz(sp, 217, 2.0) - 0.5) * 0.3, REDP)  # the red bar
    sp.paint(sp.rect(14, 98, 80, 101), 0.95, REDP)
    sp.paint(sp.rect(14, 114, 80, 116), 0.12, REDP)
    # a small paper sheet under the stamp
    sp.paint(poly(sp, [(4, 122), (92, 122), (96, 127), (2, 127)]), 0.8, PAPER)
    # the ink pad on the right: a flat tin with a red-soaked pad
    sp.paint(sp.rect(98, 100, 126, 126), bev(sp, 98, 100, 126, 126, 0.4, 0.16, 218), OLIVE)
    sp.paint(poly(sp, [(98, 100), (126, 100), (122, 92), (102, 92)]), 0.52, OLIVE)
    sp.paint(poly(sp, [(103, 99), (121, 99), (119, 94), (105, 94)]), 0.5 + (nz(sp, 219, 3.0) - 0.5) * 0.4, REDP)
    sp.paint(sp.rect(102, 108, 122, 110), 0.75, DUST)
    outline(sp)
    return sp.rgba()


# ---- the iron stove ---------------------------------------------------------------------------------------------------------------------------

def thing_stove():
    """A squat iron stove with a stovepipe going up, a kettle on top and a glow in its door."""
    sp = Sprite()
    # legs
    for x in (30, 90):
        sp.paint(sp.rect(x, 108, x + 8, 126), 0.35, IRON)
    body = sp.rect(24, 62, 104, 112) | (sp.ellipse(64, 62, 40, 6) & (sp.y < 62))
    sp.paint(body, cyl(sp, 24, 104, 0.5, 0.5, 231, 0.12), IRON)
    # rust blooms
    sp.paint(body & (nz(sp, 232, 5.0, 3) > 0.62), 0.28, DUST)
    # top plate and base plate
    sp.paint(sp.rect(20, 58, 108, 64), bev(sp, 20, 58, 108, 64, 0.62, 0.16, 233, 0.08, 1), IRON)
    sp.paint(sp.rect(22, 108, 106, 114), bev(sp, 22, 108, 106, 114, 0.5, 0.16, 234, 0.08, 1), IRON)
    # the firebox door with a glow
    door = sp.rect(42, 74, 86, 102)
    sp.paint(door, bev(sp, 42, 74, 86, 102, 0.4, 0.2, 235), IRON)
    sp.paint(sp.rect(48, 82, 80, 96), 0.2 + 0.7 * np.clip(1 - np.hypot((sp.x - 64) / 18, (sp.y - 92) / 9), 0, 1) + 0.15 * nz(sp, 236, 3.0), FIRE)
    for x in range(51, 79, 5):  # draught slots
        sp.paint(sp.rect(x, 83, x + 2, 95), 0.1, FIRE) if False else None
    sp.paint(sp.rect(48, 88, 80, 90), 0.1, IRON)
    sp.paint(sp.rect(48, 82, 80, 83), 0.1, IRON)
    sp.paint(sp.ellipse(90, 88, 2.4, 2.4), 0.8, IRON)  # latch
    sp.paint(sp.rect(88, 86, 92, 94), 0.8, IRON)
    # the stovepipe: up, an elbow, up again
    sp.paint(sp.rect(88, 20, 100, 60), cyl(sp, 88, 100, 0.5, 0.5, 237), IRON)
    sp.paint(sp.rect(86, 52, 102, 56), 0.75, IRON)
    sp.paint(sp.rect(86, 30, 102, 33), 0.7, IRON)
    sp.paint(sp.rect(88, 2, 100, 22), cyl(sp, 88, 100, 0.45, 0.5, 238), IRON)
    sp.paint(sp.rect(86, 18, 102, 22), 0.75, IRON)
    sp.paint(sp.rect(88, 40, 100, 42), 0.2, IRON)
    sp.paint(sp.rect(90, 24, 91, 50), 0.82, IRON)
    # the kettle on the left of the top plate
    k = sp.ellipse(46, 44, 19, 14) & (sp.y > 30)
    sp.paint(k | sp.rect(30, 44, 62, 58), sphere(sp, 46, 44, 18, 0.6, 0.9) - 0.1 * (sp.y > 54), STEEL)
    sp.paint(sp.rect(30, 54, 62, 58), 0.2, STEEL)
    sp.paint(sp.ellipse(46, 31, 8, 3), 0.7, STEEL)  # lid
    sp.paint(sp.ellipse(46, 28, 3, 3), 0.9, IRON)
    sp.paint(poly(sp, [(26, 38), (14, 28), (16, 26), (30, 36)]), 0.55, STEEL)  # spout
    sp.paint(sp.ellipse(46, 36, 20, 17) & ~sp.ellipse(46, 38, 15, 14) & (sp.y < 36), 0.35, IRON)  # handle arc
    # steam wisps from the spout
    for (x, y, r) in ((11, 24, 3), (8, 18, 3.5), (12, 12, 3.5), (8, 6, 3)):
        v = 0.6 + (nz(sp, 239 + y, 2.0) - 0.5) * 0.3
        b = BAYER8[sp.y.astype(int) % 8, sp.x.astype(int) % 8] + 0.5
        sp.paint(sp.ellipse(x, y, r, r) & (b < 0.8) & (sp.a == 0), v, CANVAS)
    outline(sp)
    glow(sp, 64, 92, 40, FIRE, 2.4, tint=0.3, lo=1)
    return sp.rgba()


# ---- the map table ----------------------------------------------------------------------------------------------------------------------------

def thing_table_maps():
    """A trestle table covered with maps, a lamp and tin mugs."""
    sp = Sprite()
    # trestle legs: two splayed A-frames
    for cx in (26, 102):
        sp.paint(sp.line(cx - 12, 126, cx, 76, 6) | sp.line(cx + 12, 126, cx, 76, 6), 0.45 + 0.1 * nz(sp, 241, 2.0), WOOD)
        sp.paint(sp.rect(cx - 8, 110, cx + 8, 114), 0.5, WOOD)
    # the table top seen from a little above: a front apron and a top plane
    sp.paint(sp.rect(4, 74, 124, 82), bev(sp, 4, 74, 124, 82, 0.5, 0.14, 242, 0.1, 1), WOOD)
    top = poly(sp, [(4, 74), (124, 74), (116, 56), (12, 56)])
    sp.paint(top, 0.5, WOOD)
    # maps spread over it: sheets at angles, coloured contours (no letters)
    sheet1 = poly(sp, [(10, 72), (66, 72), (68, 58), (16, 58)])
    sheet2 = poly(sp, [(56, 73), (118, 72), (112, 58), (62, 58)])
    sp.paint(sheet1, 0.8 + (nz(sp, 243, 4.0) - 0.5) * 0.2, PAPER)
    sp.paint(sheet2, 0.62 + (nz(sp, 244, 4.0) - 0.5) * 0.2, PAPER)
    for (nzs, pal_c, m) in ((245, TARP, sheet1), (246, DUST, sheet2)):
        v = nz(sp, nzs, 6.0, 3)
        contour = (np.abs((v * 9) % 1.0 - 0.5) < 0.09) & m
        sp.paint(contour, 0.45, pal_c)
    # a blue coastline (sea) and a red route line
    v = nz(sp, 247, 7.0)
    sp.paint(sheet1 & (v < 0.38), 0.82, GLASS)
    sp.paint(sp.line(18, 69, 62, 60, 1.3), 0.65, REDP)
    sp.paint(sp.line(70, 62, 108, 70, 1.3), 0.5, REDP)
    # lamp: a brass hurricane lamp with a lit glass
    sp.paint(sp.rect(14, 38, 30, 58), cyl(sp, 14, 30, 0.5, 0.5), BRASS)
    sp.paint(sp.rect(16, 18, 28, 40), cyl(sp, 16, 28, 0.9, 0.4), BULB)
    sp.paint(sp.rect(20, 24, 24, 38), 1.0, BULB)
    sp.paint(sp.rect(15, 14, 29, 19), cyl(sp, 15, 29, 0.55, 0.5), BRASS)
    sp.paint(sp.ellipse(22, 12, 4, 3), 0.8, BRASS)
    # tin mugs
    for (mx, my) in ((70, 56), (94, 58)):
        sp.paint(sp.rect(mx, my - 14, mx + 14, my + 2), cyl(sp, mx, mx + 14, 0.65, 0.5, 248 + mx), STEEL)
        sp.paint(sp.rect(mx, my - 14, mx + 14, my - 12), 0.95, STEEL)
        sp.paint(sp.ellipse(mx + 7, my - 14, 7, 2), 0.2, IRON)
        sp.paint(sp.ellipse(mx + 15, my - 7, 4, 5) & ~sp.ellipse(mx + 15, my - 7, 2, 3), 0.55, STEEL)
    # a pencil and compass on the map
    sp.paint(sp.line(46, 64, 58, 61, 1.5), 0.75, DUST)
    outline(sp)
    glow(sp, 22, 30, 38, BULB, 2.0, tint=0.5)
    return sp.rgba()


# ---- the hospital tent door --------------------------------------------------------------------------------------------------------------------

def thing_tent_flap():
    """A tent doorway: canvas flaps tied back round a dark interior, a grey cross painted on a sheet hanging beside."""
    sp = Sprite()
    # the tent's front: a tall gable of canvas with its peak at the top
    gable = poly(sp, [(4, 126), (4, 56), (44, 4), (84, 56), (84, 126)])
    sp.paint(gable, 0.62 - 0.35 * np.clip((sp.x - 4) / 80, 0, 1) + (nz(sp, 261, 3.0) - 0.5) * 0.25 + 0.05 * ((sp.y // 2) % 2), CANVAS)
    for xx in (22, 64):  # seams
        sp.paint(gable & (np.abs(sp.x - xx) < 0.8), 0.22, CANVAS)
    # the doorway: dark inside, a cot edge glimpsed
    door = poly(sp, [(22, 126), (22, 62), (44, 32), (66, 62), (66, 126)])
    sp.paint(door, 0.03 + 0.1 * nz(sp, 262, 4.0) + 0.1 * np.clip((sp.y - 90) / 36, 0, 1), GREENLIT)
    sp.paint(sp.rect(30, 98, 58, 102) & door, 0.22, DUST)
    sp.paint(sp.rect(32, 102, 34, 120) & door, 0.1, GREENLIT)
    sp.paint(sp.rect(54, 102, 56, 120) & door, 0.1, GREENLIT)
    # the flaps, tied back: gathered canvas wedges at each side, bunched with a rope
    left = poly(sp, [(22, 126), (22, 62), (44, 32), (36, 62), (31, 96), (34, 126)])
    right = poly(sp, [(66, 126), (66, 62), (44, 32), (52, 62), (57, 96), (54, 126)])
    u = np.clip((sp.x - 22) / 14, 0, 1)
    sp.paint(left, 0.88 - 0.35 * u + 0.12 * np.sin(sp.x * 1.3) + (nz(sp, 263, 3.0) - 0.5) * 0.2, CANVAS)
    u2 = np.clip((sp.x - 54) / 12, 0, 1)
    sp.paint(right, 0.55 - 0.3 * u2 + 0.1 * np.sin(sp.x * 1.3) + (nz(sp, 264, 3.0) - 0.5) * 0.2, CANVAS)
    sp.paint(sp.rect(20, 90, 36, 95), 0.3, DUST)  # ties
    sp.paint(sp.rect(52, 90, 68, 95), 0.25, DUST)
    sp.paint(sp.rect(21, 95, 24, 104), 0.3, DUST)
    sp.paint(sp.rect(64, 95, 67, 104), 0.25, DUST)
    # a guy rope and the ridge pole's end
    sp.paint(sp.line(84, 58, 96, 126, 1.4), 0.5, DUST)
    sp.paint(sp.rect(42, 2, 47, 10), 0.55, WOOD)
    # the sheet hanging on a washing line from the tent to a post: an uneven grey-white sheet
    sp.paint(sp.line(84, 46, 103, 52, 1.3) | sp.line(103, 52, 122, 46, 1.3), 0.45, DUST)
    sp.paint(sp.rect(121, 42, 125, 126), 0.45 + 0.1 * (sp.x < 123), WOOD)
    sheet = poly(sp, [(90, 47), (120, 47), (120, 102), (112, 106), (102, 104), (94, 107), (90, 103)])
    sp.paint(sheet, 0.6 - 0.16 * np.clip((sp.x - 92) / 27, 0, 1) + 0.1 * np.sin(sp.x * 0.9) + (nz(sp, 265, 3.0) - 0.5) * 0.2, SKYW)
    for fx in (100, 108):
        sp.paint(sheet & (np.abs(sp.x - fx) < 0.7), 0.3, SKYW)
    # the cross, painted in grey: plain, with uneven edges
    cross = sp.rect(101, 58, 109, 96) | sp.rect(94, 68, 116, 76)
    sp.paint(cross & (nz(sp, 266, 1.5) > 0.12), 0.35 + (nz(sp, 267, 2.0) - 0.5) * 0.3, CANVAS)
    # pegs
    for px, py in ((94, 42), (104, 44), (114, 42)):
        sp.paint(sp.rect(px, py + 2, px + 2, py + 6), 0.55, WOOD)
    outline(sp)
    return sp.rgba()


# ---- the canvas truck -------------------------------------------------------------------------------------------------------------------------

def thing_truck():
    """An olive canvas-backed truck, three-quarter front, engine running; a tarp over crates, a driver's elbow out of the cab, an exhaust puff."""
    sp = Wide()
    # wheels first (behind the body)
    def wheel(cx, cy, rx, ry, seed):
        sp.paint(sp.ellipse(cx, cy, rx, ry), 0.18 + (nz(sp, seed, 2.0) - 0.5) * 0.2 + 0.0 * sp.x, IRON)
        sp.paint(sp.ellipse(cx, cy, rx, ry) & ~sp.ellipse(cx, cy, rx - 2.5, ry - 2.5), 0.38, IRON)
        sp.paint(sp.ellipse(cx, cy, rx * 0.45, ry * 0.45), 0.5, OLIVE)
        sp.paint(sp.ellipse(cx, cy, rx * 0.18, ry * 0.18), 0.2, IRON)
    wheel(206, 105, 15, 19, 301)
    wheel(180, 107, 14, 17, 302)
    # the cargo body: drop sides, then the tarp over crates
    sp.paint(poly(sp, [(150, 70), (238, 66), (238, 100), (150, 104)]), 0.32 + (nz(sp, 303, 3.0) - 0.5) * 0.25 + 0.0, OLIVE)
    for xx in range(158, 238, 18):
        sp.paint(sp.rect(xx, 68, xx + 1, 102), 0.12, OLIVE)
    sp.paint(poly(sp, [(150, 70), (238, 66), (238, 70), (150, 74)]), 0.7, OLIVE)
    # crates showing at the open back
    for (cx0, cy0, w, h, seed) in ((214, 44, 24, 24, 304), (218, 22, 20, 22, 305)):
        sp.paint(sp.rect(cx0, cy0, cx0 + w, cy0 + h), bev(sp, cx0, cy0, cx0 + w, cy0 + h, 0.52, 0.18, seed, 0.14), WOOD)
        sp.paint(sp.rect(cx0, cy0 + h // 2, cx0 + w, cy0 + h // 2 + 1), 0.12, WOOD)
        sp.paint(sp.line(cx0 + 1, cy0 + 1, cx0 + w - 1, cy0 + h - 1, 1.6), 0.35, WOOD)
    # the tarp: a bowed canvas hood over the front two thirds, hoops showing, ropes
    tarp = poly(sp, [(150, 70), (152, 34), (160, 24), (178, 18), (198, 20), (212, 30), (218, 44), (220, 68), (212, 70), (200, 71)])
    sh = 0.62 - 0.4 * np.clip((sp.x - 150) / 90, 0, 1) + 0.18 * np.clip(1 - (sp.y - 18) / 20, 0, 1) + (nz(sp, 307, 4.0, 3) - 0.5) * 0.3
    sp.paint(tarp, sh, TARP)
    for hx in (166, 186, 204):  # hoops: darker ribs under the cloth
        sp.paint(tarp & (np.abs(sp.x - hx) < 1.2) , sh - 0.25, TARP)
    for fx, fy in ((176, 40), (198, 52), (214, 36)):  # folds
        sp.paint(tarp & (np.abs(sp.x - fx - (sp.y - fy) * 0.4) < 0.9) & (np.abs(sp.y - fy) < 16), sh - 0.22, TARP)
    sp.paint(tarp & (sp.y > 62), sh - 0.15, TARP)  # the tarp's skirt, shaded
    for xx in (170, 198):  # lashing ropes
        sp.paint(sp.rect(xx, 40, xx + 2, 70), 0.55, KHAKI)
    sp.paint(sp.rect(150, 66, 220, 69), 0.18, TARP)
    # the cab: roof, the side with a window, the hood
    cab = poly(sp, [(90, 104), (90, 24), (146, 24), (152, 34), (152, 104)])
    sp.paint(cab, bev(sp, 90, 24, 152, 104, 0.42, 0.14, 308, 0.12), OLIVE)
    sp.paint(poly(sp, [(90, 24), (146, 24), (150, 30), (90, 30)]), 0.78, OLIVE)  # roof
    win = poly(sp, [(108, 36), (140, 36), (142, 62), (108, 62)])
    sp.paint(win, 0.25 + 0.35 * np.clip(1 - (sp.x - 108) / 30, 0, 1) * np.clip(1 - (sp.y - 36) / 24, 0, 1), GLASS)
    sp.paint(poly(sp, [(110, 38), (118, 38), (112, 62), (108, 62)]) & win, 0.85, GLASS)
    # the driver: a dark hat shape, a face glimpse, and an elbow out of the window
    sp.paint(sp.ellipse(124, 50, 7, 8), 0.3, SKIN)
    sp.paint(sp.rect(116, 40, 133, 46), 0.4, OLIVE)
    sp.paint(sp.line(132, 62, 150, 54, 6), 0.45, OLIVE)  # sleeve out of the window
    sp.paint(sp.ellipse(150, 56, 4.5, 4.5), 0.6, SKIN)  # the elbow
    sp.paint(sp.rect(140, 59, 152, 63), 0.3, OLIVE)
    sp.paint(sp.rect(106, 66, 146, 69), 0.18, OLIVE)  # door line
    sp.paint(sp.rect(106, 64, 114, 66), 0.9, STEEL)
    sp.paint(sp.rect(136, 70, 148, 72), 0.8, STEEL)  # door handle
    # the front face: hood and grille, fenders, lamps, bumper
    hood = poly(sp, [(10, 104), (10, 66), (18, 56), (96, 56), (102, 66), (102, 104)])
    sp.paint(hood, bev(sp, 10, 56, 102, 104, 0.5, 0.14, 309, 0.1), OLIVE)
    sp.paint(poly(sp, [(18, 56), (96, 56), (102, 66), (10, 66)]), 0.82, OLIVE)  # hood top catching the sun
    sp.paint(poly(sp, [(26, 26), (92, 26), (96, 58), (22, 58)]) & ~sp.rect(0, 0, 0, 0), 0.0, OLIVE) if False else None
    cabf = poly(sp, [(28, 58), (30, 30), (36, 24), (86, 24), (92, 30), (94, 58)])
    sp.paint(cabf, bev(sp, 28, 24, 94, 58, 0.5, 0.16, 310, 0.1), OLIVE)
    # windscreen (two panes) with a hot glare
    for (x0, x1) in ((34, 59), (63, 88)):
        pane = poly(sp, [(x0, 54), (x0 + 1, 33), (x1 - 1, 33), (x1, 54)])
        sp.paint(pane, 0.22 + 0.4 * np.clip(1 - ((sp.x - x0) + (sp.y - 33)) / 40, 0, 1), GLASS)
        sp.paint(pane & (np.abs((sp.x - x0) - (sp.y - 33) * 0.6 - 6) < 1.3), 0.95, GLASS)
    sp.paint(sp.rect(58, 33, 64, 55), 0.35, OLIVE)
    # grille: a dark block with slats
    sp.paint(sp.rect(38, 68, 80, 98), 0.07, IRON)
    for yy in range(70, 97, 4):
        sp.paint(sp.rect(40, yy, 78, yy + 2), 0.35 + 0.0 * sp.x, IRON)
    sp.paint(sp.rect(38, 68, 80, 70), 0.55, STEEL)
    sp.paint(sp.rect(38, 68, 40, 98), 0.55, STEEL)
    sp.paint(sp.rect(58, 68, 60, 98), 0.4, STEEL)
    # headlamps
    for lx in (24, 94):
        sp.paint(sp.ellipse(lx, 78, 8, 8), 0.3, STEEL)
        sp.paint(sp.ellipse(lx, 78, 6, 6), 0.7 - 0.3 * (sp.x > lx), BULB)
        sp.paint(sp.ellipse(lx - 2, 76, 2, 2), 1.0, BULB)
    # bumper and a starting-handle stub
    sp.paint(sp.rect(4, 100, 108, 110), bev(sp, 4, 100, 108, 110, 0.55, 0.22, 311, 0.1, 1), STEEL)
    sp.paint(sp.rect(52, 104, 58, 112), 0.25, IRON)
    sp.paint(sp.line(56, 106, 62, 118, 2), 0.4, IRON)
    # front wheels: the near one at the front's right edge and a sliver of the far one on the left
    wheel(116, 106, 13, 19, 312)
    sp.paint(sp.ellipse(7, 101, 6, 17), cyl(sp, 1, 13, 0.25, 0.3, 313), IRON)
    # a mudguard over the near wheel
    sp.paint(poly(sp, [(98, 90), (104, 74), (130, 74), (134, 90)]) & ~sp.ellipse(116, 106, 13, 19), 0.55, OLIVE)
    sp.paint(sp.ellipse(116, 90, 20, 12) & (sp.y < 92) & (sp.y > 84), 0.7, OLIVE)
    # the dust at the tyres
    for (x, y) in ((100, 124), (104, 125), (122, 126), (172, 124), (196, 126), (230, 124)):
        sp.paint(sp.rect(x, y, x + 6, y + 2), 0.55, DUST)
    sp.paint(sp.rect(98, 122, 238, 126), 0.5 + (nz(sp, 314, 3.0)[122:126, 98:238].mean() * 0) , DUST) if False else None
    outline(sp)
    # exhaust: a pipe under the tail and a pale puff drifting up and back
    sp.paint(sp.rect(238, 100, 244, 114), 0.4, IRON)
    rng = np.random.RandomState(315)
    for (px, py, r) in ((242, 96, 4), (246, 88, 6), (243, 78, 7), (247, 68, 6), (243, 60, 4)):
        puff = sp.ellipse(px, py, r, r)
        v = (0.7 - 0.12 * ((sp.x - px) + (sp.y - py)) / r) + (nz(sp, 316 + px, 2.0) - 0.5) * 0.3
        b = BAYER8[sp.y.astype(int) % 8, sp.x.astype(int) % 8] + 0.5
        keep = puff & (b < 1.0)
        sp.paint(keep & (sp.a == 0), v, CANVAS)
    return sp.rgba()


# ---- the hut window ---------------------------------------------------------------------------------------------------------------------------

def thing_window_hut():
    """A small square hut window: white-hot sky behind taped glass, a half-drawn curtain."""
    sp = Sprite()
    frame = sp.rect(10, 12, 118, 116)
    sp.paint(frame, bev(sp, 10, 12, 118, 116, 0.5, 0.18, 321, 0.12, 3), WOOD)
    sp.paint(sp.rect(4, 112, 124, 122), bev(sp, 4, 112, 124, 122, 0.62, 0.2, 322, 0.1, 2), WOOD)  # sill
    sp.paint(sp.rect(6, 120, 122, 125), 0.2, WOOD)
    glass = sp.rect(20, 22, 108, 108)
    # the white-hot sky with a heat haze
    sp.paint(glass, 0.82 + (nz(sp, 323, 6.0) - 0.5) * 0.3 - 0.0 * sp.y + 0.12 * np.clip((60 - sp.y) / 40, 0, 1), SKYW)
    sp.paint(sp.ellipse(84, 44, 14, 14), 1.0, SKYW)
    # mullion cross
    sp.paint(sp.rect(62, 22, 66, 108) | sp.rect(20, 62, 108, 66), bev(sp, 20, 22, 108, 108, 0.52, 0.0, 324, 0.12) + 0.0, WOOD)
    sp.paint(sp.rect(62, 22, 63, 108) | sp.rect(20, 62, 108, 63), 0.9, WOOD)
    # blast tape: two diagonals plus an edge strip on each pane
    for (a, b, c, d) in ((20, 22, 62, 62), (66, 22, 108, 62), (20, 66, 62, 108), (66, 66, 108, 108), (62, 22, 20, 62), (108, 22, 66, 62)):
        sp.paint(sp.line(a, b, c, d, 3) & glass, 0.65 + 0.0 * sp.x, PAPER)
    # cracks
    sp.paint(sp.line(70, 80, 88, 96, 1) | sp.line(88, 96, 100, 94, 1), 0.3, SKYW)
    # the curtain: half drawn on the left, pleated, faded dust-orange
    cur = poly(sp, [(20, 22), (66, 22), (62, 40), (54, 66), (46, 90), (34, 108), (20, 108)])
    sp.paint(cur, 0.6 + 0.2 * np.sin(sp.x * 0.7) + (nz(sp, 325, 3.0) - 0.5) * 0.3, DUST)
    sp.paint(sp.rect(16, 18, 70, 23), 0.3, IRON)  # curtain rail
    for ring in range(22, 68, 8):
        sp.paint(sp.rect(ring, 22, ring + 2, 26), 0.8, IRON)
    outline(sp)
    return sp.rgba()


# ---- the office window ------------------------------------------------------------------------------------------------------------------------

def thing_window_office():
    """A tall office window with a venetian blind half drawn, white sun slats across it."""
    sp = Sprite()
    sp.paint(sp.rect(22, 2, 106, 124), bev(sp, 22, 2, 106, 124, 0.52, 0.18, 331, 0.12, 3), WOOD)
    sp.paint(sp.rect(16, 120, 112, 127), bev(sp, 16, 120, 112, 127, 0.62, 0.2, 332, 0.08, 2), WOOD)
    glass = sp.rect(30, 10, 98, 116)
    sp.paint(glass, 0.85 + (nz(sp, 333, 6.0) - 0.5) * 0.2, SKYW)
    # a transom bar and a centre mullion
    sp.paint(sp.rect(30, 56, 98, 59), bev(sp, 30, 56, 98, 59, 0.55, 0.2, 334, 0.1, 1), WOOD)
    # the blind, drawn down to y=68 with its slats tilted, a headrail on top, cords
    sp.paint(sp.rect(28, 8, 100, 14), bev(sp, 28, 8, 100, 14, 0.5, 0.2, 335, 0.06, 1), STEEL)
    for y in range(14, 70, 5):
        sp.paint(sp.rect(30, y, 98, y + 4), 0.35 + 0.0 * sp.x, KHAKI)
        sp.paint(sp.rect(30, y, 98, y + 1), 0.9, KHAKI)
        sp.paint(sp.rect(30, y + 3, 98, y + 4), 0.18, KHAKI)
        # white hot sun between slats
        sp.paint(sp.rect(30, y + 4, 98, y + 5) & (sp.y < 68), 1.0, SKYW)
    sp.paint(sp.rect(30, 66, 98, 70), 0.55, STEEL)  # the bottom rail
    for x in (44, 84):
        sp.paint(sp.rect(x, 14, x + 1, 66), 0.4, DUST)  # ladder tapes
    sp.paint(sp.rect(92, 70, 93, 98), 0.3, KHAKI)  # pull cord
    sp.paint(sp.ellipse(92.5, 99, 2, 3), 0.7, KHAKI)
    # the glare: sun-bleached bloom in the open lower pane, with a street shape outside
    sp.paint(glass & (sp.y > 74) & (nz(sp, 336, 5.0) > 0.72) & (sp.y < 100), 0.65, SKYW)
    sp.paint(sp.rect(30, 92, 98, 100) & glass, 0.55 + (nz(sp, 337, 4.0) - 0.5) * 0.3, SKYW)  # a far wall
    sp.paint(sp.rect(30, 90, 98, 92) & glass, 0.3, SKYW)
    # sun streaks on the sill
    sp.paint(sp.rect(16, 120, 112, 122), 0.9, WOOD)
    outline(sp)
    return sp.rgba()


# ---- the windsock -----------------------------------------------------------------------------------------------------------------------------

def thing_windsock():
    """A limp windsock on a tall pole, orange and white bands."""
    sp = Sprite()
    # the pole with a footing and braces
    sp.paint(sp.rect(36, 6, 42, 120), cyl(sp, 36, 42, 0.6, 0.55, 351), STEEL)
    sp.paint(sp.rect(33, 116, 45, 124), bev(sp, 33, 116, 45, 124, 0.5, 0.16, 352), STEEL)
    sp.paint(sp.line(39, 78, 14, 120, 2.5) | sp.line(39, 78, 64, 120, 2.5), 0.4, STEEL)
    sp.paint(sp.rect(8, 120, 70, 127), bev(sp, 8, 120, 70, 127, 0.45, 0.16, 353), WOOD)
    sp.paint(sp.rect(12, 122, 18, 127) | sp.rect(58, 122, 64, 127), 0.35, WOOD)
    # the swivel arm and the ring at the top
    sp.paint(sp.rect(38, 14, 58, 19), 0.55, STEEL)
    ring = sp.ellipse(62, 24, 14, 11) & ~sp.ellipse(62, 24, 11, 8)
    sp.paint(ring, cyl(sp, 48, 76, 0.62, 0.5), STEEL)
    sp.paint(sp.ellipse(39, 7, 4, 4), sphere(sp, 39, 7, 4, 0.7, 0.8), STEEL)
    # the limp sock: it hangs from the ring, narrowing, with a slight S bend; nine bands
    segs = 9
    for k in range(segs):
        t0, t1 = k / segs, (k + 1) / segs
        y0, y1 = 30 + 78 * t0, 30 + 78 * t1
        cx_at = lambda t: 62 + 6 * np.sin(t * 3.4)
        hw_at = lambda t: 15 - 9.0 * t
        xa0, xa1, w0, w1 = cx_at(t0), cx_at(t1), hw_at(t0), hw_at(t1)
        band = poly(sp, [(xa0 - w0, y0), (xa0 + w0, y0), (xa1 + w1, y1 + 0.6), (xa1 - w1, y1 + 0.6)])
        orange = (k % 2 == 0)
        u = np.clip((sp.x - (xa0 - w0)) / max(2 * w0, 1), 0, 1)
        sh = (0.62 if orange else 0.84) - 0.4 * u + (nz(sp, 360 + k, 2.0) - 0.5) * 0.2
        sp.paint(band, sh, DUST if orange else SKYW)
        sp.paint(band & (sp.y < y0 + 1), 0.22 if orange else 0.45, DUST if orange else SKYW)
    # the open mouth, seen as a thin dark lip under the ring
    sp.paint(sp.ellipse(62, 30, 15, 3), 0.1, IRON)
    sp.paint(sp.ellipse(62, 29, 14, 1.8), 0.55, DUST)
    outline(sp)
    return sp.rgba()


DRAW = {
    "thing_ladder": thing_ladder,
    "thing_lamp_hang": thing_lamp_hang,
    "thing_lamp_red": thing_lamp_red,
    "thing_ledger": thing_ledger,
    "thing_nose_glass": thing_nose_glass,
    "thing_release_lever": thing_release_lever,
    "thing_sandbags": thing_sandbags,
    "thing_scales": thing_scales,
    "thing_screen_cloth": thing_screen_cloth,
    "thing_shelves_tins": thing_shelves_tins,
    "thing_sign_ledgerless": thing_sign_ledgerless,
    "thing_stamp_big": thing_stamp_big,
    "thing_stove": thing_stove,
    "thing_table_maps": thing_table_maps,
    "thing_tent_flap": thing_tent_flap,
    "thing_truck": thing_truck,
    "thing_window_hut": thing_window_hut,
    "thing_window_office": thing_window_office,
    "thing_windsock": thing_windsock,
}
