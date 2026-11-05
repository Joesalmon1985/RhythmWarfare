#!/usr/bin/env python3
"""Authors the Ember Road's four 2.5D maps, their chapter files and art manifests (docs/THREE_PATHS_AND_FACES_PLAN.md 6.1, D8).

    python3 tools/story/ember_maps.py            # content/story/maps/<map>.json, content/story/<map>.json (the chapter file: a world of content/paths/ember/run.json names it in `story`), assets/story/<map>/manifest.json

Rooms are axis-aligned rectangles (convex sectors); a door is a portal segment on the edge two rooms share. Every id used here (textures, things, pieces) is listed in
tools/story/art/ember_spec.py. The people (`actor(...)`) are the Ember Road's cast: `kind` picks the wardrobe (tools/story/art/wardrobe_ember.py), `person` keeps one
person's face and clothes the same wherever they stand, `view` is the scene's room (one crowd per room). The run data (scenes, hotspots, cast) is tools/run/make_ember.py.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

from art import ember_spec  # noqa: E402


class Map:
    def __init__(self, art: str, start: str, fog: dict, sky: str):
        self.art = art
        self.start = start
        self.fog = fog
        self.sky = sky
        self.rooms: dict = {}
        self.sectors: list = []
        self.walls: list = []
        self.things: list = []
        self.waypoints: list = []
        self.homes: list = []
        self.actors: list = []
        self.animated: list = []

    # -- geometry --
    def room(self, rid, x0, z0, x1, z1, floor=0.0, ceil=4.5, ftex="", ctex="sky", wtex="", light=0.6, tint="#ffffff", view="main", flags=None):
        assert x0 < x1 and z0 < z1, rid
        self.rooms[rid] = (x0, z0, x1, z1)
        self.sectors.append({"id": rid, "polygon": [[x0, z0], [x1, z0], [x1, z1], [x0, z1]], "floor": floor, "ceiling": ceil, "floor_tex": ftex, "ceil_tex": ctex, "wall_tex": wtex,
                             "light": light, "tint": tint, "room": view, "flags": flags or []})

    def door(self, a, b, width=2.0, at=None, blocked=False, lower=None, upper=None):
        """A portal from room a to room b on the edge they share (centred in the overlap, or at coordinate `at`)."""
        ax0, az0, ax1, az1 = self.rooms[a]
        bx0, bz0, bx1, bz1 = self.rooms[b]
        if abs(ax1 - bx0) < 1e-6 or abs(bx1 - ax0) < 1e-6:  # a shared vertical edge, overlap in z
            x = ax1 if abs(ax1 - bx0) < 1e-6 else ax0
            lo, hi = max(az0, bz0), min(az1, bz1)
            assert hi - lo >= width - 1e-6, (a, b, lo, hi)
            c = (lo + hi) / 2 if at is None else at
            c = min(max(c, lo + width / 2), hi - width / 2)
            p0, p1 = [x, c - width / 2], [x, c + width / 2]
        elif abs(az1 - bz0) < 1e-6 or abs(bz1 - az0) < 1e-6:  # a shared horizontal edge, overlap in x
            z = az1 if abs(az1 - bz0) < 1e-6 else az0
            lo, hi = max(ax0, bx0), min(ax1, bx1)
            assert hi - lo >= width - 1e-6, (a, b, lo, hi)
            c = (lo + hi) / 2 if at is None else at
            c = min(max(c, lo + width / 2), hi - width / 2)
            p0, p1 = [c - width / 2, z], [c + width / 2, z]
        else:
            raise AssertionError(f"{a} and {b} share no edge")
        w = {"from": p0, "to": p1, "sector": a, "portal": b}
        if blocked:
            w["blocked"] = True
        if lower:
            w["lower_tex"] = lower
        if upper:
            w["upper_tex"] = upper
        self.walls.append(w)

    def wall(self, rid, side, t0, t1, tex):
        """A textured stretch of a room's wall: side xmin / xmax / zmin / zmax, t0..t1 along it."""
        x0, z0, x1, z1 = self.rooms[rid]
        seg = {"xmin": ([x0, t0], [x0, t1]), "xmax": ([x1, t0], [x1, t1]), "zmin": ([t0, z0], [t1, z0]), "zmax": ([t0, z1], [t1, z1])}[side]
        self.walls.append({"from": seg[0], "to": seg[1], "sector": rid, "tex": tex})

    # -- things --
    def thing(self, tid, sprite, x, z, y=None, size=1.0, anim="none", piece=None, blend=None):
        t = {"id": tid, "kind": "billboard", "sprite": sprite, "at": [x, z], "size": size, "anim": anim}
        if y is not None:
            t["y"] = y
        if piece:
            t["piece"] = piece
        if blend:
            t["blend"] = blend
        self.things.append(t)

    def light(self, lid, x, z, y=2.4, radius=5.0, color="#ffc880", strength=1.0, cone=None):
        t = {"id": lid, "kind": "light", "at": [x, z], "y": y, "radius": radius, "color": color, "strength": strength}
        if cone:
            t["cone"] = {"yaw": cone[0], "angle": cone[1]}
        self.things.append(t)

    def wp(self, wid, x, z, yaw=0.0):
        self.waypoints.append({"id": wid, "at": [x, z], "yaw": yaw})

    def actor(self, aid, kind, x, z, view, activity="stand", prop=None, target=None, person=None, arch="groover", variant="a", old=False, role="front", extra=None):
        a = {"id": aid, "archetype": arch, "variant": variant, "kind": kind, "group": "core", "view": view, "role": role, "thresh": 0, "activity": activity}
        if person:
            a["person"] = person
        if prop:
            a["prop"] = prop
        if target:
            a["target"] = target
        if old:
            a["old"] = True
        if extra:
            a.update(extra)
        self.actors.append(a)
        self.homes.append({"actor": aid, "at": [x, z]})

    # -- output --
    def sector_at(self, x, z):
        for sid, (x0, z0, x1, z1) in self.rooms.items():
            if x0 < x < x1 and z0 < z < z1:
                return sid
        raise AssertionError(f"({x}, {z}) is in no room of {self.art}")

    def as_json(self) -> dict:
        tex = {}
        for kind in (ember_spec.TILES, ember_spec.THINGS):
            for tid, ent in kind[self.art].items():
                tex[tid] = f"textures/{tid}.png"
        sky_tex = {"tex": f"textures/{self.sky}.png", "mode": "cylinder"}
        for t in self.things:
            if t["kind"] == "billboard":
                assert t["sprite"] in tex, (self.art, t["sprite"])
        for s in self.sectors:
            for k in ("floor_tex", "ceil_tex", "wall_tex"):
                assert s[k] in tex or s[k] in ("", "sky"), (self.art, s["id"], k, s[k])
        for w in self.walls:
            for k in ("tex", "lower_tex", "upper_tex"):
                assert w.get(k, "") in tex or w.get(k, "") == "", (self.art, w)
        things = []
        for t in self.things:
            t = dict(t)
            t["at"] = [round(t["at"][0], 3), round(t["at"][1], 3)]
            t["sector"] = self.sector_at(*t["at"])
            things.append(t)
        homes = []
        for h in self.homes:
            homes.append({"actor": h["actor"], "sector": self.sector_at(*h["at"]), "at": h["at"]})
        wps = []
        for w in self.waypoints:
            wps.append({"id": w["id"], "at": w["at"], "yaw": w["yaw"], "sector": self.sector_at(*w["at"])})
        return {"art": self.art, "units_per_m": 1, "eye_height": 1.6, "palette_weight": 0.0, "start": self.start, "textures": dict(sorted(tex.items())), "sectors": self.sectors,
                "walls": self.walls, "things": things, "homes": homes, "waypoints": wps, "spots": {}, "silhouettes": [], "occluders": [], "sky": sky_tex, "fog": self.fog, "rooms": {}, "animated": self.animated}


