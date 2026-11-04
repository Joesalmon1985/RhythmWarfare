"""Pixel people: every Story Campaign actor drawn as an individual at the internal pixel size, baked to sprite sheets.

docs/STORY_25D_ART_DIRECTION.md 2.E. An actor's look comes from `wardrobe.py` (build, skin, hair, face, clothes, accessories, chosen from the actor's seed and the
chapter's wardrobe); its poses come from the live rig (`StoryCharacter.sample`, dumped by tools/story/dump_poses.gd into assets/story/people_poses.json). This module
is the pixel rig: a skeleton with naturalistic proportions (a head is about a seventh of the height), posed by the dumped limb angles, rasterised straight into
pixels at the sheet size (no vector scaling), each body part shaded in three steps with ordered dithering between them, a one-pixel darker edge of the local
colour instead of an outline, prints, stripes and checks on the clothes, hair drawn in strands, and the props in the hand.

The sheets are indexed: a pixel is (material << 2 | shade step), +128 on the silhouette's rim, 0 is transparent. Each actor has its own palette row (32 materials
x 4 steps, written by `palette_row`), so the runtime shader (src/story/story_people.gdshader) colours, lights and fogs the figure: a back-row figure is darkened
towards the chapter's fog with its rim lit, the front row is shown in full. Three facings (front, a three-quarter turn that the runtime mirrors, back) and three
levels of detail (the full size, a half and a quarter, each drawn at its own size so a far figure is still clean pixels). Everything is deterministic.
"""
from __future__ import annotations

import math

import numpy as np

# ---- materials (5 bits) and shade steps (2 bits) --------------------------------------------------------------------------------------------------------

MATS = ["none", "skin", "skin2", "hair", "hair2", "top", "top2", "top3", "outer", "outer2", "bottom", "bottom2", "shoes", "shoes2", "hat", "hat2",
        "acc", "acc2", "eye_w", "eye_d", "mouth", "teeth", "prop", "prop2", "lit", "metal", "glass", "liquid", "furn", "furn2", "horn", "extra"]
M = {n: i for i, n in enumerate(MATS)}
EMISSIVE = {"lit"}
EDGE, DARK, MID, LIT = 0, 1, 2, 3
RIM = 128

H0 = 112  # the standing height in sheet pixels of a build-1.0 adult at the full level of detail
LODS = (1, 2, 4)  # the levels of detail: full, half, quarter size
FACINGS = ("front", "side", "back")
SIDE_DEG = 52.0  # the three-quarter turn (towards screen right; the runtime mirrors it for the left)

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) / 16.0 - 0.47


# ---- colour ----------------------------------------------------------------------------------------------------------------------------------------------

def _hex(c: str):
    c = c.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


def _to_hex(v) -> str:
    v = np.clip(np.asarray(v, dtype=np.float64), 0.0, 1.0)
    return "#" + "".join(f"{int(round(x * 255)):02x}" for x in v)


def _rgb_hsv(c):
    r, g, b = c
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    h = 0.0
    if d > 1e-9:
        if mx == r:
            h = ((g - b) / d) % 6
        elif mx == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h /= 6.0
    s = 0.0 if mx < 1e-9 else d / mx
    return h, s, mx


