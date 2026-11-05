#!/usr/bin/env python3
"""Draws the day room's card table (docs/BLACKJACK_INTEGRATION.md, the table in the room): the table, its hanging lamp, the empty chair and the three players of the
close-up (the older woman with white hair, round glasses and a yellow cardigan; the dealer in his green visor, white shirt and red braces; the woman with the wild dark
purple hair in a pink top), drawn the way the room's dancers are drawn: the people are posed and rasterised by the Story people's own pixel rig
(tools/story/art/people.py: a head about a seventh of the height, three shade steps with an ordered dither, a one-pixel darker edge of the local colour, never black),
and the furniture goes through the same finishing pass, at the dancers' pixel density (a sheet pixel is 1/66 m, the size a dancer's full-size frame has).

Outputs (assets/minigames/blackjack/):
* `world_table.png`: one still (the `idle` loop's first frame with the lamp's glow): the map's texture, what any view without the run's hook shows (the Story Campaign).
* `world_table_sheet.png` + `world_table_sheet.json`: every frame of the loops below at the full size and at half size (a far view), and the glow layer (the bulb and the
  lamp's cone: drawn unlit over the lit frame). The run plays them by song time and the table's hotspot state (src/run/run_card_table.gd).

Loops (two frames a beat, so every pose lands on a half beat): `idle` (they play among themselves), `invite` (the table is free: they look at you, the older woman waves,
the dealer riffles the deck and beckons, the woman in pink points at the empty chair and beckons), `pleased` (you touched it: arms up, grins, beckoning harder; the chair is
pulled further out), `welcome` (you sat: the dealer shows you the chair, the older woman claps, the woman in pink cheers) and `refuse` (waved off: the dealer shakes his head
and waves you away, the others shrug, then they go back to inviting). Deterministic: the same files on every run.

    python3 tools/minigames/make_world_table.py
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/story/art"))
import people as P  # noqa: E402  the Story people's pixel rig (read only)
import wardrobe as WR  # noqa: E402

OUT = ROOT / "assets/minigames/blackjack"
PPM = P.H0 / 1.7  # sheet pixels per metre: a dancer's full-size frame (112 px for a 1.7 m adult)
W_M, H_M = 3.2, 2.8  # the billboard in metres (the map's occluder has this size)
FPB = 2  # frames per beat

LOOPS = {"idle": 4, "invite": 4, "pleased": 2, "welcome": 2, "refuse": 4}  # beats per loop

# ---- the three players ---------------------------------------------------------------------------------------------------------------------------------
# Colours follow the close-up's people (src/minigames/blackjack/blackjack_people.gd) so the room's version and the seated version are the same three.
FURN = ("#3c7c74", "#24504c")  # the day room's teal chairs: their own seats and the empty one match


def _spec(who: str) -> dict:
    r = random.Random({"gran": 11, "dealer": 22, "wild": 33}[who])
    if who == "gran":
        s = {"height": 0.86, "width": 1.04, "curve": 0.85, "hair": {"style": "perm"}, "top": {"kind": "shirt", "pattern": "plain", "neck": "collar"},
             "outer": {"kind": "cardigan"}, "bottom": {"kind": "skirt", "len": 0.95}, "shoes": {"kind": "slippers"}, "hat": None, "acc": ["necklace"],
             "face": {"eyes": "open", "glasses": "round"},
             "colours": {"skin": "#f2cdb2", "hair": "#eeeae6", "hair2": "#ffffff", "top": "#f2e6c8", "top2": "#d8c8a0", "top3": "#f8f0de",
                         "outer": "#e0aa36", "outer2": "#b07c1c", "bottom": "#6a5a7a", "shoes": "#a05a6a", "acc2": "#eae4f2", "glass": "#d6eaf2"}}
    elif who == "dealer":
        s = {"height": 0.98, "width": 1.1, "curve": 0.1, "hair": {"style": "short"}, "top": {"kind": "shirt", "pattern": "plain", "neck": "collar"},
             "outer": None, "bottom": {"kind": "trousers"}, "shoes": {"kind": "boots"}, "hat": {"kind": "visor"}, "acc": ["braces"],
             "face": {"eyes": "open", "beard": "moustache"},
             "colours": {"skin": "#ecbb96", "hair": "#4a3020", "hair2": "#6a4a30", "top": "#e8ecf2", "top2": "#c0c8d6", "top3": "#ffffff", "bottom": "#2c2c3c",
                         "shoes": "#2a2020", "hat": "#3aa862", "hat2": "#86e8a2", "acc": "#cc2a3c", "acc2": "#e8c860"}}
    else:
        s = {"height": 0.92, "width": 0.96, "curve": 0.85, "hair": {"style": "wild"}, "top": {"kind": "tee", "pattern": "plain", "neck": "scoop"},
             "outer": None, "bottom": {"kind": "jeans"}, "shoes": {"kind": "trainers"}, "hat": None, "acc": ["bracelet", "hoops"],
             "face": {"eyes": "open"},
             "colours": {"skin": "#9c6642", "hair": "#3c2864", "hair2": "#6c4ca6", "top": "#de6e90", "top2": "#a8405e", "top3": "#f2a6bc", "bottom": "#2c3c6c",
                         "shoes": "#ece6dc", "acc": "#e6b84a", "acc2": "#e6b84a"}}
    s["colours"] = WR._base(r, s["colours"])
    s["colours"]["furn"], s["colours"]["furn2"] = FURN
    s["colours"]["prop"], s["colours"]["prop2"] = "#3a4a9a", "#f4eee0"  # the cards they hold: a blue back, a white face
    s["seed"] = {"gran": 1101, "dealer": 2202, "wild": 3303}[who]
    keep = dict(s["face"])
    WR._face_detail(s, "mental_hospital", "cards_" + who, "granny" if who == "gran" else "resident")
    s["face"].update(keep)
    if who == "gran":
        s["face"].update(age="old", lines=True, brow="thin", lips="thin")
    if who == "wild":
        s["colours"]["mouth"] = "#8a2a44"
    return s


class TablePainter(P.Painter):
    """The rig's painter with the three costume pieces the wardrobe does not carry: the dealer's green eyeshade (a band and a translucent brim, the hair showing over it),
    his red braces, the woman in pink's wild hair (a bigger mass of curls) and her gold hoops."""

    def hair_front(self, c, rx, ry, ang):
        if self.hair.get("style") == "wild":
            self.hair = dict(self.hair, style="afro")
            super().hair_front(self.F(c, ang, 0.0, -ry * 0.12), rx * 1.22, ry * 1.12, ang)
            self.hair = dict(self.hair, style="wild")
            return
        super().hair_front(c, rx, ry, ang)

    def hair_back(self):
        if self.hair.get("style") == "wild":
            return
        super().hair_back()

    def hat_draw(self, c, rx, ry, ang):
        if (self.hat or {}).get("kind") != "visor":
            return super().hat_draw(c, rx, ry, ang)
        cv, b = self.cv, self.b
        F = lambda x, y: self.F(c, ang, x, y)
        z = 2.5
        # the band round the forehead, then the eyeshade sticking out above the eyes, lit on top
        P.ellipse(cv, F(0, -ry * 0.62), rx * 1.08, ry * 0.6, ang, z,
                  lambda lx, ly, u, v: (np.where((v > 0.12) & (v < 0.5), P.M["hat"], 0).astype(np.uint8), -0.1))
        if b.fc != 2:
            P.ellipse(cv, F(0, -ry * 0.33), rx * 1.3, ry * 0.16, ang, z + 0.02,
                      lambda lx, ly, u, v: (np.where(v < -0.05, P.M["hat2"], P.M["hat"]).astype(np.uint8), 0.15))

    def accessories(self):
        super().accessories()
        b, S, cv = self.b, self.S, self.cv
        ts = b.t_shoulder
        if "braces" in self.acc and b.fc != 2:
            for sg in (-1, 1):
                x0 = sg * b.sw * 0.55
                P.seg(cv, b.T((x0, ts - 0.004 * S)), b.T((sg * b.waist_hw * 0.62, -0.03 * S)), "acc", P.MID, 1.15, 1.5)
        if "hoops" in self.acc and b.fc != 2 and self.lod < 4:
            hc, rx = b.head_c, b.head_w * 0.5
            for sg in (-1, 1):
                cv.dot(hc[0] + sg * (rx + 0.8), hc[1] + b.head_h * 0.18, "acc2", P.LIT, 2.7)
                cv.dot(hc[0] + sg * (rx + 0.8), hc[1] + b.head_h * 0.18 + 1.5, "acc2", P.MID, 2.7)


