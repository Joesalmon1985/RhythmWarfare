"""Authoring helper for Resources/Rooms/room01.json (the first benchmark room: a young rave-music fan's bedsit).

The JSON is the source of truth the game reads; this script only makes it easier to write by hand-placing things against
walls. Re-run:  python -I Tools/art/make_room01.py   (writes Assets/Bedsit/Resources/Rooms/room01.json)

Conventions (Unity, metres): +X east, +Z north, +Y up. A prop's FRONT faces +Z at yaw 0 and its BACK is -Z.
Props are authored with origin at the bottom centre of their bounding box, so a prop of depth d whose back is on a wall
has its origin d/2 away from the wall. Blender +X arrives as Unity -X (mirror), so "pedestal on the right of the desk
(seen from the front)" is local -X.
Yaw facing the room from a wall:  N wall 180, S wall 0, E wall 270, W wall 90.
"""
import json, os, sys, math

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Assets", "Bedsit", "Resources", "Rooms", "room01.json")
HW, HD, H = 2.10, 2.34, 2.80
WALL_T = 0.12


def v(x=0, y=0, z=0):
    return {"x": x, "y": y, "z": z}


def P(prop, pos=(0, 0, 0), yaw=0.0, tag=None, parent=None, scale=1.0, euler=None, shadows=True):
    d = {"prop": prop, "pos": v(*pos), "euler": v(*(euler if euler else (0, yaw, 0))), "scale": scale}
    if tag: d["tag"] = tag
    if parent: d["parent"] = parent
    if not shadows: d["castShadows"] = False
    return d


def on_wall(prop, wall, along, depth, y=0.0, tag=None, scale=1.0, inset=0.0):
    """Place a prop with its back on a wall. along = coordinate along the wall (x for N/S, z for E/W)."""
    off = depth / 2.0 + inset
    if wall == "N": return P(prop, (along, y, HD - off), 180, tag, scale=scale)
    if wall == "S": return P(prop, (along, y, -HD + off), 0, tag, scale=scale)
    if wall == "E": return P(prop, (HW - off, y, along), 270, tag, scale=scale)
    if wall == "W": return P(prop, (-HW + off, y, along), 90, tag, scale=scale)
    raise ValueError(wall)