def _hsv_rgb(h, s, v):
    h = (h % 1.0) * 6.0
    i = int(h) % 6
    f = h - int(h)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    return np.array([(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i])


def _shift_hue(h, target, amount):
    d = ((target - h + 0.5) % 1.0) - 0.5
    return h + d * amount


def ramp(base: str) -> list:
    """The four steps of one material: edge, dark, mid (the colour itself), lit. Shadows lean cool (towards violet), lights lean warm, as hand shading does."""
    c = _hex(base)
    h, s, v = _rgb_hsv(c)
    lit_h = _shift_hue(h, 0.12, 0.10)
    lit = _hsv_rgb(lit_h, max(0.0, s * 0.86), min(1.0, v * 1.14 + 0.07))
    dk_h = _shift_hue(h, 0.72, 0.16)
    dark = _hsv_rgb(dk_h, min(1.0, s * 1.08 + 0.06), v * 0.68)
    edge = _hsv_rgb(_shift_hue(h, 0.72, 0.1), min(1.0, s * 1.05 + 0.05), v * 0.48)
    return [_to_hex(edge), _to_hex(dark), _to_hex(c), _to_hex(lit)]


UNDERTONE = {"warm": (0.03, 0.06), "neutral": (0.0, 0.02), "olive": (0.1, -0.04), "cool": (0.95, 0.0)}


def skin_ramp(base: str, tone: str = "warm") -> list:
    """The four steps of a human skin: shadows warm and a little more saturated (blood under the skin: towards red, or towards rose for a cool undertone,
    olive towards a green-gold), never grey or violet; the light step a warm, slightly desaturated sheen. A skin outside the human range (an alien, a demon)
    keeps the cloth ramp."""
    c = _hex(base)
    h, s, v = _rgb_hsv(c)
    if not (h < 0.13 or h > 0.93) or s < 0.12 or s > 0.8:
        return ramp(base)
    th, ds = UNDERTONE.get(tone, UNDERTONE["warm"])
    dark_h = _shift_hue(h, th if tone != "olive" else 0.085, 0.3)
    dark = _hsv_rgb(dark_h, min(1.0, s * 1.08 + 0.04 + ds), v * 0.77)
    edge = _hsv_rgb(_shift_hue(dark_h, 0.99, 0.3), min(1.0, s * 1.18 + 0.08), v * 0.56)
    lit = _hsv_rgb(_shift_hue(h, 0.09, 0.25), max(0.0, s * 0.78), min(1.0, v * 1.1 + 0.06))
    return [_to_hex(edge), _to_hex(dark), _to_hex(c), _to_hex(lit)]


def palette_row(colours: dict) -> list:
    """128 RGBA tuples (material x step) for one actor; alpha 255, 254 marks an emissive material (the shader does not light it)."""
    row = []
    for name in MATS:
        base = colours.get(name, "#ff00ff")
        steps = skin_ramp(base, colours.get("skin_tone", "warm")) if name == "skin" and "skin_tone" in colours else ramp(base)
        for st in steps:
            r, g, b = (int(st[i:i + 2], 16) for i in (1, 3, 5))
            row.append((r, g, b, 254 if name in EMISSIVE else 255))
    return row


# ---- the canvas ------------------------------------------------------------------------------------------------------------------------------------------

class Canvas:
    """One frame being drawn: per pixel a material, a continuous shade (0 dark .. 1 lit), a depth and a part id. Rig space: x right, y down, the origin at the
    feet; `px` maps it to pixel centres."""

    def __init__(self, w: int, h: int, ox: float, oy: float):
        self.w, self.h, self.ox, self.oy = w, h, ox, oy
        self.mat = np.zeros((h, w), np.uint8)
        self.sh = np.zeros((h, w), np.float32)
        self.z = np.full((h, w), -1e9, np.float32)
        self.pid = np.zeros((h, w), np.int16)
        self.fixed = np.zeros((h, w), np.int8) - 1  # a forced shade step (details: eyes, mouth, print lines); -1 = from the shade
        self.nodither = np.zeros((h, w), bool)  # the face's skin: shaded in clean steps, no dither noise across the features
        ys, xs = np.mgrid[0:h, 0:w]
        self.X = xs.astype(np.float32) + 0.5 - ox
        self.Y = ys.astype(np.float32) + 0.5 - oy
        self.next_pid = 1

    def region(self, x0, y0, x1, y1):
        c0 = max(0, int(math.floor(x0 + self.ox)) - 1)
        c1 = min(self.w, int(math.ceil(x1 + self.ox)) + 2)
        r0 = max(0, int(math.floor(y0 + self.oy)) - 1)
        r1 = min(self.h, int(math.ceil(y1 + self.oy)) + 2)
        if c1 <= c0 or r1 <= r0:
            return None
        return (slice(r0, r1), slice(c0, c1))

    def put(self, sl, mask, mat, shade, z, pid=None, fixed=None):
        if sl is None:
            return
        zz = self.z[sl]
        m = mask & (z >= zz)
        if isinstance(mat, np.ndarray):
            m &= mat > 0
        elif mat == 0:
            return
        if not m.any():
            return
        if pid is None:
            pid = self.next_pid
            self.next_pid += 1
        self.mat[sl] = np.where(m, mat, self.mat[sl])
        self.sh[sl] = np.where(m, shade, self.sh[sl])
        zz[m] = z
        self.pid[sl] = np.where(m, pid, self.pid[sl])
        if fixed is None:
            self.fixed[sl] = np.where(m, -1, self.fixed[sl])
        else:
            self.fixed[sl] = np.where(m, fixed, self.fixed[sl])
        return pid

    def dot(self, x, y, mat, step, z):
        """One pixel at rig point (x, y) (a detail: an eye, a button)."""
        c = int(math.floor(x + self.ox))
        r = int(math.floor(y + self.oy))
        if 0 <= c < self.w and 0 <= r < self.h and z >= self.z[r, c] - 0.6:
            self.mat[r, c] = M[mat] if isinstance(mat, str) else mat
            self.fixed[r, c] = step
            self.z[r, c] = max(self.z[r, c], z)

    def solid(self, x, y):
        c = int(math.floor(x + self.ox))
        r = int(math.floor(y + self.oy))
        return 0 <= c < self.w and 0 <= r < self.h and self.mat[r, c] != 0


def lambert_u(u):
    """Shade across a round body part: u -1 (the left edge, towards the light) .. 1 (the right edge)."""
    u = np.clip(u, -1.0, 1.0)
    return np.clip(0.6 - 0.42 * u + 0.3 * (np.sqrt(1.0 - u * u) - 0.6), 0.0, 1.0)


# ---- primitives -----------------------------------------------------------------------------------------------------------------------------------------

def capsule(cv: Canvas, p0, p1, r0, r1, z, matfn, pid=None, shade_bias=0.0):
    """A tapered limb from p0 (radius r0) to p1 (radius r1). matfn(t, u) gives the material per pixel (t 0..1 along, u -1..1 across) and may return
    (mat, extra_shade). Returns the part id."""
    x0, y0 = p0
    x1, y1 = p1
    rr = max(r0, r1)
    sl = cv.region(min(x0, x1) - rr, min(y0, y1) - rr, max(x0, x1) + rr, max(y0, y1) + rr)
    if sl is None:
        return None
    X, Y = cv.X[sl], cv.Y[sl]
    dx, dy = x1 - x0, y1 - y0
    ln2 = dx * dx + dy * dy or 1e-6
    t = np.clip(((X - x0) * dx + (Y - y0) * dy) / ln2, 0.0, 1.0)
    cx, cy = x0 + dx * t, y0 + dy * t
    rad = r0 + (r1 - r0) * t
    ex, ey = X - cx, Y - cy
    dist = np.sqrt(ex * ex + ey * ey)
    inside = dist <= rad + 0.02
    ln = math.sqrt(ln2)
    nx, ny = -dy / ln, dx / ln
    if nx > 0 or (nx == 0 and ny > 0):  # u runs screen left to right whatever the limb's direction
        nx, ny = -nx, -ny
    u = (ex * -nx + ey * -ny) / np.maximum(rad, 0.5)
    mat, extra = _matfn(matfn, t, u)
    shade = lambert_u(u) + extra + shade_bias
    return cv.put(sl, inside, mat, shade, z, pid)


def _matfn(fn, *args):
    out = fn(*args)
    if isinstance(out, tuple):
        return out
    return out, 0.0


def ellipse(cv: Canvas, c, rx, ry, ang, z, matfn, pid=None, shape=None):
    """An ellipse (the head, a foot, a hand) rotated by ang; matfn(lx, ly, u, v) with u, v in -1..1 of the ellipse. `shape(u, v)` may move the edge (a jaw)."""
    rr = max(rx, ry) + 1
    sl = cv.region(c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr)
    if sl is None:
        return None
    X, Y = cv.X[sl] - c[0], cv.Y[sl] - c[1]
    ca, sa = math.cos(ang), math.sin(ang)
    lx = X * ca + Y * sa
    ly = -X * sa + Y * ca
    u, v = lx / rx, ly / ry
    r2 = u * u + v * v
    lim = 1.0 if shape is None else shape(u, v)
    inside = r2 <= lim
    mat, extra = _matfn(matfn, lx, ly, u, v)
    nz = np.sqrt(np.clip(1.0 - r2, 0.0, 1.0))
    shade = np.clip(0.62 - 0.4 * u - 0.22 * v + 0.28 * (nz - 0.6), 0.0, 1.0) + extra
    return cv.put(sl, inside, mat, shade, z, pid)


def profile(cv: Canvas, origin, ang, rows, z, matfn, pid=None, shift=0.0):
    """A body (torso, skirt, coat) given as half-widths down its local axis: rows = [(ly, half_left, half_right), ...] (ly increasing downwards), rotated by
    ang about `origin`. matfn(lx, ly, u) with u -1..1 across at that height. `shift` moves the middle sideways (a three-quarter turn)."""
    ys = [r[0] for r in rows]
    hw = max(max(r[1], r[2]) for r in rows) + abs(shift) + 2
    corners = [(-hw, ys[0]), (hw, ys[0]), (-hw, ys[-1]), (hw, ys[-1])]
    ca, sa = math.cos(ang), math.sin(ang)
    pts = [(origin[0] + x * ca - y * sa, origin[1] + x * sa + y * ca) for x, y in corners]
    sl = cv.region(min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
    if sl is None:
        return None
    X, Y = cv.X[sl] - origin[0], cv.Y[sl] - origin[1]
    lx = X * ca + Y * sa - shift
    ly = -X * sa + Y * ca
    hl = np.interp(ly, ys, [r[1] for r in rows])
    hr = np.interp(ly, ys, [r[2] for r in rows])
    inside = (ly >= ys[0]) & (ly <= ys[-1]) & (lx >= -hl) & (lx <= hr)
    u = np.where(lx < 0, lx / np.maximum(hl, 0.5), lx / np.maximum(hr, 0.5))
    mat, extra = _matfn(matfn, lx, ly, u)
    shade = lambert_u(u * 0.95) + extra
    return cv.put(sl, inside, mat, shade, z, pid)


def poly_fill(cv: Canvas, pts, z, mat, shade=0.6, pid=None, fixed=None):
    """A flat polygon (a brim, a prop) in rig space."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    sl = cv.region(min(xs), min(ys), max(xs), max(ys))
    if sl is None:
        return None
    X, Y = cv.X[sl], cv.Y[sl]
    inside = np.zeros(X.shape, bool)
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        cond = ((yi > Y) != (yj > Y)) & (X < (xj - xi) * (Y - yi) / ((yj - yi) or 1e-9) + xi)
        inside ^= cond
        j = i
    sh = shade if not callable(shade) else shade(X, Y)
    m = M[mat] if isinstance(mat, str) else mat
    return cv.put(sl, inside, m, sh, z, pid, fixed)


def seg(cv: Canvas, p0, p1, mat, step, z, width=1.0):
    """A thin line of pixels (a strap, a pole, a drawstring) at a fixed shade step."""
    n = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1])) * 1.5) + 1
    for k in range(n + 1):
        t = k / n
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        cv.dot(x, y, mat, step, z)
        if width > 1.2:
            cv.dot(x + 0.7, y, mat, step, z)


# ---- the finishing pass: shade steps, dither, edges, rim ----------------------------------------------------------------------------------------------

def finish(cv: Canvas) -> np.ndarray:
    """Quantise the shade into dark / mid / lit with an ordered dither between the steps, darken the silhouette's edge by one step (the local colour, never
    black), separate overlapping parts with a one-pixel shadow on the part behind, mark the rim. Returns the index image (uint8)."""
    h, w = cv.mat.shape
    ys, xs = np.mgrid[0:h, 0:w]
    dith = BAYER4[ys % 4, xs % 4] * 0.11
    dith = np.where(cv.nodither & ((cv.mat == M["skin"]) | (cv.mat == M["horn"])), 0.0, dith)
    s = cv.sh + dith
    step = np.where(s > 0.7, LIT, np.where(s > 0.38, MID, DARK)).astype(np.int16)
    step = np.where(cv.fixed >= 0, cv.fixed, step)
    solid = cv.mat > 0
    # a part behind another one gets a one-pixel shadow along the edge it is overlapped by (light from the upper left: the shadow falls down and right)
    z = cv.z
    zl = np.full_like(z, -1e9)
    zl[:, 1:] = z[:, :-1]
    zu = np.full_like(z, -1e9)
    zu[1:, :] = z[:-1, :]
    pl = np.zeros_like(cv.pid)
    pl[:, 1:] = cv.pid[:, :-1]
    pu = np.zeros_like(cv.pid)
    pu[1:, :] = cv.pid[:-1, :]
    shadow = solid & (((zl > z + 0.25) & (pl != cv.pid) & (pl > 0)) | ((zu > z + 0.25) & (pu != cv.pid) & (pu > 0)))
    step = np.where(shadow & (cv.fixed < 0), np.maximum(step - 1, DARK), step)
    # the silhouette's edge: one step darker on the shadow side (right, below), the rim on every outer edge
    def nb(dr, dc):
        out = np.zeros_like(solid)
        r0, r1 = max(0, dr), h + min(0, dr)
        c0, c1 = max(0, dc), w + min(0, dc)
        out[r0:r1, c0:c1] = solid[r0 - dr:r1 - dr, c0 - dc:c1 - dc]
        return out
    left, right, up, down = nb(0, 1), nb(0, -1), nb(1, 0), nb(-1, 0)
    outer = solid & ~(left & right & up & down)
    shadow_side = solid & (~right | ~down)
    step = np.where(outer & shadow_side & (cv.fixed < 0), np.maximum(step - 1, EDGE), step)
    step = np.where(outer & ~shadow_side & (cv.fixed < 0), np.maximum(step - 1, DARK), step)
    idx = (cv.mat.astype(np.int16) << 2) | np.clip(step, 0, 3)
    idx = np.where(solid, idx, 0)
    idx = np.where(outer, idx | RIM, idx)
    return idx.astype(np.uint8)


# ---- the skeleton ------------------------------------------------------------------------------------------------------------------------------------------

def rot(v, a):
    ca, sa = math.cos(a), math.sin(a)
    return (v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca)


def add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k)


REST_UP = math.radians(7.0)
REST_FORE = math.radians(10.0)
SEATED = ("sit", "sleep")
FLOORED = ("rock",)


class Body:
    """The posed skeleton of one person in rig pixels (feet at the origin, y down). fc: 0 front, 1 three-quarter (turned towards screen right), 2 back."""

    def __init__(self, spec: dict, pose: dict, S: float, fc: int, state: str):
        self.spec, self.pose, self.S, self.fc, self.state = spec, pose, S, fc, state
        sp = spec.get("species") or {}
        W = float(spec.get("width", 1.0))
        cu = float(spec.get("curve", 0.5))
        hs = float(spec.get("head", 1.0))
        legs = float(spec.get("legs", 1.0))
        limb = float(spec.get("limb", 1.0))
        self.W, self.cu, self.limb = W, cu, limb
        self.k = math.cos(math.radians(SIDE_DEG)) if fc == 1 else 1.0  # lateral foreshortening
        self.mir = -1.0 if fc == 2 else 1.0  # the back view is the front mirrored (the person's right arm is on screen right)
        # a head about 1/6.8 of the height (the art direction asks 1/6.5 to 1/7): 17 x 13 pixels at the full size, room for a face with eyes, a nose and lips
        wk = float((spec.get("face") or {}).get("wk", 1.0)) if not sp else 1.0
        self.head_h = 0.146 * hs * float(sp.get("head_h", 1.0)) * S
        self.head_w = 0.108 * hs * wk * float(sp.get("head_w", 1.0)) * S
        hip_y = -0.5 * legs * S
        top = -S
        chin = top + self.head_h
        neck = 0.045 * S * float(spec.get("neck", 1.0))
        sh_y = chin + neck
        drop = float(pose.get("head_drop", 0.0)) / 260.0 * S
        self.sit_dy = 0.0
        if state in SEATED:
            self.sit_dy = (-0.27 * S) - hip_y
        elif state in FLOORED:
            self.sit_dy = (-0.06 * S) - hip_y
        dy = self.sit_dy
        self.hip = (0.0, hip_y + dy)
        lean = float(pose.get("lean", 0.0))
        self.lean = lean
        # the torso's own points, relative to the hip joint, then leaned
        sw = 0.125 * W * (1.0 - 0.08 * cu) * S
        self.sw = sw
        self.chest_hw = 0.118 * W * (1.0 - 0.05 * cu) * S
        self.waist_hw = (0.088 - 0.016 * cu) * W * S
        self.hip_hw = (0.092 + 0.014 * cu) * W * S
        self.t_shoulder = sh_y - hip_y + drop * 0.5
        self.t_neck = sh_y - hip_y - 0.01 * S + drop * 0.4
        self.t_chin = chin - hip_y + drop
        self.t_waist = -0.1 * S if legs >= 0.9 else (sh_y - hip_y) * 0.35

        def T(p):  # torso-local point -> rig point
            q = rot(p, lean)
            return (self.hip[0] + q[0], self.hip[1] + q[1])
        self.T = T
        self.neck_base = T((0.0, self.t_neck))
        self.head_c = T((0.0, self.t_chin - self.head_h * 0.5))
        self.head_ang = lean + float(pose.get("head_tilt", 0.0))
        self.head_c = add(self.neck_base, rot((0.0, self.t_chin - self.t_neck - self.head_h * 0.5), self.head_ang))
        self.arms = {}
        for side, sg in (("l", 1.0), ("r", -1.0)):
            a = float(pose.get("arm_" + side, 0.14))
            e = float(pose.get("elb_" + side, 0.2))
            sx = -sg * sw * 0.86
            shp = T((sx, self.t_shoulder + 0.012 * S))
            up_len = 0.17 * S * float(sp.get("arm_len", 1.0))
            fo_len = 0.138 * S * float(sp.get("arm_len", 1.0))
            ud = rot((-sg * math.sin(REST_UP), math.cos(REST_UP)), sg * a + lean)
            fd = rot((-sg * math.sin(REST_FORE), math.cos(REST_FORE)), sg * a - sg * e + lean)
            # three-quarter and back views: the lateral part of every arm vector is foreshortened / mirrored
            shp = (self.hip[0] + (shp[0] - self.hip[0]) * self.k * self.mir, shp[1])
            ud = (ud[0] * self.k * self.mir, ud[1])
            fd = (fd[0] * self.k * self.mir, fd[1])
            el = add(shp, ud, up_len)
            wr = add(el, fd, fo_len)
            hand = add(wr, fd, 0.022 * S)
            self.arms[side] = {"sh": shp, "el": el, "wr": wr, "hand": hand, "fd": fd, "ud": ud}
        self.legs = {}
        for side, sg in (("l", 1.0), ("r", -1.0)):
            lg = float(pose.get("leg_" + side, 0.0))
            hx = -sg * 0.052 * W * S * self.k * self.mir
            hp = (self.hip[0] + hx, self.hip[1])
            ln = -hip_y - 0.045 * S
            if state in SEATED:
                kn = (hx * 1.15 - sg * 0.035 * S * min(lg, 0.8) * self.mir, self.hip[1] + 0.035 * S)
                an = (kn[0] - sg * 0.01 * S, -0.045 * S)
            elif state in FLOORED:
                kn = (hx * 0.6, self.hip[1] - 0.2 * S)
                an = (hx * 0.9 + (-sg * 0.02 * S), -0.04 * S)
            else:
                d = rot((0.0, 1.0), sg * lg)
                d = (d[0] * self.k * self.mir, d[1])
                an = add(hp, d, ln)
                kn = add(hp, d, ln * 0.5)
            self.legs[side] = {"hip": hp, "knee": kn, "ankle": an}
        self.top_y = min(self.head_c[1] - self.head_h * 0.55, min(a["hand"][1] for a in self.arms.values()))


def build_body(spec, pose, S, fc, state) -> Body:
    return Body(spec, pose, S, fc, state)


# ---- small helpers ------------------------------------------------------------------------------------------------------------------------------------------

def _hash01(a, b, seed=0):
    """A stable per-pixel pseudo random value in 0..1 (curls, wear, stubble)."""
    v = np.sin(a * 12.9898 + b * 78.233 + seed * 37.719) * 43758.5453
    return v - np.floor(v)


def _step(S, k, lo=1.0):
    return max(lo, round(k * S))


MOTIFS = ("smiley", "sun", "star", "rings", "heart", "bolt", "diamond", "flower")


def motif_mask(name, mx, my):
    """A chest print as a mask over -1..1 coordinates (True = the print's colour)."""
    r = np.sqrt(mx * mx + my * my)
    a = np.arctan2(my, mx)
    if name == "smiley":
        ring = (r > 0.72) & (r < 1.0)
        eyes = (((mx + 0.35) ** 2 + (my + 0.3) ** 2) < 0.04) | (((mx - 0.35) ** 2 + (my + 0.3) ** 2) < 0.04)
        mouth = (r > 0.38) & (r < 0.58) & (my > 0.12)
        return ring | eyes | mouth
    if name == "sun":
        rays = (r > 0.62) & (r < 1.0) & (np.cos(a * 8) > 0.35)
        return (r < 0.48) | rays
    if name == "star":
        k = np.cos(a * 5 + math.pi / 2) * 0.32 + 0.62
        return r < k
    if name == "rings":
        return (np.floor(r * 3.4) % 2 == 0) & (r < 1.0)
    if name == "heart":
        x, y = mx * 1.1, -my * 1.1 + 0.25
        return (x * x + (y - np.sqrt(np.abs(x)) * 0.8) ** 2) < 0.75
    if name == "bolt":
        return (np.abs(mx + my * 0.45 - np.where(my < 0, 0.18, -0.18)) < 0.26) & (np.abs(my) < 1.0)
    if name == "diamond":
        return (np.abs(mx) + np.abs(my)) < 0.95
    if name == "flower":
        pet = 0.55 + 0.4 * np.cos(a * 5)
        return (r < pet) & ~((r > 0.18) & (r < 0.3))
    return r < 0.8


# ---- the painter ----------------------------------------------------------------------------------------------------------------------------------------

class Painter:
    """Draws one posed person (Body) with their wardrobe (spec) onto a Canvas."""

    def __init__(self, cv: Canvas, b: Body, spec: dict, lod: int, held: str, face: str, seed: int):
        self.cv, self.b, self.sp, self.lod, self.held, self.face, self.seed = cv, b, spec, lod, held, face, seed
        self.S = b.S
        self.species = (spec.get("species") or {}).get("kind", "")
        self.top = spec.get("top") or {"kind": "tee"}
        self.outer = spec.get("outer")
        self.bottom = spec.get("bottom") or {"kind": "trousers"}
        self.shoes = spec.get("shoes") or {"kind": "trainers"}
        self.hat = spec.get("hat")
        self.hair = spec.get("hair") or {"style": "short"}
        self.acc = set(spec.get("acc", []))

    # -- the whole person --
    def draw(self):
        b, S = self.b, self.S
        b.head_c = self.snap(b.head_c)
        st = b.state
        if st in SEATED:
            self.seat()
        self.back_layers()
        for side in self.leg_order():
            self.leg(side)
        self.torso()
        self.lower_garment()
        self.neck()
        for side in self.arm_order():
            self.arm(side)
        self.head()
        self.accessories()
        self.prop()

    def leg_order(self):
        return ["r", "l"] if self.b.fc == 1 else ["l", "r"]

    def arm_order(self):
        return ["r", "l"]

    # -- z of the arms: in front of the torso, behind it in the back view, the far arm of a three-quarter turn behind --
    def arm_z(self, side):
        b = self.b
        if b.fc == 2:
            return 0.6
        if b.fc == 1 and side == "r":
            return -0.8
        a = b.arms[side]
        hx, hy = a["hand"]
        near_face = hy < b.head_c[1] + b.head_h * 0.6 and abs(hx - b.head_c[0]) < b.head_w * 0.9
        return 2.45 if near_face else 1.6

    # -- seat, back layers --
    def seat(self):
        b, S, cv = self.b, self.S, self.cv
        y = b.hip[1] + 0.03 * S
        w = 0.15 * S
        poly_fill(cv, [(-w, y - 0.012 * S), (w, y - 0.012 * S), (w, y + 0.02 * S), (-w, y + 0.02 * S)], -0.5, "furn", 0.55)
        for x in (-w + 0.02 * S, w - 0.02 * S):
            capsule(cv, (x, y + 0.02 * S), (x * 1.05, -0.002 * S), 0.012 * S, 0.01 * S, -0.6, lambda t, u: M["furn2"])
        top = b.T((0.0, b.t_shoulder + 0.05 * S))[1]
        poly_fill(cv, [(-w * 0.85, top), (w * 0.85, top), (w * 0.9, y - 0.01 * S), (-w * 0.9, y - 0.01 * S)], -2.5, "furn",
                  lambda X, Y: 0.35 + 0.25 * (X < 0))

    def back_layers(self):
        b, S, cv, sp = self.b, self.S, self.cv, self.sp
        spc = sp.get("species") or {}
        if self.species in ("insect",) or spc.get("wings"):
            self.wings(spc.get("wings", "case"))
        if spc.get("tail"):
            self.tail()
        if self.outer and self.outer.get("kind") == "cape":
            self.cape()
        self.hair_back()

    # -- legs, feet, bottoms --
    def leg(self, side):
        b, S, cv = self.b, self.S, self.cv
        L = b.legs[side]
        bot = self.bottom.get("kind", "trousers")
        W = b.W * b.limb
        r_hip = (0.062 + 0.012 * b.cu) * W * S
        r_knee = 0.043 * W * S
        r_ank = 0.03 * W * S
        if bot in ("baggy", "flares", "pyjamas"):
            r_knee *= 1.32
            r_ank *= 1.55 if bot != "pyjamas" else 1.3
            r_hip *= 1.1
        if self.species == "skeleton":
            r_hip, r_knee, r_ank = 0.022 * S, 0.02 * S, 0.016 * S
        boots = self.shoes.get("kind") in ("boots", "wellies")
        shorts = bot in ("shorts", "loincloth")
        bare = bot in ("skirt", "gownlegs", "tutu", "dress_legs")
        tights = self.bottom.get("tights", False)
        seed = self.seed

        def mat(t, u, part):
            if bare:
                m = np.full(t.shape, M["bottom2"] if tights else M["skin"], np.uint8)
                ex = np.zeros(t.shape, np.float32)
            elif shorts and part == 1:
                m = np.full(t.shape, M["skin"], np.uint8)
                ex = np.zeros(t.shape, np.float32)
            else:
                m = np.full(t.shape, M["bottom"], np.uint8)
                ex = np.zeros(t.shape, np.float32)
                if shorts:
                    m = np.where(t > 0.85, M["skin"], m)
                if bot in ("jeans", "baggy", "flares"):
                    ex += np.where(np.abs(u + 0.25) < 0.14, 0.18, 0.0)  # the lit seam
                    if part == 1:
                        ex += np.where((t < 0.18) & (_hash01(u * 7, t * 9, seed) > 0.6), 0.14, 0.0)  # worn knee
                if bot in ("baggy", "flares", "pyjamas"):
                    ex -= np.where(np.sin(u * 3.0 + t * 11.0 + seed) > 0.75, 0.3, 0.0)  # folds
                if self.bottom.get("pattern") == "check":
                    q = _step(S, 0.03, 2)
                    gx = (np.floor((u + 1.0) * 2.0) % 2 == 0) ^ (np.floor(t * 0.23 * S / q) % 2 == 0)
                    m = np.where(gx & (m == M["bottom"]), M["bottom2"], m)
                if part == 1 and bot not in ("leggings",):
                    ex -= 0.25 * (t > 0.9)  # the cuff's shadow
            if boots and part == 1:
                m = np.where(t > 0.62, M["shoes"], m)
            return m, ex
        kn, an, hp = L["knee"], L["ankle"], L["hip"]
        z = 0.1 if (b.fc == 1 and side == "l") else 0.0
        if b.state in FLOORED:
            z = 1.8  # knees up in front of the body
        capsule(cv, hp, kn, r_hip, r_knee, z, lambda t, u: mat(t, u, 0))
        capsule(cv, kn, an, r_knee, r_ank, z + 0.05, lambda t, u: mat(t, u, 1))
        if self.species == "skeleton":
            ellipse(cv, kn, r_knee * 1.25, r_knee * 1.1, 0, z + 0.06, lambda *a: M["horn"])
        self.foot(side, an, z + 0.1)

    def foot(self, side, an, z):
        b, S, cv = self.b, self.S, self.cv
        kind = self.shoes.get("kind", "trainers")
        sg = 1.0 if side == "l" else -1.0
        if b.fc == 1:
            c = (an[0] + 0.022 * S, an[1] + 0.012 * S)
            rx, ry = 0.046 * S, 0.02 * S
        else:
            c = (an[0] - sg * 0.008 * S * b.mir, an[1] + 0.013 * S)
            rx, ry = 0.032 * S, 0.02 * S
        if kind == "heels":
            rx *= 0.8
        if kind in ("slippers",):
            rx *= 1.15
            ry *= 1.15
        mat_main = M["skin"] if kind == "bare" else M["shoes"]

        def mat(lx, ly, u, v):
            m = np.full(u.shape, mat_main, np.uint8)
            if kind in ("trainers", "slippers", "clogs"):
                m = np.where(v > 0.45, M["shoes2"], m)  # the sole
            if kind == "trainers":
                m = np.where((np.abs(u + 0.1) < 0.18) & (v < 0.2) & (v > -0.5), M["shoes2"], m)
            return m
        ellipse(cv, c, rx, ry, 0.0, z, mat)

    def lower_garment(self):
        """Skirts, dresses, gowns, tutus and long coats fall over the legs."""
        b, S, cv = self.b, self.S, self.cv
        bot = self.bottom.get("kind")
        top = self.top.get("kind")
        hipw = b.hip_hw
        if b.state in SEATED + FLOORED:
            knee_y = -0.02 * S
        else:
            knee_y = None
        sh = 0.07 * S if b.fc == 1 else 0.0

        def flare(y0, y1, w0, w1, mat, z, hem_mat=None, ragged=False, pattern=None):
            rows = [(y0, w0, w0), (y1, w1, w1)]

            def mf(lx, ly, u):
                m = np.full(u.shape, M[mat], np.uint8)
                ex = -0.2 * (np.sin(lx * 0.9 + self.seed) > 0.55)  # folds
                if hem_mat:
                    m = np.where(ly > y1 - _step(S, 0.018), M[hem_mat], m)
                if pattern == "dots":
                    q = _step(S, 0.04, 3)
                    m = np.where(((np.floor(lx / q) + np.floor(ly / q)) % 2 == 0) & ((np.round(lx) % q == 0) & (np.round(ly) % q == 0)), M["top2"], m)
                if ragged:
                    m = np.where((ly > y1 - 2) & (_hash01(np.round(lx), 1, self.seed) > 0.5), 0, m)
                return m, ex
            return rows, mf, z
        jobs = []
        y_w = b.t_waist + 0.02 * S
        y_kn = (knee_y if knee_y is not None else -0.3 * S) - b.hip[1]
        if top in ("dress", "gown"):
            jobs.append(flare(y_w, y_kn, b.waist_hw * 1.05, hipw * 1.45, "top", 1.2, "top3" if top == "dress" else None,
                              pattern="dots" if top == "gown" else None))
        elif bot == "skirt":
            y_hem = y_kn * float(self.bottom.get("len", 0.85))
            jobs.append(flare(-0.05 * S, y_hem, hipw * 1.02, hipw * 1.38, "bottom", 1.2, "bottom2"))
        elif bot == "tutu":
            jobs.append(flare(-0.04 * S, 0.06 * S, hipw * 1.2, hipw * 2.3, "bottom", 1.25, "bottom2", ragged=True))
        if self.outer and self.outer.get("long") and self.outer.get("kind") != "cape":
            y_hem = (knee_y - b.hip[1] if knee_y is not None else -0.26 * S - b.hip[1])
            gap = 0.035 * S
            rows = [(-0.03 * S, hipw * 1.08, hipw * 1.08), (y_hem, hipw * 1.42, hipw * 1.42)]

            def mf(lx, ly, u, gap=gap):
                m = np.where(np.abs(lx - sh * 0.4) < gap + (ly / S) * 0.06 * S, 0, M["outer"]).astype(np.uint8)
                if self.outer.get("trim"):
                    m = np.where((m > 0) & (np.abs(np.abs(lx - sh * 0.4) - gap - (ly / S) * 0.06 * S) < _step(S, 0.016)), M["outer2"], m)
                return m, -0.18 * (np.sin(lx * 0.7 + 1.3) > 0.6)
            jobs.append((rows, mf, 1.3))
        for rows, mf, z in jobs:
            def mf2(lx, ly, u, mf=mf):
                m, ex = mf(lx, ly, u)
                return m, ex
            pid = profile(cv, b.hip, 0.0, rows, z, mf2, shift=sh)
            if pid:
                cv.mat[cv.mat == 0] = 0  # holes in an open coat stay holes

    # -- torso and top --
    def torso(self):
        b, S, cv = self.b, self.S, self.cv
        k = 0.9 if b.fc == 1 else 1.0
        sh = 0.035 * S * b.W if b.fc == 1 else 0.0
        ts = b.t_shoulder
        rows = [(ts - 0.018 * S, b.sw * 0.55 * k, b.sw * 0.55 * k), (ts + 0.012 * S, b.sw * 0.98 * k, b.sw * 0.98 * k),
                (ts + 0.075 * S, b.chest_hw * k, b.chest_hw * k), (b.t_waist, b.waist_hw * k, b.waist_hw * k),
                (0.045 * S, b.hip_hw * k, b.hip_hw * k)]
        if self.species == "blob":
            rows = [(ts - 0.03 * S, b.sw * 0.7, b.sw * 0.7), (ts + 0.06 * S, b.chest_hw * 1.1, b.chest_hw * 1.1),
                    ((ts + 0.045 * S) * 0.4, b.chest_hw * 1.3, b.chest_hw * 1.3), (0.06 * S, b.hip_hw * 1.2, b.hip_hw * 1.2)]
        top = self.top
        kind = top.get("kind", "tee")
        pat = top.get("pattern", "plain")
        neck = top.get("neck", "crew")
        hem = {"crop": b.t_waist - 0.035 * S, "tank": 0.0, "tee": 0.012 * S, "longsleeve": 0.01 * S, "jumper": 0.02 * S, "hoodie": 0.03 * S,
               "shirt": 0.01 * S, "polo": 0.008 * S, "scrubs": 0.03 * S, "jumpsuit": 1.0 * S, "dress": 1.0 * S, "gown": 1.0 * S, "chef": 0.035 * S,
               "leotard": 1.0 * S, "bare": -1.0 * S, "vest": 0.0, "robe": 1.0 * S, "tunic": 0.06 * S, "bra": b.t_shoulder + 0.11 * S}.get(kind, 0.01 * S)
        wb = -0.045 * S  # the waistband of the bottoms
        front = b.fc != 2
        seed = self.seed
        S_ = S
        chest_y = ts + 0.095 * S
        mot = top.get("motif", "sun")
        q = _step(S, 0.032, 2)

        def mat(lx, ly, u):
            m = np.full(u.shape, M["top"], np.uint8)
            ex = np.zeros(u.shape, np.float32)
            # below the hem: the bottoms (or skin of a crop top's midriff)
            if kind == "bare" or (kind == "bra"):
                m = np.where(ly > hem, M["skin"], m)
            else:
                m = np.where((ly > hem) & (ly < wb), M["skin"], m)
            m = np.where((ly > max(hem, wb)) & (kind not in ("jumpsuit", "dress", "gown", "leotard", "robe")), M["bottom"], m)
            if kind == "jumpsuit":
                m = np.where(ly > wb, M["top"], m)
                m = np.where(np.abs(ly - wb) < _step(S_, 0.012), M["acc"], m)  # the belt
            if kind == "leotard":
                m = np.where(ly > wb + 0.01 * S_, M["bottom2"], m)
            # the neckline
            if front and kind not in ("bare",):
                if neck == "v":
                    m = np.where((ly < ts + 0.06 * S_ - np.abs(lx) * 1.4) & (ly > ts - 0.03 * S_), M["skin"], m)
                elif neck == "scoop":
                    m = np.where((lx * lx / (0.05 * S_) ** 2 + (ly - ts + 0.015 * S_) ** 2 / (0.04 * S_) ** 2) < 1, M["skin"], m)
                elif neck == "crew":
                    m = np.where((lx * lx / (0.032 * S_) ** 2 + (ly - ts + 0.02 * S_) ** 2 / (0.024 * S_) ** 2) < 1, M["skin"], m)
                    m = np.where(((lx * lx / (0.04 * S_) ** 2 + (ly - ts + 0.02 * S_) ** 2 / (0.032 * S_) ** 2) < 1) & (m == M["top"]), M["top3"], m)
                elif neck == "collar":
                    m = np.where((ly < ts + 0.045 * S_ - np.abs(lx) * 1.2) & (ly > ts - 0.03 * S_), M["skin"], m)
                    col = (np.abs(ly - (ts + 0.02 * S_ - np.abs(lx) * 0.6)) < 0.018 * S_) & (np.abs(lx) < 0.06 * S_) & (np.abs(lx) > 0.01 * S_)
                    m = np.where(col, M["top3"], m)
            ontop = m == M["top"]
            # patterns on the top
            if pat == "stripes":
                m = np.where(ontop & (np.floor((ly - ts) / q) % 2 == 1), M["top2"], m)
            elif pat == "vstripes":
                m = np.where(ontop & (np.floor(lx / q) % 2 == 1), M["top2"], m)
            elif pat == "band":
                m = np.where(ontop & (np.abs(ly - chest_y - 0.02 * S_) < 0.045 * S_), M["top2"], m)
                m = np.where(ontop & (np.abs(ly - chest_y - 0.02 * S_) < 0.045 * S_) & (np.floor(lx / q) % 2 == 0), M["top3"], m)
            elif pat == "check":
                gx = np.floor(lx / (q * 1.5)) % 2 == 0
                gy = np.floor((ly - ts) / (q * 1.5)) % 2 == 0
                m = np.where(ontop & (gx ^ gy), M["top2"], m)
                m = np.where(ontop & gx & gy, M["top3"], m)
            elif pat == "dots":
                m = np.where(ontop & (np.round(lx) % (q * 2) == 0) & (np.round(ly) % (q * 2) == 0), M["top2"], m)
            elif pat == "tiedye":
                r = np.sqrt(lx * lx + (ly - chest_y) ** 2) + 1.5 * np.sin(np.arctan2(ly - chest_y, lx) * 5)
                m = np.where(ontop & (np.floor(r / q) % 3 == 1), M["top2"], m)
                m = np.where(ontop & (np.floor(r / q) % 3 == 2), M["top3"], m)
            elif pat == "ribs":  # a skeleton's ribcage
                m = np.where((ly < b.t_waist) & (np.floor((ly - ts) / max(2, q)) % 2 == 0) & (np.abs(lx) > 0.012 * S_), M["horn"], M["top"])
                m = np.where(np.abs(lx) <= 0.012 * S_, M["horn"], m)
                m = np.where(ly > b.t_waist, M["horn"], m)
            if pat in ("print", "emblem") and (front or top.get("back_print")) and self.lod < 4:
                pr = 0.06 * S_ if pat == "print" else 0.05 * S_
                mx = (lx - (0.025 * S_ if b.fc == 1 else 0.0)) / pr
                my = (ly - chest_y - (0.01 * S_)) / pr
                mm = motif_mask(mot, mx, my) & ontop
                m = np.where(mm, M["top2"], m)
            if kind == "hoodie" and front:  # the pocket and the strings
                pk = (ly > -0.13 * S_) & (ly < wb - 0.005 * S_) & (np.abs(lx) < b.waist_hw * 0.7 - (ly + 0.13 * S_) * 0.3)
                ex = np.where(pk & ontop, ex - 0.22, ex)
                m = np.where(pk & (np.abs(ly + 0.13 * S_) < 0.8) & ontop, M["top3"], m)
                strings = (np.abs(np.abs(lx) - 0.016 * S_) < 0.55) & (ly > ts) & (ly < ts + 0.08 * S_)
                m = np.where(strings, M["top3"], m)
            if kind == "chef" and front:
                bt = (np.abs(np.abs(lx) - 0.04 * S_) < 0.6) & (np.round(ly - ts) % _step(S_, 0.04, 3) == 0) & (ly > ts + 0.02 * S_) & (ly < wb)
                m = np.where(bt, M["acc"], m)
            if kind == "scrubs" and front:
                pk = (lx > 0.02 * S_) & (lx < 0.07 * S_) & (np.abs(ly - chest_y + 0.005 * S_) < 0.6)
                m = np.where(pk, M["top3"], m)
            if kind == "shirt" and front:
                m = np.where((np.abs(lx) < 0.6) & (ly > ts) & (ly < hem) & (m != M["skin"]), M["top3"], m)
            if kind == "robe":
                m = np.where(np.abs(lx - 0.25 * (ly - ts) * 0.0) < 0.6, M["top3"], m)
            # folds and the body's shading
            ex += np.where((np.sin(lx * 0.55 + ly * 0.35 + seed) > 0.8) & (m == M["top"]), -0.2, 0.0)
            ex += -0.12 * np.clip((ly - b.t_waist) / (0.08 * S_), 0, 1) * (m == M["bottom"])
            ex += np.where((ly > ts + 0.11 * S_) & (ly < ts + 0.14 * S_) & (np.abs(lx) > b.waist_hw * 0.5), -0.18, 0.0)  # under the chest
            if self.species == "blob":
                ex += np.where(_hash01(np.round(lx), np.round(ly), seed) > 0.97, 0.6, 0.0)
            return m, ex
        profile(cv, b.hip, b.lean, rows, 1.0, mat, shift=sh)
        if self.outer and self.outer.get("kind") not in ("cape",):
            self.outer_garment(rows, k, sh)
        if kind == "hoodie" and self.hat is None:
            hc = b.T((0.0, ts - 0.01 * S))
            ellipse(cv, hc, 0.065 * S * b.W, 0.028 * S, b.lean, 1.05, lambda *a: (M["top"], -0.25))
        if self.bottom.get("kind") == "dungarees":
            self.dungarees()

    def outer_garment(self, rows, k, sh):
        b, S, cv = self.b, self.S, self.cv
        o = self.outer
        kind = o.get("kind")
        gap = (0.03 if kind not in ("gilet",) else 0.04) * S
        front = b.fc != 2
        pat = o.get("pattern", "plain")
        q = _step(S, 0.032, 2)
        ts = b.t_shoulder
        rows2 = [(r[0], r[1] * 1.06, r[2] * 1.06) for r in rows[:-1]] + [(0.04 * S, rows[-1][1] * 1.1, rows[-1][2] * 1.1)]

        def mat(lx, ly, u):
            m = np.full(u.shape, M["outer"], np.uint8)
            ex = np.zeros(u.shape, np.float32)
            if front:
                off = lx - sh * 0.5
                opening = np.abs(off) < gap + np.maximum(0, (ly - ts)) * (0.12 if kind in ("jacket", "overshirt", "cardigan", "labcoat", "coat") else 0.05)
                m = np.where(opening & (ly > ts - 0.02 * S), 0, m)
                lap = (np.abs(np.abs(off) - gap - np.maximum(0, (ly - ts)) * 0.12) < _step(S, 0.014)) & (ly > ts) & (ly < ts + 0.1 * S)
                m = np.where(lap & (m > 0), M["outer2"], m)
                if kind == "labcoat":
                    m = np.where((np.abs(off - 0.075 * S) < 0.025 * S) & (np.abs(ly - ts - 0.1 * S) < 0.6) & (m > 0), M["outer2"], m)
            if pat == "check":
                gx = np.floor(lx / (q * 1.5)) % 2 == 0
                gy = np.floor((ly - ts) / (q * 1.5)) % 2 == 0
                m = np.where((m == M["outer"]) & (gx ^ gy), M["outer2"], m)
            if o.get("trim") and front:
                m = np.where((m == M["outer"]) & (np.abs(np.abs(lx - sh * 0.5) - gap - np.maximum(0, (ly - ts)) * 0.12) < _step(S, 0.02)), M["outer2"], m)
            ex += np.where(np.sin(lx * 0.6 + ly * 0.25) > 0.82, -0.2, 0.0)
            return m, ex
        profile(cv, b.hip, b.lean, rows2, 1.3, mat, shift=sh)
        # the opening shows the top again: re-cut holes to transparent are filled by the torso already (z lower); restore them
        sl = (slice(0, cv.h), slice(0, cv.w))
        hole = (cv.mat == 0) & (cv.z > 1.25) & (cv.z < 1.35)
        if hole.any():
            pass

    def dungarees(self):
        b, S, cv = self.b, self.S, self.cv
        if b.fc == 2:
            seg(cv, b.T((-0.06 * S, b.t_shoulder + 0.01 * S)), b.T((0.06 * S, b.t_waist)), "bottom", DARK, 1.15)
            seg(cv, b.T((0.06 * S, b.t_shoulder + 0.01 * S)), b.T((-0.06 * S, b.t_waist)), "bottom", DARK, 1.15)
            return
        bw = b.chest_hw * 0.62
        y0 = b.t_shoulder + 0.085 * S
        pts = [b.T((-bw, y0)), b.T((bw, y0)), b.T((bw * 1.08, -0.03 * S)), b.T((-bw * 1.08, -0.03 * S))]
        poly_fill(cv, pts, 1.15, "bottom", lambda X, Y: lambert_u((X - b.hip[0]) / (bw * 1.2)) - 0.05)
        for sg in (-1, 1):
            seg(cv, b.T((sg * bw * 0.85, y0)), b.T((sg * b.sw * 0.62, b.t_shoulder - 0.005 * S)), "bottom", MID, 1.16, 1.6 if S > 80 else 1.0)
            cv.dot(*b.T((sg * bw * 0.72, y0 + 0.012 * S)), "acc", LIT, 1.2)
        if S > 60:
            pk = [b.T((-bw * 0.5, y0 + 0.03 * S)), b.T((bw * 0.5, y0 + 0.03 * S)), b.T((bw * 0.5, y0 + 0.065 * S)), b.T((-bw * 0.5, y0 + 0.065 * S))]
            poly_fill(cv, pk, 1.17, "bottom2", 0.45)

    def cape(self):
        b, S, cv = self.b, self.S, self.cv
        ts = b.t_shoulder
        y1 = (-0.18 * S - b.hip[1]) if b.state not in SEATED else (-0.02 * S - b.hip[1])
        rows = [(ts - 0.01 * S, b.sw * 0.9, b.sw * 0.9), (ts + 0.1 * S, b.sw * 1.15, b.sw * 1.15), (y1, b.sw * 1.55, b.sw * 1.55)]
        z = 1.4 if b.fc == 2 else -1.8

        def mat(lx, ly, u):
            m = np.full(u.shape, M["outer"], np.uint8)
            m = np.where(ly > y1 - _step(S, 0.02), M["outer2"], m)
            return m, -0.2 * (np.sin(lx * 0.5 + 0.7) > 0.5) - 0.1
        profile(cv, b.hip, b.lean * 0.6, rows, z, mat)

    def wings(self, kind):
        b, S, cv = self.b, self.S, self.cv
        z = 1.45 if b.fc == 2 else -2.2
        if kind == "case":  # an insect's wing cases
            for sg in (-1, 1):
                c = b.T((sg * 0.05 * S, b.t_shoulder + 0.13 * S))
                ellipse(cv, c, 0.05 * S, 0.15 * S, b.lean + sg * 0.18, z, lambda lx, ly, u, v: (np.where(np.abs(u) < 0.12, M["extra"], M["outer"]), 0.1 * (v < -0.3)))
            return
        for sg in (-1, 1):  # bat wings
            base = b.T((sg * 0.04 * S, b.t_shoulder + 0.04 * S))
            tip = (base[0] + sg * 0.26 * S, base[1] - 0.16 * S)
            low = (base[0] + sg * 0.2 * S, base[1] + 0.16 * S)
            mid = (base[0] + sg * 0.3 * S, base[1] + 0.02 * S)
            poly_fill(cv, [base, tip, mid, low, (base[0], base[1] + 0.12 * S)], z, "extra",
                      lambda X, Y: 0.3 + 0.25 * (np.sin((X - base[0]) * 0.5) > 0.3))
            seg(cv, base, tip, "horn", DARK, z + 0.01)
            seg(cv, base, mid, "horn", DARK, z + 0.01)

    def tail(self):
        b, S, cv = self.b, self.S, self.cv
        z = 1.5 if b.fc == 2 else -2.0
        p = b.T((0.0, -0.02 * S))
        pts = []
        for i in range(9):
            t = i / 8.0
            pts.append((p[0] + 0.16 * S * t * (1 if self.seed % 2 else -1), p[1] + 0.12 * S * math.sin(t * 2.6) - 0.02 * S))
        for i in range(8):
            capsule(cv, pts[i], pts[i + 1], 0.012 * S, 0.01 * S, z, lambda t, u: M["skin"])
        tip = pts[-1]
        poly_fill(cv, [(tip[0], tip[1] - 0.03 * S), (tip[0] + 0.025 * S, tip[1]), (tip[0], tip[1] + 0.02 * S), (tip[0] - 0.02 * S, tip[1])], z + 0.01, "skin2", 0.5)

    # -- neck, arms --
    def neck(self):
        b, S, cv = self.b, self.S, self.cv
        if self.species == "blob":
            return
        r = 0.026 * S * (0.6 if self.species in ("skeleton", "insect") else 1.0) * max(0.9, min(1.25, b.W))
        top = add(b.head_c, rot((0.0, b.head_h * 0.3), b.head_ang))
        capsule(cv, b.neck_base, top, r * 1.05, r, 0.9, lambda t, u: (np.full(t.shape, M["horn"] if self.species == "skeleton" else M["skin"], np.uint8),
                                                                      -0.25 * (t > 0.55)))

    def arm(self, side):
        b, S, cv = self.b, self.S, self.cv
        a = b.arms[side]
        top = self.top.get("kind", "tee")
        sleeves = self.top.get("sleeves", {"tank": "none", "crop": "short", "tee": "short", "longsleeve": "long", "jumper": "long", "hoodie": "long",
                                            "shirt": "long", "polo": "short", "scrubs": "short", "jumpsuit": "long", "dress": "short", "gown": "short",
                                            "chef": "long", "leotard": "none", "bare": "none", "vest": "none", "robe": "long", "tunic": "short",
                                            "bra": "none"}.get(top, "short"))
        outer = self.outer if (self.outer and self.outer.get("kind") not in ("cape", "gilet")) else None
        W = b.W * b.limb
        r_sh, r_el, r_wr = 0.042 * W * S, 0.035 * W * S, 0.026 * W * S
        if sleeves == "long" or outer:
            r_sh *= 1.12
            r_el *= 1.15
            r_wr *= 1.25
        if self.species == "skeleton":
            r_sh, r_el, r_wr = 0.016 * S, 0.014 * S, 0.012 * S
        if self.species == "brute":
            r_sh *= 1.25
            r_el *= 1.2
        z = self.arm_z(side)
        sl_mat = M["outer"] if outer else M["top"]
        skin = M["horn"] if self.species == "skeleton" else M["skin"]
        cuff = M["outer2"] if outer and outer.get("trim") else (M["top3"] if not outer else M["outer"])
        stripes = (self.top.get("pattern") == "stripes") and not outer
        q = _step(S, 0.032, 2)
        acc = self.acc

        def up_mat(t, u):
            if sleeves == "none" and not outer:
                return np.full(t.shape, skin, np.uint8)
            lim = 0.55 if (sleeves == "short" and not outer) else 2.0
            m = np.where(t < lim, sl_mat, skin).astype(np.uint8)
            if sleeves == "short" and not outer:
                m = np.where((t >= lim - 0.12) & (t < lim), M["top3"] if self.top.get("neck") == "crew" else sl_mat, m)
            if stripes:
                m = np.where((m == M["top"]) & (np.floor(t * 0.17 * S / q) % 2 == 1), M["top2"], m)
            return m

        def fore_mat(t, u):
            if (sleeves != "long") and not outer:
                m = np.full(t.shape, skin, np.uint8)
                if "bracelet" in acc and side == "l":
                    m = np.where(np.abs(t - 0.86) < 0.07, M["acc"], m)
                if "watch" in acc and side == "r":
                    m = np.where(np.abs(t - 0.86) < 0.08, M["acc2"], m)
                return m
            m = np.where(t > 0.86, cuff, sl_mat).astype(np.uint8)
            if stripes:
                m = np.where((m == M["top"]) & (np.floor(t * 0.15 * S / q) % 2 == 1), M["top2"], m)
            return m
        capsule(cv, a["sh"], a["el"], r_sh, r_el, z, lambda t, u: (up_mat(t, u), 0.0))
        capsule(cv, a["el"], a["wr"], r_el * 0.95, r_wr, z + 0.02, lambda t, u: (fore_mat(t, u), 0.0))
        hand_r = 0.024 * S * (1.15 if self.species in ("brute",) else 1.0)
        glove = self.sp.get("gloves")
        ellipse(cv, a["hand"], hand_r, hand_r * 1.12, math.atan2(a["fd"][0], a["fd"][1]), z + 0.04,
                lambda *x: M["acc"] if glove else skin)

    # -- the head --
    def snap(self, c):
        """A head centre on a pixel centre, so the face's pixels sit on the grid and a front face is symmetric."""
        cv = self.cv
        return (math.floor(c[0] + cv.ox) + 0.5 - cv.ox, math.floor(c[1] + cv.oy) + 0.5 - cv.oy)

    def face_layout(self, rx, ry):
        """Where the features go, in whole pixels from the head centre (x right, y down): the size class, the face's centre column (moved towards the turn
        in the three-quarter view), the rows of the brows, eyes, nose and mouth, the eyes' width and the gap between them."""
        b = self.b
        f = self.sp.get("face") or {}
        kid = f.get("age") == "kid"
        cls = "L" if (ry >= 5.5 and rx >= 4.2) else ("S" if ry >= 3.0 else "XS")
        sx = int(round(rx * 0.38)) if b.fc == 1 else 0
        if rx >= 5.9:
            ew, ein = 3, 2
        elif rx >= 5.4:
            ew, ein = 3, 1
        elif rx >= 4.2:
            ew, ein = 2, 2 if rx >= 4.8 else 1
        else:
            ew, ein = 1, 1
        ey = 1 if (kid and cls == "L") else 0
        brow = ey - (2 if cls == "L" else 1)
        nose = ey + max(1, int(round(ry * 0.33)))
        mouth = nose + (2 if cls == "L" else 1)
        if cls == "XS":
            nose, mouth = 1, 1
        return {"cls": cls, "sx": sx, "ew": ew, "ein": ein, "ey": ey, "brow": brow, "nose": nose, "mouth": mouth, "rx": rx, "ry": ry}

    def relief(self, L, lx, ly, u, v):
        """The skin's modelling. The face is painted in clean planes rather than left to the round shading (which would scatter single pixels across the
        features): mid skin, the light (upper left) on the nose bridge, the cheekbone and the chin, the shadow on the turning cheek, inside the eye socket by
        the bridge, under the cheekbone and along the jaw; in the three-quarter view the side of the head is its own lit plane with the jawline under it.
        Returns shade offsets that bring the round shading to that target (the forehead and crown keep the round shading)."""
        b = self.b
        f = self.sp.get("face") or {}
        if b.fc == 2 or L["cls"] == "XS":
            return np.where(v > 0.55, -0.12, 0.0).astype(np.float32)  # the nape, under the skull
        if self.species in ("grey", "insect", "skeleton", "cyclops"):  # their own skulls: the round shading, a darker jaw
            return np.where(v > 0.5, -0.12 - 0.12 * np.abs(u), 0.0).astype(np.float32)
        nz = np.sqrt(np.clip(1.0 - u * u - v * v, 0.0, 1.0))
        base = np.clip(0.62 - 0.4 * u - 0.22 * v + 0.28 * (nz - 0.6), 0.0, 1.0)
        fx = np.round(lx) - L["sx"]
        fy = np.round(ly)
        ey, ew, ein, my, ny, br = L["ey"], L["ew"], L["ein"], L["mouth"], L["nose"], L["brow"]
        LITV, MIDV, DKV = 0.82, 0.55, 0.26
        tgt = np.full(u.shape, MIDV, np.float32)
        face = fy >= br - 1
        if L["cls"] == "S":
            tgt = np.where((fx == -(ein + 1)) & (fy == ey + 1), LITV, tgt)
            tgt = np.where((u > 0.55) & (fy >= ey), DKV, tgt)
            tgt = np.where((fy >= my + 1) & (u > 0.0), DKV, tgt)
            if b.fc == 1:
                tgt = np.where(fx < -ein, LITV, tgt)
                tgt = np.where((fx < -ein) & (fy >= my), DKV, tgt)
            return np.where(face, tgt - base, 0.0).astype(np.float32)
        out = ein + ew - 1  # the outer column of the eyes
        if b.fc == 0:
            tgt = np.where((fx == 0) & (fy >= ey - 1) & (fy <= ny - 2), LITV, tgt)  # the bridge of the nose
            tgt = np.where((fx >= -out) & (fx <= -ein) & (fy >= ey + 1) & (fy <= ey + 2), LITV, tgt)  # the lit cheekbone
            if f.get("cheek"):
                tgt = np.where((fx >= ein) & (fx <= out - 1) & (fy == ey + 1), LITV, tgt)
            tgt = np.where((fx == ein - 1) & (fy >= ey - 1) & (fy <= ey) & (ein > 1), DKV, tgt)  # the socket by the bridge, shadow side
            tgt = np.where((u > 0.6) & (fy >= ey - 1), DKV, tgt)  # the cheek turning away
            if f.get("cheek") or f.get("age") == "old":
                tgt = np.where((np.abs(fx) == out) & (fy >= ny) & (fy <= my - 1) & (fx > 0), DKV, tgt)
            tgt = np.where((fy >= my + 1) & (u > 0.25), DKV, tgt)  # the jaw
            tgt = np.where((fy >= my + 1) & (u < -0.55), DKV, tgt)
            tgt = np.where((fx == -1) & (fy == my + 2), LITV, tgt)  # the chin
        else:
            sideb = -(ein + ew)  # left of the near eye: the side of the head
            tgt = np.where((fx == 0) & (fy >= ey - 1) & (fy <= ny - 2), LITV, tgt)
            tgt = np.where((fx < sideb + 1) & (fy < my) & (fy >= br), LITV, tgt)
            tgt = np.where((fx >= -out) & (fx <= -ein) & (fy == ey + 1), LITV, tgt)
            tgt = np.where((fx < sideb + 2) & (fy >= my - 1), DKV, tgt)  # the jawline under the side plane
            tgt = np.where((fx > ein + 1) & (fy >= ey - 1), DKV, tgt)  # the far cheek
            tgt = np.where((fy >= my + 1) & (fx > 1), DKV, tgt)
            tgt = np.where((fx == 0) & (fy == my + 2), LITV, tgt)
        return np.where(face, tgt - base, 0.0).astype(np.float32)

    def head(self):
        b, S, cv, sp = self.b, self.S, self.cv, self.sp
        rx, ry = b.head_w * 0.5, b.head_h * 0.5
        c, ang = b.head_c, b.head_ang
        spk = self.species
        skin = M["horn"] if spk == "skeleton" else M["skin"]
        f = sp.get("face") or {}
        jaw = {"grey": 0.6, "insect": 0.45, "skeleton": 0.25, "brute": 0.05, "blob": 0.0}.get(spk, float(f.get("jaw", 0.3)))
        chin = f.get("chin", "round") if not spk else "round"
        if b.fc == 1:
            c = (c[0] + 0.004 * S, c[1])
        c = self.snap(c)
        L = self.face_layout(rx, ry)
        self.L = L
        fc = b.fc

        def shape(u, v):
            vp = np.clip(v, 0.0, None)
            lim = 1.0 - jaw * vp * vp
            if chin == "square":
                lim = lim + 0.22 * np.abs(u) * vp * vp * jaw * 3.0
                lim = np.where(v > 0.93, lim - 0.4, lim)
            elif chin == "pointed":
                lim = lim - 0.18 * np.abs(u) * vp ** 3
            if fc == 1:  # the jaw slants from below the ear to the chin, which comes forward
                lim = lim - 0.3 * vp * vp * np.clip(-u, 0.0, 1.0) + 0.06 * vp * np.clip(u, 0.0, 1.0)
            return lim
        seed = self.seed

        def mat(lx, ly, u, v):
            m = np.full(u.shape, skin, np.uint8)
            ex = self.relief(L, lx, ly, u, v) if spk not in ("blob",) else np.zeros(u.shape, np.float32)
            if spk == "flame":
                m = np.where(_hash01(np.round(lx), np.round(ly), seed) > 0.85, M["skin2"], m)
            if spk == "blob":
                ex += np.where((u < -0.3) & (v < -0.3) & (u > -0.65) & (v > -0.7), 0.5, 0.0)
            return m, ex
        hz = 2.0
        self.head_pid = ellipse(cv, c, rx, ry, ang, hz, mat, shape=shape)
        if self.head_pid is not None and b.fc != 2:
            cv.nodither |= cv.pid == self.head_pid
        # ears: a lit rim, a shadowed bowl
        if spk not in ("blob", "grey", "skeleton", "insect", "flame") and self.lod < 4:
            pointed = spk == "imp" or (sp.get("species") or {}).get("ears") == "pointed"
            for sg in ((-1, 1) if b.fc != 1 else ((-1,) if pointed else ())):
                ec = add(c, rot((sg * rx * 1.0, ry * 0.06), ang))
                er = rx * (0.22 if spk not in ("imp",) else 0.3)
                if pointed:
                    tip = add(c, rot((sg * rx * 1.75, -ry * 0.45), ang))
                    poly_fill(cv, [add(c, rot((sg * rx * 0.8, -ry * 0.15), ang)), tip, add(c, rot((sg * rx * 0.85, ry * 0.3), ang))], 1.95, "skin", 0.45)
                else:
                    ellipse(cv, ec, er, er * 1.6, ang, 1.95, lambda lx, ly, u, v, sg=sg: (M["skin"], np.where(u * sg < -0.1, -0.42, -0.05)))
        self.species_head(c, rx, ry, ang)
        if b.fc != 2:
            self.face_features(c, rx, ry, ang)
        self.hair_front(c, rx, ry, ang)
        self.hat_draw(c, rx, ry, ang)
        self.headwear_props(c, rx, ry, ang)

    def F(self, c, ang, x, y):
        return add(c, rot((x, y), ang))

    def put_decal(self, c, ang, dec, z=2.2):
        """Place the face's pixels {(x, y): (material, step)} (whole pixels from the head centre, in the head's own frame) on the head: every canvas pixel
        of the head looks up the face pixel it falls on (a tilted head carries its face without holes), and only the head's own skin is painted."""
        cv = self.cv
        if not dec or getattr(self, "head_pid", None) is None:
            return
        R = max(max(abs(k[0]), abs(k[1])) for k in dec) + 2
        sl = cv.region(c[0] - R, c[1] - R, c[0] + R, c[1] + R)
        if sl is None:
            return
        X, Y = cv.X[sl] - c[0], cv.Y[sl] - c[1]
        ca, sa = math.cos(ang), math.sin(ang)
        ix = np.round(X * ca + Y * sa).astype(np.int32)
        iy = np.round(-X * sa + Y * ca).astype(np.int32)
        mat = np.zeros(ix.shape, np.uint8)
        fixed = np.full(ix.shape, -1, np.int8)
        for (x, y), (m, st) in dec.items():
            sel = (ix == x) & (iy == y)
            if sel.any():
                mat[sel] = M[m]
                fixed[sel] = st
        on = (cv.pid[sl] == self.head_pid) & (mat > 0)
        cv.put(sl, on, mat, 0.5, z, pid=self.head_pid, fixed=fixed)

    # -- the face --
    def face_features(self, c, rx, ry, ang):
        L = self.L
        dec = {}
        spk = self.species
        if spk in ("skeleton", "grey", "cyclops", "insect", "blob"):
            getattr(self, "face_" + spk)(L, dec)
        else:
            self.face_human(L, dec)
        self.put_decal(c, ang, dec)

    def _P(self, dec, x, y, m, st):
        dec[(int(x), int(y))] = (m, st)

    def face_mood(self):
        """(mood, eyes): the mood the state shows (neutral, happy, cheer, sad, sleep, sing) and the eyes (open, closed, bliss = closed in a smile)."""
        f = self.sp.get("face") or {}
        face = self.face
        mood = face
        pose = self.b.pose
        if face == "happy" and f.get("sing") and float(pose.get("head_tilt", 0.0)) < -0.035 and self.b.state not in ("chat", "hug"):
            mood = "sing"  # head back to the music: singing along
        if face == "sleep":
            return "sleep", "closed"
        e = f.get("eyes", "open")
        if e == "closed":
            return mood, "bliss" if mood in ("happy", "cheer", "sing") else "closed"
        if e == "lost" and mood in ("happy", "cheer", "sing"):
            return mood, "bliss" if mood == "cheer" else "closed"
        return mood, "open"

    def face_human(self, L, dec):
        """A person's face (and a demon's or a humanoid alien's: the same face with their own eyes and extras)."""
        b = self.b
        f = self.sp.get("face") or {}
        P = lambda x, y, m, st: self._P(dec, x, y, m, st)
        mood, eyes = self.face_mood()
        cls, sx, ew, ein, ey = L["cls"], L["sx"], L["ew"], L["ein"], L["ey"]
        spk = self.species
        demon = spk in ("imp", "brute", "fiend", "queen", "flame")
        iris = "extra" if not spk else "eye_d"
        fc = b.fc
        glasses = f.get("glasses")
        if cls == "XS":
            # a far face: two eye shadows and, when they shout, the mouth
            if eyes == "open":
                for x in ((-1, 1) if fc == 0 else (0, 1)):
                    P(x, 0, "skin", EDGE)
            if mood in ("cheer", "sing"):
                P(sx if fc == 0 else 1, 1, "mouth", EDGE)
            return
        # the eyes, outer column first: (columns, side)
        if fc == 0:
            eye_cols = [([-(ein + k) for k in range(ew - 1, -1, -1)], -1), ([ein + k for k in range(ew - 1, -1, -1)], 1)]
        else:
            far_w = max(1, ew - 1)
            eye_cols = [([sx - ein - k for k in range(ew - 1, -1, -1)], -1), ([sx + ein + k for k in range(far_w - 1, -1, -1)], 1)]
        lash = int(f.get("lash", 1))
        if demon and spk in ("fiend", "queen"):
            lash = 2
        shape = f.get("eye", "almond")
        for cols, sg in eye_cols:
            self.eye(P, cols, sg, ey, cls, eyes, mood, lash, shape, iris, glasses, far=(fc == 1 and sg == 1))
        # brows
        if f.get("brows", True):
            for cols, sg in eye_cols:
                self.brow(P, cols, sg, L, mood, eyes, glasses, f.get("brow", "straight") if spk != "brute" else "thick")
        if spk == "brute":  # a heavy ridge over the eyes
            for x in range(-(ein + ew), ein + ew + 1):
                if (x + sx, L["brow"] + 1) not in dec:
                    P(x + sx, L["brow"] + 1, "skin", DARK)
        # glasses over the eyes
        if glasses:
            self.glasses(P, dec, eye_cols, L, glasses)
        # nose, cheeks, lines, freckles
        self.nose(P, L, f.get("nose", "straight") if not demon else ("wide" if spk == "brute" else "straight"))
        self.cheeks(P, dec, L, mood, f)
        beard = f.get("beard") if not spk else None
        if beard:
            self.beard(P, dec, L, beard)
        self.mouth(P, dec, L, mood, f, demon)

    def eye(self, P, cols, sg, ey, cls, eyes, mood, lash, shape, iris, glasses, far):
        """One eye. cols: outer to inner. Open: the upper lid's lash line, the white, the iris (and its pupil), a lit inner corner; closed: the lash line
        curving down with the lid lit above it; bliss (closed in a smile): the lid curving up."""
        n = len(cols)
        out = cols[0]
        inn = cols[-1]
        lash_m, lash_s = ("eye_d", EDGE) if lash >= 1 else ("skin", EDGE)
        if cls == "S":
            x = cols[0]
            if eyes == "open":
                P(x, ey, "eye_d" if not glasses == "shades" else "eye_d", EDGE)
                if lash >= 2 and not far:
                    P(x + sg, ey - 1 if mood != "sad" else ey, "eye_d", DARK)
            elif eyes == "bliss":
                P(x, ey - 1 if mood == "cheer" else ey, "skin", EDGE)
            else:
                P(x, ey, "skin", EDGE)
            return
        if eyes in ("closed", "bliss"):
            if eyes == "bliss":  # an arc up: the cheeks push the closed lids into a smile
                for i, x in enumerate(cols):
                    up = i == 1 if n >= 3 else i == 0
                    P(x, ey - 1 if up else ey, lash_m, lash_s if i < n - 1 or n < 3 else DARK)
                    if not up:
                        P(x, ey - 1, "skin", MID)
                    P(x, ey + 1, "skin", LIT)  # the cheek pushed up under it
            else:  # relaxed, lost in the music: the lash line low, the lid above it catching the light
                for i, x in enumerate(cols):
                    P(x, ey, lash_m if i < n - 1 else "skin", lash_s if i < n - 1 else EDGE)
                    P(x, ey - 1, "skin", LIT if i < n - 1 else MID)
                if lash >= 2 and not far:
                    P(out + sg, ey + 1, "eye_d", DARK)
            return
        # open
        lid_y = ey - 1
        sad = mood == "sad"
        for i, x in enumerate(cols):
            if i == n - 1 and n >= 3:
                P(x, lid_y, "skin", EDGE if lash >= 1 else DARK)  # the inner end of the lid, softer
            else:
                P(x, lid_y, lash_m, lash_s)
        if lash >= 2 and not far:  # a lash flick past the outer corner
            P(out + sg, lid_y if not sad else ey, "eye_d", EDGE)
        # the eye's row: white, iris, white; the iris sits in the middle (towards the turn in the three-quarter view)
        if n >= 3:
            wo, ir, wi = cols[0], cols[1], cols[2]
            P(wo, ey, "eye_w", DARK)
            P(ir, ey, iris, DARK if iris == "extra" else EDGE)
            P(wi, ey, "eye_w", MID)
            if shape == "hooded" or sad:
                P(wo, ey, "skin", DARK)  # the lid hangs over the outer corner
            if mood in ("happy", "sing"):
                P(wo, ey, "skin", LIT)  # a smile lifts the lower lid
            if shape == "round" or mood == "cheer":
                P(ir, ey + 1, "skin", DARK)  # the lower lid under a wide eye
        elif n == 2:
            if far:
                P(cols[0], ey, iris, DARK if iris == "extra" else EDGE)
                P(cols[1], ey, "eye_w", DARK)
            else:
                P(cols[0], ey, "eye_w", DARK)
                P(cols[1], ey, iris, DARK if iris == "extra" else EDGE)
                if mood in ("happy", "sing"):
                    P(cols[0], ey, "skin", LIT)
        else:
            P(cols[0], ey, iris, EDGE)

    def brow(self, P, cols, sg, L, mood, eyes, glasses, kind):
        """A brow over the eye's columns (outer to inner): straight, arched, thick, thin or angled, raised in a cheer, the inner end up when sad, a
        little up when the eyes close to the music."""
        by = L["brow"] - (1 if glasses and L["cls"] == "L" else 0)
        n = len(cols)
        if L["cls"] == "S":
            if mood in ("cheer", "sad") or kind == "thick":
                x = cols[0]
                P(x, by - (1 if mood == "cheer" else 0), "hair", EDGE if kind != "thin" else DARK)
            return
        lift = 1 if mood == "cheer" or (eyes != "open" and mood in ("happy", "sing")) else 0
        m, st = "hair", EDGE
        if kind == "thin":
            st = DARK
        xs = list(cols)
        if L["sx"] == 0 or sg < 0:
            if kind in ("thick", "arched", "angled") and n >= 3:
                xs = [cols[0] + sg] + xs  # a longer brow, past the outer corner
        for i, x in enumerate(xs):
            t = i / max(1, len(xs) - 1)  # 0 outer .. 1 inner
            y = by - lift
            if kind == "arched" and 0 < t < 0.8:
                y -= 1
            if kind == "angled" and t < 0.3:
                y -= 1
            if mood == "sad" and t > 0.6:
                y -= 1
            if mood == "sad" and t < 0.3 and kind != "arched":
                y += 0
            ss = st if (0.2 < t < 0.95 or kind == "thick") else (DARK if st == EDGE else MID)
            P(x, y, m, ss)
            if kind == "thick" and 0.2 < t < 0.9:
                P(x, y - 1, m, DARK)

    def glasses(self, P, dec, eye_cols, L, kind):
        """Frames around the eyes, the eyes still showing through, a glint on the lens; shades: dark lenses with a sharp glint."""
        ey = L["ey"]
        fm = "acc"
        if L["cls"] == "S":
            for cols, sg in eye_cols:
                x = cols[0]
                if kind == "shades":
                    P(x, ey, "eye_d", EDGE)
                    P(x + sg, ey, "eye_d", DARK)
                else:
                    P(x + sg, ey, fm, EDGE)
            if self.b.fc == 0:
                P(0, ey, fm, DARK)
            return
        fm = "metal" if kind == "round" else "acc"
        for k, (cols, sg) in enumerate(eye_cols):
            far = self.b.fc == 1 and sg == 1
            lo, hi = min(cols), max(cols)
            x0, x1 = lo - 1, hi + 1
            if far and hi + 1 > int(L["rx"]) - 1:
                x1 = hi
            for x in range(x0, x1 + 1):  # the top bar sits on the lid line
                P(x, ey - 1, fm, EDGE if (kind != "round" or x not in (x0, x1)) else DARK)
            P(x0, ey, fm, DARK if kind != "round" else MID)
            P(x1, ey, fm, DARK)
            if kind == "square":
                for x in range(lo, hi + 1):
                    P(x, ey + 1, fm, DARK)
            elif kind == "round":
                P((lo + hi) // 2 if not far else lo, ey + 1, fm, DARK)
            if kind == "shades":
                for x in range(lo, hi + 1):
                    P(x, ey, "eye_d", DARK)
                    P(x, ey + 1, "eye_d", EDGE) if lo < x < hi or len(cols) < 3 else None
                if not far:
                    P(lo + (1 if len(cols) >= 3 else 0), ey, "glass", LIT)  # the glint
            elif not far and sg < 0:
                P(x0 + 1, ey - 1, "glass", LIT)  # the glint on the rim, the eye still clear
        # the bridge, and in the three-quarter view the arm back to the ear
        if self.b.fc == 0:
            P(0, ey - 1, fm, DARK)
        else:
            near = eye_cols[0][0]
            P(min(near) - 2, ey - 1, fm, DARK)
            P(min(near) - 3, ey - 1, fm, DARK)
            P(L["sx"] + 1, ey - 1, fm, DARK)

    def nose(self, P, L, kind):
        """The nose: the tip catching the light, the shadow side and the underside with the nostrils (front); in the three-quarter turn the nose points
        into the turn with its shadow on the far cheek."""
        ny, ey, sx = L["nose"], L["ey"], L["sx"]
        if L["cls"] == "S":
            if kind != "button":
                P(sx + (1 if self.b.fc == 1 else 0), ny, "skin", DARK)
            return
        if self.b.fc == 0:
            P(0, ny - 1, "skin", LIT)
            P(1, ny - 1, "skin", DARK)
            P(0, ny, "skin", DARK)
            if kind == "button":
                P(1, ny - 1, "skin", MID)
                P(1, ny, "skin", DARK)
            elif kind == "wide":
                P(-1, ny, "skin", DARK)
                P(1, ny, "skin", EDGE)
                P(0, ny, "skin", MID)
                P(-1, ny - 1, "skin", MID)
            elif kind == "long":
                P(1, ny - 2, "skin", DARK)
                P(0, ny, "skin", EDGE)
            elif kind == "hooked":
                P(0, ny - 2, "skin", LIT)
                P(1, ny - 2, "skin", DARK)
                P(0, ny, "skin", EDGE)
                P(1, ny, "skin", DARK)
            else:  # straight
                P(1, ny, "skin", DARK)
        else:
            tip = sx + 1
            P(tip, ny - 1, "skin", LIT)
            P(tip + 1, ny - 1, "skin", DARK)
            P(tip, ny, "skin", DARK)
            P(tip - 1, ny, "skin", DARK if kind != "button" else MID)
            if kind in ("long", "hooked"):
                P(tip + 1, ny - 2, "skin", DARK)
                P(tip, ny - 2, "skin", LIT)
            if kind == "wide":
                P(tip - 1, ny, "skin", EDGE)
            if kind == "hooked":
                P(tip + 1, ny, "skin", DARK)

    def cheeks(self, P, dec, L, mood, f):
        """Blush (a kid, a flushed dancer, a cheer), freckles, the lines of age: crow's feet, the bags under the eyes, the smile lines."""
        ey, ein, ew, sx, my = L["ey"], L["ein"], L["ew"], L["sx"], L["mouth"]
        fc = self.b.fc
        sides = (-1, 1) if fc == 0 else (-1,)
        if L["cls"] == "S":
            if f.get("blush") or f.get("age") == "kid" or mood == "cheer":
                for sg in sides:
                    P(sx + sg * (ein + 1), ey + 1, "skin2", MID)
            return
        blush = f.get("blush") or f.get("age") == "kid" or mood in ("cheer",)
        for sg in sides:
            cx = sx + sg * (ein + ew - 1)
            if blush:
                P(cx, ey + 2, "skin2", MID)
                P(cx - sg, ey + 2, "skin2", MID if (f.get("blush") or mood == "cheer") else DARK)
            if f.get("freckles"):
                P(sx + sg * (ein + 1), ey + 2, "skin", DARK)
                P(sx + sg * (ein - 1), ey + 1, "skin", DARK)
            if f.get("lines"):
                P(sx + sg * (ein + ew), ey, "skin", DARK)  # crow's feet
                P(sx + sg * (ein + 1), ey + 1, "skin", DARK)  # under the eye
                P(sx + sg * 2, my - 1, "skin", DARK)  # the smile line from the nose
        if fc == 1 and f.get("freckles"):
            P(sx + ein + 1, ey + 2, "skin", DARK)

    def beard(self, P, dec, L, kind):
        """Facial hair in the hair's own colour: a full beard along the jaw (lit at the upper left, darker underneath), a moustache, a goatee, stubble."""
        ey, my, ny, sx, ein, ew = L["ey"], L["mouth"], L["nose"], L["sx"], L["ein"], L["ew"]
        rx, ry = L["rx"], L["ry"]
        fc = self.b.fc
        S_ = L["cls"] == "S"
        for y in range(ny, int(ry) + 2):
            for x in range(-int(rx) - 1, int(rx) + 2):
                fx = x - sx
                if (x, y) in dec:
                    continue
                yy = y / ry
                if (x / rx) ** 2 + yy ** 2 > 1.05:
                    continue
                if kind == "moustache":
                    if y == my - 1 and abs(fx) <= (2 if not S_ else 1) or (y == my and abs(fx) == (2 if not S_ else 1)):
                        P(x, y, "hair", DARK if fx > -1 else MID)
                    continue
                if kind == "stubble":  # a shadow along the jaw and the upper lip, a few hairs in it
                    jaw = (y >= my + 1 and abs(fx) <= ein + ew) or (y == my - 1 and abs(fx) <= 1) or (y >= my and abs(fx) >= ein + ew - 1)
                    if jaw and y >= ny + (0 if S_ else 1):
                        P(x, y, "hair" if (x * 2 + y * 3) % 5 == 0 and not S_ else "skin", DARK)
                    continue
                # a full beard: the jaw, the chin, the upper lip, up the cheeks to the sideburns
                cheek = abs(fx) >= ein + ew - 1 and y >= ey + 2
                if fc == 1 and fx < -(ein + ew):
                    cheek = y >= ey + 1
                lower = y >= my - 1
                if not (cheek or lower):
                    continue
                if lower and abs(fx) <= 1 and y in (my, my + 1) and not S_:
                    continue  # the lips show through
                st = MID if (fx < 0 and y < my + 1) else DARK
                if y >= int(ry) or (x / rx) ** 2 + yy ** 2 > 0.8:
                    st = DARK if st == MID else EDGE
                if not S_ and (x * 3 + y * 5) % 7 == 0 and st == MID:
                    st = LIT
                P(x, y, "hair", st)

    def mouth(self, P, dec, L, mood, f, demon=False):
        """Lips in the person's own colour: a closed mouth with the lower lip catching the light, a smile curling up at the corners, a laugh with the
        teeth and a dark mouth, a singer's open O, a sad mouth turned down; a demon's tusks."""
        my, sx = L["mouth"], L["sx"]
        fc = self.b.fc
        lips = f.get("lips", "thin")
        hw = 2 if lips == "wide" else 1
        mc = sx
        if L["cls"] == "S":
            if mood == "cheer":
                P(mc, my, "teeth", MID)
                P(mc - 1, my, "mouth", EDGE)
                if fc == 0:
                    P(mc + 1, my, "mouth", EDGE)
                P(mc, my + 1, "mouth", EDGE)
            elif mood == "sing":
                P(mc, my, "mouth", EDGE)
                P(mc, my + 1, "mouth", DARK)
            elif mood == "happy":
                P(mc, my, "mouth", EDGE)
                P(mc - 1, my, "mouth", DARK)
                if fc == 0:
                    P(mc + 1, my, "mouth", DARK)
            elif mood == "sad":
                P(mc, my, "mouth", EDGE)
                P(mc - 1, my + 1, "mouth", DARK)
                if fc == 0:
                    P(mc + 1, my + 1, "mouth", DARK)
            else:
                P(mc, my, "mouth", DARK)
            return
        lo = mc - hw
        hi = mc + (hw if fc == 0 else max(0, hw - 1) + 1)
        full = lips in ("full", "wide")
        if mood == "cheer":
            P(lo - 1, my - 1 if fc == 0 else my, "mouth", DARK)
            P(hi + 1, my - 1, "mouth", DARK) if fc == 0 else None
            for x in range(lo, hi + 1):
                P(x, my - 1, "mouth", DARK)  # the upper lip
                P(x, my, "teeth", LIT if x < mc + 1 else MID)
                P(x, my + 1, "mouth", EDGE)
            P(lo - 1, my, "mouth", EDGE)
            P(hi + 1, my, "mouth", EDGE)
            for x in range(lo, hi + 1):
                P(x, my + 2, "mouth", MID if x <= mc else DARK)  # the lower lip
            if demon:
                P(lo, my, "teeth", LIT)
                P(hi, my, "teeth", LIT)
            return
        if mood == "sing":
            for x in range(mc - 1, mc + 2):
                P(x, my - 1 if x == mc else my, "mouth", DARK)
                P(x, my + 1, "mouth", DARK if x != mc else EDGE)
            P(mc, my, "mouth", EDGE)
            P(mc, my + 2, "mouth", MID)
            return
        if mood == "sad":
            for x in range(lo, hi + 1):
                P(x, my, "mouth", EDGE if abs(x - mc) <= 1 else DARK)
            P(lo - 1, my + 1, "mouth", DARK)
            if fc == 0:
                P(hi + 1, my + 1, "mouth", DARK)
            P(mc, my + 2, "skin", DARK)  # the chin puckers
            return
        if mood == "sleep":
            P(mc, my, "mouth", DARK)
            P(mc - 1, my, "mouth", DARK)
            return
        # neutral and happy: the line between the lips, the lower lip below it
        for x in range(lo, hi + 1):
            P(x, my, "mouth", EDGE if abs(x - mc) < hw or lips == "thin" else DARK)
        if mood == "happy":
            P(lo - 1, my - 1, "mouth", DARK)
            if fc == 0:
                P(hi + 1, my - 1, "mouth", DARK)
            else:
                P(hi + 1, my - 1, "mouth", DARK)
            if f.get("lines") or f.get("cheek"):
                P(lo - 2, my - 1, "skin", DARK)
        if full:
            for x in range(lo, hi + 1):
                if abs(x - mc) <= 1:
                    P(x, my + 1, "mouth", LIT if x == mc - 1 else MID)
            P(mc, my - 1, "mouth", DARK) if lips == "full" else None
        else:
            P(mc, my + 1, "mouth", MID if mood == "happy" else DARK)
        if demon and self.species == "brute":
            P(lo, my - 1, "teeth", LIT)
            P(hi, my - 1, "teeth", LIT)

    # -- the faces of the other species --
    def face_skeleton(self, L, dec):
        P = lambda x, y, m, st: self._P(dec, x, y, m, st)
        mood, eyes = self.face_mood()
        ey, ein, ew, sx, ny, my = L["ey"], L["ein"], L["ew"], L["sx"], L["nose"], L["mouth"]
        fc = self.b.fc
        if L["cls"] == "XS":
            for x in ((-1, 1) if fc == 0 else (0, 1)):
                P(x, 0, "eye_d", EDGE)
            return
        sides = (-1, 1)
        for sg in sides:
            if fc == 1 and sg == 1:
                xs = [sx + ein]
            else:
                xs = [sx + sg * (ein + k) for k in range(max(1, ew - 1) if L["cls"] == "L" else 1)]
            for x in xs:
                for y in ((ey - 1, ey) if L["cls"] == "L" else (ey,)):
                    P(x, y, "eye_d", EDGE)
            if L["cls"] == "L":
                P(xs[-1], ey - 2, "horn", LIT)  # the brow of the socket
                P(xs[0] + sg, ey + 1, "horn", DARK)  # the cheekbone's underside
                if eyes == "open":
                    P(xs[0], ey, "eye_w", MID)  # a glint deep in the socket
        if L["cls"] == "L":
            P(sx, ny - 1, "eye_d", EDGE)
            P(sx + 1 if fc == 1 else sx, ny, "eye_d", EDGE)
            if fc == 0:
                P(sx - 1, ny, "eye_d", DARK)
            open_ = mood in ("cheer", "sing")
            for x in range(sx - 2, sx + 3):
                P(x, my, "teeth", LIT if x % 2 == 0 else MID)
                P(x, my + 1 + (1 if open_ else 0), "teeth", MID if x % 2 == 0 else DARK)
                if open_:
                    P(x, my + 1, "eye_d", EDGE)
            P(sx - 3, my, "horn", EDGE)
            P(sx + 3, my, "horn", EDGE)
        else:
            P(sx, my, "eye_d", EDGE if mood in ("cheer",) else DARK)

    def face_grey(self, L, dec):
        P = lambda x, y, m, st: self._P(dec, x, y, m, st)
        mood, eyes = self.face_mood()
        ey, sx = L["ey"], L["sx"]
        rx, ry = L["rx"], L["ry"]
        fc = self.b.fc
        if L["cls"] == "XS":
            for x in ((-1, 1) if fc == 0 else (0, 1)):
                P(x, 0, "eye_d", EDGE)
            return
        big = L["cls"] == "L"
        w = max(2, int(round(rx * 0.42))) if big else 1
        gap = max(1, int(round(rx * 0.18)))
        for sg in (-1, 1):
            far = fc == 1 and sg == 1
            ww = max(1, w - (2 if far else 0))
            inner = sx + sg * gap
            xs = [inner + sg * k for k in range(ww)]
            for k, x in enumerate(xs):
                t = k / max(1, ww - 1)  # 0 inner .. 1 outer: the almond lifts towards the outer corner
                if eyes != "open":
                    P(x, ey - (1 if t > 0.6 else 0), "eye_d", EDGE)
                    continue
                top = ey - 1 - (1 if t > 0.55 and big else 0)
                bot = ey + (1 if 0.15 < t < 0.85 and big else 0)
                for y in range(top, bot + 1):
                    P(x, y, "eye_d", EDGE if y < bot or not big else DARK)
            if eyes == "open" and big and not far:
                P(xs[min(len(xs) - 1, 1)], ey - 1, "eye_w", LIT)
                P(xs[0], ey + 1 if w > 2 else ey, "eye_w", MID) if w > 2 else None
        if big:
            ny, my = L["nose"] + 1, L["mouth"] + 1
            P(sx - 1 if fc == 0 else sx, ny, "skin", EDGE)
            P(sx + 1, ny, "skin", EDGE)
            if mood in ("cheer", "sing"):
                P(sx, my, "mouth", EDGE)
                P(sx, my + 1, "mouth", DARK)
            elif mood == "happy":
                for x in (sx - 1, sx, sx + 1):
                    P(x, my, "skin", EDGE)
                P(sx - 2, my - 1, "skin", DARK)
                P(sx + 2, my - 1, "skin", DARK)
            elif mood == "sad":
                for x in (sx - 1, sx, sx + 1):
                    P(x, my, "skin", EDGE)
                P(sx - 2, my + 1, "skin", DARK)
                P(sx + 2, my + 1, "skin", DARK)
            else:
                P(sx, my, "skin", EDGE)
                P(sx + 1, my, "skin", DARK)

    def face_cyclops(self, L, dec):
        P = lambda x, y, m, st: self._P(dec, x, y, m, st)
        mood, eyes = self.face_mood()
        ey, sx = L["ey"], L["sx"]
        fc = self.b.fc
        if L["cls"] == "XS":
            P(sx, 0, "eye_w", MID)
            return
        if L["cls"] == "S":
            if eyes == "open":
                P(sx - 1, ey, "eye_w", MID)
                P(sx, ey, "eye_d", EDGE)
                P(sx + 1, ey, "eye_w", DARK)
            else:
                for x in (sx - 1, sx, sx + 1):
                    P(x, ey, "skin", EDGE)
            P(sx, ey - 1, "skin", EDGE)
            self.mouth(P, dec, L, mood, {"lips": "wide"})
            return
        # one great eye: white almond, a ringed iris with its pupil and catch light, a heavy lid and brow
        if eyes == "open":
            for dx in range(-3, 4):
                for dy in range(-1, 2):
                    if abs(dx) == 3 and dy != 0:
                        continue
                    P(sx + dx, ey + dy, "eye_w", LIT if dy < 0 and dx < 0 else (MID if dy < 1 else DARK))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if abs(dx) + abs(dy) <= 1 or True:
                        P(sx + dx, ey + dy, "eye_d", MID if abs(dx) + abs(dy) == 2 else DARK)
            P(sx, ey, "eye_d", EDGE)
            P(sx - 1, ey - 1, "eye_w", LIT)
            for dx in range(-3, 4):
                P(sx + dx, ey - 2, "skin", EDGE if abs(dx) < 3 else DARK)
        else:
            for dx in range(-3, 4):
                P(sx + dx, ey + (0 if abs(dx) < 2 else (-1 if eyes == "bliss" else 1)) * (1 if abs(dx) >= 2 else 0), "skin", EDGE)
                P(sx + dx, ey - 1, "skin", LIT)
        by = ey - 3 - (1 if mood == "cheer" else 0)
        for dx in range(-3, 4):
            y = by + (1 if (mood == "sad" and abs(dx) > 1) else 0) - (1 if (mood == "sad" and abs(dx) <= 1) else 0)
            P(sx + dx, y, "hair" if (self.hair.get("style") not in ("none", None)) else "skin", EDGE)
        self.mouth(P, dec, L, mood, {"lips": "wide"})

    def face_insect(self, L, dec):
        P = lambda x, y, m, st: self._P(dec, x, y, m, st)
        mood, eyes = self.face_mood()
        ey, sx = L["ey"], L["sx"]
        rx = L["rx"]
        fc = self.b.fc
        if L["cls"] == "XS":
            for x in ((-1, 1) if fc == 0 else (0, 1)):
                P(x, 0, "eye_d", DARK)
            return
        big = L["cls"] == "L"
        for sg in (-1, 1):
            if fc == 1 and sg == 1:
                cx = sx + int(round(rx * 0.5))
            else:
                cx = sx + sg * int(round(rx * 0.55))
            pts = [(0, 0)] if not big else [(dx, dy) for dx in (-1, 0, 1) for dy in (-2, -1, 0, 1) if not (abs(dx) == 1 and dy in (-2, 1))]
            for dx, dy in pts:
                x, y = cx + dx, ey + dy
                st = DARK if (x + y) % 2 == 0 else MID  # the facets
                P(x, y, "eye_d", st if big else EDGE)
            if big:
                P(cx - 1 if sg < 0 or fc == 1 else cx, ey - 1, "eye_w", LIT)
                P(cx + (1 if sg > 0 else 0), ey + 1, "eye_d", EDGE)
        if big:
            my = L["mouth"] + 1
            open_ = mood in ("cheer", "sing")
            for sg in ((-1, 1) if fc == 0 else (1,)):
                P(sx + sg * 1, my, "horn", DARK)
                P(sx + sg * (2 if open_ else 1), my + 1, "horn", EDGE)
            if open_:
                P(sx, my, "mouth", EDGE)

    def face_blob(self, L, dec):
        P = lambda x, y, m, st: self._P(dec, x, y, m, st)
        mood, eyes = self.face_mood()
        ey, sx, ein = L["ey"], L["sx"], L["ein"]
        fc = self.b.fc
        if L["cls"] == "XS":
            for x in ((-1, 1) if fc == 0 else (0, 1)):
                P(x, 0, "eye_d", EDGE)
            return
        big = L["cls"] == "L"
        for sg in (-1, 1):
            x0 = sx + sg * (ein + 1) if not (fc == 1 and sg == 1) else sx + ein + 1
            if eyes != "open":
                P(x0, ey, "eye_d", EDGE)
                P(x0 + 1, ey - 1 if eyes == "bliss" else ey, "eye_d", EDGE) if big else None
                continue
            if big:
                for dx in (0, 1):
                    for dy in (-1, 0):
                        P(x0 + dx - (1 if sg < 0 else 0), ey + dy, "eye_d", EDGE)
                P(x0 - (1 if sg < 0 else 0), ey - 1, "eye_w", LIT)
            else:
                P(x0, ey, "eye_d", EDGE)
        my = L["mouth"]
        if big:
            w = 3
            for x in range(sx - w, sx + w + 1):
                curve = (1 if abs(x - sx) < w else 0) if mood in ("happy", "cheer", "sing", "neutral") else (0 if abs(x - sx) < w else 1)
                P(x, my + curve - 1, "mouth", EDGE)
            if mood in ("cheer", "sing"):
                for x in range(sx - 2, sx + 3):
                    P(x, my + 1, "mouth", DARK)
                P(sx - 1, my, "teeth", LIT)
                P(sx + 1, my, "teeth", MID)
        else:
            P(sx, my, "mouth", EDGE)

    # -- hair --
    def hair_style(self):
        return self.hair.get("style", "short")

    def hair_back(self):
        """The hair that hangs behind the head and shoulders (long hair, locs, braids, a ponytail in the back view)."""
        b, S, cv = self.b, self.S, self.cv
        st = self.hair_style()
        hat = (self.hat or {}).get("kind")
        if hat in ("scarf",):
            self.scarf_back()
            return
        rx, ry = b.head_w * 0.5, b.head_h * 0.5
        c, ang = b.head_c, b.head_ang
        length = {"long": 0.27, "bob": 0.09, "locs": 0.22, "braids": 0.24, "curly_long": 0.2, "ponytail": 0.16, "wavy": 0.2, "pigtails": 0.1,
                  "tentacles": 0.2, "flames": 0.0}.get(st, 0.0) * S * float(self.hair.get("len", 1.0))
        if length <= 0:
            return
        z = 1.5 if b.fc == 2 else -1.5
        seed = self.seed
        if st in ("locs", "braids", "tentacles"):
            n = 7 if st != "tentacles" else 5
            for i in range(n):
                a0 = -1.0 + 2.0 * i / (n - 1)
                top = self.F(c, ang, a0 * rx * 0.95, -ry * 0.1)
                end = (top[0] + a0 * rx * 0.5, top[1] + length * (0.85 + 0.15 * ((i * 7 + seed) % 3) / 2))
                r = (0.014 if st != "tentacles" else 0.02) * S
                capsule(cv, top, end, r, r * 0.8, z, lambda t, u, st=st: (np.where((np.floor(t * length / 2.0) % 2 == 0) & (st == "braids"), M["hair2"], M["hair"])
                                                                              if st != "tentacles" else M["skin2"], 0.0))
            return
        if st == "ponytail" and b.fc != 2:
            top = self.F(c, ang, rx * 0.9, -ry * 0.3)
            capsule(cv, top, (top[0] + 0.03 * S, top[1] + length), 0.028 * S, 0.014 * S, -1.5, lambda t, u: (M["hair"], 0.2 * (np.sin(u * 4) > 0.5)))
            return
        if st == "pigtails":
            for sg in (-1, 1):
                top = self.F(c, ang, sg * rx * 1.05, -ry * 0.05)
                capsule(cv, top, (top[0] + sg * 0.025 * S, top[1] + length), 0.022 * S, 0.016 * S, 2.35, lambda t, u: (M["hair"], 0.0))
            return
        w0, w1 = rx * 1.12, rx * (1.25 if st != "bob" else 1.15)
        rows = [(-ry * 0.6, w0, w0), (ry * 0.8, w1, w1), (ry + length, w1 * (0.95 if st != "bob" else 1.0), w1 * (0.95 if st != "bob" else 1.0))]

        def mat(lx, ly, u):
            ex = np.where(np.sin(lx * 1.7 + np.sin(ly * 0.25) * 1.5 + seed) > 0.55, -0.3, 0.0)
            ex += np.where(np.sin(lx * 1.7 + 1.9 + seed) > 0.85, 0.25, 0.0)
            m = np.full(u.shape, M["hair"], np.uint8)
            if st in ("long", "wavy", "curly_long"):
                m = np.where((ly > ry + length - 3) & (_hash01(np.round(lx), 3, seed) > 0.55), 0, m)
            return m, ex
        profile(cv, c, ang * 0.5, rows, z, mat)

    def hair_front(self, c, rx, ry, ang):
        """The hair on the head: a cap with a hairline and strands, curls, a fringe, a bun, a mohawk, flames..."""
        b, S, cv = self.b, self.S, self.cv
        st = self.hair_style()
        hat = (self.hat or {}).get("kind")
        if st in ("bald",) or self.species in ("grey", "skeleton", "insect", "blob", "cyclops") and st in ("bald", "short", "none"):
            return
        if st == "none":
            return
        seed = self.seed
        back = b.fc == 2
        part = self.hair.get("part", 0.0)
        vol = {"curly": 1.32, "afro": 1.6, "curly_long": 1.3, "spiky": 1.12, "short": 1.07, "buzz": 1.0, "shaved": 1.0, "bun": 1.08,
               "mohawk": 1.0, "long": 1.09, "bob": 1.12, "ponytail": 1.07, "wavy": 1.12, "pigtails": 1.08, "locs": 1.1, "braids": 1.06,
               "tentacles": 1.05, "flames": 1.0, "perm": 1.3, "quiff": 1.1}.get(st, 1.07)
        if hat in ("beanie", "bucket", "chef", "scrubcap", "scarf", "cap"):
            vol = min(vol, 1.12) if st not in ("afro", "curly") else vol * 0.92
        z = 2.3
        line = {"long": 0.45, "bob": 0.55, "wavy": 0.5, "curly_long": 0.5, "pigtails": 0.25}.get(st, 0.15)
        cy = -ry * (0.08 if vol < 1.2 else 0.2)
        R = rx * vol

        def mat(lx, ly, u, v):
            uu, vv = lx / rx, ly / ry
            if back:
                keep = vv < 0.62 if st not in ("long", "wavy", "curly_long", "bob", "locs", "braids", "ponytail") else vv < 2.0
            else:
                # the hairline: a fringe across the forehead, lower at the temples (sideburns), with a parting
                hl = -0.42 + 0.22 * (uu - part) ** 2 + 0.05 * np.sin(uu * 9 + seed)
                if st in ("long", "bob", "wavy", "curly_long", "pigtails", "ponytail") and self.hair.get("fringe", True):
                    hl = -0.3 + 0.12 * np.abs(uu - part) + 0.06 * np.sin(uu * 11 + seed)
                side = np.abs(uu) > 0.78
                keep = (vv < hl) | (side & (vv < line))
                if st in ("curly", "afro", "perm"):
                    keep = (vv < -0.3 + 0.1 * np.sin(uu * 7 + seed)) | (np.abs(uu) > 0.92) & (vv < 0.4)
            m = np.where(keep, M["hair"], 0).astype(np.uint8)
            # strands: lines from the crown, a highlight at the upper left
            ang_ = np.arctan2(ly + ry * 1.3, lx)
            ex = np.where(np.sin(ang_ * (22 if st not in ("curly", "afro", "perm") else 9) + seed + np.sin(ly * 0.6)) > 0.45, -0.3, 0.0)
            if st in ("curly", "afro", "perm", "curly_long"):
                cl = _hash01(np.floor(lx / 1.5), np.floor(ly / 1.5), seed)
                ex = np.where(cl > 0.62, 0.3, np.where(cl < 0.3, -0.35, 0.0))
            ex += np.where((uu < -0.15) & (vv < -0.45) & (vv > -1.0), 0.18, 0.0)
            if st in ("buzz", "shaved"):
                m = np.where(keep & (_hash01(np.round(lx), np.round(ly), seed) > 0.45), M["hair"], np.where(keep, M["skin"], 0)).astype(np.uint8)
                ex = ex * 0 - 0.15
            if st == "mohawk":
                m = np.where(keep & (np.abs(uu) < 0.3), M["hair"], np.where(keep & (_hash01(np.round(lx), np.round(ly), seed) > 0.6), M["hair2"], 0)).astype(np.uint8)
            return m, ex

        def shape(u, v):
            k = 1.0
            if st in ("curly", "afro", "perm", "curly_long"):
                a = np.arctan2(v, u)
                k = (1.0 + 0.09 * np.sin(a * 11 + seed) + 0.05 * np.sin(a * 23 + seed * 3)) ** 2
            if st == "spiky":
                a = np.arctan2(v, u)
                k = np.where(v < 0, (1.0 + 0.16 * np.abs(np.sin(a * 7 + seed))) ** 2, 1.0)
            return k
        hc = self.F(c, ang, 0.0, cy)
        if st == "mohawk":
            stop = ry * 0.15 if not back else ry * 1.2  # the crest stops at the hairline in front (it ran down the face), at the nape behind
            ellipse(cv, self.F(c, ang, 0.0, -ry * 0.25), rx * 0.32, ry * 1.12, ang, z,
                    lambda lx, ly, u, v: (np.where(ly < stop - ry * 0.25 - ry * 0.25, M["hair"], 0).astype(np.uint8), np.where(v < -0.5, 0.2, -0.1)),
                    shape=lambda u, v: np.where(v < 0, (1.0 + 0.25 * np.abs(np.sin(v * 9))) ** 2, 1.0))
            ellipse(cv, c, R, ry * 1.04, ang, z - 0.01, mat)
            return
        if st == "flames":
            for i in range(7):
                a0 = -0.9 + 1.8 * i / 6
                base = self.F(c, ang, a0 * rx, -ry * 0.55)
                h_ = (0.07 + 0.05 * ((i * 5 + seed) % 3)) * S
                tip = (base[0] + 0.012 * S * math.sin(i * 2.1 + seed), base[1] - h_)
                poly_fill(cv, [(base[0] - 0.022 * S, base[1] + 0.01 * S), tip, (base[0] + 0.022 * S, base[1] + 0.01 * S)], z, "hair",
                          lambda X, Y, by=base[1], h_=h_: np.where(Y < by - h_ * 0.55, 0.9, np.where(Y < by - h_ * 0.25, 0.6, 0.3)))
                cv.dot(tip[0], tip[1] + 1.5, "lit", MID, z + 0.01)
            return
        ellipse(cv, hc, R, ry * (vol * 0.98 if vol < 1.3 else vol * 0.85), ang, z, mat, shape=shape)
        if st == "bun":
            bc = self.F(c, ang, rx * 0.1, -ry * 1.12)
            ellipse(cv, bc, rx * 0.42, ry * 0.32, ang, z + 0.01, lambda lx, ly, u, v: (M["hair"], -0.2 * (np.sin(lx * 2) > 0.5)))
        if st == "quiff" and not back:
            ellipse(cv, self.F(c, ang, -rx * 0.15, -ry * 0.92), rx * 0.7, ry * 0.32, ang - 0.25, z + 0.01, lambda *a: (M["hair"], 0.1))

    def scarf_back(self):
        b, S, cv = self.b, self.S, self.cv
        rx, ry = b.head_w * 0.5, b.head_h * 0.5
        rows = [(-ry * 0.2, rx * 1.2, rx * 1.2), (ry + 0.04 * S, rx * 1.55, rx * 1.55)]
        profile(cv, b.head_c, b.head_ang * 0.5, rows, -1.4 if b.fc != 2 else 1.6, lambda lx, ly, u: (M["hat"], -0.1 * (np.sin(lx * 0.8) > 0.5)))

    # -- hats --
    def hat_draw(self, c, rx, ry, ang):
        b, S, cv = self.b, self.S, self.cv
        hat = self.hat
        if not hat:
            return
        kind = hat.get("kind")
        z = 2.5
        F = lambda x, y: self.F(c, ang, x, y)
        tilt = ang
        if kind in ("cap", "cap_back"):
            ellipse(cv, F(0, -ry * 0.42), rx * 1.1, ry * 0.65, tilt, z, lambda lx, ly, u, v: np.where(v > 0.35, 0, M["hat"]).astype(np.uint8))
            if kind == "cap" and b.fc != 2:
                off = rx * 0.35 if b.fc == 1 else 0.0
                ellipse(cv, F(off, -ry * 0.25), rx * (1.15 if b.fc == 0 else 1.0), ry * 0.18, tilt, z + 0.02,
                        lambda lx, ly, u, v: (np.where(v > 0.2, M["hat2"], M["hat"]).astype(np.uint8), -0.15))
            else:
                ellipse(cv, F(0, -ry * 0.95), rx * 0.25, ry * 0.12, tilt, z + 0.02, lambda *a: M["hat2"])
            cv.dot(*F(0, -ry * 1.02), "hat2", LIT, z + 0.03)
        elif kind == "bucket":
            ellipse(cv, F(0, -ry * 0.5), rx * 1.08, ry * 0.62, tilt, z, lambda lx, ly, u, v: (np.where(v > 0.55, 0, M["hat"]).astype(np.uint8), -0.1 * (np.sin(lx) > 0.6)))
            rows = [(-ry * 0.32, rx * 1.12, rx * 1.12), (-ry * 0.08, rx * 1.48, rx * 1.48)]
            profile(cv, c, tilt, rows, z + 0.01, lambda lx, ly, u: (np.full(u.shape, M["hat"], np.uint8), np.where(ly > -ry * 0.16, -0.35, 0.1)))
        elif kind == "beanie":
            ellipse(cv, F(0, -ry * 0.45), rx * 1.1, ry * 0.75, tilt, z,
                    lambda lx, ly, u, v: (np.where(v > 0.55, 0, np.where(v > 0.12, M["hat2"], M["hat"])).astype(np.uint8), -0.25 * (np.round(lx) % 2 == 0)))
            if hat.get("pom"):
                ellipse(cv, F(0, -ry * 1.25), rx * 0.3, rx * 0.28, tilt, z + 0.01, lambda *a: (M["hat2"], 0.2))
        elif kind == "crown":
            n = 5
            base_y = -ry * 0.62
            pts = [F(-rx * 1.0, base_y + ry * 0.25)]
            for i in range(n):
                x0 = -rx + 2 * rx * i / (n - 1)
                pts.append(F(x0, base_y - ry * 0.45))
                if i < n - 1:
                    pts.append(F(x0 + rx / (n - 1), base_y - ry * 0.05))
            pts.append(F(rx * 1.0, base_y + ry * 0.25))
            poly_fill(cv, pts, z, "hat", lambda X, Y: 0.55 + 0.3 * (X < c[0]))
            for i in (-1, 0, 1):
                cv.dot(*F(i * rx * 0.55, base_y + ry * 0.05), "acc", LIT, z + 0.01)
        elif kind == "chef":
            ellipse(cv, F(0, -ry * 1.35), rx * 1.2, ry * 0.75, tilt, z,
                    lambda lx, ly, u, v: (M["hat"], 0.25 * np.sin(u * 5 + 1) - 0.1), shape=lambda u, v: (1 + 0.08 * np.sin(np.arctan2(v, u) * 7)) ** 2)
            rows = [(-ry * 0.95, rx * 0.95, rx * 0.95), (-ry * 0.42, rx * 1.0, rx * 1.0)]
            profile(cv, c, tilt, rows, z + 0.01, lambda lx, ly, u: (M["hat"], -0.05))
        elif kind == "bandana":
            ellipse(cv, F(0, -ry * 0.42), rx * 1.08, ry * 0.66, tilt, z,
                    lambda lx, ly, u, v: (np.where(v > 0.38, 0, np.where((np.round(lx) + np.round(ly)) % 4 == 0, M["hat2"], M["hat"])).astype(np.uint8), 0.0))
            if b.fc != 2:
                k0 = F(rx * 1.0, -ry * 0.25)
                capsule(cv, k0, (k0[0] + 0.03 * S, k0[1] + 0.05 * S), 0.011 * S, 0.006 * S, z + 0.01, lambda t, u: M["hat"])
        elif kind == "tricorn":
            pts = [F(-rx * 1.7, -ry * 0.55), F(0, -ry * 1.45), F(rx * 1.7, -ry * 0.55), F(0, -ry * 0.2)]
            poly_fill(cv, pts, z, "hat", lambda X, Y: 0.35 + 0.25 * (Y < c[1] - ry * 0.8))
            seg(cv, F(-rx * 1.6, -ry * 0.55), F(rx * 1.6, -ry * 0.55), "hat2", MID, z + 0.01)
        elif kind == "scrubcap":
            ellipse(cv, F(0, -ry * 0.38), rx * 1.08, ry * 0.68, tilt, z,
                    lambda lx, ly, u, v: (np.where(v > 0.42, 0, np.where(_hash01(np.floor(lx / 2), np.floor(ly / 2), 3) > 0.8, M["hat2"], M["hat"])).astype(np.uint8), 0.0))
        elif kind == "nursecap":
            pts = [F(-rx * 0.7, -ry * 0.75), F(rx * 0.7, -ry * 0.75), F(rx * 0.5, -ry * 1.2), F(-rx * 0.5, -ry * 1.2)]
            poly_fill(cv, pts, z, "hat", 0.7)
            cv.dot(*F(0, -ry * 1.0), "hat2", MID, z + 0.01)
        elif kind == "party":
            pts = [F(-rx * 0.5, -ry * 0.7), F(rx * 0.5, -ry * 0.7), F(rx * 0.1, -ry * 1.9)]
            poly_fill(cv, pts, z, "hat", lambda X, Y: np.where((np.round(Y) % 3) == 0, 0.9, 0.5))
        elif kind == "scarf":
            def mf(lx, ly, u, v):
                face = (u * u / 0.62 + (v - 0.18) ** 2 / 0.75) < 1.0
                m = np.where(face & (b.fc != 2), 0, M["hat"]).astype(np.uint8)
                return m, -0.2 * (np.sin(lx * 0.8 + ly * 0.4) > 0.6)
            ellipse(cv, F(0, ry * 0.05), rx * 1.25, ry * 1.18, tilt, z, mf)
        elif kind == "halo":
            ellipse(cv, F(0, -ry * 1.4), rx * 0.9, ry * 0.18, 0, z, lambda lx, ly, u, v: np.where(u * u + v * v < 0.45, 0, M["lit"]).astype(np.uint8))

    def headwear_props(self, c, rx, ry, ang):
        """Headphones (the DJ), the alien DJ's worn the wrong way round, an eyepatch, a mask."""
        b, S, cv = self.b, self.S, self.cv
        held = self.held
        F = lambda x, y: self.F(c, ang, x, y)
        z = 2.6
        if held == "headphones" or "phones" in self.acc:
            band = [F(math.cos(t) * rx * 1.15, -ry * 0.15 - math.sin(t) * ry * 1.15) for t in np.linspace(0.15, math.pi - 0.15, 12)]
            for i in range(len(band) - 1):
                seg(cv, band[i], band[i + 1], "acc", MID if i < 6 else DARK, z, 1.5 if S > 80 else 1.0)
            for sg in ((-1, 1) if b.fc != 1 else (-1,)):
                ellipse(cv, F(sg * rx * 1.08, ry * 0.05), rx * 0.32, ry * 0.32, ang, z + 0.01, lambda lx, ly, u, v: (np.where(u * u + v * v < 0.3, M["acc2"], M["acc"]).astype(np.uint8), 0.0))
        elif held == "headphones_wrong":  # the band across the face, one cup on the forehead, the other under the chin
            ellipse(cv, F(0, -ry * 0.62), rx * 0.42, ry * 0.3, ang, z + 0.01, lambda lx, ly, u, v: (np.where(u * u + v * v < 0.3, M["acc2"], M["acc"]).astype(np.uint8), 0.1))
            ellipse(cv, F(rx * 0.1, ry * 1.08), rx * 0.42, ry * 0.3, ang, z + 0.01, lambda lx, ly, u, v: (np.where(u * u + v * v < 0.3, M["acc2"], M["acc"]).astype(np.uint8), -0.1))
            seg(cv, F(rx * 0.42, -ry * 0.55), F(rx * 0.95, ry * 0.2), "acc", MID, z, 1.5 if S > 80 else 1.0)
            seg(cv, F(rx * 0.95, ry * 0.2), F(rx * 0.5, ry * 1.0), "acc", DARK, z, 1.5 if S > 80 else 1.0)
        if "eyepatch" in self.acc and b.fc != 2 and self.lod < 4:
            ex = rx * 0.42 + (rx * 0.38 if b.fc == 1 else 0)
            for dx in (-0.5, 0.5):
                for dy in (-0.5, 0.5):
                    cv.dot(*F(-ex + dx + (rx * 0.38 if b.fc == 1 else 0), ry * 0.1 + dy), "acc", EDGE, z)
            seg(cv, F(-rx, -ry * 0.4), F(rx, ry * 0.1), "acc", EDGE, z - 0.05)
        if "mask" in self.acc and b.fc != 2:
            for xx in np.arange(-rx * 0.9, rx * 0.95, 1.0):
                for dy in (-0.6, 0.4):
                    cv.dot(*F(xx + (rx * 0.38 if b.fc == 1 else 0), ry * 0.1 + dy), "acc", MID, z - 0.1)
            if self.lod < 4:
                for sg in (-1, 1):
                    cv.dot(*F(sg * rx * 0.42 + (rx * 0.38 if b.fc == 1 else 0), ry * 0.1), "eye_w", LIT, z)

    def species_head(self, c, rx, ry, ang):
        b, S, cv = self.b, self.S, self.cv
        spc = self.sp.get("species") or {}
        F = lambda x, y: self.F(c, ang, x, y)
        horns = spc.get("horns")
        z = 2.45
        if horns:
            n = 6
            for sg in (-1, 1):
                if horns == "small":
                    path = [(sg * rx * 0.45, -ry * 0.7), (sg * rx * 0.62, -ry * 1.05), (sg * rx * 0.7, -ry * 1.3)]
                    w0 = 0.02 * S
                elif horns == "ram":
                    path = [(sg * rx * (0.75 + 0.45 * math.sin(t)), -ry * 0.5 + ry * 0.55 * math.cos(t) - ry * 0.3) for t in np.linspace(0, 4.2, n)]
                    w0 = 0.026 * S
                elif horns == "long":
                    path = [(sg * rx * (0.5 + 0.12 * k), -ry * (0.75 + 0.55 * k)) for k in range(n)]
                    w0 = 0.024 * S
                else:  # big: out and up
                    path = [(sg * rx * (0.7 + 0.3 * k), -ry * (0.6 + 0.08 * k * k)) for k in range(n)]
                    w0 = 0.03 * S
                pts = [F(*p) for p in path]
                for i in range(len(pts) - 1):
                    r0 = w0 * (1 - i / len(pts))
                    r1 = w0 * (1 - (i + 1) / len(pts))
                    capsule(cv, pts[i], pts[i + 1], max(r0, 0.6), max(r1, 0.5), z, lambda t, u, i=i: (M["horn"], 0.05 * (i % 2)))
        if spc.get("antennae"):
            for sg in (-1, 1):
                p0 = F(sg * rx * 0.35, -ry * 0.85)
                p1 = (p0[0] + sg * 0.03 * S, p0[1] - 0.09 * S)
                seg(cv, p0, p1, "extra", MID, z)
                ellipse(cv, p1, 0.016 * S, 0.016 * S, 0, z + 0.01, lambda *a: M["lit"])

    # -- accessories --
    def accessories(self):
        b, S, cv = self.b, self.S, self.cv
        acc = self.acc
        front = b.fc != 2
        ts = b.t_shoulder
        if "strap" in acc:
            p0 = b.T((-b.sw * 0.7 * b.mir, ts - 0.005 * S))
            p1 = b.T((b.hip_hw * 0.95 * b.mir, -0.02 * S))
            seg(cv, p0, p1, "acc", DARK, 1.5, 1.5 if S > 80 else 1.0)
            ellipse(cv, (p1[0] + 0.01 * S * b.mir, p1[1] + 0.02 * S), 0.035 * S, 0.028 * S, 0, 1.55, lambda *a: (M["acc"], 0.0))
        if "necklace" in acc and front and self.lod < 4:
            for k in np.linspace(-1, 1, 7):
                cv.dot(*b.T((k * 0.03 * S, ts + 0.008 * S + (1 - k * k) * 0.025 * S)), "acc2", LIT, 1.1)
        if "lanyard" in acc and front:
            seg(cv, b.T((-0.025 * S, ts - 0.005 * S)), b.T((0.0, ts + 0.1 * S)), "acc", MID, 1.12)
            seg(cv, b.T((0.025 * S, ts - 0.005 * S)), b.T((0.0, ts + 0.1 * S)), "acc", MID, 1.12)
            poly_fill(cv, [b.T((-0.016 * S, ts + 0.1 * S)), b.T((0.016 * S, ts + 0.1 * S)), b.T((0.016 * S, ts + 0.14 * S)), b.T((-0.016 * S, ts + 0.14 * S))],
                      1.13, "acc2", 0.8)
        if "stethoscope" in acc and front:
            pts = [b.T((x * 0.06 * S, ts + 0.01 * S + (1 - x * x) * 0.05 * S)) for x in np.linspace(-1, 1, 9)]
            for i in range(len(pts) - 1):
                seg(cv, pts[i], pts[i + 1], "metal", DARK, 1.14)
            seg(cv, pts[-1], b.T((0.07 * S, ts + 0.12 * S)), "metal", DARK, 1.14)
            cv.dot(*b.T((0.07 * S, ts + 0.125 * S)), "metal", LIT, 1.15)
        if "phones_neck" in acc:
            for x in np.linspace(-1, 1, 7):
                cv.dot(*b.T((x * 0.045 * S, ts + 0.0 + (1 - x * x) * 0.02 * S)), "acc", MID, 1.16)
            for sg in (-1, 1):
                ellipse(cv, b.T((sg * 0.045 * S, ts + 0.008 * S)), 0.018 * S, 0.016 * S, 0, 1.17, lambda *a: M["acc"])
        if "belt" in acc and front:
            seg(cv, b.T((-b.waist_hw * 1.05, -0.045 * S)), b.T((b.waist_hw * 1.05, -0.045 * S)), "acc", DARK, 1.12, 1.5 if S > 80 else 1.0)
            cv.dot(*b.T((0.0, -0.045 * S)), "acc2", LIT, 1.13)
        if "sash" in acc:
            p0 = b.T((b.sw * 0.7 * b.mir, ts))
            p1 = b.T((-b.hip_hw * 0.9 * b.mir, -0.03 * S))
            for d in (-1, 0, 1):
                seg(cv, (p0[0] + d, p0[1]), (p1[0] + d, p1[1]), "acc", MID if d else LIT, 1.18)
        if "scarf" in acc:
            ellipse(cv, b.T((0.0, ts - 0.005 * S)), 0.055 * S * b.W, 0.022 * S, b.lean, 1.19, lambda lx, ly, u, v: (M["acc"], -0.2 * (np.round(lx) % 3 == 0)))
            if front:
                capsule(cv, b.T((0.02 * S, ts)), b.T((0.03 * S, ts + 0.12 * S)), 0.014 * S, 0.012 * S, 1.2, lambda t, u: (np.where(t > 0.85, M["acc2"], M["acc"]).astype(np.uint8), 0.0))
        if "bow" in acc and front:
            p = b.T((0.0, ts + 0.005 * S))
            poly_fill(cv, [(p[0] - 0.035 * S, p[1] - 0.015 * S), (p[0], p[1]), (p[0] - 0.035 * S, p[1] + 0.015 * S)], 1.2, "acc", 0.6)
            poly_fill(cv, [(p[0] + 0.035 * S, p[1] - 0.015 * S), (p[0], p[1]), (p[0] + 0.035 * S, p[1] + 0.015 * S)], 1.2, "acc", 0.4)
        if "harness" in acc:
            for sg in (-1, 1):
                seg(cv, b.T((sg * b.sw * 0.6, ts - 0.005 * S)), b.T((-sg * b.waist_hw * 0.8, b.t_waist)), "acc", DARK, 1.15, 1.5 if S > 80 else 1.0)
            cv.dot(*b.T((0.0, (ts + b.t_waist) * 0.5)), "metal", LIT, 1.16)
        if "plates" in acc:
            for sg in (-1, 1):
                ellipse(cv, b.T((sg * b.sw * 0.95, ts + 0.005 * S)), 0.05 * S, 0.035 * S, b.lean, 1.7, lambda lx, ly, u, v: (M["metal"], 0.15 * (v < -0.2)))

    # -- props in the hand --
    def prop(self):
        held = self.held
        if not held or held in ("headphones", "headphones_wrong"):
            return
        b, S, cv = self.b, self.S, self.cv
        a = b.arms["r"]
        hx, hy = a["hand"]
        z = self.arm_z("r") + 0.1
        if held in ("cup", "mug", "bottle"):
            if held == "bottle":
                w, h = 0.013 * S, 0.06 * S
                top = hy - h * 0.62
                poly_fill(cv, [(hx - w, top), (hx + w, top), (hx + w, top + h), (hx - w, top + h)], z, "glass",
                          lambda X, Y: np.where(X < hx - w * 0.3, 0.85, 0.5))
                poly_fill(cv, [(hx - w * 0.5, top - 0.012 * S), (hx + w * 0.5, top - 0.012 * S), (hx + w * 0.5, top), (hx - w * 0.5, top)], z + 0.01, "acc", 0.5)
            else:
                w0, w1, h = 0.022 * S, 0.016 * S, 0.05 * S
                top = hy - h * 0.6
                liquid = "liquid" if held == "cup" else "prop"

                def mk(X, Y):
                    return np.where(X < hx - w1 * 0.4, 0.85, 0.5)
                mat = "glass" if held == "cup" else "prop"
                poly_fill(cv, [(hx - w0, top), (hx + w0, top), (hx + w1, top + h), (hx - w1, top + h)], z, mat, mk)
                if held == "cup":
                    poly_fill(cv, [(hx - w0 * 0.85, top + h * 0.3), (hx + w0 * 0.85, top + h * 0.3), (hx + w1 * 0.9, top + h - 1), (hx - w1 * 0.9, top + h - 1)],
                              z + 0.01, liquid, lambda X, Y: np.where(Y < top + h * 0.42, 0.9, 0.5))
                else:
                    seg(cv, (hx + w0, top + h * 0.3), (hx + w0 + 0.012 * S, top + h * 0.55), "prop", DARK, z)
        elif held == "phone":
            w, h = 0.012 * S, 0.022 * S
            poly_fill(cv, [(hx - w, hy - h), (hx + w, hy - h), (hx + w, hy + h * 0.3), (hx - w, hy + h * 0.3)], z + 0.2, "eye_d", 0.3)
            poly_fill(cv, [(hx - w * 0.6, hy - h * 0.8), (hx + w * 0.6, hy - h * 0.8), (hx + w * 0.6, hy + h * 0.1), (hx - w * 0.6, hy + h * 0.1)], z + 0.21, "lit", 0.6)
        elif held == "clipboard":
            w, h = 0.035 * S, 0.048 * S
            cx, cy = hx - 0.02 * S, hy - 0.01 * S
            poly_fill(cv, [(cx - w, cy - h), (cx + w, cy - h), (cx + w, cy + h), (cx - w, cy + h)], z, "furn", 0.5)
            poly_fill(cv, [(cx - w * 0.8, cy - h * 0.82), (cx + w * 0.8, cy - h * 0.82), (cx + w * 0.8, cy + h * 0.9), (cx - w * 0.8, cy + h * 0.9)], z + 0.01, "prop2",
                      lambda X, Y: np.where((np.round(Y - cy) % 3 == 0) & (np.abs(X - cx) < w * 0.6), 0.25, 0.8))
            cv.dot(cx, cy - h, "metal", LIT, z + 0.02)
        elif held == "tickets":
            for k in range(3):
                ox = hx + (k - 1) * 0.012 * S
                poly_fill(cv, [(ox - 0.012 * S, hy - 0.035 * S), (ox + 0.012 * S, hy - 0.04 * S), (ox + 0.014 * S, hy - 0.005 * S), (ox - 0.01 * S, hy)],
                          z + 0.01 * k, "prop2" if k % 2 == 0 else "prop", 0.75)
        elif held == "brush":
            fd = a["fd"]
            tip = (hx + fd[0] * 0.07 * S, hy + fd[1] * 0.07 * S - 0.02 * S)
            tail = (hx - fd[0] * 0.03 * S, hy - fd[1] * 0.03 * S)
            seg(cv, tail, tip, "furn", MID, z)
            cv.dot(tip[0], tip[1], "prop", LIT, z + 0.01)
            cv.dot(tip[0] + 0.5, tip[1] + 0.5, "prop", MID, z + 0.01)
        elif held == "sketchbook":
            w, h = 0.04 * S, 0.05 * S
            cx, cy = hx - 0.025 * S, hy - 0.012 * S
            poly_fill(cv, [(cx - w, cy - h), (cx + w, cy - h), (cx + w, cy + h), (cx - w, cy + h)], z, "prop", 0.45)
            poly_fill(cv, [(cx - w * 0.82, cy - h * 0.85), (cx + w * 0.82, cy - h * 0.85), (cx + w * 0.82, cy + h * 0.85), (cx - w * 0.82, cy + h * 0.85)], z + 0.01, "prop2",
                      lambda X, Y: np.where(((X - cx) ** 2 + (Y - cy) ** 2) < (0.02 * S) ** 2, 0.3, 0.85))
        elif held == "tray":
            l = b.arms["l"]["hand"]
            cx = (hx + l[0]) * 0.5
            ty = min(hy, l[1]) - 0.008 * S
            w = max(abs(hx - l[0]) * 0.5 + 0.03 * S, 0.07 * S)
            poly_fill(cv, [(cx - w, ty - 0.008 * S), (cx + w, ty - 0.008 * S), (cx + w * 0.95, ty + 0.006 * S), (cx - w * 0.95, ty + 0.006 * S)], z + 0.3, "metal",
                      lambda X, Y: np.where(Y < ty - 0.004 * S, 0.85, 0.4))
            for k, (dx, mat) in enumerate(((-0.6, "glass"), (0.0, "liquid"), (0.55, "glass"))):
                gx = cx + dx * w
                gh = 0.035 * S
                poly_fill(cv, [(gx - 0.012 * S, ty - 0.008 * S - gh), (gx + 0.012 * S, ty - 0.008 * S - gh), (gx + 0.009 * S, ty - 0.008 * S), (gx - 0.009 * S, ty - 0.008 * S)],
                          z + 0.31, mat, lambda X, Y, gx=gx: np.where(X < gx, 0.85, 0.5))
        elif held == "drip":
            px_ = hx + 0.035 * S
            top = -1.08 * b.S
            z0 = 0.4
            seg(cv, (px_, -0.01 * S), (px_, top), "metal", MID, z0, 1.5 if S > 80 else 1.0)
            seg(cv, (px_ - 0.04 * S, -0.004 * S), (px_ + 0.04 * S, -0.004 * S), "metal", DARK, z0)
            cv.dot(px_ - 0.04 * S, 0.0, "eye_d", EDGE, z0)
            cv.dot(px_ + 0.04 * S, 0.0, "eye_d", EDGE, z0)
            seg(cv, (px_ - 0.025 * S, top), (px_ + 0.025 * S, top), "metal", MID, z0)
            bag = [(px_ - 0.028 * S, top + 0.01 * S), (px_ + 0.028 * S, top + 0.01 * S), (px_ + 0.022 * S, top + 0.085 * S), (px_ - 0.022 * S, top + 0.085 * S)]
            poly_fill(cv, bag, z0 + 0.01, "glass", lambda X, Y: np.where(Y > top + 0.04 * S, 0.5, 0.85))
            ln = [(px_ - 0.005 * S, top + 0.09 * S), (px_ - 0.03 * S, top + 0.35 * S), (hx, hy)]
            seg(cv, ln[0], ln[1], "glass", LIT, z0 + 0.02)
            seg(cv, ln[1], ln[2], "glass", LIT, z0 + 0.02)



# ---- one frame ----------------------------------------------------------------------------------------------------------------------------------------

def render_frame(spec: dict, pose: dict, state: str, facing: int, lod: int, held: str, face: str, seed: int):
    """Draw one frame. Returns (index image uint8 [h, w], pivot (x, y) of the feet in the image, hand (x, y) of the right hand in the image) with the
    image trimmed to its pixels."""
    S = H0 / lod * float(spec.get("height", 1.0))
    lie = state == "lie"
    if lie:
        state_draw, pose = "idle", dict(pose, arm_l=0.12, arm_r=0.12, elb_l=0.2, elb_r=0.25, leg_l=0.02, leg_r=0.02, lean=0.0, head_tilt=0.0, head_drop=0.0)
    else:
        state_draw = state
    w = int(S * 1.1) + 8
    h = int(S * 1.45) + 8
    ox, oy = w / 2.0, h - 4.0
    cv = Canvas(w, h, ox, oy)
    b = Body(spec, pose, S, facing, state_draw)
    Painter(cv, b, spec, lod, held, face if not lie else "sleep", seed).draw()
    if lie:
        _blanket(cv, b, S)
    idx = finish(cv)
    hand = b.arms["r"]["hand"]
    hand_px = (hand[0] + ox, hand[1] + oy)
    pivot = (ox, oy)
    if lie:  # lying down: the figure turned a quarter (head to the left), the feet stay at the pivot
        idx = np.rot90(idx, 1)  # counter-clockwise
        H_, W_ = h, w
        pivot = (oy, W_ - ox)
        hand_px = (hand_px[1], W_ - hand_px[0])
        pivot = (pivot[0], pivot[1] - 0.12 * S)
    ys, xs = np.nonzero(idx)
    if len(xs) == 0:
        return np.zeros((1, 1), np.uint8), (0.0, 0.0), (0.0, 0.0)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return idx[y0:y1, x0:x1].copy(), (pivot[0] - x0, pivot[1] - y0), (hand_px[0] - x0, hand_px[1] - y0)


def _blanket(cv: Canvas, b: Body, S: float):
    """A sheet over a lying person, from the feet to the chest (they are in bed)."""
    y0 = b.T((0.0, b.t_shoulder + 0.08 * S))[1]
    rows = [(y0 - b.hip[1], b.chest_hw * 1.35, b.chest_hw * 1.35), (0.0, b.hip_hw * 1.5, b.hip_hw * 1.5), (-b.hip[1] + 0.01 * S, b.hip_hw * 1.3, b.hip_hw * 1.3)]
    profile(cv, b.hip, 0.0, rows, 3.0, lambda lx, ly, u: (np.where(ly < y0 - b.hip[1] + 0.02 * S, M["furn2"], M["furn"]).astype(np.uint8),
                                                         -0.25 * (np.sin(ly * 0.35 + lx * 0.2) > 0.6)))