def render_person(spec: dict, pose: dict, face: str, lod: int, held: str = "", flip: bool = False):
    """One posed, seated person: (RGBA image, feet pivot (x, y), right hand (x, y), left hand (x, y)) in image pixels."""
    S = P.H0 / lod * float(spec.get("height", 1.0))
    w, h = int(S * 1.1) + 8, int(S * 1.45) + 8
    ox, oy = w / 2.0, h - 4.0
    cv = P.Canvas(w, h, ox, oy)
    b = P.Body(spec, pose, S, 0, "sit")
    TablePainter(cv, b, spec, lod, held, face, spec["seed"]).draw()
    idx = P.finish(cv)
    pal = np.array(P.palette_row(spec["colours"]), np.uint8)
    img = np.zeros((h, w, 4), np.uint8)
    on = idx > 0
    img[on] = pal[idx[on] & 127]
    img[on, 3] = 255
    hr, hl = b.arms["r"]["hand"], b.arms["l"]["hand"]
    hand_r, hand_l = (hr[0] + ox, hr[1] + oy), (hl[0] + ox, hl[1] + oy)
    if flip:
        img = img[:, ::-1].copy()
        hand_r, hand_l = (w - hand_l[0], hand_l[1]), (w - hand_r[0], hand_r[1])
        ox = w - ox
    return Image.fromarray(img, "RGBA"), (ox, oy), hand_r, hand_l


