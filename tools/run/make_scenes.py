#!/usr/bin/env python3
"""Authors the run's scenes (WP-A5): the worlds of content/run/run.json as small graphs of scenes, the doorway waypoints they need in the five world maps,
and content/story/music.json (one entry per scene). Idempotent: run it again after editing the tables below.

    python3 tools/run/make_scenes.py

Everything written here is plain data the game validates (RunData, RunRail, tests/test_run_rail.gd). Yaw: 0 faces -z, 90 faces -x, 180 faces +z, -90 faces +x.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "content/run/run.json"
MUSIC = ROOT / "content/story/music.json"
MAPS = ROOT / "content/story/maps"

# ---- waypoints added to the maps: (map file, id, [x, z], yaw, sector) -----------------------------------------------------------------------------
NEW_WAYPOINTS = {
    "night_one": [
        ("to_bar", (6.3, 2.5), -90, "floor"), ("to_balcony", (-6.3, 1.0), 90, "floor"), ("floor_bar", (5.2, 4.0), -90, "floor"),
        ("bar_door", (7.8, 2.5), 90, "bar"), ("bar_to_chill", (9.5, 5.3), 180, "bar"), ("bar_end", (11.2, 1.2), 90, "bar"), ("bar_taps", (9.2, 4.8), -90, "bar"),
        ("balcony_door", (-7.8, 1.0), -90, "balcony"), ("balcony_stairs", (-8.5, -2.3), 0, "balcony"), ("balcony_far", (-10.2, 4.0), 90, "balcony"),
        ("chill_door", (9.5, 6.8), 0, "chill"), ("sofa_nook", (11.2, 8.4), 90, "chill"), ("sofa_front", (9.5, 11.3), 180, "sofa_a"),
        ("booth_down", (0.0, -8.4), 180, "booth"), ("booth_decks", (0.0, -9.6), 180, "booth"),
        ("door_r", (2.3, 10.2), 0, "entrance"),
    ],
    "mothership": [
        ("deck_ramp", (0.0, -0.4), 0, "deck"), ("deck_dais", (0.0, -4.7), 180, "deck_dais"), ("deck_sw_corner", (-9.5, 0.5), 90, "deck_sw"),
        ("deck_gallery_door", (6.3, 5.5), -90, "deck"), ("deck_reactor_door", (6.3, 7.8), -90, "deck"),
        ("gallery_door", (7.8, 5.5), -90, "gallery"), ("gallery_mid", (17.0, 6.5), -90, "gallery"), ("gallery_west", (8.2, 4.0), 90, "gallery"),
        ("gallery_east", (26.3, 7.5), -90, "gallery"),
        ("catwalk_door", (27.8, 7.5), -90, "catwalk"), ("catwalk_bridge", (40.2, 7.5), -90, "catwalk"), ("catwalk_mid", (33.0, 7.5), -90, "catwalk"),
        ("bridge_door", (41.8, 7.5), -90, "bridge"),
        ("med_door", (34.0, 9.7), 180, "medbay"), ("med_alcove_in", (29.8, 12.0), 90, "med_alcove"), ("exam_door", (36.5, 12.0), -90, "medbay"), ("airlock_door", (34.0, 14.6), 180, "medbay"),
    ],
    "underworld": [
        ("arena_gate", (0.0, -2.5), 0, "arena"), ("gate_dais", (0.0, -4.6), 180, "gate_dais"), ("tier_l_in", (-9.0, 3.0), 90, "tier_l"), ("tier_r_in", (9.0, 3.0), -90, "tier_r"),
        ("arena_tier_r", (6.4, 3.0), -90, "arena"), ("arena_tier_l", (-6.4, 3.0), 90, "arena"),
        ("court_door", (11.8, 4.0), -90, "court"), ("court_mid", (19.0, 4.0), -90, "court"), ("court_causeway", (19.0, 7.4), 180, "court"),
        ("furnace_door", (-11.3, 4.0), 90, "furnace"), ("furnace_mid", (-20.0, 4.0), 90, "furnace"), ("furnace_out", (-11.6, 6.0), -90, "furnace"),
        ("causeway_in", (19.0, 9.0), 180, "causeway"), ("pit_door", (19.0, 10.6), 180, "pit_deck"), ("pit_rim_e", (24.0, 12.5), 90, "pit_deck"),
        ("throne_door_l", (30.2, 1.0), 90, "throne"), ("throne_door_r", (30.2, 7.0), 90, "throne"),
    ],
    "hospital": [
        ("ward_door", (4.2, 1.0), -90, "ward"), ("bed_corner", (-1.4, 7.4), 180, "bed"), ("bed_far", (1.4, 7.6), 180, "bed"),
        ("corridor_mid", (14.0, 1.0), -90, "corridor"), ("corridor_fork", (21.0, 1.0), -90, "corridor"), ("corridor_quiet_door", (14.2, 2.2), 180, "corridor"),
        ("corridor_day_door", (20.0, -0.4), 0, "corridor"), ("corridor_cafe", (30.8, 1.0), -90, "station"),
        ("dayroom_mid", (20.0, -6.5), 0, "dayroom"), ("day_tv_in", (20.0, -13.2), 0, "day_tv"), ("dayroom_door", (20.0, -1.4), 180, "dayroom"),
        ("cafe_door_w", (33.8, 1.25), -90, "cafeteria"), ("cafe_mid", (40.0, 1.0), -90, "cafeteria"), ("cafe_serving", (44.0, -3.0), -90, "cafeteria"),
        ("cafe_garden_door", (46.2, 1.0), -90, "cafeteria"),
        ("garden_north", (53.0, -5.5), 90, "garden"), ("garden_south", (53.0, 8.0), 90, "garden"), ("garden_sw", (49.0, 8.6), 0, "garden"),
        ("garden_door_w", (47.8, 1.0), 90, "garden"), ("garden_door_w2", (47.8, -3.0), 90, "garden"), ("garden_door_e", (58.2, 1.0), -90, "garden"),
        ("quiet_far", (14.2, 14.5), 180, "quiet"), ("quiet_door", (14.2, 3.8), 0, "quiet"),
        ("bandstand_front", (62.4, -1.8), 90, "bandstand"), ("bandstand_door_l", (59.8, -1.8), -90, "bandstand"), ("bandstand_door_r", (59.8, 3.8), -90, "bandstand"),
    ],
    "mental_hospital": [
        ("bars_in", (5.0, -2.6), 180, "dayroom"), ("day_stage_in", (0.0, -4.2), 180, "day_stage"), ("day_corner", (-6.0, 8.0), 90, "dayroom"),
        ("day_door_a", (6.3, 6.8), -90, "dayroom"), ("day_door_b", (6.3, 5.0), -90, "dayroom"),
        ("art_door", (33.8, 6.0), 90, "art_room"), ("art_mid", (40.0, 6.0), -90, "art_room"), ("art_easels", (44.0, 10.0), 0, "art_room"), ("art_east_door", (46.2, 7.0), -90, "art_room"),
        ("dorm_door", (26.0, 8.6), 0, "dorm"), ("dorm_mid", (26.0, 12.0), 180, "dorm"), ("dorm_bed", (26.0, 15.4), 180, "dorm_alcove"),
        ("corr_west", (7.8, 6.0), -90, "corridor"), ("corr_mid", (18.0, 6.0), -90, "corridor"), ("corr_east", (30.0, 6.0), -90, "corridor"), ("corr_art_door", (32.4, 6.0), -90, "corridor"),
        ("court_door_w", (47.8, 7.0), -90, "courtyard"), ("court_mid", (54.0, 7.0), -90, "courtyard"), ("court_stage_door", (60.4, 7.0), -90, "courtyard"),
        ("stage_door_l", (62.6, 4.6), 90, "c_stage"), ("stage_door_r", (62.6, 9.4), 90, "c_stage"),
        ("court_north", (53.0, 1.0), 90, "courtyard"), ("court_south", (53.0, 12.0), 90, "courtyard"),
        ("treat_door", (16.0, 8.6), 0, "treatment"),
    ],
}

# ---- things added to the maps for the visual adventure (workstream C): anchors for hotspots that no existing thing gave. One billboard per row: id, sprite, (x, z), y, size, anim. -------
# Sprites are drawn by the chapter's own generator (tools/story/art/tex_<chapter>.py) and registered in tiles.py; lights are {"kind": "light"} things.
NEW_THINGS = {
    "night_one": [
        ("wizard_floor", "thing_wizard", (-5.2, 7.4), 0.85, 1.7, "sway"), ("wizard_chill", "thing_wizard", (8.4, 9.7), 0.85, 1.7, "sway"),
        ("headphones_booth", "thing_headphones", (0.9, -8.4), 1.15, 0.5, "none"), ("crack_door", "thing_crack", (2.85, 10.7), 1.2, 2.4, "none"),
    ],
    "hospital": [("mic_band", "thing_mic", (62.3, 1.4), 0.75, 1.5, "none")],
    "mental_hospital": [("mural_door", "thing_mural", (24.0, 7.85), 1.0, 2.0, "none")],
}
NEW_LIGHTS = {  # id, (x, z), y, radius, color, strength
    "night_one": [("lt_crack", (2.5, 10.7), 1.2, 3.2, "#ff5a28", 1.3), ("lt_ship_beam", (0.0, 15.5), 1.5, 4.5, "#7ff0ff", 1.2), ("lt_wizard_floor", (-5.0, 7.0), 1.6, 3.0, "#8060ff", 0.9),
                  ("lt_wizard_chill", (8.6, 9.2), 1.6, 2.6, "#8060ff", 0.8)],
    "hospital": [("lt_band_mic", (62.0, 1.2), 1.8, 3.5, "#ffd890", 1.0)],
    "mental_hospital": [("lt_mural", (24.0, 7.2), 1.8, 3.0, "#ffd27a", 1.0)],
}

# ---- journeys inside a scene ------------------------------------------------------------------------------------------------------------------
GL = {  # glances and strolls per art world (the rails of the first WP-A rails, reused; the scene id lengths vary them)
    "night_one": ([{"by": -28, "bars": 2}, {"pitch": 14, "bars": 3}, {"by": 24, "bars": 2}, {"by": -12, "pitch": 8, "bars": 2}],
                  [{"fwd": 1.6, "bars": 3}, {"turn": 35, "fwd": 1.0, "bars": 3}, {"right": 1.4, "bars": 2}]),
    "mothership": ([{"pitch": 18, "bars": 3}, {"by": 30, "bars": 2}, {"by": -22, "bars": 2}, {"pitch": 10, "by": 14, "bars": 2}],
                   [{"fwd": 1.5, "bars": 3}, {"turn": -40, "fwd": 0.9, "bars": 3}, {"right": -1.3, "bars": 2}]),
    "underworld": ([{"by": 26, "bars": 2}, {"pitch": 12, "bars": 3}, {"by": -30, "bars": 2}, {"pitch": -8, "bars": 2}],
                   [{"fwd": 1.7, "bars": 3}, {"turn": 30, "fwd": 1.1, "bars": 3}, {"right": 1.5, "bars": 2}]),
    "hospital": ([{"by": -20, "bars": 2}, {"pitch": 10, "bars": 3}, {"by": 28, "bars": 2}, {"pitch": -6, "by": 10, "bars": 2}],
                 [{"fwd": 1.4, "bars": 3}, {"turn": -30, "fwd": 0.9, "bars": 3}, {"right": 1.2, "bars": 2}]),
    "mental_hospital": ([{"by": 22, "bars": 2}, {"pitch": 12, "bars": 3}, {"by": -26, "bars": 2}, {"by": 12, "pitch": 6, "bars": 2}],
                        [{"fwd": 1.5, "bars": 3}, {"turn": 32, "fwd": 1.0, "bars": 3}, {"right": -1.4, "bars": 2}]),
}


def P(to, role="dancer", style="walk", bars=3):
    return {"to": to, "role": role, "style": style, "bars": bars}


def up(to, bars=3):
    return P(to, "on_stage", "climb", bars)


def down(to, role="queasy", style="walk", bars=2):
    return P(to, role, style, bars)


WORLDS = [
    {"id": "warehouse", "title": "Warehouse", "map": "night_one", "depth": 1, "blurb": "Doors open. Find the groove. The floor, the bar or the balcony, the chill-out or the booth, and out."},
    {"id": "mothership", "title": "The Mothership", "map": "mothership", "depth": 2, "blurb": "The lights go strange. The deck, the gallery or the reactor, the bridge, and the airlock."},
    {"id": "underworld", "title": "The Underworld", "map": "underworld", "depth": 2, "blurb": "The floor cracks open. The arena, the court or the furnace, the pit, and the throne."},
    {"id": "hospital", "title": "The Hospital", "map": "hospital", "depth": 3, "blurb": "Visiting hours never end. The ward, the corridor, the day room or the cafeteria, the garden, the bandstand."},
    {"id": "ward", "title": "The Ward", "map": "mental_hospital", "depth": 3, "blurb": "Group therapy at 174 BPM. The day room, the art room or the dormitory, the corridor, the courtyard, the stage."},
    {"id": "hospital_late", "title": "The Hospital, late", "map": "hospital", "depth": 4, "blurb": "The garden after dark: the cafeteria or the quiet room, then the bandstand, round again."},
    {"id": "ward_late", "title": "The Ward, late", "map": "mental_hospital", "depth": 4, "blurb": "The courtyard stage after hours: the treatment room or the dormitory, then the day room, round again."},
]

# scene: id, world, short name, title, home, good, bad, arrive, exits {dir: waypoint}, next [(to, dir, label[, loop])], flags
S: list[dict] = []


def scene(sid, world, name, title, home, good, bad, arrive, exits, nxt, entry=False, exit_scene=False, role="dancer"):
    S.append({"id": sid, "world": world, "scene": name, "title": title, "entry": entry, "exit_scene": exit_scene, "home": home, "good": good, "bad": bad,
              "arrive": arrive, "exits": exits, "next": nxt, "role": role})


# --- the Warehouse --------------------------------------------------------------------------------------------------------------------------
scene("warehouse", "warehouse", "floor", "The Floor", "floor_centre",
      [P("steps"), up("stage", 2), up("balcony", 4), P("booth", "dj")], [down("floor_edge"), down("corridor", "queasy", "stagger", 4), down("cubicle", "sick", "run", 4)],
      "door", {"right": "to_bar", "up": "to_balcony"},
      [("warehouse.bar", "right", "Past the speaker stacks, the bar"), ("warehouse.balcony", "up", "Up the side stairs to the balcony")], entry=True)
scene("warehouse.bar", "warehouse", "bar", "The Bar", "bar", [P("bar_taps"), P("bar_end")], [down("bar_door"), down("floor_bar")],
      "bar_door", {"right": "bar_to_chill", "left": "bar_door"},
      [("warehouse.chill", "right", "Through the curtain to the chill-out"), ("warehouse.booth", "left", "Back across the floor, up to the booth")])
scene("warehouse.balcony", "warehouse", "balcony", "The Balcony", "balcony", [P("balcony_rail"), P("balcony_far")], [down("balcony_door"), down("floor_edge")],
      "balcony_door", {"right": "balcony_door", "left": "balcony_stairs"},
      [("warehouse.chill", "right", "Down to the floor and round to the chill-out"), ("warehouse.booth", "left", "Along the stairs to the booth")])
scene("warehouse.chill", "warehouse", "chill", "The Chill-out", "chill", [P("sofa_nook"), P("sofa_front")], [down("chill_door"), down("bar_taps")],
      "chill_door", {"up": "chill_door"}, [("warehouse.exit", "up", "Out through the floor to the door")])
scene("warehouse.booth", "warehouse", "booth", "The Booth", "booth", [P("booth_decks", "dj")], [down("stage", "queasy", "walk", 2), down("steps")],
      "stage_edge", {"up": "booth_down"}, [("warehouse.exit", "up", "Down the stage, out through the floor")])
scene("warehouse.exit", "warehouse", "exit", "The Door", "door", [P("tunnel")], [down("floor_centre"), down("floor_edge")],
      "floor_centre", {"up": "tunnel", "right": "door_r"},
      [("mothership", "up", "The lights go strange"), ("underworld", "right", "The floor cracks open")], exit_scene=True)

# --- the Mothership ---------------------------------------------------------------------------------------------------------------------------
scene("mothership", "mothership", "deck", "The Deck", "deck_centre", [P("deck_ramp"), up("deck_dais", 3)], [down("deck_edge"), down("deck_sw_corner")],
      "deck_gallery_door", {"right": "deck_gallery_door", "up": "deck_reactor_door"},
      [("mothership.gallery", "right", "Along the gallery of windows"), ("mothership.reactor", "up", "Past the gallery to the reactor catwalk")], entry=True)
scene("mothership.gallery", "mothership", "gallery", "The Gallery", "gallery_in", [P("gallery_mid"), P("planet_window")], [down("gallery_west"), down("deck_edge")],
      "gallery_door", {"up": "gallery_east"}, [("mothership.bridge", "up", "On to the bridge")])
scene("mothership.reactor", "mothership", "reactor", "The Reactor", "reactor_in", [P("catwalk_mid"), up("reactor_core", 4)], [down("catwalk_door"), down("medbay")],
      "catwalk_door", {"up": "catwalk_bridge"}, [("mothership.bridge", "up", "Across the catwalk to the bridge")])
scene("mothership.bridge", "mothership", "bridge", "The Bridge", "bridge_in", [P("helm_edge"), P("helm", "on_stage")], [down("bridge_door"), down("catwalk_bridge")],
      "bridge_door", {"up": "bridge_door"}, [("mothership.exit", "up", "Back along the catwalk to the medbay")])
scene("mothership.exit", "mothership", "exit", "The Airlock", "medbay", [P("airlock_door"), P("airlock")], [down("exam"), down("med_alcove_in")],
      "med_door", {"left": "airlock_door", "right": "exam_door"},
      [("hospital", "left", "Out of the airlock, into white light"), ("ward", "right", "Through the exam room door")], exit_scene=True)

# --- the Underworld ------------------------------------------------------------------------------------------------------------------------
scene("underworld", "underworld", "arena", "The Arena", "arena_floor", [P("arena_gate"), up("gate_dais", 3)], [down("arena_edge"), down("tier_l_in")],
      "arena_tier_l", {"right": "arena_tier_r", "left": "arena_tier_l"},
      [("underworld.court", "right", "The east tier, up to the court"), ("underworld.furnace", "left", "The west tier, down to the furnace")], entry=True)
scene("underworld.court", "underworld", "court", "The Court", "court_in", [P("court_mid"), P("throne_steps")], [down("tier_r_in"), down("arena_edge")],
      "court_door", {"up": "court_causeway"}, [("underworld.pit", "up", "The causeway to the pit")])
scene("underworld.furnace", "underworld", "furnace", "The Furnace", "furnace_in", [P("furnace_chains"), P("furnace_mid")], [down("tier_l_in"), down("arena_edge")],
      "furnace_door", {"up": "furnace_out"}, [("underworld.pit", "up", "Back through the arena, over the causeway")])
scene("underworld.pit", "underworld", "pit", "The Pit", "pit_in", [P("pit_edge"), P("pit_stage", "on_stage")], [down("pit_rim_e"), down("court_in")],
      "causeway_in", {"up": "pit_door"}, [("underworld.exit", "up", "Up the causeway to the throne")])
scene("underworld.exit", "underworld", "exit", "The Throne", "throne_steps", [P("throne", "on_stage")], [down("court_mid"), down("court_in")],
      "court_causeway", {"left": "throne_door_l", "right": "throne_door_r"},
      [("hospital", "left", "The north door, into white light"), ("ward", "right", "The south door, into the quiet")], exit_scene=True)

# --- the Hospital ----------------------------------------------------------------------------------------------------------------------------
scene("hospital", "hospital", "ward", "The Ward", "bed", [P("ward_chair"), P("ward_door")], [down("bed_corner"), down("bed_far")],
      "ward_door", {"up": "ward_door"}, [("hospital.corridor", "up", "Out of the ward into the corridor")], entry=True)
scene("hospital.corridor", "hospital", "corridor", "The Corridor", "corridor_in", [P("corridor_mid"), P("corridor_fork")], [down("corridor_quiet_door"), down("quiet", "sick", "run", 3)],
      "corridor_in", {"left": "corridor_day_door", "right": "corridor_cafe"},
      [("hospital.dayroom", "left", "The day room, the television on"), ("hospital.cafeteria", "right", "On to the cafeteria")])
scene("hospital.dayroom", "hospital", "dayroom", "The Day Room", "dayroom", [P("dayroom_mid"), P("day_tv_in")], [down("dayroom_door"), down("corridor_in")],
      "dayroom_door", {"up": "dayroom_door"}, [("hospital.garden", "up", "Down the corridor to the garden")])
scene("hospital.cafeteria", "hospital", "cafeteria", "The Cafeteria", "cafe_in", [P("cafe_mid"), P("cafe_serving")], [down("cafe_door_w"), down("corridor_in")],
      "cafe_door_w", {"up": "cafe_garden_door"}, [("hospital.garden", "up", "Through the glass doors to the garden")])
scene("hospital.garden", "hospital", "garden", "The Garden", "garden_in", [P("garden_edge"), P("bandstand")], [down("garden_south"), down("garden_sw")],
      "garden_door_w", {"up": "garden_door_e"}, [("hospital.exit", "up", "On to the bandstand")])
scene("hospital.exit", "hospital", "exit", "The Bandstand", "bandstand", [P("bandstand_front", "on_stage")], [down("garden_edge"), down("garden_in")],
      "garden_door_e", {"left": "bandstand_door_l", "right": "bandstand_door_r"},
      [("hospital_late", "left", "The garden after dark"), ("ward_late", "right", "Across the lawn, to the stage")], exit_scene=True)

# --- the Ward -----------------------------------------------------------------------------------------------------------------------------------
scene("ward", "ward", "dayroom", "The Day Room", "day_centre", [P("bars_in"), P("day_stage_in")], [down("day_edge"), down("day_corner")],
      "day_door_a", {"right": "day_door_a", "up": "day_door_b"},
      [("ward.art", "right", "Down the corridor to the art room"), ("ward.dorm", "up", "To the dormitory")], entry=True)
scene("ward.art", "ward", "art", "The Art Room", "art_in", [P("art_mid"), P("art_easels")], [down("art_door"), down("corridor_in")],
      "art_door", {"up": "art_door"}, [("ward.corridor", "up", "Back to the corridor")])
scene("ward.dorm", "ward", "dorm", "The Dormitory", "dorm", [P("dorm_mid"), P("dorm_bed")], [down("dorm_door"), down("corridor_in")],
      "dorm_door", {"up": "dorm_door"}, [("ward.corridor", "up", "Out to the corridor")])
scene("ward.corridor", "ward", "corridor", "The Corridor", "corridor_in", [P("corr_mid"), P("corr_east")], [down("treat"), down("quiet", "sick", "run", 3)],
      "corr_west", {"up": "corr_art_door"}, [("ward.courtyard", "up", "Through the art room to the courtyard")])
scene("ward.courtyard", "ward", "courtyard", "The Courtyard", "court_in", [P("court_mid"), P("stage_edge")], [down("court_door_w"), down("art_in")],
      "art_east_door", {"up": "court_stage_door"}, [("ward.exit", "up", "Over to the stage")])
scene("ward.exit", "ward", "exit", "The Stage", "stage_edge", [P("stage", "on_stage")], [down("court_mid"), down("court_in")],
      "court_stage_door", {"left": "stage_door_l", "right": "stage_door_r"},
      [("hospital_late", "left", "Stage left, back to the hospital"), ("ward_late", "right", "Stage right, round again")], exit_scene=True)

# --- the Hospital, late -----------------------------------------------------------------------------------------------------------------
scene("hospital_late", "hospital_late", "garden", "The Garden", "garden_edge", [P("garden_north"), P("garden_in")], [down("garden_south"), down("garden_sw")],
      "garden_door_w", {"left": "garden_door_w", "right": "garden_door_w2"},
      [("hospital_late.cafe", "left", "Back in to the cafeteria"), ("hospital_late.quiet", "right", "Down the corridor to the quiet room")], entry=True)
scene("hospital_late.cafe", "hospital_late", "cafe", "The Cafeteria", "cafe_mid", [P("cafe_serving"), P("cafe_garden_door")], [down("cafe_in"), down("cafe_door_w")],
      "cafe_door_w", {"up": "cafe_garden_door"}, [("hospital_late.exit", "up", "Out to the bandstand")])
scene("hospital_late.quiet", "hospital_late", "quiet", "The Quiet Room", "quiet", [P("quiet_far")], [down("quiet_door"), down("corridor_in")],
      "quiet_door", {"up": "quiet_door"}, [("hospital_late.exit", "up", "Out and across to the bandstand")])
scene("hospital_late.exit", "hospital_late", "exit", "The Bandstand", "bandstand", [P("bandstand_front", "on_stage")], [down("garden_edge"), down("garden_in")],
      "garden_door_e", {"left": "bandstand_door_l", "right": "bandstand_door_r"},
      [("hospital_late", "left", "Round the garden again", True), ("ward_late", "right", "Across the lawn, to the stage")], exit_scene=True)

# --- the Ward, late ------------------------------------------------------------------------------------------------------------------------
scene("ward_late", "ward_late", "courtyard", "The Courtyard", "stage_edge", [P("stage", "on_stage"), P("court_mid")], [down("court_north"), down("court_south")],
      "court_door_w", {"left": "court_door_w", "right": "court_south"},
      [("ward_late.treat", "left", "Back through the art room to treatment"), ("ward_late.dorm", "right", "Back to the dormitory")], entry=True)
scene("ward_late.treat", "ward_late", "treat", "The Treatment Room", "treat", [P("quiet"), P("treat_door")], [down("corr_mid"), down("corr_west")],
      "treat_door", {"up": "treat_door"}, [("ward_late.exit", "up", "Out to the day room")])
scene("ward_late.dorm", "ward_late", "dorm", "The Dormitory", "dorm", [P("dorm_mid"), P("dorm_bed")], [down("dorm_door"), down("corr_mid")],
      "dorm_door", {"up": "dorm_door"}, [("ward_late.exit", "up", "Out to the day room")])
scene("ward_late.exit", "ward_late", "exit", "The Day Room", "day_edge", [P("day_centre"), P("day_stage_in")], [down("day_corner"), down("bars_in")],
      "day_door_a", {"right": "day_door_a", "left": "day_door_b"},
      [("ward_late", "right", "Round again, out to the courtyard", True), ("hospital_late", "left", "Across to the hospital")], exit_scene=True)

# ---- music: scene -> pack (audio = chart). Underworld scenes are Lv2 renders standing in for Lv3 Hell (temporary). ------------------------------------
PACK = {
    "warehouse": "lv1_warehouse", "warehouse.bar": "lv1_warehouse_v1", "warehouse.balcony": "lv1_warehouse_v2", "warehouse.chill": "lv1_warehouse_v2",
    "warehouse.booth": "lv1_warehouse_v1", "warehouse.exit": "lv1_warehouse",
    "mothership": "lv2_alien_spaceship", "mothership.gallery": "lv2_alien_spaceship_v1", "mothership.reactor": "lv2_alien_spaceship_v3",
    "mothership.bridge": "lv2_alien_spaceship_v2", "mothership.exit": "lv2_alien_spaceship",
    "underworld": "lv2_alien_spaceship_v2", "underworld.court": "lv2_alien_spaceship_v3", "underworld.furnace": "lv2_alien_spaceship_v2",
    "underworld.pit": "lv2_alien_spaceship_v3", "underworld.exit": "lv2_alien_spaceship_v2",
    "hospital": "lv4_hospital", "hospital.corridor": "lv4_hospital_v2", "hospital.dayroom": "lv4_hospital_v3", "hospital.cafeteria": "lv4_hospital_v2",
    "hospital.garden": "lv4_hospital_v3", "hospital.exit": "lv4_hospital",
    "ward": "lv5_asylum", "ward.art": "lv5_asylum_v1", "ward.dorm": "lv5_asylum_v3", "ward.corridor": "lv5_asylum_v1", "ward.courtyard": "lv5_asylum_v3",
    "ward.exit": "lv5_asylum",
    "hospital_late": "lv4_hospital_v1", "hospital_late.cafe": "lv4_hospital_v3", "hospital_late.quiet": "lv4_hospital_v2", "hospital_late.exit": "lv4_hospital_v1",
    "ward_late": "lv5_asylum_v2", "ward_late.treat": "lv5_asylum_v2", "ward_late.dorm": "lv5_asylum_v3", "ward_late.exit": "lv5_asylum_v2",
}
TEMPORARY = {"underworld", "underworld.court", "underworld.furnace", "underworld.pit", "underworld.exit"}


def build_nodes() -> list[dict]:
    wmap = {w["id"]: w for w in WORLDS}
    nodes = []
    for s in S:
        w = wmap[s["world"]]
        gl, st = GL[w["map"]]
        # the sequence of glances and strolls differs a little from scene to scene (rotated by the scene's index in its world)
        k = sum(1 for t in nodes if t["world"] == s["world"])
        rot = lambda lst: lst[k % len(lst):] + lst[:k % len(lst)]  # noqa: E731
        n = {"id": s["id"], "world": s["world"], "scene": s["scene"], "title": s["title"], "entry": s["entry"], "exit_scene": s["exit_scene"], "role": s["role"],
             "blurb": w["blurb"] if s["entry"] else s["title"],
             "next": [{"to": t[0], "dir": t[1], "label": t[2], **({"loop": True} if len(t) > 3 and t[3] else {})} for t in s["next"]],
             "place": {"waypoint": s["home"], "rail": {"good": s["good"], "bad": s["bad"], "arrive": s["arrive"], "glances": rot(gl), "strolls": rot(st), "exits": s["exits"]}}}
        if s["id"] in ("warehouse", "warehouse.chill"):  # the wizard waits on the floor and in the chill-out; the Bassment returns to the entry scene
            n["trial_gate"] = "deathtrap_opening"
        nodes.append(n)
    return nodes


def write_run(nodes: list[dict], cinematics: dict | None = None) -> None:
    run = json.loads(RUN.read_text(encoding="utf-8"))
    out = {}
    for k, v in run.items():
        if k == "nodes":
            out["worlds"] = WORLDS
            out["nodes"] = nodes
            if cinematics is not None:
                out["cinematics"] = cinematics
        elif k not in ("worlds", "cinematics"):
            out[k] = v
    RUN.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def write_music() -> None:
    m = json.loads(MUSIC.read_text(encoding="utf-8"))
    m["note"] = ("Which recordings and chart each SCENE plays (a scene is one 64-beat phase at a place in a world; run.json lists them). audio = the pack whose stems are heard, "
                 "chart = the pack whose cues are played; a scene plays the difficulty tier min(depth, 4) of its chart pack, depth is per world. The entry scene of a world plays "
                 "the world's base set and later scenes its variants; none of the variants has the base set's cues (each is its own chart), so sibling scenes that chart different "
                 "packs fall under the route lock (docs/CONTINUOUS_RUN.md). treatment = a name from run.json treatments. temporary = true for stand-ins awaiting the owner's own "
                 "recordings (the Underworld plays Lv2 Alien Spaceship renders until Lv3 Hell has MIDI). Scene ids are tools/run/make_scenes.py's PACK table; world ids never change.")
    m["nodes"] = [{"id": s["id"], "audio": PACK[s["id"]], "chart": PACK[s["id"]], "treatment": "none", "temporary": s["id"] in TEMPORARY} for s in S]
    MUSIC.write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def _inside(pt, poly, margin):
    """Point in polygon with a margin from every edge."""
    x, z = pt
    ins = False
    n = len(poly)
    for i in range(n):
        (x1, z1), (x2, z2) = poly[i], poly[(i + 1) % n]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1:
            ins = not ins
        dx, dz = x2 - x1, z2 - z1
        t = max(0.0, min(1.0, ((x - x1) * dx + (z - z1) * dz) / (dx * dx + dz * dz))) if dx or dz else 0.0
        if ((x - (x1 + t * dx)) ** 2 + (z - (z1 + t * dz)) ** 2) ** 0.5 < margin:
            return False
    return ins


def _nudge(at, sector, doc, others):
    """The nearest point to `at` inside its sector, clear of every crowd home (the map test wants a metre) and of the waypoints placed so far."""
    poly = next(sc["polygon"] for sc in doc["sectors"] if sc["id"] == sector)
    homes = [tuple(h["at"]) for h in doc.get("homes", [])]
    pts = [(0.0, 0.0)] + sorted(((i * 0.25, j * 0.25) for i in range(-12, 13) for j in range(-12, 13) if i or j), key=lambda d: d[0] ** 2 + d[1] ** 2)
    for dx, dz in pts:
        c = (round(at[0] + dx, 2), round(at[1] + dz, 2))
        if not _inside(c, poly, 0.35):
            continue
        if all(((c[0] - h[0]) ** 2 + (c[1] - h[1]) ** 2) ** 0.5 >= 1.1 for h in homes) and all(((c[0] - o[0]) ** 2 + (c[1] - o[1]) ** 2) ** 0.5 >= 0.8 for o in others):
            return c
    raise SystemExit("no clear spot near %s in %s" % (at, sector))


def add_waypoints() -> None:
    for mp, rows in NEW_WAYPOINTS.items():
        path = MAPS / f"{mp}.json"
        txt = path.read_text(encoding="utf-8")
        have = set(re.findall(r'\{"id": "([^"]+)", "at": \[[^\]]+\], "yaw": [-\d.]+, "sector": "[^"]+"\}', txt))
        m = re.search(r'("waypoints": \[\n)(.*?)(\n \],)', txt, re.S)
        assert m, mp
        lines = []
        doc = json.loads(txt)
        placed = [tuple(w["at"]) for w in doc["waypoints"]]
        for wid, at, yaw, sector in rows:
            if wid in have:
                continue
            at = _nudge(at, sector, doc, placed)
            placed.append(at)
            lines.append('  {"id": "%s", "at": [%g, %g], "yaw": %g, "sector": "%s"}' % (wid, at[0], at[1], yaw, sector))
        if lines:
            body = m.group(2) + ",\n" + ",\n".join(lines)
            txt = txt[:m.start(2)] + body + txt[m.end(2):]
            path.write_text(txt, encoding="utf-8", newline="\n")
        print(mp, "+%d waypoints" % len(lines))


def add_things() -> None:
    """New billboards and lights (NEW_THINGS, NEW_LIGHTS) go in as one line each at the end of the map's things; the sprites they name join the map's textures."""
    for mp in sorted(set(NEW_THINGS) | set(NEW_LIGHTS)):
        path = MAPS / f"{mp}.json"
        txt = path.read_text(encoding="utf-8")
        doc = json.loads(txt)
        have = {x["id"] for x in doc["things"]}
        lines = []
        for tid, sprite, at, y, size, anim in NEW_THINGS.get(mp, []):
            if tid not in have:
                lines.append('  {"id": "%s", "kind": "billboard", "sprite": "%s", "at": [%g, %g], "y": %g, "size": %g, "anim": "%s"}' % (tid, sprite, at[0], at[1], y, size, anim))
        for tid, at, y, radius, color, strength in NEW_LIGHTS.get(mp, []):
            if tid not in have:
                lines.append('  {"id": "%s", "kind": "light", "at": [%g, %g], "y": %g, "radius": %g, "color": "%s", "strength": %g}' % (tid, at[0], at[1], y, radius, color, strength))
        if lines:
            m = re.search(r'("things": \[\n)(.*?)(\n \],)', txt, re.S)
            assert m, mp
            txt = txt[:m.start(2)] + m.group(2) + ",\n" + ",\n".join(lines) + txt[m.end(2):]
        for tid, sprite, *_ in NEW_THINGS.get(mp, []):
            if sprite not in doc["textures"]:
                m = re.search(r'("textures": \{\n)(.*?)(\n \},)', txt, re.S)
                assert m, mp
                txt = txt[:m.start(2)] + m.group(2) + ',\n  "%s": "textures/%s.png"' % (sprite, sprite) + txt[m.end(2):]
                doc["textures"][sprite] = 1
        path.write_text(txt, encoding="utf-8", newline="\n")
        print(mp, "+%d things" % len(lines))


def main() -> None:
    nodes = build_nodes()
    add_waypoints()
    add_things()
    write_run(nodes)
    write_music()
    # the hotspot tables read the scenes just written (exits and doorways) and own the named cinematics (rail actions to waypoints) that go into run.json
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import make_hotspots
    write_run(nodes, make_hotspots.CINEMATICS)
    make_hotspots.write()
    print("%d scenes in %d worlds, %d cinematics" % (len(nodes), len(WORLDS), len(make_hotspots.CINEMATICS)))


if __name__ == "__main__":
    main()
