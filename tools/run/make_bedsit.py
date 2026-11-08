#!/usr/bin/env python3
"""Writes the bedsit opening as a path: content/paths/bedsit/{run.json, music.json, hotspots/bedsit.json} and content/bedsit/{themes.json, routes.json}
(docs/briefs/BEDSIT_RAVES_BRIEF.md section 2, contracts 1, 2, 6 and 9, ruling 37: the opening is its own path, content/paths/bedsit).

    python3 tools/run/make_bedsit.py            # idempotent; then: python3 tools/content/make_path_placeholders.py bedsit   (the 174 BPM stand-in pack bedsit_room)

THE FLAG. The path is only ever started on request, so the legacy campaign is untouched by default:
    RW_BEDSIT=1                 starts the bedsit path instead of the main run (src/run/run_play.gd, one line; RW_RUN_PATH=<id> still wins)
    RW_RUN_PATH=bedsit          the existing way to start any path (what tools/dev/play_bedsit.cmd also sets)
    python3 tools/run/make_bedsit.py --bedsit    the same switch for this generator: without it, nothing is written (a stray run of the tool never adds the path)
Default off in every case.

THE DATA FOR THE ENGINE HOOKS (built on another branch; today's engine ignores them and says so in docs/bedsit/LAUNCH.md):
    node.relaxed = true                       H1.7: the node never drains energy or forces a departure
    node.bedsit.viewpoint.hold_bars = 4       H3.1: the choice viewpoint holds still for the whole window (one block)
    node.bedsit.viewpoint.choice_view = true  (the four waypoints bedsit_n/e/s/w carry choice_view too, in content/story/maps/bedsit.json)
    node.bedsit.regions                       contract 5: the four screen regions are not the pads: left/right turn, bottom stays, top leaves

THE PLACEHOLDER RAVES. The four rave scenes do not exist yet. Each facing's forward route (content/bedsit/routes.json) names the rave's scene id (space_rave, magic_rave,
dino_rave, transport_rave) and, while "placeholder.active" is true, those four ids are PLACEHOLDER nodes of this path that are one-scene endings (route "run:warehouse").
To land a real rave: in content/bedsit/routes.json set "placeholder.active" to false and replace the placeholder node of that id in content/paths/bedsit/run.json (generated here:
tools/run/make_bedsit.py, the PLACEHOLDER_RAVES table) by the real scene, or route to it with `{"path": "<rave path>", "node": "<scene id>"}` through the TransitionPort.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH_DIR = ROOT / "content" / "paths" / "bedsit"
BEDSIT_DIR = ROOT / "content" / "bedsit"
TRACK_ID = "origin_unknown_valley_of_the_shadows_chase_status_remix"

FACINGS = ["N", "E", "S", "W"]
# facing -> (theme, rave scene id, waypoint, threshold waypoint, yaw, what the wall shows)
FACING = {
    "N": ("space", "space_rave", "bedsit_n", "threshold_n", 0, "the window onto the night sky, a glow behind the rooftops, a model rocket on the sill, a star mobile"),
    "E": ("dinos", "dino_rave", "bedsit_e", "threshold_e", -90, "a jungle poster whose middle has become a real opening, a plastic dinosaur on the desk, a fern"),
    "S": ("magic", "magic_rave", "bedsit_s", "threshold_s", 180, "the wardrobe door ajar with iridescent light leaking out, a unicorn figure on the shelf, fairy lights"),
    "W": ("transport", "transport_rave", "bedsit_w", "threshold_w", 90, "the door with a bus timetable pinned to it, a toy car, a blinking indicator light, orange street light under the door"),
}
LANDED = {"space_rave": "N", "magic_rave": "S", "dino_rave": "E", "transport_rave": "W"}  # raves that exist as real nodes (src/bedsit/space_rave_host.gd, tools/story/build_<theme>_rave.py)
PLACEHOLDER_RAVES = {FACING[f][1]: f for f in FACINGS if FACING[f][1] not in LANDED}  # scene id -> facing it leaves from (resolve to the bedsit)
# the raves that are real worlds: theme -> (scene id prefix, title, world blurb, hub blurb, stage blurb, race station title, race hub label, cloakroom blurb, bar blurb, race blurb)
RAVES = {
    "space": ("space", "The Space Rave", "The Mothership's ring round a void: a stage, a cloakroom, a bar and a hangar.",
              "The Mothership's ring round a void. A DJ waves from the stage; the cloakroom, the bar and the hangar are across the ring.",
              "The dais at the north of the ring: two steps up to the DJ deck. The bass knob is stuck.", "Hangar", "The hangar: a race",
              "The coat check in the ring's west alcove: a counter, a rail of coats and an attendant who wants the right coat for each symbol.",
              "The bar in the ring's east alcove: a counter, a back shelf of glasses and a bartender who remembers the drinks.",
              "The hangar in the ring's south-west alcove: a hover racer and its pilot. Touch the racer: the street race through the city outside (docs/bedsit/RACE.md)."),
    "magic": ("magic", "The Magic Rave", "An octagonal lounge of stepped tiers round a sunken dance well: a stage, a cloakroom, a bar and a carriage house.",
              "An enchanted lounge: stepped rings of moss and velvet going down to a sunken dance well. A unicorn DJ waves from the stage; the cloakroom, the bar and the carriage house are round the walls.",
              "The dais at the north of the lounge: two steps up to the DJ deck. The bass knob is stuck.", "Carriage house", "The carriage house: a race",
              "The coat check in the lounge's north-west alcove: a counter, a rail of capes and an attendant who wants the right cape for each symbol.",
              "The bar in the lounge's north-east alcove: a cauldron counter, a back shelf of potions and a bartender who remembers the drinks.",
              "The carriage house off the lounge's south side: an enchanted racer and its pilot. Touch the racer: the street race through the city outside (docs/bedsit/RACE.md)."),
    "dinos": ("dino", "The Dinosaur Rave", "A basalt ledge over a lava gulf, a causeway to the stage and two islands: a stage, a cloakroom, a bar and a ranger garage.",
              "A rave over the lava: a basalt ledge, a long railed causeway to the stage and two islands off it. A dinosaur DJ waves from the stage; the cloakroom cave, the tent bar and the ranger garage are across the lava.",
              "The dais at the end of the causeway: two steps up to the DJ deck under a ribcage arch. The bass knob is stuck.", "Ranger garage", "The ranger garage: a race",
              "The coat check in a cave on the west island: a stone desk, a rack of hides and an attendant who wants the right hide for each symbol.",
              "The bar in a tent on the east island: a log counter, a shelf of jars and a bartender who remembers the drinks.",
              "The ranger garage off the ledge: an off-road racer and its pilot. Touch the racer: the street race through the city outside (docs/bedsit/RACE.md)."),
    "transport": ("transport", "The Transport Rave", "A wet street forecourt, a pair of tracks and a depot hall: a stage, a cloakroom, a bar and a garage.",
              "A rave in a railway depot off a wet street: across the tracks the hall opens under its roof. A DJ waves from the loading dock; the left-luggage bay, the ticket-office bar and the garage are round the hall.",
              "The loading dock at the north of the hall: two steps up to the DJ deck under a locomotive's face. The bass knob is stuck.", "Garage", "The garage: a race",
              "The coat check in the left-luggage bay off the hall's west wall: a desk, a rail of hi-vis vests and an attendant who wants the right vest for each symbol.",
              "The bar in the ticket office off the hall's east wall: a ticket counter, a shelf of lockers and a bartender who remembers the drinks.",
              "The garage beside the stage: a rally hatchback and its pilot. Touch the racer: the street race through the city outside (docs/bedsit/RACE.md)."),
}
ORDER = ["space", "magic", "dinos", "transport"]  # the order the raves' nodes are written in
# WAY_OUT. A path must end somewhere (tests/test_run_matrix.gd); while a rave was a placeholder its one-scene ending was that end. With all four landed, the bedsit's way out to the
# Warehouse (bedsit.end, the development exit's scene) opens once the player has come home from every rave this run: each rave's routes home set the run flag BEEN % theme.
BEEN = "bedsit_been_%s"


def stations(theme: str) -> dict:
    """activity scene -> (title, home waypoint, doorway waypoint, activity id in content/raves/<theme>.json "activities")."""
    p = RAVES[theme][0]
    return {"%s_cloakroom" % p: ("Cloakroom", "cloak_view", "cloak_door", "cloakroom"), "%s_bar" % p: ("Bar", "bar_view", "bar_door", "bar"), "%s_race" % p: (RAVES[theme][5], "hangar_view", "hangar_door", "race")}


def activity_scenes(theme: str) -> dict:
    """The stations that are real scenes (ruling 38, contract 10): scene id -> (scene name, hold waypoint the activity is played from, the thing the hotspot is anchored on, minigame id, blurb)."""
    p, r = RAVES[theme][0], RAVES[theme]
    scenes = {"%s_cloakroom" % p: ("cloakroom", "cloak_hold", "cloak_counter", "cloakroom", r[7]), "%s_bar" % p: ("bar", "bar_hold", "bar_counter", "bar", r[8])}
    if (ROOT / "content" / "races" / ("%s.json" % theme)).exists():  # the race is a real scene once the theme has its race data (content/races/<theme>.json, docs/bedsit/RACE.md); until then a placeholder
        scenes["%s_race" % p] = ("hangar", "hangar_view", "hangar_racer", "race", r[9])
    return scenes


REPLAYABLE = ["race"]  # activities whose hotspot stays after completion (the race may be run again; its record is the save's raves.<theme>.race)


def place(home: str) -> dict:
    """The rail of every bedsit scene: one place, the home viewpoint; glances and strolls of zero (the camera holds still, ruling 35)."""
    return {
        "waypoint": home,
        "rail": {
            "good": [{"to": home, "role": "dancer", "style": "walk", "bars": 2}],
            "bad": [{"to": home, "role": "dancer", "style": "walk", "bars": 2}],
            "arrive": home,
            "glances": [{"by": 0, "pitch": 0, "bars": 2}],
            "strolls": [{"fwd": 0.0, "bars": 2}],
            "exits": {"n": "threshold_n", "e": "threshold_e", "s": "threshold_s", "w": "threshold_w", "up": FACING["N"][3], "out": "threshold_s"},
        },
    }


def srail(home: str, good: list, exits: dict, arrive: str = "") -> dict:
    # (a setback place is the scene's own last place, holds included: the rooms are relaxed, a slip does not move the camera, and a rail that is back on its good place later in the phase
    # has no late walk to shorten against the next choice window)
    bad = dict(good[-1]) if home != "" and good and float(good[-1].get("hold_bars", 0.0)) > 0.0 else {"to": home, "role": "dancer", "style": "walk", "bars": 2}
    if bad.get("choice"):
        bad = dict(bad, bars=max(2, min(4, int(bad["bars"]))))
    r = {"good": good, "bad": [bad], "glances": [{"by": 0, "pitch": 0, "bars": 2}], "strolls": [{"fwd": 0.0, "bars": 2}], "exits": exits}
    if arrive:
        r["arrive"] = arrive
    return r


def rave_nodes(theme: str) -> list:
    """A rave (content/story/maps/<prefix>_rave.json): the hub (a choice viewpoint holding 8 bars: the stage, the cloakroom, the bar, the race entrance and the way home), the stage (the deck with the
    bass knob), the cloakroom and the bar (real scenes, ruling 38) and a placeholder node for the race (the race agent builds it: the activity id is in content/raves/<theme>.json `activities`)."""
    pre, title, _wb, hub_blurb, stage_blurb, race_title, race_label, _cb, _bb, _rb = RAVES[theme]
    world = "%s_rave" % pre
    base = {"world": world, "role": "dancer", "relaxed": True, "treatment": "none"}
    hub_next = [{"to": "bedsit", "dir": "up", "label": "Home through the %s" % ("airlock" if theme == "space" else "door")}, {"to": "%s_stage" % pre, "dir": "n", "label": "Up to the stage"},
                {"to": "%s_cloakroom" % pre, "dir": "w", "label": "The cloakroom"}, {"to": "%s_bar" % pre, "dir": "e", "label": "The bar"}, {"to": "%s_race" % pre, "dir": "s", "label": race_label}]
    hub = dict(base, id=world, scene="hub", title=title, entry=True, exit_scene=True, blurb=hub_blurb, next=hub_next, theme=theme,
               place={"waypoint": "hub_view", "rail": srail("hub_view", [{"to": "hub_view", "role": "dancer", "style": "walk", "bars": 3, "choice": True, "hold_bars": 8}],
                                                              {"n": "stage_foot", "w": "cloak_door", "e": "bar_door", "s": "hangar_door", "up": "home_door"}, arrive="%s_arrive" % pre)})
    back = "Back to the ring" if theme == "space" else "Back to the rave"
    stage = dict(base, id="%s_stage" % pre, scene="stage", title="The Stage", entry=False, exit_scene=True, blurb=stage_blurb,
                 next=[{"to": world, "dir": "up", "label": back, "loop": True}, {"to": "bedsit", "dir": "out", "label": "Home"}], theme=theme,
                 place={"waypoint": "stage_foot", "rail": srail("stage_foot", [
                     {"to": "stage_steps", "role": "dancer", "style": "walk", "bars": 2, "hold_bars": 1},
                     {"to": "deck_view", "role": "on_stage", "style": "walk", "bars": 2, "hold_bars": 4}], {"up": "stage_foot", "out": "stage_foot"})})
    out = [hub, stage]
    scenes = activity_scenes(theme)
    for sid, (stitle, home, door, act_id) in stations(theme).items():
        if sid in scenes:  # a real scene: the route from the hub ends at a hold facing the counter (contract 10's camera: hold_bars for the activity)
            scene, hold, thing, mg, blurb = scenes[sid]
            out.append(dict(base, id=sid, scene=scene, title=stitle, entry=False, exit_scene=True, blurb=blurb, theme=theme, activity=mg,
                            next=[{"to": world, "dir": "up", "label": back, "loop": True}, {"to": "bedsit", "dir": "out", "label": "Home"}],
                            place={"waypoint": door, "rail": srail(door, [{"to": hold, "role": "dancer", "style": "walk", "bars": 2, "hold_bars": 10}], {"up": door, "out": door})}))
            continue
        out.append(dict(base, id=sid, scene=sid, title="PLACEHOLDER: " + stitle, entry=False, exit_scene=True, placeholder=True, placeholder_for={"theme": theme, "activity": act_id}, theme=theme,
                        blurb="A stand-in for the %s activity (id '%s' in content/raves/%s.json activities), built elsewhere as a minigame. It loops back to the %s." % (stitle.lower(), act_id, theme, "ring" if theme == "space" else "rave"),
                        next=[{"to": world, "dir": "up", "label": back, "loop": True}, {"to": "bedsit", "dir": "out", "label": "Home"}],
                        place={"waypoint": home, "rail": srail(home, [{"to": home, "role": "dancer", "style": "walk", "bars": 2}], {"up": door, "out": door})}))
    return out


def run_json() -> dict:
    main_timing = {"bpm": 174, "phase_beats": 64, "block_beats": 16, "cue_span_beats": 12.0, "decision_beat": 12.5, "fade_beats": 2.0}
    nodes = []
    bedsit_next = [{"to": FACING[f][1], "dir": f.lower(), "label": "Through the %s wall" % {"N": "north", "E": "east", "S": "south", "W": "west"}[f]} for f in FACINGS]
    bedsit_next.append({"to": "bedsit.end", "dir": "out", "label": "Out of the bedsit (development exit to the Warehouse)"})
    bedsit_node = {
        "id": "bedsit", "world": "bedsit", "scene": "room", "title": "The Bedsit", "entry": True, "exit_scene": True, "role": "dancer",
        "relaxed": True,  # H1.7 (engine hook, not built on this branch): the bedsit never drains energy or forces departure
        "blurb": "Your room. Four walls, four ways out: the window, the desk, the wardrobe, the door.",
        "next": bedsit_next,
        "bedsit": {
            "state_key": "bedsit_facing", "start_facing": "N", "themes": "res://content/bedsit/themes.json", "routes": "res://content/bedsit/routes.json",
            "viewpoint": {"waypoint": "bedsit_n", "choice_view": True, "hold_bars": 4, "turn_bars": 1},  # H3.1: hold_bars is the choice window (one block); the turn takes one bar and holds
            "regions": {  # contract 5 / brief 2: these four areas are NOT the pads
                "left": {"action": "turn", "dir": -1, "label": "turn 90 degrees left"},
                "right": {"action": "turn", "dir": 1, "label": "turn 90 degrees right"},
                "bottom": {"action": "stay", "dir": 0, "label": "stay facing the same way"},
                "top": {"action": "leave", "label": "leave for the rave of the current facing"},
            },
            "facings": {f: {"yaw": FACING[f][4], "waypoint": FACING[f][2], "threshold": FACING[f][3], "theme": FACING[f][0], "route": FACING[f][1], "shows": FACING[f][5]} for f in FACINGS},
        },
        "place": place("bedsit_n"),
    }
    nodes.append(bedsit_node)
    for scene_id, f in PLACEHOLDER_RAVES.items():
        theme = FACING[f][0]
        nodes.append({
            "id": scene_id, "world": "bedsit", "scene": scene_id, "title": "PLACEHOLDER: the %s rave" % theme, "entry": False, "exit_scene": False, "role": "dancer",
            "placeholder": True, "placeholder_for": {"theme": theme, "facing": f}, "ending": theme + "_placeholder",
            "blurb": "A stand-in for the %s rave, which does not exist yet: a one-scene ending that returns to the Warehouse. See content/bedsit/routes.json." % theme,
            "next": [{"to": "run:warehouse", "dir": "up", "label": "Back to the Warehouse"}],
            "place": {"waypoint": FACING[f][2], "rail": {**place(FACING[f][2])["rail"], "exits": {"up": FACING[f][3]}}},
        })
    for theme in ORDER:
        nodes.extend(rave_nodes(theme))
    nodes.append({
        "id": "bedsit.end", "world": "bedsit", "scene": "end", "title": "Out of the bedsit", "entry": False, "exit_scene": False, "ending": "leave", "role": "dancer",
        "blurb": "The development way out: back to the Warehouse.",
        "next": [{"to": "run:warehouse", "dir": "up", "label": "Back to the Warehouse"}],
        "place": {"waypoint": "bedsit_s", "rail": {**place("bedsit_s")["rail"], "exits": {"up": "threshold_s"}}},
    })
    return {
        "schema": 1,
        "path": {"id": "bedsit", "title": "The Bedsit", "entry_from": "bedsit.start", "returns_to": "warehouse", "dev": True,
                 "opens": "The new opening (docs/briefs/BEDSIT_RAVES_BRIEF.md section 2): a bedsit seen in four directions. Started with RW_BEDSIT=1 or RW_RUN_PATH=bedsit; tools/dev/play_bedsit.cmd."},
        "timing": main_timing,
        "start_node": "bedsit",
        "worlds": [{"id": "bedsit", "title": "The Bedsit", "map": "bedsit", "story": "res://content/story/bedsit.json", "depth": 1, "blurb": "One room, four walls, four raves."}] +
                  [{"id": "%s_rave" % RAVES[t][0], "title": RAVES[t][1], "map": "%s_rave" % RAVES[t][0], "story": "res://content/story/%s_rave.json" % RAVES[t][0], "depth": 2, "blurb": RAVES[t][2]} for t in ORDER],
        "nodes": nodes,
        "cinematics": {},
    }


def hotspot_row(hid: str, scene: str, anchor: dict, route: str, default: bool, available: dict | None = None, kind: str = "exit") -> dict:
    return {
        "id": hid, "world": "bedsit", "scene": scene, "map": "bedsit", "anchor": anchor, "kind": kind, "radius_m": 1.0, "min_px": 88,
        "available": available or {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
        "look": {"available": "open", "selected": "ring", "committed": "flash"},
        "challenge": None, "on_success": {"route": route}, "on_failure": {"route": route}, "default": default, "repeatable": True,
    }


def hotspots_json() -> dict:
    rows = []
    for f in FACINGS:
        theme, scene_id, home, thr, yaw, _ = FACING[f]
        rows.append(hotspot_row("bedsit.threshold_" + f.lower(), "bedsit", {"waypoint": thr}, scene_id, f == "N"))
    rows.append(hotspot_row("bedsit.dev_exit", "bedsit", {"waypoint": "threshold_s"}, "bedsit.end", False,
                            {"flags_all": ["bedsit_dev_exit"], "flags_none": [], "energy_min": 0, "once": False}))
    if not PLACEHOLDER_RAVES:  # every rave has landed, so no placeholder ending is left: the way out to the Warehouse opens once the player has come home from all four (WAY_OUT)
        rows.append(hotspot_row("bedsit.way_out", "bedsit", {"waypoint": "threshold_s"}, "bedsit.end", False,
                                {"flags_all": [BEEN % FACING[f][0] for f in FACINGS], "flags_none": [], "energy_min": 0, "once": False}))
    for scene_id, f in PLACEHOLDER_RAVES.items():
        ph = hotspot_row("%s.back" % scene_id, scene_id, {"waypoint": FACING[f][3]}, "run:warehouse", True)
        flag = ["keep:path_bedsit_%s_placeholder" % FACING[f][0]]
        ph["on_success"]["flags_set"] = flag
        ph["on_failure"]["flags_set"] = flag
        rows.append(ph)
        obj = hotspot_row("%s.look" % scene_id, scene_id, {"thing": "w_car"}, "", False, kind="object")
        obj["on_success"] = {"flags_set": ["bedsit_placeholder_looked"], "energy": 4}
        obj["on_failure"] = {"energy": -2}
        obj["look"] = {"available": "glow", "selected": "ring", "committed": "flash"}
        rows.append(obj)
    end = hotspot_row("bedsit.end.exit", "bedsit.end", {"waypoint": "threshold_s"}, "run:warehouse", True)
    end["on_success"]["flags_set"] = ["keep:path_bedsit_leave"]
    end["on_failure"]["flags_set"] = ["keep:path_bedsit_leave"]
    rows.append(end)
    mirror = hotspot_row("bedsit.end.mirror", "bedsit.end", {"thing": "w_car"}, "", False, kind="object")
    mirror["on_success"] = {"flags_set": ["bedsit_end_looked"], "energy": 4}
    mirror["on_failure"] = {"energy": -2}
    mirror["look"] = {"available": "glow", "selected": "ring", "committed": "flash"}
    rows.append(mirror)
    return {"world": "bedsit", "hotspots": rows}


def rave_hotspots(theme: str) -> list:
    pre = RAVES[theme][0]
    world = "%s_rave" % pre

    def row(hid, scene, anchor, kind, route="", default=False, acting=None, available=None, window="final", success=None):
        h = {"id": hid, "world": world, "scene": scene, "map": world, "anchor": anchor, "kind": kind, "radius_m": 1.2, "min_px": 88,
             "available": available or {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
             "look": {"available": "beckon", "selected": "ring", "committed": "flash"}, "challenge": None,
             "on_success": success if success is not None else {"route": route}, "on_failure": {"route": route} if route else {}, "default": default, "repeatable": True}
        if window != "final":
            h["window"] = window
        if acting:
            h["acting"] = acting
        return h

    def act(a, face="happy"):
        return {"available": {"act": a, "face": face, "look_at": "camera"}, "selected": {"act": "nod", "face": face, "look_at": "camera"},
                "committed": {"act": "point", "face": face, "look_at": "camera", "beats": 1}}

    rows = [row("%s.stage" % world, world, {"actor": "dj"}, "character", "%s_stage" % pre, acting=act("wave")),
            row("%s.cloakroom" % world, world, {"actor": "attendant"}, "character", "%s_cloakroom" % pre, acting=act("beckon")),
            row("%s.bar" % world, world, {"actor": "bartender"}, "character", "%s_bar" % pre, acting=act("beckon")),
            row("%s.race" % world, world, {"actor": "pilot"}, "character", "%s_race" % pre, acting=act("beckon")),
            row("%s.home" % world, world, {"thing": "home_hatch"}, "exit", "bedsit", default=True)]
    rows.append(row("%s_stage.deck" % pre, "%s_stage" % pre, {"thing": "deck"}, "object", window="any", success={"activity": "bass_knob"},
                    available={"flags_all": [], "flags_none": ["%s_bass_fixed" % theme], "energy_min": 0, "once": False}))
    rows.append(row("%s_stage.home" % pre, "%s_stage" % pre, {"waypoint": "stage_foot"}, "exit", "bedsit"))  # (an exit is staged as a door at its anchor: behind the camera at the deck, never over the deck)
    rows.append(row("%s_stage.back" % pre, "%s_stage" % pre, {"waypoint": "stage_foot"}, "exit", world, default=True))
    scenes = activity_scenes(theme)
    for sid, (title, home, door, act_id) in stations(theme).items():
        if sid in scenes:  # the activity's hotspot: the counter, an object whose success outcome is {activity: id} (content/bedsit/cloakroom_hotspot_example.json); any window seats it at the end of the block
            scene, hold, thing, mg, blurb = scenes[sid]
            h = row("%s.%s" % (sid, mg), sid, {"thing": thing}, "object", window="any", success={"activity": mg},
                    available={"flags_all": [], "flags_none": [] if mg in REPLAYABLE else ["%s_%s_done" % (theme, mg)], "energy_min": 0, "once": False})
            h["radius_m"] = 2.4
            h["min_px"] = 220
            rows.append(h)
        rows.append(row("%s.back" % sid, sid, {"waypoint": door}, "exit", world, default=True))
        rows.append(row("%s.home" % sid, sid, {"waypoint": door}, "exit", "bedsit"))  # (the door is behind the camera at the hold: a door staged at the station's view point stood in front of the counter)
    for h in rows:  # going home from this rave marks it as been to (the bedsit's way out opens once all four have been: hotspots_json, WAY_OUT)
        for k in ("on_success", "on_failure"):
            if h[k].get("route") == "bedsit":
                h[k]["flags_set"] = [BEEN % theme]
    return rows


def themes_json() -> dict:
    return {
        "version": 1, "scene_id": "bedsit", "map": "bedsit", "start_facing": "N",
        "facings": {f: FACING[f][0] for f in FACINGS},
        "facing_waypoints": {f: FACING[f][2] for f in FACINGS},
        "thresholds": {f: FACING[f][3] for f in FACINGS},
        "turn_beats": 2.0,
        "regions": {"top": [0.25, 0.0, 0.5, 0.42], "bottom": [0.25, 0.72, 0.5, 0.28], "left": [0.0, 0.0, 0.22, 1.0], "right": [0.78, 0.0, 0.22, 1.0]},
        "themes": {t: "res://content/raves/%s.json" % t for t in ("space", "magic", "dinos", "transport")},
    }


KEPT_THEME_BLOCKS = ("cloakroom", "bar")  # authored by the activity packages, not generated here: a regeneration keeps them (and any other top-level key it does not write)


def merge_themes(fresh: dict, existing_path: Path) -> dict:
    """The generated themes.json, with every block the generator does not own taken over from the file on disk (the `cloakroom` and `bar` blocks: per-theme looks, symbols, ingredients, layouts)."""
    if not existing_path.exists():
        return fresh
    old = json.loads(existing_path.read_text(encoding="utf-8"))
    for k, v in old.items():
        if k in KEPT_THEME_BLOCKS or k not in fresh:
            fresh[k] = v
    return fresh


def routes_json() -> dict:
    return {
        "version": 1,
        "note": "Where the top region goes, per facing (brief 2). `scene` is the rave's scene id. While placeholder.active is true each of those ids is a PLACEHOLDER node of content/paths/bedsit/run.json that resolves to the bedsit itself. "
                "TO LAND THE REAL RAVES: set placeholder.active to false here, and delete the four nodes with \"placeholder\": true from run.json (or regenerate it from tools/run/make_bedsit.py after replacing PLACEHOLDER_RAVES).",
        "placeholder": {"active": True, "resolves_to": "run:warehouse", "node_flag": "placeholder"},
        "landed": {FACING[f][1]: LANDED.get(FACING[f][1]) == f for f in FACINGS},
        "routes": {f: {"theme": FACING[f][0], "scene": FACING[f][1], "scene_contract_id": "rave." + FACING[f][0], "threshold": FACING[f][3]} for f in FACINGS},
    }


def music_json() -> dict:
    nodes = [{"id": "bedsit", "audio": "bedsit_room", "chart": "bedsit_room", "treatment": "none", "temporary": True,
              "track": TRACK_ID, "note": "the scene plays the Chase & Status remix of Valley of the Shadows (content/run/track_scenes.json paths.bedsit); bedsit_room is the 174 BPM placeholder pack used when the track pack is not on this machine"}]
    for scene_id in PLACEHOLDER_RAVES:
        nodes.append({"id": scene_id, "audio": "bedsit_room", "chart": "bedsit_room", "treatment": "none", "temporary": False})
    nodes.append({"id": "bedsit.end", "audio": "bedsit_room", "chart": "bedsit_room", "treatment": "none", "temporary": False})
    return {"schema": 1, "note": "Every bedsit scene plays one pack, bedsit_room (a synthesised 174 BPM stand-in, tools/content/make_path_placeholders.py bedsit). The real music is the track scene: content/run/track_scenes.json paths.bedsit.",
            "placeholder": {"genre": "dubstep", "key": 45, "levels_db": {"drums": -20.0, "bass": -13.0, "other": -27.0}, "sub_hz": 90.0, "sub_share_min": 0.4, "bass_over_pad_db_min": 8.0},
            "nodes": nodes}


def story_json() -> dict:
    """The story data of the bedsit world (what RunPlay builds the stage from): the Deep Halls' skeleton, no people (you are alone in your room), art in assets/story/bedsit."""
    base = json.loads((ROOT / "content" / "story" / "deep_halls.json").read_text(encoding="utf-8"))
    base.update({"id": "bedsit", "title": "The Bedsit", "chapter": 9, "art": "bedsit",
                 "description": "The new opening (docs/briefs/BEDSIT_RAVES_BRIEF.md section 2): a path's world, not a Story Campaign chapter."})
    base["acts"] = [{"id": "I", "title": "The Bedsit", "start_bar": 1}]
    base["blocks"] = [{"id": "the_room", "title": "The Bedsit", "act": "Act I", "start_bar": 1, "bars": 8,
                       "events": [{"at_bar": 1, "action": "lights_warm"}, {"at_bar": 1, "action": "player_role", "role": "dancer"}]}]
    base["actors"] = []
    base["groups"] = {"all": []}
    base["silhouettes"] = []
    return base


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8", newline="\n")


