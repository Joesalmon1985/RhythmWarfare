"""The heralds of the quest entrances (docs/art/HERALDS.md, lead ruling 25): one character from each quest, baked once, standing beside any entrance to that quest in
any world and gesturing towards it on the beat. `python tools/story/build_heralds.py` writes assets/story/heralds/.

Who (the owner may change any of these; each is the quest's own person, drawn from its own chapter's wardrobe so the player meets the same face inside):
  dungeon   the wizard of the Warehouse (assets/story/night_one/textures/thing_wizard.png): his staff held, his free arm sweeping out to point the way, the orb flaring on the beat.
  gospel    sh1, the shepherd of the first night (galilee_shore, J00 Bethlehem, the first scene of the path): a shepherd's crook planted in the left hand, the right arm sweeping out.
  squadron  gun, the young Gunner (airfield; the Flight Line C02, the bomber C04, his last flight C07): a big airman's wave over the head, then the arm drops to point the way.
  ember     bram_o, Bram the gardener (orchard, E00, the companion of the whole road): the Ember in a little glass jar held up in the left hand, glowing, the right arm sweeping out.

The gesture (GESTURES): a loop of 8 frames over 2 beats (4 a beat), feet planted, the body facing the player, one arm going out to the entrance on the first beat and thrusting
the point home on the second, the body leaning into it. It is baked pointing to screen RIGHT; the runtime (src/story/story_heralds.gd) mirrors it when the entrance is on the
left of the herald on screen. Nothing in it dances: no bounce, no second arm pumping, the head steady.

Output (deterministic): assets/story/heralds/heralds.png (RGBA; every frame of every herald at the full and the half level of detail, the body and, where a herald carries a
light, its glow as a second frame of the same size), heralds.json (the frame table), and wizard_<n>.png (the wizard's frames as whole 128 x 128 billboard textures, for an
entrance that IS the wizard: the Warehouse Floor, where his map billboard plays the gesture itself).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

from . import lib, people, wardrobe

ROOT = lib.ROOT
OUT_DIR = os.path.join(ROOT, "assets", "story", "heralds")
KEYS = ["arm_l", "arm_r", "elb_l", "elb_r", "leg_l", "leg_r", "lean", "head_tilt", "head_drop", "squash", "roll", "crouch", "lift_l", "lift_r", "fwd"]
FPB = 4  # frames a beat
LOOP_BEATS = 2
HERO_M = 1.7  # a build-1.0 adult's standing height in the world (StoryCrowd.HERO_M): people.H0 sheet pixels
SHEET_W = 1024
EMBER = ["#7a2a10", "#d0581a", "#ff9a30", "#ffe08a"]  # the coal's own light (the glow layer, drawn unlit)

# ---- the gestures: 8 poses over 2 beats, the pointing arm the right one (screen right in the front view) ------------------------------------------------------
# beat 1: the arm sweeps out from the chest to the point; beat 2: the point thrust home (the lean deepest on the beat), then the arm starts back.
_SWEEP = [dict(arm_r=0.45, elb_r=2.3, lean=0.0), dict(arm_r=0.95, elb_r=1.4, lean=-0.02), dict(arm_r=1.5, elb_r=0.4, lean=-0.05), dict(arm_r=1.72, elb_r=0.05, lean=-0.07, leg_r=0.08),
          dict(arm_r=1.84, elb_r=0.0, lean=-0.1, leg_r=0.1), dict(arm_r=1.76, elb_r=0.04, lean=-0.08, leg_r=0.1), dict(arm_r=1.72, elb_r=0.08, lean=-0.07, leg_r=0.08),
          dict(arm_r=1.2, elb_r=1.0, lean=-0.03)]
# the airman: a big wave over the head on beat 1, then down to the point on beat 2
_WAVE_OVER = [dict(arm_r=2.55, elb_r=0.3, lean=0.02), dict(arm_r=2.62, elb_r=1.05, lean=0.02), dict(arm_r=2.55, elb_r=0.3, lean=0.01), dict(arm_r=2.62, elb_r=1.05, lean=0.0),
              dict(arm_r=1.84, elb_r=0.0, lean=-0.1, leg_r=0.1), dict(arm_r=1.76, elb_r=0.04, lean=-0.08, leg_r=0.1), dict(arm_r=1.72, elb_r=0.08, lean=-0.07, leg_r=0.08),
              dict(arm_r=2.2, elb_r=0.5, lean=-0.02)]
GESTURES = {"sweep": _SWEEP, "wave_over": _WAVE_OVER}

# the free (left) arm: a hand at the hip, or holding the herald's own thing
FREE_ARM = {"hip": dict(arm_l=0.55, elb_l=1.9), "crook": dict(arm_l=0.5, elb_l=0.75), "jar": dict(arm_l=0.62, elb_l=2.05)}

HERALDS = {
    "dungeon": {"kind": "wizard", "title": "the wizard of the Warehouse", "chapter": "night_one", "who": "thing_wizard"},
    "gospel": {"kind": "person", "title": "the shepherd of the first night (J00)", "chapter": "galilee_shore", "who": "sh1", "gesture": "sweep", "free": "crook", "face": "happy"},
    "squadron": {"kind": "person", "title": "the young Gunner", "chapter": "airfield", "who": "gun", "gesture": "wave_over", "free": "hip", "face": "happy"},
    "ember": {"kind": "person", "title": "Bram the gardener", "chapter": "orchard", "who": "bram_o", "gesture": "sweep", "free": "jar", "face": "happy"},
}
QUESTS = list(HERALDS)


def spec_of(chapter: str, aid: str) -> dict:
    data = json.load(open(os.path.join(ROOT, "content", "story", chapter + ".json"), encoding="utf-8"))
    return wardrobe.cast_chapter(chapter, data["actors"])[aid]


def poses_of(h: dict) -> list:
    out = []
    for p in GESTURES[h["gesture"]]:
        pose = {k: 0.0 for k in KEYS}
        pose.update(arm_l=0.14, arm_r=0.14, elb_l=0.2, elb_r=0.2)
        pose.update(FREE_ARM[h["free"]])
        pose.update(p)
        out.append(pose)
    return out


# ---- the heralds' own things, drawn on the person's canvas (people.py draws props in the right hand only) -----------------------------------------------------
def _crook(cv, b, S, z):
    """A shepherd's crook planted on the ground beside the left foot, held in the left hand, its hook over the head (material `extra`: the herald's wood)."""
    hx, hy = b.arms["l"]["hand"]
    x = hx
    top = -1.12 * S
    for dx, step in ((0.0, people.MID), (0.6, people.DARK)):
        people.seg(cv, (x + dx, -0.005 * S), (x + dx, top), "extra", step, z)
    # the hook: a half circle bending outwards (away from the body: to screen left), open downwards
    r = 0.055 * S
    cx = x - r
    for k in range(0, 19):
        a = np.pi * k / 18.0
        cv.dot(cx + r * np.cos(a), top - r * np.sin(a) * 0.9, "extra", people.MID, z)
        cv.dot(cx + r * np.cos(a), top - r * np.sin(a) * 0.9 + 0.8, "extra", people.DARK, z)
    people.seg(cv, (cx - r, top), (cx - r, top + 0.03 * S), "extra", people.MID, z)


def _jar(cv, b, S, z):
    """A little glass jar held up in the left hand with the Ember in it: the coal is `lit` (the glow layer), the glass `glass`."""
    hx, hy = b.arms["l"]["hand"]
    w, h = 0.026 * S, 0.05 * S
    top = hy - h * 0.75
    people.poly_fill(cv, [(hx - w, top), (hx + w, top), (hx + w, top + h), (hx - w, top + h)], z, "glass", lambda X, Y: np.where(X < hx - w * 0.3, 0.9, 0.55))
    people.poly_fill(cv, [(hx - w * 1.1, top - 0.012 * S), (hx + w * 1.1, top - 0.012 * S), (hx + w * 1.1, top), (hx - w * 1.1, top)], z + 0.01, "acc", 0.45)
    people.ellipse(cv, (hx, top + h * 0.6), w * 0.62, h * 0.32, 0.0, z + 0.02, lambda lx, ly, u, v: (people.M["lit"], 0.0))


def render(spec: dict, pose: dict, h: dict, lod: int):
    """people.render_frame with the herald's own thing drawn in: (index image, pivot)."""
    S = people.H0 / lod * float(spec.get("height", 1.0))
    w = int(S * 1.1) + 8 + 2 * int(S * 0.25)  # room for the arm out to the side
    hh = int(S * 1.45) + 8
    ox, oy = w / 2.0, hh - 4.0
    cv = people.Canvas(w, hh, ox, oy)
    b = people.Body(spec, pose, S, 0, "point")
    pt = people.Painter(cv, b, spec, lod, "", h.get("face", "happy"), int(spec.get("seed", 0)))
    pt.draw()
    z = pt.arm_z("l") + 0.15
    if h.get("free") == "crook":
        _crook(cv, b, S, z)
    elif h.get("free") == "jar":
        _jar(cv, b, S, z)
    idx = people.finish(cv)
    ys, xs = np.nonzero(idx)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return idx[y0:y1, x0:x1].copy(), (ox - x0, oy - y0)


