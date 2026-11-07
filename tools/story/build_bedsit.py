#!/usr/bin/env python3
"""Builds the bedsit: its art (tools/story/art/tex_bedsit.py -> assets/story/bedsit/textures/*.png and manifest.json) and its map (content/story/maps/bedsit.json).

    python3 tools/story/build_bedsit.py            # art and map
    python3 tools/story/build_bedsit.py --map      # the map only (the sprite sizes are read from the PNGs already written)
    python3 tools/story/build_bedsit.py --sheet F  # also write a contact sheet of every texture to F (a PNG, for looking at)

The room: 4 x 5 m (x -2..2 east, z -2.5..2.5 south), 2.5 m high, eye 1.6 m, ONE sector. The player stands at (0, 0) and turns on the spot, so every facing is the same room:
  North  (z = -2.5)  the window onto a night sky with a glow behind the rooftops; a model rocket on the sill, a star mobile, a radiator, two posters, a standing lamp.      -> Space
  East   (x = +2)    the desk with the decks and headphones, a plastic dinosaur, a fern, a jungle poster whose centre has become a real opening, a coat-hook board, a poster.   -> Dinosaurs
  South  (z = +2.5)  the wardrobe with its door ajar and iridescent light leaking out, a shelf with a unicorn figurine, fairy lights, a clothes rail.                      -> Magic and unicorns
  West   (x = -2)    the bed (headboard at the north end), the door with a bus timetable pinned to it, a toy car, a blinking indicator light, orange street light under it, a mirror. -> Transport
Wall pictures are DECALS (flat on their wall, consistent from every facing); small free things are billboards. Decals that overlap are layered on explicit planes: 3 mm off the wall
(the lit things behind a frame's hole), 6 mm (the frame), 12 mm (pinned things on top).
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

PPM = 160
ART = os.path.join(ROOT, "assets", "story", "bedsit")
TEX = os.path.join(ART, "textures")
MAP = os.path.join(ROOT, "content", "story", "maps", "bedsit.json")
X0, X1, Z0, Z1 = -2.0, 2.0, -2.5, 2.5
EYE = 1.6
CEIL = 2.5

# yaw each wall's picture faces (0 toward -z, 90 toward -x, 180 toward +z, -90 toward +x)
WALLS = {"N": {"yaw": 180, "pos": Z0, "axis": "x", "sign": 1}, "S": {"yaw": 0, "pos": Z1, "axis": "x", "sign": -1},
         "E": {"yaw": 90, "pos": X1, "axis": "z", "sign": -1}, "W": {"yaw": -90, "pos": X0, "axis": "z", "sign": 1}}
LAYER = {"back": 0.003, "frame": 0.006, "top": 0.012}


def png_size(name: str):
    from PIL import Image
    with Image.open(os.path.join(TEX, name + ".png")) as im:
        return im.size


def write_art() -> dict:
    os.makedirs(TEX, exist_ok=True)
    from art import tex_bedsit
    from art.bedsit_draw import save_rgb
    built = tex_bedsit.build()
    man = {}
    for name, (kind, img, metres, extra) in sorted(built.items()):
        path = os.path.join(TEX, name + ".png")
        if kind == "tile":
            save_rgb(path, img)
            w, h = img.shape[1], img.shape[0]
        else:
            img.save(path)
            w, h = img.w, img.h
        man[name] = {"file": f"textures/{name}.png", "size": [w, h], "metres": metres if metres else 1.0}
    manifest = {"version": 1, "level": "bedsit", "px_scale_note": "texture px x px_scale = design px; the bedsit draws at 160 texels a metre (tools/story/art/tex_bedsit.py)",
                "archetypes": {}, "silhouettes": {}, "stage": {}, "textures": man, "people": {}}
    with open(os.path.join(ART, "manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1)
        fh.write("\n")
    return built


def sprite_size(name: str):
    w, h = png_size(name)
    return w, h


def decal(did, sprite, wall, along, y, layer="frame", height=None, flip=False):
    """A decal on `wall` ("N", "E", "S", "W"), `along` metres along it (x on N and S, z on E and W), its bottom edge `y` above the floor, on the plane `layer`."""
    w = WALLS[wall]
    pos = w["pos"] - w["sign"] * -1 * 0  # the wall plane
    n = -1 if wall in ("N", "W") else 1  # the inward normal's sign along the wall's axis: N and W walls sit at the low end
    off = LAYER[layer]
    inward = {"N": (0, 1), "S": (0, -1), "E": (-1, 0), "W": (1, 0)}[wall]
    if w["axis"] == "x":
        at = [round(along, 4), round(w["pos"] + inward[1] * off, 4)]
    else:
        at = [round(w["pos"] + inward[0] * off, 4), round(along, 4)]
    w_px, h_px = sprite_size(sprite)
    d = {"id": did, "kind": "decal", "sprite": sprite, "at": at, "y": round(y, 4), "size": round(height if height else h_px / PPM, 4), "yaw": w["yaw"]}
    return d


def thing(tid, sprite, at, y_base=None, anim="none", size=None, blend=None, emissive=False, sector="room"):
    w_px, h_px = sprite_size(sprite)
    h = size if size else h_px / PPM
    t = {"id": tid, "kind": "billboard", "sprite": sprite, "at": [round(at[0], 4), round(at[1], 4)], "size": round(h, 4), "anim": anim}
    if y_base is not None:
        t["y"] = round(y_base + h / 2, 4)
    if blend:
        t["blend"] = blend
    if emissive:
        t["emissive"] = True
    return t


def light(lid, at, y, radius, color, strength, yaw=None, angle=45):
    t = {"id": lid, "kind": "light", "at": list(at), "y": y, "radius": radius, "color": color, "strength": strength}
    if yaw is not None:
        t["cone"] = {"yaw": yaw, "angle": angle}
    return t


def build_map() -> dict:
    tex_names = ["wall_paper_n", "wall_paper_e", "wall_paper_s", "wall_paper_w", "ceil_plaster", "floor_room", "win_frame", "win_glass", "radiator", "wardrobe", "wardrobe_light",
                 "shelf", "fairy_lights", "clothes_rail", "desk", "jungle_poster", "jungle_glow", "door", "door_light", "timetable", "mirror", "hooks", "poster_0", "poster_1",
                 "poster_2", "poster_3", "poster_4", "bed_side", "thing_rocket", "thing_mobile", "thing_unicorn", "thing_dino", "thing_headphones", "thing_fern", "thing_car",
                 "thing_indicator", "thing_lamp", "thing_glow_pink", "thing_glow_cyan", "thing_glow_green"]
    textures = {n: f"textures/{n}.png" for n in tex_names}
    sz = lambda n: sprite_size(n)  # noqa: E731
    things: list = []
    S = lambda n: sz(n)[1] / PPM  # noqa: E731  (a sprite's height in metres)

    # ---------------------------------------------------------------- north: the window (-> Space)
    gw, gh = 180, 166  # the glass box of win_frame: (62, 20, 242, 186) in a 304 x 232 sprite
    win_bottom = 0.78
    things += [decal("n_window", "win_frame", "N", 0.0, win_bottom, "frame"),
               decal("n_glass", "win_glass", "N", 0.0, win_bottom + (232 - 186) / PPM, "back"),
               decal("n_radiator", "radiator", "N", 0.0, 0.1, "frame"),
               decal("n_poster_a", "poster_0", "N", -1.45, 1.22, "frame"),
               decal("n_poster_b", "poster_2", "N", 1.38, 1.3, "frame")]
    things += [thing("n_rocket", "thing_rocket", (-0.55, -2.34), y_base=1.05),
               thing("n_mobile", "thing_mobile", (0.62, -1.95), y_base=CEIL - S("thing_mobile"), anim="sway"),
               thing("n_lamp", "thing_lamp", (1.72, -1.98), anim="none", emissive=True)]
    things += [light("n_moon", (0.0, -2.3), 1.5, 3.4, "#7a68ff", 1.15, 180, 48),
               light("n_glow", (0.0, -2.3), 1.2, 2.2, "#ff6ac8", 0.55, 180, 30),
               light("n_lamp_light", (1.55, -1.7), 1.7, 4.4, "#ffc070", 1.3)]

    # ---------------------------------------------------------------- east: the desk and the jungle (-> Dinosaurs)
    things += [decal("e_desk", "desk", "E", 0.0, 0.0, "frame"),
               decal("e_jungle_glow", "jungle_glow", "E", 0.0, 1.12 + (200 - 150) / PPM, "back"),
               decal("e_jungle", "jungle_poster", "E", 0.0, 1.12, "frame"),
               decal("e_hooks", "hooks", "E", -1.62, 1.25, "frame"),
               decal("e_poster", "poster_3", "E", 1.6, 1.3, "frame")]
    things += [thing("e_dino", "thing_dino", (1.75, 0.42), y_base=0.93),
               thing("e_headphones", "thing_headphones", (1.72, -0.5), y_base=0.9),
               thing("e_fern", "thing_fern", (1.68, 1.28)),
               thing("e_glow", "thing_glow_green", (1.8, 0.0), y_base=1.2, blend="add")]
    things += [light("e_jungle_light", (1.8, 0.0), 1.7, 3.6, "#8aff70", 1.1, 90, 55)]

    # ---------------------------------------------------------------- south: the wardrobe (-> Magic and unicorns)
    ward_x = 0.0
    slot_x0, slot_y0, slot_x1, slot_y1 = 106, 34, 124, 314  # the slot in the 208 x 336 wardrobe sprite
    # the sprite's pixel x runs toward -x on this wall (seen from inside, facing +z, right is -x); the slot is 2..20 px right of the centre
    slot_cx_off = ((slot_x0 + slot_x1) / 2 - 104) / PPM
    things += [decal("s_wardrobe", "wardrobe", "S", ward_x, 0.0, "frame"),
               decal("s_wardrobe_light", "wardrobe_light", "S", ward_x - slot_cx_off, (336 - slot_y1) / PPM, "back"),
               decal("s_shelf", "shelf", "S", -1.35, 1.3, "frame"),
               decal("s_rail", "clothes_rail", "S", 1.32, 0.0, "frame"),
               decal("s_fairy", "fairy_lights", "S", 0.0, 2.05, "top", height=0.45)]
    things += [thing("s_unicorn", "thing_unicorn", (-1.5, 2.26), y_base=1.41),
               thing("s_glow", "thing_glow_pink", (ward_x - slot_cx_off, 2.3), y_base=0.45, blend="add"),
               thing("s_glow2", "thing_glow_cyan", (ward_x - slot_cx_off + 0.2, 2.2), y_base=0.8, blend="add")]
    things += [light("s_leak_pink", (ward_x - slot_cx_off, 2.3), 1.2, 3.4, "#ff6ad0", 1.25, 0, 58),
               light("s_leak_cyan", (ward_x - slot_cx_off + 0.15, 2.2), 1.0, 2.6, "#6af0ff", 0.85, 0, 40),
               light("s_fairy_l", (-1.2, 2.3), 2.1, 2.6, "#ffd0f0", 0.6),
               light("s_fairy_r", (1.2, 2.3), 2.1, 2.6, "#d0f0ff", 0.6)]

    # ---------------------------------------------------------------- west: the door (-> Transport)
    door_z = 0.6
    gap_y0 = 4 / PPM
    things += [decal("w_bed", "bed_side", "W", -1.4, 0.0, "frame"),
               decal("w_door", "door", "W", door_z, 0.0, "frame"),
               decal("w_door_light", "door_light", "W", door_z, gap_y0, "back"),
               decal("w_timetable", "timetable", "W", door_z - 0.1, 1.18, "top"),
               decal("w_mirror", "mirror", "W", 1.78, 0.35, "frame"),
               decal("w_poster_a", "poster_1", "W", -1.65, 1.32, "frame"),
               decal("w_poster_b", "poster_4", "W", -0.95, 1.32, "frame", height=0.6)]
    things += [thing("w_car", "thing_car", (-1.55, 1.0)),
               thing("w_indicator", "thing_indicator", (-1.88, door_z), y_base=2.18, anim="pulse", emissive=True)]
    things += [light("w_street", (-1.9, door_z), 0.5, 3.4, "#ffb347", 1.25, -90, 52),
               light("w_street_up", (-1.9, door_z), 2.0, 2.2, "#ffe08a", 0.5, -90, 40)]

    # ---------------------------------------------------------------- the room's own warmth
    things += [light("room_bulb", (0.0, 0.0), 2.3, 5.5, "#ffd9a0", 0.75),
               light("bed_lamp", (-1.5, -0.7), 0.9, 2.4, "#ffb870", 0.6)]

    return {
        "units_per_m": 1, "palette_weight": 0.0, "eye_height": EYE, "start": "bedsit_n",
        "textures": textures,
        "sectors": [{"id": "room", "polygon": [[X0, Z0], [X1, Z0], [X1, Z1], [X0, Z1]], "floor": 0, "ceiling": CEIL, "floor_tex": "floor_room", "ceil_tex": "ceil_plaster",
                     "wall_tex": "wall_paper_n", "light": 0.62, "tint": "#fff0dc", "room": "bedsit", "flags": ["bedsit"],
                     "activities": {"quiet": ["stand"], "dancing": ["stand"], "hype": ["stand"], "euphoric": ["stand"]}}],
        "walls": [{"from": [X0, Z0], "to": [X1, Z0], "sector": "room", "tex": "wall_paper_n", "portal": None},
                  {"from": [X1, Z0], "to": [X1, Z1], "sector": "room", "tex": "wall_paper_e", "portal": None},
                  {"from": [X1, Z1], "to": [X0, Z1], "sector": "room", "tex": "wall_paper_s", "portal": None},
                  {"from": [X0, Z1], "to": [X0, Z0], "sector": "room", "tex": "wall_paper_w", "portal": None}],
        "things": things,
        "homes": [],
        "waypoints": [
            {"id": "bedsit_n", "at": [0, 0], "yaw": 0, "sector": "room", "facing": "N", "choice_view": True},
            {"id": "bedsit_e", "at": [0, 0], "yaw": -90, "sector": "room", "facing": "E", "choice_view": True},
            {"id": "bedsit_s", "at": [0, 0], "yaw": 180, "sector": "room", "facing": "S", "choice_view": True},
            {"id": "bedsit_w", "at": [0, 0], "yaw": 90, "sector": "room", "facing": "W", "choice_view": True},
            {"id": "threshold_n", "at": [0, -1.55], "yaw": 0, "sector": "room"},
            {"id": "threshold_e", "at": [1.45, 0], "yaw": -90, "sector": "room"},
            {"id": "threshold_s", "at": [0, 1.65], "yaw": 180, "sector": "room"},
            {"id": "threshold_w", "at": [-1.4, door_z], "yaw": 90, "sector": "room"}],
        "spots": {}, "silhouettes": [], "occluders": [],
        "fog": {"color": "#1a1210", "density": 0.0},
        "bedsit": {"note": "one room seen from one spot in four directions (bedsit_n/e/s/w are the same point at yaw 0, -90, 180, 90); each facing's wall carries a threshold into its rave",
                   "facings": {"N": {"yaw": 0, "wall": "window and night sky", "theme": "space"}, "E": {"yaw": -90, "wall": "desk and jungle poster", "theme": "dinos"},
                               "S": {"yaw": 180, "wall": "wardrobe ajar", "theme": "magic"}, "W": {"yaw": 90, "wall": "door and bus timetable", "theme": "transport"}}},
    }


def main(argv: list) -> int:
    want_sheet = ""
    if "--sheet" in argv:
        want_sheet = argv[argv.index("--sheet") + 1]
    built = None
    if "--map" not in argv:
        built = write_art()
        print("art: %d textures in %s" % (len(built), TEX))
    m = build_map()
    os.makedirs(os.path.dirname(MAP), exist_ok=True)
    with open(MAP, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(m, fh, indent=1)
        fh.write("\n")
    print("map: %s (%d things)" % (MAP, len(m["things"])))
    if want_sheet and built is not None:
        from PIL import Image
        names = sorted(built)
        ims = [Image.open(os.path.join(TEX, n + ".png")).convert("RGBA") for n in names]
        W = 1800
        x = y = 0
        rowh = 0
        placed = []
        for im in ims:
            im2 = im if max(im.size) <= 420 else im.resize((im.width // 2, im.height // 2), Image.NEAREST)
            if x + im2.width > W:
                x = 0
                y += rowh + 8
                rowh = 0
            placed.append((im2, x, y))
            x += im2.width + 8
            rowh = max(rowh, im2.height)
        sheet = Image.new("RGBA", (W, y + rowh + 8), (60, 60, 70, 255))
        for im2, px, py in placed:
            sheet.alpha_composite(im2, (px, py))
        sheet.convert("RGB").save(want_sheet)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