def lamps(m: Map, prefix: str, pts, color="#ffc070", radius=5.5, strength=1.1, y=2.2):
    for i, (x, z) in enumerate(pts):
        m.light(f"{prefix}{i}", x, z, y, radius, color, strength)


# ======================================================================================================================================================
# orchard: the harvest orchard (E00), the ford at night (E01), the Lantern Inn (E02)   [world `hollow`]
# ======================================================================================================================================================

def orchard() -> Map:
    m = Map("orchard", "orchard_c", {"color": "#14182c", "density": 0.012}, "sky_dusk")
    m.room("o_orchard", -10, 0, 10, 16, 0, 4.5, "floor_grass", "sky", "wall_hedge", 0.66, "#ffd290", "orchard")
    m.room("o_lane", -2, -14, 2, 0, 0, 4.5, "floor_lane", "sky", "wall_hedge", 0.52, "#e8b070", "orchard")
    m.room("o_bank", -12, -26, 12, -14, 0, 5, "floor_bank", "ceil_stars", "wall_reeds", 0.62, "#8aa4e0", "ford")
    m.room("o_ford", -12, -32, 12, -26, -0.3, 5, "floor_ford", "ceil_stars", "wall_reeds", 0.64, "#7e9ade", "ford")
    m.room("o_far", -12, -42, 12, -32, 0.15, 5, "floor_bank", "ceil_stars", "wall_reeds", 0.58, "#7088d0", "ford")
    m.room("o_innroad", 12, -42, 20, -32, 0.15, 5, "floor_lane", "ceil_stars", "wall_hedge", 0.5, "#6a7ab8", "ford")
    m.room("o_inn", 12, -32, 30, -18, 0, 3.4, "floor_boards", "ceil_beams", "wall_inn", 0.58, "#ffb868", "inn")
    m.room("o_back", 30, -28, 36, -22, 0, 5, "floor_lane", "ceil_stars", "wall_reeds", 0.5, "#6a7ab8", "inn")
    m.door("o_orchard", "o_lane", 2.4)
    m.door("o_lane", "o_bank", 2.4)
    m.door("o_bank", "o_ford", 12)
    m.door("o_ford", "o_far", 12)
    m.door("o_far", "o_innroad", 3.0)
    m.door("o_innroad", "o_inn", 2.4, at=16)
    m.door("o_inn", "o_back", 1.6, at=-25)
    m.wall("o_orchard", "zmin", -10, -1.2, "wall_cottage")
    m.wall("o_orchard", "zmin", 1.2, 10, "wall_cottage")
    m.wall("o_orchard", "xmin", 0, 16, "wall_fence")
    m.wall("o_orchard", "xmax", 0, 16, "wall_fence")
    m.wall("o_inn", "zmax", 23, 27, "wall_inn_window")
    m.animated = [{"tex": "floor_ford", "mode": "scroll", "speed": [0.18, 0.0]}]

    # --- E00 the Orchard ---
    for i, (x, z) in enumerate([(-8, 4), (-8.5, 11), (8, 5), (8.5, 12), (-4, 2.5), (4.5, 2.2)]):
        m.thing(f"tree{i}", "thing_apple_tree", x, z, size=5.2 - (i % 2) * 0.5)
    m.thing("cot", "thing_cot", 0.2, 4.7, size=1.3)
    m.thing("baskets0", "thing_apple_basket", -3.4, 8.2, size=0.9)
    m.thing("baskets1", "thing_apple_basket", 4.4, 9.0, size=0.9)
    m.thing("ember_bowl", "thing_ember", 1.9, 5.4, y=0.55, size=0.85, anim="pulse")
    m.thing("hay0", "thing_hay_bale", -6, 6.5, size=1.1)
    m.thing("gate", "thing_gate", 0, 1.2, size=2.0)
    m.thing("lamp_o", "thing_lantern_post", 3.2, 7.2, size=2.6)
    m.light("sun_o", 0, 15, 3.5, 24, "#ffc878", 1.15)
    m.light("lt_cot", 0.5, 6.2, 1.2, 6.5, "#ff9a50", 1.2)
    m.light("lt_ember_o", 1.9, 5.0, 1.0, 5.0, "#ff7a30", 1.0)
    m.wp("orchard_c", 0, 13.5, 0)
    m.wp("orchard_mid", 0, 9.5, 0)
    m.wp("orchard_near", 0, 7.8, 0)
    m.wp("orchard_w", -6.5, 12.5, 15)
    m.wp("orchard_e", 6.5, 12.5, -15)
    m.wp("orchard_gate", 0, 1.8, 0)
    # the grandmother on her cot, Bram, and the village
    m.actor("gran", "grandmother", 0.2, 5.5, "orchard", "lie", person="grandmother", old=True, role="hero")
    m.actor("bram_o", "bram", -1.9, 6.3, "orchard", "stand", person="bram")
    for i, (x, z, act, tgt) in enumerate([(-3.4, 4.3, "watch", "gran"), (3.0, 4.2, "stand", None), (-4.6, 6.6, "stand", None), (4.8, 7.0, "watch", "gran")]):
        m.actor(f"vo{i}", "villager_hollow", x, z, "orchard", act, target=tgt)

    # --- E01 the Ford at Night ---
    for i, (x, z) in enumerate([(-9.5, -17), (9.5, -18), (-10, -22), (10, -23)]):
        m.thing(f"willow{i}", "thing_willow", x, z, size=5.5)
    m.thing("stones", "thing_rock_ford", 2.5, -28.5, size=1.0)
    m.thing("stones2", "thing_rock_ford", -4.0, -29.0, size=1.0)
    m.thing("stake_l", "thing_lantern_stake", -4.4, -23.4, size=2.6, anim="flicker")
    m.thing("horse0", "thing_horse_far", -6.5, -35.4, size=2.8, anim="bob")
    m.thing("horse1", "thing_horse_far", 0.5, -36.6, size=2.8, anim="bob")
    m.thing("horse2", "thing_horse_far", 7.0, -35.2, size=2.8, anim="bob")
    m.thing("river_rise", "piece_river_rise", 0, -28.8, y=1.3, size=2.6, piece="river_rise", blend="mix")
    m.thing("sign_o", "thing_signpost", -7, -19.5, size=1.9)
    m.light("moon_f", 0, -20, 4.0, 30, "#7090d0", 0.8)
    m.light("lt_stake", -4.4, -23.4, 1.8, 8.0, "#ffb060", 1.6)
    m.wp("ford_in", 0, -15.2, 0)
    m.wp("ford_c", 0, -21.8, 0)
    m.wp("ford_mid", 0, -23.4, 0)
    m.wp("ford_edge", 0, -25.0, 0)
    m.wp("ford_w", -7.5, -22.0, 12)
    m.wp("ford_e", 7.5, -22.0, -12)
    m.wp("ford_cross", 0, -25.6, 0)
    m.wp("lantern_wp", -3.2, -23.0, 15)
    m.actor("bram_f", "bram", -1.0, -28.8, "ford", "stand", person="bram", prop="", extra={"activity": "stand"})
    for i, x in enumerate([-7.5, -1.0, 6.2]):
        m.actor(f"rd_f{i}", "rider", x, -33.4 - (i % 2) * 0.6, "ford", "stare", target="camera_f", person=f"rider_f{i}")
    # (the riders face the ford; `target` names a waypoint)
    m.wp("camera_f", 0, -21.8, 0)

    # --- E02 the Lantern Inn (the camera comes in from the road and looks +z: yaw 180) ---
    m.thing("hearth", "thing_hearth", 21, -18.7, size=2.6, anim="flicker")
    m.thing("inn_t0", "thing_inn_table", 17.5, -23.5, size=1.2)
    m.thing("inn_t1", "thing_inn_table", 24.8, -23.0, size=1.2)
    m.thing("inn_t2", "thing_inn_table", 15.5, -28.0, size=1.2)
    m.thing("barrel0", "thing_barrel", 13.4, -20.0, size=1.2)
    m.thing("barrel1", "thing_barrel", 13.4, -21.4, size=1.2)
    m.thing("lamp_i0", "thing_hanging_lamp", 17.5, -23.5, y=2.5, size=0.9)
    m.thing("lamp_i1", "thing_hanging_lamp", 24.8, -23.0, y=2.5, size=0.9)
    m.thing("stool0", "thing_stool", 19.2, -22.4, size=0.8)
    m.thing("stool1", "thing_stool", 23.6, -21.6, size=0.8)
    m.thing("door_back", "thing_door_back", 29.4, -25, size=2.3)
    m.thing("rider_shadow", "piece_rider_shadow", 18.9, -18.4, y=1.6, size=2.0, piece="rider_shadow", blend="mix")
    m.light("lt_hearth", 21, -19.6, 1.2, 8.0, "#ff9040", 1.5)
    m.light("lt_inn_a", 17.5, -23.5, 2.4, 6.0, "#ffc070", 1.1)
    m.light("lt_inn_b", 24.8, -23.0, 2.4, 6.0, "#ffc070", 1.1)
    m.wp("inn_door", 16, -30.6, 180)
    m.wp("inn_c", 20, -28.6, 180)
    m.wp("inn_mid", 20, -25.8, 180)
    m.wp("inn_near", 20.5, -22.6, 180)
    m.wp("inn_w", 14.5, -27.5, 170)
    m.wp("inn_e", 26.5, -27.5, 190)
    m.wp("inn_back", 28.4, -25, 180)
    m.wp("inn_fire", 21, -21.2, 180)
    m.actor("innkeeper", "innkeeper", 16.2, -21.6, "inn", "check", prop="clipboard", target="hearth", person="innkeeper")
    m.actor("warden_i", "warden", 22.6, -20.8, "inn", "sit", person="warden")
    for i, (x, z, act, tgt) in enumerate([(17.0, -22.4, "drink", None), (18.4, -24.6, "drink", None), (24.4, -23.9, "drink", None), (26.2, -22.2, "toast", None)]):
        m.actor(f"dk{i}", "drinker", x, z, "inn", act, target=tgt)
    return m


