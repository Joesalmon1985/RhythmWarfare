"""The choice language's own props (docs/CHOICE_CLARITY.md "Art"), drawn by code into assets/run/choice/ (deterministic; rerun after an edit, then `godot --headless --path . --import`).

Every prop is a billboard the choice layer (src/run/choice_props.gd) stands in the world at an option's anchor, with depth, lit like a thing:

* door_0..door_3   a door in a steel frame, from shut (0) to wide open (3): the leaf swings towards the viewer on its left hinge and the doorway behind it is lit.
                   48 x 96 px for 1.2 x 2.4 m. The open frames show a bright doorway and a spill of light on the threshold; the shut one a dark leaf with two panels and a handle.
* bars             two boards nailed across in an X, red and white: "this way is shut" (on a doorway that is a thing of the map already, e.g. a crack in the wall, or over a shut door).
* lamp_go          a round lamp, lit green, with a white chevron pointing up (go): 24 px for 0.36 m.
* lamp_stop        a square lamp, lit red, with a white bar across (stop): 24 px.
* wizard_happy     the Warehouse wizard (assets/story/night_one/textures/thing_wizard.png) with his free arm raised, beckoning, eyes bright and the orb of his staff blazing.
* wizard_sad       the same wizard with his head bowed (hat and face lowered), eyes dark, the orb dimmed: he still holds out his hand, low.
Colour is never the only signal: open vs shut, the chevron vs the bar, round vs square, arm up vs head down.
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "assets", "run", "choice")


def hexc(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def blank(w: int, h: int) -> np.ndarray:
    return np.zeros((h, w, 4), np.float32)


def put(img: np.ndarray, mask: np.ndarray, col, shade=1.0) -> None:
    c = np.asarray(col, np.float32)
    s = np.broadcast_to(np.asarray(shade, np.float32), mask.shape)
    img[mask, :3] = np.clip(c[None, :] * s[mask][:, None], 0, 255)
    img[mask, 3] = 255


def dither(w: int, h: int) -> np.ndarray:
    b = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16.0
    return np.tile(b, (h // 4 + 1, w // 4 + 1))[:h, :w]


def save(img: np.ndarray, name: str) -> None:
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, name + ".png"))
    print("wrote", os.path.relpath(os.path.join(OUT, name + ".png"), ROOT))


# --- the door -----------------------------------------------------------------------------------------------------------------
W, H = 48, 96
FRAME = hexc("#7c8894")
FRAME_D = hexc("#3a424c")
LEAF = hexc("#6a3e22")
LEAF_D = hexc("#3c2010")
LIGHT = hexc("#fff6d8")
GLOW = hexc("#ffd88a")


def door(k: int) -> np.ndarray:
    """k = 0 (shut) .. 3 (wide open)."""
    img = blank(W, H)
    y, x = np.mgrid[0:H, 0:W]
    d = dither(W, H)
    ox0, ox1, oy0 = 6, W - 6, 8  # the doorway (inside the frame)
    frame = ((x >= 2) & (x < W - 2) & (y >= 4)) & ~((x >= ox0) & (x < ox1) & (y >= oy0))
    put(img, frame, FRAME, 0.75 + 0.25 * (x < 6) - 0.25 * (x >= W - 6) + 0.08 * (d > 0.5))
    put(img, frame & ((x == 2) | (x == W - 3) | (y == 4)), FRAME_D)
    inside = (x >= ox0) & (x < ox1) & (y >= oy0)
    if k == 0:
        put(img, inside, LEAF, 0.85 + 0.1 * (d > 0.6) - 0.15 * ((x - ox0) % 9 == 0))  # boards
        for (py0, py1) in ((14, 44), (52, 86)):  # two raised panels
            p = (x >= ox0 + 5) & (x < ox1 - 5) & (y >= py0) & (y < py1)
            put(img, p, LEAF, 1.05 + 0.08 * (d > 0.5))
            put(img, p & ((x == ox0 + 5) | (y == py0)), LEAF_D)
        put(img, (x >= ox1 - 9) & (x < ox1 - 6) & (y >= 48) & (y < 52), hexc("#d8c070"))  # handle
        return img
    # the doorway lit from behind, brighter at the floor; the leaf swung out into the room on its left hinge, narrower the wider it stands open
    open_w = ox1 - ox0
    leaf_w = int(round(open_w * (0.72, 0.42, 0.2)[k - 1]))
    put(img, inside, LIGHT, 0.82 + 0.18 * (y - oy0) / (H - oy0) + 0.06 * (d > 0.5))
    put(img, inside & (y < oy0 + 4), GLOW, 1.0)
    grow = 2 + 2 * k  # its outer edge stands taller: nearer the viewer
    top = oy0 - ((x - ox0 + 1) * grow) // max(leaf_w, 1)
    leaf = (x >= ox0 - 1) & (x < ox0 - 1 + leaf_w) & (y >= top) & (y < H)
    put(img, leaf, LEAF, 0.62 + 0.12 * (d > 0.6) - 0.12 * ((x - ox0) % 7 == 0))
    put(img, leaf & (x == ox0 - 2 + leaf_w), LEAF_D)
    return img


def spill() -> np.ndarray:
    """The light the open door throws on the floor in front of it: a soft trapezoid, alpha blended (64 x 32)."""
    w, h = 64, 32
    img = blank(w, h)
    y, x = np.mgrid[0:h, 0:w]
    half = 14 + (y / h) * 18
    a = np.clip(1.0 - np.abs(x + 0.5 - w / 2) / half, 0, 1) * np.clip(1.0 - y / h, 0, 1)
    img[..., :3] = GLOW
    img[..., 3] = (a * 200).astype(np.float32)
    return img


def bars() -> np.ndarray:
    n = 64
    img = blank(n, n)
    y, x = np.mgrid[0:n, 0:n]
    for sgn in (1, -1):
        c = (x - n / 2) * sgn - (y - n / 2)
        board = np.abs(c) < 6
        board &= (x > 1) & (x < n - 2) & (y > 1) & (y < n - 2)
        along = ((x + y * sgn) // 8) % 2 == 0
        put(img, board, np.where(along[..., None], hexc("#d02818"), hexc("#f0ece0"))[board] if False else hexc("#d02818"), 1.0)
        img[board & along, :3] = hexc("#f0ece0")
        put(img, board & (np.abs(np.abs(c) - 5.5) < 0.6), hexc("#401008"))
    for (cx, cy) in ((10, 10), (n - 11, 10), (10, n - 11), (n - 11, n - 11), (n // 2, n // 2)):  # nails
        put(img, (np.abs(x - cx) <= 1) & (np.abs(y - cy) <= 1), hexc("#202020"))
    return img


def lamp(go: bool) -> np.ndarray:
    n = 24
    img = blank(n, n)
    y, x = np.mgrid[0:n, 0:n]
    r = np.hypot(x + 0.5 - n / 2, y + 0.5 - n / 2)
    if go:
        body = r < 10.5
        put(img, body, hexc("#202a24"))
        put(img, r < 9, hexc("#2ee86a"), 0.85 + 0.25 * (r < 5))
        v = (y - 7) - np.abs(x + 0.5 - n / 2)
        chev = (v >= 0) & (v < 3) & (np.abs(x + 0.5 - n / 2) < 6.5)
        put(img, chev, hexc("#ffffff"))
    else:
        body = (np.abs(x + 0.5 - n / 2) < 10.5) & (np.abs(y + 0.5 - n / 2) < 10.5)
        put(img, body, hexc("#2a2020"))
        inner = (np.abs(x + 0.5 - n / 2) < 9) & (np.abs(y + 0.5 - n / 2) < 9)
        put(img, inner, hexc("#ff3020"), 0.85 + 0.2 * (r < 5))
        put(img, inner & (np.abs(y + 0.5 - n / 2) < 2) & (np.abs(x + 0.5 - n / 2) < 6.5), hexc("#ffffff"))
    return img


# --- the wizard -----------------------------------------------------------------------------------------------------------------
def _wizard() -> np.ndarray:
    im = Image.open(os.path.join(ROOT, "assets", "story", "night_one", "textures", "thing_wizard.png")).convert("RGBA")
    return np.array(im, np.float32)


def _eyes(img: np.ndarray) -> np.ndarray:
    y, x = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    return (img[..., 3] > 127) & (r > 140) & (g > 110) & (b < 110) & (y > 30) & (y < 44) & (x > 40) & (x < 70)


def _orb(img: np.ndarray) -> np.ndarray:
    y, x = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    return (img[..., 3] > 127) & (np.hypot(x - 24.5, y - 25.5) < 7.5)


def wizard_happy() -> np.ndarray:
    img = _wizard()
    y, x = np.mgrid[0:128, 0:128]
    e = _eyes(img)
    img[e, :3] = hexc("#fff4a0")
    img[e & (x % 2 == 0), :3] = hexc("#ffffff")
    o = _orb(img)
    img[o, :3] = np.clip(img[o, :3] * 1.9 + 40, 0, 255)
    # the free arm raised to his side, beckoning: a sleeve from the shoulder up and out, the hand at the top curling in
    robe = hexc("#1c2a48")
    robe_l = hexc("#30447a")
    skin = hexc("#c8ccd6")
    pts = [(82, 64), (96, 56), (104, 44), (106, 32)]
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        for t in np.linspace(0, 1, 12):
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            m = np.hypot(x - cx, y - cy) < 6.2
            put(img, m, robe, 1.0)
            put(img, m & (x < cx - 1.5), robe_l, 1.0)
    hand = (np.hypot(x - 107.5, y - 24.5) < 5.5)
    put(img, hand, skin)
    put(img, (x >= 103) & (x <= 106) & (y >= 19) & (y <= 22), skin, 0.85)  # the fingers curled in, towards him
    put(img, (x == 108) & (y >= 20) & (y <= 23), skin, 1.1)
    put(img, hand & (x > 110), skin, 0.7)
    # the warm rim on the new arm's lit side, so it sits in the club light like the rest of him
    rim = (img[..., 3] > 127) & ~np.roll(img[..., 3] > 127, -2, axis=1) & (x > 84) & (y < 64)
    img[rim, :3] = hexc("#f4bc4a")
    return img


def wizard_sad() -> np.ndarray:
    src = _wizard()
    e = _eyes(src)
    src[e, :3] = hexc("#2a2418")
    o = _orb(src)
    src[o, :3] = src[o, :3] * 0.45
    img = src.copy()
    # the head bowed: the hat and face (rows 0 to 58, the head's columns) drop 7 px and lean 2 px forward over the beard
    top, drop = 58, 12
    cols = slice(30, 100)
    head = src[0:top, cols].copy()
    img[0:top + drop, cols] = 0
    img[drop:top + drop, 32:102] = np.where(head[..., 3:4] > 127, head, img[drop:top + drop, 32:102])
    img[top + drop:top + drop + 4, cols] = np.where(src[top + drop:top + drop + 4, cols][..., 3:4] > 127, src[top + drop:top + drop + 4, cols], img[top + drop:top + drop + 4, cols])
    img[..., :3] *= 0.86
    return img


def sign(go: bool) -> np.ndarray:
    """An outdoor way (a road, a path, a shore): a wooden post. GO: its arrow board raised level and pointing on, pale and freshly painted. STOP: the board hanging down
    askew from one nail with a dark X daubed on it. 48 x 96 px for 1.2 x 2.4 m."""
    img = blank(W, H)
    y, x = np.mgrid[0:H, 0:W]
    d = dither(W, H)
    post = (x >= 21) & (x < 27) & (y >= 14)
    put(img, post, hexc("#7a5230"), 0.8 + 0.25 * (x < 23) + 0.08 * (d > 0.6))
    put(img, (x >= 18) & (x < 30) & (y >= H - 4), hexc("#5a3a20"))
    if go:
        board = (y >= 16) & (y < 30) & (x >= 4) & (x < 38)
        tip = (x >= 38) & (x < 46) & (np.abs(y - 22.5) < (46 - x) * 0.9)
        put(img, board | tip, hexc("#f0e2b0"), 0.9 + 0.1 * (d > 0.5))
        put(img, (board | tip) & ((y == 16) | (y == 29)), hexc("#8a6a3a"))
        arrow = ((y >= 21) & (y < 24) & (x >= 9) & (x < 36)) | ((x >= 30) & (x < 38) & (np.abs(y - 22.5) < (38 - x) * 0.8))
        put(img, arrow, hexc("#2e9a50"))
    else:
        yy = y - (x - 6) * 0.55  # the board hangs from its nail by the post, sloping down to the left
        board = (yy >= 26) & (yy < 38) & (x >= 2) & (x < 26)
        put(img, board, hexc("#8a7a60"), 0.75 + 0.08 * (d > 0.6))
        put(img, board & ((np.abs((x - 14) - (yy - 32) * 2.0) < 1.6) | (np.abs((x - 14) + (yy - 32) * 2.0) < 1.6)), hexc("#401810"))
    return img


def main() -> int:
    for k in range(4):
        save(door(k), "door_%d" % k)
    save(spill(), "spill")
    save(bars(), "bars")
    save(lamp(True), "lamp_go")
    save(lamp(False), "lamp_stop")
    save(sign(True), "sign_go")
    save(sign(False), "sign_stop")
    save(wizard_happy(), "wizard_happy")
    save(wizard_sad(), "wizard_sad")
    return 0


if __name__ == "__main__":
    sys.exit(main())