def build():
    room = {
        "id": "room01", "title": "Bedsit - Kit's room", "occupant": "young adult, rave-music fan, first flat",
        "halfWidth": HW, "halfDepth": HD, "height": H,
        "wakeYaw": 180.0,
        "bedPillowEye": v(1.6, 0.86, 1.9),
        "shell": {"wallMaterial": "wall_plaster", "floorMaterial": "floor_boards", "ceilingMaterial": "ceiling_white",
                  "skirtingMaterial": "paint_white_gloss"},
        "hideLegacy": ["bedSingleCheap_cres", "dresserColonial_cres", "bookcaseValue_cres", "paintingHorizontalCity_cres",
                       "posterTeenAngst_cres", "lightingTableValue1_cres", "chairLivingValuePlain_cres",
                       "windowColonialDoubleHung_cres", "FloorBedsit", "CeilingBedsit", "WallSouth*", "WallNorth*",
                       "WallEast*", "WallWest*", "shrub4_cres", "flowerDaisy_cres", "fenceBalustradeWhiteRail_cres@x<0",
                       "treeBirch01_cres@x<0", "treeBirch01_cres@z<0", "plantFicus_cres@z<3", "Lawn@z<-2"],
        "openings": [
            {"id": "door", "kind": "door", "wall": "N", "along": 0.0, "sill": 0.0, "width": 1.0, "height": 2.4},
            {"id": "win_east", "kind": "window", "wall": "E", "along": -0.65, "sill": 1.0, "width": 1.04, "height": 1.62,
             "frameProp": "furniture_window_frame", "view": "garden"},
            {"id": "win_south", "kind": "window", "wall": "S", "along": 1.0, "sill": 1.0, "width": 1.04, "height": 1.62,
             "frameProp": "furniture_window_frame", "view": "shop"},
            {"id": "win_west", "kind": "window", "wall": "W", "along": 0.1, "sill": 1.0, "width": 1.04, "height": 1.62,
             "frameProp": "furniture_window_frame", "view": "club"},
        ],
        "furniture": [], "decor": [], "cleanables": [], "lights": [], "exteriors": [], "ground": [],
        "environment": {
            "sky": {"r": 0.20, "g": 0.18, "b": 0.34, "a": 1},
            "ambientSky": {"r": 0.48, "g": 0.50, "b": 0.62, "a": 1}, "ambientEquator": {"r": 0.46, "g": 0.42, "b": 0.42, "a": 1},
            "ambientGround": {"r": 0.28, "g": 0.24, "b": 0.22, "a": 1}, "fog": False,
        },
    }
    F = room["furniture"]
    # ---- north: sleeping area (bed head on the north wall, right of the door), wardrobe left of the door
    F.append(P("textiles_bed_frame", (1.6, 0, HD - 1.0), 180, "bed"))
    F.append(P("textiles_mattress", (0, 0, 0), 0, "mattress", parent="bed"))
    F.append(on_wall("furniture_wardrobe", "N", -1.45, 0.59, tag="wardrobe"))
    F.append(on_wall("furniture_bedside_table", "N", 0.86, 0.38, tag="bedside"))
    F.append(P("furniture_lamp_bedside", (0, 0.50, 0), 0, "lampbed", parent="bedside"))
    # ---- east: electronics (desk under the window, TV stand in the corner)
    F.append(on_wall("furniture_desk", "E", -0.65, 0.65, tag="desk"))
    F.append(P("furniture_desk_chair", (1.05, 0, -0.55), 100, "chair"))
    F.append(on_wall("furniture_tv_stand", "E", -1.85, 0.43, tag="tvstand"))
    # ---- south: kitchenette corner, radiator under the window
    F.append(on_wall("furniture_kettle_unit", "S", -1.55, 0.61, tag="kitchen"))
    F.append(on_wall("furniture_mini_fridge", "S", -0.78, 0.53, tag="fridge"))
    F.append(on_wall("furniture_radiator", "S", 1.0, 0.10, y=0.0, tag="radiator"))
    # ---- west: dresser + DJ corner, bookcase
    F.append(on_wall("furniture_dresser", "W", -1.1, 0.48, tag="dresser"))
    F.append(on_wall("furniture_bookcase", "W", 1.2, 0.30, tag="bookcase"))
    F.append(P("furniture_ceiling_light", (0, H - 0.60, 0), 0, "pendant", shadows=False))

    D = room["decor"]
    CL = room["cleanables"]
    def PL(prop, parent, x, y, z, yaw=0.0, tag=None, scale=1.0):
        return P(prop, (x, y, z), yaw, tag, parent=parent, scale=scale)
    def W(prop, x, y, z, yaw=0.0, tag=None, scale=1.0):
        return P(prop, (x, y, z), yaw, tag, scale=scale)
    def clean(id_, label, action, view, messy, tidy=None, target=None, sound=None, radius=0.25, height=0.2, messy_extra=(), tidy_extra=()):
        c = {"id": id_, "label": label, "action": action, "view": view, "messy": messy, "radius": radius, "height": height}
        if tidy is not None: c["tidy"] = tidy
        if target: c["target"] = target
        if sound: c["sound"] = sound
        if messy_extra: c["messyExtra"] = list(messy_extra)
        if tidy_extra: c["tidyExtra"] = list(tidy_extra)
        return c

    # ------------------------------------------------------------------ decor: electronics / personal dressing
    # east: PC desk
    D.append(PL("electronics_monitor_a", "desk", 0.22, 0.74, -0.10, 0))
    D.append(PL("electronics_keyboard", "desk", 0.22, 0.74, 0.14, 0))
    D.append(PL("electronics_mouse", "desk", 0.55, 0.74, 0.14, 0))
    D.append(PL("electronics_pc_tower", "desk", 0.58, 0.74, -0.2, 0))
    D.append(PL("furniture_lamp_desk", "desk", -0.55, 0.74, -0.22, 20))
    D.append(PL("electronics_speakers_pair_desk", "desk", 0.22, 0.74, -0.27, 0))
    D.append(PL("electronics_crt_tv", "tvstand", 0.22, 0.45, 0.0, 0, tag="crt"))
    D.append(PL("electronics_games_console", "tvstand", -0.28, 0.45, 0.0, 0))
    D.append(PL("electronics_smartphone_flat", "desk", 0.9, 0.74, 0.0, 15))
    # west: DJ corner on the dresser
    D.append(PL("electronics_turntable", "dresser", 0.24, 0.95, 0.0, 0))
    D.append(PL("electronics_dj_mixer", "dresser", -0.2, 0.95, 0.0, 0))
    D.append(PL("electronics_headphones_on_stand", "dresser", -0.40, 0.95, 0.12, 0))
    D.append(W("electronics_speaker_big", -1.78, 0.0, -0.15, 90))
    # north: bedside + wardrobe top
    D.append(PL("electronics_alarm_clock", "bedside", 0.1, 0.50, 0.0, 0))
    D.append(PL("kitchen_phone_charger_plugged", "bedside", -0.05, 0.50, 0.0, 0))
    # south: kitchenette dressing
    D.append(PL("kitchen_cup_paper_takeaway", "kitchen", 0.15, 0.905, -0.05, 0))
    D.append(PL("kitchen_dish_tray", "kitchen", -0.12, 0.905, 0.0, 0, tag="dishtray"))
    # shelves in the bookcase (world coordinates against the west wall)
    D.append(W("paper_books_row", -1.93, 1.118, 1.18, 90))
    D.append(W("textiles_laundry_basket", -1.8, 0.45, 0.6, 0, tag="basket"))
    D.append(W("furniture_stool", -1.8, 0.0, 0.6, 0))
    D.append(W("kitchen_bin_small_a", -1.82, 0.0, -2.0, 0, tag="bin"))
    D.append(W("furniture_picture_frame_a", 1.45, 1.55, HD - 0.03, 180))
    D.append(W("furniture_fairy_lights", 1.1, 2.15, HD - 0.04, 180))
    D.append(W("furniture_picture_frame_c", -2.07, 1.55, 1.2, 90))
    D.append(W("furniture_wall_clock", 0.0, 2.35, HD - 0.04, 180))
    D.append(W("paper_sticky_poster_roll", -1.9, 0.0, 0.1, 0))

    # curtains + wall dressing (rave identity: flyers/prints, clock)
    D.append(W("textiles_curtain_pair", 2.0, 0.95, -0.65, 270))
    D.append(W("furniture_picture_frame_b", -2.08, 1.55, -0.85, 90))
    D.append(W("furniture_picture_frame_c", -2.08, 1.62, -1.15, 90))
    D.append(W("furniture_picture_frame_a", -0.75, 1.65, -2.33, 0))
    D.append(W("furniture_picture_frame_b", -1.45, 2.0, 2.33, 180))
    D.append(W("electronics_radio_cassette", -1.93, 0.768, 1.55, 90))
    D.append(W("paper_flyers_a", -1.93, 1.468, 0.95, 90))

    # ------------------------------------------------------------------ cleanable tasks (>= 8, 6+ different actions)
    CL.append(clean("bed", "Make the bed", "make", "N",
                    PL("textiles_bedding_messy", "bed", 0, 0, 0), PL("textiles_bedding_made", "bed", 0, 0, 0),
                    messy_extra=[PL("textiles_pillow_messy_a", "bed", 0.2, 0.52, -0.75, 20), PL("textiles_pillow_messy_b", "bed", -0.22, 0.52, -0.78, -35)],
                    tidy_extra=[PL("textiles_pillow_made_a", "bed", 0.2, 0.52, -0.78, 0), PL("textiles_pillow_made_b", "bed", -0.22, 0.52, -0.78, 0)],
                    radius=0.5, height=0.3))
    CL.append(clean("clothes_bed", "Fold the clothes", "fold", "N",
                    PL("textiles_clothes_pile_a", "bed", 0, 0.56, 0.62, 10), PL("textiles_folded_stack_a", "bed", 0, 0.56, 0.62, 0), radius=0.3, height=0.2))
    CL.append(clean("records", "Put the records away", "swap", "N",
                    PL("paper_records_scattered", "bed", 0, 0.57, -0.05, 90), PL("paper_record_crate", "bookcase", 0.0, 0.418, 0.0, 0), radius=0.35, height=0.12))
    CL.append(clean("books_desk", "Stack the books", "stack", "E",
                    PL("paper_books_scattered_a", "desk", -0.36, 0.74, 0.0, 0), PL("paper_books_stacked_a", "bookcase", 0.25, 1.118, 0.0, 90),
                    radius=0.32, height=0.15))
    CL.append(clean("papers_desk", "Square up the papers", "swap", "E",
                    PL("paper_papers_scattered_b", "desk", 0.1, 0.742, 0.02, 0), PL("paper_papers_neat", "desk", -0.2, 0.742, 0.1, 0), radius=0.3, height=0.06))
    CL.append(clean("cables", "Coil the cables", "coil", "E",
                    PL("kitchen_cables_tangled_a", "tvstand", 0.0, 0.45, 0.12, 0), PL("kitchen_cables_coiled", "tvstand", 0.0, 0.45, 0.12, 0), radius=0.2, height=0.06))
    CL.append(clean("mug_desk", "Take the mug to the tray", "slide", "E",
                    PL("kitchen_mug_dirty_a", "desk", -0.2, 0.74, -0.15, 30), PL("kitchen_mug_dirty_a", "dishtray", 0.1, 0.06, 0.0, 0), radius=0.12, height=0.1))
    CL.append(clean("plate_bed", "Take the plate to the tray", "slide", "N",
                    PL("kitchen_plate_leftovers_a", "bed", -0.2, 0.575, 0.25, 0), PL("kitchen_plate_leftovers_a", "dishtray", 0.0, 0.12, 0.0, 0), radius=0.18, height=0.05))
    CL.append(clean("mug_bedside", "Clear the mug", "slide", "N",
                    PL("kitchen_mug_dirty_b", "bedside", -0.1, 0.5, 0.05, -20), PL("kitchen_mug_dirty_b", "dishtray", -0.1, 0.06, 0.05, 0), radius=0.12, height=0.11))
    CL.append(clean("cans_desk", "Bin the cans", "bin", "E",
                    PL("kitchen_can_c", "desk", 0.62, 0.74, 0.28, 0), target="bin", radius=0.12, height=0.08))
    CL.append(clean("pizza", "Bin the pizza box", "bin", "S",
                    PL("kitchen_pizza_box_closed", "fridge", 0.0, 0.85, 0.0, 0), target="bin", radius=0.25, height=0.07))
    CL.append(clean("takeaway", "Bin the takeaway", "bin", "S",
                    PL("kitchen_takeaway_cartons", "kitchen", 0.0, 0.905, 0.0, 0), target="bin", radius=0.2, height=0.28))
    CL.append(clean("crisps", "Bin the crisp packet", "bin", "N",
                    PL("kitchen_crisp_packet_a", "bed", 0.2, 0.57, 0.1, 40), target="bin", radius=0.15, height=0.05))
    CL.append(clean("backpack", "Zip up the backpack", "zip", "E",
                    PL("textiles_backpack_open_spilled", "chair", 0, 0.5, 0, 0), PL("textiles_backpack_closed", "chair", 0, 0.5, 0, 0), radius=0.3, height=0.4))
    CL.append(clean("towel", "Fold the towel", "fold", "S",
                    PL("textiles_towel_crumpled", "radiator", 0.0, 0.72, 0.0, 0), PL("textiles_towel_folded", "radiator", 0.0, 0.72, 0.0, 0), radius=0.25, height=0.18))
    CL.append(clean("laundry", "Put the laundry in the basket", "bin", "W",
                    PL("textiles_clothes_pile_b", "bookcase", 0.0, 0.768, 0.0, 0), target="basket", radius=0.3, height=0.2))

    # ------------------------------------------------------------------ exterior: the street (south = shop, west = club)
    G = room["ground"]
    def box(mat, x0, x1, z0, z1, y0=-0.08, y1=0.0, uv=1.0):
        return {"material": mat, "min": v(x0, y0, z0), "max": v(x1, y1, z1), "uvPerMetre": uv}
    G.append(box("paving", -40, 40, -4.6, -2.46))          # near pavement (south)
    G.append(box("asphalt", -40, 40, -10.4, -4.6))         # road (south)
    G.append(box("paving", -40, 40, -12.6, -10.4))         # far pavement (south)
    G.append(box("paving", -4.6, -2.46, -2.46, 30))        # near pavement (west)
    G.append(box("asphalt", -10.4, -4.6, -4.6, 30))        # road (west)
    G.append(box("paving", -12.6, -10.4, -10.4, 30))       # far pavement (west)
    X = room["exteriors"]
    def E(prop, x, y, z, yaw=0.0, view="", scale=1.0, id_=None):
        return {"id": id_ or prop, "prop": prop, "pos": v(x, y, z), "euler": v(0, yaw, 0), "scale": scale, "view": view}
    X.append(E("exterior_shop_corner", 1.0, 0, -12.6, 0, "shop"))
    X.append(E("exterior_terrace_a", -7.0, 0, -12.6, 0, "shop", id_="terrace_left"))
    X.append(E("exterior_terrace_b", 9.0, 0, -12.6, 0, "shop", id_="terrace_right"))
    X.append(E("exterior_parked_car_a", 5.0, 0, -9.0, 0, "shop"))
    X.append(E("exterior_parked_car_b", -3.0, 0, -5.6, 0, "shop"))
    X.append(E("exterior_street_lamp", -1.8, 0, -4.4, 0, "shop"))
    X.append(E("exterior_club_building", -12.7, 0, 0.1, 90, "club"))
    X.append(E("exterior_terrace_a", -12.7, 0, 9.2, 90, "club", id_="club_neighbour_n"))
    X.append(E("exterior_terrace_b", -12.7, 0, -9.6, 90, "club", id_="club_neighbour_s"))
    X.append(E("exterior_parked_car_b", -6.2, 0, 8.0, 90, "club"))
    X.append(E("exterior_street_lamp", -4.3, 0, 1.6, 0, "club", id_="club_lamp"))
    X.append(E("exterior_shop_props", 1.0, 0, -11.4, 0, "shop"))
    L = room["lights"]
    def col(r, g, b): return {"r": r, "g": g, "b": b, "a": 1}
    L.append({"name": "Sun", "type": "directional", "euler": v(24, 95, 0), "color": col(1.0, 0.62, 0.36), "intensity": 0.55,
              "shadows": "soft", "role": "sun"})
    L.append({"name": "ClubMagenta", "type": "point", "pos": v(-5.5, 3.0, 0.1), "color": col(1.0, 0.15, 0.75), "intensity": 2.2, "range": 9, "shadows": "none", "role": "venue", "pulseHz": 2.9, "pulseDepth": 0.55})
    L.append({"name": "ClubCyan", "type": "point", "pos": v(-5.0, 2.2, 1.6), "color": col(0.1, 0.8, 1.0), "intensity": 1.6, "range": 8, "shadows": "none", "role": "venue", "pulseHz": 1.45, "pulseDepth": 0.5})
    L.append({"name": "ShopGlow", "type": "point", "pos": v(1.0, 2.5, -6.0), "color": col(1.0, 0.8, 0.5), "intensity": 1.0, "range": 10, "shadows": "none", "role": "shop"})
    L.append({"name": "RoomPendant", "type": "point", "pos": v(0, H - 0.75, 0), "color": col(1.0, 0.84, 0.62), "intensity": 1.05,
              "range": 7, "shadows": "none", "role": "room"})
    return room


if __name__ == "__main__":
    room = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(room, f, indent=2)
    print("wrote", OUT, "furniture", len(room["furniture"]))