# ======================================================================================================================================================
# birch_hall: the Birch Hall (E03) and the High Pass (E04)   [world `north`]
# ======================================================================================================================================================

def birch_hall() -> Map:
    m = Map("birch_hall", "hall_c", {"color": "#c8d4e8", "density": 0.012}, "sky_snow")
    m.room("bh_hall", -8, 0, 8, 22, 0, 5.8, "floor_birch", "ceil_hall", "wall_hall", 0.78, "#e8f0ff", "hall")
    m.room("bh_porch", -2.5, -8, 2.5, 0, 0, 4.2, "floor_birch", "ceil_hall", "wall_hall", 0.66, "#dce8ff", "pass")
    m.room("bh_pass", -12, -32, 12, -8, 0, 6, "floor_snow", "ceil_overcast", "wall_rock_snow", 0.62, "#c0d4f8", "pass")
    m.door("bh_hall", "bh_porch", 3.0)
    m.door("bh_porch", "bh_pass", 3.0)
    m.wall("bh_hall", "xmin", 0, 22, "wall_birch")
    m.wall("bh_hall", "xmax", 0, 22, "wall_birch")
    m.wall("bh_pass", "xmin", -26, -17, "wall_cave")
    for i, z in enumerate([4, 9, 14, 19]):
        m.thing(f"pil_l{i}", "thing_birch_pillar", -6.4, z, size=5.4)
        m.thing(f"pil_r{i}", "thing_birch_pillar", 6.4, z, size=5.4)
    for i, x in enumerate([-4.0, 4.0]):
        m.thing(f"banner{i}", "thing_banner_birch", x, 1.2, y=2.5, size=3.4)
    m.thing("lamp_h0", "thing_silver_lamp", -2.4, 6.5, size=2.3)
    m.thing("lamp_h1", "thing_silver_lamp", 2.4, 6.5, size=2.3)
    m.thing("chair", "thing_chair_white", 0, 2.6, size=2.2)
    m.thing("vial", "thing_vial_stand", 1.5, 4.8, size=1.2)
    m.thing("table_map", "thing_table_map", 4.8, 9.0, size=1.5)
    m.thing("tree_b0", "thing_birch_tree", -4.8, 1.0, size=4.5)
    m.light("lt_hall_a", 0, 12, 4.4, 14, "#dfeaff", 1.2)
    m.light("lt_hall_b", 0, 4.5, 3.0, 8, "#f0f4ff", 1.2)
    m.light("lt_vial", 1.5, 4.8, 1.4, 4.0, "#a8d0ff", 1.1)
    m.wp("hall_c", 0, 19.2, 0)
    m.wp("hall_mid", 0, 15.5, 0)  # (visual polish: the rails of the companion scenes stop short of the companions)
    m.wp("hall_dais", 0, 12.5, 0)
    m.wp("hall_w", -5.0, 16.5, 12)
    m.wp("hall_e", 5.0, 16.5, -12)
    m.wp("hall_far", 0, 1.6, 0)
    m.wp("hall_table", 4.4, 10.8, 0)
    m.actor("lady", "lady", 0, 3.6, "hall", "stand", person="lady", role="hero")
    m.actor("warden_h", "warden", 2.2, 7.8, "hall", "stand", person="warden")
    m.actor("bram_h", "bram", -1.8, 8.6, "hall", "stand", person="bram")
    for i, (x, z, act, tgt) in enumerate([(-4.0, 6.0, "stand", None), (4.2, 5.2, "stand", None), (-4.8, 10.6, "watch", "lady"), (-2.2, 9.0, "stand", None), (2.4, 11.8, "watch", "lady")]):
        m.actor(f"bf{i}", "birch_folk", x, z, "hall", act, target=tgt)

    # --- E04 the High Pass ---
    m.thing("storm", "piece_storm_snow", 0, -22.0, y=2.4, size=4.6, piece="storm", blend="mix")
    for i, (x, z) in enumerate([(-9.5, -12), (-10.2, -17), (9.8, -13), (10.4, -19), (-6.5, -27), (7, -28)]):
        m.thing(f"pine{i}", "thing_snow_pine", x, z, size=4.4 + (i % 3) * 0.4)
    m.thing("cave", "thing_cave_mouth", -6.5, -31.3, y=1.9, size=4.0)
    m.thing("ridge", "thing_ridge_marker", 6.5, -30.6, size=3.0)
    m.thing("cairn", "thing_cairn", 3.5, -20.5, size=1.8)
    m.light("lt_pass", 0, -18, 4.5, 26, "#c4d8ff", 1.0)
    m.light("lt_cave", -6.5, -30.0, 1.8, 6.0, "#7090c8", 0.9)
    m.wp("pass_in", 0, -9.4, 0)
    m.wp("pass_c", 0, -11.5, 0)
    m.wp("pass_mid", 0, -13.6, 0)
    m.wp("pass_far", 0, -15.2, 0)
    m.wp("pass_w", -7.5, -13.5, 20)
    m.wp("pass_e", 7.5, -13.5, -20)
    m.wp("cave_wp", -6.5, -29.4, 10)
    m.wp("ridge_wp", 6.5, -29.4, -10)
    m.actor("bram_p", "bram", -1.3, -19.2, "pass", "stand", person="bram")
    m.actor("warden_p", "warden", 1.4, -19.4, "pass", "stand", person="warden")
    return m


