"""Heralds at the quest entrances (lead ruling 25, docs/art/HERALDS.md): the one call a hotspot table makes to stand a quest's herald beside an entrance.

    from heralds import herald
    herald("gospel", "warehouse.balcony.star", side="left")             # the shepherd, on the left of the star as the player sees it from the scene's standpoint
    herald("ember", portal_dict, side="right", gap=1.3)                 # an entrance given as the dict sc()/add() returned
    herald("squadron", "hub.radio", at=(1.0, -9.5))                     # an exact ground point [x, z] in metres instead of a side
    herald("dungeon", "warehouse.wizard", self_thing=True, toward=T("sign_wc_door"))   # the entrance IS the herald (a billboard of the map): it plays the gesture itself

A herald is scenery that belongs to its entrance: it is written into the entrance hotspot as a `herald` block, never as a hotspot of its own, so it is never a choice, is never
counted by the cap or the audits, can never be selected and takes no part in routing. The run shows it while its entrance is staged (on offer in this visit: available, from the
scene's first beat), so a herald of an entrance behind a flag appears when the entrance does. src/story/story_heralds.gd draws it.

The block: {"quest": dungeon|gospel|squadron|ember, "at": [x, z] (where it stands), "toward": [x, z] (what it points at: the entrance's anchor, or `toward`), "mark_y": metres above
the floor where the quest's mark hangs over the entrance: 1.05 m over the anchor, clear of the choice layer's lamp at 0.6 m} or, with self_thing, {"quest", "self": <thing id of the anchor>, "toward"}. The gesture is mirrored at run time so that
it always points from `at` to `toward` on screen, whatever the camera.

Placement rules (checked here, errors stop make_hotspots.py): the herald stands inside a sector of the scene's map, at least the entrance's touch radius plus HALF_W from the
entrance (its body never covers the touch ring), at least HALF_W + 0.3 m clear of every other hotspot anchor of the scene, and on the same floor height as some sector there.
`side` is the side of the entrance as the player sees it from the scene's standpoint (its `place.waypoint`), looking at the entrance: the herald stands `gap` metres that way
and STEP metres towards the player, so it is beside the entrance and a little in front of it.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from hotspots_common import HOTSPOTS, NODES, ROOT

QUESTS = ("dungeon", "gospel", "squadron", "ember")
HALF_W = 0.45  # half a herald's width (m), with the arm out
STEP = 0.35
_MAPS: dict = {}


def _map(name: str) -> dict:
    if name not in _MAPS:
        _MAPS[name] = json.loads((ROOT / "content/story/maps" / f"{name}.json").read_text(encoding="utf-8"))
    return _MAPS[name]


def _inside(poly, x, z) -> bool:
    n, c = len(poly), False
    for i in range(n):
        (x1, z1), (x2, z2) = poly[i], poly[(i + 1) % n]
        if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1):
            c = not c
    return c


def sector_at(mp: dict, x: float, z: float):
    for s in mp["sectors"]:
        if _inside(s["polygon"], x, z):
            return s
    return None


def ground_of(mp: dict, anchor: dict):
    """(x, z, height above the floor of the point the hotspot centres on) of an anchor, as HotspotView.resolve reads it."""
    if "pos" in anchor:
        x, y, z = anchor["pos"]
        return float(x), float(z), float(y)
    if "thing" in anchor:
        for t in mp["things"]:
            if t["id"] == anchor["thing"]:
                return float(t["at"][0]), float(t["at"][1]), float(t.get("y", float(t.get("size", 1.0)) * 0.5))
    if "waypoint" in anchor:
        for w in mp["waypoints"]:
            if w["id"] == anchor["waypoint"]:
                return float(w["at"][0]), float(w["at"][1]), 1.0
    if "actor" in anchor:
        for h in mp["homes"]:
            if h["actor"] == anchor["actor"]:
                return float(h["at"][0]), float(h["at"][1]), 1.0
    raise SystemExit(f"herald: anchor {anchor} not found in the map")


def _find(entrance) -> dict:
    if isinstance(entrance, dict):
        return entrance
    for lst in HOTSPOTS.values():
        for h in lst:
            if h["id"] == entrance:
                return h
    raise SystemExit(f"herald: no hotspot {entrance} (call herald() after the entrance is added)")


def herald(quest: str, entrance, side: str | None = None, at=None, gap: float = 1.25, toward: dict | None = None, self_thing: bool = False) -> dict:
    """Stand the herald of `quest` at `entrance` (a hotspot id or the dict add()/sc() returned). Returns the herald block."""
    if quest not in QUESTS:
        raise SystemExit(f"herald: quest {quest} is not one of {QUESTS}")
    h = _find(entrance)
    hid = h["id"]
    mp = _map(h["map"])
    ex, ez, ey = ground_of(mp, toward or h["anchor"])
    if self_thing:
        if "thing" not in h["anchor"]:
            raise SystemExit(f"herald: {hid}: self_thing needs an entrance anchored on a thing of the map")
        block = {"quest": quest, "self": h["anchor"]["thing"], "toward": [round(ex, 3), round(ez, 3)], "mark_y": round(ey + 0.55, 3)}  # (the mark over what it points at)
        h["herald"] = block
        return block
    if at is not None:
        hx, hz = float(at[0]), float(at[1])
    else:
        if side not in ("left", "right"):
            raise SystemExit(f"herald: {hid}: give side='left' or 'right', or at=(x, z)")
        wp = next(w for w in mp["waypoints"] if w["id"] == NODES[h["scene"]]["place"]["waypoint"])
        dx, dz = ex - wp["at"][0], ez - wp["at"][1]
        ln = math.hypot(dx, dz) or 1.0
        dx, dz = dx / ln, dz / ln
        rx, rz = -dz, dx  # the screen right of a view looking along (dx, dz) (StoryProjector.right)
        sg = 1.0 if side == "right" else -1.0
        hx, hz = ex + sg * rx * gap - dx * STEP, ez + sg * rz * gap - dz * STEP
    sec = sector_at(mp, hx, hz)
    if sec is None:
        raise SystemExit(f"herald: {hid}: ({hx:.2f}, {hz:.2f}) is not inside any sector of {h['map']}")
    d = math.hypot(hx - ex, hz - ez)
    if d < float(h["radius_m"]) + HALF_W:
        raise SystemExit(f"herald: {hid}: stands {d:.2f} m from the entrance, inside its touch ring (needs {float(h['radius_m']) + HALF_W:.2f})")
    for o in HOTSPOTS.get(h["world"], []):
        if o["scene"] != h["scene"] or o is h:
            continue
        try:
            ox, oz, _ = ground_of(mp, o["anchor"])
        except SystemExit:
            continue
        if math.hypot(hx - ox, hz - oz) < HALF_W + 0.3:
            raise SystemExit(f"herald: {hid}: stands on {o['id']}'s anchor")
    block = {"quest": quest, "at": [round(hx, 3), round(hz, 3)], "toward": [round(ex, 3), round(ez, 3)], "mark_y": round(ey + 1.05, 3)}
    h["herald"] = block
    return block


def heralds_of(hotspots: dict) -> list:
    """Every herald block of the tables: [(hotspot id, block)] (the docs and the tests list them)."""
    return [(h["id"], h["herald"]) for lst in hotspots.values() for h in lst if "herald" in h]
