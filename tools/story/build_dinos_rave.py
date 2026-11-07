#!/usr/bin/env python3
"""Builds the Dinosaurs rave (docs/briefs/BEDSIT_RAVES_BRIEF.md sections 3 and 4; theme id `dinos`, scene prefix `dino`, facing EAST): its map content/story/maps/dino_rave.json, its story file
content/story/dino_rave.json, its theme file content/raves/dinos.json, the activity layouts in content/bedsit/themes.json (cloakroom.dinos.layout, bar.dinos.layout) and the art folder
assets/story/rave_dinos/ (textures, the activities' sheets, the clubgoers' rigs, the manifest).

    python3 tools/story/build_dinos_rave.py

THE PLACE. The Underworld (content/story/maps/doom_underworld.json on feature/doom-layout-worlds: a basalt ledge over a lava gap with chain railings, a long stone causeway climbing to a tusk gate,
a cave on the left, a tent on a shelf on the right) is the geography; this map is a hand-built, approximate version at rave scale, not a conversion: a wide basalt LEDGE where you arrive, a lava
gulf, and across it a 25 m CAUSEWAY with chain railings straight to the stage (the dais under a ribcage arch, tusks either side); two basalt ISLANDS either side of the causeway, each reached by a
short railed bridge, the west one holding the cloakroom (a cave) and the ranger garage (the race entrance), the east one, a step higher, the bar (a tent). Where the Space rave is a ring
and the Magic one a bowl, this is one road with side trips over lava: every route goes up the causeway and branches off over a bridge. Tiles borrowed from the Underworld (basalt, lava, cliff,
chain rail, tent, bones, tusks, gong, lantern) are used as they are; the jungle (ferns, palms, moss, eggs, a skeleton, fossils) is drawn here and called a PLACEHOLDER.

  compass: north is -z. The stage's frame is the same in every rave (phi 180, origin 0): the deck is at (0, -25.2), which is where the bass knob activity puts the knob.
  ledge  x -20..20, z 8..22 (arrival behind it: the way home is a torn jungle poster in a shallow alcove, sector `home`)   causeway x -3..3, z -17..8 (c_s, c_n)
  west island x -20..-6, z -17..-1: cloak (cave, north) and hangar (the ranger garage, north)   east island x 6..20, z -17..-1, floor 0.3: bar (tent, north)
  lava (void sectors, floor -4): the rest of x -20..20, z -17..8, with a chain railing on every edge you can walk along
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rave_builder import (ROOT, Frame, RaveMap, add_bar, add_cloak, add_crowd, add_home, add_race, add_stage, hub_bearings, leg, place_activity_sheets, rect, route, story_json,  # noqa: E402
                          theme_json, write, write_activity_layouts, QUIET, STANDING)
import rave_art as ra  # noqa: E402
import rave_people  # noqa: E402
from art.bedsit_draw import Cv, ramp  # noqa: E402

MAP_ID = "dino_rave"
MAP = os.path.join(ROOT, "content", "story", "maps", "dino_rave.json")
STORY = os.path.join(ROOT, "content", "story", "dino_rave.json")
THEME_FILE = os.path.join(ROOT, "content", "raves", "dinos.json")
BORROWED = os.path.join(HERE, "borrowed", "doom_underworld")  # tiles copied once from assets/story/doom_underworld on feature/doom-layout-worlds (tools/story/borrowed/.gdignore keeps Godot out)

STAGE_F = Frame(180)
CLOAK_F = Frame(180, (-11.0, 0.0))
RACE_F = Frame(180, (-17.6, 0.0))
BAR_F = Frame(180, (11.0, 0.0))
HOME_F = Frame(0, (0.0, 5.0))
HUB_AT = [0.0, 19.0]
LAVA = -4.0

TEXTURES = ["dn_floor_slab", "dn_floor_stone", "dn_floor_lava", "dn_floor_cave", "dn_floor_tower", "dn_floor_moss", "dn_wall_rock", "dn_wall_cliff", "dn_wall_cave", "dn_wall_step", "dn_wall_tower",
            "dn_wall_jungle", "dn_ceil", "dn_rail", "dn_tent", "dn_bones", "dn_tusks", "dn_gong", "dn_lantern", "dn_pillar", "dn_crate", "dn_drum", "dn_cloth", "dn_lavafall", "dn_stub", "dn_ribs",
            "dn_window", "dn_rune", "dn_gate", "dn_fossil", "dn_counter", "dn_desk", "dn_cabinet", "dn_rack", "dn_console", "dn_deck", "dn_hatch", "dn_jeep", "dn_fern", "dn_palm", "dn_egg", "dn_skeleton",
            "dn_torch", "dn_glow", "dn_knob_0", "dn_knob_1", "dn_knob_2", "dn_knob_3", "pc_glass_lit", "pc_lamp_lit"]
PIECES = ("dn_lava_sheets", "dn_fire_ring", "dn_ember_dome")
AMBIENT = "dn_ambient"
ORANGE, AMBER, RED, GREEN, TEAL, BONE = "#ff7a2a", "#ffc23f", "#ff4a1a", "#6ad850", "#3fd0b0", "#f4ecd0"


# ---------------------------------------------------------------------------------------------------------------------------------------- placeholder art
def build_art():
    art = ra.Art("dinos")
    art.borrow(BORROWED, {"dn_floor_slab": "uw_floor_slab", "dn_floor_stone": "uw_floor_stone", "dn_floor_lava": "uw_floor_lava", "dn_floor_cave": "uw_floor_cave", "dn_floor_tower": "uw_floor_tower",
                          "dn_wall_rock": "uw_wall_rock", "dn_wall_cliff": "uw_wall_cliff", "dn_wall_cave": "uw_wall_cave", "dn_wall_step": "uw_wall_step", "dn_wall_tower": "uw_wall_tower",
                          "dn_ceil": "uw_ceil", "dn_rail": "uw_rail", "dn_tent": "uw_tent", "dn_bones": "uw_bones", "dn_tusks": "uw_tusks", "dn_gong": "uw_gong", "dn_lantern": "uw_lantern",
                          "dn_pillar": "uw_pillar", "dn_crate": "uw_crate", "dn_drum": "uw_drum", "dn_cloth": "uw_cloth", "dn_lavafall": "uw_lavafall", "dn_stub": "uw_stub"})
    art.tile("dn_floor_moss", ra.ground(ramp("#14240e", "#2a4a18", "#4a7a24", "#8ab83a"), 8, 21, ["#ff7a2a", "#ffe27a", "#ffffff"], density=0.01))
    art.tile("dn_wall_jungle", ra.ground(ramp("#0a1a0a", "#1a4a1a", "#2a7a2a", "#5ac048"), 5, 31, ["#ffc23f", "#ff4a1a"], density=0.006))
    # decals
    c = Cv(96, 96)  # a ribcage arch behind the DJ: a great curved rib with vertebrae
    c.paint(c.ell(2, 6, 94, 190), ramp("#7a6a4a", "#b8a878", "#f4ecd0", "#ffffff"), c.dome(30, 40, 60, 120), edge=True)
    c.erase(c.ell(16, 20, 80, 204))
    c.erase(c.rect(0, 90, 96, 96))
    for k in range(7):
        a = k / 6.0
        yy = 28 + 56 * a
        c.flat(c.rect(0, int(yy), 16, int(yy) + 3), "#8a7a58")
        c.flat(c.rect(80, int(yy), 96, int(yy) + 3), "#8a7a58")
    for k in range(5):
        c.flat(c.ell(12 + k * 17, 2, 22 + k * 17, 12), "#e8dcb0", edge=True, edge_col="#4a3a1a")
    art.sprite("dn_ribs", c)
    c = Cv(96, 96)  # a lava porthole
    c.flat(c.ell(6, 6, 90, 90), "#2a1a14", edge=True, edge_col="#14102e")
    c.paint(c.ell(14, 14, 82, 82), ramp("#6a1a0a", "#d84a1a", "#ff9a3a", "#ffe27a"), c.dome(40, 40, 36, 36), edge=False)
    c.flat(c.ell(36, 30, 50, 40), "#fff0a0")
    art.sprite("dn_window", c)
    c = Cv(64, 64)  # a glowing glyph plate
    c.flat(c.rrect(2, 2, 62, 62, 8), "#2a1a14", edge=True, edge_col=ORANGE)
    c.flat(c.ell(14, 14, 50, 50), ORANGE)
    c.flat(c.ell(24, 24, 40, 40), "#2a1a14")
    c.flat(c.poly([(32, 8), (36, 22), (28, 22)]), AMBER)
    c.flat(c.poly([(32, 56), (36, 42), (28, 42)]), AMBER)
    art.sprite("dn_rune", c)
    c = Cv(96, 128)  # the ranger garage gate: logs and two skulls
    c.paint(c.rrect(4, 6, 92, 128, 30), ramp("#2a1a0a", "#5a3a1a", "#8a5a2a", "#c8904a"), c.lit((4, 6, 92, 128), 0.5, 0.4), edge=True)
    for x in (24, 40, 56, 72):
        c.flat(c.rect(x, 20, x + 3, 128), "#1a1008")
    for cx in (30, 66):
        c.flat(c.ell(cx - 9, 44, cx + 9, 62), BONE, edge=True, edge_col="#14102e")
        c.flat(c.ell(cx - 5, 50, cx - 1, 55), "#14102e")
        c.flat(c.ell(cx + 1, 50, cx + 5, 55), "#14102e")
    art.sprite("dn_gate", c)
    c = Cv(64, 64)  # an ammonite fossil on a slab
    c.paint(c.rrect(2, 4, 62, 60, 6), ramp("#2a2a38", "#4a4a5a", "#6a6a7a", "#8a8a9a"), c.lit((2, 4, 62, 60), 0.5, 0.3))
    for r, col in [(22, "#c8b890"), (16, "#6a5a40"), (11, "#c8b890"), (6, "#6a5a40"), (2, "#c8b890")]:
        c.flat(c.ell(32 - r, 32 - r, 32 + r, 32 + r), col)
    art.sprite("dn_fossil", c)
    # props
    def stew(cv, y):
        cv.paint(cv.ell(44, y - 34, 92, y + 2), ramp("#101018", "#242434", "#3b3b55", "#6a6a90"), cv.dome(64, y - 12, 24, 20))
        cv.flat(cv.ell(48, y - 36, 88, y - 22), "#c8601a", edge=True, edge_col="#14102e")
        cv.flat(cv.ell(56, y - 52, 62, y - 44), "#e8e0d0")
        cv.flat(cv.ell(72, y - 58, 80, y - 48), "#e8e0d0")
        for k in range(3):
            cv.flat(cv.rrect(12 + k * 10, y - 18, 22 + k * 10, y - 2, 3), [AMBER, BONE, "#c8a060"][k], edge=True, edge_col="#14102e")
    art.sprite("dn_counter", ra.counter(128, 128, ("#2a1408", "#5a3418", "#8a5428", "#c88a48"), "#d8b070", front="#3a2010", items=stew))
    def skull(cv, y):
        cv.flat(cv.ell(18, y - 24, 46, y - 2), BONE, edge=True, edge_col="#14102e")
        cv.flat(cv.rect(24, y - 4, 40, y), BONE, edge=True, edge_col="#14102e")
        cv.flat(cv.ell(24, y - 17, 31, y - 10), "#14102e")
        cv.flat(cv.ell(34, y - 17, 41, y - 10), "#14102e")
        cv.flat(cv.rect(92, y - 20, 96, y - 2), "#c8a050")
        cv.flat(cv.poly([(84, y - 20), (104, y - 20), (98, y - 36), (90, y - 36)]), AMBER, edge=True, edge_col="#14102e")
    art.sprite("dn_desk", ra.counter(128, 128, ("#2a2a30", "#4a4a54", "#6a6a78", "#9a9aaa"), "#b8b8c8", front="#34343e", items=skull))
    def jars(cv, ys):
        cols = [AMBER, GREEN, RED, "#c8a060", TEAL]
        for r, y in enumerate(ys):
            for k in range(4):
                x = 14 + k * 16
                h = 12 + (k + r) % 3 * 4
                cv.flat(cv.rrect(x, y - h, x + 10, y, 3), cols[(k + r) % 5], edge=True, edge_col="#14102e")
                cv.flat(cv.rect(x + 2, y - h - 3, x + 8, y - h), "#6a4a2a")
    art.sprite("dn_cabinet", ra.cabinet(96, 128, ("#1a1008", "#3a2410", "#6a4420", "#a8703a"), AMBER, jars))
    art.sprite("dn_rack", ra.rack(128, 128, "#5a3a1a", "#c8a050", ("#c8883a", "#8a5a2a", "#6a8a3a", "#a86a3a", "#d8b070"), "cape"))
    art.sprite("dn_console", ra.console(128, 128, ("#1a1814", "#3a3830", "#6a6858", "#a8a48a"), ORANGE, AMBER))
    art.sprite("dn_deck", ra.deck(96, 56, ("#1a1410", "#3a2c24", "#6a4c3a", "#a8805a"), "#ffb060", "#2a2018", ORANGE, (ORANGE, AMBER, GREEN, RED)))
    art.sprite("dn_hatch", ra.hatch_door(48, 84, ("#2a3a10", "#5a7a20", "#8ab030", "#c8e870"), ("#0a2a0a", "#1a5a1a", "#3a9a3a", "#7ae070"), "#58ff9c", glow="#d8ff9a"))
    art.sprite("dn_jeep", ra.vehicle(112, 56, ("#4a4a1a", "#8a8a2a", "#c8c050", "#f0e890"), ("#102838", "#1f5878", "#4aa8d0", "#a8e8f8"), stripe="#e8503a"))
    c = Cv(96, 96)  # a fern
    for k, ang in enumerate([-70, -40, -15, 15, 40, 70]):
        a = math.radians(ang - 90)
        pts = [(48, 94)]
        tip = (48 + 46 * math.cos(a), 94 + 80 * math.sin(a))
        mid = (48 + 22 * math.cos(a + 0.35), 94 + 42 * math.sin(a + 0.35))
        c.flat(c.poly([(46, 94), (50, 94), (tip[0] + 5, tip[1] + 6), (mid[0] + 8, mid[1]), tip]), ["#2a7a2a", "#3a9a3a", "#58b848"][k % 3], edge=True, edge_col="#0a2a0a")
    art.sprite("dn_fern", c)
    c = Cv(96, 160)  # a palm
    c.flat(c.poly([(44, 158), (52, 158), (54, 60), (46, 60)]), "#6a4a2a", edge=True, edge_col="#2a1a0a")
    for k, ang in enumerate([-80, -50, -20, 20, 50, 80, -110, 110]):
        a = math.radians(ang - 90)
        tip = (50 + 46 * math.cos(a), 60 + 46 * math.sin(a) + 14)
        c.flat(c.poly([(50, 58), (50 + 26 * math.cos(a) - 4, 58 + 26 * math.sin(a) - 8), tip, (50 + 26 * math.cos(a) + 4, 58 + 26 * math.sin(a) + 6)]), ["#2a8a2a", "#48b048", "#68d058"][k % 3], edge=True, edge_col="#0a2a0a")
    c.flat(c.ell(44, 54, 56, 66), "#c8883a", edge=True, edge_col="#2a1a0a")
    art.sprite("dn_palm", c)
    c = Cv(96, 64)  # a nest of eggs
    c.flat(c.ell(4, 34, 92, 62), "#6a4a2a", edge=True, edge_col="#2a1a0a")
    for (x, y, col) in [(22, 26, "#e8e0c0"), (44, 20, "#c8e0b0"), (66, 26, "#e8d0b8"), (34, 34, "#c8d8e8")]:
        c.paint(c.ell(x - 11, y - 12, x + 11, y + 14), ramp("#8a8a68", "#c8c8a0", col, "#ffffff"), c.dome(x - 3, y - 2, 11, 13), edge=True)
        c.flat(c.ell(x - 4, y - 4, x - 1, y - 1), "#8a9a68")
        c.flat(c.ell(x + 3, y + 3, x + 6, y + 6), "#8a9a68")
    art.sprite("dn_egg", c)
    c = Cv(192, 128)  # a dinosaur skeleton, side on: skull, spine, ribs, legs, tail
    bone = ramp("#7a6a4a", "#b8a878", "#e8dcb0", "#ffffff")
    c.paint(c.poly([(8, 70), (40, 56), (74, 50), (150, 56), (184, 74), (150, 66), (74, 66), (40, 72)]), bone, c.lit((8, 50, 184, 74), 0.55, 0.35))
    for k in range(6):
        x = 64 + k * 14
        c.flat(c.poly([(x, 56), (x + 4, 56), (x + 12, 98), (x + 6, 98)]), "#e8dcb0", edge=True, edge_col="#4a3a1a")
    c.paint(c.poly([(124, 24), (170, 24), (186, 40), (170, 52), (124, 52), (118, 38)]), bone, c.lit((118, 24, 186, 52), 0.55, 0.4))
    c.flat(c.ell(142, 30, 152, 40), "#14102e")
    for k in range(7):
        c.flat(c.poly([(152 + k * 4, 52), (155 + k * 4, 52), (153 + k * 4, 58)]), "#ffffff")
    c.flat(c.poly([(88, 66), (100, 66), (108, 120), (92, 120)]), "#e8dcb0", edge=True, edge_col="#4a3a1a")
    c.flat(c.poly([(48, 70), (60, 70), (62, 120), (46, 120)]), "#e8dcb0", edge=True, edge_col="#4a3a1a")
    art.sprite("dn_skeleton", c)
    c = Cv(32, 96)  # a standing torch
    c.flat(c.rect(14, 30, 18, 94), "#6a4a2a", edge=True, edge_col="#2a1a0a")
    c.paint(c.poly([(16, 0), (26, 22), (22, 32), (10, 32), (6, 22)]), ramp("#8a1a0a", "#e84a1a", "#ffb040", "#fff0a0"), c.lit((6, 0, 26, 32), 0.5, 0.6))
    art.sprite("dn_torch", c)
    art.image("dn_glow", ra.piece_glow("#ff9a3a", 128, 128))
    ra.split_knob(art, ra.knob_sheet(["#2a1a14", "#5a3a28", "#9a6a48", "#d8a878"], ORANGE, ring_on=ORANGE), "dn_knob")
    art.copy_mothership(["pc_glass_lit", "pc_lamp_lit"])
    ra.sky(os.path.join(art.tex, "dn_sky.png"), ["#1a0a0a", "#3a1410", "#8a2a10", "#e8681a", "#ffc060"], 0.004, [(60, 0.9, "#ff5a1a"), (190, 0.5, "#ff9a3a")], 9, bands=[(18, 0.8, "#2a1a18", 22), (30, 0.5, "#5a2a18", 18)])
    art.made["dn_sky"] = (256, 64, 1.0)
    art.image("dn_lava_sheets", ra.piece_curtain(["#ff4a1a", "#ff9a3a", "#ffe27a", "#ff6a2a", "#ff4a1a"], 256, 128))
    art.image("dn_fire_ring", ra.piece_ring("#ffb040", "#ff4a1a"))
    art.image("dn_ember_dome", ra.piece_dome("#ffa050"))
    art.image(AMBIENT, ra.piece_glow("#ff6a2a"))
    return art


# ---------------------------------------------------------------------------------------------------------------------------------------- the map
def build_map(art):
    m = RaveMap("rave_dinos", "dino_arrive",
                {"source": "content/story/maps/doom_underworld.json", "note": "the Underworld (basalt ledge, lava gap with chain railings, a causeway to the tusk gate, a cave and a tent), approximate: a ledge, a lava gulf, a causeway and two islands"},
                {n: "textures/%s.png" % n for n in TEXTURES}, {"tex": "textures/dn_sky.png", "mode": "cylinder"}, {"color": "#3a1408", "density": 0.006}, gain=1.7, lgain=1.5)
    kw = dict(step_tex="dn_wall_step", lip_tex="dn_wall_rock")
    # ---- the ledge, the causeway, the bridges and the islands
    m.sector("ledge", rect(-20, 8, 20, 22), 0.0, 22.0, "dn_floor_slab", "sky", 0.6, "#ffb070", ["dance_floor"], activities=QUIET, wall_tex="dn_wall_cliff", **kw)
    m.sector("c_s", rect(-3, -3, 3, 8), 0.0, 22.0, "dn_floor_stone", "sky", 0.6, "#ffa060", ["dance_floor"], activities=QUIET, wall_tex="dn_wall_cliff", **kw)
    m.sector("c_n", rect(-3, -17, 3, -3), 0.0, 22.0, "dn_floor_tower", "sky", 0.6, "#ff9050", ["dance_floor"], activities=QUIET, wall_tex="dn_wall_cliff", **kw)
    m.sector("br_w", rect(-6, -11, -3, -8), 0.0, 22.0, "dn_floor_stone", "sky", 0.6, "#ffa060", [], activities=STANDING, wall_tex="dn_wall_cliff", **kw)
    m.sector("br_e", rect(3, -11, 6, -8), 0.0, 22.0, "dn_floor_stone", "sky", 0.6, "#ffa060", [], activities=STANDING, wall_tex="dn_wall_cliff", **kw)
    m.sector("isle_w", rect(-20, -17, -6, -1), 0.0, 22.0, "dn_floor_stone", "sky", 0.6, "#ffb888", [], activities=STANDING, wall_tex="dn_wall_rock", **kw)
    m.sector("isle_e", rect(6, -17, 20, -1), 0.3, 22.0, "dn_floor_moss", "sky", 0.6, "#ffc890", [], activities=STANDING, wall_tex="dn_wall_rock", **kw)
    # ---- the lava (voids): the gulf round the causeway and under the islands
    lava = {"lava_w_a": rect(-20, -1, -6, 8), "lava_w_b": rect(-6, -17, -3, -11), "lava_w_c": rect(-6, -8, -3, 8), "lava_e_a": rect(6, -1, 20, 8), "lava_e_b": rect(3, -17, 6, -11), "lava_e_c": rect(3, -8, 6, 8)}
    for sid, poly in lava.items():
        m.sector(sid, poly, LAVA, 22.0, "dn_floor_lava", "sky", 0.7, "#ff5a2a", [], void=True, activities=STANDING, wall_tex="dn_wall_cliff")
    for a, b in [("ledge", "c_s"), ("c_s", "c_n"), ("c_n", "br_w"), ("c_n", "br_e"), ("c_s", "br_w"), ("c_s", "br_e"), ("br_w", "isle_w"), ("br_e", "isle_e"), ("lava_w_a", "lava_w_c"), ("lava_e_a", "lava_e_c")]:
        try:
            m.link(a, b)  # portals between the walkable pieces (flat) and between lava pools that touch
        except AssertionError:
            pass
    for walk in ["ledge", "c_s", "c_n", "br_w", "br_e", "isle_w", "isle_e"]:  # a chain railing on every walkable edge that looks onto lava
        for v in lava:
            try:
                m.railing(walk, v, "dn_rail")
            except AssertionError:
                pass
    # (lava_w_b and lava_e_b are small pools walled in by the bridge, the island, the causeway and the cliff: a void needs no portal to be drawn)
    # ---- the stations
    add_home(m, HOME_F, "ledge", {"floor": "dn_floor_slab", "tint": "#ffd8a0", "ceil": "dn_ceil", "wall": "dn_wall_cave", "hatch": "dn_hatch", "window": "dn_window"}, "dino_arrive")
    add_stage(m, STAGE_F, "c_n", {"floor": "dn_floor_stone", "tint": "#ffa868", "dais": "dn_floor_tower", "dais_tint": "#ffc890", "ceil": "dn_ceil", "wall": "dn_wall_tower", "trim": "dn_wall_step",
                                  "deck_sprite": "dn_deck", "arch": "dn_ribs", "spk_l": "dn_pillar", "spk_r": "dn_pillar", "woofer": "dn_drum", "pieces": PIECES, "lt_a": "#ff6a2a", "lt_b": "#3fd0b0",
                                  "dj": ("tentacle", "a"), "dancers": [("blob", "b"), ("cyclops", "a"), ("grey", "a")], "glow": "dn_glow"})
    add_cloak(m, CLOAK_F, "isle_w", {"floor": "dn_floor_cave", "tint": "#d8a870", "ceil": "dn_ceil", "wall": "dn_wall_cave", "counter": "dn_desk", "rail": "dn_rack", "cabinet": "dn_cabinet",
                                     "hatch_decal": "dn_gate", "lt": "#ffb868", "glow": "dn_glow"},
              [("antenna", "a"), ("grey", "b"), ("insect", "a"), ("blob", "b"), ("cyclops", "b"), ("tentacle", "a"), ("grey", "a"), ("insect", "b")], ("cyclops", "a"))
    add_bar(m, BAR_F, "isle_e", {"floor": "dn_floor_cave", "tint": "#ffb060", "ceil": "dn_ceil", "wall": "dn_wall_rock", "counter": "dn_counter", "cabinet": "dn_cabinet", "screen": "dn_rune",
                                 "window_a": "dn_window", "window_b": "dn_tent", "lt": "#ff9a3a", "glow": "dn_glow"},
            ("blob", "a"), ("antenna", "b"), [("b1", "insect", "a", 20.0, 2.6), ("b2", "cyclops", "b", 19.2, 3.4)], floor=0.3)
    add_race(m, RACE_F, "isle_w", {"floor": "dn_floor_stone", "tint": "#b8e898", "ceil": "dn_ceil", "wall": "dn_wall_jungle", "door": "dn_gate", "side_a": "dn_window", "side_b": "dn_window",
                                   "vehicle": "dn_jeep", "console": "dn_console", "lt": "#a8e888", "vehicle_size": 1.0, "door_size": 2.6, "glow": "dn_glow"}, ("insect", "b"), D=5.0, w0=1.3, w1=1.6)
    # ---- waypoints (the stations' own were placed above)
    m.wp("hub_view", HUB_AT, 0.0, "ledge", choice_view=True)
    m.wp("cause_a", [0.0, 5.5], 0.0, "c_s")
    m.wp("cause_c", [0.0, -9.5], 0.0, "c_n")
    m.wp("br_w", [-4.5, -9.5], 90.0, "br_w")
    m.wp("br_e", [4.5, -9.5], -90.0, "br_e")
    m.wp("isle_w_s", [-10.0, -9.5], 90.0, "isle_w")
    m.wp("isle_e_s", [10.0, -9.5], -90.0, "isle_e")
    # ---- the walls: cliffs with lava falls and fossils, torches, the gong
    for i, x in enumerate((-15.0, -8.0, 8.0, 15.0)):
        m.decal_at("hub_fossil_%d" % i, "dn_fossil", [x, 21.985], 0.0, 1.0, 1.6)
    for i, x in enumerate((-17.5, 17.5)):
        m.decal_at("hub_window_%d" % i, "dn_window", [x, 21.985], 0.0, 1.4, 1.8)
    m.decal_at("hub_lava_l", "dn_lavafall", [-11.5, 21.985], 0.0, 0.0, 4.4)
    m.decal_at("hub_lava_r", "dn_lavafall", [11.5, 21.985], 0.0, 0.0, 4.4)
    m.decal_at("west_fossil", "dn_fossil", [-19.985, 14.0], -90.0, 1.2, 1.6)
    m.decal_at("east_fossil", "dn_fossil", [19.985, 14.0], 90.0, 1.2, 1.6)
    m.decal_at("west_window", "dn_window", [-19.985, 18.0], -90.0, 1.4, 1.8)
    m.decal_at("east_window", "dn_window", [19.985, 18.0], 90.0, 1.4, 1.8)
    # ---- things: foliage, a skeleton, eggs, bones, torches, the gong, lanterns
    for i, (x, z) in enumerate([(-17.0, 12.0), (17.0, 12.0), (-13.0, 19.5), (13.0, 19.5), (-8.0, 10.0), (8.0, 10.0)]):
        m.bb("fern_%d" % i, "dn_fern", [x, z], 1.5, y=0.75)
    for i, (x, z) in enumerate([(-18.0, 16.0), (18.0, 16.0), (-18.0, 10.0), (18.0, 10.0)]):
        m.bb("palm_%d" % i, "dn_palm", [x, z], 4.0, y=2.0)
    m.bb("skeleton", "dn_skeleton", [-9.0, 14.0], 3.4, y=1.7)
    m.bb("nest", "dn_egg", [9.5, 13.5], 1.0, y=0.5)
    m.bb("nest_b", "dn_egg", [-4.0, 20.0], 0.8, y=0.4)
    for i, (x, z) in enumerate([(-3.4, 6.0), (3.4, 6.0), (-3.4, -6.5), (3.4, -6.5), (-3.4, -14.0), (3.4, -14.0)]):
        m.bb("torch_%d" % i, "dn_torch", [x, z], 2.2, y=1.1, anim="pulse")
        m.bb("torch_glow_%d" % i, "dn_glow", [x, z], 2.0, y=2.2, anim="pulse", blend="add")
    m.bb("gong", "dn_gong", [14.0, -12.0], 1.9, y=0.95)
    m.bb("bones_w", "dn_bones", [-8.0, -3.5], 1.7, y=0.85)
    m.bb("bones_e", "dn_bones", [8.0, -3.5], 1.7, y=1.15)
    m.bb("crate_e", "dn_crate", [18.0, -3.0], 0.9, y=0.45)
    m.bb("fern_w", "dn_fern", [-18.5, -3.0], 1.4, y=0.7)
    for i, (x, z, y) in enumerate([(-8.0, 12.0, 4.0), (8.0, 12.0, 4.0), (0.0, 10.0, 5.0), (-14.0, -6.0, 3.6), (14.0, -6.0, 3.6)]):
        m.bb("lantern_%d" % i, "dn_lantern", [x, z], 1.2, y=y)
        m.bb("lantern_glow_%d" % i, "dn_glow", [x, z], 2.4, y=y, anim="pulse", blend="add")
    m.bb("glow_ledge", "dn_glow", [0.0, 14.0], 5.0, y=0.5, anim="pulse", blend="add")
    m.light("lt_lava_a", [-10.0, 3.0], 1.0, 12.0, "#ff5a2a", 1.3)
    m.light("lt_lava_b", [10.0, 3.0], 1.0, 12.0, "#ff5a2a", 1.3)
    m.light("lt_lava_c", [0.0, -6.0], 1.0, 9.0, "#ff6a2a", 1.0)
    m.light("lt_hub", [0.0, 15.0], 3.6, 11.0, "#ffd0a0", 1.1)
    m.light("lt_isle_w", [-13.0, -9.0], 3.0, 8.0, "#d8ffa0", 0.9)
    m.light("lt_isle_e", [13.0, -9.0], 3.0, 8.0, "#ffc070", 0.9)
    # ---- the people: the ledge and the causeway are the dance floor
    spots = []
    for i in range(14):
        spots.append(("ledge", [-15.0 + (i % 7) * 5.0 + (i // 7) * 2.0, 11.0 + (i // 7) * 4.4 + (i % 3) * 0.7]))
    spots += [("c_s", [-1.4, 4.5]), ("c_s", [1.3, 2.0]), ("c_s", [-1.0, -1.0]), ("c_n", [1.4, -5.0]), ("c_n", [-1.2, -8.0]), ("c_n", [1.2, -13.0])]
    spots += [("isle_w", [-8.0, -6.0]), ("isle_w", [-12.0, -4.0]), ("isle_w", [-16.0, -6.5]), ("isle_e", [8.0, -6.0]), ("isle_e", [12.0, -4.0]), ("isle_e", [17.0, -6.5])]
    kinds = [("grey", "a"), ("antenna", "a"), ("blob", "b"), ("insect", "a"), ("cyclops", "b"), ("tentacle", "b"), ("grey", "b"), ("antenna", "b"), ("blob", "a"), ("insect", "b"), ("cyclops", "a")]
    add_crowd(m, spots, kinds)
    return m


# ---------------------------------------------------------------------------------------------------------------------------------------- theme file, story
def theme_spec():
    props = [
        {"id": "deck", "role": "stage_deck", "sprite": "dn_deck", "spot": "deck_view"},
        {"id": "bass_knob", "role": "bass_knob", "sprite": "dn_knob_0", "spot": "deck_view"},
        {"id": "coat_gate", "role": "cloakroom", "sprite": "dn_gate", "spot": "cloak_view"},
        {"id": "bar_counter", "role": "bar", "sprite": "dn_counter", "spot": "bar_view"},
        {"id": "garage_gate", "role": "race_entrance", "sprite": "dn_gate", "spot": "hangar_view"},
        {"id": "home_hatch", "role": "home_threshold", "sprite": "dn_hatch", "spot": "home_door"},
        {"id": "torches", "role": "decor", "sprite": "dn_torch", "at": [0.0, 0.0]},
    ]
    guides = [
        {"id": "dj", "sprite": "rave_dinos/tentacle_a", "spot": "deck_view", "for": "stage"},
        {"id": "attendant", "sprite": "rave_dinos/cyclops_a", "spot": "cloak_view", "for": "cloakroom"},
        {"id": "bartender", "sprite": "rave_dinos/blob_a", "spot": "bar_view", "for": "bar"},
        {"id": "pilot", "sprite": "rave_dinos/insect_b", "spot": "hangar_view", "for": "race"},
        {"id": "home_hatch", "sprite": "dn_hatch", "spot": "home_door", "for": "home"},
    ]
    routes = {
        "stage": route(MAP_ID, "hub_view", [leg("cause_c", 4, 1, via=["cause_a"]), leg("stage_foot", 2, 1, "deck"), leg("stage_steps", 2, 1, "deck"), leg("deck_view", 2, 4, "deck")], "deck_view"),
        "cloak": route(MAP_ID, "hub_view", [leg("cause_c", 4, 1, via=["cause_a"]), leg("cloak_door", 2, 1, via=["br_w", "isle_w_s"]), leg("cloak_hold", 2, 4, "attendant")], "cloak_hold"),
        "bar": route(MAP_ID, "hub_view", [leg("cause_c", 4, 1, via=["cause_a"]), leg("bar_door", 2, 1, via=["br_e", "isle_e_s"]), leg("bar_hold", 2, 4, "bartender")], "bar_hold"),
    }
    return {
        "id": "dinos", "prefix": "dino", "scene_id": "dino_rave", "geography": "doom_underworld", "arrival": "dino_arrive", "props": props, "guides": guides, "routes": routes,
        "customers": [{"id": "dinos_floor", "sprite_set": "rave_dinos/clubgoers", "count": 26, "spot": "cause_a"}, {"id": "dinos_queue", "sprite_set": "rave_dinos/clubgoers", "count": 3, "spot": "cloak_view"}],
        "ingredients": [{"id": "fern_juice", "icon": "dinos/ing_fern", "color": "#4fc760"}, {"id": "lava_sauce", "icon": "dinos/ing_lava", "color": "#ff5a2a"},
                        {"id": "amber_resin", "icon": "dinos/ing_amber", "color": "#ffb52e"}, {"id": "egg_cream", "icon": "dinos/ing_egg", "color": "#fff1d0"}],
        "cloakroom_symbols": [{"id": "egg", "icon": "dinos/sym_egg"}, {"id": "claw", "icon": "dinos/sym_claw"}, {"id": "fern", "icon": "dinos/sym_fern"}, {"id": "skull", "icon": "dinos/sym_skull"}],
    }


PALETTES = {"low": ["#5a1a0a", "#2a5a3a"], "cool": ["#3fd0b0", "#6ad850"], "warm": ["#ffc23f", "#ff4a1a"], "rave": ["#ff4a1a", "#ffc23f", "#6ad850", "#3fd0b0"]}


def main(argv) -> int:
    art = build_art()
    arche = rave_people.build("dinos", art.name)
    place_activity_sheets(art.name, "dinos", os.path.join(art.tex, "dn_knob_sheet.png"))
    ra.write_manifest(art, arche, TEXTURES + ["dn_sky"], [ra.piece_entry(PIECES[0], PIECES[0]), ra.piece_entry(PIECES[1], PIECES[1]), ra.piece_entry(PIECES[2], PIECES[2]), ra.piece_entry(AMBIENT, AMBIENT)])
    m = build_map(art)
    out = m.to_json()
    write(MAP, out)
    write(STORY, story_json(m.actors, "dino_rave", "The Dinosaur Rave", art.name, "The Ledge", AMBIENT, PALETTES, "A rave over the lava (docs/briefs/BEDSIT_RAVES_BRIEF.md section 3): a path's world, not a Story Campaign chapter."))
    write(THEME_FILE, theme_json(theme_spec()))
    write_activity_layouts("dinos", CLOAK_F, BAR_F, "rave_dinos")
    bearings = hub_bearings(m, HUB_AT, 0.0, ["dj", "attendant", "bartender", "pilot", "customer_0", "customer_7"])
    print("wrote %s (%d sectors, %d things, %d waypoints); hub bearings %s" % (MAP, len(out["sectors"]), len(out["things"]), len(out["waypoints"]), bearings))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
