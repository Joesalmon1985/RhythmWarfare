"""Shared vocabulary and state of the run's hotspot tables (split out of make_hotspots.py, work package N2.3).

The world modules in tools/run/hotspot_tables/ import the helpers from here (T, W, A, P, walk, place, cin, out, avail, add, exits, ch, ob, ft, sc, finished); every call of `add`
(and so of exits, ch, ob, ft, sc) appends to HOTSPOTS and ROWS, and `cin` fills CINEMATICS. The order the world modules are imported in (tools/run/make_hotspots.py) is the order of the
worlds in the output and of the rows of docs/VISUAL_COVERAGE.md. run.json is read when this module is first imported (make_scenes.py writes it before it imports make_hotspots).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CINEMATICS: dict[str, dict] = {}   # name -> {"world", "steps": [...]}
ROWS: list[dict] = []              # the coverage matrix rows
HOTSPOTS: dict[str, list] = {}     # world -> [hotspot]


# ---- small vocabulary ------------------------------------------------------------------------------------------------------------------------------
def T(thing):
    return {"thing": thing}


def W(wp):
    return {"waypoint": wp}


def A(actor):
    return {"actor": actor}


def P(x, y, z):
    return {"pos": [x, y, z]}


def walk(to, role="dancer", style="walk", bars=2, look=None, move="walk"):
    s = {"move": move, "to": to, "bars": bars, "role": role, "style": style}
    if look:
        s["look_at"] = look
    return s


def place(to, role="queasy", style="carried", bars=3, look=None):
    return walk(to, role, style, bars, look, move="place")


def cin(world, name, *steps):
    full = f"{world}.{name}"
    CINEMATICS[full] = {"world": world, "steps": list(steps)}
    return full


def out(route=None, flags=(), cin=None, energy=None, music=None, activity=None):
    o = {}
    if route:
        o["route"] = route
    if flags:
        o["flags_set"] = list(flags)
    if cin:
        o["cinematic"] = cin
    if energy:
        o["energy"] = energy
    if music:
        o["music"] = music
    if activity:
        o["activity"] = activity
    return o


def avail(all=(), none=(), energy_min=0, once=False):
    return {"flags_all": list(all), "flags_none": list(none), "energy_min": energy_min, "once": once}


# ---- scenes (read from run.json for the exits) -----------------------------------------------------------------------------------------------------
RUN = json.loads((ROOT / "content/run/run.json").read_text(encoding="utf-8"))
NODES = {n["id"]: n for n in RUN["nodes"]}
WORLD_MAP = {w["id"]: w["map"] for w in RUN["worlds"]}
EXIT_LOOK = {"default": "open", "other": "glow"}


def add(scene, name, kind, anchor, look, s, f, *, s_text, f_text, default=False, av=None, hook=None, radius=0.8, min_px=88, repeatable=True, selected="ring", window=None, pass_credit=None, on_select=None, ring_m=None):
    n = NODES[scene]
    world = n["world"]
    h = {"id": f"{scene}.{name}", "world": world, "scene": scene, "map": WORLD_MAP[world], "anchor": anchor, "kind": kind, "radius_m": radius, "min_px": min_px,
         "available": av or avail(), "look": {"available": look, "selected": selected, "committed": "flash"}, "challenge": None, "on_success": s, "on_failure": f}
    if ring_m is not None:
        h["look"]["ring_m"] = ring_m
    if hook:
        h["cinematic"] = hook
    h["default"] = default
    h["repeatable"] = repeatable
    if window:
        h["window"] = window
    if pass_credit is not None:
        h["pass_credit"] = pass_credit
    if on_select:
        h["on_select"] = {"cinematic": on_select}
    HOTSPOTS.setdefault(world, []).append(h)
    ROWS.append({"world": world, "scene": scene, "hotspot": h["id"], "kind": kind, "s": s_text, "f": f_text, "default": default,
                 "gate": (av or {}).get("flags_all", []) + ["not " + x for x in (av or {}).get("flags_none", [])]})
    return h


def exits(scene, anchors=None, looks=None, f_energy=-5):
    """One exit hotspot per route of the scene: anchored to its doorway, the first route the default (the door ajar). A failed exit still leaves by the same door, staggering."""
    n = NODES[scene]
    ex = n["place"]["rail"]["exits"]
    anchors = anchors or {}
    looks = looks or {}
    for i, r in enumerate(n["next"]):
        wp = ex[r["dir"]]
        dest = r["to"]
        short = dest.split(".")[-1] if "." in dest else dest
        name = "exit_" + short if "." in dest else "exit_" + dest
        if r.get("to_hub"):  # the way back to the location's hub (graph route rule `to_hub`: `<scene>.to_hub`)
            name = "to_hub"
        elif r.get("hub_link"):  # the link to the partner hub (graph hub_links: `<hub>.to_<partner>`)
            name = "to_" + dest
        look = looks.get(r["dir"], EXIT_LOOK["default"] if i == 0 else EXIT_LOOK["other"])
        fc = cin(NODES[scene]["world"], f"stagger_{scene.split('.', 1)[1] if '.' in scene else 'entry'}_{r['dir']}", walk(wp, "queasy", "stagger", 2))
        loop = " (round again)" if r.get("loop") else ""
        add(scene, name, "exit", anchors.get(r["dir"], W(wp)), look, out(route=dest), out(route=dest, cin=fc, energy=f_energy),
            s_text=f"route {dest}{loop}", f_text=f"same door, staggering ({f_energy} energy)", default=(i == 0), radius=1.0)


def ch(scene, name, anchor, look, s, f, **kw):
    add(scene, name, "character", anchor, look, s, f, **kw)


def ob(scene, name, anchor, look, s, f, **kw):
    add(scene, name, "object", anchor, look, s, f, **kw)


def ft(scene, name, anchor, look, s, f, **kw):
    add(scene, name, "feature", anchor, look, s, f, **kw)


def sc(scene, name, anchor, look, s, f, **kw):
    return add(scene, name, "secret", anchor, look, s, f, **kw)


def finished(path_id):
    """Plan D10: a portal's look once its path has been finished (any ending's keep: flag), the endings read from content/paths/<id>/run.json."""
    run = json.loads((ROOT / "content/paths" / path_id / "run.json").read_text(encoding="utf-8"))
    ends = sorted({n["ending"] for n in run["nodes"] if n.get("ending")})
    return {"flags_any": [f"keep:path_{path_id}_{e}" for e in ends], "available": "crown", "tint": "#ffd25a"}
