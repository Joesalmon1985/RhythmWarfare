"""The Gospel path's four maps (docs/THREE_PATHS_AND_FACES_PLAN.md section 4, Stage 3), authored as data.

A VIEW is one room of a map: a rectangle x -8..8, z -12..4 (metres, the camera stands near z 1 looking toward -z) with its own floor, boundary walls, sky, light, props and
people. A map is a row of views side by side (18 m apart) joined by a SPINE road behind them (z 4..8): a view's south wall has a portal onto the spine, so the rail camera walks
from any room to any other through it. A view may be split into BANDS (a river or lake sector in front of the far wall, a lower floor).

`build_all()` writes content/story/maps/<map>.json, content/story/<map>.json (the StoryData file: actors, groups, palettes) and returns the index the run-data generator reads
(`INDEX[view]`: waypoints, things, actors, map, room). Textures and sprites are copied from the art modules by `tools/story/build_gospel_art.py`. Everything here is original.
"""
from __future__ import annotations

import json
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPACING = 18.0
X0, X1, Z0, Z1 = -8.0, 8.0, -12.0, 4.0
EYE = 1.6

SKY = {"night": "sky_night", "dawn": "sky_dawn", "day": "sky_day", "dusk": "sky_dusk", "storm": "sky_storm", "morning": "sky_morning", "lake": "sky_lake", "grove": "sky_grove"}
# Open-air views are not boxes (docs/art/VISUAL_AUDIT.md F7): their walls are low banks (OPEN_H metres, or OPEN_BAND_H when a lake or river runs in front of the far wall, whose floor sits 0.4 below),
# so the sky strip's hills and far shore (tools/story/art/gospel_tex.py) rise behind them at eye level; the enclosed yards, streets and courts keep their tall house walls.
OPEN_H = 1.2
OPEN_BAND_H = 0.8
# time of day: sector light (0..1), tint, distance fog colour/density
TOD = {
    "night": (0.34, "#4a5ab0", "#10163a", 0.020),
    "dawn": (0.5, "#ffc89a", "#e8c0a0", 0.014),
    "day": (0.43, "#fff0d0", "#d6c8a8", 0.010),
    "morning": (0.45, "#ffecc8", "#e2d4b0", 0.010),
    "dusk": (0.5, "#ff9a60", "#c08060", 0.014),
    "storm": (0.36, "#6a80a8", "#2a3440", 0.022),
    "dark": (0.40, "#9070a0", "#30203a", 0.020),
    "indoor": (0.6, "#ffd8a0", "#c0a080", 0.010),
}
ACTS_DEFAULT = {"quiet": ["stand", "sit", "watch"], "dancing": ["stand", "watch", "wave"], "hype": ["wave", "watch", "point"], "euphoric": ["wave", "watch"]}


def P(aid, wear, x, z, act="", **kw):
    """One person of a view: id, wardrobe archetype, place, and a locked activity ('' = picks by the crowd's mood)."""
    d = {"id": aid, "wear": wear, "at": [x, z], "activity": act}
    d.update(kw)
    return d


def T(tid, sprite, x, z, size, **kw):
    """One prop of a view: a billboard thing (`piece`: shown only while the scene switches it on)."""
    d = {"id": tid, "sprite": sprite, "at": [x, z], "size": size}
    d.update(kw)
    return d


def LT(lid, x, z, y, radius, color, strength, **kw):
    d = {"id": lid, "kind": "light", "at": [x, z], "y": y, "radius": radius, "color": color, "strength": strength}
    d.update(kw)
    return d


def V(vid, map_id, idx, tod, floor, far, side_l, side_r, back, props, people, *, sky=None, bands=None, exits=None, rail_x=0.0, light=None, tint=None, acts=None, ceil="sky",
      wall_h=3.4, doors=None):
    return {"id": vid, "map": map_id, "idx": idx, "tod": tod, "floor": floor, "far": far, "side_l": side_l, "side_r": side_r, "back": back, "props": props, "people": people,
            "sky": sky or tod, "bands": bands, "exits": exits or {}, "light": light, "tint": tint, "acts": acts or ACTS_DEFAULT, "ceil": ceil, "wall_h": wall_h}


# the three exit doorways every view offers (a waypoint each: the lit way on, up the middle or at either side)
NEAREST_PERSON_Z = -3.0  # no person stands nearer the camera than this (the rail walks the camera up to z 0.4)
EXIT_AT = {"up": (0.0, -9.6), "left": (-6.2, -8.2), "right": (6.2, -8.2)}

VIEWS: list[dict] = []


def _v(*a, **k):
    v = V(*a, **k)
    VIEWS.append(v)
    return v


# ======================================================================================================================================================
# galilee_shore: the world `jordan` (J00 to J03)
# ======================================================================================================================================================
_v("bank_night", "galilee_shore", 0, "night", "floor_dust", "wall_hill", "wall_hill", "wall_reeds", "wall_rock",
   [T("stable", "thing_stable", 3.6, -9.0, 3.4), T("star", "thing_star", 3.6, -10.0, 1.7, piece="star", y=5.2, blend="add"),
    T("fire", "thing_fire", -3.4, -4.4, 1.0, anim="flicker"), T("hay", "thing_hay", 5.8, -7.4, 0.9),
    T("sheep1", "thing_sheep", -6.2, -7.0, 0.75), T("sheep2", "thing_sheep", -5.0, -9.0, 0.75), T("sheep3", "thing_sheep_lie", -1.2, -8.2, 0.6), T("sheep4", "thing_sheep", 1.0, -6.6, 0.75),
    T("sheep5", "thing_sheep_lie", -7.0, -2.4, 0.6), T("rock1", "thing_rock_c", -7.2, -11.0, 2.8), T("rock2", "thing_rock_b", 7.2, -2.0, 1.4), T("rock3", "thing_rock_a", -2.4, -2.0, 0.8),
    T("grass1", "thing_grass", 0.0, -3.0, 0.55), T("grass2", "thing_grass", 5.4, -4.0, 0.55), T("grass3", "thing_grass", -4.6, -10.0, 0.55), T("reeds1", "thing_reeds", 7.3, -6.0, 1.6),
    T("town", "thing_town_far", -3.0, -11.6, 4.2),
    LT("lt_stable", 3.6, -7.6, 2.0, 8.0, "#ffd080", 1.7), LT("lt_fire", -3.4, -4.4, 1.0, 6.0, "#ff9a40", 1.4), LT("lt_star", 3.6, -9.0, 5.0, 11.0, "#fff0c0", 0.9)],
   [P("sh1", "shepherd", -4.4, -3.2, "stand"), P("sh2", "shepherd", -2.0, -5.8, "stand"), P("sh3", "shepherd", -5.6, -5.4, "stand"), P("sh4", "shepherd", -2.6, -2.7, "sit"),
    P("m1", "mother", 2.0, -6.2, "stand"), P("el1", "elder", 5.6, -4.8, "watch")])

