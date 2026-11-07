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
LANDED = {"space_rave": "N"}  # raves that exist as real nodes (src/bedsit/space_rave_host.gd, tools/story/build_space_rave.py)
PLACEHOLDER_RAVES = {FACING[f][1]: f for f in FACINGS if FACING[f][1] not in LANDED}  # scene id -> facing it leaves from (resolve to the bedsit)
SPACE_STATIONS = {  # activity scene -> (title, home waypoint, doorway waypoint, activity id in content/raves/space.json "activities")
    "space_cloakroom": ("Cloakroom", "cloak_view", "cloak_door", "cloakroom"),
    "space_bar": ("Bar", "bar_view", "bar_door", "bar"),
    "space_race": ("Hangar", "hangar_view", "hangar_door", "race"),
}
# the stations that are real scenes (ruling 38, contract 10): scene id -> (scene name, hold waypoint the activity is played from, the thing the hotspot is anchored on, minigame id, blurb)
SPACE_ACTIVITY_SCENES = {
    "space_cloakroom": ("cloakroom", "cloak_hold", "cloak_counter", "cloakroom", "The coat check in the ring's west alcove: a counter, a rail of coats and an attendant who wants the right coat for each symbol."),
    "space_bar": ("bar", "bar_hold", "bar_counter", "bar", "The bar in the ring's east alcove: a counter, a back shelf of glasses and a bartender who remembers the drinks."),
}


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
    r = {"good": good, "bad": [{"to": home, "role": "dancer", "style": "walk", "bars": 2}], "glances": [{"by": 0, "pitch": 0, "bars": 2}], "strolls": [{"fwd": 0.0, "bars": 2}], "exits": exits}
    if arrive:
        r["arrive"] = arrive
    return r