def to_rgba(spec: dict, idx: np.ndarray):
    """(body RGBA, glow RGBA): the palette applied; the emissive `lit` pixels go to the glow layer in the Ember's colours instead (drawn unlit at run time)."""
    colours = dict(spec["colours"])
    colours.setdefault("extra", "#7a5634")
    colours["extra"] = "#7a5634"  # the crook's wood
    pal = np.array(people.palette_row(colours), np.uint8)
    m = idx > 0
    mat = (idx & 127) >> 2
    step = idx & 3
    body = np.zeros(idx.shape + (4,), np.uint8)
    body[m] = pal[idx[m] & 127]
    body[..., 3] = np.where(m, 255, 0)
    lit = m & (mat == people.M["lit"])
    glow = np.zeros_like(body)
    if lit.any():
        ember = np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in EMBER], np.uint8)
        glow[lit, :3] = ember[step[lit]]
        glow[lit, 3] = 255
        body[lit] = 0
    return body, glow


# ---- the wizard: his billboard art, the free arm pointing -------------------------------------------------------------------------------------------------------
_WIZ_ARMS = [  # the sleeve's points from the shoulder to the wrist, and the orb's flare (1 on the beat)
    ([(82, 64), (96, 56), (104, 44), (106, 32)], 1.0),
    ([(82, 64), (96, 58), (107, 50), (114, 44)], 0.6),
    ([(82, 64), (96, 61), (108, 58), (118, 56)], 0.4),
    ([(82, 64), (97, 61), (109, 59), (120, 58)], 0.3),
    ([(82, 64), (98, 62), (111, 60), (122, 59)], 1.0),
    ([(82, 64), (97, 61), (109, 59), (120, 58)], 0.6),
    ([(82, 64), (96, 61), (108, 58), (118, 56)], 0.4),
    ([(82, 64), (96, 58), (107, 50), (114, 44)], 0.3),
]