# ---- poses: the rig's angles (radians; arm 0 hangs, about 1.6 straight out to the side, 2.5 raised; elbow bends the forearm) ---------------------------------------

POSE_KEYS = ("arm_l", "arm_r", "elb_l", "elb_r", "lean", "head_tilt", "head_drop")


def pose(arm_l=0.3, arm_r=0.3, elb_l=0.9, elb_r=0.9, lean=0.0, tilt=0.0, drop=0.0) -> dict:
    return {"arm_l": arm_l, "arm_r": arm_r, "elb_l": elb_l, "elb_r": elb_r, "lean": lean, "head_tilt": tilt, "head_drop": drop,
            "leg_l": 0.7, "leg_r": 0.7, "squash": 0.0, "roll": 0.0, "crouch": 0.0, "lift_l": 0.0, "lift_r": 0.0}


# Per loop, per frame (FPB a beat): {who: (pose, face, held)}. The person's right arm is on screen left (they face us).
def frames_of(loop: str) -> list:
    n = LOOPS[loop] * FPB
    out = []
    for k in range(n):
        half = k % 2  # 0 on the beat, 1 on the off-beat
        beat = k // 2
        f = {}
        if loop == "idle":  # a hand in progress: they look at their cards, the dealer deals across the table
            f["gran"] = (pose(0.35, 0.5, 1.7, 1.9, tilt=0.03 * (1 - 2 * (beat % 2)), drop=6.0), "neutral", "tickets")
            f["wild"] = (pose(0.5, 0.35, 1.9, 1.7, tilt=-0.04 if beat % 2 else 0.0, drop=6.0), "neutral", "tickets")
            deal = (beat % 2 == 0) and half == 1
            f["dealer"] = (pose(0.35, 1.25 if deal else 0.55, 1.55, 0.4 if deal else 1.6, drop=4.0), "neutral", "tickets")
        elif loop == "invite":  # free seat: they look at you; she waves, he riffles then beckons, the woman in pink points at the chair and beckons
            wave = (2.45, 0.2) if half == 0 else (2.6, 1.0)
            f["gran"] = (pose(0.3, wave[0], 1.2, wave[1], lean=-0.03, tilt=-0.05), "happy", "")
            if beat < 2:  # the riffle: both hands at the chest, the deck squared then bridged
                f["dealer"] = (pose(0.55 if half else 0.42, 0.55 if half else 0.42, 1.95 if half else 2.25, 1.95 if half else 2.25, tilt=0.04 * (1 - 2 * beat)), "happy", "tickets")
            else:  # the beckon: the open hand toward the chair, then the forearm curling back
                f["dealer"] = (pose(0.3, 1.35, 1.0, 0.35 if half == 0 else 1.6, lean=0.03, tilt=0.06), "happy", "")
            if beat % 2 == 0:  # point down at the empty chair
                f["wild"] = (pose(1.0 if half == 0 else 1.15, 0.3, 0.1, 1.0, lean=0.05, tilt=0.06), "happy", "")
            else:  # come here: the forearm curls up
                f["wild"] = (pose(0.7, 0.3, 2.3 if half == 0 else 1.5, 1.0, lean=0.03, tilt=0.04), "happy", "")
        elif loop == "pleased":  # you touched the table: arms up and grins, beckoning harder
            up = half == 0
            f["gran"] = (pose(2.45 if up else 2.1, 2.55 if up else 2.2, 0.45 if up else 1.2, 0.45 if up else 1.2, tilt=-0.06), "cheer", "")
            f["dealer"] = (pose(0.4 if up else 0.4, 2.5 if up else 1.4, 1.0, 0.2 if up else 1.9, lean=0.04 * (1 - 2 * beat), tilt=-0.05), "cheer", "")
            f["wild"] = (pose(2.6 if up else 2.3, 2.4 if up else 2.1, 0.3 if up else 1.4, 0.3 if up else 1.4, tilt=0.05), "cheer", "")
        elif loop == "welcome":  # you sit down: he shows you the chair, she claps, the woman in pink cheers
            f["dealer"] = (pose(0.3, 1.2, 1.0, 0.3, lean=0.05, tilt=0.05), "happy", "")
            f["gran"] = (pose(0.62, 0.62, 1.15 if half else 1.5, 1.15 if half else 1.5), "happy", "")
            f["wild"] = (pose(2.5, 2.5 if half else 2.3, 0.4, 0.4 if half else 0.9, tilt=0.04), "cheer", "")
        else:  # refuse: he shakes his head and waves you away, the others shrug
            sh = 1 - 2 * half
            f["dealer"] = (pose(0.3, 1.0, 1.0, 2.0 if half else 1.2, lean=0.0, tilt=0.09 * sh), "sad", "")
            shrug = pose(0.4, 0.4, -1.6, -1.6, tilt=0.06 * sh) if beat % 2 == 0 else pose(0.25, 0.25, -1.3, -1.3, tilt=0.0)
            f["gran"] = (shrug, "sad", "")
            f["wild"] = (dict(shrug, head_tilt=-shrug["head_tilt"]), "sad", "")
        out.append(f)
    return out


