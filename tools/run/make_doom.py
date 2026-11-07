#!/usr/bin/env python3
"""The Doom worlds' scenes (docs/briefs/DOOM_WORLDS_BRIEF.md, docs/doom/LAUNCH.md): the pilot scene `doom_warehouse` and its placeholder destinations, written as an OVERLAY on the run.

    python3 tools/run/make_scenes.py --doom        (or RW_DOOM_WORLDS=1)  writes the overlay after the normal generation
    python3 tools/run/make_doom.py                 the overlay alone

Writes content/run/doom/run.json (worlds, nodes, cinematics), content/run/doom/music.json (the nodes' music) and content/run/doom/hotspots/doom_warehouse.json. content/run/run.json is NOT
touched: RunData merges the overlay only when the environment variable RW_DOOM_WORLDS=1 is set, so the legacy campaign (and every test that does not set it) is exactly as before.

Placeholders: the brief routes the Warehouse floor to doom_balcony (ahead), doom_bar (left) and doom_lounge (right). Those scenes do not exist yet, so under the flag they are three
alias scenes of the same world and map (doom_balcony, doom_bar, doom_lounge), each standing on the warehouse floor and leading on to `doom_warehouse.return` (the world's exit scene,
whose two routes loop back to the floor). When a real scene lands it replaces its alias in DOOM_SCENES.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "content/run/doom"
MAPS = ROOT / "content/story/maps"
WORLD = {"id": "doom_warehouse", "title": "The Warehouse (Doom worlds pilot)", "map": "doom_warehouse", "depth": 1, "story": "res://content/run/doom/story_doom_warehouse.json",
         "blurb": "A fenced dance floor under steel trusses. The stage ahead, the bar on the left, the lounge on the right: follow the guide you like."}


def P(to, role="dancer", style="walk", bars=3, hold=0, via=None, choice=False):
    """One rail place: the move to waypoint `to` (a polyline through the `via` waypoints, each leg traced through the map: docs/story/HEIGHTS_AND_PATHS.md), then the camera stands
    still for `hold` bars; `choice` marks a choice viewpoint (it holds at least RunRail.CHOICE_HOLD_BARS)."""
    d = {"to": to, "role": role, "style": style, "bars": bars}
    if via:
        d["via"] = list(via)
    if hold:
        d["hold_bars"] = hold
    if choice:
        d["choice"] = True
    return d


EXITS = {"up": "wh_stage_top", "left": "wh_bar_door", "right": "wh_lounge_door", "down": "wh_ref"}
# The stay loop (the good rail) goes round the floor: the west band north of the bar, up on the pedestal, against the south railing on the floor, then back to the reference viewpoint, a
# choice viewpoint (8 bars still). The via points are in the map (tools/doom/author_warehouse.py); tools/story/check_rail_paths.gd traces every leg.
GOOD = [
    P("wh_plinths", bars=4, hold=2, via=["wh_v_bar_e1", "wh_v_bar_mid", "wh_v_bar_e2"]),
    P("wh_platform", bars=4, hold=2, via=["wh_v_gate_w_out", "wh_v_gate_w_in", "wh_v_court_n", "wh_ped_foot"]),
    P("wh_fence", bars=3, hold=2, via=["wh_ped_foot"]),
    P("wh_ref", bars=4, hold=8, choice=True, via=["wh_v_court_sw", "wh_v_gate_s", "wh_v_lounge_w"]),
]
BAD = [P("wh_ref_back", "queasy", "walk", 2), P("wh_sw_corner", "queasy", "stagger", 3)]  # a stumble back along the walkway
# The routes out of the floor and back in, one polyline move each (the way the camera walks to the threshold of ahead / left / right, the arrival from the doorway, the stumble round the
# corner and home), from the reference viewpoint unless it says `from`. They carry hold_bars (still at the end) like a rail place.
ROUTE_MOVES = {
    "up": P("wh_stage_top", "on_stage", bars=4, hold=1, via=["wh_v_lounge_w", "wh_v_gate_s", "wh_stage_approach", "wh_stage_steps"]),
    "left": P("wh_bar_door", bars=2, hold=1, via=["wh_bar_approach"]),
    "right": P("wh_lounge_door", bars=2, hold=1, via=["wh_lounge_approach"]),
    "stumble": P("wh_ref", "recovered", "stagger", bars=3, via=["wh_ref_back", "wh_sw_corner"]),
    "arrive": {**P("wh_ref", bars=3), "from": "wh_arrive"},
}


def rail(arrive="wh_arrive"):
    return {"good": json.loads(json.dumps(GOOD)), "bad": json.loads(json.dumps(BAD)), "arrive": arrive, "exits": dict(EXITS), "routes": json.loads(json.dumps(ROUTE_MOVES)), "_glances": True}


# id, short name, title, entry, exit_scene, next [(to, dir, label, loop)], music slot
DOOM_SCENES = [
    ("doom_warehouse", "floor", "The Dance Floor", True, False,
     [("doom_warehouse", "down", "Stay on the floor", True), ("doom_balcony", "up", "Up the stage steps to the balcony", False), ("doom_warehouse.bar", "left", "Into the bar", False),
      ("doom_warehouse.chill", "right", "Into the chill-out", False)], 0),
    ("doom_balcony", "balcony", "The Balcony (stand-in)", False, False, [("doom_warehouse.return", "up", "On", False)], 2),
    ("doom_warehouse.bar", "bar", "The Bar (stand-in; the real scene is the world doom_bar, reached from the return scene)", False, False, [("doom_warehouse.return", "up", "On", False)], 1),
    ("doom_warehouse.chill", "chill", "The Chill-out (stand-in; the real scene is the world doom_lounge, reached from the return scene)", False, False, [("doom_warehouse.return", "up", "On", False)], 3),
    ("doom_warehouse.return", "return", "Back to the Floor", False, True,
     [("doom_warehouse", "up", "Round again", True), ("doom_bar", "left", "On to the Copper Bar", False), ("doom_lounge", "right", "On to the Chill-out lounge", False)], 5),
]
GUIDE = {  # hotspot id suffix: (guide thing, route, sprite stem)
    "balcony": ("wh_guide_stage", "doom_balcony", "stage"),
    "bar": ("wh_guide_bar", "doom_warehouse.bar", "bar"),
    "lounge": ("wh_guide_lounge", "doom_warehouse.chill", "lounge"),
}


def staging(thing, stem):
    """The choice layer's staging of a guide (src/run/choice_staging.gd, archetype figure): the billboard's sprite and motion per state, no ring and no lamp."""
    def st(state, n, motion):
        return [{"thing": thing, "sprite": "guide_%s_%s_%d" % (stem, state, n), "motion": motion}]
    return {"archetype": "figure", "touch": {"w": 1.8, "h": 2.4},
            "states": {"current": st("available", 0, "still"), "other": st("idle", 0, "still"), "touched": st("selected", 0, "still"), "committed": st("committed", 0, "still"), "declined": st("idle", 0, "still")}}


def hotspots(cinematics: dict) -> dict:
    hs = []
    for i, (name, (thing, dest, stem)) in enumerate(GUIDE.items()):
        dr = {"balcony": "up", "bar": "left", "lounge": "right"}[name]
        cname = "doom_warehouse.stagger_%s" % name
        cinematics[cname] = {"world": "doom_warehouse", "steps": [{"move": "walk", "to": EXITS[dr], "bars": 2, "role": "queasy", "style": "stagger"}]}
        hs.append({"id": "doom_warehouse.exit_%s" % name, "world": "doom_warehouse", "scene": "doom_warehouse", "map": "doom_warehouse", "anchor": {"thing": thing}, "kind": "exit",
                   "radius_m": 1.0, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
                   "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": dest},
                   "on_failure": {"route": dest, "cinematic": cname, "energy": -5}, "default": False, "repeatable": True, "staging": staging(thing, stem)})
    hs.append({"id": "doom_warehouse.exit_stay", "world": "doom_warehouse", "scene": "doom_warehouse", "map": "doom_warehouse", "anchor": {"pos": [-17.7, 0.4, 17.05]}, "kind": "exit",
               "radius_m": 1.4, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
               "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": "doom_warehouse"},
               "on_failure": {"route": "doom_warehouse", "energy": -5}, "default": True, "repeatable": True,
               "staging": {"archetype": "none", "touch": {"w": 2.6, "h": 1.4}}})  # (no door and no lamp: the foreground is the place you stand; the choice layer draws nothing for it)
    return {"world": "doom_warehouse", "hotspots": hs}


def write(helpers: dict | None = None) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    if helpers is None:
        import make_scenes as ms
        helpers = {"GL": ms.GL}
    nodes = []
    for k, (sid, short, title, entry, exit_scene, nxt, slot) in enumerate(DOOM_SCENES):
        r = rail()
        r.pop("_glances")
        r["glances"] = [{"by": -12, "bars": 2}, {"by": 14, "bars": 2}, {"by": -8, "pitch": 4, "bars": 2}]  # restrained: the pads and the guides stay in view
        r["strolls"] = [{"fwd": 0.8, "bars": 3}]
        nodes.append({"id": sid, "world": "doom_warehouse", "scene": short, "title": title, "entry": entry, "exit_scene": exit_scene, "role": "dancer",
                      "blurb": WORLD["blurb"] if entry else title,
                      "next": [{"to": t[0], "dir": t[1], "label": t[2], **({"loop": True} if t[3] else {})} for t in nxt],
                      "place": {"waypoint": "wh_ref", "rail": r}})
    cin: dict = {}
    hot = hotspots(cin)
    music = [{"id": sid, "arrangement": "warehouse_1", "slot": slot, "alternates": ["warehouse_2", "warehouse_3"], "treatment": "none", "temporary": False} for sid, *_r, slot in DOOM_SCENES]
    worlds, extra_hot = [WORLD], {}
    # --- the DJ Booth (env-booth): its world, nodes, music and hotspots, from tools/run/make_doom_booth.py (a separate block: other scenes add theirs the same way)
    import make_doom_booth
    make_doom_booth.add(P, worlds, nodes, cin, music, extra_hot)
    (OUT / "hotspots").mkdir(parents=True, exist_ok=True)
    # --- the Copper Bar (env-bar): its world, nodes, music and hotspots, from tools/run/make_doom_bar.py (docs/doom/scenes/bar.md)
    import make_doom_bar as bar
    worlds.append(bar.WORLD)
    nodes += bar.nodes()
    music += bar.music()
    extra_hot["doom_bar"] = bar.hotspots(cin)
    # --- the Chill-out Lounge (env-chill): its world, scenes, hotspots, cinematics, music and story, from tools/run/make_doom_lounge.py (docs/doom/scenes/lounge.md)
    import make_doom_lounge
    lounge = make_doom_lounge.contribute()
    worlds += lounge["worlds"]
    nodes += lounge["nodes"]
    cin.update(lounge["cinematics"])
    music += lounge["music"]
    extra_hot.update(lounge["hotspots"])
    for stem, doc in lounge["story"].items():
        (OUT / (stem + ".json")).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    # --- the Mothership (env-mothership): its world, nodes, music and hotspots, from tools/run/make_doom_mothership.py (docs/doom/scenes/mothership.md)
    import make_doom_mothership
    make_doom_mothership.add(P, worlds, nodes, cin, music, extra_hot)
    for wid, doc in extra_hot.items():
        (OUT / "hotspots" / ("%s.json" % wid)).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (OUT / "run.json").write_text(json.dumps({"worlds": worlds, "nodes": nodes, "cinematics": cin}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (OUT / "music.json").write_text(json.dumps({"nodes": music}, indent=1) + "\n", encoding="utf-8", newline="\n")
    (OUT / "hotspots" / "doom_warehouse.json").write_text(json.dumps(hot, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("doom overlay: %d scenes, %d hotspots, %d cinematics -> %s" % (len(nodes), len(hot["hotspots"]), len(cin), OUT))


if __name__ == "__main__":
    write()
