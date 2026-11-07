#!/usr/bin/env python3
"""Builds a rave's street race course (docs/briefs/BEDSIT_RAVES_BRIEF.md sections 8 to 10, docs/bedsit/RACE.md): the story map content/story/maps/race_<theme>.json,
its story file content/story/race_<theme>.json, the course file content/races/courses/race_<theme>.json (contract 8's RaceCourse plus the analytic `segments` the game
computes the centreline from) and the PLACEHOLDER art under assets/story/race_<theme>/ (tools/story/race_art.py).

    python3 tools/story/build_race.py --theme space            # the Space rave's street (the city outside the Mothership: neon and rain)
    python3 tools/story/build_race.py --theme space --sheet F  # also a contact sheet of the placeholder art

THE STREET. A finite course of straight runs and circular bends (THEMES[theme]["layout"]), `lanes` lanes wide, kerbed pavements both sides, and the buildings as
Doom-style blocks: a sector per block whose floor is the roof, so the step face up to it is the facade (its texture, its window decals, its neon) and the skyline
varies block by block; their outer walls are "sky" (not drawn). Every piece of street is five convex sectors side by side (block, pavement, road, pavement, block),
cut every `straight_step` metres on the straights and every `arc_step_deg` degrees on the bends; neighbouring pieces share their cut exactly, so the portals meet.
Lamps on the pavement every `lamp_every` metres (their light reaches the road and pavements of three pieces), cat's eyes on the lane lines, shop windows and neon
signs on the facades, approach banners before the finish, the finish gantry at `length_m`, and the street ends at a building `runoff` metres later.
Waypoints: one per lane per piece (`ln<k>_<i>`, the lane's middle in that piece), `race_grid` (the start, middle lane), `race_finish`. Only the space theme is authored;
another theme is a THEMES entry (its palette, layout and lengths), nothing else.
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import race_course as rc  # noqa: E402

THEMES = {
    "space": {
        "title": "The Mothership Strip",
        "blurb": "The city outside the Mothership rave: a wet night street of neon and rain, three lanes between towers, the Mothership hanging over the roofs.",
        "lanes": 3, "lane_w": 3.4, "pavement": 3.0, "block_depth": 7.0, "heights": [9.0, 30.0], "seed": 11,
        "length_m": 2200.0, "runoff": 160.0, "back_m": 30.0,
        "straight_step": 30.0, "arc_step_deg": 6.0, "lamp_every": 40.0, "stud_every": 9.0,
        "layout": [("straight", 260), ("bend", 40, 90), ("straight", 300), ("bend", -60, 80), ("straight", 220), ("bend", -30, 120), ("straight", 340),
                   ("bend", 50, 90), ("straight", 260), ("bend", 20, 150), ("straight", 640)],
        # palette (tools/story/race_art.py)
        "road_dark": "#0c0d18", "road_mid": "#191b2a", "road_lite": "#2a2d42", "sodium": "#ffae4a", "sodium_hot": "#fff0c0", "neon_a": "#ff3fb4", "neon_b": "#3ff0ff",
        "neon_c": "#9aff5a", "neon_d": "#b06aff", "stud": "#c8f8ff", "city_glow": "#ff7a9a", "nebula": "#5a2a8a", "choice": "#e8fcff",
        "sky": ["#05030f", "#0c0820", "#180f36", "#26184e", "#3a2260"],
        "facades": [(("#141522", "#1e2032", "#2a2d44", "#3a3e5a"), ["#ffc870", "#ffe0a0", "#7ad8ff"]),
                    (("#1a1418", "#261c22", "#34262e", "#46343e"), ["#ffb060", "#ff8ac8", "#ffe8b0"]),
                    (("#10161a", "#18222a", "#22303a", "#30424e"), ["#9af0ff", "#ffd27a", "#c8a0ff"])],
        "shop": ["#ffcf8a", "#9af4ff", "#ffa8d8"],
        "hood": ("#120818", "#3a0f3a", "#7a1a6a", "#d04aa8"),
        "rivals": [("#1a0610", "#6a0a2a", "#d0205a", "#ff6aa0"), ("#06140a", "#145a24", "#2ac85a", "#9aff7a"), ("#140c02", "#6a3a08", "#e08a10", "#ffd060")],
        "taxi": ("#2a2006", "#7a6010", "#e0b820", "#ffe070"), "van": ("#14161e", "#3a3e4e", "#7a8094", "#c8ccd8"),
        "fog": {"color": "#120a24", "density": 0.016}, "road_tint": "#8c84ff", "pave_tint": "#a08cff", "block_tint": "#7a70c8",
    },
}


def sector(sid, poly, floor, floor_tex, tint, light, wall_tex="sky", step_tex="", ceiling=90.0, flags=None):
    d = {"id": sid, "polygon": [[round(p[0], 4), round(p[1], 4)] for p in poly], "floor": floor, "ceiling": ceiling, "floor_tex": floor_tex, "ceil_tex": "sky",
         "wall_tex": wall_tex, "light": light, "tint": tint, "room": "main", "flags": flags or [],
         "activities": {"quiet": ["stand"], "dancing": ["stand"], "hype": ["stand"]}}
    if step_tex:
        d["step_tex"] = step_tex
    return d


def build(theme: str) -> dict:
    t = THEMES[theme]
    import numpy as np
    rng = np.random.RandomState(t["seed"])
    segs = rc.build_segments(t["layout"])
    L, run = t["length_m"], t["runoff"]
    end = L + run
    assert rc.total(segs) >= end - 1e-6, "the layout (%.1f m) is shorter than the course and its run-off (%.1f m)" % (rc.total(segs), end)
    half = t["lanes"] * t["lane_w"] / 2.0
    offs = [-(half + t["pavement"] + t["block_depth"]), -(half + t["pavement"]), -half, half, half + t["pavement"], half + t["pavement"] + t["block_depth"]]
    lanes = [{"id": "LCR"[k] if t["lanes"] == 3 else "L%d" % k, "x": round(-half + t["lane_w"] * (k + 0.5), 3)} for k in range(t["lanes"])]
    st = rc.stations(segs, -t["back_m"], end, t["straight_step"], t["arc_step_deg"])
    cuts = [[rc.point(segs, s, o)[0] for o in offs] for s in st]
    nfac = len(t["facades"])
    sectors, walls, things, waypoints = [], [], [], []
    heights = {"L": [], "R": []}
    blocks = []
    for side in ("L", "R"):  # building blocks: runs of 1..3 pieces at one height and one facade
        i = 0
        while i < len(st) - 1:
            n = int(rng.randint(1, 4))
            h = round(float(rng.uniform(*t["heights"])), 1)
            fac = int(rng.randint(0, nfac))
            for _ in range(n):
                if i < len(st) - 1:
                    heights[side].append((h, fac))
                    i += 1
            blocks.append({"side": side, "from_m": round(max(st[i - n], 0.0), 3), "to_m": round(max(st[i], 0.001), 3), "height_m": h})
    pieces = []
    for i in range(len(st) - 1):
        a, b = cuts[i], cuts[i + 1]
        quad = lambda k: [a[k], a[k + 1], b[k + 1], b[k]]
        rd, sl, sr, bl, br = "rd_%d" % i, "pl_%d" % i, "pr_%d" % i, "bl_%d" % i, "br_%d" % i
        hl, fl = heights["L"][i]
        hr, fr = heights["R"][i]
        sectors.append(sector(bl, quad(0), hl, "rc_roof", t["block_tint"], 0.42, "sky", "rc_facade_%d" % fl))
        sectors.append(sector(sl, quad(1), 0.15, "rc_pave", t["pave_tint"], 0.5, "rc_facade_%d" % fl, "rc_kerb"))
        sectors.append(sector(rd, quad(2), 0.0, "rc_asphalt", t["road_tint"], 0.5, "rc_facade_0"))
        sectors.append(sector(sr, quad(3), 0.15, "rc_pave", t["pave_tint"], 0.5, "rc_facade_%d" % fr, "rc_kerb"))
        sectors.append(sector(br, quad(4), hr, "rc_roof", t["block_tint"], 0.42, "sky", "rc_facade_%d" % fr))
        row = [bl, sl, rd, sr, br]
        for k in range(4):  # side by side
            walls.append({"from": [round(a[k + 1][0], 4), round(a[k + 1][1], 4)], "to": [round(b[k + 1][0], 4), round(b[k + 1][1], 4)], "sector": row[k], "portal": row[k + 1]})
        if i + 1 < len(st) - 1:  # on to the next piece
            for k in range(5):
                walls.append({"from": [round(b[k][0], 4), round(b[k][1], 4)], "to": [round(b[k + 1][0], 4), round(b[k + 1][1], 4)], "sector": row[k], "portal": ["bl_%d", "pl_%d", "rd_%d", "pr_%d", "br_%d"][k] % (i + 1)})
        pieces.append({"i": i, "s0": st[i], "s1": st[i + 1], "road": rd})
        for k, ln in enumerate(lanes):  # one waypoint per lane in the middle of the piece
            sm = (st[i] + st[i + 1]) / 2.0
            p, yaw = rc.point(segs, sm, ln["x"])
            waypoints.append({"id": "ln%d_%d" % (k, i), "at": [round(p[0], 3), round(p[1], 3)], "yaw": round(yaw, 3), "sector": rd, "lane": k, "s": round(sm, 3)})

    def piece_at(s):
        for pc in pieces:
            if pc["s0"] <= s < pc["s1"]:
                return pc["i"]
        return pieces[-1]["i"]

    def wp(wid, s, x, **kw):
        p, yaw = rc.point(segs, s, x)
        d = {"id": wid, "at": [round(p[0], 3), round(p[1], 3)], "yaw": round(yaw, 3), "sector": "rd_%d" % piece_at(s), "s": s}
        d.update(kw)
        waypoints.append(d)

    wp("race_grid", 0.0, lanes[len(lanes) // 2]["x"])
    wp("race_finish", L, lanes[len(lanes) // 2]["x"])
    wp("race_end", end - 25.0, lanes[len(lanes) // 2]["x"])

    def bb(tid, sprite, s, x, size, y=None, **kw):
        p, _ = rc.point(segs, s, x)
        d = {"id": tid, "kind": "billboard", "sprite": sprite, "at": [round(p[0], 3), round(p[1], 3)], "size": size, "anim": kw.pop("anim", "none")}
        if y is not None:
            d["y"] = y
        d.update(kw)
        things.append(d)

    def light(lid, s, x, y, radius, color, strength, reach):
        p, _ = rc.point(segs, s, x)
        i = piece_at(s)
        secs = []
        for j in range(max(0, i - reach), min(len(pieces), i + reach + 1)):
            secs += ["rd_%d" % j, "pl_%d" % j, "pr_%d" % j]
        things.append({"id": lid, "kind": "light", "at": [round(p[0], 3), round(p[1], 3)], "y": y, "radius": radius, "color": color, "strength": strength, "sectors": secs})

    def decal(did, sprite, s, side, y, size, **kw):
        x = (half + t["pavement"] - 0.02) * (-1 if side == "L" else 1)
        p, yaw = rc.point(segs, s, x)
        face = yaw - 90.0 if side == "L" else yaw + 90.0  # facing the road
        face = (face + 180.0) % 360.0 - 180.0
        d = {"id": did, "kind": "decal", "sprite": sprite, "at": [round(p[0], 3), round(p[1], 3)], "y": y, "size": size, "yaw": round(face, 3), "emissive": True}
        d.update(kw)
        things.append(d)

    # lamps (alternate sides), with their pools on the road
    n = 0
    s = 20.0
    while s < end - 10:
        side = -1 if n % 2 == 0 else 1
        bb("lamp_%d" % n, "rc_lamp", s, side * (half + 0.7), 6.6)
        light("lt_lamp_%d" % n, s, side * (half - 0.4), 6.2, 15.0, t["sodium"], 1.5, 1)
        n += 1
        s += t["lamp_every"]
    # cat's eyes on the lane lines
    n = 0
    for k in range(1, t["lanes"]):
        x = -half + t["lane_w"] * k
        s = 4.0
        while s < end - 4:
            bb("stud_%d" % n, "rc_stud", s, x, 0.09, y=0.0, emissive=True)
            n += 1
            s += t["stud_every"]
    # shop windows, neon signs (and their light on the street)
    n = 0
    s = 14.0
    while s < end - 20:
        for side in ("L", "R"):
            if rng.rand() < 0.55:
                decal("shop_%d" % n, "rc_shop_%d" % int(rng.randint(0, 3)), s + rng.uniform(-4, 4), side, 0.3, 2.0)
                n += 1
            if rng.rand() < 0.45:
                k = int(rng.randint(0, 5))
                ys = round(float(rng.uniform(3.2, 7.5)), 2)
                ss = s + rng.uniform(-6, 6)
                decal("neon_%d" % n, "rc_neon_%d" % k, ss, side, ys, 2.4)
                col = [t["neon_a"], t["neon_b"], t["neon_c"], t["sodium"], t["neon_d"]][k]
                light("lt_neon_%d" % n, ss, (half + t["pavement"] - 0.6) * (-1 if side == "L" else 1), ys, 9.0, col, 1.2, 0)
                n += 1
        s += 22.0
    # the finish approach: banners over the road, the gantry, the building at the street's end
    for k, d in enumerate((400.0, 200.0, 80.0)):
        bb("banner_%d" % k, "rc_banner", L - d, 0.0, 1.4, y=6.0, emissive=True)
    bb("finish_gantry", "rc_gantry", L, 0.0, 8.0, emissive=True)
    light("lt_finish_a", L, -(half + 1.2), 7.0, 16.0, t["neon_a"], 1.8, 1)
    light("lt_finish_b", L, half + 1.2, 7.0, 16.0, t["neon_b"], 1.8, 1)
    decal_end = rc.point(segs, end - 0.05, 0.0)
    things.append({"id": "end_neon", "kind": "decal", "sprite": "rc_neon_1", "at": [round(decal_end[0][0], 3), round(decal_end[0][1], 3)], "y": 4.0, "size": 5.0,
                   "yaw": round(decal_end[1], 3), "emissive": True})
    centre = []
    s = 0.0
    while s <= end + 1e-6:
        centre.append([round(v, 3) for v in rc.point(segs, s, 0.0)[0]])
        s += 5.0
    m = {
        "units_per_m": 1, "eye_height": 1.15, "art": "race_%s" % theme, "start": "race_grid", "max_step": 0.5,
        "visibility": {"mode": "clip", "depth": 60, "far": 170},
        "geography": {"source": "tools/story/build_race.py --theme %s" % theme, "note": "a generated street course (PLACEHOLDER art)"},
        "textures": {name: "textures/%s.png" % name for name in TEXTURE_NAMES(t)},
        "sky": {"tex": "textures/rc_sky.png", "mode": "cylinder"},
        "fog": t["fog"], "palette_weight": 0.0,
        "sectors": sectors, "walls": walls, "homes": [], "spots": {}, "silhouettes": [], "occluders": [], "waypoints": waypoints,
        "things": things,
    }
    course = {
        "id": "race_%s" % theme, "theme": theme, "map": "race_%s" % theme, "title": t["title"], "length_m": L, "runoff_m": run, "back_m": t["back_m"],
        "centreline": centre, "segments": segs, "lanes": lanes, "eye_m": 1.15, "blocks": blocks,
        "camera": {"fov_deg": 52.0, "pitch_deg": -2.0, "lane_ease_beats": 1.5, "speed_fov_gain": 0.0, "max_roll_deg": 0.0},
        "cockpit": {"sprite": "dash", "height_frac": 0.3},
        "regions": {"top": [0.25, 0.0, 0.5, 0.42], "bottom": [0.25, 0.72, 0.5, 0.28], "left": [0.0, 0.0, 0.22, 1.0], "right": [0.78, 0.0, 0.22, 1.0]},
        "pieces": pieces, "grid_waypoint": "race_grid", "finish_waypoint": "race_finish",
        "lane_waypoints": [["ln%d_%d" % (k, pc["i"]) for pc in pieces] for k in range(len(lanes))],
    }
    return m, course


def TEXTURE_NAMES(t):
    return ["rc_asphalt", "rc_pave", "rc_kerb", "rc_roof", "rc_lamp", "rc_stud", "rc_gantry", "rc_banner"] + ["rc_facade_%d" % i for i in range(len(t["facades"]))] + \
        ["rc_neon_%d" % k for k in range(5)] + ["rc_shop_%d" % k for k in range(3)]


def story(theme: str) -> dict:
    t = THEMES[theme]
    return {
        "id": "race_%s" % theme, "title": t["title"], "chapter": 9, "art": "race_%s" % theme,
        "description": "The street race of the %s rave (docs/bedsit/RACE.md): a path's activity stage, not a Story Campaign chapter." % theme,
        "intro": "", "duration_bars": 8, "sequence_bars": 2, "initial_energy": 45,
        "palettes": {"low": ["#3a2a8a", "#1d6a8a"], "cool": [t["neon_b"], "#6a7bff"], "warm": [t["sodium"], t["neon_a"]], "rave": [t["neon_a"], t["neon_b"], t["neon_d"], t["sodium"]]},
        "energy": {"pass_delta": {"sharp": 4, "steady": 3, "loose": 2}, "fail_delta": -5, "min": 0, "max": 100,
                   "bands": [{"id": "quiet", "label": "Unimpressed", "max": 29}, {"id": "dancing", "label": "Dancing", "max": 64}, {"id": "hype", "label": "Hype", "max": 84},
                             {"id": "euphoric", "label": "Euphoric", "max": 100}]},
        "acts": [{"id": "I", "title": t["title"], "start_bar": 1}],
        "blocks": [{"id": "the_street", "title": t["title"], "act": "Act I", "start_bar": 1, "bars": 8, "events": [{"at_bar": 1, "action": "player_role", "role": "dancer"}]}],
        "decisions": [],
        "endings": {"road_open": {"title": "The road opens", "energy_min": 80, "pass_min": 0.9, "text": "", "journey": []},
                    "road_hard": {"title": "A hard road", "energy_min": 40, "pass_min": 0.5, "text": "", "journey": []},
                    "road_lost": {"title": "Lost on the road", "energy_min": 0, "pass_min": 0.0, "text": "", "journey": []}},
        "ending_order": ["road_open", "road_hard", "road_lost"], "groups": {"circle": [], "all": [], "early": []}, "actors": [], "silhouettes": [],
    }


def write(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=1)
        fh.write("\n")


def write_art(theme: str) -> list:
    import race_art
    t = THEMES[theme]
    base = os.path.join(ROOT, "assets", "story", "race_%s" % theme)
    tex_dir, spr_dir = os.path.join(base, "textures"), os.path.join(base, "sprites")
    os.makedirs(tex_dir, exist_ok=True)
    os.makedirs(spr_dir, exist_ok=True)
    man_tex = {}
    shown = []
    for name, (cv, metres) in race_art.textures(t).items():
        cv.save(os.path.join(tex_dir, name + ".png"))
        shown.append((name, cv))
        if metres is not None:
            man_tex[name] = {"file": "textures/%s.png" % name, "size": [cv.w, cv.h], "metres": metres}
    for name, (cv, grid) in race_art.sheets(t).items():
        cv.save(os.path.join(spr_dir, name + ".png"))
        with open(os.path.join(spr_dir, name + ".json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"grid": grid, "placeholder": True}, fh)
            fh.write("\n")
        shown.append((name, cv))
    write(os.path.join(base, "manifest.json"), {"version": 1, "level": "race_%s" % theme, "placeholder": True,
                                                "px_scale_note": "PLACEHOLDER art drawn by tools/story/race_art.py (build_race.py)", "archetypes": {}, "silhouettes": {}, "stage": {},
                                                "textures": man_tex, "people": {}})
    return shown


def contact(path: str, shown: list) -> None:
    from PIL import Image
    W = 1400
    x = y = 4
    rowh = 0
    placed = []
    for name, cv in shown:
        im = cv.image()
        k = 2 if im.width <= 300 and im.height <= 260 else 1
        if im.width * k > W - 8:
            k = (W - 8) / im.width
        im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.NEAREST)
        if x + im.width > W - 4:
            x, y = 4, y + rowh + 6
            rowh = 0
        placed.append((im, x, y))
        x += im.width + 6
        rowh = max(rowh, im.height)
    sheet = Image.new("RGBA", (W, y + rowh + 8), (24, 20, 40, 255))
    for im, px_, py in placed:
        sheet.paste(im, (px_, py), im)
    sheet.convert("RGB").save(path)


def main(argv: list) -> int:
    theme = argv[argv.index("--theme") + 1] if "--theme" in argv else "space"
    if theme not in THEMES:
        print("unknown theme %s (authored: %s)" % (theme, ", ".join(THEMES)))
        return 2
    shown = write_art(theme)
    m, course = build(theme)
    write(os.path.join(ROOT, "content", "story", "maps", "race_%s.json" % theme), m)
    write(os.path.join(ROOT, "content", "story", "race_%s.json" % theme), story(theme))
    write(os.path.join(ROOT, "content", "races", "courses", "race_%s.json" % theme), course)
    if "--sheet" in argv:
        contact(argv[argv.index("--sheet") + 1], shown)
    print("race_%s: %d sectors, %d walls, %d things, %d waypoints, %.0f m to the finish (+%.0f run-off), %d placeholder images" % (
        theme, len(m["sectors"]), len(m["walls"]), len(m["things"]), len(m["waypoints"]), course["length_m"], course["runoff_m"], len(shown)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