def wizard_frames() -> list:
    """The wizard's 8 frames as 128 x 128 RGBA (the canvas of thing_wizard.png, so his map billboard can show them as they are)."""
    sys.path.insert(0, os.path.join(ROOT, "tools", "run"))
    import make_choice_art as mca  # the wizard's own pixel helpers (his eyes, his orb, the sleeve's colours)
    out = []
    y, x = np.mgrid[0:128, 0:128]
    robe, robe_l, skin = mca.hexc("#1c2a48"), mca.hexc("#30447a"), mca.hexc("#c8ccd6")
    for pts, flare in _WIZ_ARMS:
        img = mca._wizard()
        e = mca._eyes(img)
        img[e, :3] = mca.hexc("#fff4a0")
        img[e & (x % 2 == 0), :3] = mca.hexc("#ffffff")
        o = mca._orb(img)
        img[o, :3] = np.clip(img[o, :3] * (1.3 + 0.8 * flare) + 30 * flare, 0, 255)
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            for t in np.linspace(0, 1, 14):
                cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                mk = np.hypot(x - cx, y - cy) < 6.0
                mca.put(img, mk, robe, 1.0)
                mca.put(img, mk & (y < cy - 1.5), robe_l, 1.0)
        wx, wy = pts[-1]
        dx, dy = wx - pts[-2][0], wy - pts[-2][1]
        ln = max(np.hypot(dx, dy), 1e-6)
        ux, uy = dx / ln, dy / ln
        hand = np.hypot(x - (wx + ux * 3.0), y - (wy + uy * 3.0)) < 4.2
        mca.put(img, hand, skin)
        if pts[-1][1] > 50:  # pointing: one finger out along the arm
            for k in range(3, 8):
                mca.put(img, (np.abs(x - (wx + ux * (3 + k))) < 1.0) & (np.abs(y - (wy + uy * (3 + k))) < 1.0), skin, 1.0 if k < 7 else 0.85)
        else:  # the beckon at the top: the fingers curled in
            mca.put(img, (np.abs(x - (wx - 2)) < 2) & (np.abs(y - (wy - 6)) < 2), skin, 0.85)
        rim = (img[..., 3] > 127) & ~np.roll(img[..., 3] > 127, -2, axis=0) & (x > 84) & (y < 66)
        img[rim, :3] = mca.hexc("#f4bc4a")  # the warm rim along the top of the arm, the club light on him
        # the orb's flare: a ring of light pixels round the orb on the beat
        if flare >= 0.99:
            ring = (np.abs(np.hypot(x - 24.5, y - 25.5) - 9.0) < 0.8) & ((x + y) % 2 == 0)
            img[ring, :3] = mca.hexc("#c8f0ff")
            img[ring, 3] = 255
        out.append(np.clip(img, 0, 255).astype(np.uint8))
    return out