_v("bank_dawn", "galilee_shore", 1, "dawn", "floor_sand", "wall_hill", "wall_reeds", "wall_reeds", "wall_rock",
   [T("dove", "thing_dove", 0.0, -8.0, 1.8, piece="dove", y=3.6, blend="mix"), T("palm1", "thing_palm", -6.8, -9.4, 5.2), T("palm2", "thing_palm", 6.8, -10.4, 5.0),
    T("town", "thing_town_far", 5.2, -11.6, 4.6), T("reeds1", "thing_reeds", -7.2, -3.2, 1.6), T("reeds2", "thing_reeds", 7.3, -2.6, 1.6), T("reeds3", "thing_reeds", -6.4, -7.2, 1.7),
    T("reeds4", "thing_reeds", 6.4, -7.6, 1.7), T("rock1", "thing_rock_b", 5.2, -3.4, 1.3), T("rock2", "thing_rock_a", -5.6, -1.6, 0.8), T("grass1", "thing_grass", 2.0, -1.6, 0.5),
    T("grass2", "thing_grass", -2.6, -3.0, 0.5), T("waves", "thing_waves", 0.0, -6.8, 0.7, blend="mix"),
    LT("lt_dawn", 0.0, -6.0, 3.0, 14.0, "#ffd9a8", 1.0)],
   [P("b1", "baptist", 0.0, -8.4, "stand"), P("v1", "villager", -3.6, -2.4, "stand"), P("v2", "villager", -1.8, -3.6, "watch"), P("v3", "villager", 2.0, -3.2, "stand"),
    P("v4", "villager", 4.2, -2.2, "watch"), P("v5", "woman", -5.0, -3.9, "stand"), P("v6", "elder", 5.6, -4.0, "sit"), P("k1", "child", 1.0, -1.8, "stand")],
   bands=[(-6.5, 4.0, "floor_sand", 0.0, ""), (-12.0, -6.5, "floor_water", -0.4, "_river")])

_v("rocks", "galilee_shore", 2, "day", "floor_dust", "wall_rock", "wall_rock", "wall_rock", "wall_rock",
   [T("rockA", "thing_rock_c", -6.4, -9.4, 3.2), T("rockB", "thing_rock_c", 6.6, -9.0, 3.0), T("rockC", "thing_rock_b", -3.0, -10.4, 1.8), T("rockD", "thing_rock_b", 3.4, -10.6, 1.8),
    T("rockE", "thing_rock_a", -4.4, -2.4, 0.9), T("rockF", "thing_rock_b", 4.6, -1.8, 1.3), T("rockG", "thing_rock_a", 7.0, -5.0, 1.0), T("bush1", "thing_bush", -1.0, -3.0, 1.0),
    T("bush2", "thing_bush", 5.4, -6.4, 1.1), T("grass1", "thing_grass", 1.0, -2.6, 0.5), T("bread", "thing_basket_full", 1.6, -5.6, 0.55),
    T("fires", "thing_fire", -6.4, -11.0, 0.9, anim="flicker"), T("fires2", "thing_fire", -5.0, -11.2, 0.8, anim="flicker"), T("village", "thing_town_far", -4.6, -11.7, 3.4),
    LT("lt_fires", -5.6, -10.8, 1.4, 6.0, "#ff9a40", 0.9)],
   [P("t1", "tempter", 2.4, -6.4, "stand")])

_v("workshop", "galilee_shore", 3, "morning", "floor_clay", "wall_door", "wall_limestone", "wall_limestone", "wall_limestone",
   [T("bench", "thing_workbench", -3.2, -8.6, 1.3), T("planks", "thing_planks", -6.4, -7.0, 1.8), T("cart", "thing_cart", 5.0, -6.6, 1.6), T("jars", "thing_jars", 6.6, -9.6, 0.9),
    T("house", "thing_house_a", -6.6, -10.6, 3.4), T("stool", "thing_stool", -1.4, -6.4, 0.5), T("olive", "thing_olive_small", 7.0, -2.4, 2.6), T("grass1", "thing_grass", 0.4, -2.6, 0.5),
    T("hay", "thing_hay", 3.2, -2.2, 0.8),
    T("door1", "thing_door", -0.6, -11.92, 2.0), T("door2", "thing_door", 5.4, -11.92, 2.0)],
   [P("c1", "carpenter", -2.2, -6.8, "check"), P("n1", "villager", 2.6, -9.0, "stand"), P("k1", "child", -5.0, -3.4, "stand"), P("v1", "woman", 0.2, -4.2, "watch")],
   exits={"up": (0.0, -10.0)})

