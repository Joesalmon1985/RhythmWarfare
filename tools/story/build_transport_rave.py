#!/usr/bin/env python3
"""Builds the Transport rave (docs/briefs/BEDSIT_RAVES_BRIEF.md sections 3 and 4; theme id `transport`, scene prefix `transport`, facing WEST): its map content/story/maps/transport_rave.json,
its story file content/story/transport_rave.json, its theme file content/raves/transport.json, the activity layouts in content/bedsit/themes.json (cloakroom.transport.layout,
bar.transport.layout) and the art folder assets/story/rave_transport/ (textures, the activities' sheets, the clubgoers' rigs, the manifest).

    python3 tools/story/build_transport_rave.py

THE PLACE. The Dock (content/story/maps/doom_dock.json on feature/doom-layout-worlds; the painting art/reference/standard/dock_three_paths.webp: a rain-slick asphalt forecourt, yellow bollards,
a warehouse whose roller shutter is up on a purple-lit crowd, sodium lamps, wet reflections) is the geography; this map is a hand-built, approximate version at rave scale, not a conversion: you
arrive on a wet street FORECOURT open to the rain, cross a pair of railway TRACKS sunk a step into the ground, and go in under the roof of a long DEPOT hall. The stage is a loading dock at the
hall's north end with a locomotive's face behind the DJ; the cloakroom is a left-luggage BAY off the west wall, the bar a ticket-office BAY off the east wall, and the GARAGE (the race entrance)
stands beside the stage. Where the Space rave is a ring, the Magic one a bowl and the Dinosaur one a causeway over lava, this is a street-to-shed T: a narrow open yard into a wide roofed hall,
the side bays branching off the hall's long walls. Tiles borrowed from the Dock (asphalt, concrete, brick, steel, shutters, truss roof, bollard, lamps, crates, van, pallets) are used as they are;
everything else (the tracks, the locomotive, the shutter onto the crowd, the bus, the racer, the departures board, the signals, the counters, the lockers, the hi-vis rail, the sky) is drawn here
and is a PLACEHOLDER (ruling 36: the painting is the bar; these are procedural, not hand-finished).

  compass: north is -z. The stage's frame is the same in every rave (phi 180, origin 0): the deck is at (0, -25.2), which is where the bass knob activity puts the knob.
  forecourt (yard) x -9..9, z 4..18, open to the sky and the rain; the way home is a bus-stop door in a shallow alcove behind it (sector `home`, z 18..23)
  tracks x -13..13, z 0..4, floor -0.2 (a step down and up), open      depot hall x -13..13, z -17..0, a truss roof at 9 m
  stage (phi 180) z -17..-28      garage (phi 180, x 9.5) z -17..-22.5      cloakroom bay (phi 270) x -13..-19, z about -10      bar bay (phi 90) x 13..19, z about -10
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rave_builder import (ROOT, Frame, RaveMap, add_bar, add_cloak, add_crowd, add_home, add_race, add_stage, hub_bearings, leg, place_activity_sheets, rect, route, story_json,  # noqa: E402
                          theme_json, write, write_activity_layouts, QUIET, STANDING)
import rave_art as ra  # noqa: E402
import rave_people  # noqa: E402
from art import pixeltex as px  # noqa: E402
from art.bedsit_draw import Cv, ramp  # noqa: E402

MAP_ID = "transport_rave"
MAP = os.path.join(ROOT, "content", "story", "maps", "transport_rave.json")
STORY = os.path.join(ROOT, "content", "story", "transport_rave.json")
THEME_FILE = os.path.join(ROOT, "content", "raves", "transport.json")
BORROWED = os.path.join(HERE, "borrowed", "doom_dock")  # tiles copied once from assets/story/doom_dock on feature/doom-layout-worlds (tools/story/borrowed/.gdignore keeps Godot out)

STAGE_F = Frame(180)
RACE_F = Frame(180, (9.5, 0.0))       # the garage: beside the stage, its mouth on the hall's north wall
CLOAK_F = Frame(270, (4.0, -10.0))    # the left-luggage bay: mouth on the hall's west wall (x -13)
BAR_F = Frame(90, (-4.0, -10.0))      # the ticket-office bar: mouth on the hall's east wall (x 13)
HOME_F = Frame(0, (0.0, 1.0))         # the bus-stop door: behind the forecourt (mouth z 18)
HUB_AT = [0.0, 15.0]

TEXTURES = ["tr_floor_asphalt", "tr_floor_conc", "tr_floor_walk", "tr_floor_blue", "tr_floor_rails", "tr_floor_dock", "tr_wall_brick", "tr_wall_steel", "tr_wall_ware", "tr_wall_shutter",
            "tr_wall_blue", "tr_wall_tile", "tr_trim", "tr_ceil_truss", "tr_bollard", "tr_street_lamp", "tr_hang_lamp", "tr_wall_lamp", "tr_neon", "tr_crate", "tr_case", "tr_drum", "tr_pallet",
            "tr_pallet_stack", "tr_van", "tr_fence", "tr_windows", "tr_towers", "tr_shutter_rave", "tr_loco", "tr_bus", "tr_racer", "tr_signal", "tr_board", "tr_garage_door", "tr_timetable",
            "tr_luggage", "tr_counter", "tr_desk", "tr_lockers", "tr_rack", "tr_console", "tr_deck", "tr_hatch", "tr_cone", "tr_glow", "tr_knob_0", "tr_knob_1", "tr_knob_2", "tr_knob_3",
            "pc_glass_lit", "pc_lamp_lit"]
PIECES = ("tr_signal_beams", "tr_track_lights", "tr_headlamp_dome")
AMBIENT = "tr_ambient"
SODIUM, AMBER, HIVIS, LIME, PURPLE, CYAN, RED, YELLOW = "#ffab4a", "#ffc23f", "#ff8a1f", "#b8f020", "#a04cff", "#5ad8ff", "#ff3a2a", "#f0d020"
OUTLINE = "#12101c"


# ---------------------------------------------------------------------------------------------------------------------------------------- placeholder art: tiles
def rails_tile() -> np.ndarray:
    """Two railway tracks' worth of ballast across a 2 m tile: grey-brown chippings, timber sleepers across (along z), two steel rails along x with a wet highlight."""
    x, y = ra.grid()
    sh = px.noise(ra.N, 3, 41, 3) * 0.7 + px.noise(ra.N, 14, 42) * 0.3
    out = ra.q(sh, ramp("#1a1a20", "#34343c", "#55525a", "#7a746e"))
    sleeper = ((x % 32) >= 4) & ((x % 32) < 20) & (y >= 10) & (y < 118)
    grain = px.noise(ra.N, 18, 43)
    sl = ra.q(0.35 + (grain - 0.5) * 0.4 + 0.15 * ((x % 32) - 4 < 3), ramp("#1c120c", "#3a2618", "#5a3c24", "#7a5636"))
    out[sleeper] = sl[sleeper]
    for r in (28, 100):  # the rails (a 1.435 m gauge is 92 px at 64 px a metre: 28 and 100 are 72 px apart, a scaled track that reads)
        head = (y >= r - 3) & (y <= r + 3)
        rail = ra.q(0.25 + 0.6 * np.clip(1 - np.abs(y - (r - 1.5)) / 3.0, 0, 1), ramp("#2a2a30", "#5a5a66", "#9a9aa8", "#e8f0ff"))
        out[head] = rail[head]
        shadow = (y == r + 4)
        out[shadow] = (px.hexc("#0c0c10") * 255).astype(np.uint8)
    chair = (((x % 32) >= 4) & ((x % 32) < 20)) & (((np.abs(y - 28) <= 5) & (np.abs(y - 28) > 3)) | ((np.abs(y - 100) <= 5) & (np.abs(y - 100) > 3)))
    out[chair] = (px.hexc("#4a3a30") * 255).astype(np.uint8)
    return out