# ---- the furniture: drawn through the rig's finishing pass (three shade steps, dither, edges of the local colour) with its own palette -------------------------

PROPS = {"furn": "#7a5232", "furn2": "#4c321e", "top": "#2c7a54", "outer": FURN[0], "outer2": FURN[1], "metal": "#3c7a5a", "extra": "#3e4648",
         "prop": "#3a4a9a", "prop2": "#f4eee0", "acc": "#2c9ea8", "acc2": "#e2b848", "hat": "#c83040", "lit": "#fff4c8", "glass": "#e8d8a8"}


def _props_palette() -> np.ndarray:
    return np.array(P.palette_row(WR._base(random.Random(5), dict(PROPS))), np.uint8)


class Plate:
    """A rig Canvas in billboard metres: x from the table's middle, y up from the floor (the occluder's feet line)."""

    def __init__(self, ppm: float):
        self.ppm = ppm
        self.w, self.h = int(round(W_M * ppm)), int(round(H_M * ppm))
        self.cv = P.Canvas(self.w, self.h, self.w / 2.0, self.h - 1.0)

    def p(self, x, y):
        return (x * self.ppm, -(y + BASE) * self.ppm)

    def poly(self, pts, z, mat, shade):
        P.poly_fill(self.cv, [self.p(x, y) for x, y in pts], z, mat, shade)

    def image(self) -> Image.Image:
        idx = P.finish(self.cv)
        pal = _props_palette()
        img = np.zeros((self.h, self.w, 4), np.uint8)
        on = idx > 0
        img[on] = pal[idx[on] & 127]
        img[on, 3] = 255
        return Image.fromarray(img, "RGBA")


