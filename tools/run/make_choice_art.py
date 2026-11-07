"""The choice language's own props (docs/CHOICE_CLARITY.md "Art"), drawn by code into assets/run/choice/ (deterministic; rerun after an edit, then
`godot --headless --path . --import`). Package A4 of docs/art/VISUAL_AUDIT.md (findings F3, F11, F12): every world has its own set.

    python tools/run/make_choice_art.py                 draw everything
    python tools/run/make_choice_art.py --check         the style checks (docs/art/STYLE_GUIDE.md sections 6, 7) over what was drawn
    python tools/run/make_choice_art.py --sheet <jpg>   a contact sheet of every set in every state

Every prop is a billboard the choice layer (src/run/choice_props.gd) stands in the world at an option's anchor; ChoiceProps looks a name up in the folder of
the stage's world first (assets/run/choice/<set>/<name>.png, SET_MAPS below) and falls back to the shared file (assets/run/choice/<name>.png).

* door_0..door_3   the world's way out (a fire door, an iris hatch, a gate of bone and iron, ward doors...), from shut (0) to wide open (3). 144 x 288 px for
                   1.2 x 2.4 m (120 px/m), the bottom centre on the floor (the footprint of the old 48 x 96 door). Open, the doorway shows a dark room or passage
                   in the world's own colours with a lit doorway at its far end and its light on the floor: a calm, dark hint of where it leads.
* bars             the world's "no way": two members crossed in an X over a doorway (hazard tape, chains and a padlock, crossed planks, lashed poles...).
                   192 x 192 px (drawn 0.7 x the door height: about 114 px/m).
* lamp_go          a lamp of the world (a cage lamp, a console light, a brazier, a call light, an oil lantern...) with a ROUND lens lit green, the light
                   inside it shaped as an up chevron. 44 x 44 px for 0.34 m.
* lamp_stop        the same fixture with a SQUARE lens lit red, a bar of light across it.
* lamp_lit         the same fixture with a plain round lens of warm white glass and no symbol in it (package A7, lead ruling 35b): the engine lights it by the choice's
                   state (ChoiceShow: off, dim, lit, open; a red flicker for a cost) by tinting it, so it reads as a practical lamp of the room, not a sign.
* sign_go/stop     an outdoor way: a post in the world's wood; GO its arrow board level and pointing on, STOP the board hanging askew with an X daubed on it.
* spill            the light an open door throws on the floor (additive, the world's light colour, stepped and dithered).
* wizard_happy/sad the Warehouse wizard (from assets/story/night_one/textures/thing_wizard.png) beckoning or bowed, his coloured rim light taken off
                   (style guide 6: no halo outline). Shared by every world (A2 replaces him with a baked person).
Colour is never the only signal: open vs shut, round vs square, the chevron vs the bar, the board level vs hanging, arm up vs head down.
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "assets", "run", "choice")

W, H = 144, 288          # door and sign: 1.2 x 2.4 m
BN = 192                 # bars
LN = 44                  # lamp
SPW, SPH = 192, 96       # spill
DOOR_M, LAMP_M, BARS_M = 2.4, 0.34, 2.4 * 0.7

# which map draws which set (ChoiceProps.SETS mirrors this; the Bassment's zones are every map named bassment_*)
SET_MAPS = {
    "warehouse": ["night_one"], "ship": ["mothership"], "hell": ["underworld"], "hospital": ["hospital"], "ward": ["mental_hospital"],
    "galilee": ["galilee_shore", "hillside", "bethany"], "jerusalem": ["jerusalem"],
    "airfield": ["airfield"], "city": ["city"], "harbour": ["harbour"],
    "orchard": ["orchard"], "birch": ["birch_hall"], "deeps": ["deep_halls"], "ash": ["ash_land"],
    "bassment": ["bassment_*"],
}


# --- pixel helpers ---------------------------------------------------------------------------------------------------------------
def hexc(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def ramp(*cols: str, n: int = 0) -> np.ndarray:
    """A colour ramp dark -> light; with n, the given keys are spread over n steps."""
    keys = np.stack([hexc(c) for c in cols])
    if not n or n == len(keys):
        return keys
    t = np.linspace(0, len(keys) - 1, n)
    i = np.minimum(t.astype(int), len(keys) - 2)
    f = (t - i)[:, None]
    return np.round(keys[i] * (1 - f) + keys[i + 1] * f)


_B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16.0 + 1.0 / 32.0


def bayer(h: int, w: int) -> np.ndarray:
    return np.tile(_B4, (h // 4 + 1, w // 4 + 1))[:h, :w]


def hash2(x: np.ndarray, y: np.ndarray, seed: int = 0) -> np.ndarray:
    x, y = np.broadcast_arrays(np.asarray(x).astype(np.int64), np.asarray(y).astype(np.int64))
    v = (x * 73856093) ^ (y * 19349663) ^ (int(seed) * 83492791)
    v = (v ^ (v >> 13)) * 1274126177
    return ((v ^ (v >> 16)) & 0xFFFF).astype(np.float32) / 65535.0


def vnoise(h: int, w: int, cell: int, seed: int) -> np.ndarray:
    """Smooth value noise 0..1, deterministic."""
    gy, gx = h // cell + 2, w // cell + 2
    g = np.random.default_rng(seed).random((gy, gx)).astype(np.float32)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32) / cell
    x0, y0 = x.astype(int), y.astype(int)
    fx, fy = x - x0, y - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = g[y0, x0], g[y0, x0 + 1], g[y0 + 1, x0], g[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def _fine(rp: np.ndarray, n: int = 8) -> np.ndarray:
    t = np.linspace(0, len(rp) - 1, n)
    i = np.minimum(t.astype(int), len(rp) - 2)
    f = (t - i)[:, None]
    return np.round(rp[i] * (1 - f) + rp[i + 1] * f)


class Cv:
    """An RGBA canvas (float 0..255) with ramp painting: a value field 0..1 is quantised to a ramp through the 4x4 ordered dither."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.float32)
        self.y, self.x = np.mgrid[0:h, 0:w]
        self.d = bayer(h, w)

    def solid(self, mask: np.ndarray, col) -> None:
        self.a[mask, :3] = np.asarray(col, np.float32)
        self.a[mask, 3] = 255

    def paint(self, mask: np.ndarray, val, rp: np.ndarray, spread: float = 0.15, fine: bool = True) -> None:
        """`fine`: the ramp is spread over 8 steps first, so the grain and wear of a surface move a short step, not a blotch from dark to light."""
        val = np.broadcast_to(np.asarray(val, np.float32), mask.shape)
        if fine and len(rp) < 8:
            rp = _fine(rp)
        n = len(rp)
        f = np.clip(val, 0, 1) * (n - 1) + (self.d - 0.5) * spread
        i = np.clip(np.floor(f + 0.5).astype(int), 0, n - 1)
        self.a[mask, :3] = rp[i][mask]
        self.a[mask, 3] = 255

    def darken(self, mask: np.ndarray, k: float) -> None:
        self.a[mask, :3] *= k

    def opaque(self) -> np.ndarray:
        return self.a[..., 3] > 127

    def outline(self, k: float = 0.62) -> None:
        """The one-pixel darker edge of the silhouette (style guide 6: no black outline, one step darker than the local colour)."""
        o = self.opaque()
        inner = o.copy()
        inner[1:, :] &= o[:-1, :]
        inner[:-1, :] &= o[1:, :]
        inner[:, 1:] &= o[:, :-1]
        inner[:, :-1] &= o[:, 1:]
        self.a[o & ~inner, :3] *= k


def edge_of(mask: np.ndarray) -> np.ndarray:
    inner = mask.copy()
    inner[1:, :] &= mask[:-1, :]
    inner[:-1, :] &= mask[1:, :]
    inner[:, 1:] &= mask[:, :-1]
    inner[:, :-1] &= mask[:, 1:]
    return mask & ~inner


def lit_edges(mask: np.ndarray):
    """(upper-left edge, lower-right edge) of a region: light from the upper left (style guide 5)."""
    up =mask & ~np.vstack([np.zeros((1, mask.shape[1]), bool), mask[:-1, :]])
    left = mask & ~np.hstack([np.zeros((mask.shape[0], 1), bool), mask[:, :-1]])
    down = mask & ~np.vstack([mask[1:, :], np.zeros((1, mask.shape[1]), bool)])
    right = mask & ~np.hstack([mask[:, 1:], np.zeros((mask.shape[0], 1), bool)])
    return up | left, down | right


def save(img: np.ndarray, name: str) -> None:
    p = os.path.join(OUT, name + ".png")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8), "RGBA").save(p)
    print("wrote", os.path.relpath(p, ROOT).replace("\\", "/"))