def tile_wall() -> np.ndarray:
    """Old station wall tiles: cream glazed bricks with a green band and grime (2 m)."""
    x, y = ra.grid()
    row = (y // 8).astype(int)
    off = np.where(row % 2 == 0, 0, 8)
    grout = ((y % 8) == 0) | (((x + off) % 16) == 0)
    sh = 0.62 + (px.noise(ra.N, 10, 51) - 0.5) * 0.25 - np.clip((y - 96) / 64.0, 0, 1) * 0.25
    gloss = ((y % 8) == 2) & (((x + off) % 16) > 2) & (((x + off) % 16) < 10)
    out = ra.q(sh, ramp("#5a5444", "#a89c80", "#d8ccaa", "#f4ead0"))
    band = (y >= 72) & (y < 88)
    out[band] = ra.q(0.5 + (px.noise(ra.N, 8, 52) - 0.5) * 0.3, ramp("#0c2a1c", "#1a4a30", "#2a6a44", "#4a9a68"))[band]
    out[gloss & ~band] = (px.hexc("#fffaf0") * 255).astype(np.uint8)
    out[grout] = (px.hexc("#3a3428") * 255).astype(np.uint8)
    return out


def dock_floor() -> np.ndarray:
    """The loading dock's steel deck: chequer plate with a yellow and black edge stripe at the top (2 m)."""
    x, y = ra.grid()
    sh = 0.45 + (px.noise(ra.N, 6, 61) - 0.5) * 0.2
    out = ra.q(sh, ramp("#1a1c22", "#34383f", "#565c66", "#8a92a0"))
    stud = (((x + (y // 8 % 2) * 4) % 8) < 3) & ((y % 8) < 2)
    out[stud] = (px.hexc("#9aa2b0") * 255).astype(np.uint8)
    stripe = y < 14
    hazard = ((x + y) // 10) % 2 == 0
    out[stripe & hazard] = (px.hexc(YELLOW) * 255).astype(np.uint8)
    out[stripe & ~hazard] = (px.hexc("#14141a") * 255).astype(np.uint8)
    return out


# ---------------------------------------------------------------------------------------------------------------------------------------- placeholder art: the big pictures (the 256 px class)
def shutter_rave() -> Cv:
    """The painting's picture: a warehouse wall with its roller shutter two thirds up on a purple-lit crowd, a caged lamp over it, a yellow bollard at each side."""
    c = Cv(256, 192)
    c.paint(c.rect(0, 0, 256, 192), ramp("#14161e", "#262a34", "#3a404c", "#565e6c"), c.lit((0, 0, 256, 192), 0.5, 0.3, noise=0.25, seed=3), edge=False)
    for k in range(0, 256, 32):  # wall panel seams and rust
        c.flat(c.rect(k, 0, k + 1, 192), "#0e1016")
    c.paint(c.rect(40, 40, 216, 192), ramp("#120a24", "#2a1450", "#5a2a9a", "#b070ff"), c.lit((40, 40, 216, 192), 0.55, -0.35), edge=False)
    for k, (bx, sw) in enumerate([(70, 18), (110, 12), (150, 22), (190, 14)]):  # the lights' beams from the roof inside
        c.tint(c.poly([(bx, 40), (bx + 6, 40), (bx + sw + 24, 192), (bx - sw - 10, 192)]), ["#ff4fd8", "#7ad8ff", "#c890ff", "#ff9ae0"][k], 0.35)
    rng = np.random.RandomState(5)
    for k in range(26):  # the crowd in silhouette, heads and raised arms against the light
        hx = 44 + k * 6.6 + rng.randint(-2, 3)
        hy = 140 + rng.randint(-8, 9)
        c.flat(c.ell(hx - 5, hy - 6, hx + 5, hy + 5), "#0c0618")
        c.flat(c.rect(hx - 7, hy + 4, hx + 7, 192), "#0c0618")
        if k % 4 == 1:
            c.flat(c.poly([(hx + 3, hy), (hx + 6, hy), (hx + 12, hy - 22), (hx + 9, hy - 23)]), "#0c0618")
    for yy in range(4, 40, 4):  # the rolled-up shutter
        c.paint(c.rect(36, yy, 220, yy + 4), ramp("#2a2e38", "#4a505c", "#7a8290", "#b8c0cc"), c.round_y(yy, yy + 4, 0.55, 0.6), edge=False)
    c.flat(c.rect(36, 36, 220, 40), "#0a0a10")
    c.flat(c.rect(30, 30, 36, 192), "#1a1c24")
    c.flat(c.rect(220, 30, 226, 192), "#1a1c24")
    c.paint(c.rrect(116, 6, 140, 18, 3), ramp("#5a3a10", "#c88a2a", "#ffd27a", "#fff8d8"), c.lit((116, 6, 140, 18), 0.7, 0.4), edge_col=OUTLINE)  # the caged lamp
    c.tint(c.poly([(116, 18), (140, 18), (170, 40), (86, 40)]), "#ffd27a", 0.25)
    for bx in (12, 232):  # bollards
        c.paint(c.rrect(bx, 132, bx + 14, 192, 4), ramp("#5a4a08", "#b8960c", "#f0d020", "#fff6a0"), c.round_x(bx, bx + 14), edge_col=OUTLINE)
        c.flat(c.rect(bx, 150, bx + 14, 156), "#1a1a1a")
    floor_glow = c.rect(40, 186, 216, 192)
    c.tint(floor_glow, "#d08aff", 0.5)
    return c


def loco() -> Cv:
    """The face of a diesel locomotive behind the DJ: a yellow warning panel, two cab windows, the headlamps, buffers and a number plate."""
    c = Cv(256, 256)
    body = ramp("#3a0c0c", "#8a1a14", "#c8382a", "#ff8a6a")
    c.paint(c.poly([(30, 40), (226, 40), (240, 230), (16, 230)]), body, c.lit((16, 40, 240, 230), 0.5, 0.35, noise=0.2, seed=9), edge_col=OUTLINE)
    c.paint(c.poly([(46, 20), (210, 20), (226, 44), (30, 44)]), ramp("#1a1a20", "#3a3a44", "#5a5a66", "#8a8a98"), c.lit((30, 20, 226, 44), 0.55, 0.4), edge_col=OUTLINE)  # the roof
    c.paint(c.poly([(40, 132), (216, 132), (232, 230), (24, 230)]), ramp("#6a5a08", "#c8a810", "#f0d020", "#fff6a0"), c.lit((24, 132, 232, 230), 0.55, 0.3), edge_col=OUTLINE)  # warning panel
    for x0, x1 in ((50, 120), (136, 206)):  # the cab windows, the rave's light in them
        c.paint(c.poly([(x0, 56), (x1, 56), (x1 + 4, 116), (x0 - 4, 116)]), ramp("#0a1028", "#1a2a5a", "#3a5aa8", "#9ac8ff"), c.lit((x0, 56, x1, 116), 0.6, -0.5), edge_col=OUTLINE)
        c.flat(c.poly([(x0 + 8, 62), (x0 + 16, 62), (x0 + 4, 104), (x0 - 2, 104)]), "#d8ecff")
    c.flat(c.rect(124, 56, 132, 118), "#2a0a0a")
    for cx in (64, 192):  # headlamps
        c.paint(c.ell(cx - 18, 150, cx + 18, 186), ramp("#8a6a20", "#ffd27a", "#fff4c0", "#ffffff"), c.dome(cx - 4, 162, 18, 18, 0.7, 0.5), edge_col=OUTLINE)
        c.flat(c.ell(cx - 6, 158, cx + 2, 166), "#ffffff")
    c.paint(c.ell(116, 148, 140, 172), ramp("#5a0a0a", "#c81a1a", "#ff5a4a", "#ffd0c8"), c.dome(124, 156, 12, 12, 0.6, 0.5), edge_col=OUTLINE)  # the marker lamp
    c.flat(c.rrect(96, 196, 160, 214, 3), "#14141a", edge=True, edge_col="#c8c8d0")  # the number plate
    for k in range(5):
        c.flat(c.rect(104 + k * 11, 201, 110 + k * 11, 209), "#e8e8f0")
    for bx in (20, 212):  # buffers
        c.paint(c.ell(bx, 214, bx + 24, 238), ramp("#1a1a20", "#3a3a44", "#7a7a88", "#c8c8d8"), c.dome(bx + 8, 222, 12, 12), edge_col=OUTLINE)
    c.flat(c.rect(0, 238, 256, 256), "#14141a")
    return c


def bus() -> Cv:
    """A red double-decker, side on, its windows lit, parked in the rain."""
    c = Cv(256, 160)
    body = ramp("#3a0808", "#8a1410", "#d02a1a", "#ff7a5a")
    c.paint(c.rrect(4, 8, 252, 140, 14), body, c.lit((4, 8, 252, 140), 0.52, 0.35, noise=0.15, seed=12), edge_col=OUTLINE)
    glass = ramp("#2a1a08", "#7a5a20", "#ffc860", "#fff4c8")
    for row, (y0, y1) in enumerate(((18, 54), (74, 108))):
        for k in range(6):
            x0 = 14 + k * 38
            c.paint(c.rrect(x0, y0, x0 + 32, y1, 3), glass, c.lit((x0, y0, x0 + 32, y1), 0.65, 0.4), edge_col=OUTLINE)
            if (k + row) % 3 == 0:  # a passenger's head in the window
                c.flat(c.ell(x0 + 10, y1 - 22, x0 + 22, y1 - 8), "#3a2410")
    c.flat(c.rect(4, 60, 252, 66), "#f0e0c0")  # the cream band
    c.flat(c.rrect(200, 112, 238, 138, 2), "#14141a", edge=True, edge_col="#c8c8d0")  # the doors
    c.flat(c.rrect(14, 112, 120, 128, 2), "#ffd23f")  # the route blind
    for k in range(5):
        c.flat(c.rect(22 + k * 18, 116, 32 + k * 18, 124), "#1a1408")
    for cx in (52, 204):
        c.paint(c.ell(cx - 18, 122, cx + 18, 158), ramp("#08080c", "#1a1a20", "#3a3a44", "#6a6a78"), c.dome(cx, 140, 18, 18), edge_col=OUTLINE)
        c.flat(c.ell(cx - 6, 134, cx + 6, 146), "#a8a8b8")
    c.flat(c.rect(244, 96, 252, 110), "#fff4c0")  # a headlamp
    return c


def racer() -> Cv:
    """The garage's racer: a low hatchback with a chequered stripe and a roof number, nose to the right."""
    c = Cv(256, 128)
    body = ramp("#0a2a3a", "#16587a", "#2a9ad0", "#a8f0ff")
    c.paint(c.poly([(8, 98), (14, 64), (66, 50), (100, 22), (176, 20), (214, 50), (248, 62), (250, 98)]), body, c.lit((8, 20, 250, 98), 0.52, 0.45, noise=0.1, seed=17), edge_col=OUTLINE)
    c.paint(c.poly([(106, 28), (172, 26), (204, 52), (92, 54)]), ramp("#081018", "#1a2a40", "#4a6a98", "#c8e0ff"), c.lit((92, 26, 204, 54), 0.6, -0.4), edge_col=OUTLINE)
    c.flat(c.rect(146, 26, 150, 54), "#0a1a28")
    for k in range(14):  # the chequered stripe
        for r in range(2):
            col = "#f4f4f4" if (k + r) % 2 == 0 else "#14141a"
            c.flat(c.rect(16 + k * 16, 70 + r * 6, 32 + k * 16, 76 + r * 6), col)
    c.flat(c.ell(118, 4, 154, 22), "#f4f4f4", edge=True, edge_col=OUTLINE)  # the roof roundel
    c.flat(c.rect(130, 8, 134, 18), "#14141a")
    c.flat(c.rect(138, 8, 142, 18), "#14141a")
    c.flat(c.rect(236, 66, 250, 76), "#fff8c8")  # headlamp
    c.flat(c.rect(8, 66, 16, 76), "#ff3a2a")  # tail lamp
    for cx in (60, 200):
        c.paint(c.ell(cx - 22, 82, cx + 22, 126), ramp("#08080c", "#1a1a20", "#3a3a44", "#6a6a78"), c.dome(cx, 104, 22, 22), edge_col=OUTLINE)
        c.paint(c.ell(cx - 10, 94, cx + 10, 114), ramp("#5a5a66", "#9a9aa8", "#d8d8e8", "#ffffff"), c.dome(cx - 3, 100, 10, 10), edge_col=OUTLINE)
    return c


def signal() -> Cv:
    """A railway colour-light signal on a post: a black head with three lamps (red lit), a white-edged backboard."""
    c = Cv(64, 192)
    c.paint(c.rect(28, 70, 36, 192), ramp("#1a1a20", "#3a3a44", "#6a6a78", "#a8a8b8"), c.round_x(28, 36), edge_col=OUTLINE)
    c.flat(c.rrect(6, 4, 58, 92, 8), "#f4f4f4", edge=True, edge_col=OUTLINE)
    c.flat(c.rrect(12, 10, 52, 86, 6), "#14141a")
    for k, (col, lit) in enumerate([("#ff3a2a", True), ("#ffc23f", False), ("#3aff7a", False)]):
        y = 14 + k * 24
        if lit:
            c.paint(c.ell(20, y, 44, y + 20), ramp("#6a0a0a", "#d81a1a", "#ff6a5a", "#fff0e8"), c.dome(28, y + 7, 12, 10, 0.75, 0.5), edge=False)
        else:
            c.flat(c.ell(20, y, 44, y + 20), px_mix(col, "#000000", 0.75))
    c.flat(c.rect(20, 180, 44, 192), "#3a3a44")
    return c


def px_mix(a: str, b: str, t: float) -> str:
    ca, cb = px.hexc(a), px.hexc(b)
    m = ca * (1 - t) + cb * t
    return "#%02x%02x%02x" % tuple(int(v * 255) for v in m)


def board() -> Cv:
    """A departures board: amber dot-matrix rows on black in a steel frame, a clock on top."""
    c = Cv(192, 96)
    c.paint(c.rrect(0, 14, 192, 96, 4), ramp("#1a1c22", "#3a3e48", "#6a707e", "#a8b0c0"), c.lit((0, 14, 192, 96), 0.5, 0.4), edge_col=OUTLINE)
    c.flat(c.rect(6, 20, 186, 90), "#08080a")
    rng = np.random.RandomState(23)
    for r in range(6):
        y = 25 + r * 11
        x = 10
        while x < 180:
            w = rng.randint(4, 14)
            if rng.rand() < 0.8:
                for xx in range(x, min(x + w, 180), 2):
                    for yy in range(y, y + 6, 2):
                        if rng.rand() < 0.75:
                            c.dots([(xx, yy)], AMBER if r % 3 else "#fff0a0")
            x += w + 4
    c.paint(c.ell(80, 0, 112, 30), ramp("#c8c8d0", "#e8e8f0", "#f8f8ff", "#ffffff"), c.dome(92, 10, 16, 15, 0.7, 0.3), edge_col=OUTLINE)
    c.flat(c.line((96, 15), (96, 5), 2), OUTLINE)
    c.flat(c.line((96, 15), (104, 15), 2), OUTLINE)
    return c


def garage_door() -> Cv:
    """The garage's roller door, half up on a lit workshop: a lift, a tyre stack, a chequered flag over the opening."""
    c = Cv(256, 192)
    c.paint(c.rect(0, 0, 256, 192), ramp("#14161e", "#262a34", "#3a404c", "#565e6c"), c.lit((0, 0, 256, 192), 0.5, 0.3, noise=0.25, seed=31), edge=False)
    c.paint(c.rect(24, 70, 232, 192), ramp("#2a1a08", "#6a4a1a", "#c8902a", "#ffe0a0"), c.lit((24, 70, 232, 192), 0.6, -0.3), edge=False)
    c.flat(c.rect(24, 180, 232, 192), "#3a2a14")
    for k in range(3):  # tyres
        c.paint(c.ell(40, 150 - k * 14, 76, 166 - k * 14), ramp("#08080c", "#1a1a20", "#3a3a44", "#5a5a66"), c.dome(58, 156 - k * 14, 18, 8), edge_col=OUTLINE)
    c.flat(c.rect(150, 120, 156, 182), "#c8c8d0")
    c.flat(c.rect(196, 120, 202, 182), "#c8c8d0")
    c.flat(c.rect(146, 140, 206, 146), "#ffd23f", edge=True, edge_col=OUTLINE)
    for yy in range(12, 70, 5):
        c.paint(c.rect(20, yy, 236, yy + 5), ramp("#2a2e38", "#4a505c", "#7a8290", "#b8c0cc"), c.round_y(yy, yy + 5, 0.55, 0.6), edge=False)
    for k in range(16):
        for r in range(2):
            c.flat(c.rect(20 + k * 13.5, 2 + r * 5, 20 + (k + 1) * 13.5, 7 + r * 5), "#f4f4f4" if (k + r) % 2 == 0 else "#14141a")
    c.flat(c.rect(14, 0, 20, 192), YELLOW)
    c.flat(c.rect(236, 0, 242, 192), YELLOW)
    return c


def timetable() -> Cv:
    """The way home's sign: a bus-stop flag with a timetable panel (the one pinned on the bedsit's door, grown up)."""
    c = Cv(64, 96)
    c.flat(c.rrect(4, 2, 60, 40, 6), "#e8e8f0", edge=True, edge_col=OUTLINE)
    c.flat(c.ell(14, 6, 50, 36), "#d02a1a")
    c.flat(c.rect(10, 17, 54, 25), "#1a2a8a")
    c.flat(c.rect(8, 46, 56, 94), "#f4f0e0", edge=True, edge_col=OUTLINE)
    for r in range(8):
        c.flat(c.rect(12, 50 + r * 5, 12 + 16 + (r * 7) % 20, 52 + r * 5), "#3a3a44")
    return c


def luggage_hatch() -> Cv:
    """A left-luggage hatch in the bay's back wall: a steel frame, a roller shutter half up on shelves of cases, a yellow number plate."""
    c = Cv(128, 128)
    c.paint(c.rect(0, 0, 128, 128), ramp("#14161e", "#2a2e38", "#4a505c", "#7a8290"), c.lit((0, 0, 128, 128), 0.5, 0.3), edge_col=OUTLINE)
    c.paint(c.rect(12, 40, 116, 116), ramp("#1a1408", "#4a3418", "#8a6430", "#d8a860"), c.lit((12, 40, 116, 116), 0.6, -0.3), edge=False)
    for r, y in enumerate((70, 104)):
        c.flat(c.rect(12, y, 116, y + 4), "#3a3e48")
        for k in range(5):
            x = 16 + k * 20
            col = ["#7a1a2a", "#1a3a6a", "#5a3a14", "#2a5a2a", "#6a1a5a"][(k + r) % 5]
            c.paint(c.rrect(x, y - 22 + (k % 2) * 4, x + 16, y, 2), ramp("#08080c", col, px_mix(col, "#ffffff", 0.35), "#ffffff"), c.lit((x, y - 22, x + 16, y), 0.5, 0.4), edge_col=OUTLINE)
    for yy in range(14, 42, 4):
        c.paint(c.rect(10, yy, 118, yy + 4), ramp("#2a2e38", "#4a505c", "#7a8290", "#b8c0cc"), c.round_y(yy, yy + 4, 0.55, 0.6), edge=False)
    c.flat(c.rrect(48, 2, 80, 12, 2), YELLOW, edge=True, edge_col=OUTLINE)
    c.flat(c.rect(58, 4, 62, 10), "#14141a")
    c.flat(c.rect(66, 4, 70, 10), "#14141a")
    c.flat(c.rect(10, 116, 118, 120), "#c8c8d0")
    return c


def cone() -> Cv:
    c = Cv(48, 64)
    c.paint(c.poly([(20, 4), (28, 4), (42, 56), (6, 56)]), ramp("#7a2a08", "#d8501a", "#ff8a3a", "#ffd0a0"), c.round_x(6, 42), edge_col=OUTLINE)
    c.flat(c.poly([(15, 24), (33, 24), (36, 34), (12, 34)]), "#f4f4f4")
    c.flat(c.rect(2, 56, 46, 63), "#2a2a30", edge=True, edge_col=OUTLINE)
    return c


# ---------------------------------------------------------------------------------------------------------------------------------------- placeholder art: the set
def build_art():
    art = ra.Art("transport")
    art.borrow(BORROWED, {"tr_floor_asphalt": "dk_floor_asphalt", "tr_floor_conc": "dk_floor_conc", "tr_floor_walk": "dk_floor_walk", "tr_floor_blue": "dk_floor_blue",
                          "tr_wall_brick": "dk_wall_brick", "tr_wall_steel": "dk_wall_steel", "tr_wall_ware": "dk_wall_ware", "tr_wall_shutter": "dk_wall_shutter", "tr_wall_blue": "dk_wall_blue",
                          "tr_trim": "dk_trim", "tr_ceil_truss": "dk_ceil_truss", "tr_bollard": "dk_bollard", "tr_street_lamp": "dk_street_lamp", "tr_hang_lamp": "dk_hang_lamp",
                          "tr_wall_lamp": "dk_wall_lamp", "tr_neon": "dk_neon_blue", "tr_crate": "dk_crate", "tr_case": "dk_case", "tr_drum": "dk_drum", "tr_pallet": "dk_pallet",
                          "tr_pallet_stack": "dk_pallet_stack", "tr_van": "dk_van", "tr_fence": "dk_fence", "tr_windows": "dk_windows_lit", "tr_towers": "dk_towers"})
    art.tile("tr_floor_rails", rails_tile())
    art.tile("tr_wall_tile", tile_wall())
    art.tile("tr_floor_dock", dock_floor())
    art.sprite("tr_shutter_rave", shutter_rave())
    art.sprite("tr_loco", loco())
    art.sprite("tr_bus", bus())
    art.sprite("tr_racer", racer())
    art.sprite("tr_signal", signal())
    art.sprite("tr_board", board())
    art.sprite("tr_garage_door", garage_door())
    art.sprite("tr_timetable", timetable())
    art.sprite("tr_cone", cone())
    art.sprite("tr_luggage", luggage_hatch())

    def tickets(cv, y):  # the ticket office's counter top: a ticket machine, a bell, a stack of tickets
        cv.paint(cv.rrect(70, y - 46, 104, y - 2, 4), ramp("#1a2a5a", "#2a4a9a", "#4a7ad8", "#a8c8ff"), cv.lit((70, y - 46, 104, y - 2), 0.55, 0.4), edge_col=OUTLINE)
        cv.flat(cv.rect(76, y - 40, 98, y - 28), "#9affc8")
        cv.flat(cv.rect(80, y - 20, 94, y - 16), "#14141a")
        cv.paint(cv.ell(18, y - 14, 36, y), ramp("#6a5010", "#c8a020", "#ffe070", "#ffffff"), cv.dome(25, y - 9, 9, 7), edge_col=OUTLINE)
        for k in range(3):
            cv.flat(cv.rect(44, y - 6 - k * 3, 62, y - 3 - k * 3), ["#f4e8c8", "#ffc8a0", "#c8e8ff"][k], edge=True, edge_col=OUTLINE)
    art.sprite("tr_counter", ra.counter(128, 128, ("#0a1a2a", "#1a3a5a", "#2a5a8a", "#5a90c8"), "#c8d8e8", front="#14283e", items=tickets))

    def parcels(cv, y):  # the left-luggage desk: a parcel with a label, a suitcase, a brass bell
        cv.paint(cv.rect(16, y - 26, 50, y), ramp("#5a3a14", "#8a5a24", "#c88a40", "#f0c080"), cv.lit((16, y - 26, 50, y), 0.55, 0.4), edge_col=OUTLINE)
        cv.flat(cv.rect(16, y - 15, 50, y - 12), "#e8d8a8")
        cv.flat(cv.rect(26, y - 22, 40, y - 17), "#f4f4f4")
        cv.paint(cv.rrect(60, y - 30, 100, y, 4), ramp("#3a0a14", "#7a1a2a", "#b83048", "#ff7a90"), cv.lit((60, y - 30, 100, y), 0.55, 0.4), edge_col=OUTLINE)
        cv.flat(cv.rect(74, y - 36, 86, y - 30), "#c8a050", edge=True, edge_col=OUTLINE)
        cv.paint(cv.ell(106, y - 12, 122, y), ramp("#6a5010", "#c8a020", "#ffe070", "#ffffff"), cv.dome(112, y - 8, 8, 6), edge_col=OUTLINE)
    art.sprite("tr_desk", ra.counter(128, 128, ("#1a1a20", "#34343e", "#55555f", "#8a8a96"), "#d8c890", front="#2a2a32", items=parcels))

    def lockers(cv, ys):  # left-luggage lockers on the shelves: numbered doors
        for r, y in enumerate(ys):
            for k in range(4):
                x = 12 + k * 18
                cv.paint(cv.rect(x, y - 18, x + 16, y), ramp("#3a4a14", "#5a7a20", "#8ab030", "#c8e870"), cv.lit((x, y - 18, x + 16, y), 0.55, 0.3), edge_col=OUTLINE)
                cv.flat(cv.rect(x + 11, y - 11, x + 13, y - 7), "#f4f4f4")
    art.sprite("tr_lockers", ra.cabinet(96, 128, ("#14161e", "#262a34", "#3a404c", "#565e6c"), YELLOW, lockers))
    art.sprite("tr_rack", ra.rack(128, 128, "#3a3e48", YELLOW, (HIVIS, "#f0e020", LIME, "#ff5a1f", "#e8f4ff"), "vest"))
    art.sprite("tr_console", ra.console(128, 128, ("#14161e", "#2a2e38", "#4a505c", "#7a8290"), CYAN, AMBER))
    art.sprite("tr_deck", ra.deck(96, 56, ("#14161e", "#2a2e38", "#4a505c", "#7a8290"), YELLOW, "#1a1c22", HIVIS, (HIVIS, YELLOW, LIME, CYAN)))
    art.sprite("tr_hatch", ra.hatch_door(48, 84, ("#3a2a08", "#7a5a10", "#d8a020", "#ffe070"), ("#2a1408", "#6a3a14", "#c87a2a", "#ffc070"), SODIUM, glow="#ffd8a0"))
    art.image("tr_glow", ra.piece_glow(SODIUM, 128, 128))
    ra.split_knob(art, ra.knob_sheet(["#14161e", "#2a2e38", "#4a505c", "#8a92a0"], HIVIS, strain=YELLOW, ring_on=LIME, ring_off="#2a2e38"), "tr_knob")
    art.copy_mothership(["pc_glass_lit", "pc_lamp_lit"])
    ra.sky(os.path.join(art.tex, "tr_sky.png"), ["#06080e", "#10141e", "#1e2434", "#3a3448", "#6a4a3a"], 0.0, [(40, 0.7, "#ff8a3a"), (150, 0.5, "#a04cff"), (220, 0.4, "#ff8a3a")], 13,
           bands=[(14, 0.7, "#1a1e28", 20), (26, 0.6, "#2a2a38", 16)])
    art.made["tr_sky"] = (256, 64, 1.0)
    art.image("tr_signal_beams", ra.piece_beams(HIVIS, 4))
    art.image("tr_track_lights", ra.piece_ring(YELLOW, LIME))
    art.image("tr_headlamp_dome", ra.piece_dome("#fff0c0"))
    art.image(AMBIENT, ra.piece_glow(SODIUM))
    return art


# ---------------------------------------------------------------------------------------------------------------------------------------- the map
def build_map(art):
    m = RaveMap("rave_transport", "transport_arrive",
                {"source": "content/story/maps/doom_dock.json", "note": "the Dock (a rain-slick forecourt, a warehouse with its shutter up on the crowd, sodium lamps), approximate: a forecourt, a pair of tracks and a depot hall with three bays"},
                {n: "textures/%s.png" % n for n in TEXTURES}, {"tex": "textures/tr_sky.png", "mode": "cylinder"}, {"color": "#141822", "density": 0.008}, gain=1.6, lgain=1.4)
    kw = dict(step_tex="tr_trim", lip_tex="tr_wall_steel")
    # ---- the forecourt, the tracks and the depot hall
    m.sector("yard", rect(-9, 4, 9, 18), 0.0, 14.0, "tr_floor_asphalt", "sky", 0.5, "#c8b8a0", ["dance_floor"], activities=QUIET, wall_tex="tr_wall_brick", **kw)
    m.sector("tracks", rect(-13, 0, 13, 4), -0.2, 14.0, "tr_floor_rails", "sky", 0.5, "#b8b0a8", [], activities=STANDING, wall_tex="tr_wall_brick", **kw)
    m.sector("hall", rect(-13, -17, 13, 0), 0.0, 9.0, "tr_floor_conc", "tr_ceil_truss", 0.6, "#d8c8b0", ["dance_floor"], activities=QUIET, wall_tex="tr_wall_tile", **kw)
    m.link("yard", "tracks")
    m.link("tracks", "hall")
    # ---- the stations
    add_home(m, HOME_F, "yard", {"floor": "tr_floor_walk", "tint": "#ffd8a8", "ceil": "tr_ceil_truss", "wall": "tr_wall_brick", "hatch": "tr_hatch", "window": "tr_timetable"}, "transport_arrive")
    add_stage(m, STAGE_F, "hall", {"floor": "tr_floor_dock", "tint": "#e8d0b0", "dais": "tr_floor_dock", "dais_tint": "#ffe0b8", "ceil": "tr_ceil_truss", "wall": "tr_wall_steel", "trim": "tr_trim",
                                   "deck_sprite": "tr_deck", "arch": "tr_loco", "spk_l": "tr_signal", "spk_r": "tr_signal", "woofer": "tr_drum", "pieces": PIECES, "lt_a": HIVIS, "lt_b": CYAN,
                                   "dj": ("tentacle", "a"), "dancers": [("blob", "b"), ("cyclops", "a"), ("grey", "a")], "glow": "tr_glow"})
    add_cloak(m, CLOAK_F, "hall", {"floor": "tr_floor_blue", "tint": "#c8d8f0", "ceil": "tr_ceil_truss", "wall": "tr_wall_tile", "counter": "tr_desk", "rail": "tr_rack", "cabinet": "tr_lockers",
                                   "hatch_decal": "tr_luggage", "lt": "#d8e8ff", "glow": "tr_glow"},
              [("antenna", "a"), ("grey", "b"), ("insect", "a"), ("blob", "b"), ("cyclops", "b"), ("tentacle", "a"), ("grey", "a"), ("insect", "b")], ("cyclops", "a"))
    add_bar(m, BAR_F, "hall", {"floor": "tr_floor_walk", "tint": "#ffd0a0", "ceil": "tr_ceil_truss", "wall": "tr_wall_brick", "counter": "tr_counter", "cabinet": "tr_lockers", "screen": "tr_board",
                               "window_a": "tr_windows", "window_b": "tr_windows", "lt": SODIUM, "glow": "tr_glow"},
            ("blob", "a"), ("antenna", "b"), [("b1", "insect", "a", 20.0, 2.6), ("b2", "cyclops", "b", 19.2, 3.4)])
    add_race(m, RACE_F, "hall", {"floor": "tr_floor_conc", "tint": "#d8e8f0", "ceil": "tr_ceil_truss", "wall": "tr_wall_shutter", "door": "tr_garage_door", "side_a": "tr_wall_lamp", "side_b": "tr_wall_lamp",
                                 "vehicle": "tr_racer", "console": "tr_console", "lt": "#e8f4ff", "vehicle_size": 1.6, "door_size": 3.0, "glow": "tr_glow"}, ("insect", "b"), D=5.5, w0=2.2, w1=2.6)
    # ---- waypoints (the stations' own were placed above)
    m.wp("hub_view", HUB_AT, 0.0, "yard", choice_view=True)
    m.wp("cross", [0.0, 2.0], 0.0, "tracks")
    m.wp("hall_c", [0.0, -7.0], 0.0, "hall")
    m.wp("hall_w", [-8.0, -10.0], 90.0, "hall")
    m.wp("hall_e", [8.0, -10.0], -90.0, "hall")
    # ---- the walls: the forecourt's warehouse fronts with their shutters up on the crowd (the painting), the depot's tunnel mouths and windows
    m.decal_at("yard_shutter_w", "tr_shutter_rave", [-8.985, 11.0], -90.0, 0.0, 5.2)
    m.decal_at("yard_shutter_e", "tr_shutter_rave", [8.985, 11.0], 90.0, 0.0, 5.2)
    m.decal_at("yard_towers_w", "tr_towers", [-8.985, 6.2], -90.0, 3.0, 3.6)
    m.decal_at("yard_towers_e", "tr_towers", [8.985, 6.2], 90.0, 3.0, 3.6)
    m.decal_at("track_mouth_w", "tr_garage_door", [-12.985, 2.0], -90.0, -0.2, 4.0)
    m.decal_at("track_mouth_e", "tr_garage_door", [12.985, 2.0], 90.0, -0.2, 4.0)
    for i, x in enumerate((-9.0, 9.0)):
        m.decal_at("hall_board_%d" % i, "tr_board", [x, -16.985], 0.0, 3.4, 2.4)
    for i, z in enumerate((-15.0, -4.0)):
        m.decal_at("hall_win_w_%d" % i, "tr_windows", [-12.985, z], -90.0, 3.2, 2.6)
        m.decal_at("hall_win_e_%d" % i, "tr_windows", [12.985, z], 90.0, 3.2, 2.6)
    m.decal_at("hall_neon_n", "tr_neon", [-5.6, -16.985], 0.0, 4.6, 1.2)
    # ---- things: the bus and the van parked on the forecourt, bollards, street lamps, signals at the tracks, cones, pallets, crates, hanging lamps in the hall
    m.bb("bus", "tr_bus", [-6.6, 8.0], 4.2, y=2.1)
    m.bb("van", "tr_van", [6.4, 7.4], 2.6, y=1.3)
    for i, (x, z) in enumerate([(-3.0, 4.6), (3.0, 4.6), (-8.4, 14.0), (8.4, 14.0), (-8.4, 17.4), (8.4, 17.4)]):
        m.bb("bollard_%d" % i, "tr_bollard", [x, z], 1.0, y=0.5)
    for i, (x, z) in enumerate([(-8.3, 16.0), (8.3, 9.0)]):
        m.bb("lamp_%d" % i, "tr_street_lamp", [x, z], 5.6, y=2.8)
        m.bb("lamp_glow_%d" % i, "tr_glow", [x, z], 2.6, y=5.2, anim="pulse", blend="add")
        m.light("lt_lamp_%d" % i, [x + (0.8 if x < 0 else -0.8), z], 5.0, 9.0, SODIUM, 1.4)
    for i, x in enumerate((-12.2, 12.2)):
        m.bb("signal_%d" % i, "tr_signal", [x, 0.4], 3.2, y=1.4)
        m.bb("signal_glow_%d" % i, "tr_glow", [x, 0.4], 1.0, y=2.7, anim="pulse", blend="add")
    for i, (x, z) in enumerate([(-11.6, 3.4), (11.6, 3.4), (-4.4, 0.6), (4.4, 0.6)]):
        m.bb("cone_%d" % i, "tr_cone", [x, z], 0.7, y=0.15)
    m.bb("pallets_w", "tr_pallet_stack", [-12.0, -1.2], 1.6, y=0.8)
    m.bb("crate_e", "tr_crate", [12.0, -1.4], 1.0, y=0.5)
    m.bb("case_e", "tr_case", [12.2, -15.6], 0.9, y=0.45)
    m.bb("drum_w", "tr_drum", [-12.2, -15.4], 0.9, y=0.45)
    for i, (x, z) in enumerate([(-6.0, -3.0), (6.0, -3.0), (-6.0, -12.0), (6.0, -12.0), (0.0, -9.0)]):
        m.bb("hang_lamp_%d" % i, "tr_hang_lamp", [x, z], 1.0, y=6.6)
        m.bb("hang_glow_%d" % i, "tr_glow", [x, z], 2.4, y=6.4, anim="pulse", blend="add")
    m.bb("glow_hall", "tr_glow", [0.0, -8.0], 6.0, y=0.4, anim="pulse", blend="add")
    m.light("lt_hall_a", [-6.0, -6.0], 6.4, 11.0, "#ffd8a8", 1.1)
    m.light("lt_hall_b", [6.0, -6.0], 6.4, 11.0, "#ffd8a8", 1.1)
    m.light("lt_hall_c", [0.0, -13.0], 6.4, 10.0, PURPLE, 0.9)
    m.light("lt_tracks", [0.0, 2.0], 4.0, 9.0, RED, 0.7)
    m.light("lt_yard", [0.0, 10.0], 4.0, 9.0, "#8aa8d8", 0.6)
    # ---- the people: the hall is the dance floor; a few stand out on the forecourt in the rain
    spots = []
    for i in range(18):
        spots.append(("hall", [-9.0 + (i % 6) * 3.6 + (i // 6) * 1.2, -3.0 - (i // 6) * 3.2 - (i % 2) * 0.8]))
    spots += [("hall", [-2.6, -14.6]), ("hall", [2.6, -14.2]), ("hall", [-5.6, -15.6])]
    spots += [("yard", [-4.0, 9.0]), ("yard", [4.0, 11.0]), ("yard", [-2.0, 12.4]), ("yard", [5.4, 15.0]), ("tracks", [-8.0, 2.2]), ("tracks", [8.0, 1.8])]
    kinds = [("grey", "a"), ("antenna", "a"), ("blob", "b"), ("insect", "a"), ("cyclops", "b"), ("tentacle", "b"), ("grey", "b"), ("antenna", "b"), ("blob", "a"), ("insect", "b"), ("cyclops", "a")]
    add_crowd(m, spots, kinds)
    return m


# rain on the forecourt and the tracks (docs/engine/WEATHER.md): the hall and the bays are roofed, so dry; drips fall from the hall roof's front edge onto the tracks
WEATHER = {"rain": 0.75, "wind": 8, "drips": [{"at": [-7.0, 0.3], "h": 8.8}, {"at": [7.0, 0.3], "h": 8.8}, {"at": [-2.5, 0.3], "h": 8.8}]}


# ---------------------------------------------------------------------------------------------------------------------------------------- theme file, story
def theme_spec():
    props = [
        {"id": "deck", "role": "stage_deck", "sprite": "tr_deck", "spot": "deck_view"},
        {"id": "bass_knob", "role": "bass_knob", "sprite": "tr_knob_0", "spot": "deck_view"},
        {"id": "left_luggage", "role": "cloakroom", "sprite": "tr_desk", "spot": "cloak_view"},
        {"id": "bar_counter", "role": "bar", "sprite": "tr_counter", "spot": "bar_view"},
        {"id": "garage_door", "role": "race_entrance", "sprite": "tr_garage_door", "spot": "hangar_view"},
        {"id": "home_hatch", "role": "home_threshold", "sprite": "tr_hatch", "spot": "home_door"},
        {"id": "signals", "role": "decor", "sprite": "tr_signal", "at": [0.0, 0.0]},
    ]
    guides = [
        {"id": "dj", "sprite": "rave_transport/tentacle_a", "spot": "deck_view", "for": "stage"},
        {"id": "attendant", "sprite": "rave_transport/cyclops_a", "spot": "cloak_view", "for": "cloakroom"},
        {"id": "bartender", "sprite": "rave_transport/blob_a", "spot": "bar_view", "for": "bar"},
        {"id": "pilot", "sprite": "rave_transport/insect_b", "spot": "hangar_view", "for": "race"},
        {"id": "home_hatch", "sprite": "tr_hatch", "spot": "home_door", "for": "home"},
    ]
    routes = {
        "stage": route(MAP_ID, "hub_view", [leg("hall_c", 4, 1, via=["cross"]), leg("stage_foot", 2, 1, "deck"), leg("stage_steps", 2, 1, "deck"), leg("deck_view", 2, 4, "deck")], "deck_view"),
        "cloak": route(MAP_ID, "hub_view", [leg("hall_c", 4, 1, via=["cross"]), leg("cloak_door", 2, 1, via=["hall_w"]), leg("cloak_hold", 2, 4, "attendant")], "cloak_hold"),
        "bar": route(MAP_ID, "hub_view", [leg("hall_c", 4, 1, via=["cross"]), leg("bar_door", 2, 1, via=["hall_e"]), leg("bar_hold", 2, 4, "bartender")], "bar_hold"),
    }
    return {
        "id": "transport", "prefix": "transport", "scene_id": "transport_rave", "geography": "doom_dock", "arrival": "transport_arrive", "props": props, "guides": guides, "routes": routes,
        "customers": [{"id": "transport_floor", "sprite_set": "rave_transport/clubgoers", "count": 27, "spot": "hall_c"},
                      {"id": "transport_queue", "sprite_set": "rave_transport/clubgoers", "count": 3, "spot": "cloak_view"}],
        "ingredients": [{"id": "diesel_cola", "icon": "transport/ing_cola", "color": "#6b3a1e"}, {"id": "tyre_liquorice", "icon": "transport/ing_liquorice", "color": "#2a2a33"},
                        {"id": "road_salt", "icon": "transport/ing_salt", "color": "#e8e8ea"}, {"id": "headlamp_lemon", "icon": "transport/ing_lemon", "color": "#ffe84a"}],
        "cloakroom_symbols": [{"id": "bus", "icon": "transport/sym_bus"}, {"id": "bike", "icon": "transport/sym_bike"}, {"id": "train", "icon": "transport/sym_train"},
                              {"id": "boat", "icon": "transport/sym_boat"}],
    }


PALETTES = {"low": ["#1a1430", "#3a2a14"], "cool": [CYAN, "#8aa8d8"], "warm": [SODIUM, HIVIS], "rave": [HIVIS, YELLOW, LIME, PURPLE]}


def main(argv) -> int:
    art = build_art()
    arche = rave_people.build("transport", art.name)
    place_activity_sheets(art.name, "transport", os.path.join(art.tex, "tr_knob_sheet.png"))
    ra.write_manifest(art, arche, TEXTURES + ["tr_sky"], [ra.piece_entry(PIECES[0], PIECES[0]), ra.piece_entry(PIECES[1], PIECES[1]), ra.piece_entry(PIECES[2], PIECES[2]),
                                                         ra.piece_entry(AMBIENT, AMBIENT)])
    m = build_map(art)
    out = m.to_json()
    out["weather"] = WEATHER
    write(MAP, out)
    write(STORY, story_json(m.actors, "transport_rave", "The Transport Rave", art.name, "The Depot", AMBIENT, PALETTES,
                            "A rave in a railway depot off a wet street (docs/briefs/BEDSIT_RAVES_BRIEF.md section 3): a path's world, not a Story Campaign chapter."))
    write(THEME_FILE, theme_json(theme_spec()))
    write_activity_layouts("transport", CLOAK_F, BAR_F, "rave_transport")
    bearings = hub_bearings(m, HUB_AT, 0.0, ["dj", "attendant", "bartender", "pilot", "customer_0", "customer_7"])
    print("wrote %s (%d sectors, %d things, %d waypoints); hub bearings %s" % (MAP, len(out["sectors"]), len(out["things"]), len(out["waypoints"]), bearings))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
