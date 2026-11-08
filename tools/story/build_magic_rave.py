#!/usr/bin/env python3
"""Builds the Magic and unicorns rave (docs/briefs/BEDSIT_RAVES_BRIEF.md sections 3 and 4; theme id `magic`, facing SOUTH): its map content/story/maps/magic_rave.json, its story file
content/story/magic_rave.json, its theme file content/raves/magic.json, the activity layouts in content/bedsit/themes.json (cloakroom.magic.layout, bar.magic.layout) and the art folder
assets/story/rave_magic/ (textures, the activities' sheets, the clubgoers' rigs, the manifest).

    python3 tools/story/build_magic_rave.py

THE PLACE. The Chill-out lounge (content/story/maps/doom_lounge.json on feature/doom-layout-worlds: an octagonal conversation pit, concentric rings of stepped sofa and rug going down to a sunken
middle, curtained doorways round the edge, a street door ahead) is the geography; this map is a hand-built, approximate version at rave scale, not a conversion: an OCTAGON of eight pieces in
three tiers going down by 0.375 m (the pearl walkway, the moss ring with its toadstools, the velvet ring) to a sunken well that is the dance floor, curtained alcoves round the outer wall. Where
the Space rave is a ring round a drop that you walk round, this one is a bowl you cross: every route descends the steps, goes over the floor between the dancers and climbs out. Tiles borrowed from
the lounge (curtain, marble, wood, rug, potion shelf, lamp, plant) are recoloured violet and pearl; everything iridescent is drawn here and called a PLACEHOLDER.

  compass: north is -z. Piece k stands at 45 k degrees from SOUTH through EAST (0 south, 2 east, 4 north, 6 west).
  piece 0   the hub: the player arrives in the wardrobe alcove behind it (sector `home`, the way home is its door), hub_view looks north across the well
  piece 3   the bar (alcove, NE)   piece 4  the stage (a dais of 0.9 m up two 0.3 m steps, N)   piece 5  the cloakroom (alcove, NW) and, shallower, beside it, the carriage house (the race entrance)
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rave_builder import (ROOT, Frame, RaveMap, add_bar, add_cloak, add_crowd, add_home, add_race, add_stage, hub_bearings, leg, loc, pol, place_activity_sheets, route, story_json,  # noqa: E402
                          theme_json, write, write_activity_layouts, yaw_in, yaw_out, QUIET, STANDING, A_OUT)
import rave_art as ra  # noqa: E402
import rave_people  # noqa: E402
from art.bedsit_draw import Cv, ramp  # noqa: E402

MAP_ID = "magic_rave"
MAP = os.path.join(ROOT, "content", "story", "maps", "magic_rave.json")
STORY = os.path.join(ROOT, "content", "story", "magic_rave.json")
THEME_FILE = os.path.join(ROOT, "content", "raves", "magic.json")
BORROWED = os.path.join(HERE, "borrowed", "doom_lounge")  # tiles copied once from assets/story/doom_lounge on feature/doom-layout-worlds (tools/story/borrowed/.gdignore keeps Godot out)

C22 = math.cos(math.radians(22.5))
TIERS = [("t0", 14.5, 17.0, 0.0, "mg_floor_pearl", 6.0), ("t1", 12.0, 14.5, -0.375, "mg_floor_moss", 7.0), ("t2", 9.5, 12.0, -0.75, "mg_floor_velvet", 8.0)]
WELL_A, WELL_FLOOR = 9.5, -1.125
RING_TINT = ["#ffd0f0", "#c8b8ff", "#9ff0ff", "#ffe8a8", "#d8b8ff", "#ffb8e8", "#a8ffe0", "#c8c8ff"]
WALLS = ["mg_wall_crystal", "mg_wall_curtain", "mg_wall_vine", "mg_wall_crystal", "mg_wall_crystal", "mg_wall_curtain", "mg_wall_vine", "mg_wall_curtain"]

CLOAK_F = Frame(225)
BAR_F = Frame(135)
STAGE_F = Frame(180)
HOME_F = Frame(0)
RACE_F = Frame(225, loc(225, 0.0, 6.0))  # the carriage house: a narrow alcove beside the cloakroom's
HUB_AT = [0.0, 15.0]

TEXTURES = ["mg_floor_pearl", "mg_floor_moss", "mg_floor_velvet", "mg_floor_rug", "mg_floor_star", "mg_floor_plank", "mg_wall_crystal", "mg_wall_curtain", "mg_wall_vine", "mg_wall_marble", "mg_wall_plank",
            "mg_trim", "mg_ceil_dome", "mg_arch", "mg_window", "mg_moon", "mg_pylon", "mg_panel", "mg_rune", "mg_stable_door", "mg_counter", "mg_cauldron", "mg_cabinet", "mg_rail", "mg_console", "mg_deck",
            "mg_hatch", "mg_carriage", "mg_unicorn", "mg_mushroom", "mg_crystal", "mg_lantern", "mg_plant", "mg_knob_0", "mg_knob_1", "mg_knob_2", "mg_knob_3", "pc_glass_lit", "pc_lamp_lit", "mg_wall_wood"]
PIECES = ("mg_aurora", "mg_sparkle_ring", "mg_orb_dome")
AMBIENT = "mg_ambient"
PINK, CYAN, LILAC, GOLD, MINT, PEARL = "#ff7ad8", "#7ff0ff", "#b48cff", "#ffe27a", "#8fffd0", "#fff0fa"


# ---------------------------------------------------------------------------------------------------------------------------------------- placeholder art
def build_art():
    art = ra.Art("magic")
    # tiles borrowed from the Chill-out lounge and recoloured violet and pearl
    art.borrow(BORROWED, {"mg_floor_velvet": ("floor_curtain", 290, 0.9, 0.95), "mg_floor_plank": ("floor_wood", 280, 0.45, 1.1), "mg_wall_curtain": ("wall_curtain", 292, 1.0, 1.05),
                     "mg_wall_marble": ("wall_marble", 285, 0.35, 1.45), "mg_wall_plank": ("wall_wood", 275, 0.5, 1.25), "mg_wall_wood": ("wall_table", 285, 0.5, 1.25),
                     "mg_plant": "thing_plant"})
    # floors
    pearl = [ramp("#5a4a8a", "#8a78c8", "#c8b8f0", "#fff0fa"), ramp("#4a6a9a", "#7ab0e0", "#b8e8ff", "#f0ffff"), ramp("#8a4a8a", "#d078c8", "#ffb0e8", "#fff0fa"), ramp("#4a8a7a", "#78d0b8", "#b0ffe0", "#f0fff8")]
    art.tile("mg_floor_pearl", ra.inlay(ra.mosaic(None, 4, 3, "#2a1860", pearl), "diamond", "#ffe27a", 1))
    art.tile("mg_floor_moss", ra.ground(ramp("#1a3a3a", "#2a6a58", "#4aa878", "#8ae0a0"), 9, 5, ["#ff7ad8", "#ffe27a", "#7ff0ff", "#ffffff"], density=0.018))
    art.tile("mg_floor_rug", ra.inlay(ra.inlay(ra.ground(ramp("#2a0a4a", "#5a1a8a", "#8a3ac8", "#c880ff"), 14, 7), "rings", "#ffe27a", 2), "cross", "#ff7ad8", 1))
    art.tile("mg_floor_star", ra.inlay(ra.starfield(ramp("#0a0a2a", "#1a1a5a", "#2a2a8a", "#4a4ac0"), 9), "rings", "#7ff0ff", 1))
    art.tile("mg_wall_crystal", ra.facets(ramp("#2a1860", "#5a3aa8", "#9a78e8", "#e0d0ff"), 11, 5))
    art.tile("mg_wall_vine", ra.ground(ramp("#0a2a2a", "#1a5a40", "#3a9a60", "#7ad890"), 7, 13, ["#ff7ad8", "#ffffff", "#ffe27a"], density=0.012))
    art.tile("mg_ceil_dome", ra.starfield(ramp("#0a0820", "#1a1450", "#2a2080", "#4a3ab0"), 17, 0.02))
    art.tile("mg_trim", ra.band(ramp("#3a2a6a", "#8a6ac8", "#d0b0ff", "#ffffff"), "#ffe27a", 3), 1.0)
    # decals (alpha)
    c = Cv(96, 96)  # a rainbow arch behind the DJ
    for k, col in enumerate(["#ff5a8a", "#ffa04a", "#ffe27a", "#8fffd0", "#7ff0ff", "#b48cff"]):
        c.flat(c.ell(6 + k * 4, 6 + k * 4, 90 - k * 4, 180 - k * 4), col)
    c.erase(c.rect(0, 62, 96, 96))
    c.erase(c.ell(30, 30, 66, 200))
    art.sprite("mg_arch", c)
    c = Cv(96, 96)  # a stained-glass window
    c.flat(c.rrect(10, 4, 86, 92, 36), "#2a1860", edge=True, edge_col="#14102e")
    for k, (x0, y0, x1, y1, col) in enumerate([(16, 20, 46, 50, PINK), (50, 20, 80, 50, CYAN), (16, 54, 46, 86, GOLD), (50, 54, 80, 86, LILAC), (30, 8, 66, 24, MINT)]):
        c.flat(c.rect(x0, y0, x1, y1), col)
    c.flat(c.rect(46, 8, 50, 88), "#2a1860")
    art.sprite("mg_window", c)
    c = Cv(96, 96)  # a moon window
    c.flat(c.ell(8, 8, 88, 88), "#14102e")
    c.paint(c.ell(14, 14, 82, 82), ramp("#6a5aa8", "#a898e0", "#e8e0ff", "#ffffff"), c.dome(40, 40, 36, 36), edge=False)
    c.flat(c.ell(30, 24, 44, 38), "#c8c0f0")
    c.flat(c.ell(50, 50, 64, 64), "#c8c0f0")
    art.sprite("mg_moon", c)
    c = Cv(64, 96)  # a crystal pylon (the speaker)
    for k, (x, w, h) in enumerate([(8, 14, 70), (20, 18, 88), (36, 14, 62), (46, 12, 50)]):
        c.paint(c.poly([(x, 94), (x + w // 2, 94 - h), (x + w, 94)]), ramp("#3a1a8a", "#7a4ae0", "#c8a0ff", "#ffffff"), c.lit((x, 94 - h, x + w, 94), 0.5, 0.5))
    art.sprite("mg_pylon", c)
    c = Cv(96, 128)  # the cloak wall panel: a curtained doorway with a star
    c.paint(c.rrect(8, 10, 88, 128, 30), ramp("#3a1060", "#7a2a98", "#c050c0", "#ff90e0"), c.lit((8, 10, 88, 128), 0.5, 0.4), edge=True)
    c.flat(c.rect(46, 28, 50, 128), "#2a0a48")
    c.flat(c.poly([(48, 30), (52, 40), (62, 41), (54, 47), (57, 57), (48, 51), (39, 57), (42, 47), (34, 41), (44, 40)]), GOLD)
    art.sprite("mg_panel", c)
    c = Cv(64, 64)  # a glowing rune plate
    c.flat(c.rrect(2, 2, 62, 62, 8), "#14102e", edge=True, edge_col=LILAC)
    c.lines([(14, 48), (24, 16), (32, 40), (42, 16), (50, 48)], 4)
    c.flat(c.lines([(14, 48), (24, 16), (32, 40), (42, 16), (50, 48)], 4), CYAN)
    art.sprite("mg_rune", c)
    c = Cv(96, 128)  # the carriage house door: big planks with a lantern
    c.paint(c.rrect(4, 6, 92, 128, 40), ramp("#3a2010", "#6a4020", "#a8703a", "#e0b068"), c.lit((4, 6, 92, 128), 0.5, 0.4), edge=True)
    for x in (30, 48, 66):
        c.flat(c.rect(x, 20, x + 2, 128), "#2a1608")
    c.flat(c.ell(40, 52, 56, 68), GOLD, edge=True, edge_col="#14102e")
    art.sprite("mg_stable_door", c)
    # furniture and props (billboards)
    def cauldron(cv, y):
        cv.paint(cv.ell(40, y - 38, 92, y + 4), ramp("#101018", "#242434", "#3b3b55", "#6a6a90"), cv.dome(60, y - 14, 26, 22))
        cv.flat(cv.ell(44, y - 40, 88, y - 24), "#8fffd0", edge=True, edge_col="#14102e")
        for k, (x, r) in enumerate([(54, 5), (68, 4), (78, 6)]):
            cv.flat(cv.ell(x - r, y - 56 + k * 4, x + r, y - 48 + k * 4), PINK if k != 1 else CYAN)
        for k in range(3):
            cv.flat(cv.rect(14 + k * 8, y - 22, 20 + k * 8, y - 2), [PINK, CYAN, GOLD][k], edge=True, edge_col="#14102e")
    art.sprite("mg_counter", ra.counter(128, 128, ("#2a1840", "#5a3a8a", "#8a60c8", "#c8a0ff"), GOLD, front="#3a1a5a", items=cauldron))
    def lamp_desk(cv, y):
        cv.flat(cv.rect(96, y - 18, 100, y - 2), "#c8a050")
        cv.flat(cv.poly([(88, y - 18), (108, y - 18), (102, y - 34), (94, y - 34)]), GOLD, edge=True, edge_col="#14102e")
        cv.flat(cv.rrect(16, y - 14, 50, y - 2, 3), "#fff0fa", edge=True, edge_col="#14102e")
        cv.flat(cv.rect(22, y - 12, 44, y - 10), LILAC)
    art.sprite("mg_cauldron", ra.counter(128, 128, ("#5a3010", "#8a5a2a", "#c08a48", "#f0c070"), "#fff0fa", front="#6a3a1a", items=lamp_desk))
    def potions(cv, ys):
        cols = [PINK, CYAN, GOLD, MINT, LILAC]
        for r, y in enumerate(ys):
            for k in range(4):
                x = 14 + k * 16
                h = 14 + (k + r) % 3 * 4
                cv.flat(cv.rect(x, y - h, x + 8, y), cols[(k + r) % 5], edge=True, edge_col="#14102e")
                cv.flat(cv.rect(x + 2, y - h - 4, x + 6, y - h), "#fff0fa")
    art.sprite("mg_cabinet", ra.cabinet(96, 128, ("#1a1030", "#3a2468", "#6a48a8", "#a888e0"), GOLD, potions))
    art.sprite("mg_rail", ra.rack(128, 128, "#7a5a3a", GOLD, (PINK, CYAN, GOLD, LILAC, MINT), "cape"))
    art.sprite("mg_console", ra.console(128, 128, ("#1a1030", "#3a2468", "#6a48a8", "#a888e0"), CYAN, GOLD))
    art.sprite("mg_deck", ra.deck(96, 56, ("#2a1060", "#5a2a98", "#9a58e0", "#d8a8ff"), "#ffe9a8", "#3a2468", PINK, (CYAN, MINT, GOLD, PINK)))
    art.sprite("mg_hatch", ra.hatch_door(48, 84, ("#5a3010", "#a8703a", "#e0b068", "#fff0c0"), ("#3a1060", "#7a2a98", "#c050c0", "#ff90e0"), "#58ff9c", glow="#ffe9a8"))
    c = Cv(112, 72)  # the pumpkin coach
    c.paint(c.ell(12, 6, 100, 56), ramp("#8a3a0a", "#d8701a", "#ffa040", "#ffd890"), c.dome(46, 28, 44, 26), edge=True)
    for x in (34, 54, 74):
        c.flat(c.rect(x, 10, x + 2, 52), "#a84a10")
    c.flat(c.rrect(40, 20, 64, 40, 4), "#8fe0ff", edge=True, edge_col="#14102e")
    c.flat(c.rect(54, 0, 58, 10), "#2a8a50")
    for cx in (26, 86):
        c.paint(c.ell(cx - 13, 44, cx + 13, 70), ramp("#4a3010", "#8a6030", "#c8a050"), c.dome(cx, 57, 13, 13))
        c.flat(c.ell(cx - 4, 53, cx + 4, 61), GOLD)
    art.sprite("mg_carriage", c)
    c = Cv(96, 128)  # a unicorn statue: pearl horse, rainbow mane, gold horn
    pal = ramp("#7a6aa8", "#b8a8e0", "#f0e8ff", "#ffffff")
    c.paint(c.ell(18, 56, 70, 96), pal, c.dome(40, 74, 30, 22))
    c.paint(c.poly([(54, 64), (70, 30), (84, 38), (74, 72)]), pal, c.lit((54, 30, 84, 72), 0.55, 0.4))
    c.paint(c.ell(68, 22, 94, 46), pal, c.dome(80, 32, 14, 12))
    for x in (22, 32, 54, 62):
        c.paint(c.rect(x, 88, x + 6, 124), pal, c.round_x(x, x + 6))
    c.flat(c.poly([(82, 24), (90, 2), (88, 24)]), GOLD, edge=True, edge_col="#14102e")
    for k, col in enumerate([PINK, CYAN, LILAC, MINT]):
        c.flat(c.poly([(66, 26 + k * 6), (60 - k * 2, 36 + k * 7), (70, 36 + k * 7)]), col)
    c.flat(c.ell(86, 30, 90, 34), "#14102e")
    art.sprite("mg_unicorn", c)
    c = Cv(64, 80)  # a toadstool
    c.flat(c.rect(24, 40, 40, 78), "#fff0e0", edge=True, edge_col="#4a3a5a")
    c.paint(c.ell(2, 8, 62, 52), ramp("#8a1a6a", "#d83a98", "#ff7ad8", "#ffc8f0"), c.dome(26, 26, 30, 22), edge=True)
    for (x, y, r) in [(18, 20, 5), (40, 16, 4), (30, 34, 4), (50, 32, 3)]:
        c.flat(c.ell(x - r, y - r, x + r, y + r), "#fff8f0")
    art.sprite("mg_mushroom", c)
    c = Cv(64, 80)  # a crystal cluster
    for (x, w, h, col) in [(4, 16, 46, "#7a4ae0"), (18, 22, 74, "#c8a0ff"), (38, 16, 54, "#7ff0ff"), (48, 12, 36, "#ff7ad8")]:
        c.paint(c.poly([(x, 78), (x + w // 2, 78 - h), (x + w, 78)]), ramp("#2a1060", col, "#e8d8ff", "#ffffff"), c.lit((x, 78 - h, x + w, 78), 0.55, 0.5))
    art.sprite("mg_crystal", c)
    c = Cv(48, 64)  # a floating lantern
    c.flat(c.rect(23, 0, 25, 14), "#c8a050")
    c.paint(c.ell(8, 12, 40, 54), ramp("#a8681a", "#ffb840", "#ffe58a", "#ffffff"), c.dome(22, 30, 16, 20), edge=True)
    c.flat(c.rect(14, 8, 34, 15), "#7a5a3a")
    art.sprite("mg_lantern", c)
    ra.split_knob(art, ra.knob_sheet(["#3a1a6a", "#7a4ac0", "#c8a0ff", "#f0e0ff"], PINK, ring_on=CYAN), "mg_knob")
    art.copy_mothership(["pc_glass_lit", "pc_lamp_lit"])
    # the sky (aurora over a violet night) and the soft pieces
    ra.sky(os.path.join(art.tex, "mg_sky.png"), ["#0a0828", "#1a1458", "#4a2a98", "#c880d8", "#ffc8e8"], 0.01, [(40, 0.7, "#ff7ad8"), (170, 0.6, "#7ff0ff")], 5, bands=[(16, 0.7, "#8fffd0", 30), (28, 0.55, "#ff7ad8", 26)])
    art.made["mg_sky"] = (256, 64, 1.0)
    art.image("mg_aurora", ra.piece_curtain(["#ff7ad8", "#b48cff", "#7ff0ff", "#8fffd0", "#ffe27a"], 256, 128))
    art.image("mg_sparkle_ring", ra.piece_ring("#ffe27a", "#ff7ad8"))
    art.image("mg_orb_dome", ra.piece_dome("#b8f0ff"))
    art.image(AMBIENT, ra.piece_glow("#b48cff"))
    return art


# ---------------------------------------------------------------------------------------------------------------------------------------- the map
def piece_poly(k, a0, a1):
    phi = 45 * k
    return [pol(a0 / C22, phi - 22.5), pol(a1 / C22, phi - 22.5), pol(a1 / C22, phi + 22.5), pol(a0 / C22, phi + 22.5)]


def build_map(art):
    m = RaveMap("rave_magic", "magic_arrive",
                {"source": "content/story/maps/doom_lounge.json", "note": "the Chill-out lounge (octagonal conversation pit), approximate: eight pieces in three stepped tiers round a sunken well, curtained alcoves"},
                {n: "textures/%s.png" % n for n in TEXTURES}, {"tex": "textures/mg_sky.png", "mode": "cylinder"}, {"color": "#1a1038", "density": 0.010})
    # ---- the bowl: three tiers of eight pieces and the sunken well
    for k in range(8):
        for (tid, a0, a1, fl, ftex, ceil) in TIERS:
            m.sector("%s_%d" % (tid, k), piece_poly(k, a0, a1), fl, ceil, ftex, "mg_ceil_dome", 0.55, RING_TINT[k], ["dance_floor"] if tid == "t2" else [], activities=QUIET if tid == "t2" else STANDING,
                     step_tex="mg_trim", lip_tex="mg_wall_crystal", wall_tex=WALLS[k])
    m.sector("well", [pol(WELL_A / C22, 22.5 + 45 * j) for j in range(8)], WELL_FLOOR, 12.0, "mg_floor_rug", "sky", 0.6, "#ff9ae8", ["dance_floor"], activities=QUIET, step_tex="mg_trim", wall_tex="mg_wall_crystal")
    for k in range(8):
        for tid in ("t0", "t1", "t2"):
            m.link("%s_%d" % (tid, k), "%s_%d" % (tid, (k + 1) % 8))
        m.link("t0_%d" % k, "t1_%d" % k)
        m.link("t1_%d" % k, "t2_%d" % k)
        m.link("t2_%d" % k, "well")
    # ---- the stations
    add_home(m, HOME_F, "t0_0", {"floor": "mg_floor_pearl", "tint": "#ffd0f0", "ceil": "mg_ceil_dome", "wall": "mg_wall_curtain", "hatch": "mg_hatch", "window": "mg_moon"}, "magic_arrive")
    add_stage(m, STAGE_F, "t0_4", {"floor": "mg_floor_pearl", "tint": "#d8b8ff", "dais": "mg_floor_star", "dais_tint": "#e8c8ff", "ceil": "mg_ceil_dome", "wall": "mg_wall_crystal", "trim": "mg_trim",
                                   "deck_sprite": "mg_deck", "arch": "mg_arch", "spk_l": "mg_pylon", "spk_r": "mg_pylon", "pieces": PIECES, "lt_a": "#ff7ad8", "lt_b": "#7ff0ff",
                                   "dj": ("tentacle", "a"), "dancers": [("blob", "b"), ("cyclops", "a"), ("grey", "a")]})
    add_cloak(m, CLOAK_F, "t0_5", {"floor": "mg_floor_plank", "tint": "#d8b8ff", "ceil": "mg_ceil_dome", "wall": "mg_wall_curtain", "counter": "mg_cauldron", "rail": "mg_rail", "cabinet": "mg_cabinet",
                                   "hatch_decal": "mg_panel", "lt": "#d8b8ff"},
              [("antenna", "a"), ("grey", "b"), ("insect", "a"), ("blob", "b"), ("cyclops", "b"), ("tentacle", "a"), ("grey", "a"), ("insect", "b")], ("cyclops", "a"))
    add_bar(m, BAR_F, "t0_3", {"floor": "mg_floor_plank", "tint": "#ffb0e8", "ceil": "mg_ceil_dome", "wall": "mg_wall_marble", "counter": "mg_counter", "cabinet": "mg_cabinet", "screen": "mg_rune",
                               "window_a": "mg_window", "window_b": "mg_moon", "lt": "#ff7ad8"},
            ("blob", "a"), ("antenna", "b"), [("b1", "insect", "a", 20.0, 2.6), ("b2", "cyclops", "b", 19.2, 3.4)])
    add_race(m, RACE_F, "t0_5", {"floor": "mg_floor_plank", "tint": "#ffd890", "ceil": "mg_ceil_dome", "wall": "mg_wall_plank", "door": "mg_stable_door", "side_a": "mg_window", "side_b": "mg_window",
                                 "vehicle": "mg_carriage", "console": "mg_console", "lt": "#ffd890", "vehicle_size": 1.0, "door_size": 2.6}, ("insect", "b"), D=5.0, w0=1.0, w1=1.3, door_u=15.9)
    # ---- waypoints
    m.wp("hub_view", HUB_AT, 0.0, "t0_0", choice_view=True)
    m.wp("well_s", [0.0, 6.5], 0.0, "well")
    m.wp("well_n", [0.0, -6.5], 0.0, "well")
    m.wp("well_sw", [-5.2, 5.2], 0.0, "well")
    m.wp("well_se", [5.2, 5.2], 0.0, "well")
    # ---- the walls: windows, arches and a moon between the stations, as emissive decals
    for k in (1, 2, 6, 7):
        fr = Frame(45 * k)
        for s, sp in ((-3.6, "mg_window"), (3.6, "mg_moon" if k in (2, 6) else "mg_window")):
            m.decal("win_%d_%d" % (k, 0 if s < 0 else 1), sp, fr, A_OUT - 0.015, s, 1.0, 2.4)
        m.decal("rune_%d" % k, "mg_rune", fr, A_OUT - 0.015, 0.0, 3.6, 0.9)
    for s in (-4.4, 4.4):
        m.decal("home_win_%s" % ("l" if s < 0 else "r"), "mg_window", HOME_F, A_OUT - 0.015, s, 1.0, 2.2)
    # ---- things: statues, toadstools, crystals, lanterns, plants, the glow of the rooms
    m.bb("unicorn_e", "mg_unicorn", loc(90, 15.4, 0.0), 1.9, y=0.95)
    m.bb("unicorn_w", "mg_unicorn", loc(270, 15.4, 0.0), 1.9, y=0.95)
    for i, (k, r) in enumerate([(1, 13.2), (2, 13.4), (6, 13.4), (7, 13.2), (3, 12.8), (5, 12.8)]):
        m.bb("toadstool_%d" % i, "mg_mushroom", pol(r, 45 * k + (10 if i % 2 else -10)), 1.5, y=0.75)
    for i, (k, r) in enumerate([(1, 10.8), (3, 10.8), (5, 10.8), (7, 10.8), (0, 10.4), (4, 10.4)]):
        m.bb("crystal_%d" % i, "mg_crystal", pol(r, 45 * k + 12), 1.4, y=0.7)
    for i, (x, z) in enumerate([(-4.0, -2.0), (4.5, -3.0), (0.0, 2.0), (-5.5, 3.0), (5.5, 4.0), (0.0, -6.0)]):
        m.bb("lantern_%d" % i, "mg_lantern", [x, z], 0.9, y=3.4 + (i % 3) * 0.5, anim="bob")
        m.bb("lantern_glow_%d" % i, "glow", [x, z], 1.8, y=3.5 + (i % 3) * 0.5, anim="pulse", blend="add")
    for k in (1, 7):
        m.bb("plant_%d" % k, "mg_plant", loc(45 * k, 15.0, 3.2), 1.3, y=0.65)
    m.bb("glow_well", "glow", [0.0, 0.0], 5.0, y=0.3, anim="pulse", blend="add")
    m.bb("glow_hub", "glow", loc(0, 15.5, 0.0), 2.6, y=1.4, anim="pulse", blend="add")
    m.light("lt_well", [0.0, 0.0], 6.0, 13.0, "#ff7ad8", 1.1)
    m.light("lt_well_b", [0.0, 0.0], 3.0, 9.0, "#7ff0ff", 0.8)
    m.light("lt_hub", loc(0, 15.0), 3.6, 7.0, "#ffd8f0", 1.1)
    m.light("lt_ring_e", loc(90, 15.5), 3.0, 8.0, "#b8e8ff", 1.0)
    m.light("lt_ring_w", loc(270, 15.5), 3.0, 8.0, "#d8b8ff", 1.0)
    # ---- the people: the crowd of the rave (a sunlit bowl of dancers), the guides are placed by the stations
    spots = []
    for k in range(8):
        for (tid, r, dphi) in [("t2", 10.6, 6), ("t2", 11.6, -9)]:
            if k in (3, 4, 5) and r > 11:
                continue
            spots.append(("%s_%d" % (tid, k), pol(r, 45 * k + dphi)))
    for i in range(8):
        spots.append(("well", pol(2.0 + (i % 2) * 3.2 + (i // 4) * 1.4, 45 * i + 20)))
    for k in (1, 2, 6, 7):
        spots.append(("t1_%d" % k, pol(13.4, 45 * k + 5)))
    spots += [("t0_1", pol(16.0, 55)), ("t0_7", pol(16.0, 305)), ("t0_2", pol(15.6, 100)), ("t0_6", pol(15.6, 260))]
    kinds = [("grey", "a"), ("antenna", "a"), ("blob", "b"), ("insect", "a"), ("cyclops", "b"), ("tentacle", "b"), ("grey", "b"), ("antenna", "b"), ("blob", "a"), ("insect", "b"), ("cyclops", "a")]
    add_crowd(m, spots, kinds)
    return m


# ---------------------------------------------------------------------------------------------------------------------------------------- theme file, story, routes
def theme_spec():
    props = [
        {"id": "deck", "role": "stage_deck", "sprite": "mg_deck", "spot": "deck_view"},
        {"id": "bass_knob", "role": "bass_knob", "sprite": "mg_knob_0", "spot": "deck_view"},
        {"id": "coat_panel", "role": "cloakroom", "sprite": "mg_panel", "spot": "cloak_view"},
        {"id": "bar_counter", "role": "bar", "sprite": "mg_counter", "spot": "bar_view"},
        {"id": "stable_door", "role": "race_entrance", "sprite": "mg_stable_door", "spot": "hangar_view"},
        {"id": "home_hatch", "role": "home_threshold", "sprite": "mg_hatch", "spot": "home_door"},
        {"id": "lanterns", "role": "decor", "sprite": "mg_lantern", "at": [0.0, 0.0]},
    ]
    guides = [
        {"id": "dj", "sprite": "rave_magic/tentacle_a", "spot": "deck_view", "for": "stage"},
        {"id": "attendant", "sprite": "rave_magic/cyclops_a", "spot": "cloak_view", "for": "cloakroom"},
        {"id": "bartender", "sprite": "rave_magic/blob_a", "spot": "bar_view", "for": "bar"},
        {"id": "pilot", "sprite": "rave_magic/insect_b", "spot": "hangar_view", "for": "race"},
        {"id": "home_hatch", "sprite": "mg_hatch", "spot": "home_door", "for": "home"},
    ]
    routes = {
        "stage": route(MAP_ID, "hub_view", [leg("well_n", 4, 1, via=["well_s"]), leg("stage_foot", 2, 1, "deck"), leg("stage_steps", 2, 1, "deck"), leg("deck_view", 2, 4, "deck")], "deck_view"),
        "cloak": route(MAP_ID, "hub_view", [leg("well_sw", 4, 1), leg("cloak_door", 2, 1), leg("cloak_hold", 2, 4, "attendant")], "cloak_hold"),
        "bar": route(MAP_ID, "hub_view", [leg("well_se", 4, 1), leg("bar_door", 2, 1), leg("bar_hold", 2, 4, "bartender")], "bar_hold"),
    }
    return {
        "id": "magic", "prefix": "magic", "scene_id": "magic_rave", "geography": "doom_lounge", "arrival": "magic_arrive", "props": props, "guides": guides, "routes": routes,
        "customers": [{"id": "unicorns_floor", "sprite_set": "rave_magic/clubgoers", "count": 31, "spot": "well_s"}, {"id": "unicorns_queue", "sprite_set": "rave_magic/clubgoers", "count": 3, "spot": "cloak_view"}],
        "ingredients": [{"id": "rainbow_nectar", "icon": "magic/ing_nectar", "color": "#ff7ac8"}, {"id": "unicorn_foam", "icon": "magic/ing_foam", "color": "#fff0fa"},
                        {"id": "glitter_sugar", "icon": "magic/ing_glitter", "color": "#ffe27a"}, {"id": "dragonfruit", "icon": "magic/ing_dragonfruit", "color": "#e8368f"}],
        "cloakroom_symbols": [{"id": "unicorn", "icon": "magic/sym_unicorn"}, {"id": "wand", "icon": "magic/sym_wand"}, {"id": "potion", "icon": "magic/sym_potion"}, {"id": "crown", "icon": "magic/sym_crown"}],
    }


PALETTES = {"low": ["#4a2a98", "#2a6a9a"], "cool": ["#7ff0ff", "#b48cff"], "warm": ["#ffe27a", "#ff7ad8"], "rave": ["#ff7ad8", "#7ff0ff", "#b48cff", "#ffe27a"]}


def main(argv) -> int:
    art = build_art()
    arche = rave_people.build("magic", art.name)
    place_activity_sheets(art.name, "magic", os.path.join(art.tex, "mg_knob_sheet.png"))
    ra.write_manifest(art, arche, TEXTURES + ["mg_sky"], [ra.piece_entry(PIECES[0], PIECES[0], "pulse"), ra.piece_entry(PIECES[1], PIECES[1], "pulse"), ra.piece_entry(PIECES[2], PIECES[2], "pulse"),
                                                           ra.piece_entry(AMBIENT, AMBIENT, "pulse")])
    m = build_map(art)
    out = m.to_json()
    write(MAP, out)
    write(STORY, story_json(m.actors, "magic_rave", "The Magic Rave", art.name, "The Lounge", AMBIENT, PALETTES, "A rave in the enchanted lounge (docs/briefs/BEDSIT_RAVES_BRIEF.md section 3): a path's world, not a Story Campaign chapter."))
    write(THEME_FILE, theme_json(theme_spec()))
    write_activity_layouts("magic", CLOAK_F, BAR_F, "rave_magic")
    bearings = hub_bearings(m, HUB_AT, 0.0, ["dj", "attendant", "bartender", "pilot", "customer_0", "customer_7"])
    print("wrote %s (%d sectors, %d things, %d waypoints); hub bearings %s" % (MAP, len(out["sectors"]), len(out["things"]), len(out["waypoints"]), bearings))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