# --- surface patterns: value fields 0..1 over the canvas ------------------------------------------------------------------------
def pat_steel(cv: Cv, seed: int) -> np.ndarray:
    n = vnoise(cv.h, cv.w, 9, seed)
    scratch = (hash2(cv.x // 2, cv.y, seed) > 0.985).astype(np.float32)
    return 0.5 + 0.1 * (n - 0.5) + 0.1 * scratch


def pat_planks(cv: Cv, x0: int, x1: int, boards: int, seed: int, horizontal: bool = False) -> np.ndarray:
    u = (cv.y if horizontal else cv.x) - (0 if horizontal else x0)
    span = (x1 - x0) / boards
    b = np.floor(u / span).astype(int)
    tone = 0.5 + 0.18 * (hash2(b, b * 7, seed) - 0.5)
    along = cv.x if horizontal else cv.y
    grain = 0.1 * np.sin(along * 0.11 + b * 2.3 + 3.0 * vnoise(cv.h, cv.w, 14, seed + 1)) + 0.05 * (hash2(u, along // 7, seed) > 0.92)
    seam = (np.mod(u, span) < 1.0) & (u > 0.5)
    v = tone + grain
    v = np.where(seam, 0.12, v)
    v = np.where((np.mod(u, span) >= 1.0) & (np.mod(u, span) < 2.0) & (u > 0.5), v + 0.12, v)  # the board's lit left edge
    return v


def pat_blocks(cv: Cv, bw: int, bh: int, seed: int, mortar: float = 0.12) -> np.ndarray:
    row = cv.y // bh
    off = np.where(row % 2 == 0, 0, bw // 2)
    col = (cv.x + off) // bw
    tone = 0.5 + 0.22 * (hash2(col, row, seed) - 0.5)
    n = vnoise(cv.h, cv.w, 5, seed + 3)
    lx, ly = (cv.x + off) % bw, cv.y % bh
    v = tone + 0.12 * (n - 0.5)
    v = np.where((ly == 1) | (lx == 1), v + 0.12, v)
    v = np.where((ly == bh - 1) | (lx == bw - 1), v - 0.12, v)
    v = np.where((ly == 0) | (lx == 0), mortar, v)
    return v


def pat_corrugated(cv: Cv, pitch: int, seed: int) -> np.ndarray:
    ph = np.mod(cv.x, pitch) / pitch
    ridge = np.where(ph < 0.35, 0.72, np.where(ph < 0.55, 0.5, np.where(ph < 0.85, 0.32, 0.45)))
    return ridge + 0.1 * (vnoise(cv.h, cv.w, 11, seed) - 0.5)


def pat_cloth(cv: Cv, x0: int, folds: float, seed: int) -> np.ndarray:
    f = np.sin((cv.x - x0) * folds)
    return 0.5 + 0.22 * f + 0.06 * (hash2(cv.x, cv.y // 3, seed) - 0.5)


def pat_birch(cv: Cv, seed: int) -> np.ndarray:
    v = 0.75 + 0.1 * (vnoise(cv.h, cv.w, 7, seed) - 0.5)
    mark = (hash2(cv.x // 6, cv.y // 3, seed) > 0.9) & (np.mod(cv.y, 3) == 0)
    return np.where(mark, 0.1, v)


# --- what is seen through an open doorway ---------------------------------------------------------------------------------------
def beyond(cv: Cv, inside: np.ndarray, box, spec: dict) -> None:
    """A dark room or passage running away from the doorway, in the world's ramp (`room`: key -> wall -> floor -> glow -> light), with a lit doorway
    at its far end (the owner's reference motif: a lit doorway at the end of a dark room) and that light lying along the floor. Few steps, little
    dither: calm when the door fills the screen."""
    x0, x1, y0, floor_y = box
    rp = spec["room"]
    vx = (x0 + x1) / 2.0
    vy = floor_y - (floor_y - y0) * 0.70
    hw = (x1 - x0) / 2.0
    dx = (cv.x + 0.5 - vx) / hw
    dyd = (cv.y + 0.5 - vy) / max(floor_y - vy, 1)
    dyu = (vy - cv.y - 0.5) / max(vy - y0, 1)
    sc = np.maximum(np.abs(dx), np.where(cv.y + 0.5 > vy, dyd, dyu))
    sc = np.maximum(sc, 1e-3)
    far = spec.get("far_scale", 0.34)
    near = np.clip(far / sc, 0, 1)  # 1 at the far wall, about `far` at the doorway
    floor = (cv.y + 0.5 > vy) & (dyd >= np.abs(dx))
    ceil = (cv.y + 0.5 <= vy) & (dyu >= np.abs(dx))
    wall = ~floor & ~ceil
    # the far doorway: a lit opening in the far wall, its shape the world's (`far_shape` rect or arch)
    fdx = dx / far
    fdy = (cv.y + 0.5 - (vy + (floor_y - vy) * far)) / ((floor_y - y0) * far)  # 0 at the far floor, -1 at the far ceiling
    door_w = spec.get("far_door_w", 0.42)
    lit = (np.abs(fdx) < door_w) & (fdy < 0) & (fdy > -0.8)
    if spec.get("far_shape") == "arch":
        cy = -0.8 + door_w * 0.9
        lit &= ~((fdy < cy) & (np.hypot(fdx / door_w, (fdy - cy) / (door_w * 0.9)) > 1.0))
    in_far = sc <= far
    st = 1.0 / (len(rp) - 1)  # one step of the room ramp: the inside is drawn in flat steps, no dither (calm when it fills the screen)
    v = np.zeros(cv.x.shape, np.float32)
    v = np.where(ceil, np.where(near > 0.72, 1, 0) * st, v)
    v = np.where(wall, np.where(near > 0.55, 2, 1) * st, v)
    v = np.where(floor, np.where(near > 0.8, 3, np.where(near > 0.5, 2, 1)) * st, v)
    glow = np.clip(1.0 - (np.maximum(np.abs(fdx) - door_w, 0) * 2.2 + np.maximum(-0.8 - fdy, 0) * 2.2), 0, 1)
    v = np.where(in_far, np.where(glow > 0.75, 3, 2) * st, v)
    v = np.where(in_far & lit, np.where((fdy > -0.72) & (np.abs(fdx) < door_w - 0.06), 5, 4) * st, v)
    # the lines where the walls meet the floor and the ceiling, a step darker: they draw the room
    seam = (np.abs(np.where(cv.y + 0.5 > vy, dyd, dyu) - np.abs(dx)) < 0.010 / np.maximum(sc, 0.2)) & ~in_far
    v = np.where(seam, np.maximum(v - st, 0), v)
    cv.paint(inside, v, rp, spread=0.0, fine=False)


# --- the leaf painters: (cv, mask, u 0..1 across the leaf, v 0..1 down it, shade offset) -------------------------------------------
def leaf_fire(cv, m, u, v, off, spec):
    """A steel fire door: a painted slab, a wired-glass vision panel, a push bar, scuffs low down."""
    val = 0.55 + off + 0.05 * (vnoise(cv.h, cv.w, 8, 11) - 0.5) + 0.1 * (hash2(cv.x, cv.y, 4) > 0.97) * (v > 0.75)
    cv.paint(m, val, spec["leaf"])
    win = m & (u > 0.36) & (u < 0.76) & (v > 0.12) & (v < 0.34)
    gl = 0.2 + off + 0.25 * (u - 0.36) + 0.3 * (v < 0.2)
    wire = ((np.round(u * 60) % 4 == 0) | (np.round(v * 120) % 4 == 0))
    cv.paint(win, np.where(wire, gl + 0.25, gl), spec["glass"])
    rim = win & ~np.roll(win, 1, 1) | win & ~np.roll(win, 1, 0)
    cv.paint(rim, 0.25 + off, spec["leaf"])
    bar = m & (np.abs(v - 0.5) < 0.016) & (u > 0.12) & (u < 0.92)
    cv.paint(bar, 0.8 + off, spec["metal"])
    cv.paint(m & (np.abs(v - 0.5 - 0.022) < 0.005) & (u > 0.12) & (u < 0.92), 0.2 + off, spec["metal"])
    kick = m & (v > 0.9)
    cv.paint(kick, 0.42 + off + 0.1 * (hash2(cv.x // 3, cv.y, 9) > 0.8), spec["metal"])


def leaf_ward(cv, m, u, v, off, spec):
    """A ward door: pale painted leaf, a tall wired-glass panel, a steel kick plate and push plate."""
    val = 0.6 + off + 0.04 * (vnoise(cv.h, cv.w, 10, 21) - 0.5)
    cv.paint(m, val, spec["leaf"])
    win = m & (u > 0.24) & (u < 0.76) & (v > 0.1) & (v < 0.46)
    gl = 0.22 + off + 0.35 * np.clip(1 - v * 2.5, 0, 1)
    wire = (np.round(u * 70) + np.round(v * 140)) % 6 == 0
    wire |= (np.round(u * 70) - np.round(v * 140)) % 6 == 0
    cv.paint(win, np.where(wire, gl + 0.22, gl), spec["glass"])
    cv.paint(edge_of(win), 0.3 + off, spec["leaf"])
    cv.paint(m & (u > 0.7) & (u < 0.88) & (v > 0.5) & (v < 0.58), 0.75 + off, spec["metal"])
    cv.paint(m & (v > 0.86), 0.5 + off + 0.15 * (np.mod(cv.x + cv.y, 9) == 0), spec["metal"])


def leaf_planks(cv, m, u, v, off, spec, straps: bool = True, studs: bool = True):
    """A plank door: boards, iron straps with studs (a dungeon, a city's old door when straps is False)."""
    nb = spec.get("boards", 5)
    b = np.floor(u * nb)
    tone = 0.5 + 0.2 * (hash2(b.astype(int), b.astype(int) * 3, spec.get("seed", 1)) - 0.5)
    grain = 0.06 * np.sin(v * 70 + b * 1.7 + 4 * vnoise(cv.h, cv.w, 12, 31))
    seam = np.mod(u * nb, 1.0) < 0.05
    val = np.where(seam, 0.1, tone + grain + off)
    cv.paint(m, val, spec["leaf"])
    if straps:
        for sv in (0.16, 0.5, 0.84):
            s = m & (np.abs(v - sv) < 0.022) & (u < 0.93)
            cv.paint(s, 0.42 + off + 0.15 * (np.abs(v - sv) < 0.008), spec["metal"])
            if studs:
                st = s & (np.mod(np.floor(u * 9), 2) == 0) & (np.abs(v - sv) < 0.01) & (np.mod(u * 9, 1) < 0.35)
                cv.paint(st, 0.85 + off, spec["metal"])
    ring = m & (np.abs(np.hypot((u - 0.82) * 2.0, (v - 0.52) * 4.0) - 0.07) < 0.025)
    cv.paint(ring, 0.6 + off, spec["metal"])


def leaf_panel(cv, m, u, v, off, spec):
    """A panelled timber door (the city, Jerusalem's cedar): four sunk panels lit from the upper left, a brass knob."""
    val = 0.52 + off + 0.06 * np.sin(v * 90 + 3 * vnoise(cv.h, cv.w, 10, 41))
    cv.paint(m, val, spec["leaf"])
    for (u0, u1, v0, v1) in ((0.16, 0.46, 0.08, 0.44), (0.54, 0.84, 0.08, 0.44), (0.16, 0.46, 0.52, 0.92), (0.54, 0.84, 0.52, 0.92)):
        p = m & (u >= u0) & (u < u1) & (v >= v0) & (v < v1)
        cv.paint(p, 0.4 + off, spec["leaf"])
        ul, dr = lit_edges(p)
        cv.paint(ul, 0.2 + off, spec["leaf"])
        cv.paint(dr, 0.72 + off, spec["leaf"])
    if spec.get("knob", True):
        cv.paint(m & (np.hypot((u - 0.88) * 3, (v - 0.5) * 6) < 0.09), 0.85 + off, spec["metal"])


def leaf_bulkhead(cv, m, u, v, off, spec):
    """A ship's bulkhead door (the harbour): riveted steel, dogs on the edge, a hand wheel."""
    val = 0.5 + off + 0.1 * (vnoise(cv.h, cv.w, 9, 51) - 0.5) + 0.12 * ((vnoise(cv.h, cv.w, 5, 52) > 0.72) * (v > 0.5))
    cv.paint(m, val, spec["leaf"])
    riv = m & ((np.abs(u - 0.08) < 0.02) | (np.abs(u - 0.92) < 0.02) | (np.abs(v - 0.06) < 0.008) | (np.abs(v - 0.94) < 0.008)) & (np.mod(np.round(v * 60 + u * 30), 4) == 0)
    cv.paint(riv, 0.85 + off, spec["leaf"])
    r = np.hypot(u - 0.5, (v - 0.42) * 2.5)
    wheel = m & ((np.abs(r - 0.19) < 0.03) | ((r < 0.19) & ((np.abs(u - 0.5) < 0.025) | (np.abs((v - 0.42) * 2.5) < 0.025))))
    cv.paint(wheel, 0.75 + off, spec["metal"])
    for dv in (0.2, 0.7):
        cv.paint(m & (u > 0.9) & (np.abs(v - dv) < 0.02), 0.7 + off, spec["metal"])


def leaf_hangar(cv, m, u, v, off, spec):
    """Corrugated iron in olive drab, a top rail, a stencilled number band."""
    val = pat_corrugated(cv, 6, 61) * 0.8 + 0.1 + off
    cv.paint(m, val, spec["leaf"])
    band = m & (np.abs(v - 0.3) < 0.04)
    cv.paint(band, 0.25 + off + 0.5 * ((np.mod(cv.x, 9) < 3) & (np.abs(v - 0.3) < 0.02)), spec["leaf"])
    cv.paint(m & (u > 0.06) & (u < 0.12) & (v > 0.45) & (v < 0.6), 0.8 + off, spec["metal"])


def leaf_slab(cv, m, u, v, off, spec):
    """A stone slab door of the deep halls: dressed stone with a carved knot of lines, an ember-lit seam."""
    val = 0.45 + off + 0.15 * (vnoise(cv.h, cv.w, 6, 71) - 0.5)
    cv.paint(m, val, spec["leaf"])
    r = np.hypot(u - 0.5, (v - 0.4) * 0.5)
    carve = m & ((np.abs(r - 0.22) < 0.018) | (np.abs(r - 0.13) < 0.016) | ((np.abs(u - 0.5) < 0.02) & (v > 0.18) & (v < 0.8)))
    cv.paint(carve, 0.15 + off, spec["leaf"])
    cv.paint(carve & np.roll(~carve, 1, 0), 0.7 + off, spec["leaf"])


def leaf_round(cv, m, u, v, off, spec):
    """A round-topped wooden door (the orchard): honey boards, black iron hinges reaching across, a ring."""
    leaf_planks(cv, m, u, v, off, spec, straps=False)
    for sv in (0.22, 0.78):
        h = m & (np.abs(v - sv) < 0.016 + 0.01 * (u < 0.2)) & (u < 0.7)
        cv.paint(h, 0.3 + off, spec["metal"])
    cv.paint(m & (np.hypot((u - 0.8) * 2, (v - 0.55) * 4) < 0.09), 0.75 + off, spec["metal"])


def leaf_birch(cv, m, u, v, off, spec):
    """A carved birch door: pale boards with a carved border and a sun knot, iron latch."""
    leaf_planks(cv, m, u, v, off, spec, straps=False)
    border = m & ((np.abs(u - 0.1) < 0.02) | (np.abs(u - 0.9) < 0.02) | (np.abs(v - 0.06) < 0.01) | (np.abs(v - 0.94) < 0.01))
    cv.paint(border, 0.25 + off, spec["leaf"])
    r = np.hypot((u - 0.5), (v - 0.32) * 0.5)
    cv.paint(m & (np.abs(r - 0.14) < 0.02), 0.25 + off, spec["leaf"])
    ang = np.arctan2((v - 0.32) * 0.5, u - 0.5)
    cv.paint(m & (r < 0.12) & (np.mod(ang * 8 / np.pi, 2) < 0.5), 0.25 + off, spec["leaf"])
    cv.paint(m & (u > 0.76) & (u < 0.9) & (np.abs(v - 0.52) < 0.012), 0.6 + off, spec["metal"])


def leaf_gate(cv, m, u, v, off, spec):
    """A gate of iron bars and bone (the Underworld): only the bars are drawn, the doorway's dim inside shows between them."""
    bar = m & ((np.mod(u * 7, 1.0) < 0.2) | (np.abs(v - 0.1) < 0.018) | (np.abs(v - 0.55) < 0.018) | (u < 0.04) | (u > 0.96))
    cv.paint(bar, 0.42 + off + 0.25 * (np.mod(u * 7, 1.0) < 0.07), spec["metal"])
    bone = m & (np.abs(v - 0.55) < 0.03) & (np.mod(u * 7, 1.0) > 0.25)  # a crossbar of bones lashed between the bars
    cv.paint(bone, 0.55 + off + 0.25 * (np.abs(v - 0.55) < 0.012), spec["bone"])
    spike = m & (v < 0.1) & (np.mod(u * 7, 1.0) < 0.2) & (v > 0.1 - 0.05 * (1 - np.abs(np.mod(u * 7, 1.0) - 0.1) * 10))
    cv.paint(spike, 0.7 + off, spec["bone"])


def leaf_curtain(cv, m, u, v, off, spec):
    """A woven curtain: bands of the world's dye, folds."""
    folds = 0.5 + 0.25 * np.sin(u * spec.get("folds", 22.0))
    bands = np.floor(v * 9) % 3
    rp = spec["leaf"]
    val = folds * 0.75 + 0.1 + off + 0.04 * (hash2(cv.x, cv.y // 2, 81) - 0.5)
    cv.paint(m & (bands != 1), val, rp)
    cv.paint(m & (bands == 1), val, spec.get("leaf2", rp))
    fringe = m & (v > 0.97) & (np.mod(cv.x, 3) == 0)
    cv.paint(fringe, val * 0.6, rp)


def leaf_hull(cv, m, u, v, off, spec):
    """An iris blade: hull plate with a seam and a cyan edge light."""
    cv.paint(m, 0.45 + off + 0.15 * (vnoise(cv.h, cv.w, 6, 91) - 0.5), spec["leaf"])


LEAVES = {"fire": leaf_fire, "ward": leaf_ward, "planks": leaf_planks, "panel": leaf_panel, "bulkhead": leaf_bulkhead, "hangar": leaf_hangar,
          "slab": leaf_slab, "round": leaf_round, "birch": leaf_birch, "gate": leaf_gate, "curtain": leaf_curtain, "hull": leaf_hull}


# --- the door ----------------------------------------------------------------------------------------------------------------------
def opening_mask(cv: Cv, sp: dict) -> np.ndarray:
    x0, x1, y0 = sp["ox0"], sp["ox1"], sp["oy0"]
    sh = sp.get("shape", "rect")
    m = (cv.x >= x0) & (cv.x < x1) & (cv.y >= y0) & (cv.y < sp.get("oy1", H))
    if sh == "arch":
        r = (x1 - x0) / 2.0
        cx, cy = (x0 + x1) / 2.0, y0 + r * sp.get("arch_k", 1.0)
        m &= ~((cv.y + 0.5 < cy) & (np.hypot((cv.x + 0.5 - cx) / r, (cv.y + 0.5 - cy) / (r * sp.get("arch_k", 1.0))) > 1.0))
    elif sh == "round":
        cx, cy, r = sp["cx"], sp["cy"], sp["r"]
        m = np.hypot(cv.x + 0.5 - cx, cv.y + 0.5 - cy) < r
    return m


def surround(cv: Cv, sp: dict, opening: np.ndarray) -> None:
    """The frame, jamb or wall the door sits in, in the world's material, the opening cut out."""
    s = sp["frame"]
    kind = s["kind"]
    fx0, fx1, fy0 = s.get("x0", 6), s.get("x1", W - 6), s.get("y0", 16)
    outer = (cv.x >= fx0) & (cv.x < fx1) & (cv.y >= fy0)
    if s.get("shape") == "arch":
        r = (fx1 - fx0) / 2.0
        cx, cy = (fx0 + fx1) / 2.0, fy0 + r * s.get("arch_k", 1.0)
        outer &= ~((cv.y + 0.5 < cy) & (np.hypot((cv.x + 0.5 - cx) / r, (cv.y + 0.5 - cy) / (r * s.get("arch_k", 1.0))) > 1.0))
    elif s.get("shape") == "plate":  # a hull bulkhead: a rounded plate
        cx = (fx0 + fx1) / 2.0
        k = s.get("round", 24)
        dxp = np.maximum(np.abs(cv.x + 0.5 - cx) - ((fx1 - fx0) / 2.0 - k), 0)
        dyp = np.maximum(fy0 + k - cv.y - 0.5, 0)
        outer &= np.hypot(dxp, dyp) < k
    ring = outer & ~opening
    rp = s["ramp"]
    if kind == "steel":
        val = pat_steel(cv, 3)
    elif kind == "blocks":
        val = pat_blocks(cv, s.get("bw", 24), s.get("bh", 12), s.get("seed", 5))
    elif kind == "brick":
        val = pat_blocks(cv, 16, 7, s.get("seed", 6), mortar=0.2)
    elif kind == "timber":
        val = pat_planks(cv, fx0, fx1, 1, 7) * 0.8 + 0.1
    elif kind == "birch":
        val = pat_birch(cv, 8)
    elif kind == "hull":
        val = pat_steel(cv, 9) * 0.8
        seam = (np.mod(cv.y - fy0, 48) == 0) | (np.abs(cv.x - (fx0 + fx1) / 2.0) < 0.6) & (cv.y < s.get("seam_y", 60))
        val = np.where(seam, 0.15, val)
        val = np.where((np.mod(cv.y - fy0, 48) == 4) & (np.mod(cv.x, 8) == 2), 0.85, val)  # rivets
    elif kind == "bone":
        val = 0.5 + 0.25 * np.sin(cv.y * 0.55 + 2 * vnoise(cv.h, cv.w, 6, 10) * 3) + 0.1 * (vnoise(cv.h, cv.w, 4, 11) - 0.5)
    elif kind == "mud":
        val = 0.5 + 0.12 * (vnoise(cv.h, cv.w, 7, 12) - 0.5) + 0.12 * (vnoise(cv.h, cv.w, 3, 13) > 0.75)
    elif kind == "char":
        val = 0.3 + 0.3 * np.abs(np.sin(cv.x * 0.9 + cv.y * 0.07)) * (vnoise(cv.h, cv.w, 5, 14) > 0.4) + 0.1 * (hash2(cv.x, cv.y // 4, 15) > 0.9)
    elif kind == "rock":
        val = 0.45 + 0.3 * (vnoise(cv.h, cv.w, 10, 16) - 0.5) + 0.15 * (vnoise(cv.h, cv.w, 4, 17) - 0.5)
    else:
        val = 0.5
    # light from the upper left over the whole frame: the left jamb a step lighter than the right
    cx = (sp["ox0"] + sp["ox1"]) / 2.0
    val = val + np.where(cv.x < cx, 0.06, -0.08)
    cv.paint(ring, val, rp)
    # the reveal: a dark step just inside the opening on the lit sides (the wall's thickness in shadow)
    rev = opening & ~np.roll(opening, 2, 0) | opening & ~np.roll(opening, 2, 1)
    cv.a[rev & cv.opaque(), :3] *= 0.7
    if s.get("lintel") is not None:  # a lintel, keystone or sign board over the opening
        s["lintel"](cv, sp)


def door(sp: dict, k: int) -> np.ndarray:
    """k = 0 (shut) .. 3 (wide open)."""
    cv = Cv(W, H)
    op = opening_mask(cv, sp)
    box = (sp["ox0"], sp["ox1"], sp["oy0"], sp.get("oy1", H))
    surround(cv, sp, op)
    closer = sp["closer"]
    leaf = LEAVES[sp["leaf_kind"]]
    x0, x1, y0, y1 = sp["ox0"], sp["ox1"], sp["oy0"], sp.get("oy1", H)
    ow, oh = x1 - x0, y1 - y0
    if closer == "gate":  # the inside always shows (dimmer when shut), the barred leaf over it
        beyond(cv, op, box, sp)
        if k == 0:
            cv.darken(op, 0.55)
    elif k > 0:
        beyond(cv, op, box, sp)
    if closer in ("swing", "gate"):
        if k == 0:
            m = op.copy()
            u = (cv.x + 0.5 - x0) / ow
            v = (cv.y + 0.5 - y0) / oh
            leaf(cv, m, u, v, 0.0, sp)
        else:
            frac = (0.68, 0.4, 0.17)[k - 1]
            lw = max(int(round(ow * frac)), 3)
            grow = 4 + 4 * k  # the outer edge stands taller: nearer the viewer
            xr = cv.x - (x0 - 1)
            top = y0 - (xr * grow) / lw
            m = (xr >= 0) & (xr < lw) & (cv.y >= top) & (cv.y < y1)
            if sp.get("shape") == "arch":
                m &= (cv.y >= top + np.clip(op.argmax(0)[np.clip(x0 + (xr * ow // lw), 0, W - 1)] - y0, 0, None))
            u = xr / lw
            v = (cv.y - top) / (y1 - top)
            leaf(cv, m, u, v, -0.14 - 0.03 * k, sp)
            cv.darken(edge_of(m) & (cv.x == x0 - 1 + lw - 1), 0.6)
            if closer == "gate":
                pass
    elif closer == "double":
        half = ow // 2
        if k == 0:
            for (a, flip) in ((x0, False), (x0 + half, True)):
                m = op & (cv.x >= a) & (cv.x < a + half)
                u = (cv.x + 0.5 - a) / half
                leaf(cv, m, (1 - u) if flip else u, (cv.y + 0.5 - y0) / oh, 0.0 if not flip else -0.04, sp)
            cv.darken(op & (cv.x == x0 + half), 0.55)
        else:
            frac = (0.62, 0.36, 0.15)[k - 1]
            lw = max(int(round(half * frac)), 3)
            grow = 3 + 3 * k
            for side in (0, 1):
                xr = (cv.x - (x0 - 1)) if side == 0 else ((x1) - cv.x)
                top = y0 - (xr * grow) / lw
                m = (xr >= 0) & (xr < lw) & (cv.y >= top) & (cv.y < y1)
                if sp.get("shape") == "arch":
                    m &= cv.y >= top + 6
                u = xr / lw
                leaf(cv, m, u, (cv.y - top) / (y1 - top), -0.14 - 0.03 * k - 0.04 * side, sp)
    elif closer == "slide":  # the leaf slides into the wall to the right: the gap opens from the left
        gap = int(round(ow * (0, 0.34, 0.66, 0.97)[k]))
        m = op & (cv.x >= x0 + gap)
        u = (cv.x + 0.5 - x0 - gap) / ow
        leaf(cv, m, u, (cv.y + 0.5 - y0) / oh, 0.0, sp)
        cv.darken(m & (cv.x == x0 + gap), 0.55)
        if sp.get("rail"):
            rail = (cv.y >= y0 - 7) & (cv.y < y0 - 2) & (cv.x >= x0 - 4) & (cv.x < x1 + 10)
            cv.paint(rail, 0.45 + 0.3 * (cv.y == y0 - 7), sp["metal"])
    elif closer == "iris":
        cx, cy, r = sp["cx"], sp["cy"], sp["r"]
        ap = r * (0.0, 0.42, 0.74, 1.0)[k]
        rr = np.hypot(cv.x + 0.5 - cx, cv.y + 0.5 - cy)
        ang = np.arctan2(cv.y + 0.5 - cy, cv.x + 0.5 - cx)
        m = op & (rr >= ap)
        blade = np.floor(np.mod(ang + rr / r * 1.4 + k * 0.35, 2 * np.pi) / (2 * np.pi) * 6)
        seam = np.mod(ang + rr / r * 1.4 + k * 0.35, 2 * np.pi / 6) < 0.09
        val = 0.42 + 0.12 * (np.mod(blade, 2)) - 0.18 * (cv.y > cy) * (rr / r) + 0.18 * (cv.y < cy) * (cv.x < cx) * (rr / r)
        cv.paint(m, np.where(seam, 0.12, val), sp["leaf"])
        if k > 0:
            cv.paint(m & (rr < ap + 1.6), 0.95, sp["glow"])  # the lit lip of the aperture
        else:
            cv.paint(op & (rr < 3.2), 0.9, sp["glow"])
    elif closer == "curtain":
        left = int(round(ow * (1.0, 0.5, 0.3, 0.17)[k]))
        m = op & (cv.x < x0 + left)
        hang = (cv.y - y0) / oh
        if k > 0:  # gathered to the left jamb and tied back: the hem pulled in, a tie at two thirds
            edge = x0 + left * (0.55 + 0.45 * np.abs(hang - 0.62) / 0.62)
            m = op & (cv.x < edge)
            u = (cv.x + 0.5 - x0) / np.maximum(edge - x0, 1)
            spec_f = dict(sp)
            spec_f["folds"] = sp.get("folds", 22.0) * (1.0 / ((1.0, 0.5, 0.3, 0.17)[k]))
            leaf(cv, m, u * 0.25, hang, -0.1, spec_f)
            tie = m & (np.abs(hang - 0.62) < 0.012)
            cv.paint(tie, 0.8, sp["metal"])
        else:
            leaf(cv, m, (cv.x + 0.5 - x0) / ow, hang, 0.0, sp)
        rod = (cv.y >= y0 - 4) & (cv.y < y0 - 1) & (cv.x >= x0 - 6) & (cv.x < x1 + 6)
        cv.paint(rod, 0.5 + 0.3 * (cv.y == y0 - 4), sp["metal"])
    if sp.get("dress") is not None:
        sp["dress"](cv, sp, k)
    cv.outline()
    return cv.a


# --- per-world dressings (drawn after the leaf) -----------------------------------------------------------------------------------
def dress_warehouse(cv, sp, k):
    # a cage bulkhead light's box on the lintel is the lamp's place; here a green fire-exit plate (a running man is text-free) over the frame
    plate = (cv.x >= 54) & (cv.x < 90) & (cv.y >= 2 + 28) & (cv.y < 14 + 28)
    cv.paint(plate, 0.75, sp["exit"])
    fig = plate & (((np.abs(cv.x - 64) < 2) & (cv.y >= 32) & (cv.y < 40)) | ((cv.y == 35) & (cv.x >= 60) & (cv.x < 70)) | ((np.abs(cv.x - 76 - (cv.y - 32) * 0.5) < 1.5) & (cv.y >= 32) & (cv.y < 40)))
    cv.paint(fig, 0.15, sp["exit"])
    cv.paint(plate & ((cv.x == 82) | (cv.x == 83)) & (cv.y >= 32) & (cv.y < 40), 0.15, sp["exit"])
    # hazard paint on the foot of the jambs
    foot = ((cv.x >= 8) & (cv.x < 18) | (cv.x >= W - 18) & (cv.x < W - 8)) & (cv.y >= H - 22)
    cv.paint(foot, np.where(np.mod(cv.x + cv.y, 8) < 4, 0.85, 0.08), sp["hazard"])


def dress_hell(cv, sp, k):
    # a horned skull for a keystone, its eye sockets lit by the fire behind
    cx = W / 2.0
    sk = (np.hypot((cv.x + 0.5 - cx) / 13.0, (cv.y + 0.5 - 18) / 11.0) < 1.0) | ((np.abs(cv.x + 0.5 - cx) < 8) & (cv.y >= 18) & (cv.y < 32))
    horn = ((np.abs(cv.x + 0.5 - cx) - 13 - (20 - cv.y) * 0.5) ** 2 < 6) & (cv.y >= 2) & (cv.y < 18)
    cv.paint(sk | horn, 0.62 + 0.2 * (cv.x < cx) - 0.2 * (cv.y > 26), sp["bone"])
    eyes = (np.hypot(np.abs(cv.x + 0.5 - cx) - 5, cv.y + 0.5 - 19) < 3.0)
    cv.paint(eyes, 0.85 if k > 0 else 0.5, sp["room"])
    teeth = (cv.y >= 28) & (cv.y < 31) & (np.abs(cv.x + 0.5 - cx) < 7) & (np.mod(cv.x, 3) == 0)
    cv.paint(teeth, 0.15, sp["bone"])


def dress_ship(cv, sp, k):
    # a strip of status lights on the bulkhead over the hatch (dim; the lamp is the signal)
    for i in range(5):
        m = (cv.x >= 44 + i * 12) & (cv.x < 52 + i * 12) & (cv.y >= 52) & (cv.y < 55)
        cv.paint(m, 0.75 if (i == 2) else 0.35, sp["glow"])


def dress_hospital(cv, sp, k):
    # a pale room-number plate and a hand-rub dispenser by the frame
    cv.paint((cv.x >= 58) & (cv.x < 86) & (cv.y >= 31) & (cv.y < 38), 0.85, sp["frame"]["ramp"])
    cv.paint((cv.x >= 62) & (cv.x < 82) & (cv.y >= 34) & (cv.y < 36) & (np.mod(cv.x, 4) != 0), 0.2, sp["frame"]["ramp"])


def dress_city(cv, sp, k):
    # a fanlight over the door, blacked out, its glazing bars
    fan = (np.hypot(cv.x + 0.5 - W / 2.0, cv.y + 0.5 - 42) < 30) & (cv.y < 40) & (cv.y >= 14)
    cv.paint(fan, 0.12, sp["room"])
    bars = fan & ((np.abs(np.arctan2(cv.y + 0.5 - 42, cv.x + 0.5 - W / 2.0) * 4 / np.pi - np.round(np.arctan2(cv.y + 0.5 - 42, cv.x + 0.5 - W / 2.0) * 4 / np.pi)) < 0.08) | (np.abs(np.hypot(cv.x + 0.5 - W / 2.0, cv.y + 0.5 - 42) - 29) < 1.2))
    cv.paint(bars, 0.4, sp["frame"]["ramp"])
    step = (cv.y >= H - 6) & (cv.x >= 4) & (cv.x < W - 4)
    cv.paint(step, 0.55 + 0.25 * (cv.y == H - 6), sp["frame"]["ramp"])


def dress_harbour(cv, sp, k):
    # stencilled hazard band at the sill, a cleat on each side
    sill = (cv.y >= H - 12) & (cv.y < H) & (cv.x >= 14) & (cv.x < W - 14)
    cv.paint(sill, np.where(np.mod(cv.x - cv.y, 10) < 5, 0.85, 0.15), sp["hazard"])


def dress_ward(cv, sp, k):
    # a wired call box over the frame, and rust weeping from the hinge side
    rust = (cv.x >= 10) & (cv.x < 16) & (cv.y >= 40) & (hash2(cv.x, cv.y // 6, 7) > 0.6) & cv.opaque()
    cv.paint(rust & ~opening_mask(cv, sp), 0.5, sp["rust"])


def dress_bassment(cv, sp, k):
    # iron torch-ring by the arch and moss in the joints at the foot
    moss = cv.opaque() & (cv.y > H - 40) & (hash2(cv.x // 2, cv.y // 2, 3) > 0.82) & ~opening_mask(cv, sp)
    cv.paint(moss, 0.4, sp["moss"])


def dress_orchard(cv, sp, k):
    # ivy over the stone, apples' red in two leaves
    leaves = cv.opaque() & ~opening_mask(cv, sp) & (vnoise(H, W, 6, 5) > 0.62) & (cv.y < 120)
    cv.paint(leaves, 0.3 + 0.5 * (hash2(cv.x, cv.y, 6) > 0.6), sp["ivy"])


def dress_ash(cv, sp, k):
    # a cracked skull of a beast on the post top, ash drift at the foot
    drift = (cv.y > H - 10 - 6 * np.sin(cv.x * 0.08)) & (cv.x >= 0) & ((cv.x < sp["ox0"] + 4) | (cv.x >= sp["ox1"] - 4))
    cv.paint(drift, 0.7 + 0.1 * (hash2(cv.x, cv.y, 9) > 0.7), sp["frame"]["ramp"][::-1][1:][::-1] if False else ramp("#6a6460", "#9a948c", "#c0b8ac"))


def dress_deeps(cv, sp, k):
    # the carved lintel's rune line lit faintly by the Ember from below
    m = (cv.y >= 18) & (cv.y < 22) & (cv.x >= 30) & (cv.x < W - 30) & (np.mod(cv.x, 7) < 4)
    cv.paint(m, 0.75, sp["room"])


# --- the sets: one per world --------------------------------------------------------------------------------------------------
def _sets() -> dict:
    common = dict(ox0=24, ox1=120, oy0=40)
    S = {}
    S["warehouse"] = dict(common, closer="swing", leaf_kind="fire",
        frame=dict(kind="steel", ramp=ramp("#16101a", "#2e2a34", "#4a4652", "#6a6672"), x0=12, x1=W - 12, y0=26),
        leaf=ramp("#16201e", "#2c3c38", "#4a605a", "#6e8a80"), glass=ramp("#0a0618", "#2a2440", "#5a5878", "#9a98b8"), metal=ramp("#2a2428", "#5a5258", "#9a9098", "#d0c8c8"),
        exit=ramp("#0e2a18", "#1e6a3a", "#3aa860", "#8ae0a0"), hazard=ramp("#16100a", "#4a3a10", "#b08a18", "#e8c040"),
        room=ramp("#0a0618", "#1a0e24", "#3a1c34", "#7a3c5a", "#c87a6a", "#eab278"), dress=dress_warehouse,
        lamp=dict(style="cage", metal=ramp("#2a2428", "#5a5258", "#9a9098")), bars=dict(kind="tape", a="#e8c040", b="#1a1410", centre="none"),
        sign=dict(wood=ramp("#2a1c14", "#4a3424", "#6a5038", "#8a6a48")), spill="#eab278")
    S["ship"] = dict(closer="iris", leaf_kind="hull", shape="round", cx=72, cy=170, r=60, ox0=12, ox1=132, oy0=110, oy1=230,
        frame=dict(kind="hull", shape="plate", ramp=ramp("#0b0c1e", "#1e2a3c", "#3b4d63", "#5a7088", "#88a0b8"), x0=4, x1=W - 4, y0=40, round=40, seam_y=110),
        leaf=ramp("#0b0c1e", "#22304a", "#3b4d63", "#5a7088", "#7a92a8"), glow=ramp("#1a3a48", "#4e8d8e", "#7be0d0", "#cfefff"),
        metal=ramp("#1e2a3c", "#3b4d63", "#88a0b8"), room=ramp("#06081c", "#0e1430", "#1c2c48", "#2e5466", "#4e8d8e", "#9fe8e0"), far_shape="arch", dress=dress_ship,
        lamp=dict(style="bezel", metal=ramp("#1e2a3c", "#3b4d63", "#5a7088", "#88a0b8"), plate="hex"), bars=dict(kind="strut", a="#c02848", b="#1e2a3c", metal=ramp("#1e2a3c", "#3b4d63", "#5a7088", "#88a0b8"), centre="bolt"),
        sign=dict(wood=ramp("#1e2a3c", "#3b4d63", "#5a7088", "#88a0b8")), spill="#7be0d0")
    S["hell"] = dict(closer="gate", leaf_kind="gate", shape="arch", ox0=26, ox1=118, oy0=42,
        frame=dict(kind="bone", ramp=ramp("#200d11", "#4a2420", "#8a5c57", "#b89080", "#d8c0a8"), shape="arch", x0=8, x1=W - 8, y0=20),
        metal=ramp("#120808", "#2a1414", "#4a2a26", "#7a4a3a"), bone=ramp("#3a1c18", "#8a5c57", "#c0a08a", "#e0cdb0"),
        room=ramp("#2a0a08", "#3a0e0a", "#601a10", "#a03a14", "#ff6a1a", "#ffb050"), far_shape="arch", far_door_w=0.5, dress=dress_hell,
        lamp=dict(style="brazier", metal=ramp("#120808", "#2a1414", "#4a2a26", "#7a4a3a")), bars=dict(kind="chain", metal=ramp("#120808", "#3a2222", "#6a4a40", "#9a7a68"), centre="lock"),
        sign=dict(wood=ramp("#1a0a08", "#3a1c18", "#5a2c22", "#8a5c57")), spill="#ff8a30")
    S["hospital"] = dict(common, closer="swing", leaf_kind="ward",
        frame=dict(kind="steel", ramp=ramp("#18293d", "#3a4a68", "#7088a8", "#a8b8cc", "#d8ccb4"), x0=14, x1=W - 14, y0=30),
        leaf=ramp("#18293d", "#4a5a78", "#7a8aa8", "#a8b4c8"), glass=ramp("#0c1636", "#1e3050", "#4a6a8a", "#9fc4e8"), metal=ramp("#2a3448", "#5a6a80", "#a0b0c0", "#d8e0e8"),
        room=ramp("#0c1636", "#141e3c", "#22304e", "#3a4a68", "#b09060", "#e0b060"), dress=dress_hospital,
        lamp=dict(style="bezel", metal=ramp("#3a4a68", "#7088a8", "#a8b8cc", "#d8ccb4"), plate="box"), bars=dict(kind="tape", a="#d8ccb4", b="#c03030", centre="none"),
        sign=dict(wood=ramp("#3a4a68", "#5a6a80", "#7088a8", "#a8b8cc")), spill="#e0b060")
    S["ward"] = dict(common, closer="double", leaf_kind="ward", ox0=18, ox1=126,
        frame=dict(kind="steel", ramp=ramp("#0b1519", "#1e2e28", "#394d44", "#5a7266"), x0=8, x1=W - 8, y0=28),
        leaf=ramp("#0b1519", "#26382f", "#394d44", "#4a6758", "#6a8a78"), glass=ramp("#06110c", "#14281e", "#3a5a48", "#88b098"), metal=ramp("#1a2420", "#3a4a42", "#6a7a70", "#a0aca4"),
        rust=ramp("#2a1408", "#5a2a10", "#a05a30"), room=ramp("#06110c", "#0b1a14", "#16281e", "#2a4234", "#9a8a50", "#e8c070"), dress=dress_ward,
        lamp=dict(style="bezel", metal=ramp("#1a2420", "#394d44", "#5a7266", "#8aa094"), plate="box"), bars=dict(kind="plank", wood=ramp("#1a140c", "#3a2c1c", "#5a4630", "#7a6448"), centre="lock",
        metal=ramp("#1a2420", "#3a4a42", "#6a7a70", "#a0aca4")),
        sign=dict(wood=ramp("#1a140c", "#3a2c1c", "#5a4630", "#7a6448")), spill="#e8c070")
    S["galilee"] = dict(closer="curtain", leaf_kind="curtain", shape="rect", ox0=28, ox1=116, oy0=48,
        frame=dict(kind="mud", ramp=ramp("#3a2a20", "#7a5a3c", "#b08848", "#c8a878", "#e0c8a0"), x0=6, x1=W - 6, y0=24),
        leaf=ramp("#3a2a20", "#6a4a2c", "#a07040", "#c8a070"), leaf2=ramp("#1a2238", "#2a4a70", "#5a8ab8", "#9ab8d0"), metal=ramp("#3a2a20", "#7a5a3c", "#b08848"), folds=26.0,
        room=ramp("#1a1210", "#2a1e18", "#4a3424", "#7a5636", "#d09a60", "#fff0c8"), far_door_w=0.38,
        lamp=dict(style="lantern", metal=ramp("#3a2a20", "#6a4a2c", "#a07040", "#c8a070"), oil=True), bars=dict(kind="pole", wood=ramp("#3a2a20", "#6a4a2c", "#a07848", "#c8a070"), centre="lash"),
        sign=dict(wood=ramp("#3a2a20", "#6a4a2c", "#a07848", "#c8a070")), spill="#ffd090")
    S["jerusalem"] = dict(closer="double", leaf_kind="panel", shape="arch", arch_k=0.8, ox0=26, ox1=118, oy0=36, knob=False,
        frame=dict(kind="blocks", bw=26, bh=13, seed=4, ramp=ramp("#3a2a20", "#8a7050", "#c8a878", "#e0c8a0", "#f0dcb8"), shape="arch", arch_k=0.8, x0=4, x1=W - 4, y0=8),
        leaf=ramp("#24140c", "#4a2c18", "#6e4424", "#8e6034"), metal=ramp("#2a2018", "#6a5a38", "#b09050"),
        room=ramp("#1a1210", "#2a1e18", "#4a3424", "#7a5636", "#d09a60", "#fff0c8"), far_shape="arch",
        lamp=dict(style="lantern", metal=ramp("#2a2018", "#6a5a38", "#b09050", "#d8b870"), oil=True), bars=dict(kind="pole", wood=ramp("#24140c", "#4a2c18", "#7a5030", "#a07040"), centre="lash"),
        sign=dict(wood=ramp("#3a2a20", "#6a4a2c", "#a07848", "#c8a070")), spill="#ffd090")
    S["airfield"] = dict(common, closer="slide", leaf_kind="hangar", rail=True, oy0=44,
        frame=dict(kind="timber", ramp=ramp("#2a2418", "#4a4030", "#6a5a40", "#8a7a50"), x0=10, x1=W - 10, y0=30),
        leaf=ramp("#1e2214", "#3a4024", "#4a5030", "#6a7044", "#8a8a5a"), metal=ramp("#2a2418", "#4a4436", "#7a7462", "#a8a08a"),
        room=ramp("#141008", "#201a10", "#3a2e1c", "#5a4a30", "#c0a060", "#ffd890"),
        lamp=dict(style="cage", metal=ramp("#2a2418", "#4a4436", "#7a7462")), bars=dict(kind="plank", wood=ramp("#2a2418", "#4a4030", "#6a5a40", "#8a7a50"), centre="nail"),
        sign=dict(wood=ramp("#2a2418", "#4a4030", "#6a5a40", "#8a7a50")), spill="#ffd890")
    S["city"] = dict(common, closer="swing", leaf_kind="panel", oy0=46,
        frame=dict(kind="brick", seed=6, ramp=ramp("#1e1410", "#4a2c20", "#7a4a34", "#9a6a4c"), x0=4, x1=W - 4, y0=10),
        leaf=ramp("#0e1a14", "#1a3024", "#2a4a36", "#3e6a4c"), metal=ramp("#2a2010", "#6a5428", "#b09048"),
        room=ramp("#100c0a", "#1a1410", "#2e2218", "#4a3828", "#a07a48", "#ffd890"), dress=dress_city,
        lamp=dict(style="cage", metal=ramp("#1a1a1a", "#3a3a36", "#6a6a60")), bars=dict(kind="plank", wood=ramp("#1e1610", "#3e2e20", "#5e4630", "#7a6048"), centre="nail"),
        sign=dict(wood=ramp("#1e1610", "#3e2e20", "#5e4630", "#7a6048")), spill="#ffd890")
    S["harbour"] = dict(closer="swing", leaf_kind="bulkhead", shape="arch", arch_k=0.5, ox0=26, ox1=118, oy0=40, oy1=H - 12,
        frame=dict(kind="hull", shape="plate", round=30, ramp=ramp("#0a1222", "#1e2a3a", "#34465a", "#506680", "#7088a0"), x0=6, x1=W - 6, y0=18, seam_y=40),
        leaf=ramp("#0e1626", "#22303e", "#38485a", "#526678"), metal=ramp("#1a1a1a", "#4a4440", "#8a7a6a", "#b8a890"),
        hazard=ramp("#14100a", "#3a3010", "#a08020", "#d8b040"),
        room=ramp("#0e1c34", "#121e30", "#1e2c40", "#2e4058", "#a08850", "#ffd890"), dress=dress_harbour,
        lamp=dict(style="cage", metal=ramp("#1a1a1a", "#4a4440", "#8a7a6a"), bulkhead=True), bars=dict(kind="rope", rope=ramp("#2a2014", "#5a4a30", "#8a7450", "#b8a07a"), centre="lash"),
        sign=dict(wood=ramp("#1e1610", "#3e2e20", "#5e4630", "#7a6048")), spill="#ffd890")
    S["orchard"] = dict(closer="swing", leaf_kind="round", shape="arch", ox0=26, ox1=118, oy0=40, boards=6, seed=3,
        frame=dict(kind="blocks", bw=20, bh=14, seed=8, ramp=ramp("#1a1410", "#3e3428", "#625444", "#8a7a64", "#aa9a80"), shape="arch", x0=6, x1=W - 6, y0=18),
        leaf=ramp("#2a1808", "#5a3818", "#8a5a28", "#b07a3a"), metal=ramp("#141010", "#2a2422", "#4a4440", "#7a7068"),
        ivy=ramp("#14200c", "#2a3a14", "#46601e", "#5a6a30"),
        room=ramp("#1a1410", "#241a12", "#3a2a1c", "#5a4028", "#c08040", "#ffb050"), far_shape="arch", dress=dress_orchard,
        lamp=dict(style="lantern", metal=ramp("#141010", "#2a2422", "#4a4440", "#7a7068")), bars=dict(kind="branch", wood=ramp("#1a1208", "#3a2a18", "#5a4428", "#7a6038"), leaf=ramp("#1e2a10", "#3a5018", "#5a6a30"), centre="lash"),
        sign=dict(wood=ramp("#2a1808", "#5a3818", "#7a5028", "#9a6a3a")), spill="#ffb050")
    S["birch"] = dict(common, closer="swing", leaf_kind="birch", boards=5, seed=9, oy0=42,
        frame=dict(kind="birch", ramp=ramp("#2a2a34", "#6a6a74", "#a8a8b0", "#c8c8d0", "#e0dcd4"), x0=8, x1=W - 8, y0=22),
        leaf=ramp("#3a3430", "#6a625a", "#9a9084", "#c0b8aa"), metal=ramp("#141418", "#2a2a30", "#5a5a64", "#8a8a94"),
        room=ramp("#1a1a24", "#24242e", "#3a3a48", "#5a5a6c", "#c09060", "#ffb050"),
        lamp=dict(style="lantern", metal=ramp("#141418", "#2a2a30", "#5a5a64", "#8a8a94")), bars=dict(kind="pole", wood=ramp("#4a4a54", "#8a8a94", "#c8c8d0", "#e0dcd4"), centre="lash", birch=True),
        sign=dict(wood=ramp("#4a4a54", "#8a8a94", "#b8b8c0", "#d8d4cc")), spill="#ffb050")
    S["deeps"] = dict(closer="slide", leaf_kind="slab", shape="rect", ox0=26, ox1=118, oy0=44,
        frame=dict(kind="rock", ramp=ramp("#0a0a0e", "#1a1a20", "#2e2c32", "#4a4650", "#6a6470"), x0=0, x1=W, y0=10),
        leaf=ramp("#121216", "#24222a", "#3a3640", "#544e5a"), metal=ramp("#121216", "#3a3640", "#6a6470"),
        room=ramp("#0a0a0e", "#120e10", "#1e1612", "#3a2416", "#c05a18", "#ff7a20"), far_shape="arch", far_door_w=0.3, dress=dress_deeps,
        lamp=dict(style="brazier", metal=ramp("#0a0a0e", "#24222a", "#4a4650", "#6a6470")), bars=dict(kind="beam", metal=ramp("#0a0a0e", "#24222a", "#3e3a44", "#6a6470"), centre="bolt"),
        sign=dict(wood=ramp("#121216", "#24222a", "#3a3640", "#544e5a")), spill="#ff7a20")
    S["ash"] = dict(closer="curtain", leaf_kind="curtain", ox0=26, ox1=118, oy0=46, folds=10.0,
        frame=dict(kind="char", ramp=ramp("#0e0c0a", "#2a2420", "#4a4038", "#6a6058", "#8a8078"), x0=10, x1=W - 10, y0=20),
        leaf=ramp("#1e140c", "#3e2a1a", "#5e4430", "#7e6044"), leaf2=ramp("#1a1410", "#2e2620", "#4a4038", "#6a6058"), metal=ramp("#1a1410", "#4a4038", "#8a8078"),
        room=ramp("#141210", "#1a1614", "#2a2420", "#3e3028", "#c06020", "#ff7a20"), dress=dress_ash, far_door_w=0.3,
        lamp=dict(style="brazier", metal=ramp("#0e0c0a", "#2a2420", "#4a4038", "#6a6058")), bars=dict(kind="beam", metal=ramp("#1e1a16", "#3a3430", "#5e5650", "#8a8078"), centre="none", char=True),
        sign=dict(wood=ramp("#0e0c0a", "#2a2420", "#4a4038", "#6a6058")), spill="#ff7a20")
    S["bassment"] = dict(closer="swing", leaf_kind="planks", shape="arch", arch_k=0.7, ox0=26, ox1=118, oy0=36, boards=5, seed=7,
        frame=dict(kind="blocks", bw=22, bh=12, seed=11, ramp=ramp("#100c10", "#1e1a24", "#2e2c3a", "#46445a", "#62607a"), shape="arch", arch_k=0.7, x0=4, x1=W - 4, y0=8),
        leaf=ramp("#140c08", "#2e1e12", "#4a321e", "#6a4a2c"), metal=ramp("#0e0c10", "#24222a", "#4a4854", "#7a7884"),
        moss=ramp("#0e1a10", "#1e3a1e", "#3a5a2a"),
        room=ramp("#100c10", "#16121a", "#241e26", "#3a2c28", "#c07a38", "#ffb050"), far_shape="arch", dress=dress_bassment,
        lamp=dict(style="brazier", metal=ramp("#0e0c10", "#24222a", "#4a4854", "#7a7884")), bars=dict(kind="plank", wood=ramp("#140c08", "#2e1e12", "#4a321e", "#6a4a2c"), centre="lock",
        metal=ramp("#0e0c10", "#24222a", "#4a4854", "#7a7884")),
        sign=dict(wood=ramp("#140c08", "#2e1e12", "#4a321e", "#6a4a2c")), spill="#ffb050")
    return S


# --- the "no way" mark ----------------------------------------------------------------------------------------------------------
def bars(sp: dict) -> np.ndarray:
    b = sp["bars"]
    cv = Cv(BN, BN)
    c0 = BN / 2.0
    kind = b["kind"]
    hw = {"tape": 9, "plank": 14, "chain": 9, "rope": 7, "pole": 9, "strut": 12, "beam": 12, "branch": 8}[kind]
    for sgn in (-1, 1):  # the back member first
        c = ((cv.x + 0.5 - c0) * sgn - (cv.y + 0.5 - c0)) / np.sqrt(2)
        s = ((cv.x + 0.5 - c0) + (cv.y + 0.5 - c0) * sgn) / np.sqrt(2)
        L = BN * 0.66
        width = hw * (1.0 - 0.35 * (s + L) / (2 * L)) if kind == "branch" else hw
        if kind == "tape":
            width = hw + 1.2 * np.sin(s * 0.09 + sgn)  # it sags and twists a little
        m = (np.abs(c) < width) & (np.abs(s) < L)
        t = c / np.maximum(width, 1)  # -1..1 across
        if kind == "tape":
            stripe = np.mod(np.floor((s + c * 0.8) / 11), 2) == 0
            cv.paint(m & stripe, 0.75 - 0.2 * (t > 0.5), ramp("#3a3020", b["a"], "#ffffff", n=3) if False else ramp(_dk(b["a"]), b["a"]))
            cv.paint(m & ~stripe, 0.75 - 0.2 * (t > 0.5), ramp(_dk(b["b"]), b["b"]))
            # the tape's ends flutter loose past the doorway
            end = m & (np.abs(s) > L - 10) & (hash2(np.round(s).astype(int), np.round(c).astype(int), 3) > 0.5)
            cv.a[end, 3] = 0
        elif kind == "plank":
            grain = 0.08 * np.sin(s * 0.35 + c * 0.9 + 3 * vnoise(BN, BN, 9, 4 + sgn))
            v = 0.55 + grain - 0.25 * (t > 0.75) + 0.15 * (t < -0.7) - 0.08 * (sgn < 0)
            cv.paint(m, v, b["wood"])
            if b.get("stencil"):
                st = m & (np.abs(s) < 22) & (np.abs(t) < 0.45) & (np.mod(np.floor(s / 4), 3) != 2)
                cv.paint(st, 0.85, ramp(_dk(b["stencil"]), b["stencil"]))
            for ns in (-L + 12, L - 12):
                cv.paint(m & (np.hypot(s - ns, c) < 2.6), 0.9, ramp("#141414", "#5a5a5a", "#a0a0a0"))
        elif kind in ("pole", "branch"):
            v = 0.62 - 0.45 * t + 0.06 * np.sin(s * 0.5)
            if b.get("birch"):
                mark = (hash2(np.round(s / 5).astype(int), sgn + 5, 2) > 0.7) & (np.abs(t) < 0.7)
                v = np.where(mark & (np.mod(np.round(s), 5) < 2), 0.05, v)
            cv.paint(m, v, b["wood"])
            if kind == "branch":  # a few leaves still on it
                lf = (np.abs(c) < width + 7) & (np.abs(s) < L) & (vnoise(BN, BN, 5, 7 + sgn) > 0.7) & ~m
                cv.paint(lf, 0.5 + 0.4 * (hash2(cv.x, cv.y, 1) > 0.5), b["leaf"])
        elif kind == "rope":
            tw = np.mod(np.floor((s + t * 9) / 4), 2)
            cv.paint(m, 0.62 - 0.3 * t - 0.25 * tw, b["rope"])
        elif kind == "chain":
            seg = np.mod(s + L, 16.0)
            idx = np.floor((s + L) / 16.0)
            face = np.mod(idx, 2) == 0
            ring = np.hypot((seg - 8) / 8.5, c / 7.5)
            link = np.where(face, (ring < 1.0) & (ring > 0.5), (np.abs(c) < 2.4) & (np.abs(seg - 8) < 9))
            mm = (np.abs(s) < L) & link
            cv.paint(mm, 0.6 - 0.35 * (c * np.sign(sgn) > 0) + 0.25 * (np.abs(seg - 5) < 1.5), b["metal"])
        elif kind in ("strut", "beam"):
            v = 0.5 - 0.2 * (t > 0.6) + 0.2 * (t < -0.6)
            rp = b["metal"]
            if b.get("char"):
                v = v * 0.7 + 0.25 * (np.mod(np.floor(s / 6), 2) == 0) * (np.abs(t) < 0.5)
            cv.paint(m, v, rp)
            if b.get("char"):  # embers still glowing in the charred grain
                crack = m & (np.abs(t) < 0.5) & (np.abs(np.sin(s * 0.45 + 2.0 * vnoise(BN, BN, 6, 5 + sgn) * 3)) < 0.18)
                cv.paint(crack, 0.5 + 0.4 * (hash2(cv.x, cv.y, 4) > 0.6), ramp("#3a1006", "#a03a10", "#ff7a20"))
            if kind == "strut":
                chev = m & (np.abs(t) < 0.55) & (np.mod(s + np.abs(c) * 1.2, 14) < 6)
                cv.paint(chev, 0.8, ramp(_dk(b["a"]), b["a"]))
            riv = m & (np.mod(s + L, 22) < 3) & (np.abs(np.abs(t) - 0.6) < 0.18)
            cv.paint(riv, 0.85, rp)
    ctr = b.get("centre", "none")
    r = np.hypot(cv.x + 0.5 - c0, cv.y + 0.5 - c0)
    if ctr == "lock":  # a padlock where they cross: the shackle over, the body under
        sh = (np.abs(np.hypot(cv.x + 0.5 - c0, cv.y + 0.5 - (c0 + 2)) - 9) < 2.2) & (cv.y + 0.5 < c0 + 6)
        body = (np.abs(cv.x + 0.5 - c0) < 12) & (cv.y + 0.5 >= c0 + 4) & (cv.y + 0.5 < c0 + 26)
        rp = b.get("metal", ramp("#141414", "#4a4a4a", "#8a8a8a", "#c0c0c0"))
        cv.paint(sh, 0.7, rp)
        cv.paint(body, 0.55 + 0.25 * (cv.x + 0.5 < c0 - 6) - 0.2 * (cv.x + 0.5 > c0 + 7), ramp("#2a1a08", "#6a4a18", "#a07a30", "#d0a848"))
        cv.paint(body & (np.hypot(cv.x + 0.5 - c0, cv.y + 0.5 - (c0 + 13)) < 2.5) | body & (np.abs(cv.x + 0.5 - c0) < 1) & (cv.y > c0 + 13) & (cv.y < c0 + 20), 0.0,
                 ramp("#140c04", "#2a1a08"))
    elif ctr == "lash":
        m = (np.abs(cv.x + 0.5 - c0) < 12) & (np.abs(cv.y + 0.5 - c0) < 12) & (np.abs(cv.x - cv.y) < 14) | (r < 10)
        cv.paint(m, 0.55 + 0.3 * (np.mod(cv.x + cv.y, 5) < 2), ramp("#2a2014", "#5a4a30", "#8a7450", "#b8a07a"))
    elif ctr == "bolt":
        cv.paint(r < 7, 0.8 - 0.4 * (cv.x + cv.y > 2 * c0), b["metal"])
    elif ctr == "nail":
        cv.paint(r < 3, 0.9, ramp("#141414", "#5a5a5a", "#a0a0a0"))
    cv.outline()
    return cv.a


def _dk(h: str) -> str:
    c = hexc(h) * 0.45
    return "#%02x%02x%02x" % tuple(int(v) for v in c)


# --- the lamp -------------------------------------------------------------------------------------------------------------------
GO = ramp("#0a2a14", "#14682e", "#2ec85a", "#7aff9a", "#e8ffe8")
PLAIN = ramp("#2a2420", "#7a6a58", "#d8c8a8", "#f4ead8", "#fffaf0")  # lamp_lit: warm white glass, tinted by the engine
STOP = ramp("#2a0806", "#801810", "#e03020", "#ff7a5a", "#fff0e8")


def lamp(sp: dict, go) -> np.ndarray:
    """A lamp of the world: GO a round lens lit green with an up chevron of light in it; STOP a square lens lit red with a bar of light across it.
    The fixture is the world's: a wire cage on a stem, a console bezel, a ward call-light box, an oil lantern, a brazier on a chain."""
    L = sp["lamp"]
    st = L["style"]
    mt = L["metal"]
    cv = Cv(LN, LN)
    cx, cy = LN / 2.0, 25.0
    rr = np.hypot(cv.x + 0.5 - cx, cv.y + 0.5 - cy)
    ax, ay = np.abs(cv.x + 0.5 - cx), np.abs(cv.y + 0.5 - cy)
    R = 11.5
    plain = go is None  # lamp_lit: a round lens with nothing in it
    if plain:
        go = True
    lens = (rr < R) if go else ((ax < R - 1) & (ay < R - 1))
    rim = ((rr < R + 3) & ~lens) if go else (((ax < R + 2) & (ay < R + 2)) & ~lens)
    # the fixture behind and around the lens
    if st == "bezel":
        if L.get("plate") == "hex":
            plate = (ax * 0.55 + ay < 19) & (ax < 19)
        else:
            plate = (ax < 18) & (ay < 16)
        cv.paint(plate, 0.4 + 0.25 * ((cv.x < cx - 12) | (cv.y < cy - 11)) - 0.15 * ((cv.x > cx + 12) | (cv.y > cy + 11)), mt)
        for sx, sy in ((-14, -12), (14, -12), (-14, 12), (14, 12)):
            cv.paint((np.hypot(cv.x + 0.5 - cx - sx, cv.y + 0.5 - cy - sy) < 1.6) & plate, 0.9, mt)
    elif st == "cage":
        stem = (np.abs(cv.x + 0.5 - cx) < 2) & (cv.y < cy - R - 2)
        cv.paint(stem, 0.5 + 0.3 * (cv.x < cx), mt)
        cap = (np.abs(cv.x + 0.5 - cx) < 8) & (cv.y >= cy - R - 4) & (cv.y < cy - R + 1)
        cv.paint(cap, 0.6 + 0.3 * (cv.y == int(cy - R - 4)), mt)
        if L.get("bulkhead"):
            cv.paint((rr < R + 4) & ~lens if go else ((ax < R + 3) & (ay < R + 3)) & ~lens, 0.5, mt)
    elif st == "lantern":
        ring = (np.abs(np.hypot(cv.x + 0.5 - cx, cv.y + 0.5 - 4) - 3.5) < 1.1) & (cv.y < 6)
        cv.paint(ring, 0.6, mt)
        roof = (cv.y >= 6) & (cv.y < cy - R + 1) & (np.abs(cv.x + 0.5 - cx) < 3 + (cv.y - 6) * 0.9)
        cv.paint(roof, 0.55 + 0.3 * (cv.x < cx) - 0.2 * (cv.x > cx + 3), mt)
        base = (cv.y >= cy + R - 1) & (cv.y < cy + R + 5) & (np.abs(cv.x + 0.5 - cx) < 10 - (cv.y - cy - R) * 0.8)
        cv.paint(base, 0.5 + 0.25 * (cv.x < cx), mt)
    elif st == "brazier":
        chain = (np.abs(cv.x + 0.5 - cx) < 1.5) & (cv.y < cy - R) & (np.mod(cv.y, 4) != 0)
        cv.paint(chain, 0.6, mt)
        bowl = (cv.y >= cy + 3) & (cv.y < cy + R + 5) & (np.abs(cv.x + 0.5 - cx) < 15 - np.maximum(cv.y - cy - 3, 0) * 0.6)
        cv.paint(bowl, 0.45 + 0.3 * (cv.x < cx - 4) - 0.2 * (cv.x > cx + 6) + 0.2 * (cv.y == int(cy + 3)), mt)
    cv.paint(rim, 0.55 + 0.3 * ((cv.x + cv.y) < (cx + cy - 6)) - 0.25 * ((cv.x + cv.y) > (cx + cy + 8)), mt)
    rp = PLAIN if plain else (GO if go else STOP)
    glow = np.clip(1.0 - (rr / (R + 1)) ** 1.5, 0, 1)
    cv.paint(lens, 0.35 + 0.45 * glow, rp, spread=0.6)
    if plain:  # a filament's hot heart instead of a symbol
        glyph = lens & (rr < 3.2)
    elif go:
        vv = (cv.y + 0.5 - (cy - 5)) - np.abs(cv.x + 0.5 - cx) * 0.95
        glyph = lens & (vv >= 0) & (vv < 4.5) & (np.abs(cv.x + 0.5 - cx) < 8.5)
    else:
        glyph = lens & (ay < 2.6) & (ax < 8)
    cv.paint(glyph, 1.0, rp)
    cv.paint(lens & edge_of(glyph) & ~glyph, 0.7, rp)
    if st == "cage":  # the wires of the cage over the lens
        wires = (lens | rim) & ((np.abs(cv.x + 0.5 - cx) < 0.6) | (np.abs(np.abs(cv.x + 0.5 - cx) - 7) < 0.6)) & ~glyph
        cv.paint(wires, 0.45, mt)
    if st == "brazier":  # tongues of the fire over the bowl's lip
        tongue = (cv.y < cy - R + 2) & (cv.y >= cy - R - 5) & (np.mod(cv.x, 5) < 2) & (np.abs(cv.x + 0.5 - cx) < 8) & (hash2(cv.x // 5, 1, 3 + go) > 0.3)
        cv.paint(tongue, 0.6, rp)
    cv.outline(0.7)
    return cv.a


# --- the sign post (outdoor ways) -------------------------------------------------------------------------------------------------
def sign(sp: dict, go: bool) -> np.ndarray:
    wd = sp["sign"]["wood"]
    cv = Cv(W, H)
    x, y = cv.x, cv.y
    post = (x >= 64) & (x < 80) & (y >= 40)
    cv.paint(post, 0.5 + 0.25 * (x < 69) - 0.15 * (x > 75) + 0.08 * np.sin(y * 0.3 + x), wd)
    cv.paint((x >= 56) & (x < 88) & (y >= H - 10), 0.35 + 0.2 * (y == H - 10), wd)
    if go:
        board = (y >= 46) & (y < 86) & (x >= 10) & (x < 112)
        tip = (x >= 112) & (x < 136) & (np.abs(y + 0.5 - 66) < (136 - x) * 0.85)
        b = board | tip
        cv.paint(b, 0.55 + 0.06 * np.sin(x * 0.4 + y * 0.05) + 0.2 * (y < 49) - 0.25 * (y > 83), np.vstack([wd[1:], np.clip(wd[-1:] * 1.35 + 20, 0, 255)]))
        arrow = ((y >= 62) & (y < 71) & (x >= 24) & (x < 106)) | ((x >= 94) & (x < 118) & (np.abs(y + 0.5 - 66.5) < (118 - x) * 0.8))
        cv.paint(arrow, 0.75, GO[:4])
    else:
        yy = y - (x - 18) * 0.55
        board = (yy >= 70) & (yy < 104) & (x >= 6) & (x < 76)
        cv.paint(board, 0.5 + 0.06 * np.sin(x * 0.4) + 0.2 * (yy < 73) - 0.25 * (yy > 100), wd)
        xx = (np.abs((x - 40) - (yy - 87) * 2.0) < 3.5) | (np.abs((x - 40) + (yy - 87) * 2.0) < 3.5)
        cv.paint(board & xx & (np.abs(x - 40) < 24), 0.5, STOP[:3])
        cv.paint((np.hypot(x - 70, y - 50) < 3), 0.8, ramp("#141414", "#5a5a5a", "#a0a0a0"))  # the nail it hangs from
    cv.outline()
    return cv.a


# --- the spill of light -----------------------------------------------------------------------------------------------------------
def spill(sp: dict) -> np.ndarray:
    """The light the open door throws on the floor: a trapezoid widening from the threshold, in stepped alpha through the ordered dither (additive)."""
    img = np.zeros((SPH, SPW, 4), np.float32)
    y, x = np.mgrid[0:SPH, 0:SPW]
    half = 40 + (y / SPH) * 56
    a = np.clip(1.0 - np.abs(x + 0.5 - SPW / 2) / half, 0, 1) ** 0.8 * np.clip(1.0 - y / SPH, 0, 1) ** 1.2
    d = bayer(SPH, SPW)
    steps = np.floor(a * 4 + d * 0.9) / 4.0
    img[..., :3] = hexc(sp["spill"])
    img[..., 3] = np.clip(steps, 0, 1) * 190
    return img


# --- the wizard (shared by every world) ------------------------------------------------------------------------------------------
def _wizard() -> np.ndarray:
    im = Image.open(os.path.join(ROOT, "assets", "story", "night_one", "textures", "thing_wizard.png")).convert("RGBA")
    img = np.array(im, np.float32)
    eyes = _eyes(img)  # found on the source colours, before the halo comes off and the colours are reduced
    return _quantise(_no_halo(img)), eyes


def _no_halo(img: np.ndarray) -> np.ndarray:
    """Takes the coloured rim light (yellow on his left, magenta on his right) off the silhouette: each rim pixel becomes the robe's shadow step,
    a one-pixel edge darker than its neighbour inside (style guide 6)."""
    a = img[..., 3] > 127
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    sat = (mx - mn) / np.maximum(mx, 1)
    warm = (r > 150) & (b < 120) & (sat > 0.45)
    mag = (r > 110) & (b > 90) & (g < 0.6 * r) & (sat > 0.4)
    near_edge = np.zeros_like(a)
    for dy in (-2, -1, 0, 1, 2):
        for dx in (-2, -1, 0, 1, 2):
            near_edge |= ~np.roll(np.roll(a, dy, 0), dx, 1)
    rim = a & near_edge & (warm | mag)
    rim &= ~((np.hypot(np.mgrid[0:img.shape[0], 0:img.shape[1]][1] - 24.5, np.mgrid[0:img.shape[0], 0:img.shape[1]][0] - 25.5) < 9) & ~mag)  # the orb keeps its glow
    out = img.copy()
    ink = hexc("#13111f")
    robe_d = hexc("#1a2036")
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    for _ in range(2):
        src = out.copy()
        for (y, x) in zip(*np.nonzero(rim)):
            nb = []
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                yy2, xx2 = y + dy, x + dx
                if 0 <= yy2 < img.shape[0] and 0 <= xx2 < img.shape[1] and a[yy2, xx2] and not rim[yy2, xx2]:
                    nb.append(src[yy2, xx2, :3])
            out[y, x, :3] = (np.mean(nb, 0) * 0.7) if nb else robe_d
    edge = a & near_edge & rim
    out[edge & ~np.roll(a, 1, 1) | edge & ~np.roll(a, -1, 1), :3] = np.minimum(out[edge & ~np.roll(a, 1, 1) | edge & ~np.roll(a, -1, 1), :3], ink + 20)
    return out


def _quantise(img: np.ndarray, n: int = 40) -> np.ndarray:
    """The wizard's source is a resampled crop (thousands of colours, audit F2/F12): reduce it to n colours, no dither, so he reads as pixel art."""
    a = img[..., 3] > 127
    rgb = Image.fromarray(np.clip(np.round(img[..., :3]), 0, 255).astype(np.uint8), "RGB")
    q = np.array(rgb.quantize(colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB"), np.float32)
    out = img.copy()
    out[a, :3] = q[a]
    out[..., 3] = np.where(a, 255, 0)
    return out


def put(img: np.ndarray, mask: np.ndarray, col, shade=1.0) -> None:
    c = np.asarray(col, np.float32)
    s = np.broadcast_to(np.asarray(shade, np.float32), mask.shape)
    img[mask, :3] = np.clip(c[None, :] * s[mask][:, None], 0, 255)
    img[mask, 3] = 255


def _eyes(img: np.ndarray) -> np.ndarray:
    y, x = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    return (img[..., 3] > 127) & (r > 140) & (g > 110) & (b < 110) & (y > 30) & (y < 44) & (x > 40) & (x < 70)


def _orb(img: np.ndarray) -> np.ndarray:
    y, x = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    return (img[..., 3] > 127) & (np.hypot(x - 24.5, y - 25.5) < 7.5)


def wizard_happy() -> np.ndarray:
    img, e = _wizard()
    y, x = np.mgrid[0:128, 0:128]
    img[e, :3] = hexc("#fff4a0")
    img[e & (x % 2 == 0), :3] = hexc("#ffffff")
    o = _orb(img)
    img[o, :3] = np.clip(img[o, :3] * 1.9 + 40, 0, 255)
    # the free arm raised to his side, beckoning: a sleeve from the shoulder up and out in three steps lit from the upper left, the hand curling in
    rp = ramp("#0e0e1a", "#161e34", "#202c4c", "#2e3e66")
    d = bayer(128, 128)
    pts = [(82, 66), (94, 56), (101, 44), (104, 33)]
    sleeve = np.zeros((128, 128), bool)
    shade = np.zeros((128, 128), np.float32)
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        for t in np.linspace(0, 1, 14):
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            rad = 6.4 - 1.6 * (cy < 50) * (50 - cy) / 17.0
            m = np.hypot(x - cx, y - cy) < rad
            sleeve |= m
            shade = np.where(m, np.maximum(shade, np.clip(0.55 - (x - cx) / rad * 0.35 - (y - cy) / rad * 0.1, 0, 1)), shade)
    idx = np.clip(np.floor(shade * 3 + (d - 0.5) * 0.8 + 0.5).astype(int), 0, 3)
    img[sleeve, :3] = rp[idx][sleeve]
    img[sleeve, 3] = 255
    cuff = sleeve & (y < 37) & (y > 32)
    img[cuff, :3] = rp[1]
    skin = ramp("#5a4a50", "#9a8a90", "#c8bcc0", "#e0d6d8")
    hand = np.hypot(x - 104.5, y - 27.5) < 4.6
    hs = np.clip(np.floor((0.7 - (x - 104.5) / 4.6 * 0.4 - (y - 27.5) / 4.6 * 0.3) * 3 + (d - 0.5) * 0.6 + 0.5).astype(int), 0, 3)
    img[hand, :3] = skin[hs][hand]
    img[hand, 3] = 255
    fing = (x >= 100) & (x <= 104) & (y >= 21) & (y <= 23)  # the fingers curled in, towards him
    img[fing, :3] = skin[2]
    img[fing, 3] = 255
    img[(x == 100) & (y >= 22) & (y <= 25), :3] = skin[1]
    img[(x == 100) & (y >= 22) & (y <= 25), 3] = 255
    ed = edge_of(img[..., 3] > 127) & (sleeve | hand | fing)
    img[ed, :3] *= 0.6
    return img


def wizard_sad() -> np.ndarray:
    src, e = _wizard()
    src[e, :3] = hexc("#2a2418")
    o = _orb(src)
    src[o, :3] = src[o, :3] * 0.45
    img = src.copy()
    # the head bowed: the hat and face (rows 0 to 58, the head's columns) drop and lean 2 px forward over the beard
    top, drop = 58, 12
    cols = slice(30, 100)
    head = src[0:top, cols].copy()
    img[0:top + drop, cols] = 0
    img[drop:top + drop, 32:102] = np.where(head[..., 3:4] > 127, head, img[drop:top + drop, 32:102])
    img[top + drop:top + drop + 4, cols] = np.where(src[top + drop:top + drop + 4, cols][..., 3:4] > 127, src[top + drop:top + drop + 4, cols], img[top + drop:top + drop + 4, cols])
    img[..., :3] = np.round(img[..., :3] * 0.86)
    return img


# --- the run ---------------------------------------------------------------------------------------------------------------------
NAMES = ["door_0", "door_1", "door_2", "door_3", "bars", "lamp_go", "lamp_stop", "lamp_lit", "sign_go", "sign_stop", "spill"]
SHARED = "warehouse"  # the set also written to the shared names (a stage whose map has no set of its own, the tests' maps)


def draw_set(sp: dict) -> dict:
    out = {}
    for k in range(4):
        out["door_%d" % k] = door(sp, k)
    out["bars"] = bars(sp)
    out["lamp_go"] = lamp(sp, True)
    out["lamp_stop"] = lamp(sp, False)
    out["lamp_lit"] = lamp(sp, None)
    out["sign_go"] = sign(sp, True)
    out["sign_stop"] = sign(sp, False)
    out["spill"] = spill(sp)
    return out


def main(only=None) -> int:
    """Draws every set; `only` (--only name,name): write just those names (a new piece of art without rewriting the rest)."""
    sets = _sets()
    for sid, sp in sets.items():
        for name, img in draw_set(sp).items():
            if only and name not in only:
                continue
            save(img, "%s/%s" % (sid, name))
            if sid == SHARED:
                save(img, name)
    if not only:
        save(wizard_happy(), "wizard_happy")
        save(wizard_sad(), "wizard_sad")
    return 0


def check() -> int:
    """Style guide 6 and 7 over the drawn art: alpha 0 or 255 on every billboard (spill is a glow), no resampled look (the MANYCOL limit of
    tools/art/texture_sheet.py), texels per metre 96 to 160 (doors, signs, lamps, bars)."""
    sys.path.insert(0, os.path.join(ROOT, "tools", "art"))
    import texture_sheet  # noqa: E402
    dens = {"door": W / 1.2, "sign": W / 1.2, "lamp": LN / LAMP_M, "bars": BN / BARS_M}
    bad = 0
    rows = []
    for sid in list(_sets().keys()) + [""]:
        for n in NAMES + (["wizard_happy", "wizard_sad"] if sid == "" else []):
            p = os.path.join(OUT, sid, n + ".png")
            im, nc, sm, sat = texture_sheet.stats(p)
            a = np.asarray(im)[..., 3]
            fringe = int(((a > 0) & (a < 255)).sum())
            flags = []
            if n != "spill" and fringe:
                flags.append("FRINGE")
            if nc > (1500 if max(im.size) >= 128 else 600):
                flags.append("MANYCOL")
            dd = dens.get(n.split("_")[0], 0.0)
            if dd and not (96 <= dd <= 160):
                flags.append("DENS")
            bad += 1 if flags else 0
            rows.append("%-10s %-13s %3dx%-3d colours %4d sat %.2f px/m %4.0f %s" % (sid or "(shared)", n, im.width, im.height, nc, sat, dd, ",".join(flags) or "ok"))
    print("\n".join(rows))
    print("%d of %d with a flag" % (bad, len(rows)))
    return 1 if bad else 0


def contact_sheet(path: str) -> int:
    """Every set in every state: a row per world (door shut .. wide, bars, lamps go/stop at 3x, signs, spill), on the world's key colour."""
    from PIL import ImageDraw
    sets = _sets()
    cell_w = [W] * 4 + [BN, LN * 3, LN * 3, W // 2, W // 2]
    gap = 10
    row_h = H + 26
    width = sum(cell_w) + gap * (len(cell_w) + 1)
    sheet = Image.new("RGB", (width, 30 + row_h * len(sets)), (20, 20, 24))
    d = ImageDraw.Draw(sheet)
    d.text((8, 8), "assets/run/choice/<set>: door_0 (shut) .. door_3 (wide), bars, lamp_go, lamp_stop (3x), sign_go, sign_stop (1/2), 1x unless said", fill=(230, 230, 230))
    for i, (sid, sp) in enumerate(sets.items()):
        y0 = 30 + i * row_h
        bg = tuple(int(v) for v in sp["room"][1])
        d.rectangle([0, y0, width, y0 + row_h - 2], fill=bg)
        d.text((8, y0 + 4), "%s  (%s)" % (sid, ", ".join(SET_MAPS[sid])), fill=(235, 225, 200))
        x = gap
        for j, n in enumerate(["door_0", "door_1", "door_2", "door_3", "bars", "lamp_go", "lamp_stop", "sign_go", "sign_stop"]):
            im = Image.open(os.path.join(OUT, sid, n + ".png")).convert("RGBA")
            if n.startswith("lamp"):
                im = im.resize((LN * 3, LN * 3), Image.NEAREST)
            if n.startswith("sign"):
                im = im.resize((W // 2, H // 2), Image.NEAREST)
            sheet.paste(im, (x, y0 + 20 + (H - im.height)), im)
            x += cell_w[j] + gap
    sheet.save(path, quality=86, optimize=True)
    print("sheet", path, sheet.size)
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    if "--sheet" in sys.argv:
        sys.exit(contact_sheet(sys.argv[sys.argv.index("--sheet") + 1]))
    if "--only" in sys.argv:
        sys.exit(main(sys.argv[sys.argv.index("--only") + 1].split(",")))
    sys.exit(main())
