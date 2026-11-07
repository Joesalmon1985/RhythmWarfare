"""Seamless pixel textures and sky strips for the Gospel adventure (the Life of Jesus): sunlit, dusty and warm, in the pixel look of pixeltex.

`build(out_dir)` writes every tile as an opaque RGB PNG into out_dir and returns {name: {"size": [w, h], "metres": float}}. Floors repeat in both directions;
walls repeat horizontally and run top to bottom over their `metres` (StoryWorld maps v = 0 to the TOP of a wall, so skirting and bases sit at the bottom of the
tile and shadows under cornices at the top). Everything is painted as DAYLIGHT mid-tones (no pure black, no pure white): the engine multiplies each room's light
colour over it, so a night room goes indigo and a dusk room orange. Skies are 256 x 64, seamless left to right, zenith at the top and the horizon at about row 44.
Nothing here is copied from any picture; every random value comes from a seeded generator, so the same code gives the same bytes.
"""
from __future__ import annotations

import os
import sys

import numpy as np

try:
    from . import pixeltex as px
except ImportError:  # run as a script
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pixeltex as px

R = px.ramp
BAYER = px.BAYER8


def SB(ramp, k=1.22, g=1.0):
    """Sunlit colour: boost a ramp's saturation (k) and exposure (g) about its own luminance (the daylight rooms must read as warm sun, not grey haze)."""
    lum = (ramp * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
    return np.clip((lum + (ramp - lum) * k) * g, 0, 1).astype(np.float32)


# ---- small kit -------------------------------------------------------------------------------------------------------------------------------------------

def hexu(h: str) -> np.ndarray:
    return (px.hexc(h) * 255 + 0.5).astype(np.uint8)


def G(w: int, h: int | None = None):
    h = w if h is None else h
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return x, y


def pn(w: int, h: int, sx: float, sy: float, seed: int, octaves: int = 3, c: float = 1.0) -> np.ndarray:
    """Periodic value noise 0..1 on a w x h canvas, feature size sx x sy pixels, contrast c about 0.5."""
    rng = np.random.RandomState(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    for o in range(octaves):
        cx = max(1, int(round(w / sx * 2 ** o)))
        cy = max(1, int(round(h / sy * 2 ** o)))
        g = rng.rand(cy, cx).astype(np.float32)
        fx, fy = x / w * cx, y / h * cy
        x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
        tx, ty = fx - x0, fy - y0
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        x0, y0 = x0 % cx, y0 % cy
        x1, y1 = (x0 + 1) % cx, (y0 + 1) % cy
        v = (g[y0, x0] * (1 - tx) + g[y0, x1] * tx) * (1 - ty) + (g[y1, x0] * (1 - tx) + g[y1, x1] * tx) * ty
        out += v * amp
        tot += amp
        amp *= 0.5
    out /= tot
    return np.clip((out - 0.5) * c + 0.5, 0, 1).astype(np.float32)


def Q(shade, pal: np.ndarray, dither: float = 1.0) -> np.ndarray:
    return px.quantise(np.asarray(shade, np.float32), pal, dither)


def qloc(shade, pal: np.ndarray, ys: np.ndarray, xs: np.ndarray, dither: float = 1.0) -> np.ndarray:
    """Quantise with the Bayer cell of the GLOBAL pixel coordinates (ys, xs index arrays), for window drawing."""
    b = BAYER[ys[:, None] % 8, xs[None, :] % 8]
    k = len(pal) - 1
    i = np.clip(np.round(np.clip(shade, 0, 1) * k + b * dither), 0, k).astype(int)
    return (pal[i] * 255 + 0.5).astype(np.uint8)


def put(img: np.ndarray, mask, layer) -> np.ndarray:
    m = np.asarray(mask, bool)
    if isinstance(layer, str):
        img[m] = hexu(layer)
    elif layer.ndim == 1:
        img[m] = layer
    else:
        img[m] = layer[m]
    return img


def speck(n: int, density: float, seed: int, h: int | None = None) -> np.ndarray:
    h = n if h is None else h
    return np.random.RandomState(seed).rand(h, n) < density


def smooth(a, lo, hi):
    t = np.clip((a - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def wrapd(a, b, n):
    return (a - b + n / 2.0) % n - n / 2.0


def blob(img, cx, cy, rx, ry, ang, shade_fn, pal, shadow: float = 0.0, sdx: float = 1.0, sdy: float = 1.0) -> None:
    """Draw a shaded ellipse (rotated by ang) into img with wrap-around, with an optional cast shadow offset (sdx, sdy)."""
    h, w = img.shape[:2]
    rr = int(max(rx, ry)) + 3
    xs = np.arange(int(np.floor(cx)) - rr, int(np.floor(cx)) + rr + 1)
    ys = np.arange(int(np.floor(cy)) - rr, int(np.floor(cy)) + rr + 1)
    dx = (xs - cx)[None, :] + 0 * ys[:, None]
    dy = (ys - cy)[:, None] + 0 * xs[None, :]
    ca, sa = np.cos(ang), np.sin(ang)
    u, v = (dx * ca + dy * sa) / rx, (-dx * sa + dy * ca) / ry
    body = u * u + v * v <= 1
    ix = np.ix_(ys % h, xs % w)
    sub = img[ix].copy()
    if shadow > 0:
        ux, vx = ((dx - sdx) * ca + (dy - sdy) * sa) / rx, (-(dx - sdx) * sa + (dy - sdy) * ca) / ry
        sm = (ux * ux + vx * vx <= 1) & ~body
        sub[sm] = (sub[sm].astype(np.float32) * (1 - shadow)).astype(np.uint8)
    sub = np.where(body[..., None], qloc(shade_fn(u, v), pal, ys % h, xs % w), sub)
    img[ix] = sub


def dome(tone: float, k: float = 0.3):
    """A lit-from-the-upper-left dome shading for blob()."""
    return lambda u, v: tone - k * (u + v) * 0.7 - 0.18 * (u * u + v * v)


def line(img, x0, y0, x1, y1, col) -> None:
    """A 1 px line with wrap-around; col is a uint8 triple or an array of triples, one per step."""
    h, w = img.shape[:2]
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    t = np.linspace(0, 1, steps + 1)
    xs = np.round(x0 + (x1 - x0) * t).astype(int) % w
    ys = np.round(y0 + (y1 - y0) * t).astype(int) % h
    img[ys, xs] = col


def pix(img, x, y, col) -> None:
    img[int(y) % img.shape[0], int(x) % img.shape[1]] = col


def voronoi(n: int, cells: int, seed: int, jitter: float = 0.9) -> dict:
    """Periodic Voronoi: distance to the nearest (f1) and second nearest (f2) point, the nearest id and the vector to it."""
    rng = np.random.RandomState(seed)
    gx = (np.arange(cells)[None, :] + 0.5 + (rng.rand(cells, cells) - 0.5) * jitter) * n / cells
    gy = (np.arange(cells)[:, None] + 0.5 + (rng.rand(cells, cells) - 0.5) * jitter) * n / cells
    X, Y = G(n)
    b1 = np.full((n, n), 1e9, np.float32)
    b2 = np.full((n, n), 1e9, np.float32)
    idx = np.zeros((n, n), int)
    bdx = np.zeros((n, n), np.float32)
    bdy = np.zeros((n, n), np.float32)
    for k, (qx, qy) in enumerate(zip(gx.ravel(), gy.ravel())):
        dx, dy = wrapd(X, qx, n), wrapd(Y, qy, n)
        d = np.sqrt(dx * dx + dy * dy)
        m1 = d < b1
        b2 = np.where(m1, b1, np.minimum(b2, d))
        idx = np.where(m1, k, idx)
        bdx = np.where(m1, dx, bdx)
        bdy = np.where(m1, dy, bdy)
        b1 = np.where(m1, d, b1)
    return {"f1": b1, "f2": b2, "id": idx, "dx": bdx, "dy": bdy, "rnd": rng.rand(cells * cells).astype(np.float32)}


def courses(n: int, rows, seed: int, wmean: float, wjit: float = 0.3, hjit: float = 0.0, stagger: bool = True) -> dict:
    """Masonry courses tiling horizontally: per-pixel block id, local x/y, block width/height and a tone per block. rows is a count or a list of heights."""
    rng = np.random.RandomState(seed)
    if isinstance(rows, (list, tuple)):
        ys = np.concatenate([[0], np.cumsum(rows)]).astype(int)
        ys[-1] = n
    else:
        hs = 1 + (rng.rand(rows) - 0.5) * 2 * hjit
        ys = np.round(np.concatenate([[0], np.cumsum(hs / hs.sum() * n)])).astype(int)
    out = {k: np.zeros((n, n), np.float32) for k in ("lx", "ly", "bw", "bh", "tone")}
    out["bid"] = np.zeros((n, n), int)
    bi = 0
    for r in range(len(ys) - 1):
        y0, y1 = ys[r], ys[r + 1]
        k = max(1, int(round(n / wmean)))
        ws = 1 + (rng.rand(k) - 0.5) * 2 * wjit
        ed = np.round(np.concatenate([[0], np.cumsum(ws / ws.sum() * n)])).astype(int)
        ed[-1] = n
        off = int(rng.randint(0, n)) if stagger else 0
        xs = (np.arange(n) - off) % n
        i = np.searchsorted(ed, xs, "right") - 1
        tn = rng.rand(k).astype(np.float32)[i]
        out["lx"][y0:y1, :] = (xs - ed[i])[None, :]
        out["bw"][y0:y1, :] = (ed[i + 1] - ed[i])[None, :]
        out["tone"][y0:y1, :] = tn[None, :]
        out["ly"][y0:y1, :] = (np.arange(y0, y1) - y0)[:, None]
        out["bh"][y0:y1, :] = y1 - y0
        out["bid"][y0:y1, :] = (bi + i)[None, :]
        bi += k
    return out


def masonry(n: int, rows, seed: int, wmean: float, pal, jpal, tone: float = 0.16, wjit: float = 0.3, hjit: float = 0.0, joint: int = 1,
            wear: float = 0.5, extra=None, bevel: float = 0.13, scale: float = 9, stagger: bool = True):
    """Dressed blocks with a lit top/left lip, a shaded bottom/right edge, chips and mottle: (rgb, courses, joint mask, shade)."""
    c = courses(n, rows, seed, wmean, wjit, hjit, stagger)
    sh = 0.52 + (c["tone"] - 0.5) * 2 * tone + (pn(n, n, scale, scale, seed + 1, 3) - 0.5) * 0.5 * wear
    sh -= 0.17 * (pn(n, n, 3, 3, seed + 2, 2) > 0.74) * wear * 1.6
    lip = ((c["ly"] >= joint) & (c["ly"] < joint + 1)) | ((c["lx"] >= joint) & (c["lx"] < joint + 1))
    low = (c["ly"] >= c["bh"] - 1) | (c["lx"] >= c["bw"] - 1)
    sh = sh + bevel * lip - bevel * low
    if extra is not None:
        sh = sh + extra
    img = Q(sh, pal)
    mort = (c["ly"] < joint) | (c["lx"] < joint)
    jsh = 0.5 + (pn(n, n, 5, 5, seed + 3, 2) - 0.5) * 0.8 + (0 if extra is None else extra * 0.6)
    img[mort] = Q(jsh, jpal)[mort]
    return img, c, mort, sh


def cracks(n: int, seed: int, sx: float = 14, sy: float = 14, width: float = 0.014, h: int | None = None) -> np.ndarray:
    v = pn(n, n if h is None else h, sx, sy, seed, 3)
    return np.abs(v - 0.5) < width


# ---- palettes (dark to light; daylight mid-tones) ---------------------------------------------------------------------------------------------------------

SAND = R("#a89570", "#bba67f", "#cdb98f", "#dccaa0", "#e8dab4")
SAND = SB(SAND)
DUST = R("#8e6538", "#a47940", "#b98e4f", "#cca262", "#dcb678")
DUST = SB(DUST)
PATHP = R("#a99575", "#b9a583", "#c9b794", "#d7c8a6", "#e3d6b8")
PATHP = SB(PATHP)
GRASS = R("#646230", "#7a7838", "#908c40", "#a69e4e", "#bcb264")
GRASS = SB(GRASS)
GARDEN = R("#566a30", "#687c3a", "#7a9048", "#8ea25a", "#a2b46c")
GARDEN = SB(GARDEN)
SHING = R("#5a5148", "#6e6458", "#827766", "#968b76", "#aa9f88")
WATER = R("#486e8a", "#5a809c", "#7096b0", "#8cb0c6", "#aac8da")
COBB = R("#9a8668", "#ae9a79", "#c1ad8b", "#d1be9d", "#e0cfae")
COBB = SB(COBB)
COBBJ = R("#5e5038", "#6e5e46", "#806e54")
FLAG = R("#aa9f86", "#b9ae94", "#c6bba2", "#d3c9af", "#ddd4bb")
FLAG = SB(FLAG)
FLAGJ = R("#7c705a", "#8c8068", "#9c9078")
PLANK = R("#6a5640", "#7e6a50", "#927d62", "#a89478", "#bca98c")
PLANKJ = R("#3e3224", "#4c3e2e", "#5c4c3a")
CLAY = R("#a86a40", "#bc7c4a", "#cc8e58", "#da9f69", "#e6b27e")
CLAY = SB(CLAY)
CLAYT = R("#b8825a", "#c99468", "#d8a778", "#e4b98c")
SOIL = R("#4a3a28", "#5a4832", "#6c593e", "#806a4a", "#947c58")
SOIL = SB(SOIL)
LEAF = R("#7a5a2c", "#92702e", "#a88838", "#7c7a38", "#98963f")
ROCK = R("#6e665a", "#827a6c", "#968c7a", "#aa9f8a", "#bdb29b")
ROCK = SB(ROCK)
ROCKO = R("#7c6a4a", "#92805a", "#a8946a", "#bca67c", "#cdb98e")
ROCKO = SB(ROCKO)
ROCKJ = R("#4e463c", "#5a5044", "#665c50")
ROAD = R("#9c927e", "#aca28d", "#bcb29b", "#cbc1a9", "#d6ccb4")
ROAD = SB(ROAD)
ROADJ = R("#6c6250", "#7c725e", "#8c826c")
STRAW = R("#8a6c30", "#a28238", "#b89a48", "#cdb15a", "#ddc470")
STRAW = SB(STRAW)
LIME = R("#9d8f73", "#b0a285", "#c2b698", "#d1c6ab", "#ddd3b9")
LIME = SB(LIME)
LIMEJ = R("#7e7058", "#8c7e66", "#9c8e76")
MUDO = R("#a87a48", "#bb8c56", "#cc9e68", "#dcb07a", "#e8c18c")
MUDO = SB(MUDO)
MUDB = R("#7c5634", "#8e6640", "#a07650", "#b08660")
MUDB = SB(MUDB)
MUDJ = R("#5e4026", "#6e4c30")
HILLO = R("#665f34", "#7c743e", "#928848", "#a89c58", "#bdb06c")
HILLO = SB(HILLO)
HILLC = R("#7a6a3c", "#90804a", "#a69658", "#bcac6c", "#cfc084")
HILLC = SB(HILLC)
REEDS = R("#3a4624", "#4c5a2c", "#627238", "#7e8a44", "#a09a4e", "#c4b45e")
REEDG = R("#52602e", "#6a7a38", "#86924a", "#a4a858")
OLIVE = R("#3e4a34", "#56634a", "#6e7b5a", "#8a9674", "#a7b08f")
BARK = R("#4a4034", "#5e5242", "#746654", "#8a7b66")
WOOD = R("#5c4a38", "#6e5a44", "#826c52", "#98826a", "#ac9880")
WOODJ = R("#2e241a", "#3c2f22")
DOOR = R("#4a3422", "#5c452e", "#70573a", "#866a48")
CYP = R("#243626", "#324630", "#415a3a", "#546e48", "#688458")
PLASTER = R("#b8ab8e", "#c9bda0", "#d8ccb0", "#e4dac0", "#eee5cd")
RED = R("#74302a", "#8a3c30", "#9e4a38", "#b25a42")
DEEP = R("#262a38", "#343644", "#463f48", "#5a4c4c", "#725e58")
CLOTHW = R("#bcae8e", "#cdc0a2", "#dccfb2", "#e8ddc2")
CLOTHB = R("#5c432c", "#6e5238", "#84644a", "#9a785a")


# ---- floors ----------------------------------------------------------------------------------------------------------------------------------------------

def floor_sand() -> np.ndarray:
    n = 128
    X, Y = G(n)
    s = 0.52 + (pn(n, n, 32, 32, 1, 3, 1.3) - 0.5) * 0.5 + (pn(n, n, 9, 9, 2, 2) - 0.5) * 0.25
    s += 0.06 * np.sin(2 * np.pi * (Y / n * 7 + pn(n, n, 40, 40, 3, 2) * 1.8))  # faint river ripples in the sand
    img = Q(s, SAND)
    put(img, speck(n, 0.05, 4), Q(s - 0.35, SAND))
    put(img, speck(n, 0.03, 5), Q(s + 0.35, SAND))
    rng = np.random.RandomState(6)
    pal = R("#7e7262", "#968a76", "#b0a48c", "#c8bca2", "#dcd0b6")
    for _ in range(60):
        r = 1.2 + rng.rand() * 1.9
        blob(img, rng.rand() * n, rng.rand() * n, r * 1.2, r, rng.rand() * 3, dome(0.25 + rng.rand() * 0.5), pal, 0.28)
    return img


def floor_dust() -> np.ndarray:
    n = 128
    s = 0.52 + (pn(n, n, 26, 26, 11, 3) - 0.5) * 0.4 + (pn(n, n, 8, 8, 12, 3) - 0.5) * 0.32
    s -= 0.1 * (pn(n, n, 14, 14, 13, 3) > 0.68)
    img = Q(s, DUST)
    put(img, speck(n, 0.05, 14), Q(s - 0.32, DUST))
    put(img, speck(n, 0.035, 15), Q(s + 0.32, DUST))
    rng = np.random.RandomState(16)
    pal = R("#6e5a44", "#8a7458", "#a48e70", "#bca686", "#d0bc9c")
    for _ in range(78):
        r = 1.1 + rng.rand() * 2.4
        blob(img, rng.rand() * n, rng.rand() * n, r * 1.15, r, rng.rand() * 3, dome(0.25 + rng.rand() * 0.5), pal, 0.3)
    return img


def floor_path() -> np.ndarray:
    n = 128
    X, Y = G(n)
    s = 0.55 + (pn(n, n, 32, 32, 21, 3) - 0.5) * 0.38 + (pn(n, n, 9, 9, 22, 2) - 0.5) * 0.24
    for cx, ph in ((32.0, 0.0), (94.0, 1.7)):  # two faint wheel ruts running along the path
        d = wrapd(X + 2.8 * np.sin(Y / n * 2 * np.pi + ph) + 6.0 * (pn(n, n, 80, 28, 26 + int(cx), 2) - 0.5), cx, n)
        s -= 0.17 * np.exp(-(d / 7.2) ** 2) * (0.6 + 0.8 * pn(n, n, 100, 24, 28 + int(cx), 2))
        s += 0.05 * np.exp(-((np.abs(d) - 11.6) / 2.6) ** 2)
    img = Q(s, PATHP)
    put(img, speck(n, 0.05, 23), Q(s - 0.3, PATHP))
    put(img, speck(n, 0.03, 24), Q(s + 0.3, PATHP))
    rng = np.random.RandomState(25)
    pal = R("#8e826c", "#a89c84", "#c0b49c", "#d4c8ae")
    for _ in range(36):
        r = 1.1 + rng.rand() * 1.6
        blob(img, rng.rand() * n, rng.rand() * n, r * 1.2, r, rng.rand() * 3, dome(0.3 + rng.rand() * 0.5), pal, 0.28)
    return img


def floor_grass() -> np.ndarray:
    n = 128
    s = 0.4 + (pn(n, n, 26, 26, 31, 3) - 0.5) * 0.4 + (pn(n, n, 7, 7, 32, 2) - 0.5) * 0.3
    img = Q(s, GRASS)
    rng = np.random.RandomState(33)
    top = GRASS

    def blade(x, y, ln, lean, tone):
        for t in range(ln):
            k = t / max(ln - 1, 1)
            sh = np.clip(tone * 0.5 + 0.1 + 0.45 * k, 0, 1.0)
            pix(img, x + lean * t, y - t, top[int(round(sh * (len(top) - 1)))] * 255 + 0.5)

    for _ in range(300):  # single blades
        blade(rng.rand() * n, rng.rand() * n, int(rng.randint(3, 6)), (rng.rand() - 0.5) * 0.8, rng.rand())
    for _ in range(56):  # tufts: a fan of blades from one root, dark at the root, pale and golden at the tip
        cx, cy = rng.rand() * n, rng.rand() * n
        pix(img, cx + 1, cy + 1, hexu("#4e4a24"))
        pix(img, cx + 2, cy + 1, hexu("#4e4a24"))
        for k in range(9):
            blade(cx, cy, int(rng.randint(5, 10)), (k - 4) * 0.42, 0.3 + rng.rand() * 0.7)
    put(img, speck(n, 0.01, 34), hexu("#e2d68a"))
    return img


def floor_shingle() -> np.ndarray:
    n = 128
    v = voronoi(n, 15, 41, 0.85)
    t = v["f1"] / (v["f1"] + v["f2"] + 1e-3)
    lit = -(v["dx"] + v["dy"]) / (np.abs(v["dx"]) + np.abs(v["dy"]) + 1.0)
    dm = 1 - (t / 0.5) ** 2
    s = 0.12 + 0.62 * v["rnd"][v["id"]] + 0.3 * dm + 0.1 * lit * (1 - dm) + (pn(n, n, 6, 6, 42, 2) - 0.5) * 0.18
    img = Q(s, SHING)
    put(img, t > 0.455, Q(0.12 + (pn(n, n, 4, 4, 43, 2) - 0.5) * 0.4, SHING))
    put(img, speck(n, 0.03, 44) & (t < 0.4), Q(s + 0.3, SHING))
    return img


def floor_water() -> np.ndarray:
    n = 128
    X, Y = G(n)
    s = 0.45 + (pn(n, n, 64, 64, 51, 2) - 0.5) * 0.18 + (pn(n, n, 30, 12, 52, 2) - 0.5) * 0.12

    def ridge(v, w):
        return np.clip(1 - np.abs(v - 0.5) / w, 0, 1)

    r1 = ridge(pn(n, n, 64, 22, 53, 3), 0.04) ** 1.5
    r2 = ridge(pn(n, n, 36, 12, 54, 3), 0.036) ** 1.5
    s = s + 0.42 * r1 + 0.22 * r2 - 0.1 * np.roll(r1, 2, 0) - 0.06 * np.roll(r2, 1, 0)
    img = Q(s, WATER)
    put(img, speck(n, 0.004, 55) & (r1 + r2 < 0.2), hexu("#d6e4ea"))
    return img


def floor_cobble() -> np.ndarray:
    n = 128
    v = voronoi(n, 5, 61, 0.78)
    t = v["f1"] / (v["f1"] + v["f2"] + 1e-3)
    lit = -(v["dx"] + v["dy"]) / (np.abs(v["dx"]) + np.abs(v["dy"]) + 1.0)
    dm = 1 - (t / 0.5) ** 2.2
    s = 0.22 + 0.34 * v["rnd"][v["id"]] + 0.34 * dm + 0.1 * lit * (1 - dm) + (pn(n, n, 6, 6, 62, 3) - 0.5) * 0.2
    img = Q(s, COBB)
    put(img, speck(n, 0.04, 63) & (t < 0.42), Q(s - 0.3, COBB))
    put(img, t > 0.455, Q(0.35 + (pn(n, n, 4, 4, 64, 2) - 0.5) * 0.7, COBBJ))
    return img


def floor_flag() -> np.ndarray:
    n = 128
    rows = [40, 44, 44]
    img, c, mort, sh = masonry(n, rows, 71, 64, FLAG, FLAGJ, tone=0.1, wjit=0.28, joint=2, wear=0.55, bevel=0.1, scale=14)
    ck = cracks(n, 72, 20, 20, 0.008) & ~mort
    put(img, ck, Q(sh - 0.38, FLAG))
    stain = (pn(n, n, 26, 26, 73, 3) > 0.64) & ~mort
    put(img, stain, Q(sh - 0.17, FLAG))
    return img


def floor_plank() -> np.ndarray:
    n = 64
    c = courses(n, 5, 81, 44, 0.25, 0.1)
    X, Y = G(n)
    gr = pn(n, n, 30, 2.6, 82, 3, 1.8)
    s = 0.5 + (c["tone"] - 0.5) * 0.35 + (gr - 0.5) * 0.4 + (pn(n, n, 9, 9, 83, 2) - 0.5) * 0.15
    s += 0.1 * (c["ly"] == 1) - 0.12 * (c["ly"] >= c["bh"] - 2)
    img = Q(s, PLANK)
    put(img, speck(n, 0.03, 84), Q(s - 0.3, PLANK))
    gap = (c["ly"] < 1) | (c["lx"] < 1)
    put(img, gap, Q(0.3 + (pn(n, n, 4, 4, 85, 2) - 0.5) * 0.5, PLANKJ))
    # nails at the plank ends and a couple of knots
    m = (c["lx"] == 3) & (np.abs(c["ly"] - c["bh"] / 2) < 0.6)
    put(img, m, hexu("#40362a"))
    put(img, np.roll(m, 1, 1), hexu("#b8a888"))
    for kx, ky in ((27, 21),):
        for rr, col in ((3.0, "#6a5238"), (2.0, "#4e3a28"), (1.0, "#3a2c1e")):
            blob(img, kx, ky, rr * 1.5, rr * 0.8, 0, lambda u, v: np.full_like(u, 0.5), px.ramp(col, col))
    return img


def floor_clay() -> np.ndarray:
    n = 128
    X, Y = G(n)
    s = 0.5 + (pn(n, n, 52, 52, 91, 3) - 0.5) * 0.45 + (pn(n, n, 12, 12, 92, 2) - 0.5) * 0.25
    sweep = np.sin(2 * np.pi * (X / n * 5 + 1.6 * pn(n, n, 68, 68, 93, 2) + 0.35 * Y / n))
    s += 0.09 * sweep  # the broom's long strokes
    img = Q(s, CLAY)
    put(img, speck(n, 0.05, 94), Q(s - 0.3, CLAY))
    put(img, speck(n, 0.03, 95), Q(s + 0.3, CLAY))
    # a few worn square tiles half-buried in the swept clay
    for tx, ty, sz in ((6, 10, 54), (76, 76, 34)):
        box = (X >= tx) & (X < tx + sz) & (Y >= ty) & (Y < ty + sz)
        wear = pn(n, n, 28, 28, 96 + tx, 2, 1.6) > 0.22
        ts = 0.5 + (pn(n, n, 8, 8, 97 + ty, 2) - 0.5) * 0.4
        put(img, box & wear, Q(ts, CLAYT))
        gap = ((X == tx) | (Y == ty) | (X == tx + sz) | (Y == ty + sz)) & (X >= tx) & (Y >= ty) & (X <= tx + sz) & (Y <= ty + sz) & wear
        put(img, gap, Q(np.full((n, n), 0.0), CLAY))
        put(img, box & wear & ((X == tx + 1) | (Y == ty + 1)), Q(ts + 0.2, CLAYT))
    return img


def floor_soil() -> np.ndarray:
    n = 128
    X, Y = G(n)
    s = 0.45 + (pn(n, n, 40, 40, 101, 3) - 0.5) * 0.6 + (pn(n, n, 8, 8, 102, 3) - 0.5) * 0.35
    img = Q(s, SOIL)
    put(img, speck(n, 0.05, 103), Q(s - 0.3, SOIL))
    put(img, speck(n, 0.03, 104), Q(s + 0.35, SOIL))
    rng = np.random.RandomState(105)
    clod = R("#3c2e20", "#54432e", "#6c5840", "#86704e")
    for _ in range(26):
        r = 1.5 + rng.rand() * 2.2
        blob(img, rng.rand() * n, rng.rand() * n, r * 1.2, r, rng.rand() * 3, dome(0.3 + rng.rand() * 0.5), clod, 0.3)
    # leaf litter first, then a few roots creeping over it (one thick, forking, one thin)
    for _ in range(44):
        blob(img, rng.rand() * n, rng.rand() * n, 2.6 + rng.rand() * 1.4, 1.1 + rng.rand() * 0.5, rng.rand() * 3.14, lambda u, v, t=rng.rand(): np.full_like(u, 0.1 + 0.5 * t) + 0.1 * (u - v) * 0.3, LEAF, 0.0)
    rootp = R("#3a2c1e", "#52402c", "#6a5438", "#86704c")

    def root(x0, y0, x1, y1, w0, w1, wob, seed):
        rr = np.random.RandomState(seed)
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 1.5) + 2
        ph = rr.rand() * 6.28
        for i in range(steps):
            t = i / (steps - 1)
            cx = x0 + (x1 - x0) * t + wob * np.sin(t * 9 + ph)
            cy = y0 + (y1 - y0) * t + wob * 0.8 * np.sin(t * 7 + ph * 2)
            w = w0 + (w1 - w0) * t
            for dy in range(-int(w) - 1, int(w) + 2):
                for dx in range(-int(w) - 1, int(w) + 2):
                    if dx * dx + dy * dy <= w * w:
                        sh = np.clip(0.5 - 0.3 * (dx + dy) / max(w, 1) + 0.07 * np.sin(t * 40), 0, 1)
                        pix(img, cx + dx, cy + dy, rootp[int(round(sh * 3))] * 255 + 0.5)

    root(-6, 34, 70, 58, 4.0, 2.0, 2.2, 106)
    root(48, 49, 84, 38, 1.6, 0.8, 1.2, 107)
    root(70, 100, 140, 88, 2.2, 1.0, 1.6, 108)
    return img


def floor_rock() -> np.ndarray:
    n = 128
    v = voronoi(n, 3, 111, 0.75)
    edge = v["f2"] - v["f1"]
    lit = -(v["dx"] + v["dy"]) / (np.abs(v["dx"]) + np.abs(v["dy"]) + 1.0)
    X, Y = G(n)
    tone = v["rnd"][v["id"]]
    strata = np.sin(2 * np.pi * (X * 0.6 + Y * 0.25) / n * 3 + pn(n, n, 30, 30, 112, 2) * 5 + tone * 6) * 0.07
    s = 0.34 + 0.34 * tone + strata + (pn(n, n, 14, 14, 113, 3) - 0.5) * 0.3 + (pn(n, n, 4, 4, 114, 2) - 0.5) * 0.12
    s += 0.1 * ((edge >= 2) & (edge < 5)) * lit
    img = Q(s, ROCK)
    ochre = pn(n, n, 22, 22, 115, 2, 2.0) > 0.74
    put(img, ochre, Q(s - 0.02, ROCKO))
    cr = (edge < 1.8) | cracks(n, 116, 16, 16, 0.009)
    put(img, cr, Q(0.15 + (pn(n, n, 4, 4, 117, 2) - 0.5) * 0.5, ROCKJ))
    put(img, speck(n, 0.05, 118) & ~cr, Q(s - 0.28, ROCK))
    return img


def floor_road() -> np.ndarray:
    n = 128
    v = voronoi(n, 3, 121, 0.9)
    edge = v["f2"] - v["f1"]
    lit = -(v["dx"] + v["dy"]) / (np.abs(v["dx"]) + np.abs(v["dy"]) + 1.0)
    tone = v["rnd"][v["id"]]
    tilt = (v["dx"] * 0.004 + v["dy"] * 0.006)
    s = 0.3 + 0.4 * tone + tilt + (pn(n, n, 10, 10, 122, 3) - 0.5) * 0.28 + 0.12 * ((edge >= 2.2) & (edge < 4.5)) * lit
    img = Q(s, ROAD)
    put(img, speck(n, 0.04, 123), Q(s - 0.3, ROAD))
    put(img, edge < 2.2, Q(0.3 + (pn(n, n, 3, 3, 124, 2) - 0.5) * 0.8, ROADJ))
    # wear scratches
    rng = np.random.RandomState(125)
    for _ in range(30):
        x0, y0 = rng.rand() * n, rng.rand() * n
        a = rng.rand() * 3.14
        ln = 5 + rng.rand() * 10
        line(img, x0, y0, x0 + np.cos(a) * ln, y0 + np.sin(a) * ln * 0.5, Q(np.full((1, 1), 0.88), ROAD)[0, 0])
    return img


def floor_straw() -> np.ndarray:
    n = 64
    s = 0.35 + (pn(n, n, 14, 14, 131, 3) - 0.5) * 0.4
    img = Q(s, STRAW)
    rng = np.random.RandomState(132)
    for _ in range(240):
        x0, y0 = rng.rand() * n, rng.rand() * n
        a = (rng.rand() - 0.5) * 1.3 + (np.pi * 0.5 if rng.rand() < 0.15 else 0.0)
        ln = 7 + rng.rand() * 8
        tone = 0.2 + rng.rand() * 0.8
        x1, y1 = x0 + np.cos(a) * ln, y0 + np.sin(a) * ln
        line(img, x0, y1 + 1, x1, y1 + 2, STRAW[0] * 255 + 0.5) if False else None
        line(img, x0, y0 + 1, x1, y1 + 1, STRAW[max(0, int(tone * 4) - 2)] * 255 + 0.5)
        line(img, x0, y0, x1, y1, STRAW[int(round(tone * 4))] * 255 + 0.5)
    return img


def floor_garden() -> np.ndarray:
    n = 128
    s = 0.5 + (pn(n, n, 26, 26, 141, 3) - 0.5) * 0.36 + (pn(n, n, 7, 7, 142, 2) - 0.5) * 0.3
    img = Q(s, GARDEN)
    rng = np.random.RandomState(143)
    for _ in range(360):
        x0, y0, ln, lean, tone = rng.rand() * n, rng.rand() * n, int(rng.randint(2, 5)), (rng.rand() - 0.5) * 0.6, rng.rand()
        for t in range(ln):
            k = t / max(ln - 1, 1)
            sh = np.clip(tone * 0.5 + 0.2 + 0.4 * k, 0, 1)
            pix(img, x0 + lean * t, y0 - t, GARDEN[int(round(sh * 4))] * 255 + 0.5)
    for _ in range(90):  # tiny yellow buds
        x0, y0 = rng.rand() * n, rng.rand() * n
        pix(img, x0, y0 + 1, hexu("#3e5a24"))
        pix(img, x0, y0, hexu("#e6cc4a"))
    for _ in range(60):  # tiny white daisies: four petals round a gold eye
        x0, y0 = rng.rand() * n, rng.rand() * n
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            pix(img, x0 + dx, y0 + dy, hexu("#ece6d2"))
        pix(img, x0, y0, hexu("#e2b838"))
        pix(img, x0 + 1, y0 + 2, hexu("#3e5a24"))
    return img


# ---- walls (top-down: v = 0 at the top) ------------------------------------------------------------------------------------------------------------------

def wall_limestone() -> np.ndarray:
    """A tall house wall: it repeats top to bottom (the sector light, not the tile, darkens the foot), so nothing here depends on the row."""
    n = 128
    X, Y = G(n)
    extra = -(pn(n, n, 3, 44, 202, 2, 1.8) - 0.5) * 0.14 - 0.05  # rain streaks run down
    img, c, mort, sh = masonry(n, 4, 201, 64, LIME, LIMEJ, tone=0.18, wjit=0.28, extra=extra, wear=0.75, bevel=0.17, joint=1, scale=14)
    return img


def wall_mudbrick() -> np.ndarray:
    n = 128
    X, Y = G(n)
    brick, c, mort, bsh = masonry(n, 6, 211, 40, MUDB, MUDJ, tone=0.14, wjit=0.25, joint=1, wear=0.6, bevel=0.1, scale=7)
    sh = 0.55 + (pn(n, n, 30, 30, 212, 3) - 0.5) * 0.5 + (pn(n, n, 7, 7, 213, 2) - 0.5) * 0.22
    sh += 0.07 * np.sin(2 * np.pi * (X / n * 3 + Y / n * 12 + pn(n, n, 20, 20, 214, 2) * 2))  # trowel marks (whole cycles: the tile repeats)
    plaster = Q(sh, MUDO)
    put(plaster, speck(n, 0.04, 215), Q(sh - 0.3, MUDO))
    flake = pn(n, n, 16, 14, 216, 3, 1.8) > 0.8
    up = flake & ~np.roll(flake, 1, 0)       # the lip's lit upper edge
    down = flake & ~np.roll(flake, -1, 0)
    img = np.where(flake[..., None], brick, plaster)
    put(img, up, Q(sh + 0.25, MUDO))
    put(img, np.roll(down, 1, 0) & flake, Q(bsh - 0.2, MUDB))
    crng = np.random.RandomState(218)
    for _ in range(3):  # a few long hairline cracks running down the plaster
        x, y0 = crng.rand() * n, crng.rand() * 60
        for i in range(int(crng.randint(22, 44))):
            x += (crng.rand() - 0.5) * 1.6
            if not flake[int(y0 + i) % n, int(x) % n]:
                pix(img, x, y0 + i, hexu("#7a5636"))
    return img


def wall_rock() -> np.ndarray:
    n = 128
    X, Y = G(n)
    rng = np.random.RandomState(221)
    hs = []
    while sum(hs) < n + 50:
        hs.append(int(rng.randint(9, 28)))
    edges = np.cumsum(hs)
    warp = (pn(n, n, 64, 56, 222, 3) - 0.5) * 22
    yw = Y + warp
    band = np.searchsorted(edges, yw, "right")
    start = np.where(band > 0, edges[np.clip(band - 1, 0, len(edges) - 1)], 0)
    height = edges[np.clip(band, 0, len(edges) - 1)] - start
    ly = yw - start
    bt = rng.rand(len(edges) + 2).astype(np.float32)[band]
    ochre = (rng.rand(len(edges) + 2) < 0.4)[band]
    s = 0.5 + (bt - 0.5) * 0.34 + (pn(n, n, 14, 6, 223, 3) - 0.5) * 0.3 + (pn(n, n, 3, 3, 224, 2) - 0.5) * 0.14
    s += 0.18 * (ly < 2.2) - 0.22 * (ly > height - 3.2) - 0.1 * np.clip((ly - 2) / np.maximum(height, 1), 0, 1)
    s -= 0.17 * np.exp(-Y / 8.0)
    img = np.where(ochre[..., None], Q(s, ROCKO), Q(s, ROCK))
    put(img, speck(n, 0.04, 228), Q(s - 0.3, ROCK))
    # a few vertical cracks: they start at a ledge and run down through one or two strata, with a lit edge beside them
    for k in range(7):
        x0, y0 = rng.rand() * n, rng.rand() * 90
        ln = int(rng.randint(14, 44))
        x = x0
        for i in range(ln):
            x += (rng.rand() - 0.5) * 1.3
            col = Q(np.full((1, 1), 0.08 + 0.2 * rng.rand()), ROCKJ)[0, 0]
            pix(img, x, y0 + i, col)
            if i % 7 < 4:
                pix(img, x + 1, y0 + i, Q(np.full((1, 1), 0.85), ROCK)[0, 0])
    return img


def wall_hill() -> np.ndarray:
    n = 128
    X, Y = G(n)
    t = Y / n
    s = 0.74 - 0.36 * t + (pn(n, n, 36, 16, 231, 3) - 0.5) * 0.26 + (pn(n, n, 6, 6, 236, 2) - 0.5) * 0.12
    s += 0.05 * np.sin(2 * np.pi * (t * 5 + pn(n, n, 50, 30, 232, 2) * 1.6))  # terraces and folds in the slope
    s -= 0.3 * smooth(t, 0.84, 1.0)
    hue = smooth(pn(n, n, 36, 22, 233, 3, 1.6), 0.4, 0.62)
    b = BAYER[np.arange(n)[:, None] % 8, np.arange(n)[None, :] % 8]
    img = np.where((hue > b + 0.5)[..., None], Q(s, HILLC), Q(s, HILLO))
    # pale rock outcrops in long strata on the upper slope
    out = (pn(n, n, 30, 5, 237, 3, 1.8) > 0.72) & (t < 0.6)
    put(img, out, Q(s + 0.22, HILLC))
    rng = np.random.RandomState(234)
    for _ in range(420):  # scrub dots, denser lower down
        x0, y0 = rng.rand() * n, (rng.rand() ** 0.8) * n
        if rng.rand() < 0.1 + 0.9 * (y0 / n):
            col = hexu("#555530") if rng.rand() < 0.6 else hexu("#706c38")
            pix(img, x0, y0, col)
            if rng.rand() < 0.5:
                pix(img, x0 + 1, y0, col)
    return img


def wall_reeds() -> np.ndarray:
    n = 128
    X, Y = G(n)
    s = 0.3 + (pn(n, n, 10, 80, 241, 3) - 0.5) * 0.4 - 0.25 * smooth(Y / n, 0.85, 1.0)
    img = Q(s, REEDS)
    rng = np.random.RandomState(242)
    for layer, (count, lo, hi) in enumerate(((110, 0.0, 0.55), (110, 0.25, 0.8), (96, 0.5, 1.0))):
        for _ in range(count):
            x0 = rng.rand() * n
            wdt = int(rng.randint(1, 3))
            lean = (rng.rand() - 0.5) * 0.09
            ph = rng.rand() * 6.28
            gold = lo + rng.rand() * (hi - lo)
            top = int(rng.randint(0, 24))
            for y in range(top, n):
                xx = x0 + lean * y + 1.1 * np.sin(y * 0.05 + ph)
                k = y / n
                # green at the root, gold up the reed, a pale tip
                sh = np.clip(0.15 + 0.35 * (1 - k) + 0.15 * gold + (0.15 if y < top + 5 else 0), 0, 1)
                pal = REEDG if gold < 0.45 else REEDS
                col = pal[int(round(sh * (len(pal) - 1)))] * 255 + 0.5
                for d in range(wdt):
                    pix(img, xx + d, y, col * (0.82 if d == wdt - 1 and wdt > 1 else 1.0))
    # feathery seed heads at the top of some reeds
    for _ in range(60):
        x0, y0 = rng.rand() * n, rng.rand() * 20
        for k in range(6):
            pix(img, x0 + (k % 2), y0 + k, REEDS[4] * 255 + 0.5)
    return img


def wall_city() -> np.ndarray:
    """The city wall: great dressed blocks (0.4 m courses, 0.8 m blocks), seamless top to bottom."""
    n = 128
    X, Y = G(n)
    extra = -(pn(n, n, 4, 40, 252, 2, 1.8) - 0.5) * 0.1 - 0.04
    img, c, mort, sh = masonry(n, [43, 42, 43], 251, 90, LIME, LIMEJ, tone=0.11, wjit=0.2, joint=1, wear=0.5, extra=extra, bevel=0.12, scale=14)
    rim = (c["ly"] >= 2) & (c["ly"] < 4) & (c["lx"] >= 2) & ~mort  # the drafted margin of each block
    put(img, rim, Q(sh + 0.08, LIME))
    return img


def wall_door() -> np.ndarray:
    n = 128
    X, Y = G(n)
    extra = -0.17 * np.exp(-Y / 7.0) - 0.07 * (Y / n) ** 2 - 0.14 * smooth(Y, 112, 127)
    img, c, mort, sh = masonry(n, 10, 261, 30, LIME, LIMEJ, tone=0.12, wjit=0.28, extra=extra, wear=0.6, bevel=0.12)
    x0, x1, ytop = 46, 82, 42
    # jamb stones either side, a heavy lintel with a drip shadow under it
    for k, yy in enumerate(range(ytop - 2, n, 11)):
        for xa in (x0 - 5, x1):
            ln = 5 if (k % 2 == 0) else 7
            blk = (X >= xa) & (X < xa + ln) & (Y >= yy) & (Y < yy + 10)
            put(img, blk, Q(sh * 0 + 0.55 + 0.1 * (k % 2) - 0.1 * (X >= xa + ln - 1), LIME))
            put(img, blk & ((Y == yy) | (X == xa)), Q(np.full((n, n), 0.18), LIMEJ))
    lint = (X >= x0 - 9) & (X < x1 + 9) & (Y >= ytop - 10) & (Y < ytop - 1)
    put(img, lint, Q(0.62 + (pn(n, n, 6, 6, 262, 2) - 0.5) * 0.2 - 0.1 * (Y > ytop - 4), LIME))
    put(img, lint & ((Y == ytop - 10) | (X == x0 - 9) | (X == x1 + 8)), Q(np.full((n, n), 0.12), LIMEJ))
    put(img, (X >= x0 - 9) & (X < x1 + 9) & (Y == ytop - 1), Q(np.full((n, n), 0.06), LIMEJ))
    # the door leaf: vertical planks with grain, two iron straps, a ring pull
    door = (X >= x0) & (X < x1) & (Y >= ytop)
    pw = (X - x0) % 9
    plk = (X - x0) // 9
    tn = np.random.RandomState(263).rand(8).astype(np.float32)[np.clip(plk, 0, 7).astype(int)]
    s = 0.45 + (tn - 0.5) * 0.3 + (pn(n, n, 2.5, 30, 264, 3, 1.6) - 0.5) * 0.35 + 0.12 * (pw == 1) - 0.14 * (pw >= 8)
    s -= 0.25 * np.exp(-np.clip(Y - ytop, 0, None) / 4.0) * 0.8
    put(img, door, Q(s, DOOR))
    put(img, door & (pw == 0), Q(np.full((n, n), 0.0), DOOR))
    put(img, door & (Y < ytop + 3), Q(np.full((n, n), 0.0), DOOR))
    for sy in (ytop + 14, ytop + 60):
        strap = door & (Y >= sy) & (Y < sy + 5)
        put(img, strap, Q(0.35 + 0.2 * (Y == sy), R("#2c2a2a", "#3e3a38", "#58524c", "#76706a")))
        for rx in range(int(x0) + 4, int(x1) - 2, 9):
            put(img, (X == rx) & (Y == sy + 2), hexu("#8a8478"))
    put(img, (X >= x1 - 9) & (X < x1 - 5) & (Y >= ytop + 42) & (Y < ytop + 46), hexu("#2e2a28"))
    put(img, (X >= x1 - 8) & (X < x1 - 6) & (Y >= ytop + 43) & (Y < ytop + 45), hexu("#8a8478"))
    put(img, (Y >= 124) & (X >= x0 - 7) & (X < x1 + 7), Q(0.7 - 0.2 * (Y > 125), LIME))  # worn threshold step
    return img


def wall_arch() -> np.ndarray:
    n = 128
    X, Y = G(n)
    extra = -0.17 * np.exp(-Y / 7.0) - 0.08 * (Y / n) ** 2 - 0.12 * smooth(Y, 112, 127)
    img, c, mort, sh = masonry(n, 8, 271, 30, LIME, LIMEJ, tone=0.12, wjit=0.28, extra=extra, wear=0.55, bevel=0.12)
    cx, spring, r0 = 64.0, 62.0, 40.0
    r = np.hypot(X - cx, Y - spring)
    d = np.where(Y >= spring, np.minimum(X - 24, 104 - X), r0 - r)
    d = np.where((Y >= spring) & ((X < 24) | (X >= 104)), -1, d)
    # voussoirs round the arch and a keystone
    a = np.arctan2(spring - Y, X - cx)
    vs = (Y < spring) & (r >= r0) & (r < r0 + 9)
    k = np.floor(a / (np.pi / 13)).astype(int)
    kf = (a / (np.pi / 13)) % 1.0
    vt = np.random.RandomState(272).rand(16).astype(np.float32)[np.clip(k, 0, 15)]
    put(img, vs, Q(0.52 + (vt - 0.5) * 0.25 + 0.1 * (r < r0 + 2) - 0.08 * (r > r0 + 7), LIME))
    put(img, vs & ((kf < 0.09) | (r < r0 + 0.6)), Q(np.full((n, n), 0.18), LIMEJ))
    key = (np.abs(a - np.pi / 2) < np.pi / 24) & (r >= r0 - 1) & (r < r0 + 14) & (Y < spring)
    put(img, key, Q(0.72 + (pn(n, n, 5, 5, 273, 2) - 0.5) * 0.15, LIME))
    put(img, key & ((np.abs(a - np.pi / 2) > np.pi / 24 - 0.04) | (r > r0 + 13)), Q(np.full((n, n), 0.15), LIMEJ))
    # the pier bases
    # the opening: a stone reveal, then deep blue-brown shadow, floor light creeping in at the foot
    op = d >= 0
    rev = op & (d < 5)
    put(img, rev, Q(0.5 - 0.09 * d + (X < cx) * 0.06 - 0.18 * (Y < spring - 8) * (1 - d / 5) * 0.0, LIMEJ.copy() if False else LIME))
    deep = op & (d >= 5)
    ds = 0.5 - 0.3 * np.clip((d - 5) / 26, 0, 1) + (pn(n, n, 10, 10, 274, 2) - 0.5) * 0.12 + 0.32 * smooth(Y, 96, 128) * (1 - 0.4 * np.clip((d - 5) / 26, 0, 1))
    put(img, deep, Q(ds, DEEP))
    put(img, op & (d < 7) & (d >= 5), Q(np.full((n, n), 0.2), DEEP))
    return img


def wall_timber() -> np.ndarray:
    n = 64
    X, Y = G(n)
    widths = [9, 8, 9, 7, 8, 9, 7, 7]
    edges = np.concatenate([[0], np.cumsum(widths)])
    b = np.searchsorted(edges, X, "right") - 1
    lx = X - edges[b]
    tn = np.random.RandomState(281).rand(len(widths)).astype(np.float32)[b]
    s = 0.46 + (tn - 0.5) * 0.35 + (pn(n, n, 2.6, 40, 282, 3, 1.7) - 0.5) * 0.35 + (pn(n, n, 12, 12, 283, 2) - 0.5) * 0.14
    s += 0.1 * (lx == 1) - 0.1 * (lx >= widths[0] - 2) * 0
    s -= 0.17 * np.exp(-Y / 5.0)
    img = Q(s, WOOD)
    put(img, lx == 0, Q(0.28 + (pn(n, n, 3, 6, 284, 2) - 0.5) * 0.3, WOODJ))
    for ry in (10, 44):  # two battens across, nailed
        rail = (Y >= ry) & (Y < ry + 7)
        rs = 0.62 + (pn(n, n, 22, 2.4, 285 + ry, 3, 1.5) - 0.5) * 0.3 + 0.1 * (Y == ry) - 0.15 * (Y == ry + 6)
        put(img, rail, Q(rs, WOOD))
        put(img, rail & ((Y == ry + 6) | (Y == ry)), Q(rs - 0.25, WOOD))
        for nx in (4, 17, 30, 43, 56):
            put(img, (X == nx) & (Y == ry + 3), hexu("#3a3024"))
            put(img, (X == nx + 1) & (Y == ry + 3), hexu("#b8a888"))
    for kx, ky in ((20, 28), (50, 56)):  # knots
        for rr, col in ((3.0, "#5c4a36"), (2.0, "#403224"), (0.9, "#2e241a")):
            blob(img, kx, ky, rr * 0.8, rr * 1.3, 0, lambda u, v: np.full_like(u, 0.5), px.ramp(col, col))
    return img


def wall_olive() -> np.ndarray:
    n = 128
    X, Y = G(n)
    s = 0.5 + (pn(n, n, 12, 12, 291, 4, 1.4) - 0.5) * 0.5 - 0.05 * (Y / n)
    img = Q(s, OLIVE)
    rng = np.random.RandomState(292)
    for _ in range(1900):  # narrow silver-green leaves: short strokes, lit where the foliage mass is lit
        x0, y0 = rng.rand() * n, rng.rand() * n * 0.94
        a = rng.rand() * 6.28
        ln = 2.5 + rng.rand() * 2.5
        loc = s[int(y0) % n, int(x0) % n]
        k = int(round(np.clip(loc + (rng.rand() - 0.4) * 0.8, 0, 1) * 4))
        line(img, x0, y0, x0 + np.cos(a) * ln, y0 + np.sin(a) * ln * 0.6, OLIVE[k] * 255 + 0.5)
    gaps = (pn(n, n, 7, 7, 293, 3, 2.2) > 0.86)
    put(img, gaps, Q(np.full((n, n), 0.0) + (pn(n, n, 3, 3, 294, 2) - 0.5) * 0.3, OLIVE))
    # the grove floor shadow and the gnarled trunks showing underneath the foliage
    sh_b = smooth(Y, 74, 104)
    base = Q(0.06 + (pn(n, n, 6, 6, 295, 2) - 0.5) * 0.3 + 0.1 * smooth(Y, 120, 128), OLIVE)
    dap = speck(n, 0.03, 296) | (pn(n, n, 8, 8, 297, 2, 2.0) > 0.78)
    put(base, dap, Q(np.full((n, n), 0.5), OLIVE))
    img = np.where(((Y > 74) & (rng.rand(n, n) < sh_b))[..., None], base, img)
    for tx, tw in ((20, 9), (66, 11), (104, 8)):
        ty0 = 70 + rng.randint(0, 8)
        for y in range(ty0, n):
            k = (y - ty0) / (n - ty0)
            cx = tx + 4 * np.sin(y * 0.09 + tx) + 2.5 * np.sin(y * 0.23)
            w = tw * (0.7 + 0.5 * k) + 1.5 * np.sin(y * 0.3)
            for xx in range(int(cx - w / 2), int(cx + w / 2) + 1):
                u = (xx - cx) / (w / 2 + 1e-3)
                sh = np.clip(0.5 - 0.35 * u - 0.12 * abs(u) + 0.12 * np.sin(xx * 1.7 + y * 0.1), 0, 1)
                pix(img, xx, y, BARK[int(round(sh * 3))] * 255 + 0.5)
    return img


def wall_stable() -> np.ndarray:
    n = 64
    X, Y = G(n)
    s = 0.5 + (pn(n, n, 16, 16, 301, 3) - 0.5) * 0.5 + (pn(n, n, 4, 4, 302, 2) - 0.5) * 0.24
    daub = R("#8a6e4c", "#9c805a", "#ae926a", "#c0a47a", "#d0b88c")
    img = Q(s, daub)
    put(img, cracks(n, 303, 10, 10, 0.007), hexu("#7a6046"))
    rng = np.random.RandomState(304)
    for _ in range(60):  # straw chopped into the daub
        x0, y0 = rng.rand() * n, 14 + rng.rand() * 50
        a = rng.rand() * 3.14
        line(img, x0, y0, x0 + np.cos(a) * 3, y0 + np.sin(a) * 1.5, STRAW[int(1 + rng.rand() * 3)] * 255 + 0.5)
    # timber frame: two posts, a mid rail and a sill
    for x0 in (0, 32):
        post = ((X - x0) % n < 6)
        ps = 0.45 + (pn(n, n, 2.5, 30, 305 + x0, 3, 1.6) - 0.5) * 0.4 + 0.15 * (((X - x0) % n) == 1) - 0.18 * (((X - x0) % n) == 5)
        put(img, post & (Y > 10), Q(ps, WOOD))
    for ry in (34, 56):
        rail = (Y >= ry) & (Y < ry + 6 + (2 if ry > 50 else 0))
        rs = 0.55 + (pn(n, n, 20, 2.4, 307 + ry, 3, 1.5) - 0.5) * 0.35 + 0.15 * (Y == ry) - 0.15 * (Y >= ry + 5)
        put(img, rail, Q(rs, WOOD))
    put(img, (Y >= 12) & (Y < 16), Q(0.12 + (pn(n, n, 4, 4, 308, 2) - 0.5) * 0.3, daub))  # shadow under the thatch
    # the thatch edge: straw hanging in ragged strands, jagged along its lower edge
    edge = 10 + 3 * pn(n, 1, 3, 1, 309, 2)[0] * 3 + (np.random.RandomState(310).rand(n) * 3)
    th = Y < edge[X.astype(int)]
    ts = 0.5 + (pn(n, n, 1.6, 12, 311, 3, 1.8) - 0.5) * 0.6 + 0.1 * (1 - Y / 12.0)
    put(img, th, Q(ts, STRAW))
    put(img, th & (Y >= edge[X.astype(int)] - 1.5), Q(ts - 0.25, STRAW))
    return img


def _column(n, img, cx, hw, y0, y1, sh_mod=None):
    X, Y = G(n)
    u = np.clip((X - cx) / hw, -1, 1)
    th = np.arcsin(u)
    lamb = np.clip(np.cos(th + 0.65), 0, 1)
    t = (th / 0.5236) % 1.0
    groove = 1 - np.abs(2 * t - 1)  # 0 at the arris, 1 at the flute's centre
    s = 0.28 + 0.62 * lamb - 0.14 * groove ** 1.3 * (0.5 + 0.5 * np.abs(u) ** 0.2) + 0.05 * np.sin(2 * np.pi * t)
    s += (pn(n, n, 3, 40, int(cx) + 7, 2) - 0.5) * 0.1
    m = (np.abs(X - cx) <= hw) & (Y >= y0) & (Y < y1)
    put(img, m, Q(s, LIME))
    return m


def wall_columns() -> np.ndarray:
    n = 128
    X, Y = G(n)
    ds = 0.42 + (pn(n, n, 12, 18, 321, 2) - 0.5) * 0.14 - 0.14 * (Y / n) + 0.0
    img = Q(ds, DEEP)
    # faint courses of the back wall far behind
    put(img, ((Y % 22) < 1) & (Y > 30), Q(np.full((n, n), 0.08), DEEP))
    put(img, (Y >= 118), Q(0.55 + 0.25 * (Y == 118), DEEP))
    # entablature across the top: a pale architrave in two fasciae, shadow under it
    put(img, Y < 7, Q(0.58 + 0.12 * (Y < 2) + (pn(n, n, 8, 8, 322, 2) - 0.5) * 0.15 - 0.06 * (Y >= 5), LIME))
    put(img, (Y >= 7) & (Y < 11), Q(0.38 - 0.07 * (Y - 7) + (pn(n, n, 8, 8, 323, 2) - 0.5) * 0.1, DEEP))
    put(img, (Y == 6), hexu("#8c7e66"))
    for cx in (32.0, 96.0):
        _column(n, img, cx, 10.5, 17, 108)
        # capital: neck ring, a curved echinus, a square abacus; base: a torus on a plinth
        cap = [(14, 17, 11.5, 0.30), (11, 14, 14.0, 0.55), (7, 11, 16.5, 0.68)]
        for ya, yb, hw, tone in cap:
            m = (np.abs(X - cx) <= hw) & (Y >= ya) & (Y < yb)
            put(img, m, Q(tone + 0.2 * (np.abs(X - cx) < hw * 0.5) * 0.4 - 0.12 * (X > cx + hw * 0.6) + (pn(n, n, 6, 6, 330, 2) - 0.5) * 0.1, LIME))
            put(img, m & (Y == ya), Q(np.full((n, n), 0.12) + 0.0, LIME))
        put(img, (np.abs(X - cx) <= 16.5) & (Y == 10), Q(np.full((n, n), 0.15), LIME))
        for ya, yb, hw, tone in ((108, 112, 12.5, 0.55), (112, 116, 14.5, 0.62), (116, 120, 15.5, 0.52)):
            m = (np.abs(X - cx) <= hw) & (Y >= ya) & (Y < yb)
            put(img, m, Q(tone - 0.14 * (X > cx + hw * 0.6) + 0.1 * (Y == ya) + (pn(n, n, 6, 6, 331, 2) - 0.5) * 0.1, LIME))
        put(img, (np.abs(X - cx) <= 12) & (Y >= 17) & (Y < 21), Q(np.full((n, n), 0.12), LIME))
        # a soft cast shadow of the column on the back wall
        sx = (X > cx + 11) & (X < cx + 17) & (Y > 11) & (Y < 118)
        put(img, sx, Q(0.12 + 0.0 * Y, DEEP))
    put(img, (Y >= 120), Q(0.6 + 0.12 * (Y == 120) - 0.05 * (Y >= 126) + (pn(n, n, 10, 3, 332, 2) - 0.5) * 0.12, LIME))
    put(img, (Y == 125), Q(np.full((n, n), 0.2), LIMEJ))
    return img


def wall_praetorium() -> np.ndarray:
    """The governor's hall: plaster with a deep red fresco panel inside a pale border, one panel per 1.2 m tile, so it repeats as a painted wall in every direction."""
    n = 128
    X, Y = G(n)
    sh = 0.58 + (pn(n, n, 30, 30, 341, 3) - 0.5) * 0.35 + (pn(n, n, 7, 7, 342, 2) - 0.5) * 0.16
    img = Q(sh, PLASTER)
    put(img, speck(n, 0.025, 343), Q(sh - 0.3, PLASTER))
    put(img, cracks(n, 344, 6, 46, 0.006) & (pn(n, n, 30, 30, 349, 2) > 0.52), Q(sh - 0.3, PLASTER))
    x0, y0, x1, y1 = 16, 16, 112, 112
    panel = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    bs = 0.52 + (pn(n, n, 18, 18, 345, 3) - 0.5) * 0.45 + (pn(n, n, 5, 5, 346, 2) - 0.5) * 0.18 - 0.1 * ((Y - y0) / (y1 - y0)) + 0.1 * (Y < y0 + 4)
    put(img, panel, Q(bs, R("#6c3c34", "#7e4838", "#8e5440", "#9e6048")))
    border = ((X >= x0 - 4) & (X < x1 + 4) & (Y >= y0 - 4) & (Y < y1 + 4)) & ~panel
    put(img, border, Q(np.full((n, n), 0.88), PLASTER))
    inner = (X >= x0 + 8) & (X < x1 - 8) & (Y >= y0 + 8) & (Y < y1 - 8)
    ring = inner & ~((X >= x0 + 10) & (X < x1 - 10) & (Y >= y0 + 10) & (Y < y1 - 10))
    put(img, ring, Q(np.full((n, n), 0.78), PLASTER))
    put(img, panel & ((X == x0) | (Y == y0)), Q(np.full((n, n), 0.15), R("#6c3c34", "#7e4838")))
    put(img, panel & speck(n, 0.012, 347), "#b8806a")
    return img


def wall_cloth() -> np.ndarray:
    n = 64
    X, Y = G(n)
    pat = [(14, 0), (6, 1), (4, 0), (8, 1)] * 2
    stripe = np.zeros(n, int)
    x = 0
    for w, k in pat:
        stripe[x:x + w] = k
        x += w
    st = stripe[X.astype(int)]
    drape = 0.12 * np.sin(2 * np.pi * (X / n * 2 + 0.07 * pn(n, n, 30, 30, 351, 2) * 3 + 0.0)) + (pn(n, n, 40, 30, 352, 2) - 0.5) * 0.14
    drape += 0.04 * np.sin(2 * np.pi * (Y / n * 3 + X / n * 1)) - 0.08 * (Y / n)
    weave = 0.05 * (((X + Y) % 2) - 0.5) + 0.03 * (((X // 2 + Y // 2) % 2) - 0.5)
    wool = Q(0.5 + drape + weave, CLOTHW)
    brown = Q(0.5 + drape * 1.2 + weave, CLOTHB)
    img = np.where((st == 1)[..., None], brown, wool)
    put(img, speck(n, 0.03, 353) & (st == 0), Q(np.full((n, n), 0.1), CLOTHW))
    put(img, (Y < 3), Q(0.4 + 0.15 * (Y == 0) * 0 - 0.1 * (Y == 2) + weave, CLOTHB))  # the top seam
    put(img, (Y >= 58) & (Y < 61), Q(0.55 + weave - 0.12 * (Y == 58), CLOTHB))  # the hem, with a row of stitches
    put(img, (Y == 59) & (X % 3 < 2), Q(np.full((n, n), 0.9), CLOTHW))
    put(img, (Y >= 61), Q(0.3 + weave, CLOTHB))
    return img


def wall_cypress() -> np.ndarray:
    n = 128
    X, Y = G(n)
    s = 0.5 + (pn(n, n, 8, 70, 361, 3, 1.2) - 0.5) * 0.45 + (pn(n, n, 22, 22, 362, 2) - 0.5) * 0.18
    s += 0.1 * np.exp(-((Y - 16) / 24.0) ** 2) - 0.06 * (Y / n)
    img = Q(s, CYP)
    rng = np.random.RandomState(363)
    for _ in range(520):  # upswept foliage sprays: dark crown, paler tip, lit where the flame-shaped clump is lit
        x0, y0 = rng.rand() * n, rng.rand() * n
        ln = int(rng.randint(5, 11))
        lean = (rng.rand() - 0.5) * 0.3
        loc = s[int(y0) % n, int(x0) % n]
        for t in range(ln):
            k = t / ln
            sh = np.clip(loc - 0.2 + 0.28 * k, 0, 1)
            pix(img, x0 + lean * t, y0 - t, CYP[int(round(sh * 4))] * 255 + 0.5)
    put(img, speck(n, 0.02, 364), Q(np.full((n, n), 0.0), CYP))
    # the foot of the hedge is in deep shade
    put(img, Y > 112, Q(0.1 + (pn(n, n, 5, 5, 365, 2) - 0.5) * 0.3 + 0.2 * speck(n, 0.1, 366), CYP))
    return img


# ---- ceilings, trim -------------------------------------------------------------------------------------------------------------------------------------

def ceil_beams() -> np.ndarray:
    n = 64
    X, Y = G(n)
    # reed/thatch laid across the rafters: long horizontal strokes in browns and golds
    rs = 0.5 + (pn(n, n, 22, 2.2, 371, 3, 1.7) - 0.5) * 0.6 + (pn(n, n, 10, 10, 372, 2) - 0.5) * 0.2
    img = Q(rs, STRAW)
    put(img, speck(n, 0.06, 373), Q(rs - 0.4, STRAW))
    img = (img.astype(np.float32) * 0.82).astype(np.uint8)
    bx = X % 32
    beam = (bx >= 10) & (bx < 24)
    bs = 0.5 + (pn(n, n, 3, 34, 374, 3, 1.6) - 0.5) * 0.4 + 0.15 * (bx < 12) - 0.2 * (bx >= 21)
    put(img, beam, Q(bs, R("#3e2e20", "#50402e", "#64523c", "#7a6650", "#8e7a62")))
    put(img, beam & ((bx == 10) | (bx == 23)), hexu("#2c2016"))
    put(img, ((bx >= 24) & (bx < 27)), (img.astype(np.float32) * 0.78).astype(np.uint8))  # shadow the beam throws on the thatch
    return img


def ceil_awning() -> np.ndarray:
    n = 64
    X, Y = G(n)
    st = ((X // 16) % 2).astype(int)
    sag = 0.5 + 0.18 * np.cos(2 * np.pi * Y / 32.0 * 1) + 0.07 * np.sin(2 * np.pi * (X / n * 2 + pn(n, n, 32, 32, 381, 2) * 0.6))
    weave = 0.05 * (((X + Y) % 2) - 0.5)
    cream = Q(sag + weave + (pn(n, n, 10, 10, 382, 2) - 0.5) * 0.12, CLOTHW)
    red = Q(sag + weave + (pn(n, n, 10, 10, 383, 2) - 0.5) * 0.12, R("#7a3a2a", "#90472f", "#a65a3a", "#b9704a"))
    img = np.where((st == 1)[..., None], red, cream)
    put(img, (Y % 32) < 2, Q(0.3 + 0.2 * (Y % 32 == 1), CLOTHB))  # seams between cloth widths
    put(img, ((X % 16) == 0) & (st == 0), Q(np.full((n, n), 0.15), CLOTHW))
    return img


def trim() -> np.ndarray:
    n = 64
    X, Y = G(n)
    c = courses(n, [14, 50], 391, 32, 0.0, 0.0, stagger=False)
    s = 0.5 + (c["tone"] - 0.5) * 0.2 + (pn(n, n, 8, 8, 392, 3) - 0.5) * 0.34
    s += 0.14 * (Y < 3) - 0.16 * ((Y >= 11) & (Y < 14)) * 1.0 - 0.1 * (Y > 58)
    img = Q(s, FLAG)
    put(img, (Y >= 14) & (Y < 15), Q(np.full((n, n), 0.1) + (pn(n, n, 4, 4, 393, 2) - 0.5) * 0.4, FLAGJ))  # the nosing's lower edge
    put(img, (X % 32 < 1) & (Y >= 15), Q(np.full((n, n), 0.2) + (pn(n, n, 4, 4, 394, 2) - 0.5) * 0.3, FLAGJ))
    put(img, speck(n, 0.03, 395), Q(s - 0.3, FLAG))
    return img


# ---- skies -----------------------------------------------------------------------------------------------------------------------------------------------
# A sky strip is drawn for the engine's sky at infinity (StoryWorld.sky_params): 1024 x 128 texels wrapping the horizon ONCE, so a texel is 0.35 degrees (about 2.4 pixels of the 360-line
# picture). The map says `sky.horizon` 0.75: row 96 is eye level, 96 rows (34 degrees) of sky above it and 32 rows (11 degrees) of ground or water below. Column 0 is straight ahead
# (the camera looks along -z), +x is to the right. Nothing is soft: a star is one texel or a small cross, a cloud is three flat tones with a hard edge, the sun and the moon are discs of
# 3 to 5 texels (about 1 to 2 degrees: bigger than the real thing, so that they read), the hills are layers that fade to the horizon haze, and the final step is the 8x8 ordered dither.

SW, SH, HZ = 1024, 128, 96
TEXEL = 360.0 / SW


def _az(deg):
    return (deg / TEXEL) % SW


def _el(deg):
    return HZ - deg / TEXEL


def _grad(stops):
    ys = np.arange(SH)
    rows = np.zeros((SH, 3), np.float32)
    for k in range(3):
        rows[:, k] = np.interp(ys, [s[0] for s in stops], [px.hexc(s[1])[k] for s in stops])
    return np.repeat(rows[:, None, :], SW, axis=1)


def _lerp(a, b, t):
    return a * (1 - t) + b * t


def _ridge(seed, base, amp, harm=(2, 3, 5, 8, 13, 21), step=0, peaks=(), floor=1.0):
    """Height in rows above the horizon for every column: a sum of sines (whole cycles, so it wraps), optional terraces (`step`) and peaks (cx, height, width)."""
    rng = np.random.RandomState(seed)
    x = np.arange(SW, dtype=np.float32)
    h = np.full(SW, base, np.float32)
    for k, f in enumerate(harm):
        h += amp / (1 + k) ** 0.85 * np.sin(2 * np.pi * f * x / SW + rng.rand() * 6.28)
    for cx, ph, wd in peaks:
        h += ph * np.exp(-(wrapd(x, cx, SW) / wd) ** 2)
    if step:
        h = np.round(h / step) * step
    return np.maximum(np.round(h), floor)


def _layer(rgb, h, top_col, base_col, depth):
    """A hill layer: from its crest (colour top_col, a hard edge) down to the horizon, fading to base_col (the haze) over `depth` rows."""
    Y = np.arange(SH, dtype=np.float32)[:, None]
    top = (HZ - h)[None, :]
    m = (Y >= top) & (Y < HZ)
    t = np.clip((Y - top) / depth, 0, 1)[..., None]
    c = _lerp(px.hexc(top_col)[None, None, :], px.hexc(base_col)[None, None, :], t)
    return np.where(m[..., None], c, rgb)


def _glow(rgb, az, el, rx, ry, col, k):
    X, Y = G(SW, SH)
    d = np.sqrt((wrapd(X, _az(az), SW) / rx) ** 2 + ((Y - _el(el)) / ry) ** 2)
    return rgb + px.hexc(col)[None, None, :] * (np.clip(1 - d, 0, 1) ** 2 * k)[..., None]


_LIGHTS = []  # discs painted since the last _finish: the sun keeps its full brightness when the sky is graded down


def _disc(rgb, az, el, r, col, edge=None):
    X, Y = G(SW, SH)
    d = np.hypot(wrapd(X, _az(az), SW), Y - _el(el))
    _LIGHTS.append(d <= r)
    if edge is not None:
        rgb = np.where(((d > r) & (d <= r + 1.0))[..., None], px.hexc(edge)[None, None, :], rgb)
    return np.where((d <= r)[..., None], px.hexc(col)[None, None, :], rgb)


def _moon(rgb, az, el, r, phase, lit="#f2eed2", dark="#2c3556"):
    """A moon disc; phase 1 = full, under 1 = a crescent lit on the right."""
    X, Y = G(SW, SH)
    cx, cy = _az(az), _el(el)
    dx, dy = wrapd(X, cx, SW), Y - cy
    d = np.hypot(dx, dy)
    disc = d <= r
    if phase < 1.0:
        cut = np.hypot(dx + (1.0 - phase) * r * 1.5, dy) <= r * (0.95 + 0.2 * phase)
        lit_m = disc & ~cut
        rgb = np.where(disc[..., None], px.hexc(dark)[None, None, :], rgb)
    else:
        lit_m = disc
    shade = 0.82 + 0.18 * np.clip(0.5 - 0.5 * (dx + dy) / max(r, 1), 0, 1)
    rgb = np.where(lit_m[..., None], px.hexc(lit)[None, None, :] * shade[..., None], rgb)
    if phase >= 0.9:  # a few maria on the full moon
        rng = np.random.RandomState(int(az * 7 + el))
        for _ in range(4):
            ox, oy = (rng.rand() - 0.5) * r, (rng.rand() - 0.5) * r
            rgb = np.where((np.hypot(dx - ox, dy - oy) <= max(r * 0.28, 1.0))[..., None] & lit_m[..., None], px.hexc(lit)[None, None, :] * 0.78, rgb)
    return rgb


def _milky_band(x):
    return 40 + 14 * np.sin(2 * np.pi * x / SW + 1.0) + 5 * np.sin(2 * np.pi * 2 * x / SW + 0.4)


def _milky(rgb, seed, col="#7a8cc4", k=0.22):
    X, Y = G(SW, SH)
    band = np.exp(-(((Y - _milky_band(X)) / 11.0) ** 2)) * (0.35 + 0.9 * pn(SW, SH, 90, 14, seed, 3))
    return rgb + px.hexc(col)[None, None, :] * (band * k)[..., None]


def _stars(rgb, seed, n, top=0, bottom=HZ - 2, band=True, bright=0.12, cols=("#c8d2f2", "#9aa8d8", "#e8e4ff", "#b8c4ec")):
    """Single-texel stars, denser high up and along the Milky Way; a few bright ones as a small cross."""
    rng = np.random.RandomState(seed)
    k = 0
    while k < n:
        x = rng.randint(0, SW)
        y = int(top + (bottom - top) * rng.rand() ** 1.25)
        if band and abs(y - _milky_band(x)) >= 11 and rng.rand() < 0.6:
            continue
        k += 1
        if rng.rand() < bright:
            rgb[y, x] = px.hexc("#f4f4ff")
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rgb[(y + dy) % SH, (x + dx) % SW] = _lerp(rgb[(y + dy) % SH, (x + dx) % SW], px.hexc("#8a98d0"), 0.8)
        else:
            rgb[y, x] = px.hexc(cols[rng.randint(0, len(cols))]) * (0.55 + 0.45 * rng.rand())
    return rgb


def _cumulus(rgb, seed, n, rows, wmin, wmax, lit, mid, shade, hmin=5, hmax=11, keep_clear=None):
    """Fair-weather clouds: a union of a few ellipses with a flat base, three flat tones top to bottom (the bands broken by the ordered dither), a hard edge."""
    rng = np.random.RandomState(seed)
    cl, cm, cs = px.hexc(lit), px.hexc(mid), px.hexc(shade)
    for _ in range(n):
        cx = rng.rand() * SW
        cy = rows[0] + rng.rand() * (rows[1] - rows[0])
        w = int(rng.randint(wmin, wmax + 1))
        hgt = int(rng.randint(hmin, hmax + 1))
        ox_ = [(rng.rand() - 0.5) * w * 1.1 for _ in range(5)]
        rx_ = [w * (0.28 + 0.3 * rng.rand()) for _ in range(5)]
        ry_ = [hgt * (0.55 + 0.6 * rng.rand()) for _ in range(5)]
        nb = int(rng.randint(3, 6))
        if keep_clear is not None and abs(wrapd(cx, _az(keep_clear[0]), SW)) < keep_clear[1]:
            continue
        x0, x1, y0, y1 = int(cx - w), int(cx + w), int(cy - hgt * 2), int(cy + 3)
        xs = np.arange(x0, x1 + 1)
        ys = np.arange(y0, y1 + 1)
        dx = xs[None, :] - cx
        dy = ys[:, None] - cy
        m = np.zeros((len(ys), len(xs)), bool)
        for b in range(nb):
            m |= ((dx - ox_[b]) / rx_[b]) ** 2 + ((dy + ry_[b] * 0.35) / ry_[b]) ** 2 <= 1.0
        m &= dy <= 0
        m &= (ys[:, None] >= 0) & (ys[:, None] < HZ - 3)
        top = np.where(m.any(0), m.argmax(0), 0)
        v = (np.arange(len(ys))[:, None] - top[None, :]) / max(hgt * 1.7, 1)
        bay = BAYER[ys[:, None] % 8, xs[None, :] % 8] * 0.25
        tone = np.clip(v + bay, 0, 1)
        col = np.where((tone < 0.3)[..., None], cl, np.where((tone < 0.68)[..., None], cm, cs))
        yy = ys[:, None] % SH
        xx = xs[None, :] % SW
        rgb[yy, xx] = np.where(m[..., None], col, rgb[yy, xx])
    return rgb


def _cirrus(rgb, seed, n, rows, wmin, wmax, col, k=0.7):
    """Thin streaks: one or two texels high, broken into dashes."""
    rng = np.random.RandomState(seed)
    c = px.hexc(col)
    for _ in range(n):
        cx = rng.rand() * SW
        y = int(rows[0] + rng.rand() * (rows[1] - rows[0]))
        w = int(rng.randint(wmin, wmax + 1))
        for i in range(-w, w + 1):
            if rng.rand() < 0.72 - 0.5 * abs(i) / w:
                x = int(cx + i) % SW
                rgb[y % SH, x] = _lerp(rgb[y % SH, x], c, k)
                if rng.rand() < 0.3:
                    rgb[(y + 1) % SH, x] = _lerp(rgb[(y + 1) % SH, x], c, k * 0.6)
    return rgb


def _ground(rgb, top_col, bot_col, seed, spec_col=None, density=0.0, water=False, glint_col=None):
    """The rows under the horizon: a gradient from the haze at eye level to the ground (or water) colour, with specks (bushes, boulders) or glints (water)."""
    Y = np.arange(SH, dtype=np.float32)[:, None]
    t = np.clip((Y - HZ) / (SH - HZ - 1), 0, 1)[..., None] ** 0.7
    c = _lerp(px.hexc(top_col)[None, None, :], px.hexc(bot_col)[None, None, :], t)
    rgb = np.where((Y >= HZ)[..., None], c, rgb)
    rng = np.random.RandomState(seed)
    if spec_col is not None and density > 0:
        for _ in range(int(density * SW * (SH - HZ))):
            x, y = rng.randint(0, SW), HZ + int((rng.rand() ** 1.6) * (SH - HZ))
            rgb[y, x] = px.hexc(spec_col) * (0.8 + 0.4 * rng.rand())
            if rng.rand() < 0.5:
                rgb[y, (x + 1) % SW] = px.hexc(spec_col) * 0.9
    if water and glint_col is not None:
        for _ in range(int(0.012 * SW * (SH - HZ))):
            x, y = rng.randint(0, SW), HZ + 1 + int((rng.rand() ** 1.5) * (SH - HZ - 1))
            for i in range(int(rng.randint(1, 4 + (y - HZ) // 6))):
                rgb[y, (x + i) % SW] = _lerp(rgb[y, (x + i) % SW], px.hexc(glint_col), 0.75)
    return rgb


def _finish(rgb, levels: int = 20, gain: float = 1.0) -> np.ndarray:
    """gain: the exposure of the strip (the sky is not lit by the sector, so a daylight sky is graded down to the style guide's value range)."""
    b = BAYER[np.arange(SH)[:, None] % 8, np.arange(SW)[None, :] % 8][..., None]
    g = np.full((SH, SW, 1), gain, np.float32)
    for m in _LIGHTS:
        g[m] = 1.0
    _LIGHTS.clear()
    v = np.clip(rgb * g, 0.04, 0.93) * (levels - 1) + b
    return (np.clip(np.round(v), 0, levels - 1) / (levels - 1) * 255 + 0.5).astype(np.uint8)


def sky_day() -> np.ndarray:
    """The Judean day: a deep blue overhead going to a dusty haze, fair-weather clouds, a sun to the right, three layers of hills (blue far, grey mid, ochre near)."""
    rgb = _grad([(0, "#123c96"), (40, "#2a6cc0"), (70, "#58a2de"), (88, "#b4d6e4"), (96, "#e2dcc0")])
    rgb = _cirrus(rgb, 501, 6, (50, 84), 12, 36, "#e8f0f4", 0.55)
    rgb = _glow(rgb, 30, 24, 90, 90, "#ffd890", 0.75)
    rgb = _disc(rgb, 30, 24, 4.2, "#fff6c8")
    rgb = _cumulus(rgb, 502, 13, (40, 76), 16, 40, "#f4f6f2", "#d4dfe6", "#a2b8cc", keep_clear=(30, 36))
    rgb = _layer(rgb, _ridge(511, 16, 4.6, peaks=[(40, 8, 30), (610, 11, 44), (990, 6, 24)]), "#869cbc", "#dcd8c4", 14)
    rgb = _layer(rgb, _ridge(512, 10, 3.2, step=1, peaks=[(300, 4, 30), (820, 5, 20)]), "#7a8ea6", "#dcd6bc", 9)
    rgb = _layer(rgb, _ridge(513, 5, 1.8, harm=(3, 7, 12, 19), step=1), "#a39064", "#e0d4b0", 5)
    rgb = _ground(rgb, "#dcc8a0", "#b89a68", 514, "#7a6642", 0.008)
    return _finish(rgb, 20, 0.72)


def sky_lake() -> np.ndarray:
    """The Sea of Galilee: Hermon's snow far to the left, the flat Golan shore across the water, the water itself under the horizon with the sun's glitter."""
    rgb = _grad([(0, "#143e9a"), (38, "#2c70c4"), (68, "#5eaae2"), (88, "#b8dae8"), (96, "#d4e4e4")])
    rgb = _cirrus(rgb, 521, 5, (50, 84), 12, 36, "#e8f0f4", 0.5)
    rgb = _glow(rgb, 32, 22, 90, 90, "#ffd890", 0.75)
    rgb = _disc(rgb, 32, 22, 4.2, "#fff6c8")
    rgb = _cumulus(rgb, 522, 11, (42, 80), 16, 38, "#f4f6f2", "#d4e0e8", "#a4bcd0", keep_clear=(32, 36))
    # Hermon: a pale blue mass with a snow cap whose lower edge steps in dithered ledges
    hermon = _ridge(531, 4, 1.2, peaks=[(930, 17, 54), (905, 6, 22)])
    rgb = _layer(rgb, hermon, "#a8bad0", "#dce2dc", 18)
    Y = np.arange(SH)[:, None]
    bay = BAYER[Y % 8, np.arange(SW)[None, :] % 8] * 3.0
    crest = HZ - hermon[None, :]
    snow = (Y >= crest) & (Y < crest + 5 + bay) & (hermon[None, :] > 12)
    rgb = np.where(snow[..., None], px.hexc("#eef2f6")[None, None, :], rgb)
    rgb = _layer(rgb, _ridge(532, 10, 1.2, harm=(2, 3, 6), step=1, peaks=[(150, -3, 40), (700, -2, 60)]), "#a4a47c", "#d8dcc8", 8)
    rgb = _layer(rgb, _ridge(533, 4.5, 1.4, harm=(4, 9, 15), step=1), "#7e8e5c", "#d4dcc4", 4)
    rgb = _ground(rgb, "#cfe0e0", "#7aa0b8", 534, water=True, glint_col="#eef4f4")
    rng = np.random.RandomState(535)  # the sun's glitter: a column of bright dashes under the sun
    for y in range(HZ + 1, SH):
        for _ in range(3):
            rgb[y, int(_az(32) + rng.randn() * (2 + (y - HZ) * 0.35)) % SW] = px.hexc("#fff6d8")
    return _finish(rgb, 20, 0.72)


def sky_dawn() -> np.ndarray:
    """Dawn over the Jordan valley: the sun just clear of the far hills, a glow in dithered steps, clouds lit from under, purple hills of Moab."""
    rgb = _grad([(0, "#1c2866"), (28, "#3c3c88"), (56, "#9c5a88"), (78, "#e48a74"), (90, "#f6b87a"), (96, "#fadc9c")])
    rgb = _glow(rgb, -10, 3, 210, 60, "#ffc47a", 0.8)
    rgb = _glow(rgb, -10, 2, 60, 30, "#fff0b8", 0.7)
    rgb = _cumulus(rgb, 541, 12, (44, 86), 18, 44, "#f4a898", "#c07084", "#6a4a82", hmin=3, hmax=7)
    rgb = _cirrus(rgb, 542, 6, (50, 84), 14, 40, "#f6c0a8", 0.6)
    rgb = _disc(rgb, -10, 3.6, 4.2, "#fff4c4", "#ffd890")
    rgb = _layer(rgb, _ridge(543, 13, 3.8, peaks=[(430, 8, 40), (760, 11, 30)]), "#7e5c92", "#f0b890", 12)
    rgb = _layer(rgb, _ridge(544, 7, 2.4, step=1), "#5e4680", "#eeb08c", 8)
    rgb = _layer(rgb, _ridge(545, 2.4, 1.2, harm=(3, 8, 14)), "#443468", "#e8a888", 4)
    rgb = _ground(rgb, "#f2c08c", "#9c6e62", 546, "#5a4468", 0.004)
    return _finish(rgb, 20, 1.02)


def sky_morning() -> np.ndarray:
    """A clear morning in the hill country: a pale blue going to gold, a low sun, olive-green hills in layers."""
    rgb = _grad([(0, "#5a94d4"), (34, "#86b8e4"), (66, "#c4d8d0"), (88, "#f0e4bc"), (96, "#f6e8b8")])
    rgb = _glow(rgb, 32, 9, 100, 80, "#ffd890", 0.7)
    rgb = _disc(rgb, 32, 9, 4.2, "#fff6c8")
    rgb = _cumulus(rgb, 551, 9, (46, 78), 16, 36, "#fbf4e0", "#e4dcc4", "#bcb8a8", hmin=4, hmax=8, keep_clear=(32, 30))
    rgb = _cirrus(rgb, 552, 4, (52, 84), 12, 36, "#f6f0dc", 0.5)
    rgb = _layer(rgb, _ridge(553, 13, 3.8, peaks=[(60, 7, 30), (560, 9, 36)]), "#a6aa7c", "#f0e4b8", 12)
    rgb = _layer(rgb, _ridge(554, 8, 2.6), "#8a9250", "#eee0b0", 8)
    rgb = _layer(rgb, _ridge(555, 3, 1.4, harm=(3, 8, 14, 22)), "#6e8040", "#ecdca8", 5)
    rgb = _ground(rgb, "#f0e2ac", "#9a9c5c", 556, "#5a6a30", 0.008)
    return _finish(rgb, 20, 0.72)


def sky_dusk() -> np.ndarray:
    """Sunset: the sun half down behind the hills, an orange glow, red-lit clouds, purple layers."""
    rgb = _grad([(0, "#241c52"), (30, "#48306a"), (58, "#a04068"), (80, "#e0683e"), (92, "#f4a04c"), (96, "#f8c070")])
    rgb = _glow(rgb, 24, 2, 220, 60, "#ffb060", 0.8)
    rgb = _glow(rgb, 24, 2, 64, 30, "#ffe090", 0.6)
    rgb = _cumulus(rgb, 561, 12, (42, 84), 18, 46, "#f28a68", "#bc5668", "#582e66", hmin=3, hmax=8)
    rgb = _cirrus(rgb, 562, 6, (50, 84), 14, 40, "#f4a078", 0.6)
    rgb = _disc(rgb, 24, 2.2, 5.0, "#ffe8a8", "#ffb868")
    rgb = _layer(rgb, _ridge(563, 13, 3.8, peaks=[(120, 8, 36), (700, 10, 30)]), "#74406c", "#f0a060", 12)
    rgb = _layer(rgb, _ridge(564, 7, 2.4, step=1), "#52305a", "#e89258", 8)
    rgb = _layer(rgb, _ridge(565, 2.4, 1.2, harm=(3, 8, 14)), "#342244", "#e08450", 4)
    rgb = _ground(rgb, "#ea9c52", "#5e3c44", 566, "#2e1e3a", 0.006)
    return _finish(rgb, 20, 1.08)


def sky_night() -> np.ndarray:
    """The shepherds' night: the Milky Way, single-texel stars and a few small crosses, a crescent moon, black-blue hills with a shepherd's fire or two."""
    rgb = _grad([(0, "#080e2c"), (40, "#121e4c"), (78, "#223268"), (96, "#3a4c84")])
    rgb = _milky(rgb, 572)
    rgb = _stars(rgb, 573, 900)
    rgb = _glow(rgb, -24, 20, 40, 8, "#8a9ad0", 0.22)
    rgb = _moon(rgb, -24, 20, 3.6, 0.42)
    rgb = _layer(rgb, _ridge(574, 13, 3.8, peaks=[(60, 8, 34), (640, 10, 30)]), "#222e5c", "#3a4c84", 12)
    rgb = _layer(rgb, _ridge(575, 7, 2.4, step=1), "#182248", "#34467c", 8)
    near = _ridge(576, 2.6, 1.3, harm=(3, 8, 14))
    rgb = _layer(rgb, near, "#10173a", "#2e4072", 4)
    for fx, fy in ((120, 3), (333, 2), (560, 4), (801, 3), (950, 2)):  # lit windows and fires on the far slopes
        y = int(HZ - near[fx] + fy)
        rgb[y, fx] = px.hexc("#ffb458")
        if fx % 2:
            rgb[y, fx + 1] = px.hexc("#e08a3c")
    rgb = _ground(rgb, "#3a4c84", "#101a3c", 577, "#2a3a70", 0.004)
    return _finish(rgb, 24, 1.4)


def sky_grove() -> np.ndarray:
    """Gethsemane: a full moon, fewer stars, and the city across the valley (wall, towers, the Temple platform) in the moon's pale blue with a few lit windows."""
    rgb = _grad([(0, "#0a1030"), (40, "#16245a"), (78, "#2a3a74"), (96, "#445890")])
    rgb = _milky(rgb, 582, k=0.12)
    rgb = _stars(rgb, 583, 380, bright=0.08)
    rgb = _glow(rgb, 24, 22, 70, 12, "#9aaee0", 0.32)
    rgb = _moon(rgb, 24, 22, 4.4, 1.0)
    rgb = _layer(rgb, _ridge(584, 11, 3.2, peaks=[(230, 7, 40), (700, 9, 36)]), "#24305e", "#445890", 11)
    rng = np.random.RandomState(586)
    h = _ridge(585, 5, 1.0, harm=(3, 7)).astype(np.float32)
    x = 930
    blocks = []
    while x < 930 + 190:  # the city along the far ridge, ahead and a little to the left: blocks of different height
        w = int(rng.randint(5, 13))
        hh = int(rng.randint(2, 8))
        blocks.append((x % SW, w))
        for i in range(w):
            h[(x + i) % SW] = max(h[(x + i) % SW], 5 + hh)
        x += w
    for cx, w, hh in ((955, 6, 15), (1000, 8, 17), (1015, 5, 13), (40, 7, 14)):  # towers
        for i in range(w):
            h[(cx + i) % SW] = 5 + hh
    for i in range(1000, 1024 + 60):  # the Temple platform: a long flat top
        h[i % SW] = max(h[i % SW], 12)
    rgb = _layer(rgb, h, "#5a6a98", "#3a4a80", 6)
    Y = np.arange(SH)[:, None]
    sides = np.zeros((SH, SW), bool)
    for bx, w in blocks:
        sides[:, (bx + w - 1) % SW] = True
    rgb = np.where((sides & (Y >= (HZ - h[None, :])) & (Y < HZ))[..., None], px.hexc("#2c3868")[None, None, :], rgb)
    for _ in range(26):  # lit windows
        wx = int(rng.randint(930, 930 + 200)) % SW
        wy = int(HZ - h[wx] + 2 + rng.randint(0, 6))
        if wy < HZ - 1:
            rgb[wy, wx] = px.hexc("#ffb458")
    rgb = _layer(rgb, _ridge(587, 2.6, 1.2, harm=(3, 8, 14)), "#141c44", "#344678", 4)
    rgb = _ground(rgb, "#445890", "#121c40", 588, "#26346a", 0.004)
    return _finish(rgb, 24, 1.4)


def _deck(rgb, seed, rows, cols, ths, sx, sy):
    """An overcast deck: ragged masses of noise posterised into flat tones (darkest first), hard edges, the thresholds shifted a little by the ordered dither."""
    X, Y = G(SW, SH)
    v = pn(SW, SH, sx, sy, seed, 4, 1.7)
    fade = smooth(Y, rows[0], rows[0] + 12) * (1 - smooth(Y, rows[1] - 14, rows[1]))
    v = v * fade + BAYER[Y.astype(int) % 8, X.astype(int) % 8] * 0.07
    for c, th in zip(cols, ths):
        rgb = np.where((v > th)[..., None], px.hexc(c)[None, None, :], rgb)
    return rgb


def sky_storm() -> np.ndarray:
    """The squall on the lake: ragged cloud decks in dark tones with paler bellies, thin sick-yellow seams, curtains of rain under the clouds, black hills and rough water under the horizon."""
    rgb = _grad([(0, "#161c1e"), (26, "#232d2d"), (58, "#394540"), (84, "#566250"), (96, "#6c7860")])
    rgb = _deck(rgb, 591, (0, 74), ("#1c2422", "#2a3430", "#3a4640", "#4e5a50"), (0.34, 0.46, 0.56, 0.66), 150, 20)
    rgb = _deck(rgb, 592, (30, 90), ("#3a4640", "#4c584e", "#5e6a5c"), (0.5, 0.6, 0.7), 90, 12)
    rng = np.random.RandomState(593)
    for k in range(3):  # seams of sick light under the cloud base
        yy = 74 + 5 * k
        noise = pn(SW, 8, 70, 4, 600 + k, 2)[3]
        for x in range(SW):
            if noise[x] > 0.55 and x % 3 != 0:
                y = yy + int(1.5 * np.sin(x / 40.0 + k))
                rgb[y, x] = _lerp(rgb[y, x], px.hexc("#b4b45a"), 0.7)
    for cx in (60, 330, 640, 870):  # rain curtains: short dashes falling from the cloud base to the horizon
        wid = int(rng.randint(26, 44))
        for _ in range(int(wid * 9)):
            x = int(cx + (rng.rand() - 0.5) * wid)
            y = int(62 + rng.rand() * (HZ - 66))
            for i in range(3):
                xx, yy2 = (x - i // 2) % SW, y + i
                rgb[yy2, xx] = _lerp(rgb[yy2, xx], px.hexc("#8a9a96"), 0.55)
    rgb = _layer(rgb, _ridge(594, 12, 3.2, peaks=[(200, 7, 40)]), "#3a4a46", "#5c6a58", 8)
    rgb = _layer(rgb, _ridge(595, 3.2, 1.2, harm=(3, 8, 14), step=1), "#26322e", "#4e5c4c", 4)
    rgb = _ground(rgb, "#6c7860", "#2a3630", 596, water=True, glint_col="#a8b4a6")
    return _finish(rgb, 22)


# ---- build -----------------------------------------------------------------------------------------------------------------------------------------------

TILES = [
    ("floor_sand", floor_sand, 1.25), ("floor_dust", floor_dust, 1.25), ("floor_path", floor_path, 1.25), ("floor_grass", floor_grass, 1.25),
    ("floor_shingle", floor_shingle, 1.25), ("floor_water", floor_water, 1.3), ("floor_cobble", floor_cobble, 1.2), ("floor_flag", floor_flag, 1.2),
    ("floor_plank", floor_plank, 2.0), ("floor_clay", floor_clay, 1.25), ("floor_soil", floor_soil, 1.25), ("floor_rock", floor_rock, 1.25),
    ("floor_road", floor_road, 1.25), ("floor_straw", floor_straw, 1.5), ("floor_garden", floor_garden, 1.25),
    ("wall_limestone", wall_limestone, 1.2), ("wall_mudbrick", wall_mudbrick, 1.2), ("wall_rock", wall_rock, 1.2), ("wall_hill", wall_hill, 1.2),
    ("wall_reeds", wall_reeds, 1.2), ("wall_city", wall_city, 1.2), ("wall_door", wall_door, 3.0), ("wall_arch", wall_arch, 4.0),
    ("wall_timber", wall_timber, 2.5), ("wall_olive", wall_olive, 1.2), ("wall_stable", wall_stable, 2.5), ("wall_columns", wall_columns, 5.0),
    ("wall_praetorium", wall_praetorium, 1.2), ("wall_cloth", wall_cloth, 3.0), ("wall_cypress", wall_cypress, 1.2),
    ("ceil_beams", ceil_beams, 2.0), ("ceil_awning", ceil_awning, 2.0), ("trim", trim, 1.0),
    ("sky_dawn", sky_dawn, 1.0), ("sky_day", sky_day, 1.0), ("sky_dusk", sky_dusk, 1.0), ("sky_night", sky_night, 1.0), ("sky_storm", sky_storm, 1.0),
    ("sky_morning", sky_morning, 1.0), ("sky_lake", sky_lake, 1.0), ("sky_grove", sky_grove, 1.0),
]


def grade(rgb: np.ndarray, k: float = 1.8, pivot: float = 0.56) -> np.ndarray:
    """Daylight contrast for a surface tile: luminance is stretched about `pivot` (lights stay, shade goes deep) with the hue kept, so a sunlit wall is bright and its stones and joints are in shade."""
    f = rgb.astype(np.float32) / 255.0
    lum = (f * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
    nl = np.clip(pivot + (lum - pivot) * k, 0.03, 0.97)
    out = np.clip(f * (nl / np.maximum(lum, 1e-3)), 0, 1)
    return (out * 255 + 0.5).astype(np.uint8)


def build(out_dir: str) -> dict:
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    out: dict = {}
    for name, fn, metres in TILES:
        rgb = fn()
        if name.startswith(("floor_", "wall_")) and name not in ("floor_water",):
            rgb = grade(rgb, 2.3, 0.52) if name.startswith("floor_") else grade(rgb)
        assert rgb.dtype == np.uint8 and rgb.ndim == 3 and rgb.shape[2] == 3, name
        im = Image.fromarray(rgb, "RGB")
        if len(np.unique(rgb.reshape(-1, 3), axis=0)) <= 256:  # a few-colour strip or tile is saved as an indexed PNG (a fraction of the bytes, the same pixels)
            pim = im.convert("P", palette=Image.ADAPTIVE, colors=256)
            if np.array_equal(np.asarray(pim.convert("RGB")), rgb):
                im = pim
        im.save(os.path.join(out_dir, name + ".png"), optimize=True, compress_level=9)
        out[name] = {"size": [int(rgb.shape[1]), int(rgb.shape[0])], "metres": float(metres)}
    return out


if __name__ == "__main__":
    print(len(build(sys.argv[1])), "textures written")