# ---- the quest's mark over the entrance: a small sign in the quest's colour, lit by itself (drawn unlit at run time, swelling on the beat) ---------------------------
MARK_PX = 24
MARK_M = 0.42  # its size in the world
COLOURS = {"dungeon": "#9a7aff", "gospel": "#ffd25a", "squadron": "#8cff9a", "ember": "#ff9a30"}


def _rgb(h: str) -> np.ndarray:
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32)


def mark(quest: str) -> np.ndarray:
    """The quest's sign, MARK_PX square: dungeon an arched door with a chevron pointing down (the way down), gospel an eight-pointed star, squadron an airman's wings
    round a lit dot (the radio's green), ember a flame. A one-pixel dark edge keeps it readable on a bright wall."""
    n = MARK_PX
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) + 0.5
    cx = cy = n / 2.0
    col = _rgb(COLOURS[quest])
    hot = np.minimum(col * 0.45 + 150, 255)
    shape = np.zeros((n, n), bool)
    core = np.zeros((n, n), bool)
    if quest == "gospel":
        ang = np.arctan2(y - cy, x - cx)
        r = np.hypot(x - cx, y - cy)
        rr = 3.2 + 7.6 * np.abs(np.cos(ang * 4.0)) ** 6 + 2.0 * np.abs(np.cos(ang * 4.0 + np.pi / 2)) ** 8 * 0
        shape = r < rr
        core = r < 3.0
    elif quest == "ember":
        u = (x - cx) / 6.5
        v = (y - 4.0) / 16.0
        width = np.clip(np.sin(np.clip(v, 0, 1) * np.pi * 0.95) * (0.55 + 0.45 * v), 0, None)
        shape = (np.abs(u + 0.25 * np.sin(v * 5.0) * (1 - v)) < width) & (v > 0) & (v < 1.05)
        core = shape & (np.abs(u) < width * 0.45) & (v > 0.45)
    elif quest == "squadron":
        r = np.hypot(x - cx, y - cy)
        wing = (np.abs(y - cy - (np.abs(x - cx) - 4) * 0.25) < 1.6 - np.abs(x - cx) * 0.05) & (np.abs(x - cx) < 11)
        wing2 = (np.abs(y - cy - 2.5 - (np.abs(x - cx) - 4) * 0.25) < 1.0) & (np.abs(x - cx) < 8.5)
        shape = wing | wing2 | (r < 4.2)
        core = r < 2.6
    else:  # dungeon
        arch = ((np.abs(x - cx) < 7.5) & (y > 9) & (y < 22)) | (np.hypot(x - cx, y - 9) < 7.5)
        inner = ((np.abs(x - cx) < 5.0) & (y > 9) & (y < 22)) | (np.hypot(x - cx, y - 9) < 5.0)
        chev = (np.abs((y - 11) - (4 - np.abs(x - cx)) * 0.9) < 1.3) & (np.abs(x - cx) < 4.2)
        shape = arch & ~(inner & ~chev)
        core = chev
    img = np.zeros((n, n, 4), np.float32)
    img[shape, :3] = col
    img[core, :3] = hot
    img[shape | core, 3] = 255
    solid = shape | core
    edge = np.zeros_like(solid)
    for dy_, dx_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        edge |= np.roll(np.roll(solid, dy_, 0), dx_, 1)
    edge &= ~solid
    img[edge, :3] = (18, 10, 30)
    img[edge, 3] = 220
    return np.clip(img, 0, 255).astype(np.uint8)


