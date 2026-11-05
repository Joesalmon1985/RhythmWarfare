"""The Mission Count's story data (docs/THREE_PATHS_AND_FACES_PLAN.md 5.2): the 14 scenes with their routes, hotspots, acting, cast and the three Clause cinematics.

Tables only; make_squadron.py turns them into content/paths/squadron/{run.json, music.json, hotspots/*.json}. Nothing here is text: an act, a face, a look and a beat of a person of the scene's map.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "run"))
from acting_data import L, a  # noqa: E402

CAM = "camera"

# ---- worlds ------------------------------------------------------------------------------------------------------------------------------------------------------------------
WORLDS = [
    {"id": "base", "title": "The Airfield", "map": "airfield", "depth": 1, "blurb": "A small island, a war that never ends and the briefing hut."},
    {"id": "air", "title": "The Mission", "map": "airfield", "depth": 2, "blurb": "The bomber's nose, the Quartermaster's store and the Surgeon's office."},
    {"id": "city", "title": "The Old City", "map": "city", "depth": 3, "blurb": "Red light over the sea, an old city's streets and the Colonel's deal."},
    {"id": "escape", "title": "The Way Out", "map": "harbour", "depth": 4, "blurb": "The count painted higher, a harbour at night, and the neutral coast."},
]

# scene id -> code; routes: (target code, dir, loop?) first = the default
S = {
    "C01": dict(id="base", world="base", room="c01", title="The Briefing Room", entry=True, exit=False, routes=[("C03", "up"), ("C02", "right")]),
    "C02": dict(id="base.c02", world="base", room="c02", title="The Flight Line", entry=True, exit=True, routes=[("C04", "up"), ("C05", "right")]),
    "C03": dict(id="base.c03", world="base", room="c03", title="The Hospital", entry=True, exit=True, routes=[("C05", "up"), ("C06", "right")]),
    "C04": dict(id="air", world="air", room="c04", title="The Bombing Mission", entry=True, exit=True, routes=[("C07", "up"), ("C03", "right")]),
    "C05": dict(id="air.c05", world="air", room="c05", title="The Syndicate", entry=True, exit=True, routes=[("C08", "up"), ("C06", "right", True)]),
    "C06": dict(id="air.c06", world="air", room="c06", title="The Surgeon's Office", entry=True, exit=True, routes=[("C02", "up"), ("C09", "right")]),
    "C07": dict(id="city", world="city", room="c07", title="The Gunner's Last Flight", entry=True, exit=True, routes=[("C10", "up", True), ("C03", "right")]),
    "C08": dict(id="city.c08", world="city", room="c08", title="The Old City", entry=True, exit=False, routes=[("C10", "up"), ("C09", "right")]),
    "C09": dict(id="city.c09", world="city", room="c09", title="The Colonel's Deal", entry=True, exit=True, routes=[("C12", "up"), ("C11", "right")]),
    "C10": dict(id="city.c10", world="city", room="c10", title="The Ruined City", entry=True, exit=True, routes=[("C09", "up", True), ("C12", "right")]),
    "C11": dict(id="escape", world="escape", room="c11", title="Endless Missions", entry=True, exit=True, routes=[("C02", "up", True), ("C12", "right", True)]),
    "C12": dict(id="escape.c12", world="escape", room="c12", title="Escape North", entry=True, exit=False, routes=[("C14", "up"), ("C13", "right")]),
    "C13": dict(id="escape.c13", world="escape", room="c13", title="The Neutral Coast", entry=False, exit=False, ending="free", routes=[("run:warehouse", "up")]),
    "C14": dict(id="escape.c14", world="escape", room="c14", title="Captured", entry=False, exit=True, routes=[("C11", "up", True), ("C12", "right", True)]),
}
for _w in WORLDS:  # the art world's story data file (the run builds its stage from it; these maps are not chapters of the old campaign)
    _w["story"] = f"res://content/story/{_w['map']}.json"
NODE = {k: v["id"] for k, v in S.items()}
MAP_OF_WORLD = {w["id"]: w["map"] for w in WORLDS}


def nid(code: str) -> str:
    return "run:warehouse" if code == "run:warehouse" else NODE[code]


# ---- hotspots: (scene code) -> list of dicts ---------------------------------------------------------------------------------------------------------------------------------
def hs(code, name, kind, anchor, look, ok, bad, default=False, acting=None, repeatable=None, radius=0.9):
    sid = NODE[code]
    h = {"id": f"{sid}.{name}", "scene": sid, "kind": kind, "anchor": anchor, "radius_m": radius, "look": {"available": look}, "on_success": ok, "on_failure": bad, "default": default}
    if repeatable is not None:
        h["repeatable"] = repeatable
    elif kind == "exit":
        h["repeatable"] = True
    if acting:
        h["acting"] = acting
    return h


def to(code, energy=None, flags=None, cin=None):
    o = {"route": nid(code)}
    if flags:
        o["flags_set"] = flags
    if cin:
        o["cinematic"] = cin
    if energy is not None:
        o["energy"] = energy
    return o


def stay(energy, flags=None):
    o = {"energy": energy}
    if flags:
        o["flags_set"] = flags
    return o


HOTSPOTS = {
    "C01": [
        hs("C01", "cot", "exit", {"thing": "cot_empty"}, "open", to("C03"), to("C03", -5), default=True),
        hs("C01", "board", "exit", {"thing": "board"}, "glow", to("C02", 6, ["sq_briefed"]), to("C03", -5), acting={
            "actor": "col", "available": a("point", "resolve", "board"), "selected": a("nod", "resolve", CAM),
            "committed": a("point", "resolve", "board", 1), "success": a("salute", "resolve", CAM, 8), "failure": a("shake_head", "doubt", CAM, 6, then=a("stare", "neutral", CAM, 8))}),
    ],
    "C02": [
        hs("C02", "ladder", "exit", {"thing": "ladder"}, "open", to("C04"), to("C04", -5), default=True, acting={
            "actor": "gun", "available": a("wave", "happy", CAM), "selected": a("wave", "cheer", CAM), "committed": a("point", "resolve", "ladder", 1),
            "success": a("cheer", "cheer", CAM, 8), "failure": a("shake_head", "doubt", CAM, 6)}),
        hs("C02", "crates", "exit", {"thing": "crates"}, "glow", to("C05", 6, ["sq_egg", "keep:path_squadron_met_quartermaster"]), to("C04", -5), acting={
            "actor": "qm", "available": a("offer", "laugh", CAM), "selected": a("laugh", "laugh", CAM), "committed": a("point", "happy", "crates", 1),
            "success": a("offer", "happy", CAM, 8), "failure": a("laugh", "laugh", CAM, 8, then=a("stare", "doubt", CAM, 8))}),
    ],
    "C03": [
        hs("C03", "hatch", "exit", {"thing": "kitchen_hatch"}, "open", to("C05"), to("C05", -5), default=True),
        hs("C03", "office_door", "exit", {"waypoint": "c03_x_right"}, "open", to("C06"), to("C06", -5)),
        hs("C03", "clipboard", "character", {"actor": "surg"}, "beckon", to("C06", 6, ["sq_examined", "keep:path_squadron_met_surgeon"]), to("C05", -6), acting={
            "available": a("write", "doubt", CAM), "selected": a("write", "doubt", "surg"), "committed": a("nod", "doubt", CAM, 1),
            "success": a("nod", "relief", CAM, 8), "failure": a("shake_head", "doubt", CAM, 6, then=a("point", "resolve", "kitchen_hatch", 8))}),
    ],
    "C04": [
        hs("C04", "lever", "exit", {"thing": "release_lever"}, "pulse", to("C07", 6, ["sq_released"]), to("C03", -6, cin="squadron.turn_back"), default=True, acting={
            "actor": "pilot", "available": a("stare", "fear", "release_lever"), "selected": a("nod", "resolve", "release_lever"), "committed": a("point", "resolve", "release_lever", 1),
            "success": a("stare", "resolve", "nose_glass", 8), "failure": a("shake_head", "doubt", CAM, 8)}),
        hs("C04", "emergency", "exit", {"thing": "emergency_box"}, "flicker", to("C03", 3), to("C07", -5, ["sq_released"]), acting={
            "actor": "crew1", "available": a("recoil", "fear", CAM), "selected": a("plead", "plea", CAM), "committed": a("point", "fear", "emergency_box", 1),
            "success": a("cover_face", "relief", CAM, 8), "failure": a("recoil", "fear", CAM, 8)}),
    ],
    "C05": [
        hs("C05", "truck", "exit", {"thing": "truck"}, "open", to("C08"), to("C06", -4), default=True, acting={
            "actor": "drv", "available": a("beckon", "happy", CAM), "selected": a("nod", "happy", CAM), "committed": a("point", "resolve", "truck", 1),
            "success": a("nod", "happy", CAM, 8), "failure": a("shake_head", "doubt", CAM, 8)}),
        hs("C05", "ledger", "exit", {"thing": "ledger"}, "glow", to("C06", 6, ["sq_ledger"]), to("C08", -6), acting={
            "actor": "qm_s", "available": a("write", "laugh", "ledger"), "selected": a("offer", "laugh", CAM), "committed": a("point", "laugh", "ledger", 1),
            "success": a("offer", "happy", CAM, 8, then=a("laugh", "laugh", CAM, 8)), "failure": a("block", "anger", CAM, 8, then=a("stamp", "anger", CAM, 8))}),
    ],
    "C06": [
        hs("C06", "door_a", "exit", {"thing": "door_a"}, "open", to("C02"), to("C02", -5), default=True),
        # The Clause: the rhythm is a success, the bureaucracy thwarts it (cinematic squadron.double_stamp) and the route is not the one the touch promised
        hs("C06", "certificate", "exit", {"thing": "certificate"}, "glow", to("C09", 5, ["sq_stamped", "keep:path_squadron_clause"], cin="squadron.double_stamp"), to("C02", -5), acting={
            "actor": "clerk", "available": a("write", "neutral", "certificate"), "selected": a("stare", "neutral", CAM), "committed": a("stamp", "neutral", "desk_clerk", 1),
            "success": a("laugh", "laugh", CAM, 8), "failure": a("nod", "resolve", CAM, 8)}),
    ],
    "C07": [
        hs("C07", "jacket", "exit", {"thing": "jacket"}, "open", to("C10"), to("C10", -5), default=True, acting={
            "actor": "pilot_c", "available": a("stare", "resolve", "nose_glass_r"), "selected": a("nod", "resolve", "jacket"), "committed": a("point", "resolve", "jacket", 1),
            "success": a("stare", "resolve", "nose_glass_r", 8), "failure": a("stare", "grief", "gun_c", 8)}),
        hs("C07", "medkit", "exit", {"thing": "medkit"}, "glow", to("C03", 3, ["sq_kit"]), to("C10", -6), acting={
            "actor": "crew1c", "available": a("plead", "plea", "medkit"), "selected": a("nod", "plea", CAM), "committed": a("point", "plea", "medkit", 1),
            "success": a("cover_face", "grief", CAM, 8), "failure": a("shake_head", "grief", CAM, 8)}),
    ],
    "C08": [
        hs("C08", "arch", "exit", {"thing": "arch"}, "open", to("C10"), to("C10", -5), default=True, acting={
            "actor": "mp1", "available": a("block", "anger", CAM), "selected": a("stare", "anger", CAM), "committed": a("stamp", "anger", "arch", 1),
            "success": a("nod", "neutral", CAM, 8), "failure": a("stamp", "anger", CAM, 8, then=a("point", "resolve", "street_lamp", 8))}),
        hs("C08", "staff_car", "exit", {"thing": "staff_car"}, "glow", to("C09", 6, ["sq_car"]), to("C10", -5), acting={
            "actor": "mp2", "available": a("stare", "neutral", "staff_car"), "selected": a("block", "anger", CAM), "committed": a("stare", "anger", CAM, 1),
            "success": a("salute", "resolve", CAM, 8), "failure": a("block", "anger", CAM, 8)}),
    ],
    "C09": [
        hs("C09", "map", "exit", {"thing": "escape_map"}, "glow", to("C12", 6, ["sq_map"]), to("C12", -5), default=True, acting={
            "actor": "aide_c", "available": a("write", "doubt", "escape_map"), "selected": a("stare", "doubt", "escape_map"), "committed": a("point", "resolve", "escape_map", 1),
            "success": a("nod", "relief", CAM, 8), "failure": a("shake_head", "doubt", CAM, 8)}),
        # The Clause: success pins the medal and the count goes up anyway; failure throws you out with the map falling into your hands
        hs("C09", "medal", "exit", {"thing": "medal"}, "pulse", to("C11", 5, ["sq_medal", "keep:path_squadron_met_colonel"], cin="squadron.medal_pinned"), to("C12", -5, ["sq_map"]), acting={
            "actor": "col_c", "available": a("offer", "resolve", CAM), "selected": a("nod", "resolve", CAM), "committed": a("point", "resolve", "medal", 1),
            "success": a("laugh", "laugh", CAM, 8), "failure": a("point", "anger", "c09_x_up", 8)}),
    ],
    "C10": [
        hs("C10", "hq", "exit", {"thing": "hq_door"}, "open", to("C09"), to("C09", -5), default=True, acting={
            "actor": "drunk", "available": a("laugh", "laugh", CAM), "selected": a("laugh", "laugh", "hq_door"), "committed": a("point", "laugh", "hq_door", 1),
            "success": a("laugh", "laugh", CAM, 8), "failure": a("laugh", "laugh", CAM, 8)}),
        hs("C10", "train", "exit", {"thing": "night_train"}, "pulse", to("C12", 6, ["sq_train"]), to("C09", -6), acting={
            "actor": "wom", "available": a("plead", "plea", CAM), "selected": a("plead", "plea", "night_train"), "committed": a("point", "plea", "night_train", 1),
            "success": a("cheer", "relief", CAM, 8), "failure": a("collapse", "grief", CAM, 8)}),
    ],
    "C11": [
        hs("C11", "aircraft", "exit", {"thing": "aircraft_door"}, "open", to("C02"), to("C02", -5), default=True),
        # The radio is the loop's way out; its failure is the Clause (the Clerk paints the number higher)
        hs("C11", "radio", "exit", {"thing": "radio_broken"}, "flicker", to("C12", 6, ["sq_radio"]), to("C02", -4, cin="squadron.count_raised"), acting={
            "actor": "chap_h", "available": a("shake_head", "grief", CAM), "selected": a("plead", "plea", "radio_broken"), "committed": a("point", "resolve", "radio_broken", 1),
            "success": a("nod", "relief", CAM, 8), "failure": a("cover_face", "grief", CAM, 8)}),
    ],
    "C12": [
        hs("C12", "searchlights", "exit", {"thing": "search_a"}, "open", to("C14"), to("C14", -5), default=True, acting={
            "actor": "sent", "available": a("stare", "neutral", CAM), "selected": a("stare", "anger", CAM), "committed": a("point", "resolve", "search_a", 1),
            "success": a("point", "anger", CAM, 8), "failure": a("stamp", "anger", CAM, 8)}),
        hs("C12", "boat", "exit", {"thing": "boat"}, "beckon", to("C13", 8, ["sq_boat"]), to("C14", -6), acting={
            "actor": "fish", "available": a("beckon", "fear", CAM), "selected": a("nod", "resolve", CAM), "committed": a("beckon", "resolve", "boat", 1),
            "success": a("nod", "relief", CAM, 8), "failure": a("recoil", "fear", CAM, 8)}),
    ],
    "C13": [
        hs("C13", "shore", "exit", {"thing": "shore_post"}, "open", to("run:warehouse", None, ["keep:path_squadron_free"]), to("run:warehouse", -5, ["keep:path_squadron_free"]), default=True),
        hs("C13", "fisherman", "character", {"actor": "fish_c"}, "beckon", stay(8, ["sq_thanks"]), stay(-3), acting={
            "available": a("laugh", "relief", CAM), "selected": a("nod", "happy", CAM), "committed": a("cheer", "cheer", CAM, 1),
            "success": a("cheer", "cheer", CAM, 8), "failure": a("shake_head", "happy", CAM, 6)}),
    ],
    "C14": [
        hs("C14", "order", "exit", {"thing": "order_paper"}, "open", to("C11"), to("C11", -5), default=True, acting={
            "actor": "clerk_k", "available": a("write", "laugh", "order_paper"), "selected": a("stamp", "laugh", CAM), "committed": a("stamp", "laugh", "order_paper", 1),
            "success": a("laugh", "laugh", CAM, 8), "failure": a("laugh", "laugh", CAM, 8)}),
        hs("C14", "latch", "exit", {"thing": "latch"}, "glow", to("C12", 6, ["sq_latch"]), to("C11", -5), acting={
            "actor": "mate", "available": a("point", "resolve", "latch"), "selected": a("nod", "resolve", CAM), "committed": a("point", "resolve", "latch", 1),
            "success": a("cheer", "relief", CAM, 8), "failure": a("shake_head", "doubt", CAM, 8)}),
    ],
}

# ---- cast: the beats that happen whether or not anything is touched ---------------------------------------------------------------------------------------------------------
CAST = {
    "C01": [L("col", 0, "point", "resolve", "board", 14), L("a01", 16, "salute", "resolve", CAM, 6), L("a02", 16.5, "salute", "resolve", CAM, 6), L("a03", 17, "salute", "resolve", CAM, 6),
            L("a06", 32, "shake_head", "fear", CAM, 12), L("a04", 48, "salute", "resolve", CAM, 8), L("col", 48, "stare", "resolve", CAM, 12)],
    "C02": [L("gun", 0, "wave", "happy", CAM, 14), L("qm", 16, "offer", "laugh", CAM, 14), L("mech", 32, "stare", "doubt", CAM, 16), L("qm", 48, "laugh", "laugh", CAM, 12)],
    "C03": [L("surg", 0, "write", "doubt", CAM, 14), L("p01", 16, "laugh", "laugh", CAM, 12), L("surg", 32, "write", "doubt", "surg", 14), L("p01", 48, "laugh", "laugh", CAM, 10)],
    "C04": [L("pilot", 0, "stare", "fear", "nose_glass", 14), L("crew1", 16, "recoil", "fear", "nose_glass", 12), L("gun_b", 32, "point", "resolve", "c04_b1", 14), L("crew2", 32, "recoil", "fear", CAM, 12),
            L("crew1", 61, "cheer", "relief", CAM, 3, if_flags_all=["sq_released"]), L("gun_b", 61.5, "collapse", "grief", CAM, 6, if_flags_all=["sq_released"]),
            L("pilot", 61, "shake_head", "doubt", CAM, 6, if_flags_none=["sq_released"])],
    "C05": [L("qm_s", 0, "write", "laugh", "ledger", 14), L("sc1", 16, "nod", "happy", CAM, 8), L("sc2", 17, "nod", "happy", CAM, 8), L("qm_s", 32, "offer", "laugh", CAM, 14), L("sc1", 48, "nod", "happy", CAM, 8),
            L("sc2", 49, "nod", "happy", CAM, 8)],
    "C06": [L("surg_o", 0, "plead", "plea", "clerk", 14), L("clerk", 0, "write", "neutral", CAM, 14), L("clerk", 16, "stare", "neutral", "surg_o", 14), L("surg_o", 32, "plead", "plea", "clerk", 14),
            L("clerk", 48, "stare", "neutral", CAM, 14)],
    "C07": [L("gun_c", 0, "lie", "fear", CAM, 46), L("gun_c", 48, "lie", "neutral", CAM, 16), L("crew1c", 16, "cover_face", "grief", CAM, 20), L("crew2c", 32, "cover_face", "grief", CAM, 20),
            L("pilot_c", 0, "stare", "resolve", "nose_glass_r", 60)],
    "C08": [L("singer", 0, "laugh", "laugh", CAM, 12), L("singer", 16, "offer", "happy", CAM, 14), L("mp1", 0, "block", "anger", CAM, 14), L("mp2", 32, "block", "anger", CAM, 14), L("kid_c", 16, "beckon", "happy", CAM, 12),
            L("kid_c", 48, "beckon", "happy", CAM, 12)],
    "C09": [L("col_c", 0, "offer", "resolve", CAM, 30), L("aide_c", 0, "write", "neutral", CAM, 30), L("chap", 16, "shake_head", "grief", CAM, 12), L("chap", 48, "shake_head", "grief", CAM, 12)],
    "C10": [L("surv1", 0, "collapse", "grief", CAM, 14), L("surv2", 16, "collapse", "grief", CAM, 14), L("wom", 16, "plead", "plea", CAM, 14), L("drunk", 32, "laugh", "laugh", CAM, 14),
            L("wom", 48, "plead", "plea", "night_train", 12)],
    "C11": [L("col_h", 0, "point", "resolve", "count_board", 14), L("h01", 0, "salute", "resolve", CAM, 3), L("h02", 0.5, "salute", "resolve", CAM, 3), L("h03", 1, "salute", "resolve", CAM, 3),
            L("h01", 16, "salute", "resolve", CAM, 6), L("h02", 16.5, "salute", "resolve", CAM, 6), L("h03", 17, "salute", "resolve", CAM, 6),
            L("h01", 32, "salute", "resolve", CAM, 10), L("h02", 32.5, "salute", "resolve", CAM, 10), L("h03", 33, "salute", "resolve", CAM, 10),
            L("h01", 48, "salute", "resolve", CAM, 14), L("h02", 48.5, "salute", "resolve", CAM, 14), L("h03", 49, "salute", "resolve", CAM, 14),
            L("chap_h", 16, "cover_face", "grief", CAM, 14), L("chap_h", 48, "cover_face", "grief", CAM, 12)],
    "C12": [L("fish", 0, "beckon", "fear", CAM, 14), L("sent", 0, "stare", "neutral", CAM, 30), L("fish", 32, "nod", "relief", CAM, 14),
            L("sent", 61, "stare", "shame", CAM, 3, if_flags_all=["sq_boat"]), L("sent", 61, "point", "resolve", CAM, 3, if_flags_none=["sq_boat"])],
    "C13": [L("fish_c", 0, "laugh", "relief", CAM, 14), L("quay_w", 16, "wave", "happy", CAM, 14), L("dock_c", 32, "laugh", "laugh", CAM, 12), L("kid_q", 48, "wave", "happy", CAM, 12)],
    "C14": [L("guard", 0, "block", "anger", CAM, 14), L("clerk_k", 0, "write", "neutral", CAM, 14), L("mate", 16, "shake_head", "doubt", CAM, 12), L("clerk_k", 32, "laugh", "laugh", CAM, 14),
            L("mate", 32, "point", "resolve", "latch", 14)],
}

# ---- cinematics: the Clause's three, and the bomber turning back --------------------------------------------------------------------------------------------------------------
CINEMATICS = {
    "squadron.double_stamp": {"world": "air", "steps": [{"move": "walk", "to": "c06_desk", "bars": 2, "role": "dancer", "style": "walk", "look_at": "stamp_big"}],
                              "cast": [L("clerk", 0.5, "stamp", "laugh", CAM, 4), L("clerk", 3, "laugh", "laugh", CAM, 6), L("surg_o", 1.5, "cover_face", "shame", CAM, 10)]},
    "squadron.medal_pinned": {"world": "city", "steps": [{"move": "walk", "to": "c09_g1", "bars": 2, "role": "dancer", "style": "walk", "look_at": "col_c"}],
                              "cast": [L("col_c", 0.5, "laugh", "laugh", CAM, 8), L("aide_c", 1, "write", "neutral", CAM, 8), L("chap", 1.5, "shake_head", "grief", CAM, 8)]},
    "squadron.count_raised": {"world": "escape", "steps": [{"move": "walk", "to": "c11_count", "bars": 2, "role": "dancer", "style": "walk", "look_at": "count_board"}],
                              "cast": [L("clerk_h", 0.5, "write", "laugh", "count_board", 8), L("col_h", 1, "point", "resolve", "count_board", 8), L("chap_h", 1.5, "cover_face", "grief", CAM, 8)]},
    "squadron.turn_back": {"world": "air", "steps": [{"move": "walk", "to": "c04_b1", "bars": 2, "role": "queasy", "style": "stagger", "look_at": "pilot"}],
                           "cast": [L("pilot", 0.5, "shake_head", "doubt", CAM, 8), L("crew2", 1, "recoil", "fear", CAM, 8), L("gun_b", 2, "cover_face", "fear", CAM, 8)]},
}

# the music: which pack each scene plays (the owner's 14 loops)
PACK = {code: f"squadron_{code.lower()}" for code in S}
