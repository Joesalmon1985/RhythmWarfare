#!/usr/bin/env python3
"""Writes content/trial/hotspots.json from content/trial/passages.json (so the two never drift; tests/test_trial.gd checks they agree):
    python3 tools/trial/make_hotspots.py

One hotspot per choice of every passage (the defeat passage 0 included), keyed by passage, following the contract in docs/VISUAL_RHYTHM_ADVENTURE_PLAN.md section 2:
  id "trial.<passage>.<n>" (n is the choice's index in the passage's full choice list, gated choices included), scene "<passage>", map, anchor, kind, radius_m, min_px,
  available {flags_all: [item], ...}, look, challenge {family, tier} | null, on_success, on_failure, default, repeatable, choice (= n).
kind:   encounter (a fight: the creature's thing), feature (a luck test: the rope, the pipes, the door), object (a choice that needs an item, or whose place grants one: the
        crystal, the archway, the palm), exit (everything else: the waypoint the choice leads toward, a doorway, a ladder foot, a gap).
anchor: exit -> {"waypoint": exit_wp}; others -> {"thing": id}. Creatures have no thing in the maps: a marker thing `hs_<encounter>` is written into the map at the spot where the
        creature stands (TrialScene.figure_spot); the mirror has none either (`hs_mirror`). The markers are the only edit to content/story/maps/bassment_*.json, and are rewritten
        on every run (lines whose id starts "hs_").
on_success: {"route": "<passage>"} or {"route": "exit"} (a death's or the victory's way out); on_failure only for a luck test: {"route": <fail passage>}. A failed plain choice or fight holds the place
        and a third lost fight leads to 0: TrialFlow does that, and the contract's outcome keys have no word for it. The consequence text and the fight's texts come from passages.json at run time.
The file is {"world": "bassment", "hotspots": [...]} as TrialData.load_hotspots reads it. `kind` follows the contract (only an exit may be the default), `trial_kind` is what the Bassment means.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "content/trial/hotspots.json"
MAPS = ROOT / "content/story/maps"

FIGURES = {  # mirrors TrialScene.FIGURES: size, lift, dist
    "lampmoth": (1.7, 0.7, 2.6), "cable_eel": (1.9, 0.9, 3.4), "barrel_knight": (2.0, 0.0, 2.8), "mildew_mother": (2.0, 0.0, 2.8), "mirror_twin": (1.9, 0.0, 2.8),
    "bouncer": (2.5, 0.0, 3.0), "rat_king": (1.7, 0.0, 2.6), "furnace_imp": (1.4, 0.0, 2.4), "gargoyle": (3.0, 0.4, 3.4), "echo": (2.0, 0.0, 3.0),
}
# (passage, choice index) -> an existing thing of the map the hotspot sits on (a luck test's feature, an item's object); "marker" writes a new one at the exit waypoint
THINGS = {
    (5, 1): "junc2", (12, 1): "valve2", (16, 1): "crack_crystal", (20, 1): "bar_g", (23, 1): "arch_door", (32, 1): "marker:hs_mirror", (37, 1): "rope_ledge",
    (40, 1): "rope_sign", (52, 2): "hand_ar0", (55, 1): "hand_pl1", (57, 0): "door_glow",
}
RADIUS = {"exit": 0.9, "encounter": 1.2, "object": 0.7, "feature": 1.0}
LOOK = {"exit": "glow", "encounter": "pulse", "object": "glow", "feature": "flicker"}


def pip(p, poly):
    x, y = p
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / l2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def boundary(p, poly):
    return min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


class Map:
    def __init__(self, mid):
        self.id = mid
        self.path = MAPS / f"{mid}.json"
        self.d = json.load(open(self.path))
        self.sec = {s["id"]: s for s in self.d["sectors"]}
        self.wp = {w["id"]: w for w in self.d["waypoints"]}
        self.things = {t["id"]: t for t in self.d["things"]}

    def sector_at(self, p):
        for s in self.d["sectors"]:
            poly = s["polygon"]
            if pip(p, poly) or boundary(p, poly) < 1e-4:
                return s["id"]
        return ""

    def inside(self, p, sid, margin):
        poly = self.sec[sid]["polygon"]
        return pip(p, poly) and boundary(p, poly) >= margin - 1e-6

    def figure_spot(self, wid, dist):
        """TrialScene.figure_spot: walk back from `dist` in front of the waypoint until the point is inside a sector with a 0.5 m margin."""
        w = self.wp[wid]
        at = w["at"]
        r = math.radians(w["yaw"])
        fwd = (-math.sin(r), -math.cos(r))
        d = dist
        while d >= 1.2:
            p = (at[0] + fwd[0] * d, at[1] + fwd[1] * d)
            sid = self.sector_at(p)
            if sid != "" and self.inside(p, sid, 0.5):
                return p, sid
            d -= 0.4
        return (at[0] + fwd[0] * 1.2, at[1] + fwd[1] * 1.2), w["sector"]


def fmt(v):
    return json.dumps(v, ensure_ascii=False)


def main():
    data = json.load(open(ROOT / "content/trial/passages.json"))
    P, ph, enc = data["passages"], data["phrases"], data["encounters"]
    maps = {}
    markers = {}  # map id -> {thing id: line}
    out = {}
    for n in sorted(P, key=int):
        p = P[n]
        m = maps.setdefault(p["map"], Map(p["map"]))
        gives = lambda to: to is not None and bool(P[str(to)].get("grants"))
        hs = []
        for i, c in enumerate(p["choices"]):
            to = c.get("to")
            req = c.get("requires")
            if c.get("encounter"):
                kind = "encounter"
            elif c.get("test"):
                kind = "feature"
            elif req or gives(to) or (int(n), i) in THINGS:
                kind = "object"
            else:
                kind = "exit"
            if kind == "encounter":
                e = c["encounter"]
                size, lift, dist = FIGURES[e]
                (x, z), sid = m.figure_spot(p["waypoint"], dist)
                tid = "hs_" + e
                markers.setdefault(p["map"], {})[tid] = (
                    '  {"id": %s, "kind": "billboard", "sprite": "thing_glow", "at": [%.2f, %.2f], "y": %.2f, "size": 0.05, "anim": "none"},' % (fmt(tid), x, z, lift + size * 0.5))
                anchor = {"thing": tid}
            elif kind == "exit":
                anchor = {"waypoint": c["exit_wp"]}
            else:
                t = THINGS.get((int(n), i))
                if t is None:
                    raise SystemExit(f"passage {n} choice {i} ({kind}) needs an entry in THINGS")
                if t.startswith("marker:"):
                    tid = t[7:]
                    w = m.wp[c["exit_wp"]]
                    markers.setdefault(p["map"], {})[tid] = (
                        '  {"id": %s, "kind": "billboard", "sprite": "thing_glow", "at": [%.2f, %.2f], "y": 1.2, "size": 0.05, "anim": "none"},' % (fmt(tid), w["at"][0], w["at"][1]))
                    t = tid
                elif t not in m.things:
                    raise SystemExit(f"passage {n}: thing {t} is not in {p['map']}")
                anchor = {"thing": t}
            fail = None
            if to is None:
                ok = {"route": "exit"}
                chal = None
            else:
                ok = {"route": str(to)}
                phr = ph[c["phrase"]]
                chal = {"family": phr["family"], "tier": phr["tier"], "phrase": c["phrase"]}
                if c.get("test"):
                    ok = {"route": str(c["test"]["pass"])}
                    fail = {"route": str(c["test"]["fail"])}
                # a plain choice or a fight that is failed holds the place (TrialFlow: the choice becomes the default; a third lost fight leads to 0): no outcome is written for it
            avail = {"flags_all": [req] if req else [], "flags_none": [], "energy_min": 0, "once": False}
            default = bool(c.get("default", False))
            look = LOOK[kind]
            h = {
                "id": f"trial.{n}.{i}", "world": "bassment", "scene": n, "map": p["map"], "choice": i, "anchor": anchor,
                # the engine contract lets only an exit be the default: a default fight, luck test or object is an `exit` there, and `trial_kind` keeps what it really is
                "kind": "exit" if default else kind, "trial_kind": kind,
                "radius_m": RADIUS[kind], "min_px": 72, "available": avail,
                "look": {"available": look, "selected": "ring", "committed": "flash"},
                "challenge": chal, "on_success": ok,
                "default": default, "repeatable": False,
            }
            if fail is not None:
                h["on_failure"] = fail
            hs.append(h)
        out[n] = hs
    doc = {"schema": 1, "world": "bassment", "title": "The Bassment's hotspots (generated by tools/trial/make_hotspots.py from passages.json: do not edit)",
           "hotspots": [h for n in sorted(out, key=int) for h in out[n]]}
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    # marker things: rewrite the hs_ lines of each map that has any (and remove stale ones everywhere)
    for mp in sorted(MAPS.glob("bassment_*.json")):
        lines = mp.read_text().split("\n")
        keep = [ln for ln in lines if '{"id": "hs_' not in ln]
        add = list(markers.get(mp.stem, {}).values())
        if add:
            k = next(i for i, ln in enumerate(keep) if ln.strip().startswith('"things": ['))
            keep[k + 1:k + 1] = add
        if keep != lines:
            mp.write_text("\n".join(keep))
    kinds = {}
    for hs in out.values():
        for h in hs:
            kinds[h["trial_kind"]] = kinds.get(h["trial_kind"], 0) + 1
    print("hotspots:", sum(len(v) for v in out.values()), kinds, "markers:", sum(len(v) for v in markers.values()))


if __name__ == "__main__":
    main()