# ======================================================================================================================================================
# deep_halls: the Deep Halls (E05) and the Falls (E06)   [world `deeps`]
# ======================================================================================================================================================

def deep_halls() -> Map:
    m = Map("deep_halls", "halls_c", {"color": "#050914", "density": 0.02}, "sky_falls")
    m.room("dh_hall", -10, 0, 10, 26, 0, 9, "floor_deep", "ceil_black", "wall_deep", 0.62, "#8aaae0", "halls")
    m.room("dh_lake", -10, -16, -1.5, 0, -1.2, 9, "floor_lake", "ceil_black", "wall_rock_wet", 0.5, "#6a8ac0", "halls")
    m.room("dh_bridge", -1.5, -16, 1.5, 0, 0, 9, "floor_bridge", "ceil_black", "wall_deep", 0.62, "#8aaae0", "halls")
    m.room("dh_ledge", 1.5, -16, 10, 0, 0, 9, "floor_wet_rock", "ceil_black", "wall_rock_wet", 0.56, "#7a9ad0", "halls")
    m.room("dh_far", -10, -30, 10, -16, 0, 9, "floor_deep", "ceil_black", "wall_deep", 0.6, "#84a4d8", "halls")
    m.room("dh_tunnel", -2, -40, 2, -30, 0, 5, "floor_deep", "ceil_black", "wall_deep_arch", 0.55, "#8aaae0", "falls")
    m.room("dh_falls", -12, -70, 12, -40, 0, 11, "floor_boardwalk", "ceil_stars", "wall_rock_wet", 0.72, "#a8c8f8", "falls")
    m.door("dh_hall", "dh_lake", 8.5)
    m.door("dh_hall", "dh_bridge", 3.0)
    m.door("dh_hall", "dh_ledge", 4.0)
    m.door("dh_far", "dh_lake", 8.5)
    m.door("dh_far", "dh_bridge", 3.0)
    m.door("dh_far", "dh_ledge", 4.0)
    m.door("dh_far", "dh_tunnel", 3.0)
    m.door("dh_tunnel", "dh_falls", 3.0)
    m.wall("dh_falls", "zmin", -12, 12, "wall_falls")
    m.animated = [{"tex": "floor_lake", "mode": "scroll", "speed": [0.05, 0.03]}, {"tex": "wall_falls", "mode": "scroll", "speed": [0.0, 0.5]}]
    for i, z in enumerate([4, 11, 18, 24]):
        m.thing(f"pil_dl{i}", "thing_pillar_deep", -8.2, z, size=8.5)
        m.thing(f"pil_dr{i}", "thing_pillar_deep", 8.2, z, size=8.5)
    for i, z in enumerate([-20, -27]):
        m.thing(f"pil_fl{i}", "thing_pillar_deep", -8.2, z, size=8.5)
        m.thing(f"pil_fr{i}", "thing_pillar_deep", 8.2, z, size=8.5)
    m.thing("cold", "thing_cold_light", 0.0, 9.0, y=6.0, size=3.6)
    m.thing("drum", "thing_drum", 6.2, -5.0, size=2.0, anim="pulse")
    m.thing("drowned", "piece_drowned_thing", -4.4, -4.0, y=3.4, size=7.5, piece="drowned", blend="mix")
    m.thing("stalag0", "thing_stalagmite", -9.2, -13.0, size=2.6)
    m.thing("rail0", "thing_bridge_rail", -2.1, -8.0, size=1.2)
    m.thing("mist0", "thing_mist", -5.0, -6.0, size=2.2, anim="sway")
    m.thing("blamp", "thing_lantern_boat", 2.4, 15.8, size=0.8)
    m.light("lt_cold", 0, 9, 7.0, 20, "#b8d8ff", 1.6, )
    m.light("lt_lake", -5.0, -6.0, 4.0, 12, "#6890c8", 0.9)
    m.light("lt_lamp", 0.0, 15.6, 1.6, 9.0, "#ffb878", 1.7)
    m.light("lt_far", 0, -22, 6.0, 16, "#a0c0f0", 1.1)
    m.wp("halls_c", 0, 23.0, 0)
    m.wp("halls_mid", 0, 20.6, 0)  # (visual polish: the rail stops short of Bram and the Warden, who wait under the lamp)
    m.wp("halls_edge", 0, 18.8, 0)
    m.wp("halls_w", -6.0, 20.0, 12)
    m.wp("halls_e", 6.0, 20.0, -12)
    m.wp("bridge_wp", 0, -1.2, 0)
    m.wp("lake_edge", -5.0, 1.2, 8)
    m.wp("far_in", 0, -17.6, 0)
    m.actor("bram_d", "bram", -1.2, 14.8, "halls", "stand", person="bram")
    m.actor("warden_d", "warden", 1.4, 14.5, "halls", "stand", person="warden")

    # --- E06 the Falls ---
    m.thing("falls_lip", "thing_waterfall_edge", 0, -67.0, y=1.0, size=4.5)
    m.thing("boat", "thing_boat", -5.0, -50.0, size=2.6, anim="bob")
    m.thing("post0", "thing_rope_post", -3.0, -50.0, size=1.4)
    m.thing("horn", "thing_horn", 6.5, -50.0, size=1.2)
    m.thing("mist1", "thing_mist", 0, -62, size=3.0, anim="sway")
    m.thing("rail1", "thing_bridge_rail", 8.5, -46.0, size=1.2)
    m.thing("blamp2", "thing_lantern_boat", -3.8, -48.0, size=0.9)
    m.light("lt_falls", 0, -56, 8.0, 24, "#a8c8f8", 1.2)
    m.light("lt_boat", -3.2, -50.5, 1.6, 7.0, "#ffb060", 1.4)
    m.wp("falls_in", 0, -41.8, 0)
    m.wp("falls_c", 0, -43.5, 0)
    m.wp("falls_mid", 0, -46.0, 0)  # (visual polish: the rail stops short of the pair on the boardwalk)
    m.wp("falls_lip_wp", 0, -47.6, 0)
    m.wp("falls_w", -7.5, -47.0, 15)
    m.wp("falls_e", 7.5, -47.0, -15)
    m.wp("boat_wp", -5.0, -52.4, 8)
    m.wp("horn_wp", 6.5, -52.4, -8)
    m.actor("bram_fb", "bram", -1.8, -52.0, "falls", "stand", person="bram")
    m.actor("warden_f", "warden", 2.2, -52.2, "falls", "stand", person="warden")
    return m