# ======================================================================================================================================================
# hillside: the world `galilee` (J04 to J07)
# ======================================================================================================================================================
_v("lakeshore", "hillside", 0, "day", "floor_shingle", "wall_hill", "wall_hill", "wall_hill", "wall_rock",
   [T("boat1", "thing_boat", -4.6, -4.6, 2.6), T("boat2", "thing_boat", 5.0, -3.2, 2.4), T("boat_far", "thing_boat_far", 3.0, -9.0, 1.0), T("boat_far2", "thing_boat_far", -3.0, -10.4, 0.8),
    T("nets1", "thing_nets", -1.2, -4.0, 2.0), T("nets2", "thing_nets", 2.4, -4.6, 2.0), T("rack", "thing_fishrack", 6.6, -6.4, 1.6), T("waves", "thing_waves", 0.0, -6.0, 0.8, blend="mix"),
    T("rock1", "thing_rock_b", -7.0, -2.0, 1.4), T("rock2", "thing_rock_a", 6.8, -1.4, 0.8), T("palm", "thing_palm", -7.0, -6.4, 5.0), T("grass1", "thing_grass", 0.8, -1.2, 0.5)],
   [P("f1", "fisher", -2.6, -3.0, "stand"), P("f2", "fisher", -0.4, -2.8, "stand"), P("f3", "fisher", 3.6, -2.2, "sit"), P("f4", "fisher", -6.0, -3.2, "stand"), P("f5", "elder", 1.2, -5.4, "stand"),
    P("k1", "child", 5.6, -4.6, "stand")],
   bands=[(-6.0, 4.0, "floor_shingle", 0.0, ""), (-12.0, -6.0, "floor_water", -0.4, "_lake")])

_v("street", "hillside", 1, "day", "floor_cobble", "wall_limestone", "wall_door", "wall_limestone", "wall_limestone",
   [T("houseA", "thing_house_a", -5.4, -10.8, 3.6), T("houseB", "thing_house_b", 5.2, -10.8, 3.2), T("caravan", "thing_caravan", 1.0, -11.2, 2.2), T("jars", "thing_jars", -6.8, -4.4, 0.9),
    T("donkey", "thing_donkey", 6.4, -5.4, 1.3), T("mat", "thing_hay", -1.4, -6.0, 0.55), T("palm", "thing_palm", 7.2, -9.4, 5.0), T("bench", "thing_bench", -4.6, -2.0, 0.7),
    T("jar2", "thing_jar", 3.0, -2.0, 0.7), T("grass1", "thing_grass", 4.6, -3.4, 0.5),
    T("door1", "thing_door", -7.85, -9.6, 2.0), T("door2", "thing_door", -7.85, -5.2, 2.0)],
   [P("p1", "villager", -2.4, -4.6, "stand"), P("p2", "woman", -0.4, -4.8, "stand"), P("k1", "child", -1.4, -6.0, "lie"), P("e1", "elder", 2.6, -4.6, "stand"),
    P("v1", "villager", 5.0, -2.6, "watch"), P("v2", "woman", -6.0, -2.2, "stand"), P("v3", "villager", 3.8, -6.8, "stand")])

_v("slope", "hillside", 2, "day", "floor_grass", "wall_hill", "wall_hill", "wall_hill", "wall_rock",
   [T("hill", "thing_hill_mount", 0.0, -11.7, 5.2), T("boat_far", "thing_boat_far", 4.0, -9.4, 1.0), T("rock1", "thing_rock_b", -1.0, -9.4, 1.4), T("rock2", "thing_rock_a", 5.4, -2.0, 0.8),
    T("bush1", "thing_bush", -7.0, -5.0, 1.0), T("flowers1", "thing_flowers", 2.0, -2.2, 0.6), T("flowers2", "thing_flowers", -4.4, -1.6, 0.6), T("olive", "thing_olive_small", 7.0, -7.0, 2.6),
    T("grass1", "thing_grass", -2.4, -4.4, 0.5), T("waves", "thing_waves", 0.0, -9.6, 0.7, blend="mix")],
   [P(f"c{i}", w, x, z, "sit") for i, (w, x, z) in enumerate([("villager", -5.0, -3.8), ("woman", -3.4, -5.0), ("villager", -1.6, -3.4), ("elder", 0.4, -5.4), ("woman", 2.0, -3.6),
                                                             ("villager", 3.8, -5.0), ("child", -4.2, -6.6), ("villager", 5.6, -3.4)], 1)]
   + [P("h1", "villager", -6.4, -7.8, "stand")] + [P(f"d{i:02d}", "disciple", x, z, "stand") for i, (x, z) in enumerate([(-1.8, -7.8), (0.0, -8.4), (1.8, -7.8), (3.4, -8.2)], 1)],
   bands=[(-9.0, 4.0, "floor_grass", 0.0, ""), (-12.0, -9.0, "floor_water", -0.5, "_lake")])

_v("storm", "hillside", 3, "storm", "floor_shingle", "wall_hill", "wall_hill", "wall_hill", "wall_rock",
   [T("boat", "thing_boat", 0.0, -7.8, 2.8), T("cloud", "thing_storm_cloud", 0.0, -11.4, 6.0, piece="storm_cloud", y=7.0, blend="mix"), T("rain", "thing_rain", 0.0, -3.0, 5.0, piece="rain", y=2.5, blend="mix"),
    T("bolt", "thing_lightning", -3.0, -11.2, 9.0, piece="lightning", y=5.5, blend="add"), T("waves", "thing_waves", 0.0, -8.4, 0.9, blend="mix"), T("waves2", "thing_waves", -4.0, -9.4, 0.8, blend="mix"),
    T("beacon", "thing_fire", -6.2, -2.4, 1.3, anim="flicker"), T("rock1", "thing_rock_b", 6.4, -2.6, 1.5), T("rock2", "thing_rock_c", 7.0, -9.0, 2.6), T("palm", "thing_palm", 7.4, -5.6, 5.0),
    LT("lt_beacon", -6.2, -2.4, 1.2, 9.0, "#ff9a40", 1.5), LT("lt_flash", 0.0, -6.0, 5.0, 14.0, "#c8d8ff", 0.5)],
   [P(f"d{i:02d}", "disciple", x, z, "stand") for i, (x, z) in enumerate([(-2.6, -5.6), (-1.4, -4.6), (-0.2, -5.8), (1.0, -4.8), (2.2, -5.6), (3.2, -4.4), (-3.6, -4.4), (4.2, -5.4)], 1)]
   + [P("f1", "fisher", 5.6, -2.0, "stand")],
   bands=[(-7.0, 4.0, "floor_shingle", 0.0, ""), (-12.0, -7.0, "floor_water", -0.4, "_lake")])

