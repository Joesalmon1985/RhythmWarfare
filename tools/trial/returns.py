#!/usr/bin/env python3
"""The Bassment's own way back (lead ruling 19; docs/parallel-development/NARRATIVE_GRAPH.md 2.6, the graph overlay's `bassment.return`): every passage that has no way out of the
Bassment gets one more choice, the return, leading out (`"to": null, "exit": "warehouse"`: TrialFlow ends the adventure there and the router lands it on the hub the quest was
entered from, the items kept, docs/narrative/N2_2_ROUTER.md). The death passages and the victory already lead out and are left as they are.

    python tools/trial/returns.py [--check]      # writes the choices into content/trial/passages.json in place (idempotent); then python tools/trial/make_hotspots.py

THE CHOICE. Last in the passage's list (the existing choices keep their index and their hotspot id `trial.<passage>.<n>`), never the default, no phrase of its own (the passage's
default phrase plays), no consequence text. Its hotspot (tools/trial/make_hotspots.py) is an exit anchored at `exit_wp`, the spot of SPOTS below.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PASSAGES = ROOT / "content/trial/passages.json"
MAPS = ROOT / "content/story/maps"
LABEL = "Climb back up to the hub"
# A room whose waypoints the passage's own choices use up gets one more for the return (written into the map once, as the first waypoint): map -> (id, [x, z], yaw, sector)
EXTRA_WAYPOINTS = {  # map -> [(id, [x, z], yaw, sector)]
    "bassment_echo": [("echo_way_up", [3.4, 0.5], 23, "e_round")],  # (the Echo's round room: mirrored from echo_still, the way back up the stairs it came down)
    "bassment_vaults": [("vault_way_up", [-2.5, -5.5], 0, "inner")],  # (the inner vault: every waypoint ahead is a choice's; one 4 m ahead, to the left)
    "bassment_hall": [("hall_way_up", [3.41, 6.51], -71, "h_aisle")],  # (the seam's view: its one waypoint ahead is the seam's)
}
# Where each passage's return stands: tools/trial/return_spots.json, written by tools/trial/return_spots.gd (a waypoint of the room, or a spot ahead of the camera that becomes the
# waypoint `way_up_<passage>`), the spots from which the passage's camera lays every hotspot out (tests/test_trial.gd). A passage with no spot gets no return.
SPOTS = json.loads((Path(__file__).resolve().parent / "return_spots.json").read_text(encoding="utf-8"))
NEW_WAYPOINTS: dict = {}  # map -> [(id, [x, z], yaw, sector)] the spots that are not waypoints yet (filled by apply)
FRONT_DEG = 50.0
MIN_M = 2.0
NL = chr(10)


def _fwd(yaw):
    r = math.radians(yaw)
    return (-math.sin(r), -math.cos(r))


def pick_wp(m: dict, p: dict) -> str:
    wps = {w["id"]: w for w in m["waypoints"]}
    me = wps[p["waypoint"]]
    used = {p["waypoint"]} | {c.get("exit_wp", "") for c in p["choices"] if not c.get("return")}
    f = _fwd(me.get("yaw", 0.0))
    best, best_any = None, None
    for wid, w in wps.items():
        if wid in used:
            continue
        dx, dz = w["at"][0] - me["at"][0], w["at"][1] - me["at"][1]
        d = math.hypot(dx, dz)
        if d < 1.0e-3:
            continue
        ang = math.degrees(math.acos(max(-1.0, min(1.0, (dx * f[0] + dz * f[1]) / d))))
        if d >= MIN_M and ang <= FRONT_DEG and (best is None or d < best[0]):
            best = (d, wid)
        if best_any is None or (ang, d) < best_any[0]:
            best_any = ((ang, d), wid)
    if best:
        return best[1]
    if best_any:
        return best_any[1]
    raise SystemExit("passage %s: no waypoint for the return" % p.get("title"))


def add_waypoints() -> None:
    for mid, rows in EXTRA_WAYPOINTS.items():
      for wid, at, yaw, sec in rows:
        path = MAPS / f"{mid}.json"
        txt = path.read_text(encoding="utf-8")
        if '"id": "%s"' % wid in txt:
            continue
        head = ' "waypoints": [' + NL
        one = json.dumps({"id": wid, "at": at, "yaw": yaw, "sector": sec}, indent=1)  # (the map's own layout: one space a level, the list two levels in)
        block = NL.join("  " + ln for ln in one.split(NL))
        a = txt.index(head)
        b = txt.index(NL + " ]", a)  # (the end of the waypoint list: the new one goes last, the map's first waypoint stays its first)
        path.write_text(txt[:b] + "," + NL + block + txt[b:], encoding="utf-8", newline=NL)


def apply(doc: dict) -> dict:
    maps = {}
    for k, p in doc["passages"].items():
        own = [c for c in p["choices"] if c.get("return")]
        rest = [c for c in p["choices"] if not c.get("return")]
        if any(c.get("to") is None for c in rest):
            p["choices"] = rest  # a way out already (a death, the victory)
            continue
        mid = p["map"]
        if mid not in maps:
            maps[mid] = json.loads((MAPS / f"{mid}.json").read_text(encoding="utf-8"))
        spot = SPOTS.get(str(k))
        if spot is None:  # (no spot in the room the passage's camera can show it at: tools/trial/return_spots.gd found none; the pause menu's back key stays its way out)
            p["choices"] = rest
            continue
        wp = spot.get("wp") or "way_up_%s" % k
        if "at" in spot:
            NEW_WAYPOINTS.setdefault(mid, []).append((wp, spot["at"], next(w["yaw"] for w in maps[mid]["waypoints"] if w["id"] == p["waypoint"]), spot["sector"]))
        p["choices"] = rest + [{"label": LABEL, "to": None, "exit": "warehouse", "phrase": None, "exit_wp": wp, "return": True}]
    return doc


def main(argv: list) -> int:
    text0 = PASSAGES.read_text(encoding="utf-8")
    doc = apply(json.loads(text0))
    if "--check" not in argv:
        for mid, rows in NEW_WAYPOINTS.items():
            EXTRA_WAYPOINTS.setdefault(mid, []).extend(rows)
        add_waypoints()
    text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    if text == text0.replace("\r\n", "\n"):
        print("bassment returns: up to date")
        return 0
    if "--check" in argv:
        print("bassment returns: content/trial/passages.json is not up to date")
        return 1
    PASSAGES.write_text(text, encoding="utf-8", newline="\n")
    n = sum(1 for p in doc["passages"].values() if any(c.get("return") for c in p["choices"]))
    print("bassment returns: %d passages" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