# ======================================================================================================================================================
# ash_land: the marsh (E07), the Black Wall (E08), the Stair of Bells (E09), the Ash Plain (E10)   [world `marsh`]
#           the Throat (E11), the Drowned Spring (E12), the Keeper (E13), the riders' camp (E14)  [world `mountain`]
# ======================================================================================================================================================

def ash_land() -> Map:
    m = Map("ash_land", "marsh_c", {"color": "#1a0e10", "density": 0.014}, "sky_ash")
    m.room("al_marsh", -14, 0, 14, 26, 0, 6, "floor_marsh", "ceil_mist_teal", "wall_reed", 0.6, "#60e0c0", "marsh")
    m.room("al_wall", -14, -24, 14, 0, 0, 5, "floor_ash", "sky", "wall_obsidian", 0.64, "#d08a78", "wall")
    m.room("al_gatehall", -3, -32, 3, -24, 0, 5, "floor_basalt", "sky", "wall_gate", 0.56, "#c88070", "wall")
    m.room("al_crack", 11, -32, 13, -24, 0, 5, "floor_basalt", "sky", "wall_obsidian", 0.5, "#c07a68", "stair")
    m.room("al_camp", -32, -24, -14, 0, 0, 4, "floor_camp", "sky", "wall_tent", 0.6, "#e08868", "camp")
    m.room("al_plain", -20, -72, 6, -32, 0, 6, "floor_ash", "sky", "wall_ash_dune", 0.66, "#d89078", "plain")
    m.room("al_stair_a", 8, -44, 28, -32, 0, 7, "floor_stair", "sky", "wall_cliff", 0.62, "#c89078", "stair")
    m.room("al_stair_b", 8, -54, 28, -44, 1.4, 8.4, "floor_stair", "sky", "wall_cliff", 0.62, "#c89078", "stair")
    m.room("al_stair_c", 8, -62, 28, -54, 2.8, 9.8, "floor_stair", "sky", "wall_cliff", 0.62, "#c89078", "stair")
    m.room("al_stair_top", 8, -72, 20, -62, 3.6, 10.6, "floor_basalt", "sky", "wall_cliff", 0.6, "#c08a70", "stair")
    m.room("al_ridge", 4, -80, 20, -72, 3.6, 10.6, "floor_red_rock", "sky", "wall_cliff", 0.58, "#d08068", "stair")
    m.room("al_throat", -4, -96, 4, -72, 0, 4.4, "floor_vent", "ceil_hot", "wall_vent", 0.58, "#ff7a58", "throat")
    m.room("al_cav_s", -12, -110, 12, -96, 0, 7, "floor_cavern", "ceil_cavern", "wall_cavern", 0.56, "#9ab4e0", "spring")
    m.room("al_pool", -12, -122, 12, -110, -0.4, 7, "floor_pool", "ceil_cavern", "wall_cavern", 0.56, "#8098d0", "spring")
    m.room("al_cav_n", -12, -132, 12, -122, 0, 7, "floor_cavern", "ceil_cavern", "wall_cavern", 0.5, "#9ab4e0", "spring")
    m.room("al_keep_in", 4, -92, 20, -80, 0, 4.4, "floor_vent", "ceil_hot", "wall_vent", 0.55, "#ff7a58", "keeper")
    m.room("al_keep", 14, -122, 38, -92, 0, 6, "floor_cavern", "ceil_cavern", "wall_cavern", 0.5, "#ffa070", "keeper")
    m.door("al_marsh", "al_wall", 6.0)
    m.door("al_wall", "al_gatehall", 5.0)
    m.door("al_wall", "al_crack", 2.0)
    m.door("al_wall", "al_camp", 3.0, at=-12)
    m.door("al_gatehall", "al_plain", 5.0)
    m.door("al_crack", "al_stair_a", 2.0)
    m.door("al_stair_a", "al_stair_b", 6.0)
    m.door("al_stair_b", "al_stair_c", 6.0)
    m.door("al_stair_c", "al_stair_top", 6.0)
    m.door("al_stair_top", "al_ridge", 6.0)
    m.door("al_ridge", "al_throat", 6.0, at=-76)
    m.door("al_plain", "al_throat", 4.0)
    m.door("al_throat", "al_cav_s", 4.0)
    m.door("al_cav_s", "al_pool", 20.0)
    m.door("al_pool", "al_cav_n", 20.0)
    m.door("al_throat", "al_keep_in", 3.0, at=-86)
    m.door("al_keep_in", "al_keep", 5.0)
    m.animated = [{"tex": "floor_marsh", "mode": "scroll", "speed": [0.03, 0.04]}, {"tex": "floor_pool", "mode": "scroll", "speed": [0.02, 0.0]},
                  {"tex": "wall_vent", "mode": "pulse", "rate": 1.0, "amount": 0.4}]

    # --- E07 the Reed Marsh ---
    for i, (x, z) in enumerate([(-10, 4), (-11, 12), (-9, 20), (10, 6), (11, 14), (9.5, 21), (-5, 2.4), (5.5, 2.6)]):
        m.thing(f"reed{i}", "thing_reed_clump", x, z, size=2.6 + (i % 3) * 0.4)
    for i, (x, z, y) in enumerate([(-6.5, 8, 1.7), (-2.5, 6, 2.1), (4.0, 9.5, 1.5), (7.5, 5, 2.3), (-8, 17, 1.8), (2, 15.5, 1.4)]):
        m.thing(f"mlight{i}", "thing_marsh_light", x, z, y=y, size=0.9, anim="bob")
    m.thing("dead0", "thing_dead_tree", -12, 8, size=4.5)
    m.thing("dead1", "thing_dead_tree", 12, 18, size=4.8)
    m.light("lt_marsh", 0, 12, 3.5, 20, "#40d0a0", 0.9)
    m.light("lt_ml_a", -6.5, 8, 1.7, 5.0, "#50f0b0", 1.1)
    m.light("lt_ml_b", 4.0, 9.5, 1.5, 5.0, "#50f0b0", 1.1)
    m.light("lt_ho_m", 0.2, 15.2, 1.9, 3.4, "#f4e6d2", 0.9)  # (visual polish: a warm lamp on the pair, so the Hollow One's skin is not read as the marsh's teal)
    m.wp("marsh_c", 0, 23.4, 0)
    m.wp("marsh_mid", 0, 20.5, 0)
    m.wp("marsh_fwd", 0, 18.6, 0)
    m.wp("marsh_w", -8.5, 20.0, 12)
    m.wp("marsh_e", 8.5, 20.0, -12)
    m.wp("marsh_path", 0, 1.6, 0)
    m.wp("lights_wp", -5.0, 9.0, 10)
    m.actor("ho_m", "hollow_one", -0.9, 14.0, "marsh", "stand", person="hollow_one", role="hero")
    m.actor("bram_m", "bram", 1.3, 14.8, "marsh", "stand", person="bram")

    # --- E08 the Black Wall ---
    m.thing("gate_black", "thing_gate_black", 0, -23.2, size=6.2)
    m.thing("gate_mouths", "piece_gate_mouths", 0, -22.9, y=3.0, size=5.8, piece="gate_mouths", blend="mix")
    m.thing("crack", "thing_wall_crack", 11.9, -23.4, size=3.2)
    m.thing("brazier_w0", "thing_brazier_red", -6, -12, size=1.8, anim="flicker")
    m.thing("brazier_w1", "thing_brazier_red", 6, -14, size=1.8, anim="flicker")
    m.thing("banner_w", "thing_banner_rider", -9, -17, size=4.4)
    m.thing("chains_w", "thing_chain_post", 8.5, -8.5, size=1.8)
    m.light("lt_wall", 0, -12, 4.0, 22, "#d07050", 0.9)
    m.light("lt_br0", -6, -12, 1.8, 7.0, "#ff6030", 1.3)
    m.light("lt_br1", 6, -14, 1.8, 7.0, "#ff6030", 1.3)
    m.light("lt_crack", 11.9, -22.4, 1.8, 6.0, "#ffa040", 1.2)
    m.wp("wall_in", 0, -1.6, 0)
    m.wp("wall_c", 0, -4.2, 0)
    m.wp("wall_mid", 0, -5.0, 0)  # (visual polish 2: the rail stops short of the Hollow One and the riders ahead; it used to walk between them)
    m.wp("wall_near", 0, -6.6, 0)
    m.wp("wall_gate_wp", 0, -17.2, 0)
    m.wp("wall_w", -9.0, -7.0, 14)
    m.wp("wall_e", 9.0, -7.0, -14)
    m.wp("crack_wp", 11.2, -21.2, -15)
    m.wp("camp_door", -12.4, -12.0, 90)
    for i, (x, z) in enumerate([(-3.8, -14.6), (3.8, -14.8), (0.0, -20.6)]):
        m.actor(f"rd_w{i}", "rider", x, z, "wall", "stand", person=f"rider_w{i}")
    m.actor("ho_w", "hollow_one", 2.6, -8.6, "wall", "stand", person="hollow_one")

    # --- E09 the Stair of Bells ---
    m.thing("bells", "thing_bell_row", 18, -50.5, size=4.6, anim="sway")
    m.thing("bell_big", "thing_bell", 12.5, -52.0, size=3.0, anim="sway")
    m.thing("bell_lone", "thing_bell", 23.5, -50.5, size=2.6, anim="sway")
    m.thing("dead2", "thing_dead_tree", 26, -36, size=4.0)
    m.thing("post_s", "thing_chain_post", 10, -38, size=1.7)
    m.light("lt_stair", 18, -42, 5.0, 22, "#c08060", 0.9)
    m.light("lt_bell", 18, -48.5, 3.0, 8.0, "#d8a050", 1.0)
    m.wp("stair_in", 12, -33.2, 0)
    m.wp("stair_c", 17, -36.0, 0)
    m.wp("stair_mid", 17.4, -37.0, 0)  # (visual polish 2: the rail stops short of the Hollow One and the sentinel, who stood on its line)
    m.wp("stair_fwd", 17.6, -38.0, 0)
    m.wp("stair_up", 18, -53.0, 0)
    m.wp("stair_w", 11.5, -38.5, 12)
    m.wp("stair_e", 25, -38.5, -12)
    m.wp("stair_side", 25.0, -35.0, -20)
    m.wp("bells_wp", 18, -49.2, 0)
    m.actor("sentinel", "sentinel", 18.0, -47.4, "stair", "stand", person="sentinel", role="hero")
    m.actor("ho_b", "hollow_one", 15.6, -42.4, "stair", "stand", person="hollow_one")

    # --- E10 the Ash Plain ---
    m.thing("glass_mtn", "thing_glass_mountain", -2, -70.0, size=22.0)
    m.thing("tower", "thing_tower_light", -14, -60.0, size=8.0, anim="pulse")
    m.thing("dead3", "thing_dead_tree", 3, -45, size=4.5)
    m.thing("dead4", "thing_dead_tree", -16, -48, size=4.2)
    m.thing("vent_p", "thing_vent_glow", -8, -66.0, size=2.6, anim="flicker")
    m.light("lt_plain", -4, -50, 4.5, 30, "#c07860", 0.9)
    m.light("lt_tower", -14, -60.0, 5.0, 14, "#ff5040", 1.0)
    m.wp("plain_in", 0, -33.4, 0)
    m.wp("plain_c", 0, -37.0, 0)
    m.wp("plain_mid", -2, -48.0, 0)
    m.wp("plain_far", -2, -49.5, 0)
    m.wp("plain_w", -9.0, -40.0, 14)
    m.wp("plain_e", 3.5, -40.0, -14)
    m.wp("road_wp", -1.0, -68.8, 0)
    m.wp("tower_wp", -13.0, -58.0, 30)
    m.actor("bram_pl", "bram", -0.6, -53.5, "plain", "stand", person="bram")
    m.actor("ho_pl", "hollow_one", -3.4, -54.0, "plain", "stand", person="hollow_one")
    for i, (x, z) in enumerate([(-12.0, -54.0), (-8.0, -57.5), (-15.0, -66.0)]):
        m.actor(f"rd_pl{i}", "rider", x, z, "plain", "stand", person=f"rider_pl{i}")

    # --- E11 the Throat (the camera comes in looking down the tunnel) ---
    m.thing("vent0", "thing_vent_glow", -3.1, -80.0, size=2.4, anim="pulse")
    m.thing("vent1", "thing_vent_glow", 3.1, -88.0, size=2.4, anim="pulse")
    m.thing("vent2", "thing_vent_glow", -3.1, -92.0, size=2.4, anim="pulse")
    m.thing("redrock0", "thing_stalagmite_red", 3.0, -81.5, size=1.6)
    m.light("lt_throat_a", 0, -80, 2.4, 9, "#ff5a30", 1.4)
    m.light("lt_throat_b", 0, -90, 2.4, 9, "#ff4a28", 1.5)
    m.wp("throat_in", 0, -73.8, 0)
    m.wp("throat_c", 0, -76.0, 0)
    m.wp("throat_mid", 0, -83.0, 0)
    m.wp("throat_low", 0, -90.5, 0)
    m.wp("throat_w", -2.4, -78.0, 10)
    m.wp("throat_e", 2.4, -78.0, -10)
    m.wp("down_wp", 0, -94.6, 0)
    m.wp("whisper_wp", 3.0, -86.0, -30)
    m.actor("ho_t", "hollow_one", 1.0, -95.0, "throat", "stand", person="hollow_one")

    # --- E12 the Drowned Spring ---
    m.thing("pool_stones", "thing_pool_stones", 0, -116.0, size=3.0)
    m.thing("shaft", "piece_light_shaft", 0, -117.5, y=3.5, size=7.0, piece="shaft", blend="add")
    m.thing("swell", "piece_white_swell", 0, -118.0, y=3.0, size=7.5, piece="swell", blend="add")
    m.thing("stal_s0", "thing_stalagmite_red", -9.5, -102.0, size=2.6)
    m.thing("stal_s1", "thing_stalagmite_red", 9.5, -128.0, size=2.6)
    m.light("lt_shaft", 0, -117, 4.0, 14, "#e8f4ff", 1.4)
    m.light("lt_spring", 0, -104, 3.0, 12, "#9ab4e0", 0.7)
    m.light("lt_spring_p", 0, -103.0, 2.4, 9.0, "#c8d8ff", 1.4)
    m.wp("spring_in", 0, -97.6, 0)
    m.wp("spring_c", 0, -100.5, 0)
    m.wp("spring_mid", 0, -101.8, 0)  # (visual polish: the rail stops short of the pair, so they stay in the picture)
    m.wp("spring_edge", 0, -102.8, 0)
    m.wp("spring_w", -7.5, -101.0, 14)
    m.wp("spring_e", 7.5, -101.0, -14)
    m.wp("pool_wp", 0, -109.4, 0)
    m.actor("ho_s", "hollow_one", -2.0, -107.0, "spring", "stand", person="hollow_one")
    m.actor("bram_s", "bram", 2.1, -107.0, "spring", "stand", person="bram")

    # --- E13 the Keeper ---
    m.thing("altar", "thing_ember_altar", 25.0, -112.0, size=3.0, anim="pulse")
    m.thing("long_shadow", "piece_long_shadow", 25.0, -106.8, y=0.05, size=9.0, piece="long_shadow", blend="mix")  # (visual polish 2: it lay 2 m in front of the rail's camera, under its feet, and was bigger than the screen's floor strip; now across the floor between the pair and the altar, 9 m wide)
    m.thing("stal_k0", "thing_stalagmite_red", 17.0, -110.0, size=2.4)
    m.thing("stal_k1", "thing_stalagmite_red", 34.0, -108.0, size=2.4)
    m.light("lt_altar", 25, -111.0, 1.8, 16, "#ff8a40", 1.9)
    m.light("lt_keep_in", 10, -86, 2.2, 7.0, "#ff6a30", 1.0)
    m.light("lt_keep_p", 24.6, -104.5, 2.0, 10.0, "#ff8a40", 1.7)
    m.wp("keep_in_wp", 9.0, -85.5, -90)
    m.wp("keep_in2", 17.0, -90.2, 0)
    m.wp("keep_c", 24.0, -96.0, 0)
    m.wp("keep_mid", 24.4, -99.0, 0)  # (visual polish: the rail stops short of Bram and the Hollow One, who stand in the altar's light)
    m.wp("keep_near", 24.7, -101.5, 0)
    m.wp("keep_w", 18.0, -98.0, 15)
    m.wp("keep_e", 31.0, -98.0, -15)
    m.wp("ember_wp", 25.0, -109.4, 0)
    m.actor("bram_k", "bram", 22.8, -105.5, "keeper", "stand", person="bram")
    m.actor("ho_k", "hollow_one", 26.6, -106.5, "keeper", "stand", person="hollow_one")

    # --- E14 Taken: the riders' camp (the camera is walked in from the east and looks west: yaw 90) ---
    m.thing("tent0", "thing_tent", -27, -4.5, size=4.2)
    m.thing("tent1", "thing_tent", -28, -19.5, size=4.2)
    m.thing("stake", "thing_stake", -22.5, -17.5, size=2.4)
    m.thing("fire_c", "thing_camp_fire", -22, -10.0, size=1.6, anim="flicker")
    m.thing("banner_c", "thing_banner_rider", -30, -12, size=4.6)
    m.thing("chain_c", "thing_chain_post", -20, -5.5, size=1.8)
    m.light("lt_camp", -22, -10, 1.6, 12, "#ff6a30", 1.5)
    m.light("lt_camp2", -26, -12, 3.0, 14, "#d86040", 0.9)
    m.wp("camp_in", -15.4, -12.0, 90)
    m.wp("camp_c", -17.4, -11.0, 90)
    m.wp("camp_mid", -17.8, -11.0, 90)  # (visual polish 2: the rail stops short of Bram and the captain's riders; it used to walk past Bram)
    m.wp("camp_fwd", -18.5, -11.4, 90)
    m.wp("camp_near", -22.5, -12.0, 90)
    m.wp("camp_n", -18.0, -4.5, 80)
    m.wp("camp_s", -18.0, -19.5, 100)
    m.wp("stake_wp", -21.5, -17.5, 120)
    m.wp("captain_wp", -26.0, -12.0, 90)
    m.actor("captain", "captain", -26.0, -12.4, "camp", "stand", person="captain", role="hero")
    for i, (x, z) in enumerate([(-22.8, -8.4), (-23.0, -14.6), (-27.5, -8.5)]):
        m.actor(f"rd_c{i}", "rider", x, z, "camp", "stand", person=f"rider_c{i}")
    m.actor("bram_c", "bram", -21.6, -12.6, "camp", "stand", person="bram")
    return m