# ======================================================================================================================================================
# bethany: the world `road` (J08 to J10)
# ======================================================================================================================================================
_v("courtyard", "bethany", 0, "day", "floor_clay", "wall_limestone", "wall_mudbrick", "wall_mudbrick", "wall_limestone",
   [T("table", "thing_table_meal", 0.0, -6.4, 1.2), T("stool1", "thing_stool", -2.6, -5.0, 0.5), T("stool2", "thing_stool", 2.6, -5.0, 0.5), T("jars", "thing_jars", -6.6, -9.4, 0.9),
    T("house", "thing_house_b", 5.8, -10.8, 3.2), T("olive", "thing_olive_small", -6.6, -3.6, 2.6), T("donkey", "thing_donkey", 6.4, -3.8, 1.3), T("lantern", "thing_lantern", -3.8, -8.2, 1.0),
    T("hay", "thing_hay", 6.8, -7.0, 0.8), T("grass1", "thing_grass", 0.0, -2.0, 0.5)],
   [P("s1", "sister", -1.2, -7.6, "stand"), P("s2", "sister", 1.2, -7.6, "stand")]
   + [P(f"d{i:02d}", "disciple", x, z, "sit") for i, (x, z) in enumerate([(-2.8, -6.0), (2.8, -6.2), (-4.2, -4.6), (4.4, -4.2)], 1)] + [P("d12", "disciple", 0.6, -4.4, "stand")])

_v("hill_dusk", "bethany", 1, "dusk", "floor_grass", "wall_hill", "wall_hill", "wall_hill", "wall_rock",
   [T("basket1", "thing_basket", -2.4, -4.4, 0.6), T("basket2", "thing_basket", 0.0, -5.0, 0.6), T("basket3", "thing_basket", 2.4, -4.4, 0.6),
    T("full1", "thing_basket_full", -2.4, -4.4, 0.7, piece="full1"), T("full2", "thing_basket_full", 0.0, -5.0, 0.7, piece="full2"), T("full3", "thing_basket_full", 2.4, -4.4, 0.7, piece="full3"),
    T("hill", "thing_hill_mount", 0.0, -11.7, 5.0), T("rock1", "thing_rock_b", 6.8, -2.4, 1.4), T("olive", "thing_olive", -7.0, -8.8, 3.6), T("grass1", "thing_grass", 4.0, -2.0, 0.5),
    T("lantern", "thing_lantern", 4.8, -6.2, 1.0), T("bush1", "thing_bush", -5.0, -10.0, 1.0), T("flowers1", "thing_flowers", -4.6, -1.6, 0.6),
    LT("lt_lantern", 4.8, -6.0, 1.2, 6.0, "#ffc070", 1.3)],
   [P(f"c{i}", w, x, z, "sit") for i, (w, x, z) in enumerate([("villager", -5.0, -3.4), ("woman", -3.8, -6.2), ("child", -1.4, -3.0), ("elder", 1.4, -3.2), ("villager", 3.6, -3.2),
                                                             ("woman", 5.4, -4.2), ("child", -6.0, -5.4), ("villager", 0.4, -7.0)], 1)]
   + [P("tr1", "villager", 5.4, -6.4, "stand")] + [P(f"d{i:02d}", "disciple", x, z, "stand") for i, (x, z) in enumerate([(-1.0, -5.8), (1.2, -5.8)], 1)])

_v("gate", "bethany", 2, "day", "floor_road", "wall_city", "wall_limestone", "wall_limestone", "wall_limestone",
   [T("gate", "thing_citygate", 0.0, -11.0, 7.5), T("palm1", "thing_palm", -6.6, -7.0, 5.4), T("palm2", "thing_palm", 6.6, -7.0, 5.4), T("palm3", "thing_palm", -7.0, -2.4, 5.0), T("palm4", "thing_palm", 7.0, -2.0, 5.0),
    T("stairs", "thing_stairs", -5.4, -9.2, 2.4), T("olive", "thing_olive", 6.0, -10.0, 3.6), T("grass1", "thing_grass", 2.6, -2.6, 0.5), T("jar", "thing_jar", -3.6, -2.4, 0.7),
    T("crenA", "thing_crenels", -4.0, -11.96, 0.5, y=4.75), T("crenB", "thing_crenels", 4.0, -11.96, 0.5, y=4.75)],
   [P(f"cr{i}", w, x, z, "wave") for i, (w, x, z) in enumerate([("villager", -4.6, -3.0), ("woman", -2.8, -4.0), ("villager", -0.6, -3.0), ("elder", 1.6, -3.6), ("woman", 3.4, -3.0),
                                                              ("villager", 5.0, -4.2), ("villager", -6.0, -5.0), ("woman", 6.4, -5.8)], 1)]
   + [P("pr1", "priest", -1.6, -8.2, "stand"), P("pr2", "priest", 1.6, -8.2, "stand"), P("k1", "child", 0.2, -1.4, "stand")],
   exits={"up": (-5.4, -7.6), "left": (-6.4, -5.6), "right": (6.2, -8.2)}, wall_h=4.5)