BASE = 0.12  # the table's floor line stands this far up the picture: the empty chair, nearer to us than the table, stands lower (the map's occluder stands at the chair)
# the table: top at 0.7 m, its far edge seen 0.17 m higher than its near edge (the eye is above it), 2.5 m long
TOP_Y, FAR_DY, HALF = 0.7, 0.15, 1.25


def lamp_shade(ppm):
    """How much of the lamp's pool falls on a point of the table top (1 under the bulb): the shade of the felt and the rim."""
    def f(X, Y):
        x = X / ppm
        return np.clip(0.95 - 0.55 * np.abs(x) / HALF, 0.15, 0.95)
    return f


def table_plate(ppm: float, chair_out: float) -> Image.Image:
    """The table (top, apron, legs, the game on it) and the empty chair on our side, pulled out by `chair_out` metres and turned to us."""
    pl = Plate(ppm)
    cv = pl.cv
    sh = lamp_shade(ppm)
    # legs, then the top: the felt with a lit middle, the wooden rim, the apron
    for lx in (-HALF + 0.12, HALF - 0.12):
        pl.poly([(lx - 0.035, 0.06), (lx + 0.035, 0.06), (lx + 0.035, TOP_Y - 0.06), (lx - 0.035, TOP_Y - 0.06)], 0.0, "furn2", 0.3)
    for lx in (-HALF + 0.3, HALF - 0.3):  # the far legs, half hidden
        pl.poly([(lx - 0.03, 0.14), (lx + 0.03, 0.14), (lx + 0.03, TOP_Y), (lx - 0.03, TOP_Y)], -0.1, "furn2", 0.15)
    top = [(-HALF, TOP_Y), (HALF, TOP_Y), (HALF - 0.16, TOP_Y + FAR_DY), (-HALF + 0.16, TOP_Y + FAR_DY)]
    P.poly_fill(cv, [pl.p(x, y) for x, y in top], 0.5, "furn", lambda X, Y: sh(X, Y) * 0.9)
    felt = [(-HALF + 0.07, TOP_Y + 0.025), (HALF - 0.07, TOP_Y + 0.025), (HALF - 0.21, TOP_Y + FAR_DY - 0.025), (-HALF + 0.21, TOP_Y + FAR_DY - 0.025)]
    P.poly_fill(cv, [pl.p(x, y) for x, y in felt], 0.6, "top", lambda X, Y: sh(X, Y))
    P.poly_fill(cv, [pl.p(x, y) for x, y in [(-HALF, TOP_Y - 0.09), (HALF, TOP_Y - 0.09), (HALF, TOP_Y), (-HALF, TOP_Y)]], 0.7, "furn",
                lambda X, Y: sh(X, Y) * 0.62)
    # the game: the deck before the dealer, a card or two before each player, notes and coins
    def card(x, y, face=True, z=0.8):
        pl.poly([(x - 0.045, y), (x + 0.045, y), (x + 0.045, y + 0.05), (x - 0.045, y + 0.05)], z, "prop2" if face else "prop", 0.8)
        if face:
            P.seg(cv, pl.p(x - 0.01, y + 0.025), pl.p(x + 0.01, y + 0.025), "hat", P.MID, z + 0.01)
    card(0.22, TOP_Y + 0.09, False)
    card(0.24, TOP_Y + 0.1, False, 0.81)
    for x in (-0.86, -0.74, 0.74, 0.86, -0.1, 0.02):
        card(x, TOP_Y + 0.06 + 0.012 * (x > 0))
    for x, y in ((-0.42, TOP_Y + 0.05), (0.5, TOP_Y + 0.07)):
        pl.poly([(x - 0.07, y), (x + 0.07, y), (x + 0.07, y + 0.035), (x - 0.07, y + 0.035)], 0.82, "acc", 0.7)
    for x in (-0.3, -0.26, 0.4, 0.62):
        P.ellipse(cv, pl.p(x, TOP_Y + 0.04), 0.022 * ppm, 0.014 * ppm, 0.0, 0.83, lambda *a: (P.M["acc2"], 0.2))
    chair(pl, chair_out)
    return pl.image()