def track_scenes_entry() -> None:
    """content/run/track_scenes.json paths.bedsit: the bedsit plays the Chase & Status remix (the one line to the shared file; a dict key, nothing else changes)."""
    p = ROOT / "content" / "run" / "track_scenes.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["paths"]["bedsit"] = {"bedsit": {"track": TRACK_ID, "note": "the bedsit's own track: the Chase & Status remix of Valley of the Shadows by Origin Unknown, a relaxed scene"}}
    for t in ORDER:  # every rave plays the same track; its bass stem is locked until the knob is freed (src/bedsit/space_rave_host.gd)
        for n in ("%s_rave" % RAVES[t][0], "%s_stage" % RAVES[t][0]):
            d["paths"]["bedsit"][n] = {"track": TRACK_ID, "note": "the opening rave track; the bass stem is locked on entry until the bass knob is freed"}
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def main(argv: list) -> int:
    if "--bedsit" not in argv:
        print("make_bedsit.py: nothing written. The bedsit path is opt-in; run with --bedsit to (re)write content/paths/bedsit and content/bedsit.")
        return 0
    write(PATH_DIR / "run.json", run_json())
    write(PATH_DIR / "hotspots" / "bedsit.json", hotspots_json())
    for t in ORDER:
        write(PATH_DIR / "hotspots" / ("%s_rave.json" % RAVES[t][0]), {"world": "%s_rave" % RAVES[t][0], "hotspots": rave_hotspots(t)})
    mp = PATH_DIR / "music.json"
    if not mp.exists():
        write(mp, music_json())
    else:  # the space nodes' entries are added to the existing file, nothing else in it changes
        md = json.loads(mp.read_text(encoding="utf-8"))
        have = {n["id"] for n in md["nodes"]}
        for t in ORDER:
            for n in rave_nodes(t):
                if n["id"] not in have:
                    md["nodes"].append({"id": n["id"], "audio": "bedsit_room", "chart": "bedsit_room", "treatment": "none", "temporary": False})
        write(mp, md)
    write(ROOT / "content" / "story" / "bedsit.json", story_json())
    write(BEDSIT_DIR / "themes.json", merge_themes(themes_json(), BEDSIT_DIR / "themes.json"))
    write(BEDSIT_DIR / "routes.json", routes_json())
    track_scenes_entry()
    print("wrote content/paths/bedsit (run.json, hotspots/bedsit.json, music.json if new), content/bedsit/{themes,routes}.json and the track_scenes entry")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