# ======================================================================================================================================================
# jerusalem: the world `jerusalem` (J11 to J16)
# ======================================================================================================================================================
_v("temple", "jerusalem", 0, "day", "floor_flag", "wall_columns", "wall_columns", "wall_columns", "wall_limestone",
   [T("front", "thing_temple_front", 0.0, -11.2, 6.6), T("pillar1", "thing_pillar", -5.4, -9.4, 5.0), T("pillar2", "thing_pillar", 5.4, -9.4, 5.0), T("pillar3", "thing_pillar", -5.8, -3.4, 5.0),
    T("pillar4", "thing_pillar", 5.8, -3.4, 5.0),
    T("t1_up", "thing_table_coins", -3.8, -6.4, 1.1, piece="t1_up"), T("t2_up", "thing_table_coins", 0.0, -7.0, 1.1, piece="t2_up"), T("t3_up", "thing_table_coins", 3.8, -6.4, 1.1, piece="t3_up"),
    T("t1_over", "thing_table_over", -3.8, -6.4, 1.1, piece="t1_over"), T("t2_over", "thing_table_over", 0.0, -7.0, 1.1, piece="t2_over"), T("t3_over", "thing_table_over", 3.8, -6.4, 1.1, piece="t3_over"),
    T("jar1", "thing_jar", -2.0, -4.4, 0.7), T("brazier", "thing_brazier", 2.0, -4.2, 1.0), T("spears", "thing_spears", 7.0, -7.6, 2.0),
    T("col1", "thing_column", -7.4, -11.9, 4.6), T("col2", "thing_column", 7.4, -11.9, 4.6), T("col3", "thing_column", -7.85, -6.6, 4.6), T("col4", "thing_column", 7.85, -6.6, 4.6)],
   [P("mc1", "merchant", -3.8, -8.0, "stand"), P("mc2", "merchant", 0.0, -8.6, "stand"), P("mc3", "merchant", 3.8, -8.0, "stand"), P("pr1", "priest", -6.4, -6.0, "stand"), P("pr2", "priest", 6.4, -5.6, "stand"),
    P("g1", "soldier", -2.0, -10.4, "stand"), P("g2", "soldier", 2.0, -10.4, "stand"), P("v1", "villager", -1.6, -3.0, "watch"), P("v2", "woman", 1.8, -2.6, "watch")],
   exits={"up": (-5.2, -7.8), "left": (-6.4, -2.0), "right": (6.2, -8.2)}, wall_h=5.2)

_v("grove", "jerusalem", 1, "night", "floor_soil", "wall_olive", "wall_olive", "wall_olive", "wall_olive",
   [T("olive1", "thing_olive", -6.0, -9.0, 4.0), T("olive2", "thing_olive", 6.0, -9.6, 4.2), T("olive3", "thing_olive", -6.6, -3.4, 3.6), T("olive4", "thing_olive", 6.6, -3.8, 3.8),
    T("olive5", "thing_olive_small", -1.2, -10.4, 2.8), T("olive6", "thing_olive_small", 2.6, -10.8, 2.8), T("rock1", "thing_rock_b", 0.4, -2.0, 1.2), T("rock2", "thing_rock_a", -3.8, -7.4, 0.9),
    T("torch1", "thing_torch", 6.6, -11.0, 1.4, anim="flicker"), T("torch2", "thing_torch", 7.4, -10.0, 1.4, anim="flicker"), T("grass1", "thing_grass", 2.0, -2.6, 0.5),
    LT("lt_torch", 7.0, -10.4, 1.4, 7.0, "#ff9a40", 1.4), LT("lt_moon", 0.0, -5.0, 6.0, 14.0, "#8fb4ff", 0.9)],
   [P("d09", "disciple", -3.0, -4.4, "sleep"), P("d10", "disciple", 0.0, -5.6, "sleep"), P("d11", "disciple", 3.0, -4.6, "sleep"), P("d12", "disciple", 5.4, -9.4, "stand", group="late"),
    P("g1", "soldier", 6.2, -8.4, "stand", group="late"), P("g2", "soldier", 4.6, -10.2, "stand", group="late"), P("g3", "soldier", 7.2, -7.2, "stand", group="late")], wall_h=3.6)

_v("praetorium", "jerusalem", 2, "day", "floor_flag", "wall_praetorium", "wall_praetorium", "wall_praetorium", "wall_limestone",
   [T("dais", "thing_dais", 0.0, -9.0, 2.2), T("bowl", "thing_bowl_set", 2.4, -7.6, 0.9), T("pillar1", "thing_pillar", -4.8, -10.4, 5.0), T("pillar2", "thing_pillar", 4.8, -10.4, 5.0),
    T("brazier1", "thing_brazier", -3.0, -6.8, 1.0, anim="flicker"), T("brazier2", "thing_brazier", 3.0, -6.8, 1.0, anim="flicker"), T("spears", "thing_spears", -7.0, -3.4, 2.0),
    T("bench", "thing_bench", -5.6, -8.2, 0.7), T("jar", "thing_jar", 6.6, -9.6, 0.8), T("bench2", "thing_bench", 6.0, -3.0, 0.7)],
   [P("gov", "governor", 0.0, -9.6, "stand"), P("sc1", "priest", -2.4, -7.8, "stand"), P("sc2", "merchant", 2.0, -8.4, "stand"), P("w1", "woman", -6.0, -4.6, "stand"),
    P("g1", "soldier", -3.6, -10.2, "stand"), P("g2", "soldier", 3.6, -10.2, "stand")]
   + [P(f"cr{i}", w, x, z, "stand") for i, (w, x, z) in enumerate([("villager", -3.4, -3.0), ("villager", -1.4, -4.2), ("elder", 0.8, -3.2), ("villager", 2.6, -4.0), ("priest", 4.6, -3.0), ("woman", 5.6, -5.2)], 1)],
   exits={"up": (-1.6, -11.0), "left": (-6.4, -1.0), "right": (6.4, -8.0)}, wall_h=5.2)