def chair(pl: "Plate", out: float) -> None:
    """The empty chair on our side: pulled out from the table by `out` metres (toward us and a little to the right), its seat facing us and catching the lamp, its
    back against the table: the place left for you."""
    cv = pl.cv
    cx, fy = 0.12 + out * 0.45, -BASE + 0.03 + (0.3 - out) * 0.25
    sy = fy + 0.46
    sk = 0.07  # the three-quarter turn: the far edge sits this far right of the near one
    for x0, y0, y1, z in ((cx - 0.2 + sk, fy + 0.07, sy + 0.08, 0.95), (cx + 0.2 + sk, fy + 0.07, sy + 0.08, 0.95), (cx - 0.21, fy, sy, 1.3), (cx + 0.21, fy, sy, 1.3)):
        pl.poly([(x0 - 0.02, y0), (x0 + 0.02, y0), (x0 + 0.02, y1), (x0 - 0.02, y1)], z, "outer2", 0.3)
    for x0 in (cx - 0.19 + sk, cx + 0.19 + sk):  # the back: two posts and two rails, the table showing through
        pl.poly([(x0 - 0.025, sy + 0.08), (x0 + 0.025, sy + 0.08), (x0 + 0.035, sy + 0.52), (x0 - 0.015, sy + 0.52)], 1.0, "outer", 0.55)
    for y0, y1, shade in ((sy + 0.4, sy + 0.52, 0.85), (sy + 0.24, sy + 0.29, 0.55)):
        pl.poly([(cx - 0.2 + sk, y0), (cx + 0.2 + sk, y0), (cx + 0.21 + sk, y1), (cx - 0.19 + sk, y1)], 1.01, "outer", shade)
    seat = [(cx - 0.23, sy), (cx + 0.23, sy), (cx + 0.23 + sk, sy + 0.09), (cx - 0.23 + sk, sy + 0.09)]
    P.poly_fill(cv, [pl.p(x, y) for x, y in seat], 1.2, "outer", 0.95)
    P.poly_fill(cv, [pl.p(x, y) for x, y in [(cx - 0.23, sy - 0.04), (cx + 0.23, sy - 0.04), (cx + 0.23, sy), (cx - 0.23, sy)]], 1.25, "outer2", 0.45)


def under_plate(ppm: float) -> Image.Image:
    """The shade under the table top, over the players' legs and the floor beneath: the table reads as a solid thing they sit at."""
    w, h = int(round(W_M * ppm)), int(round(H_M * ppm))
    ys, xs = np.mgrid[0:h, 0:w]
    X = (xs + 0.5 - w / 2.0) / ppm
    Y = (h - 1.0 - ys - 0.5) / ppm - BASE
    inside = (np.abs(X) < HALF - 0.05) & (Y < TOP_Y + 0.02) & (Y > 0.0)
    a = np.where(inside, 0.72 - 0.35 * (1.0 - Y / TOP_Y), 0.0)
    img = np.zeros((h, w, 4), np.uint8)
    img[..., 0], img[..., 1], img[..., 2] = 8, 10, 16
    img[..., 3] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