def space_nodes() -> list:
    """The Space rave (content/story/maps/space_rave.json): the hub (a choice viewpoint holding 8 bars: the stage, the cloakroom, the bar, the hangar and the way home), the stage (the deck with the
    bass knob), and a placeholder node per activity that loops back to the hub (other agents build those as minigames: the activity id is in content/raves/space.json `activities`)."""
    base = {"world": "space_rave", "role": "dancer", "relaxed": True, "treatment": "none"}
    hub_next = [{"to": "bedsit", "dir": "up", "label": "Home through the airlock"}, {"to": "space_stage", "dir": "n", "label": "Up to the stage"}, {"to": "space_cloakroom", "dir": "w", "label": "The cloakroom"},
                {"to": "space_bar", "dir": "e", "label": "The bar"}, {"to": "space_race", "dir": "s", "label": "The hangar: a race"}]
    hub = dict(base, id="space_rave", scene="hub", title="The Space Rave", entry=True, exit_scene=True, blurb="The Mothership's ring round a void. A DJ waves from the stage; the cloakroom, the bar and the hangar are across the ring.",
               next=hub_next, theme="space",
               place={"waypoint": "hub_view", "rail": srail("hub_view", [{"to": "hub_view", "role": "dancer", "style": "walk", "bars": 3, "choice": True, "hold_bars": 8}],
                                                              {"n": "stage_foot", "w": "cloak_door", "e": "bar_door", "s": "hangar_door", "up": "home_door"}, arrive="space_arrive")})
    stage = dict(base, id="space_stage", scene="stage", title="The Stage", entry=False, exit_scene=True, blurb="The dais at the north of the ring: two steps up to the DJ deck. The bass knob is stuck.",
                 next=[{"to": "space_rave", "dir": "up", "label": "Back to the ring", "loop": True}, {"to": "bedsit", "dir": "out", "label": "Home"}], theme="space",
                 place={"waypoint": "stage_foot", "rail": srail("stage_foot", [
                     {"to": "stage_steps", "role": "dancer", "style": "walk", "bars": 2, "hold_bars": 1},
                     {"to": "deck_view", "role": "on_stage", "style": "walk", "bars": 2, "hold_bars": 4}], {"up": "stage_foot", "out": "stage_foot"})})
    out = [hub, stage]
    for sid, (title, home, door, act_id) in SPACE_STATIONS.items():
        if sid in SPACE_ACTIVITY_SCENES:  # a real scene: the route from the hub ends at a hold facing the counter (contract 10's camera: hold_bars for the activity)
            scene, hold, thing, mg, blurb = SPACE_ACTIVITY_SCENES[sid]
            out.append(dict(base, id=sid, scene=scene, title=title, entry=False, exit_scene=True, blurb=blurb, theme="space", activity=mg,
                            next=[{"to": "space_rave", "dir": "up", "label": "Back to the ring", "loop": True}, {"to": "bedsit", "dir": "out", "label": "Home"}],
                            place={"waypoint": door, "rail": srail(door, [{"to": hold, "role": "dancer", "style": "walk", "bars": 2, "hold_bars": 10}], {"up": door, "out": door})}))
            continue
        out.append(dict(base, id=sid, scene=sid, title="PLACEHOLDER: " + title, entry=False, exit_scene=True, placeholder=True, placeholder_for={"theme": "space", "activity": act_id}, theme="space",
                        blurb="A stand-in for the %s activity (id '%s' in content/raves/space.json activities), built elsewhere as a minigame. It loops back to the ring." % (title.lower(), act_id),
                        next=[{"to": "space_rave", "dir": "up", "label": "Back to the ring", "loop": True}, {"to": "bedsit", "dir": "out", "label": "Home"}],
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
    nodes.extend(space_nodes())
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
        "worlds": [{"id": "bedsit", "title": "The Bedsit", "map": "bedsit", "story": "res://content/story/bedsit.json", "depth": 1, "blurb": "One room, four walls, four raves."},
                   {"id": "space_rave", "title": "The Space Rave", "map": "space_rave", "story": "res://content/story/space_rave.json", "depth": 2, "blurb": "The Mothership's ring round a void: a stage, a cloakroom, a bar and a hangar."}],
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


def space_hotspots() -> list:
    def row(hid, scene, anchor, kind, route="", default=False, acting=None, available=None, window="final", success=None):
        h = {"id": hid, "world": "space_rave", "scene": scene, "map": "space_rave", "anchor": anchor, "kind": kind, "radius_m": 1.2, "min_px": 88,
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

    rows = [row("space_rave.stage", "space_rave", {"actor": "dj"}, "character", "space_stage", acting=act("wave")),
            row("space_rave.cloakroom", "space_rave", {"actor": "attendant"}, "character", "space_cloakroom", acting=act("beckon")),
            row("space_rave.bar", "space_rave", {"actor": "bartender"}, "character", "space_bar", acting=act("beckon")),
            row("space_rave.race", "space_rave", {"actor": "pilot"}, "character", "space_race", acting=act("beckon")),
            row("space_rave.home", "space_rave", {"thing": "home_hatch"}, "exit", "bedsit", default=True)]
    rows.append(row("space_stage.deck", "space_stage", {"thing": "deck"}, "object", window="any", success={"activity": "bass_knob"},
                    available={"flags_all": [], "flags_none": ["space_bass_fixed"], "energy_min": 0, "once": False}))
    rows.append(row("space_stage.home", "space_stage", {"waypoint": "deck_view"}, "exit", "bedsit"))
    rows.append(row("space_stage.back", "space_stage", {"waypoint": "stage_foot"}, "exit", "space_rave", default=True))
    for sid, (title, home, door, act_id) in SPACE_STATIONS.items():
        if sid in SPACE_ACTIVITY_SCENES:  # the activity's hotspot: the counter, an object whose success outcome is {activity: id} (content/bedsit/cloakroom_hotspot_example.json); any window seats it at the end of the block
            scene, hold, thing, mg, blurb = SPACE_ACTIVITY_SCENES[sid]
            h = row("%s.%s" % (sid, mg), sid, {"thing": thing}, "object", window="any", success={"activity": mg},
                    available={"flags_all": [], "flags_none": ["space_%s_done" % mg], "energy_min": 0, "once": False})
            h["radius_m"] = 2.4
            h["min_px"] = 220
            rows.append(h)
        rows.append(row("%s.back" % sid, sid, {"waypoint": door}, "exit", "space_rave", default=True))
        rows.append(row("%s.home" % sid, sid, {"waypoint": home}, "exit", "bedsit"))
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
    for n in ("space_rave", "space_stage"):  # the Space rave plays the same track; its bass stem is locked until the knob is freed (src/bedsit/space_rave_host.gd)
        d["paths"]["bedsit"][n] = {"track": TRACK_ID, "note": "the opening rave track; the bass stem is locked on entry until the bass knob is freed"}
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def main(argv: list) -> int:
    if "--bedsit" not in argv:
        print("make_bedsit.py: nothing written. The bedsit path is opt-in; run with --bedsit to (re)write content/paths/bedsit and content/bedsit.")
        return 0
    write(PATH_DIR / "run.json", run_json())
    write(PATH_DIR / "hotspots" / "bedsit.json", hotspots_json())
    write(PATH_DIR / "hotspots" / "space_rave.json", {"world": "space_rave", "hotspots": space_hotspots()})
    mp = PATH_DIR / "music.json"
    if not mp.exists():
        write(mp, music_json())
    else:  # the space nodes' entries are added to the existing file, nothing else in it changes
        md = json.loads(mp.read_text(encoding="utf-8"))
        have = {n["id"] for n in md["nodes"]}
        for n in space_nodes():
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