_v("hill", "jerusalem", 3, "dusk", "floor_rock", "wall_rock", "wall_rock", "wall_rock", "wall_rock",
   [T("hill", "thing_hill_far", 0.0, -11.7, 6.0), T("cross1", "thing_cross", -2.8, -10.4, 3.0), T("cross2", "thing_cross", 0.0, -11.0, 3.6), T("cross3", "thing_cross", 2.8, -10.4, 3.0),
    T("rockA", "thing_rock_c", -6.6, -8.6, 3.0), T("rockB", "thing_rock_c", 6.8, -9.0, 3.0), T("rock1", "thing_rock_b", 5.0, -2.2, 1.3), T("rock2", "thing_rock_a", -5.0, -1.8, 0.8),
    T("dark1", "thing_sky_dark1", 0.0, -11.9, 34.0, piece="dark1", y=14.0, blend="mix", dim_people=0.1), T("dark2", "thing_sky_dark2", 0.0, -11.9, 34.0, piece="dark2", y=14.0, blend="mix", dim_people=0.16),
    T("dark3", "thing_sky_dark3", 0.0, -11.9, 34.0, piece="dark3", y=14.0, blend="mix", dim_people=0.22), T("spears", "thing_spears", 5.4, -5.8, 2.0), T("grass1", "thing_grass", 1.0, -2.0, 0.5)],
   [P("w1", "woman", -3.6, -4.0, "stand"), P("w2", "woman", -2.2, -3.2, "stand"), P("w3", "woman", -4.8, -2.6, "stand"), P("s1", "soldier", 2.4, -6.0, "stand"), P("s2", "soldier", 4.0, -5.0, "stand"),
    P("s3", "soldier", 0.8, -7.4, "stand"), P("x1", "disciple", -6.0, -6.0, "stand"), P("x2", "villager", 6.0, -3.4, "stand"), P("x3", "elder", 3.0, -2.4, "stand")],
   exits={"up": (0.0, -8.6)})

_v("tomb", "jerusalem", 4, "morning", "floor_garden", "wall_cypress", "wall_cypress", "wall_cypress", "wall_rock",
   [T("tomb", "thing_tomb", 0.0, -10.2, 4.2), T("stone_closed", "thing_stone_closed", -0.2, -8.4, 2.0, piece="stone_closed"), T("stone_rolled", "thing_stone_rolled", 2.4, -8.4, 1.3, piece="stone_rolled"),
    T("cyp1", "thing_cypress", -5.6, -9.4, 4.4), T("cyp2", "thing_cypress", 5.8, -9.8, 4.4), T("cyp3", "thing_cypress", -7.0, -4.0, 4.0), T("cyp4", "thing_cypress", 7.0, -4.2, 4.0),
    T("flowers1", "thing_flowers", -3.0, -3.0, 0.7), T("flowers2", "thing_flowers", 3.2, -2.4, 0.7), T("flowers3", "thing_flowers", 1.0, -5.4, 0.7), T("bush1", "thing_bush", -5.0, -6.4, 1.0),
    T("olive", "thing_olive_small", 5.6, -6.6, 2.6), T("grass1", "thing_grass", -1.4, -2.0, 0.5),
    LT("lt_dawn", 0.0, -8.0, 4.0, 12.0, "#ffe0a8", 1.1)],
   [P("w1", "woman", -3.0, -3.8, "stand"), P("w2", "woman", -1.4, -2.8, "stand"), P("w3", "woman", 1.2, -3.6, "stand"), P("gd1", "gardener", 4.4, -5.0, "stand")],
   exits={"up": (0.0, -6.4)}, wall_h=4.5)

_v("road", "jerusalem", 5, "morning", "floor_road", "wall_hill", "wall_hill", "wall_hill", "wall_hill",
   [T("city", "thing_city_far", 5.6, -11.5, 3.6), T("olive", "thing_olive", -6.4, -9.0, 3.8), T("rock1", "thing_rock_b", 5.8, -2.4, 1.3), T("bush1", "thing_bush", -6.8, -3.0, 1.0),
    T("flowers1", "thing_flowers", 3.0, -2.0, 0.6), T("sheep1", "thing_sheep", -5.2, -8.0, 0.75), T("sheep2", "thing_sheep", -3.8, -9.4, 0.75), T("cart", "thing_cart", 6.4, -7.0, 1.5),
    T("grass1", "thing_grass", -2.0, -2.2, 0.5), T("wall", "thing_wall_low", -3.0, -6.0, 0.9)],
   [P("d01", "disciple", -2.0, -3.4, "stand"), P("d02", "disciple", 1.6, -3.2, "stand"), P("sp1", "shepherd", -5.0, -6.6, "stand"), P("g1", "soldier", 4.6, -6.4, "stand"), P("g2", "soldier", 6.2, -4.6, "stand"),
    P("v1", "woman", 3.6, -2.0, "stand")],
   exits={"up": (0.0, -9.4)})


# ======================================================================================================================================================
# the look of each room's boundary (art only: no wall, door, waypoint or anchor moves). vid: the walls' textures (far, left, right, back), the walls' height (the sectors' ceiling), the sky.
# Open rooms get low banks, so the sky strip shows its hills; enclosed ones keep tall walls of seamless masonry (1.2 m repeats, 107 texels per metre).
# ======================================================================================================================================================
LOOK = {
    "bank_night": dict(h=OPEN_H),
    "bank_dawn": dict(h=OPEN_BAND_H, far="wall_reeds"),
    "rocks": dict(h=OPEN_H),
    "workshop": dict(far="wall_limestone", h=2.6),
    "lakeshore": dict(h=OPEN_BAND_H, sky="lake"),
    "street": dict(side_l="wall_limestone", h=2.8),
    "courtyard": dict(h=2.8),
    "praetorium": dict(h=4.4),
    "slope": dict(h=OPEN_BAND_H, sky="lake"),
    "storm": dict(h=OPEN_BAND_H),
    "hill_dusk": dict(h=OPEN_H),
    "grove": dict(h=OPEN_H, sky="grove"),
    "hill": dict(h=OPEN_H),
    "tomb": dict(h=OPEN_H),
    "road": dict(h=OPEN_H),
    "temple": dict(far="wall_limestone", side_l="wall_limestone", side_r="wall_limestone", h=4.6),
}
for _v_ in VIEWS:
    _o = LOOK.get(_v_["id"], {})
    for _k, _a in (("far", "far"), ("side_l", "side_l"), ("side_r", "side_r"), ("back", "back"), ("h", "wall_h"), ("sky", "sky")):
        if _k in _o:
            _v_[_a] = _o[_k]