def shadow_plate(ppm: float) -> Image.Image:
    """The grounding shadow under the table and the chair (a dark translucent ellipse; the floor shows through)."""
    w, h = int(round(W_M * ppm)), int(round(H_M * ppm))
    ys, xs = np.mgrid[0:h, 0:w]
    u = (xs + 0.5 - w / 2.0) / (1.45 * ppm)
    v = (ys + 0.5 - (h - (BASE - 0.02) * ppm)) / (0.11 * ppm)
    d = u * u + v * v
    a = np.clip((1.0 - d) * 1.6, 0.0, 1.0) * 120
    b = P.BAYER4[ys % 4, xs % 4] * 60
    a = np.where(a + b > 60, np.minimum(a + 30, 150), 0).astype(np.uint8)
    img = np.zeros((h, w, 4), np.uint8)
    img[..., 0], img[..., 1], img[..., 2] = 6, 6, 14
    img[..., 3] = a
    return Image.fromarray(img, "RGBA")


def glow_plate(ppm: float) -> Image.Image:
    """Unlit over the lit frame: the lamp (cord, enamel shade, the hot bulb) and its cone of warm light, a dithered haze that fades toward the table."""
    w, h = int(round(W_M * ppm)), int(round(H_M * ppm))
    ys, xs = np.mgrid[0:h, 0:w]
    X = (xs + 0.5 - w / 2.0) / ppm
    Y = (h - 1.0 - ys - 0.5) / ppm - BASE
    img = np.zeros((h, w, 4), np.float32)
    bulb_y = 2.02
    # the cone: from the shade's rim (0.22 m wide) down to the table (2.2 m wide), fading downwards, dithered into three levels
    k = np.clip((bulb_y - Y) / (bulb_y - TOP_Y), 0.0, 1.0)
    half = 0.2 + k * 0.95
    inside = (np.abs(X) < half) & (Y < bulb_y) & (Y > TOP_Y + 0.02)
    a = np.where(inside, 0.2 * (1.0 - 0.75 * k) * (1.0 - 0.6 * (np.abs(X) / half) ** 2), 0.0)
    a = a + P.BAYER4[ys % 4, xs % 4] * 0.07
    a = np.where(a > 0.17, 0.22, np.where(a > 0.1, 0.13, np.where(a > 0.05, 0.06, 0.0)))
    a = np.where(inside, a, 0.0)
    img[..., 0], img[..., 1], img[..., 2], img[..., 3] = 255, 214, 130, a * 255
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA")
    # the lamp itself through the rig's finishing pass: a cord, a green enamel shade lit on top, the bulb (the palette's emissive `lit`)
    pl = Plate(ppm)
    cv = pl.cv
    P.poly_fill(cv, [pl.p(x, y) for x, y in [(-0.012, H_M), (0.012, H_M), (0.012, bulb_y + 0.2), (-0.012, bulb_y + 0.2)]], 0.0, "extra", 0.4)
    P.poly_fill(cv, [pl.p(x, y) for x, y in [(-0.07, bulb_y + 0.21), (0.07, bulb_y + 0.21), (0.25, bulb_y + 0.02), (-0.25, bulb_y + 0.02)]], 0.2, "metal",
                lambda X, Y: np.where(Y < -(bulb_y + 0.15) * ppm, 0.85, 0.45))
    P.ellipse(cv, pl.p(0.0, bulb_y + 0.01), 0.075 * ppm, 0.045 * ppm, 0.0, 0.3, lambda *a: (P.M["lit"], 0.6))
    out.alpha_composite(pl.image())
    return out


def _paste(base: Image.Image, im: Image.Image, x: int, y: int) -> None:
    """alpha_composite at (x, y), clipped to the base (a raised hand may reach past the top)."""
    x0, y0 = max(0, -x), max(0, -y)
    x1, y1 = min(im.width, base.width - x), min(im.height, base.height - y)
    if x1 > x0 and y1 > y0:
        base.alpha_composite(im.crop((x0, y0, x1, y1)), (x + x0, y + y0))


