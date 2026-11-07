#!/usr/bin/env python3
"""Builds the Space rave (docs/briefs/BEDSIT_RAVES_BRIEF.md sections 3 and 4): its map content/story/maps/space_rave.json, its story file content/story/space_rave.json, its
theme file content/raves/space.json and the few placeholder sprites it needs (assets/story/mothership/textures/sr_*.png).

    python3 tools/story/build_space_rave.py            # art and data
    python3 tools/story/build_space_rave.py --sheet F  # also a contact sheet of the placeholder sprites

THE PLACE. The Mothership's ring: content/story/maps/doom_mothership.json (the traced MAP11: a ring corridor round a sunken chamber, ivory ribs, mint light, violet depth) is
the geography; this map is a hand-built, approximate version at rave scale (twelve ring pieces, apothem 9 to 17 m, round a 12-sided void 9 m deep, railings on the void edges), not
a conversion. The Mothership's own textures and stage sprites (assets/story/mothership) are reused wherever they fit; what does not exist is drawn here with the project's pixel kit
and called a PLACEHOLDER (sr_rail, sr_deck, sr_knob_*, sr_hatch, sr_racer).

  compass: north is -z. Ring piece k stands at angle 30*k degrees from SOUTH, turning through EAST (piece 3) to NORTH (piece 6); local frame (u outward, s along the ring).
  piece 0 (south)  the hub: the player arrives in an airlock behind it (apse `airlock`), looks north across the void, hub_view is the choice viewpoint
  piece 5          the bar (apse), piece 6 the stage (a dais of 0.9 m up two 0.3 m steps), piece 7 the cloakroom (apse), piece 8 the hangar (apse, the race entrance)
Everything is seen from the hub across the void: the DJ at the deck (waving), the cloakroom attendant, the bartender, the hangar door with a racer glimpsed, the way home at the hub.
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

TEX = os.path.join(ROOT, "assets", "story", "mothership", "textures")
MAP = os.path.join(ROOT, "content", "story", "maps", "space_rave.json")
STORY = os.path.join(ROOT, "content", "story", "space_rave.json")
THEME = os.path.join(ROOT, "content", "raves", "space.json")
TRACK = "origin_unknown_valley_of_the_shadows_chase_status_remix"

A_IN, A_OUT = 9.0, 17.0          # apothems of the ring (m)
C15 = math.cos(math.radians(15))
R_IN, R_OUT = A_IN / C15, A_OUT / C15
CEIL = 6.0
VOID_FLOOR = -9.0


def loc(phi: float, u: float, s: float = 0.0):
    """Local frame of ring piece at `phi` degrees (from south through east): u outward, s along the ring (towards increasing phi)."""
    a = math.radians(phi)
    return [round(u * math.sin(a) + s * math.cos(a), 3), round(u * math.cos(a) - s * math.sin(a), 3)]


def pol(r: float, phi: float):
    a = math.radians(phi)
    return [round(r * math.sin(a), 3), round(r * math.cos(a), 3)]


def yaw_out(phi: float) -> float:
    """The yaw of looking outward (away from the middle) at piece `phi`: the way e_r points; yaw 0 looks -z, 90 looks -x."""
    y = (phi + 180) % 360
    return round(y - 360 if y > 180 else y, 3)


def yaw_in(phi: float) -> float:
    return round(phi if phi <= 180 else phi - 360, 3)


# ---------------------------------------------------------------------------------------------------------------------------------------- placeholder art
def build_art() -> list:
    from art.bedsit_draw import Cv, ramp, fnoise
    os.makedirs(TEX, exist_ok=True)
    out = {}

    # sr_rail: the railing tile (alpha): posts and two glowing rails, 32 x 32, repeats along the void edge. PLACEHOLDER.
    c = Cv(32, 32)
    c.flat(c.rect(0, 0, 3, 32), "#9fb4c4", edge=True, edge_col="#31485a")
    c.flat(c.rect(14, 0, 18, 32), "#9fb4c4", edge=True, edge_col="#31485a")
    c.flat(c.rect(0, 3, 32, 6), "#7cf0d0", edge=True, edge_col="#1b8f86")
    c.flat(c.rect(0, 14, 32, 17), "#7cf0d0", edge=True, edge_col="#1b8f86")
    c.flat(c.rect(0, 25, 32, 27), "#4aa89e")
    out["sr_rail"] = c

    # sr_deck: the DJ deck seen from the dance floor (a billboard), 96 x 56: a lit desk, two platters, a mixer with the stuck bass knob in the middle. PLACEHOLDER.
    c = Cv(96, 56)
    body = ramp("#1a1240", "#2c2368", "#43399a", "#6a5fd0")
    c.paint(c.rrect(0, 14, 96, 56, 3), body, c.lit((0, 14, 96, 56), 0.5, 0.4))
    c.flat(c.rect(1, 14, 95, 17), "#8cf6e0")          # the lip glow
    for cx in (22, 74):
        c.paint(c.ell(cx - 15, 18, cx + 15, 48), ramp("#101018", "#242434", "#3b3b55"), c.dome(cx, 33, 15, 15))
        c.flat(c.ell(cx - 3, 31, cx + 3, 37), "#ff4fc8")
    c.flat(c.rect(40, 20, 56, 52), "#14102e", edge=True, edge_col="#05030f")
    for i, col in enumerate(["#7cf0d0", "#7cf0d0", "#ffd23f", "#ff4fc8"]):
        c.flat(c.rect(42, 23 + i * 6, 54, 26 + i * 6), col)
    c.flat(c.ell(44, 44, 52, 52), "#a8a8c0", edge=True, edge_col="#3b3b55")   # the stuck knob (the close-up has its own)
    out["sr_deck"] = c

    # sr_knob: four frames of the bass knob, one row (stuck, straining, free, up), 40 x 40 each. PLACEHOLDER.
    sheet = Cv(160, 40)
    for i, (ang, glow, jitter) in enumerate([(-40, False, 0), (-34, False, 2), (10, True, 0), (62, True, 0)]):
        f = Cv(40, 40)
        f.paint(f.ell(2, 2, 38, 38), ramp("#3b2b50", "#5d4a7a", "#8f7cb0", "#c8bfe0"), f.dome(18, 18, 18, 18), edge=True)
        a = math.radians(ang - 90)
        cx, cy = 20 + jitter, 20
        f.flat(f.line((cx, cy), (cx + 14 * math.cos(a), cy + 14 * math.sin(a)), 4), "#ffffff" if glow else "#d8c8e8")
        for k in range(8):                     # the scale round the knob
            b = math.radians(-135 + k * 38.5 - 90)
            f.flat(f.ell(20 + 18 * math.cos(b) - 1, 20 + 18 * math.sin(b) - 1, 20 + 18 * math.cos(b) + 1, 20 + 18 * math.sin(b) + 1), "#7cf0d0" if (glow and k <= 2 + 2 * (i - 2)) else "#2b2040")
        if i == 1:
            f.flat(f.rect(0, 18, 3, 22), "#ffd23f")
            f.flat(f.rect(37, 18, 40, 22), "#ffd23f")   # the strain marks either side
        sheet.stamp(f, i * 40, 0)
    out["sr_knob"] = sheet

    # sr_hatch: the way home, an airlock door standing in the hub's airlock (a billboard), 48 x 84. PLACEHOLDER.
    c = Cv(48, 84)
    c.paint(c.rrect(0, 0, 48, 84, 4), ramp("#3a3a14", "#7a6a1c", "#d8b02a", "#f2d66a"), c.lit((0, 0, 48, 84), 0.5, 0.4))
    c.paint(c.rrect(5, 5, 43, 79, 3), ramp("#142840", "#1f4468", "#2f6a96", "#4a90c0"), c.lit((5, 5, 43, 79), 0.5, 0.4))
    c.flat(c.ell(15, 16, 33, 34), "#0a1a2c", edge=True, edge_col="#d8b02a")   # the porthole
    c.flat(c.ell(19, 20, 25, 26), "#7cf0d0")
    c.flat(c.ell(14, 44, 34, 64), "#c8d4dc", edge=True, edge_col="#3b4a56")   # the wheel
    c.flat(c.rect(23, 44, 25, 64), "#3b4a56")
    c.flat(c.rect(14, 53, 34, 55), "#3b4a56")
    c.flat(c.ell(21, 8, 27, 12), "#58ff9c")                                   # the lamp
    out["sr_hatch"] = c

    # sr_racer: the vehicle glimpsed in the hangar: a low hover racer side on, 112 x 44. PLACEHOLDER.
    c = Cv(112, 44)
    hull = ramp("#3a0a2a", "#7a1450", "#d8287a", "#ff7ab8")
    c.paint(c.poly([(4, 30), (14, 18), (46, 10), (84, 12), (108, 26), (108, 34), (4, 34)]), hull, c.lit((0, 8, 112, 36), 0.5, 0.5))
    c.paint(c.poly([(40, 12), (52, 4), (74, 6), (84, 13)]), ramp("#102838", "#1f5878", "#4aa8d0", "#a8e8f8"), c.lit((40, 4, 84, 13), 0.5, 0.5))
    c.flat(c.rect(2, 33, 110, 36), "#7cf0d0")                                  # the under glow
    for cx in (26, 88):
        c.paint(c.ell(cx - 9, 28, cx + 9, 44), ramp("#101018", "#242434", "#3b3b55"), c.dome(cx, 36, 9, 8))
    out["sr_racer"] = c

    names = []
    for n, c in out.items():
        c.save(os.path.join(TEX, n + ".png"))
        names.append((n, c))
    return names


def sheet(path: str, names: list) -> None:
    from PIL import Image
    w = sum(c.w * 3 + 8 for _, c in names)
    h = max(c.h * 3 for _, c in names) + 8
    im = Image.new("RGBA", (w, h), (30, 24, 50, 255))
    x = 4
    for _, c in names:
        big = c.image().resize((c.w * 3, c.h * 3), Image.NEAREST)
        im.paste(big, (x, 4), big)
        x += c.w * 3 + 8
    im.convert("RGB").save(path)


# ---------------------------------------------------------------------------------------------------------------------------------------- the map
def sec(sid, poly, floor, ceiling, floor_tex, ceil_tex, light, tint, flags=None, room="main", **kw):
    d = {"id": sid, "polygon": poly, "floor": floor, "ceiling": ceiling, "floor_tex": floor_tex, "ceil_tex": ceil_tex, "wall_tex": "wall_hull", "light": light, "tint": tint, "room": room,
         "flags": flags or []}
    d.update(kw)
    return d


QUIET = {"quiet": ["stand", "chat", "drink", "lean_wall", "point"], "dancing": ["dance", "dance", "dance", "chat", "drink"], "hype": ["dance", "dance", "dance", "wave", "point"],
         "euphoric": ["dance", "dance", "wave", "point", "toast"]}
STANDING = {"quiet": ["stand", "chat", "lean_wall"], "dancing": ["stand", "chat", "drink", "watch"], "hype": ["watch", "wave", "chat", "drink"], "euphoric": ["wave", "watch", "chat", "toast"]}
STAGEACT = {"quiet": ["stand", "mix", "point"], "dancing": ["mix", "dance", "point", "wave"], "hype": ["mix", "dance", "wave", "point"], "euphoric": ["mix", "dance", "wave", "point"]}

# (id, piece, depth D, half width at the ring w0, half width at the far end w1, floor_tex, tint, light, flags)
APSES = {
    "airlock": (0, 5.0, 2.5, 2.5, "floor_airlock", "#7fe8ff", 0.55, []),
    "bar": (150, 6.0, 3.6, 4.6, "floor_lounge", "#ff7ad8", 0.55, []),
    "cloak": (210, 6.0, 3.6, 4.6, "floor_lounge", "#9fb8ff", 0.55, []),
    "hangar": (240, 7.5, 3.8, 5.0, "floor_airlock", "#ffb066", 0.6, []),
}
STAGE_W0, STAGE_W1, STAGE_D = 4.4, 7.2, 11.0
STEP1_U, STEP2_U = 19.2, 21.4


def width_at(w0, w1, d, du):
    return w0 + (w1 - w0) * du / d


def build_map() -> dict:
    sectors, walls, things, lights, decals, waypoints, homes = [], [], [], [], [], [], []
    phis = [30 * k for k in range(12)]
    ring_tint = ["#7fe8ff", "#8fb0ff", "#a58cff", "#7fe8ff", "#8fb0ff", "#c08cff", "#b48cff", "#8fb0ff", "#7fe8ff", "#8fb0ff", "#a58cff", "#7fe8ff"]
    # the void
    sectors.append(sec("void", [pol(R_IN, 15 + 30 * j) for j in range(12)], VOID_FLOOR, 16.0, "floor_grate", "sky", 0.28, "#3a2a8a", room="main", void=True, activities=STANDING))
    for k, phi in enumerate(phis):
        dance = 2 <= k <= 10
        sectors.append(sec("r%d" % k, [pol(R_IN, phi - 15), pol(R_OUT, phi - 15), pol(R_OUT, phi + 15), pol(R_IN, phi + 15)], 0.0, CEIL, "floor_hex", "ceil_hull", 0.55 if k != 0 else 0.6, ring_tint[k],
                           ["dance_floor"] if dance else [], activities=QUIET if dance else STANDING, step_tex="trim", lip_tex="trim"))
        nxt = (k + 1) % 12
        walls.append({"from": pol(R_IN, phi + 15), "to": pol(R_OUT, phi + 15), "sector": "r%d" % k, "portal": "r%d" % nxt})
        walls.append({"from": pol(R_IN, phi - 15), "to": pol(R_IN, phi + 15), "sector": "r%d" % k, "portal": "void", "kind": "railing", "tex": "sr_rail", "height": 1.1})

    def apse(sid, phi, D, w0, w1, floor_tex, tint, light, flags, floor=0.0, u0=A_OUT, u1=None, ceiling=7.0, room="main", acts=STANDING, **kw):
        u1 = u1 if u1 is not None else A_OUT + D
        du0, du1 = u0 - A_OUT, u1 - A_OUT
        wa, wb = width_at(w0, w1, D, du0), width_at(w0, w1, D, du1)
        poly = [loc(phi, u0, -wa), loc(phi, u0, wa), loc(phi, u1, wb), loc(phi, u1, -wb)]
        sectors.append(sec(sid, poly, floor, ceiling, floor_tex, "ceil_hull", light, tint, flags, room, activities=acts, **kw))
        return poly

    ring_of = {150: 5, 210: 7, 240: 8, 0: 0}
    for sid, (phi, D, w0, w1, ftex, tint, light, flags) in APSES.items():
        apse(sid, phi, D, w0, w1, ftex, tint, light, flags)
        walls.append({"from": loc(phi, A_OUT, -w0), "to": loc(phi, A_OUT, w0), "sector": "r%d" % ring_of[phi], "portal": sid})
    # the stage: two steps and a dais on piece 6 (north)
    apse("ap6_a", 180, STAGE_D, STAGE_W0, STAGE_W1, "floor_bridge", "#b890ff", 0.55, [], floor=0.3, u0=A_OUT, u1=STEP1_U, ceiling=7.5, acts=STANDING, step_tex="trim")
    apse("ap6_b", 180, STAGE_D, STAGE_W0, STAGE_W1, "floor_bridge", "#b890ff", 0.58, [], floor=0.6, u0=STEP1_U, u1=STEP2_U, ceiling=7.5, acts=STANDING, step_tex="trim")
    apse("stage", 180, STAGE_D, STAGE_W0, STAGE_W1, "floor_dais", "#c8a0ff", 0.62, ["stage"], floor=0.9, u0=STEP2_U, u1=A_OUT + STAGE_D, ceiling=8.5, acts=STAGEACT, step_tex="trim")
    walls.append({"from": loc(180, A_OUT, -STAGE_W0), "to": loc(180, A_OUT, STAGE_W0), "sector": "r6", "portal": "ap6_a"})
    walls.append({"from": loc(180, STEP1_U, -width_at(STAGE_W0, STAGE_W1, STAGE_D, STEP1_U - A_OUT)), "to": loc(180, STEP1_U, width_at(STAGE_W0, STAGE_W1, STAGE_D, STEP1_U - A_OUT)),
                  "sector": "ap6_a", "portal": "ap6_b"})
    walls.append({"from": loc(180, STEP2_U, -width_at(STAGE_W0, STAGE_W1, STAGE_D, STEP2_U - A_OUT)), "to": loc(180, STEP2_U, width_at(STAGE_W0, STAGE_W1, STAGE_D, STEP2_U - A_OUT)),
                  "sector": "ap6_b", "portal": "stage"})

    # ---- waypoints
    def wp(wid, at, yaw, sector, **kw):
        d = {"id": wid, "at": at, "yaw": yaw, "sector": sector}
        d.update(kw)
        waypoints.append(d)

    wp("space_arrive", loc(0, 20.4), yaw_in(0), "airlock")
    wp("hub_view", loc(0, 14.2), yaw_in(0), "r0", choice_view=True)
    for k, phi in enumerate(phis):
        wp("rv%d" % k, loc(phi, 13.3), yaw_in(phi), "r%d" % k)
    wp("stage_foot", loc(180, 15.2), yaw_out(180), "r6")
    wp("stage_steps", loc(180, 20.3), yaw_out(180), "ap6_b")
    wp("deck_view", loc(180, 22.6), yaw_out(180), "stage")
    wp("cloak_door", loc(210, 15.2), yaw_out(210), "r7")
    wp("cloak_view", loc(210, 20.0), yaw_out(210), "cloak")
    wp("bar_door", loc(150, 15.2), yaw_out(150), "r5")
    wp("bar_view", loc(150, 20.0), yaw_out(150), "bar")
    wp("hangar_door", loc(240, 15.2), yaw_out(240), "r8")
    wp("hangar_view", loc(240, 21.0), yaw_out(240), "hangar")
    wp("home_door", loc(0, 19.0), yaw_out(0), "airlock")

    # ---- the outer walls: windows, planets, LED bars, speaker stacks, as emissive decals
    def decal(did, sprite, phi, u, s, y, size, **kw):
        d = {"id": did, "kind": "decal", "sprite": sprite, "at": loc(phi, u, s), "y": y, "size": size, "yaw": yaw_in(phi), "emissive": True}
        d.update(kw)
        decals.append(d)

    for k in (1, 2, 3, 4, 9, 10, 11, 0):
        phi = 30 * k
        sprite = "wall_planet" if k in (2, 3, 10) else "wall_window"
        if k == 0:  # the hub's own wall beside the airlock opening
            for s in (-3.9, 3.9):
                decal("win_0_%s" % ("l" if s < 0 else "r"), "wall_window", phi, A_OUT - 0.015, s, 1.0, 2.2)
            continue
        decal("win_%d_a" % k, sprite, phi, A_OUT - 0.015, -2.0, 1.1, 2.6)
        decal("win_%d_b" % k, "wall_window", phi, A_OUT - 0.015, 2.2, 1.1, 2.6)
        decal("led_%d" % k, "wall_led", phi, A_OUT - 0.015, 0.0, 4.1, 0.6)
    # stage walls: speakers either side of the dais, an arch behind the DJ
    far = A_OUT + STAGE_D - 0.015
    decal("stage_arch", "wall_arch", 180, far, 0.0, 0.9, 4.6)
    decal("stage_spk_l", "wall_speaker", 180, far, -5.2, 0.9, 3.4)
    decal("stage_spk_r", "wall_speaker", 180, far, 5.2, 0.9, 3.4)
    # the hangar door: a big warm door at the end wall, a racer standing in front of it; the cloakroom hatches; the bar's menu light
    hfar = A_OUT + APSES["hangar"][1] - 0.015
    decal("hangar_door", "wall_door", 240, hfar, 0.0, 0.0, 3.4)
    decal("hangar_warn", "wall_hatch", 240, hfar, -3.7, 0.0, 2.4)
    decal("hangar_glow", "wall_arch", 240, hfar, 3.7, 0.0, 2.4)
    cfar = A_OUT + APSES["cloak"][1] - 0.015
    for i, s in enumerate((-2.6, 0.0, 2.6)):
        decal("coat_hatch_%d" % i, "wall_hatch", 210, cfar, s, 0.0, 2.0)
    bfar = A_OUT + APSES["bar"][1] - 0.015
    decal("bar_screen", "wall_led", 150, bfar, 0.0, 2.2, 0.9)
    decal("bar_window", "wall_window", 150, bfar, -3.0, 1.0, 2.2)
    decal("bar_window_b", "wall_planet", 150, bfar, 3.0, 1.0, 2.2)
    afar = A_OUT + APSES["airlock"][1] - 0.015
    decal("airlock_window", "wall_window", 0, afar, 0.0, 1.6, 1.0)

    # ---- things: the deck and its knob, luminous equipment, props at the stations, the home hatch, the racer
    def bb(tid, sprite, phi, u, s, size, y=None, **kw):
        d = {"id": tid, "kind": "billboard", "sprite": sprite, "at": loc(phi, u, s), "size": size, "anim": kw.pop("anim", "none")}
        if y is not None:
            d["y"] = y
        d.update(kw)
        things.append(d)

    bb("deck", "sr_deck", 180, 25.2, 0.0, 1.05, y=0.525)                       # the DJ deck (placeholder art); its knob is the thing `bass_knob` at the deck's middle
    bb("bass_knob", "sr_knob_0", 180, 25.12, 0.0, 0.2, y=0.84, anim="none")    # (a thing of its own so the host can swap its frame; the frames are sr_knob_0..3, split from the sheet)
    bb("stage_ball", "disco_ball", 180, 24.0, 0.0, 1.4, y=5.6, anim="rotate")
    for i, s in enumerate((-4.2, 4.2)):
        bb("woofer_%d" % i, "woofer", 180, 23.0, s, 1.7, y=0.85, anim="pump")
    # the stage lights: a light group of set pieces, off until the bass is back (the host switches them with piece_on)
    bb("stage_beams_l", "pylon_beams", 180, 25.8, -4.4, 4.2, y=3.0, piece="pylon_beams")
    bb("stage_ring", "ring_lights", 180, 22.6, 0.0, 2.6, y=0.9, piece="ring_lights")
    bb("stage_dome", "hologram_dome", 180, 26.4, 0.0, 3.4, y=2.6, piece="hologram_dome")
    for i, (phi, u, s) in enumerate([(180, 24.4, -2.0), (180, 24.4, 2.0), (150, 21.0, 0.0), (210, 21.0, 0.0), (240, 21.0, 2.0), (0, 18.5, -1.4)]):
        bb("fixture_%d" % i, "fixture", phi, u, s, 0.9, y=5.0, anim="none")
    bb("glow_stage", "glow", 180, 25.5, 0.0, 3.0, y=1.4, anim="pulse", blend="add")
    bb("glow_bar", "glow", 150, 22.5, 0.0, 2.2, y=1.4, anim="pulse", blend="add")
    bb("glow_hangar", "glow", 240, 23.6, 0.0, 3.0, y=1.4, anim="pulse", blend="add")
    bb("bar_counter", "thing_bar", 150, 20.6, 0.0, 1.3, y=0.65)
    for i, s_ in enumerate((-3.0, -1.0, 1.0, 3.0)):  # the bar's static set (contract 10): the shelf, four bays, glasses lit by piece_on later
        bb("bar_shelf_%d" % (i + 1), "thing_cabinet", 150, 22.9, s_, 1.8, y=0.9)
    bb("cloak_counter", "thing_bar", 210, 19.4, 0.0, 1.2, y=0.6)   # the cloakroom's counter (contract 10) and its coat rail
    bb("cloak_rail", "thing_suit", 210, 21.6, 0.0, 1.8, y=0.9)
    bb("coat_cabinet", "thing_cabinet", 210, 22.2, -3.0, 1.8, y=0.9)
    bb("hangar_racer", "sr_racer", 240, 23.8, 0.0, 1.5, y=0.75)
    bb("hangar_console", "thing_console", 240, 21.6, -3.2, 1.3, y=0.65)
    bb("home_hatch", "sr_hatch", 0, 19.9, 0.0, 2.3, y=1.15)
    bb("plant_a", "thing_plant", 0, 12.0, -3.2, 1.3, y=0.65)
    bb("plant_b", "thing_plant", 90, 15.0, 0.0, 1.3, y=0.65)
    bb("plant_c", "thing_plant", 270, 15.0, 0.0, 1.3, y=0.65)
    for k in (1, 3, 4, 9, 11):
        phi = 30 * k
        bb("ring_lamp_%d" % k, "glow", phi, 16.2, 0.0, 1.6, y=2.8, anim="pulse", blend="add")
    # ring lights (baked into the surfaces): cool light across the void, a warm key on each destination
    def light(lid, at, y, radius, color, strength, **kw):
        d = {"id": lid, "kind": "light", "at": at, "y": y, "radius": radius, "color": color, "strength": strength}
        d.update(kw)
        lights.append(d)
    light("lt_void", [0.0, 0.0], 5.4, 14.0, "#6a4cff", 1.0)
    light("lt_hub", loc(0, 14.0), 3.6, 8.0, "#7fe8ff", 1.1)
    light("lt_airlock", loc(0, 20.0), 3.0, 6.0, "#fff2c8", 1.0)
    light("lt_stage_a", loc(180, 24.0, -3.0), 5.0, 9.0, "#ff4fc8", 1.2)
    light("lt_stage_b", loc(180, 24.0, 3.0), 5.0, 9.0, "#7fe8ff", 1.2)
    light("lt_bar", loc(150, 21.0), 3.4, 7.0, "#ff7ad8", 1.2)
    light("lt_cloak", loc(210, 21.0), 3.4, 7.0, "#b8c8ff", 1.1)
    light("lt_hangar", loc(240, 22.0), 3.6, 8.0, "#ffb066", 1.3)
    light("lt_planet_e", loc(90, 15.5), 3.0, 9.0, "#6fe4f4", 1.0)
    light("lt_planet_w", loc(270, 15.5), 3.0, 9.0, "#8fa8ff", 1.0)

    # ---- the people: aliens of the Mothership's rigs (the crowd), and the four guides
    actors = []
    kinds = [("grey", "a"), ("antenna", "a"), ("blob", "b"), ("insect", "a"), ("cyclops", "b"), ("tentacle", "b"), ("grey", "b"), ("antenna", "b"), ("blob", "a"), ("insect", "b"), ("cyclops", "a")]
    n = 0
    for k in range(2, 11):
        for (u, s) in ((11.0, -1.4), (13.6, 1.2), (15.6, -0.6)):
            if (k + int(u)) % 3 == 0 and k not in (6,):
                continue
            arch, var = kinds[n % len(kinds)]
            aid = "a%02d" % n
            n += 1
            actors.append({"id": aid, "archetype": arch, "variant": var, "group": "core", "thresh": (n * 7) % 13 - 6})
            homes.append({"actor": aid, "sector": "r%d" % k, "at": loc(30 * k, u, s)})
    guides = [("dj", "tentacle", "a", "stage", loc(180, 26.2, 0.9)), ("attendant", "cyclops", "a", "cloak", loc(210, 20.9, 0.0)), ("bartender", "blob", "a", "bar", loc(150, 22.4, 0.0)),
              ("pilot", "insect", "b", "hangar", loc(240, 20.4, 2.2))]
    for gid, arch, var, sector, at in guides:
        actors.append({"id": gid, "archetype": arch, "variant": var, "group": "core", "role": "front", "thresh": -20, "glow": gid == "dj"})
        homes.append({"actor": gid, "sector": sector, "at": at})
    # a few at the bar, a coat queue, aliens on the dais
    extra = [("q1", "grey", "a", "cloak", loc(210, 18.4, -1.3)), ("q2", "blob", "b", "cloak", loc(210, 18.9, -2.0)), ("q3", "antenna", "a", "cloak", loc(210, 18.2, 1.5)),
             ("b1", "insect", "a", "bar", loc(150, 19.2, -1.8)), ("b2", "cyclops", "b", "bar", loc(150, 18.8, 1.9)), ("s1", "grey", "b", "ap6_a", loc(180, 18.0, -3.0)),
             ("s2", "tentacle", "b", "stage", loc(180, 24.0, -4.6)), ("s3", "blob", "a", "stage", loc(180, 24.0, 4.8))]
    for aid, arch, var, sector, at in extra:
        actors.append({"id": aid, "archetype": arch, "variant": var, "group": "core", "thresh": (len(aid) * 5) % 11 - 5})
        homes.append({"actor": aid, "sector": sector, "at": at})

    m = {
        "units_per_m": 1, "eye_height": 1.6, "art": "mothership", "start": "space_arrive", "max_step": 0.5, "void_drop": 3.0,
        "visibility": {"mode": "clip", "depth": 48, "far": 0},
        "geography": {"source": "content/story/maps/doom_mothership.json", "note": "the Mothership's ring (MAP11), approximate: twelve ring pieces round a void"},
        "textures": {n: "textures/%s.png" % n for n in ["floor_hex", "floor_grate", "floor_airlock", "floor_bridge", "floor_dais", "floor_lounge", "ceil_hull", "wall_hull", "trim", "wall_planet", "wall_window",
                                                         "wall_arch", "wall_door", "wall_hatch", "wall_led", "wall_speaker", "thing_bar", "thing_cabinet", "thing_suit", "thing_console", "thing_plant",
                                                         "thing_planet", "sr_rail", "sr_deck", "sr_racer", "sr_hatch", "sr_knob_0", "sr_knob_1", "sr_knob_2", "sr_knob_3"]},
        "sky": {"tex": "textures/sky_space.png", "mode": "cylinder"},
        "fog": {"color": "#0a0620", "density": 0.012},
        "sectors": sectors, "walls": walls, "homes": homes, "spots": {}, "silhouettes": [], "occluders": [],
        "waypoints": waypoints,
    }
    m["things"] = things + lights + decals
    return m, actors


def build_story(actors: list) -> dict:
    base = json.loads(open(os.path.join(ROOT, "content", "story", "mothership.json"), encoding="utf-8").read())
    ids = [a["id"] for a in actors]
    d = {k: base[k] for k in ["palettes", "energy", "initial_energy", "sequence_bars"]}
    d.update({"id": "space_rave", "title": "The Space Rave", "chapter": 9, "art": "mothership", "music_pack": base["music_pack"], "music_packs": base["music_packs"],
              "description": "A rave on the Mothership's ring (docs/briefs/BEDSIT_RAVES_BRIEF.md section 3): a path's world, not a Story Campaign chapter.",
              "duration_bars": 8, "intro": "",
              "acts": [{"id": "I", "title": "The Space Rave", "start_bar": 1}],
              "blocks": [{"id": "the_ring", "title": "The Ring", "act": "Act I", "start_bar": 1, "bars": 8,
                          "events": [{"at_bar": 1, "action": "lights_cool"}, {"at_bar": 1, "action": "player_role", "role": "dancer"}, {"at_bar": 1, "action": "piece_on", "piece": "planet_window_glow"}]}],
              "groups": {"circle": ids[:], "all": ids[:]}, "actors": actors, "silhouettes": []})
    d["groups"]["early"] = []
    d["endings"] = {k: {kk: vv for kk, vv in v.items() if kk != "journey"} for k, v in base["endings"].items()}  # (the ring has no helm: no ending journeys)
    d["ending_order"] = base["ending_order"]
    return d


def theme_json() -> dict:
    """content/raves/space.json: contract 2's shape (src/contracts/fixtures/theme_space.json) for the real map, with the routes of contract 3 and the activity ids."""
    return {
        "id": "space", "scene_id": "space_rave", "geography": "mothership", "map": "space_rave", "track": TRACK, "arrival": "space_arrive",
        "props": [
            {"id": "deck", "role": "stage_deck", "sprite": "sr_deck", "spot": "deck_view"},
            {"id": "bass_knob", "role": "bass_knob", "sprite": "sr_knob_0", "spot": "deck_view"},
            {"id": "coat_hatch", "role": "cloakroom", "sprite": "wall_hatch", "spot": "cloak_view"},
            {"id": "bar_counter", "role": "bar", "sprite": "thing_bar", "spot": "bar_view"},
            {"id": "hangar_door", "role": "race_entrance", "sprite": "wall_door", "spot": "hangar_view"},
            {"id": "home_hatch", "role": "home_threshold", "sprite": "sr_hatch", "spot": "home_door"},
            {"id": "ring_lamps", "role": "decor", "sprite": "glow", "at": [0.0, 0.0]},
        ],
        "customers": [{"id": "aliens_floor", "sprite_set": "mothership/aliens", "count": 27, "spot": "rv6"}, {"id": "aliens_queue", "sprite_set": "mothership/aliens", "count": 3, "spot": "cloak_view"}],
        "guides": [
            {"id": "dj", "sprite": "mothership/tentacle_a", "spot": "deck_view", "for": "stage"},
            {"id": "attendant", "sprite": "mothership/cyclops_a", "spot": "cloak_view", "for": "cloakroom"},
            {"id": "bartender", "sprite": "mothership/blob_a", "spot": "bar_view", "for": "bar"},
            {"id": "pilot", "sprite": "mothership/insect_b", "spot": "hangar_view", "for": "race"},
            {"id": "home_hatch", "sprite": "sr_hatch", "spot": "home_door", "for": "home"},
        ],
        "ingredients": [{"id": "stardust", "icon": "space/ing_stardust", "color": "#d8e8ff"}, {"id": "comet_ice", "icon": "space/ing_ice", "color": "#7fe3ff"},
                        {"id": "plasma", "icon": "space/ing_plasma", "color": "#ff5fd2"}, {"id": "moon_syrup", "icon": "space/ing_syrup", "color": "#ffd25f"}],
        "cloakroom_symbols": [{"id": "ringed_planet", "icon": "space/sym_planet"}, {"id": "rocket", "icon": "space/sym_rocket"}, {"id": "crescent", "icon": "space/sym_moon"}, {"id": "ufo", "icon": "space/sym_ufo"}],
        "stations": {"stage": {"waypoint": "deck_view", "route": "space.to_stage"}, "cloakroom": {"waypoint": "cloak_view", "route": "space.to_cloak"}, "bar": {"waypoint": "bar_view", "route": "space.to_bar"}},
        "race": {"entrance": "hangar_view", "course": "race_street_space", "activity": "race"},
        "home": {"threshold": "home_door", "route": "home"},
        "activities": {"stage": "bass_knob", "cloakroom": "cloakroom", "bar": "bar", "race": "race"},
        "routes": {
            "space.to_stage": {"id": "space.to_stage", "map": "space_rave", "from": "hub_view", "legs": [
                {"to": "rv4", "bars": 4, "hold_bars": 1, "style": "walk", "via": ["rv1", "rv2", "rv3"]},
                {"to": "stage_foot", "bars": 2, "hold_bars": 1, "style": "walk", "look": "deck", "via": ["rv5"]},
                {"to": "stage_steps", "bars": 2, "hold_bars": 1, "style": "walk", "look": "deck"},
                {"to": "deck_view", "bars": 2, "hold_bars": 4, "style": "walk", "look": "deck"}],
                "arrive": {"waypoint": "deck_view", "choice_view": True, "hold": "window"}, "eye_m": 1.6},
            "space.to_cloak": {"id": "space.to_cloak", "map": "space_rave", "from": "hub_view", "legs": [
                {"to": "rv9", "bars": 4, "hold_bars": 1, "style": "walk", "via": ["rv11", "rv10"]},
                {"to": "cloak_door", "bars": 2, "hold_bars": 1, "style": "walk", "via": ["rv8"]},
                {"to": "cloak_view", "bars": 2, "hold_bars": 4, "style": "walk", "look": "attendant"}],
                "arrive": {"waypoint": "cloak_view", "choice_view": True, "hold": "window"}, "eye_m": 1.6},
            "space.to_bar": {"id": "space.to_bar", "map": "space_rave", "from": "hub_view", "legs": [
                {"to": "rv3", "bars": 4, "hold_bars": 1, "style": "walk", "via": ["rv1", "rv2"]},
                {"to": "bar_door", "bars": 2, "hold_bars": 1, "style": "walk", "via": ["rv4"]},
                {"to": "bar_view", "bars": 2, "hold_bars": 4, "style": "walk", "look": "bartender"}],
                "arrive": {"waypoint": "bar_view", "choice_view": True, "hold": "window"}, "eye_m": 1.6},
        },
        "hub": {"viewpoint": "hub_view", "choice_view": True, "hold_bars": 8,
                "choices": {"stage": {"actor": "dj", "node": "space_stage"}, "cloakroom": {"actor": "attendant", "node": "space_cloakroom"},
                            "bar": {"actor": "bartender", "node": "space_bar"}, "race": {"actor": "pilot", "node": "space_race"}, "home": {"thing": "home_hatch", "node": "bedsit"}}},
    }


def write(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=1)
        fh.write("\n")


def split_knob_sheet() -> None:
    """The knob's four frames as four sprites (sr_knob_0..3) next to the sheet (sr_knob.png: one row), so a thing or the close-up can show a frame by name."""
    from PIL import Image
    im = Image.open(os.path.join(TEX, "sr_knob.png")).convert("RGBA")
    for i in range(4):
        im.crop((i * 40, 0, i * 40 + 40, 40)).save(os.path.join(TEX, "sr_knob_%d.png" % i))


def main(argv: list) -> int:
    names = build_art()
    split_knob_sheet()
    m, actors = build_map()
    write(MAP, m)
    write(STORY, build_story(actors))
    write(THEME, theme_json())
    if "--sheet" in argv:
        sheet(argv[argv.index("--sheet") + 1], names)
    print("wrote %s (%d sectors, %d things, %d waypoints), %s, %s and %d placeholder sprites" % (MAP, len(m["sectors"]), len(m["things"]), len(m["waypoints"]), STORY, THEME, len(names)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
