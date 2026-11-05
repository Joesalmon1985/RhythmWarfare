#!/usr/bin/env python3
"""Authors the Ember Road's run data (docs/THREE_PATHS_AND_FACES_PLAN.md section 6): content/paths/ember/run.json, hotspots/<world>.json and the music prompts.

    python3 tools/run/make_ember.py          # then: python3 tools/content/make_path_placeholders.py ember   (the synthesised stand-in loops, music.json)

Edit the tables below and run it again. Scenes are E00..E14 of the plan (`scene` is the plan's code); a scene's id is its world's id for the first scene of a world
(the save's `reached` ids), `<world>.<name>` for the others. Maps are tools/story/ember_maps.py. No text anywhere: faces, acts, lights and pieces carry the story.
Divergences from the plan are listed in docs/paths/ember.md.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import laps as laps_mod  # noqa: E402

# Two laps per scene (docs/CONTINUOUS_RUN.md "Two laps"): E00 is the prologue (the orchard, one way on) and stays at one lap; the endings E13 (the Spring) and E12 (the Keeper) take two.
LAPS = 2
SINGLE_LAP = ("hollow",)
OUT = os.path.join(ROOT, "content", "paths", "ember")

WORLDS = [
    ("hollow", "The Hollow", "orchard", 1, "An orchard village at harvest, a black ford, a lantern inn."),
    ("north", "The Birch Hall", "birch_hall", 2, "A white hall of birch pillars and the snow pass above it."),
    ("deeps", "The Deep Halls", "deep_halls", 2, "A pillared dark with a lake, and the top of a waterfall."),
    ("marsh", "The Marsh and the Wall", "ash_land", 3, "Lights under the reeds, a wall of black stone, a stair of bells, an ash plain."),
    ("mountain", "The Glass Mountain", "ash_land", 4, "A tunnel lit red, a black pool and a shaft of light, the riders' camp."),
]

GLANCES = [{"by": -12, "pitch": 8, "bars": 2}, {"by": -28, "bars": 2}, {"pitch": 14, "bars": 3}, {"by": 24, "bars": 2}]
STROLLS = [{"fwd": 1.6, "bars": 3}, {"turn": 35, "fwd": 1.0, "bars": 3}, {"right": 1.4, "bars": 2}]


def place(to, role="dancer", bars=3, style="walk"):
    return {"to": to, "role": role, "style": style, "bars": bars}


# ---- scenes -------------------------------------------------------------------------------------------------------------------------------------
# id: world, code (the plan's), title, entry, exit_scene, ending, home, arrive, good, bad, exits {dir: waypoint}, next [(to, dir, loop)]
SCENES = [
    dict(id="hollow", world="hollow", code="E00", name="orchard", title="The Orchard", entry=True, home="orchard_c", arrive="orchard_c", good=["orchard_mid", "orchard_near"], bad=["orchard_w", "orchard_e"],
         exits={"up": "orchard_gate"}, next=[("hollow.ford", "up", False)]),
    dict(id="hollow.ford", world="hollow", code="E01", name="ford", title="The Ford at Night", exit=True, home="ford_c", arrive="ford_in", good=["ford_mid", "ford_edge"], bad=["ford_w", "ford_e"],
         exits={"up": "ford_cross", "left": "lantern_wp"}, next=[("hollow.inn", "up", False), ("north", "left", False)]),
    dict(id="hollow.inn", world="hollow", code="E02", name="inn", title="The Lantern Inn", exit=True, home="inn_c", arrive="inn_door", good=["inn_mid", "inn_near"], bad=["inn_w", "inn_e"],
         exits={"up": "inn_back", "left": "inn_fire"}, next=[("north", "up", False), ("north.pass", "left", False)]),
    dict(id="north", world="north", code="E03", name="birch_hall", title="The Birch Hall", entry=True, exit=True, home="hall_c", arrive="hall_c", good=["hall_mid", "hall_dais"], bad=["hall_w", "hall_e"],
         exits={"up": "hall_far", "right": "hall_table"}, next=[("north.pass", "up", False), ("deeps", "right", False)]),
    dict(id="north.pass", world="north", code="E04", name="high_pass", title="The High Pass", entry=True, exit=True, home="pass_c", arrive="pass_in", good=["pass_mid", "pass_far"], bad=["pass_w", "pass_e"],
         exits={"left": "cave_wp", "right": "ridge_wp"}, next=[("deeps", "left", False), ("deeps.falls", "right", False)]),
    dict(id="deeps", world="deeps", code="E05", name="deep_halls", title="The Deep Halls", entry=True, exit=True, home="halls_c", arrive="halls_c", good=["halls_mid", "halls_edge"], bad=["halls_w", "halls_e"],
         exits={"up": "bridge_wp", "left": "lake_edge"}, next=[("deeps.falls", "up", False), ("north.pass", "left", True)]),
    dict(id="deeps.falls", world="deeps", code="E06", name="falls", title="The Falls", entry=True, exit=True, home="falls_c", arrive="falls_in", good=["falls_mid", "falls_lip_wp"], bad=["falls_w", "falls_e"],
         exits={"up": "boat_wp", "right": "horn_wp", "left": "horn_wp"}, next=[("marsh", "up", False), ("marsh.wall", "right", False), ("mountain.taken", "left", False)]),
    dict(id="marsh", world="marsh", code="E07", name="reed_marsh", title="The Reed Marsh", entry=True, home="marsh_c", arrive="marsh_c", good=["marsh_mid", "marsh_fwd"], bad=["marsh_w", "marsh_e"],
         exits={"up": "marsh_path", "right": "lights_wp"}, next=[("marsh.wall", "up", False), ("marsh.stair", "right", False)]),
    dict(id="marsh.wall", world="marsh", code="E08", name="black_wall", title="The Black Wall", entry=True, exit=True, home="wall_c", arrive="wall_in", good=["wall_mid", "wall_near"], bad=["wall_w", "wall_e"],
         exits={"right": "crack_wp", "up": "wall_gate_wp", "left": "camp_door"}, next=[("marsh.stair", "right", False), ("marsh.plain", "up", False), ("mountain.taken", "left", False)]),
    dict(id="marsh.stair", world="marsh", code="E09", name="stair_of_bells", title="The Stair of Bells", exit=True, home="stair_c", arrive="stair_in", good=["stair_mid", "stair_fwd"], bad=["stair_w", "stair_e"],
         exits={"left": "stair_side", "up": "stair_up", "right": "bells_wp"}, next=[("marsh.plain", "left", False), ("mountain", "up", False), ("mountain.taken", "right", False)]),
    dict(id="marsh.plain", world="marsh", code="E10", name="ash_plain", title="The Ash Plain", entry=True, exit=True, home="plain_c", arrive="plain_in", good=["plain_mid", "plain_far"], bad=["plain_w", "plain_e"],
         exits={"up": "road_wp", "left": "tower_wp"}, next=[("mountain", "up", False), ("mountain.taken", "left", False)]),
    dict(id="mountain", world="mountain", code="E11", name="throat", title="The Throat", entry=True, home="throat_c", arrive="throat_in", good=["throat_mid", "throat_low"], bad=["throat_w", "throat_e"],
         exits={"up": "down_wp", "right": "whisper_wp"}, next=[("mountain.spring", "up", False), ("mountain.keeper", "right", False)]),
    dict(id="mountain.spring", world="mountain", code="E12", name="drowned_spring", title="The Drowned Spring", ending="quenched", home="spring_c", arrive="spring_in", good=["spring_mid", "spring_edge"],
         bad=["spring_w", "spring_e"], exits={"up": "pool_wp"}, next=[("run:warehouse", "up", False)]),
    dict(id="mountain.keeper", world="mountain", code="E13", name="keeper", title="The Keeper", ending="kept", home="keep_c", arrive="keep_in2", good=["keep_mid", "keep_near"], bad=["keep_w", "keep_e"],
         exits={"up": "ember_wp"}, next=[("run:warehouse", "up", False)]),
    dict(id="mountain.taken", world="mountain", code="E14", name="taken", title="Taken", entry=True, exit=True, home="camp_c", arrive="camp_in", good=["camp_mid", "camp_fwd"], bad=["camp_n", "camp_s"],
         exits={"up": "stake_wp", "left": "captain_wp"}, next=[("marsh.plain", "up", True), ("marsh.wall", "left", True)]),
]
BY_ID = {s["id"]: s for s in SCENES}

# ---- cast (the story beats that happen whether or not the player touches anything) ----------------------------------------------------------------
# (actor, at_beat, act, face, look_at, beats, extra conditions). `P(piece, at, op)` switches a set piece, `H(actor, flag)` removes a person while a flag holds.


def C(actor, at, act, face="", look="", beats=12, **cond):
    d = {"actor": actor, "at_beat": at, "act": act}
    if face:
        d["face"] = face
    if look:
        d["look_at"] = look
    d["beats"] = beats
    d.update(cond)
    return d


def P(piece, at, op, **cond):
    d = {"piece": piece, "at_beat": at, "op": op}
    d.update(cond)
    return d


def H(actor, flag, at=0):
    return {"actor": actor, "at_beat": at, "hide": True, "if_flags_all": [flag]}


CAST = {
    "hollow": [C("gran", 0, "lie", "relief", "camera", 40), C("gran", 44, "sleep", "neutral", "", 20), C("bram_o", 30, "cover_face", "grief", "", 24),
               C("vo0", 52, "bow", "neutral", "gran", 11), C("vo1", 52, "bow", "neutral", "gran", 11), C("vo2", 53, "bow", "neutral", "gran", 10), C("vo3", 53, "bow", "neutral", "gran", 10)],
    "hollow.ford": [C("rd_f0", 0, "stare", "anger", "camera", 16), C("rd_f1", 0, "stare", "anger", "camera", 16), C("rd_f2", 2, "stare", "anger", "camera", 16),
                    C("bram_f", 16, "plead", "plea", "camera", 16), C("bram_f", 40, "plead", "plea", "camera", 16), C("bram_f", 48, "cover_face", "fear", "", 14, if_energy_below=35),
                    C("rd_f0", 32, "stamp", "anger", "", 10), C("rd_f2", 34, "stamp", "anger", "", 10)],
    "hollow.inn": [C("innkeeper", 0, "write", "neutral", "", 22), C("innkeeper", 24, "stare", "doubt", "warden_i", 22), C("dk0", 0, "laugh", "laugh", "dk1", 14), C("dk1", 10, "laugh", "laugh", "dk0", 14),
                   C("dk2", 22, "laugh", "laugh", "dk3", 14), C("dk3", 34, "laugh", "laugh", "dk2", 12), C("warden_i", 16, "stare", "resolve", "camera", 14), C("warden_i", 32, "beckon", "resolve", "camera", 16),
                   P("rider_shadow", 48, "on"), P("rider_shadow", 61, "off"),
                   C("dk0", 50, "recoil", "fear", "rider_shadow", 12), C("dk1", 50, "recoil", "fear", "rider_shadow", 12), C("dk2", 51, "recoil", "fear", "rider_shadow", 12),
                   C("dk3", 51, "recoil", "fear", "rider_shadow", 12), C("innkeeper", 50, "recoil", "fear", "rider_shadow", 12)],
    "north": [C("lady", 4, "offer", "awe", "camera", 16), C("lady", 24, "stare", "grief", "camera", 22), C("bf0", 40, "bow", "neutral", "lady", 12), C("bf1", 40, "bow", "neutral", "lady", 12),
              C("bf2", 41, "bow", "neutral", "lady", 12), C("bf3", 41, "bow", "neutral", "lady", 12), C("bf4", 42, "bow", "neutral", "lady", 12), C("warden_h", 32, "point", "resolve", "table_map", 14),
              C("bram_h", 12, "stare", "awe", "lady", 14)],
    "north.pass": [H("warden_p", "ember_warden_lost"), P("storm", 0, "on"), P("storm", 56, "off", if_energy_above=50), C("bram_p", 0, "recoil", "fear", "storm", 14), C("bram_p", 24, "plead", "plea", "camera", 14),
                   C("warden_p", 16, "beckon", "resolve", "camera", 14), C("warden_p", 40, "beckon", "resolve", "camera", 14), C("bram_p", 44, "cover_face", "fear", "", 14, if_energy_below=40)],
    "deeps": [P("drowned", 0, "off"), H("bram_d", "ember_alone"), C("bram_d", 0, "stare", "awe", "drowned", 16), C("warden_d", 0, "stare", "awe", "drowned", 16), C("warden_d", 20, "look", "awe", "drum", 12),
              P("drowned", 46, "on"), C("warden_d", 48, "block", "resolve", "drowned", 14), C("bram_d", 50, "recoil", "fear", "drowned", 12)],
    "deeps.falls": [H("warden_f", "ember_warden_lost"), P("drowned", 0, "off"), C("warden_f", 6, "offer", "resolve", "camera", 14), C("bram_fb", 6, "offer", "happy", "camera", 14), C("bram_fb", 36, "nod", "resolve", "camera", 10),
                    C("warden_f", 40, "point", "resolve", "horn", 12), C("bram_fb", 52, "stare", "fear", "falls_lip", 8, if_energy_below=40)],
    "marsh": [H("bram_m", "ember_alone"), C("ho_m", 0, "beckon", "plea", "camera", 24), C("ho_m", 26, "stare", "plea", "camera", 22), C("ho_m", 52, "laugh", "anger", "marsh_fwd", 11),
              C("bram_m", 20, "stare", "fear", "mlight1", 14)],
    "marsh.wall": [P("gate_mouths", 0, "off"), C("rd_w0", 0, "block", "anger", "camera", 20), C("rd_w1", 1, "block", "anger", "camera", 20), C("rd_w2", 2, "block", "anger", "camera", 20),
                   C("ho_w", 16, "point", "doubt", "crack", 14), P("gate_mouths", 34, "on"), C("rd_w0", 34, "stamp", "anger", "", 10), C("rd_w2", 36, "stamp", "anger", "", 10),
                   C("ho_w", 46, "stare", "doubt", "gate_mouths", 14)],
    "marsh.stair": [C("sentinel", 0, "stare", "neutral", "camera", 40), C("ho_b", 24, "cover_face", "shame", "", 24), C("ho_b", 52, "stare", "shame", "sentinel", 10)],
    "marsh.plain": [H("bram_pl", "ember_alone"), C("rd_pl0", 0, "stare", "anger", "camera", 20), C("rd_pl1", 4, "stare", "anger", "camera", 20), C("rd_pl2", 8, "stare", "anger", "camera", 20),
                    C("ho_pl", 16, "plead", "plea", "camera", 20), C("ho_pl", 42, "plead", "plea", "camera", 18), C("bram_pl", 24, "offer", "relief", "camera", 16)],
    "mountain": [C("ho_t", 0, "stare", "anger", "camera", 30), C("ho_t", 34, "stare", "anger", "camera", 26)],
    "mountain.spring": [H("bram_s", "ember_alone"), P("shaft", 0, "on"), P("swell", 0, "off"), C("ho_s", 0, "plead", "plea", "pool_stones", 26), C("ho_s", 28, "recoil", "fear", "pool_stones", 18),
                        C("bram_s", 40, "cheer", "cheer", "camera", 16), P("swell", 48, "on")],
    "mountain.keeper": [H("bram_k", "ember_alone"), P("long_shadow", 0, "off"), C("bram_k", 0, "recoil", "fear", "altar", 40), C("ho_k", 16, "laugh", "laugh", "camera", 20), C("ho_k", 40, "bow", "neutral", "camera", 20),
                        P("long_shadow", 32, "on")],
    "mountain.taken": [H("bram_c", "ember_alone"), C("rd_c0", 0, "laugh", "laugh", "camera", 18), C("rd_c1", 2, "laugh", "laugh", "camera", 18), C("rd_c2", 4, "laugh", "laugh", "camera", 18),
                       C("rd_c0", 22, "stamp", "anger", "", 10), C("rd_c1", 24, "stamp", "anger", "", 10), C("captain", 16, "offer", "resolve", "camera", 22), C("bram_c", 8, "plead", "plea", "camera", 20)],
}


# ---- acting of the characters a hotspot touches ---------------------------------------------------------------------------------------------------

def A(act, face="", look="", beats=None, then=None):
    d = {"act": act}
    if face:
        d["face"] = face
    if look:
        d["look_at"] = look
    if beats:
        d["beats"] = beats
    if then:
        d["then"] = then
    return d


ACTING = {
    "bram_f": dict(available=A("plead", "plea", "camera"), selected=A("nod", "relief", "camera"), committed=A("point", "resolve", "ford_cross"), success=A("cheer", "relief", "camera", 8),
                   failure=A("collapse", "grief", "", 10, then=A("stare", "sad", "camera"))),
    "warden_i": dict(available=A("beckon", "resolve", "camera"), selected=A("nod", "resolve", "camera"), committed=A("point", "resolve", "inn_back"), success=A("beckon", "resolve", "camera", 8),
                     failure=A("shake_head", "doubt", "", 8, then=A("stare", "resolve", "camera"))),
    "lady": dict(available=A("offer", "awe", "camera"), selected=A("nod", "relief", "camera"), committed=A("offer", "resolve", "camera"), success=A("nod", "relief", "camera", 8),
                 failure=A("shake_head", "fear", "", 8, then=A("stare", "grief", "camera"))),
    "bram_fb": dict(available=A("beckon", "happy", "camera"), selected=A("nod", "relief", "camera"), committed=A("point", "resolve", "boat_wp"), success=A("cheer", "relief", "camera", 8),
                    failure=A("cover_face", "grief", "", 10, then=A("stare", "sad", "camera"))),
    "ho_m": dict(available=A("beckon", "plea", "camera"), selected=A("plead", "plea", "camera"), committed=A("point", "doubt", "marsh_path"), success=A("beckon", "happy", "camera", 6, then=A("laugh", "anger", "marsh_fwd", 12)),
                 failure=A("shake_head", "anger", "", 8, then=A("stare", "anger", "camera"))),
    "sentinel": dict(available=A("stare", "neutral", "camera"), selected=A("block", "neutral", "camera"), committed=A("stare", "neutral", "camera"), success=A("bow", "neutral", "", 10, then=A("sleep", "neutral")),
                     failure=A("stamp", "anger", "", 8, then=A("stare", "neutral", "camera"))),
    "captain": dict(available=A("offer", "resolve", "camera"), selected=A("stare", "resolve", "camera"), committed=A("point", "resolve", "camera"), success=A("bow", "resolve", "camera", 8, then=A("stare", "neutral", "camera")),
                    failure=A("laugh", "laugh", "camera", 8, then=A("stare", "resolve", "camera"))),
}


# ---- hotspots -----------------------------------------------------------------------------------------------------------------------------------

def hs(sid, name, kind, anchor, success, failure=None, *, default=False, repeatable=False, look=None, radius=None, flags_all=None, flags_none=None, acting=None, cinematic=None):
    world = BY_ID[sid]["world"]
    h = {"id": f"{sid}.{name}", "world": world, "scene": sid, "map": dict((w[0], w[2]) for w in WORLDS)[world], "anchor": anchor, "kind": kind, "radius_m": radius or (1.0 if kind == "exit" else 0.9),
         "min_px": 72, "available": {"flags_all": flags_all or [], "flags_none": flags_none or [], "energy_min": 0, "once": False},
         "look": {"available": look or {"exit": "open", "object": "glow", "character": "beckon", "feature": "pulse", "encounter": "flicker", "secret": "pulse"}[kind], "selected": "ring", "committed": "flash"},
         "challenge": None, "on_success": success}
    if failure is not None:
        h["on_failure"] = failure
    if cinematic:
        h["cinematic"] = cinematic
    h["default"] = default
    h["repeatable"] = repeatable or kind == "exit"
    if acting:
        h["acting"] = {"actor": acting} | ACTING[acting]
    return h


def out(route=None, flags=None, energy=None, cine=None):
    d = {}
    if route:
        d["route"] = route
    if flags:
        d["flags_set"] = flags
    if energy:
        d["energy"] = energy
    if cine:
        d["cinematic"] = cine
    return d


QUENCHED = "keep:path_ember_quenched"
KEPT = "keep:path_ember_kept"

HOTSPOTS = [
    # E00 the Orchard
    hs("hollow", "gate", "exit", {"waypoint": "orchard_gate"}, out("hollow.ford"), out("hollow.ford", energy=-5), default=True),
    hs("hollow", "ember_bowl", "object", {"thing": "ember_bowl"}, out(flags=["ember_held"], energy=6), out(energy=-3), repeatable=True, look="pulse"),
    # E01 the Ford at Night
    hs("hollow.ford", "crossing", "exit", {"waypoint": "ford_cross"}, out("hollow.inn"), out("hollow.inn", energy=-5), default=True),
    hs("hollow.ford", "lantern", "character", {"actor": "bram_f"}, out("north", flags=["ember_bram_lamp"], cine="ember.river_rises"), out("hollow.inn", energy=-8, cine="ember.bram_falls"), acting="bram_f"),
    # E02 the Lantern Inn
    hs("hollow.inn", "back_door", "exit", {"waypoint": "inn_back"}, out("north"), out("north", energy=-5), default=True),
    hs("hollow.inn", "hooded_man", "character", {"actor": "warden_i"}, out("north.pass", flags=["ember_warden_met"]), out("north", energy=-4), acting="warden_i"),
    # E03 the Birch Hall
    hs("north", "porch", "exit", {"waypoint": "hall_far"}, out("north.pass"), out("north.pass", energy=-5), default=True),
    hs("north", "ladys_hand", "character", {"actor": "lady"}, out("deeps", flags=["ember_vial"]), out("north.pass", flags=["ember_no_vial"], energy=-6), acting="lady"),
    hs("north", "map_table", "object", {"thing": "table_map"}, out("north.pass", flags=["ember_map"]), out("deeps", energy=-4), look="glow"),
    # E04 the High Pass
    hs("north.pass", "cave_mouth", "exit", {"thing": "cave"}, out("deeps", cine="ember.pass_calm"), out("deeps", energy=-5), default=True),
    hs("north.pass", "ridge_path", "exit", {"thing": "ridge"}, out("deeps.falls"), out("deeps", energy=-6)),
    # E05 the Deep Halls
    hs("deeps", "bridge", "exit", {"waypoint": "bridge_wp"}, out("deeps.falls"), out("deeps.falls", energy=-5), default=True),
    hs("deeps", "lake", "encounter", {"thing": "drowned"}, out("deeps.falls", flags=["ember_lake_calm"]), out("north.pass", flags=["ember_warden_lost"], energy=-8, cine="ember.warden_falls"), look="flicker", radius=1.6),
    # E06 the Falls
    hs("deeps.falls", "landing", "exit", {"waypoint": "boat_wp"}, out("marsh"), out("marsh", energy=-5), default=True),
    hs("deeps.falls", "boat", "character", {"actor": "bram_fb"}, out("marsh", flags=["ember_bram_boat"]), out("marsh.wall", flags=["ember_alone"], energy=-6), acting="bram_fb"),
    hs("deeps.falls", "horn", "object", {"thing": "horn"}, out("marsh.wall", flags=["ember_horn"]), out("marsh", energy=-4), look="glow", flags_none=["ember_warden_lost"]),
    hs("deeps.falls", "riders_horn", "object", {"thing": "horn"}, out("mountain.taken", flags=["ember_horn_riders"]), out("marsh", energy=-6), look="glow", flags_all=["ember_warden_lost"]),
    # E07 the Reed Marsh
    hs("marsh", "path", "exit", {"waypoint": "marsh_path"}, out("marsh.wall"), out("marsh.wall", energy=-5), default=True),
    hs("marsh", "hollow_one", "character", {"actor": "ho_m"}, out("marsh.stair", flags=["ember_hollow_trust"]), out("marsh.wall", energy=-6), acting="ho_m"),
    hs("marsh", "lights", "feature", {"thing": "mlight1"}, out("marsh.wall", flags=["ember_lights"]), out("marsh.stair", energy=-4), look="pulse", radius=1.4),
    # E08 the Black Wall
    hs("marsh.wall", "crack", "exit", {"thing": "crack"}, out("marsh.stair"), out("marsh.stair", energy=-5), default=True),
    hs("marsh.wall", "gate", "encounter", {"thing": "gate_black"}, out("marsh.plain", flags=["ember_gate_open"]), out("mountain.taken", energy=-8, cine="ember.riders_seize"), look="flicker", radius=1.8),
    # E09 the Stair of Bells
    hs("marsh.stair", "side_path", "exit", {"waypoint": "stair_side"}, out("marsh.plain"), out("marsh.plain", energy=-5), default=True),
    hs("marsh.stair", "bells", "feature", {"thing": "bells"}, out("marsh.plain", flags=["ember_bells_silent"]), out("marsh.plain", energy=-6), look="pulse", radius=1.5, flags_none=["ember_no_vial"]),
    hs("marsh.stair", "bells_hard", "feature", {"thing": "bells"}, out("marsh.plain", flags=["ember_bells_silent"]), out("mountain.taken", energy=-8, cine="ember.riders_seize"), look="pulse", radius=1.5,
       flags_all=["ember_no_vial"]),
    hs("marsh.stair", "sentinel", "encounter", {"actor": "sentinel"}, out("mountain", flags=["ember_sentinel_asleep"], cine="ember.sentinel_sleeps"), out("mountain.taken", energy=-8, cine="ember.riders_seize"), acting="sentinel"),
    # E10 the Ash Plain
    hs("marsh.plain", "road", "exit", {"waypoint": "road_wp"}, out("mountain"), out("mountain", energy=-5), default=True),
    hs("marsh.plain", "tower", "feature", {"thing": "tower"}, out("mountain.taken", flags=["ember_tower"]), out("mountain", energy=-4), look="pulse", radius=1.4),
    # E11 the Throat
    hs("mountain", "way_down", "exit", {"waypoint": "down_wp"}, out("mountain.spring"), out("mountain.spring", energy=-5), default=True),
    hs("mountain", "whisper", "feature", {"thing": "vent1"}, out("mountain.keeper", flags=["ember_listened"]), out("mountain.spring", energy=-6), look="pulse", radius=1.2),
    # E12 the Drowned Spring (ending quenched)
    hs("mountain.spring", "way_back", "exit", {"waypoint": "pool_wp"}, out("run:warehouse", flags=[QUENCHED]), out("run:warehouse", flags=[QUENCHED], energy=-5), default=True),
    hs("mountain.spring", "pool", "feature", {"thing": "pool_stones"}, out("run:warehouse", flags=[QUENCHED]), out("run:warehouse", flags=[QUENCHED], cine="ember.snatched"), look="pulse", radius=1.8),
    # E13 the Keeper (ending kept)
    hs("mountain.keeper", "way_back", "exit", {"waypoint": "ember_wp"}, out("run:warehouse", flags=[KEPT]), out("run:warehouse", flags=[KEPT], energy=-5), default=True),
    hs("mountain.keeper", "ember", "feature", {"thing": "altar"}, out("run:warehouse", flags=[KEPT]), out("run:warehouse", flags=[KEPT], energy=-4), look="pulse", radius=1.4),
    # E14 Taken (setback)
    hs("mountain.taken", "camp_out", "exit", {"waypoint": "stake_wp"}, out("marsh.plain"), out("marsh.plain", energy=-5), default=True),
    hs("mountain.taken", "stake", "object", {"thing": "stake"}, out("marsh.plain", flags=["ember_escaped"]), out("marsh.wall", energy=-6), look="glow"),
    hs("mountain.taken", "captain", "encounter", {"actor": "captain"}, out("marsh.wall", flags=["ember_bargain"]), out("marsh.plain", energy=-10), acting="captain"),
]

# ---- cinematics: what the outcome plays (a short move and the acted reactions of the people around) ------------------------------------------------

CINEMATICS = {
    "ember.river_rises": {"world": "hollow", "steps": [{"move": "walk", "to": "ford_mid", "bars": 2, "role": "dancer", "style": "walk", "look_at": "stake_l"}],
                          "cast": [P("river_rise", 0, "on"), C("rd_f0", 0.5, "recoil", "fear", "river_rise", 8), C("rd_f1", 1, "recoil", "fear", "river_rise", 8), C("rd_f2", 1.5, "recoil", "fear", "river_rise", 8)]},
    "ember.bram_falls": {"world": "hollow", "steps": [{"move": "walk", "to": "ford_edge", "bars": 2, "role": "queasy", "style": "stagger", "look_at": "bram_f"}],
                         "cast": [C("rd_f0", 0.5, "laugh", "laugh", "bram_f", 8), C("rd_f1", 1, "laugh", "laugh", "bram_f", 8), C("rd_f2", 1.5, "stamp", "anger", "", 8)]},
    "ember.pass_calm": {"world": "north", "steps": [{"move": "walk", "to": "pass_far", "bars": 2, "role": "dancer", "style": "walk", "look_at": "cave"}],
                        "cast": [P("storm", 0, "off"), C("bram_p", 1, "nod", "relief", "camera", 8)]},
    "ember.warden_falls": {"world": "deeps", "steps": [{"move": "walk", "to": "halls_edge", "bars": 2, "role": "queasy", "style": "stagger", "look_at": "drowned"}],
                           "cast": [C("warden_d", 0.5, "collapse", "grief", "drowned", 12), C("bram_d", 1, "cover_face", "fear", "", 10), P("drowned", 2, "off")]},
    "ember.riders_seize": {"world": "marsh", "steps": [{"move": "walk", "to": "wall_w", "bars": 2, "role": "queasy", "style": "stagger", "look_at": "gate_black"}],
                           "cast": [C("rd_w0", 0.5, "laugh", "laugh", "camera", 8), C("rd_w1", 1, "stamp", "anger", "", 8), C("rd_w2", 1.5, "laugh", "laugh", "camera", 8)]},
    "ember.sentinel_sleeps": {"world": "marsh", "steps": [{"move": "walk", "to": "stair_up", "bars": 2, "role": "dancer", "style": "walk", "look_at": "sentinel"}],
                              "cast": [C("ho_b", 1, "cover_face", "shame", "", 8)]},
    "ember.snatched": {"world": "mountain", "steps": [{"move": "walk", "to": "spring_edge", "bars": 2, "role": "dancer", "style": "walk", "look_at": "ho_s"}],
                       "cast": [C("ho_s", 0, "plead", "plea", "camera", 4), C("ho_s", 2, "collapse", "relief", "pool_stones", 12), P("swell", 1, "on"), C("bram_s", 3, "cover_face", "grief", "", 12),
                                C("bram_s", 7, "cheer", "relief", "camera", 8)]},
}

# ---- music prompts (the owner's, verbatim from the plan: one per scene, 8-bar seamless loop) ---------------------------------------------------------

PROMPTS = {
    "hollow": "145 BPM progressive psytrance, 8-bar seamless loop. Soft rolling kick, warm plucked arpeggios, rounded bass pulse, harvest-bell chimes and airy pads. Separate editable MIDI tracks.",
    "hollow.ford": "145 BPM dark psytrance, 8-bar seamless loop. Driving kick, galloping 16th bass, metallic hoof percussion, low horn drones and tense rising leads. Separate editable MIDI tracks.",
    "hollow.inn": "145 BPM full-on psytrance, 8-bar seamless loop. Punchy kick, bouncing bass, tavern-fiddle synth, clapping percussion and a whispering filtered lead. Separate editable MIDI tracks.",
    "north": "145 BPM atmospheric psytrance, 8-bar seamless loop. Deep kick, glassy arpeggios, choir-like pads, flowing bass and birch-wind textures. Separate editable MIDI tracks.",
    "north.pass": "145 BPM hypnotic psytrance, 8-bar seamless loop. Relentless kick, howling filtered noise, icy plucks, low throbbing bass and sparse hollow percussion. Separate editable MIDI tracks.",
    "deeps": "145 BPM dark progressive psytrance, 8-bar seamless loop. Cavernous kick, sub-bass drones, dripping water percussion, dissonant stabs and distant drum hits. Separate editable MIDI tracks.",
    "deeps.falls": "145 BPM melodic psytrance, 8-bar seamless loop. Cascading water arpeggios, deep kick, emotional lead, flowing bass and distant choir pads. Separate editable MIDI tracks.",
    "marsh": "145 BPM swampy psytrance, 8-bar seamless loop. Wet kick, bubbling bass, croaking percussion, eerie whispered vocal synth and submerged pads. Separate editable MIDI tracks.",
    "marsh.wall": "145 BPM industrial psytrance, 8-bar seamless loop. Hammering kick, grinding bass, iron-gate percussion, war-horn synth stabs and oppressive drones. Separate editable MIDI tracks.",
    "marsh.stair": "145 BPM minimal psytrance, 8-bar seamless loop. Tiptoe kick, muted bass pulse, tuned bell percussion, held breath pads and a single tense lead. Separate editable MIDI tracks.",
    "marsh.plain": "145 BPM driving psytrance, 8-bar seamless loop. Marching kick, scorched bass, dry rattling percussion, ash-wind noise sweeps and a distant tolling lead. Separate editable MIDI tracks.",
    "mountain": "145 BPM dark psytrance, 8-bar seamless loop. Pounding kick, molten bass growls, crackling fire percussion, volcanic drones and a hypnotic whispering lead. Separate editable MIDI tracks.",
    "mountain.spring": "145 BPM uplifting psytrance, 8-bar seamless loop. Clean kick, radiant arpeggios, warm bass, water-droplet percussion and a soaring resolving lead. Separate editable MIDI tracks.",
    "mountain.keeper": "145 BPM sinister psytrance, 8-bar seamless loop. Slow-burn kick, seductive warm bass, glowing pad swells, ember-crackle percussion and a lead that never resolves. Separate editable MIDI tracks.",
    "mountain.taken": "145 BPM oppressive psytrance, 8-bar seamless loop. Heavy kick, chained metallic percussion, low horn drones, grinding bass and cold rising sirens. Separate editable MIDI tracks.",
}


def node_json(s: dict) -> dict:
    n = {"id": s["id"], "world": s["world"], "scene": f"{s['code'].lower()}_{s['name']}", "title": s["title"], "entry": bool(s.get("entry")), "exit_scene": bool(s.get("exit")),
         "role": "dancer", "blurb": f"{s['code']} {s['title']}."}
    if s.get("ending"):
        n["ending"] = s["ending"]
    n["next"] = []
    for to, d, loop in s["next"]:
        e = {"to": to, "dir": d, "label": to}
        if loop:
            e["loop"] = True
        n["next"].append(e)
    n["place"] = {"waypoint": s["home"], "rail": {"good": [place(w, "dancer", 3) for w in s["good"]], "bad": [place(w, "queasy", 2) for w in s["bad"]], "arrive": s["arrive"],
                                                  "glances": GLANCES, "strolls": STROLLS, "exits": s["exits"]}}
    n["cast"] = CAST[s["id"]]
    return n


def write(path: str, doc) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
        fh.write("\n")


def main() -> int:
    run = {"schema": 1,
           "path": {"id": "ember", "title": "The Ember Road", "entry_from": "warehouse.bar.ember", "returns_to": "warehouse",
                    "opens": "Take the stranger's VIP pass at the bar, then touch the small ember in the glass on the table (the bar)."},
           "timing": {"bpm": 145, "phase_beats": 64, "block_beats": 16, "cue_span_beats": 12.0, "decision_beat": 12.5, "fade_beats": 2.0},
           "start_node": "hollow",
           "worlds": [{"id": w, "title": t, "map": m, "story": f"res://content/story/{m}.json", "depth": d, "blurb": b} for (w, t, m, d, b) in WORLDS],
           "nodes": [node_json(s) for s in SCENES], "cinematics": CINEMATICS}
    if os.path.exists(os.path.join(OUT, "run.json")):  # the path's mix (the audio polish: level, bass bus) is data kept across a rewrite
        old = json.load(open(os.path.join(OUT, "run.json"), encoding="utf-8"))
        if "mix" in old:
            run["mix"] = old["mix"]
    run = laps_mod.finish_run(run, LAPS, SINGLE_LAP)
    write(os.path.join(OUT, "run.json"), run)
    by_world: dict = {}
    for h in HOTSPOTS:
        by_world.setdefault(h["world"], []).append(h)
    for w, hs_ in by_world.items():
        write(os.path.join(OUT, "hotspots", f"{w}.json"), {"world": w, "hotspots": hs_})
    # the prompts ride on music.json (the shopping list; make_path_placeholders keeps them)
    mp = os.path.join(OUT, "music.json")
    music = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {"schema": 1, "nodes": []}
    music.setdefault("note", "Which pack each scene of the Ember Road plays. Written by tools/content/make_path_placeholders.py ember (synthesised, temporary); the owner's loops replace them with beatshaper.py import --path ember. "
                     "`prompt` is the owner's music prompt for the scene, verbatim from docs/THREE_PATHS_AND_FACES_PLAN.md 6.2.")
    music["placeholder"] = {"genre": "psytrance", "key": 40, "levels_db": {"drums": -21.0, "bass": -11.0, "other": -28.0}, "sub_hz": 90.0, "sub_share_min": 0.45, "bass_over_pad_db_min": 10.0}
    have = {n["id"]: n for n in music["nodes"]}
    for s in SCENES:
        if s["id"] in have:
            have[s["id"]]["prompt"] = PROMPTS[s["id"]]
    music["prompts"] = {s["id"]: {"scene": s["code"], "title": s["title"], "prompt": PROMPTS[s["id"]]} for s in SCENES}
    write(mp, music)
    print(f"ember: {len(SCENES)} scenes, {len(HOTSPOTS)} hotspots, {len(CINEMATICS)} cinematics, {sum(len(v) for v in CAST.values())} cast lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