MAPS = {"orchard": orchard, "birch_hall": birch_hall, "deep_halls": deep_halls, "ash_land": ash_land}
TITLES = {"orchard": "The Orchard", "birch_hall": "The Birch Hall", "deep_halls": "The Deep Halls", "ash_land": "The Ash Lands"}


def chapter_json(m: Map, title: str) -> dict:
    hosp = json.load(open(os.path.join(ROOT, "content", "story", "hospital.json"), encoding="utf-8"))
    endings = {}
    for i, k in enumerate(["road_open", "road_hard", "road_lost"]):
        endings[k] = {"title": ["The road opens", "A hard road", "Lost on the road"][i], "energy_min": [80, 40, 0][i], "pass_min": [0.9, 0.5, 0.0][i], "text": "", "journey": []}
    return {"id": m.art, "title": title, "chapter": 9, "art": m.art, "description": "The Ember Road: a sister run at 145 BPM (docs/THREE_PATHS_AND_FACES_PLAN.md section 6). Not a Story Campaign chapter.",
            "intro": "", "duration_bars": 8, "sequence_bars": 2, "initial_energy": 45, "palettes": hosp["palettes"], "energy": hosp["energy"],
            "acts": [{"id": "I", "title": title, "start_bar": 1}],
            "blocks": [{"id": "the_road", "title": title, "act": "Act I", "start_bar": 1, "bars": 8, "events": [{"at_bar": 1, "action": "lights_warm"}, {"at_bar": 1, "action": "player_role", "role": "dancer"}]}],
            "decisions": [], "endings": endings, "ending_order": ["road_open", "road_hard", "road_lost"],
            "groups": {"all": [a["id"] for a in m.actors]}, "actors": m.actors, "silhouettes": []}


def write_json(path: str, doc) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
        fh.write("\n")


def main() -> int:
    for name, fn in MAPS.items():
        m = fn()
        write_json(os.path.join(ROOT, "content", "story", "maps", name + ".json"), m.as_json())
        write_json(os.path.join(ROOT, "content", "story", name + ".json"), chapter_json(m, TITLES[name]))
        print(f"{name}: {len(m.sectors)} sectors, {len(m.things)} things, {len(m.actors)} people, {len(m.waypoints)} waypoints")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