def _trim(img: np.ndarray, pivot):
    a = img[..., 3] > 0
    ys, xs = np.nonzero(a)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return img[y0:y1, x0:x1], (pivot[0] - x0, pivot[1] - y0)


def build() -> dict:
    os.makedirs(OUT_DIR, exist_ok=True)
    items = []  # (quest, lod, i, body, glow, pivot)
    meta = {}
    for q, h in HERALDS.items():
        if h["kind"] == "wizard":
            frames = wizard_frames()
            for i, f in enumerate(frames):
                Image.fromarray(f, "RGBA").save(os.path.join(OUT_DIR, f"wizard_{i}.png"), optimize=False, compress_level=9)
                Image.fromarray(f[:, ::-1].copy(), "RGBA").save(os.path.join(OUT_DIR, f"wizard_{i}_l.png"), optimize=False, compress_level=9)  # (a billboard cannot be mirrored by its scale)
            # the billboard thing is `size` 1.7 m for its 128 px canvas, the feet at the canvas' bottom centre
            for lod in (1, 2):
                for i, f in enumerate(frames):
                    im = Image.fromarray(f, "RGBA")
                    if lod == 2:
                        im = im.resize((64, 64), Image.NEAREST)
                    arr = np.array(im)
                    body, piv = _trim(arr, (arr.shape[1] / 2.0, float(arr.shape[0])))
                    items.append((q, lod, i, body, None, piv))
            meta[q] = {"title": h["title"], "chapter": h["chapter"], "who": h["who"], "px_per_m": {"1": 128 / 1.7, "2": 64 / 1.7},
                       "self_frames": [f"res://assets/story/heralds/wizard_{i}.png" for i in range(len(frames))],
                       "self_frames_left": [f"res://assets/story/heralds/wizard_{i}_l.png" for i in range(len(frames))]}
            continue
        spec = spec_of(h["chapter"], h["who"])
        for lod in (1, 2):
            for i, pose in enumerate(poses_of(h)):
                idx, piv = render(spec, pose, h, lod)
                body, glow = to_rgba(spec, idx)
                items.append((q, lod, i, body, glow if glow[..., 3].any() else None, piv))
        ppm = people.H0 / HERO_M
        meta[q] = {"title": h["title"], "chapter": h["chapter"], "who": h["who"], "px_per_m": {"1": ppm, "2": ppm / 2.0}}
    for q in HERALDS:
        items.append((q, 0, 0, mark(q), None, (MARK_PX / 2.0, MARK_PX / 2.0)))  # lod 0: the quest's mark (its pivot at its centre)
    # shelf packing, tallest first
    tiles = []
    for k, it in enumerate(items):
        tiles.append((k, "body", it[3]))
        if it[4] is not None:
            tiles.append((k, "glow", it[4]))
    order = sorted(range(len(tiles)), key=lambda j: (-tiles[j][2].shape[0], j))
    x = y = row_h = 0
    place = {}
    for j in order:
        h_, w_ = tiles[j][2].shape[:2]
        if x + w_ + 1 > SHEET_W:
            x, y, row_h = 0, y + row_h + 1, 0
        place[j] = (x, y)
        x += w_ + 1
        row_h = max(row_h, h_)
    H = 1
    while H < y + row_h:
        H *= 2
    sheet = np.zeros((H, SHEET_W, 4), np.uint8)
    rect = {}
    for j, (k, layer, img) in enumerate(tiles):
        px, py = place[j]
        sheet[py:py + img.shape[0], px:px + img.shape[1]] = img
        rect[(k, layer)] = [px, py, int(img.shape[1]), int(img.shape[0])]
    Image.fromarray(sheet, "RGBA").save(os.path.join(OUT_DIR, "heralds.png"), optimize=False, compress_level=9)
    for q in meta:
        meta[q]["lods"] = {}
    for k, (q, lod, i, body, glow, piv) in enumerate(items):
        if lod == 0:
            meta[q]["mark"] = {"rect": rect[(k, "body")], "px_per_m": round(MARK_PX / MARK_M, 4), "colour": COLOURS[q]}
            continue
        lods = meta[q]["lods"].setdefault(str(lod), {"frames": [], "glow": []})
        lods["frames"].append(rect[(k, "body")] + [round(float(piv[0]), 2), round(float(piv[1]), 2)])
        lods["glow"].append(rect.get((k, "glow"), []))
    for q in meta:
        meta[q]["px_per_m"] = {k: round(v, 4) for k, v in meta[q]["px_per_m"].items()}
        fr = meta[q]["lods"]["1"]["frames"]
        meta[q]["height_m"] = round(max(f[5] for f in fr) / meta[q]["px_per_m"]["1"], 3)  # the tallest frame above the feet (the wave, the crook)
    doc = {"version": 1, "sheet": "res://assets/story/heralds/heralds.png", "frames_per_beat": FPB, "loop_beats": LOOP_BEATS, "points": "right",
           "frame_fields": ["x", "y", "w", "h", "pivot_x", "pivot_y"], "heralds": meta}
    with open(os.path.join(OUT_DIR, "heralds.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"heralds: {len(meta)} heralds, {len(items)} frames, sheet {SHEET_W} x {H}")
    return doc


def strips(out_dir: str, zoom: int = 3) -> list:
    """One strip a herald (docs/shots/art/heralds/strip_<quest>.png): the 8 frames of the loop at the full size, zoomed, on the night colour, with the beat marked under
    frames 0 and 4, and the mirrored first point frame at the end (an entrance on the left)."""
    doc = json.load(open(os.path.join(OUT_DIR, "heralds.json"), encoding="utf-8"))
    sheet = np.array(Image.open(os.path.join(OUT_DIR, "heralds.png")).convert("RGBA"))
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for q, m in doc["heralds"].items():
        fr = m["lods"]["1"]["frames"]
        gl = m["lods"]["1"]["glow"]
        cells = []
        for i, f in enumerate(fr):
            x, y, w, h, px, py = f
            im = Image.fromarray(sheet[y:y + h, x:x + w])
            if gl[i]:
                gx, gy, gw, gh = gl[i]
                im.alpha_composite(Image.fromarray(sheet[gy:gy + gh, gx:gx + gw]))
            cells.append((im, px, py, i % FPB == 0))
        mx, my, mw, mh = fr[4][:4]
        mir = Image.fromarray(sheet[my:my + mh, mx:mx + mw]).transpose(Image.FLIP_LEFT_RIGHT)
        cells.append((mir, mw - fr[4][4], fr[4][5], False))
        left = max(c[1] for c in cells)
        right = max(c[0].width - c[1] for c in cells)
        top = max(c[2] for c in cells)
        cw = int(left + right) + 8
        can = Image.new("RGBA", (cw * len(cells), int(top) + 14), (36, 26, 56, 255))
        for k, (im, px, py, beat) in enumerate(cells):
            ox = k * cw + 4 + int(left - px)
            can.alpha_composite(im, (ox, int(top - py) + 4))
            if beat:
                can.paste((255, 210, 90, 255), (k * cw + cw // 2 - 3, can.height - 6, k * cw + cw // 2 + 3, can.height - 3))
            if k == len(cells) - 1:
                can.paste((120, 120, 160, 255), (k * cw, 0, k * cw + 1, can.height))
        can = can.resize((can.width * zoom, can.height * zoom), Image.NEAREST)
        p = os.path.join(out_dir, f"strip_{q}.png")
        can.convert("RGB").save(p)
        paths.append(p)
    return paths