# ---- one frame -------------------------------------------------------------------------------------------------------------------------------------------

SEATS = {"gran": -0.92, "dealer": 0.0, "wild": 0.92}  # x of each player (m), all behind the table
SEAT_BACK = 0.24  # their feet stand this far up the picture (behind the table)
CHAIR_OUT = {"idle": 0.0, "invite": 0.12, "pleased": 0.3, "welcome": 0.3, "refuse": 0.0}


def frame(loop: str, k: int, lod: int, specs: dict) -> Image.Image:
    ppm = PPM / lod
    w, h = int(round(W_M * ppm)), int(round(H_M * ppm))
    img = shadow_plate(ppm)
    fr = frames_of(loop)[k]
    for who in ("gran", "dealer", "wild"):
        pz, face, held = fr[who]
        if loop == "pleased" and k == 0:  # the jump at the touch: they bounce up off their seats
            pz = dict(pz)
        pim, piv, _hr, _hl = render_person(specs[who], pz, face, lod, held)
        bounce = (0.04 if loop == "pleased" and k % 2 == 0 else 0.0) + (0.015 if loop == "invite" and k % 2 == 0 else 0.0)
        x = w / 2.0 + SEATS[who] * ppm - piv[0]
        y = (h - 1.0) - (BASE + SEAT_BACK + bounce) * ppm - piv[1]
        _paste(img, pim, int(round(x)), int(round(y)))
    img.alpha_composite(under_plate(ppm))
    img.alpha_composite(table_plate(ppm, CHAIR_OUT[loop] + (0.04 if loop in ("invite",) and k % 4 < 2 else 0.0)))
    return img


def main() -> None:
    specs = {w: _spec(w) for w in ("gran", "dealer", "wild")}
    frames: list = []  # (lod, loop, k, image)
    for lod in (1, 2):
        for loop in LOOPS:
            for k in range(LOOPS[loop] * FPB):
                frames.append((lod, loop, k, frame(loop, k, lod, specs)))
    glows = {lod: glow_plate(PPM / lod) for lod in (1, 2)}
    # the sheet: the full-size frames in rows of 8, then the half-size ones, then the two glow layers
    fw, fh = frames[0][3].size
    hw, hh = frames[-1][3].size
    cols = 8
    n1 = sum(1 for f in frames if f[0] == 1)
    rows1 = (n1 + cols - 1) // cols
    n2 = len(frames) - n1
    rows2 = (n2 + cols * 2 - 1) // (cols * 2)
    sheet = Image.new("RGBA", (fw * cols, fh * rows1 + hh * rows2 + fh), (0, 0, 0, 0))
    meta = {"metres": [W_M, H_M], "frames_per_beat": FPB, "lods": {}}
    for lod in (1, 2):
        ent = {"loops": {}, "glow": []}
        sub = [f for f in frames if f[0] == lod]
        for i, (_l, loop, k, im) in enumerate(sub):
            if lod == 1:
                x, y = (i % cols) * fw, (i // cols) * fh
            else:
                x, y = (i % (cols * 2)) * hw, rows1 * fh + (i // (cols * 2)) * hh
            sheet.alpha_composite(im, (x, y))
            ent["loops"].setdefault(loop, []).append([x, y, im.width, im.height])
        gx = 0 if lod == 1 else fw
        gy = rows1 * fh + rows2 * hh
        sheet.alpha_composite(glows[lod], (gx, gy))
        ent["glow"] = [gx, gy, glows[lod].width, glows[lod].height]
        meta["lods"][str(lod)] = ent
    meta["beats"] = dict(LOOPS)
    OUT.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT / "world_table_sheet.png", optimize=True)
    (OUT / "world_table_sheet.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    still = frames[0][3].copy()
    still.alpha_composite(glows[1])
    still.save(OUT / "world_table.png", optimize=True)
    print("wrote", (OUT / "world_table_sheet.png").relative_to(ROOT), sheet.size, len(frames), "frames;", (OUT / "world_table.png").relative_to(ROOT), still.size)


if __name__ == "__main__":
    main()