# ======================================================================================================================================================
# the builder
# ======================================================================================================================================================
def _rect(x0, z0, x1, z1):
    return [[x0, z0], [x1, z0], [x1, z1], [x0, z1]]


def _tint_of(v):
    light, tint, fogc, dens = TOD[v["tod"]]
    return (v["light"] if v["light"] is not None else light, v["tint"] or tint, fogc, dens)


def _full_ids(views: list) -> dict:
    """{(view id, local id): the actor's id in the map file}: a local id used in one view keeps its name, a repeated one (a disciple in two rooms) gets the room as a suffix."""
    count: dict = {}
    for v in views:
        for p in v["people"]:
            count[p["id"]] = count.get(p["id"], 0) + 1
    out = {}
    for v in views:
        for p in v["people"]:
            out[(v["id"], p["id"])] = p["id"] if count[p["id"]] == 1 else f"{p['id']}_{v['id']}"
    return out


def build_map(map_id: str, views: list) -> tuple[dict, dict, dict]:
    fid = _full_ids(views)
    textures: dict = {}
    sectors: list = []
    walls: list = []
    things: list = []
    homes: list = []
    wps: list = []
    skies: dict = {}
    index: dict = {}
    actors: list = []
    first = True
    xs = []
    for v in views:
        ox = v["idx"] * SPACING
        vid = v["id"]
        room = "main" if first else vid
        first = False
        light, tint, fogc, dens = _tint_of(v)
        xs += [ox + X0, ox + X1]
        bands = v["bands"] or [(Z0, Z1, v["floor"], 0.0, "")]
        skies[v["sky"]] = SKY[v["sky"]]
        for tex in (v["floor"], v["far"], v["side_l"], v["side_r"], v["back"]):
            textures[tex] = f"textures/{tex}.png"
        sec_ids = []
        for (za, zb, ftex, fh, suffix) in bands:
            sid = vid + suffix
            sec_ids.append((sid, za, zb, fh))
            textures[ftex] = f"textures/{ftex}.png"
            sec = {"id": sid, "polygon": _rect(ox + X0, za, ox + X1, zb), "floor": fh, "ceiling": v["wall_h"], "floor_tex": ftex, "ceil_tex": v["ceil"], "wall_tex": v["side_l"],
                   "light": light, "tint": tint, "room": room, "flags": [], "activities": v["acts"], "sky": v["sky"], "fog": {"color": fogc, "density": dens}}
            sectors.append(sec)
        # walls: the far edge of the farthest band, the sides of every band, the back of the nearest
        sec_ids.sort(key=lambda s: s[1])
        for k, (sid, za, zb, fh) in enumerate(sec_ids):
            if k == 0:
                walls.append({"from": [ox + X0, za], "to": [ox + X1, za], "sector": sid, "tex": v["far"]})
            walls.append({"from": [ox + X1, za], "to": [ox + X1, zb], "sector": sid, "tex": v["side_r"]})
            walls.append({"from": [ox + X0, za], "to": [ox + X0, zb], "sector": sid, "tex": v["side_l"]})
            if k + 1 < len(sec_ids):  # an open step down to the water (the nearer band declares the portal)
                nxt = sec_ids[k + 1]
                # the farther band is sec_ids[k]; the nearer is sec_ids[k+1]: declare on the nearer one's far edge
        for k in range(len(sec_ids) - 1):
            far_id = sec_ids[k][0]
            near_id, near_za = sec_ids[k + 1][0], sec_ids[k + 1][1]
            walls.append({"from": [ox + X0, near_za], "to": [ox + X1, near_za], "sector": near_id, "portal": far_id, "lower_tex": "trim", "upper_tex": v["far"]})
        near_id = sec_ids[-1][0]
        walls.append({"from": [ox + X0, Z1], "to": [ox - 2.0, Z1], "sector": near_id, "tex": v["back"]})
        walls.append({"from": [ox - 2.0, Z1], "to": [ox + 2.0, Z1], "sector": near_id, "portal": f"{map_id}_spine"})
        walls.append({"from": [ox + 2.0, Z1], "to": [ox + X1, Z1], "sector": near_id, "tex": v["back"]})
        # waypoints
        def sec_at(z):
            for sid, za, zb, fh in sec_ids:
                if za - 1e-6 <= z <= zb + 1e-6:
                    return sid
            return near_id
        W = {"home": (0.0, 1.6, 0.0), "arrive": (0.0, 3.0, 0.0), "g1": (-2.2, 1.4, 0.0), "g2": (2.4, 0.8, 0.0), "g3": (0.0, 0.4, 0.0), "b1": (-6.2, 2.6, 0.0), "b2": (6.2, 2.6, 0.0)}
        for name, (ex, ez) in EXIT_AT.items():
            ex, ez = v["exits"].get(name, (ex, ez))
            W["door_" + name] = (ex, ez, 0.0)
        wp_ids = {}
        for name, (wx, wz, yaw) in W.items():
            wid = f"{vid}.{name}"
            wps.append({"id": wid, "at": [ox + wx, wz], "yaw": yaw, "sector": sec_at(wz)})
            wp_ids[name] = wid
        # things
        thing_ids = {}
        for t in v["props"]:
            d = dict(t)
            d["id"] = f"{vid}.{t['id']}"
            d["at"] = [ox + t["at"][0], t["at"][1]]
            if d.get("kind") != "light":
                textures[d["sprite"]] = f"textures/{d['sprite']}.png"
            else:
                d["sector"] = sec_at(t["at"][1])
            if "piece" in d:
                d["piece"] = f"{vid}.{d['piece']}"
            things.append(d)
            thing_ids[t["id"]] = d["id"]
        # people
        who = {}
        for p in v["people"]:
            aid = fid[(vid, p["id"])]
            hz = min(p["at"][1], NEAREST_PERSON_Z)
            p = dict(p, at=[p["at"][0], hz])
            homes.append({"actor": aid, "sector": sec_at(hz), "at": [ox + p["at"][0], hz], "_view": vid})
            who[p["id"]] = {"id": aid, "wear": p["wear"], "view": room, "activity": p.get("activity", ""), "group": p.get("group", "core")}
            actors.append(dict(p, id=aid, _local=p["id"], _view=vid, _room=room))
        index[vid] = {"map": map_id, "room": room, "ox": ox, "waypoints": wp_ids, "things": thing_ids, "actors": who, "bands": [s[0] for s in sec_ids], "tod": v["tod"], "sky": v["sky"]}
    # the spine
    sx0, sx1 = min(xs) - 2.0, max(xs) + 2.0
    sp = {"id": f"{map_id}_spine", "polygon": _rect(sx0, Z1, sx1, Z1 + 4.0), "floor": 0.0, "ceiling": 6.0, "floor_tex": "floor_path", "ceil_tex": "sky", "wall_tex": "wall_rock", "light": 0.6, "tint": "#ffe8c8",
          "room": "spine", "flags": [], "activities": ACTS_DEFAULT, "sky": views[0]["sky"], "fog": {"color": "#c0a880", "density": 0.012}}
    sectors.append(sp)
    textures["floor_path"] = "textures/floor_path.png"
    textures["wall_rock"] = "textures/wall_rock.png"
    textures["trim"] = "textures/trim.png"
    # homes: the actor ids of a view are unique per map (a disciple keeps its id), so a repeated id in one map gets its view as a prefix in the data only if needed
    seen = {}
    for h in homes:
        seen.setdefault(h["actor"], []).append(h)
    for aid, lst in seen.items():
        if len(lst) > 1:
            raise SystemExit(f"{map_id}: actor id {aid} used in several views {[h['_view'] for h in lst]}: ids must be unique inside a map")
    for h in homes:
        h.pop("_view")
    first_view = views[0]["id"]
    m = {"units_per_m": 1, "palette_weight": 0.0, "eye_height": EYE, "start": f"{first_view}.home", "textures": dict(sorted(textures.items())), "sectors": sectors, "walls": walls,
         "things": things, "homes": homes, "waypoints": wps, "spots": {}, "silhouettes": [], "occluders": [],
         "sky": {"tex": f"textures/{SKY[views[0]['sky']]}.png", "mode": "cylinder", "repeats": 1, "horizon": 0.75, "by_name": {k: f"textures/{v}.png" for k, v in sorted(skies.items())}},
         "fog": {"color": "#40384a", "density": 0.012}, "rooms": {}, "animated": []}
    for k, v in skies.items():
        m["textures"][v] = f"textures/{v}.png"
    water = [t for t in textures if t == "floor_water"]
    if water:
        m["animated"].append({"tex": "floor_water", "mode": "scroll", "speed": [0.05, 0.02], "amount": 0.15, "bright": 0.2})
    # the StoryData file: the people (their wardrobe archetype in `wear`; a Night One rig stands in as the live-rig fallback)
    rigs = ["groover", "ponytail", "hoodie", "curly", "bob", "punk"]
    sd_actors = []
    for a in actors:
        h = zlib.crc32(a["id"].encode())
        sd_actors.append({"id": a["id"], "archetype": rigs[h % 6], "variant": "ab"[(h >> 3) % 2], "group": a.get("group", "core"), "view": a["_room"], "wear": a["wear"], "seed_id": a["_local"] if (a["_local"][0] == "d" and a["_local"][1:].isdigit()) else f"{map_id}/{a['id']}",
                          **({"activity": a["activity"]} if a.get("activity") else {}), "thresh": ((h >> 5) % 13) - 6, **{k: a[k] for k in ("prop", "target") if k in a}})
    sd = {"id": map_id, "title": map_id.replace("_", " ").title(), "chapter": 9, "art": map_id, "description": "A map of the Gospel path (content/paths/gospel).", "intro": "",
          "duration_bars": 128, "sequence_bars": 2, "initial_energy": 60, "blocks": [], "decisions": [], "endings": {}, "ending_order": [], "acts": [],
          "groups": {"all": [a["id"] for a in sd_actors]}, "actors": sd_actors, "silhouettes": [],
          "palettes": {"low": ["#7a5a4a", "#a8785a"], "cool": ["#6a8ac8", "#9aa8d8"], "warm": ["#ffb060", "#ff8a50"], "rave": ["#ffc060", "#8ab0ff", "#ff9060", "#ffe090"]},
          "energy": {"pass_delta": {"sharp": 4, "steady": 3, "loose": 2}, "fail_delta": -5, "min": 0, "max": 100,
                     "bands": [{"id": "quiet", "label": "Quiet", "max": 29}, {"id": "dancing", "label": "Gathered", "max": 64}, {"id": "hype", "label": "Moved", "max": 84}, {"id": "euphoric", "label": "Joyful", "max": 100}]}}
    return m, sd, index


MAPS = ["galilee_shore", "hillside", "bethany", "jerusalem"]
INDEX: dict = {}


def build_all(write: bool = True) -> dict:
    out = {}
    for mid in MAPS:
        views = [v for v in VIEWS if v["map"] == mid]
        m, sd, idx = build_map(mid, views)
        out[mid] = (m, sd)
        INDEX.update(idx)
        if write:
            (ROOT / "content/story/maps").mkdir(parents=True, exist_ok=True)
            (ROOT / "content/story/maps" / f"{mid}.json").write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
            (ROOT / "content/story" / f"{mid}.json").write_text(json.dumps(sd, indent=1) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    build_all()
    print({k: len(v["actors"]) for k, v in INDEX.items()})
