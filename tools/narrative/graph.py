#!/usr/bin/env python3
"""Narrative graph: builds today's and the target graph from the game data, checks the ten rules, exports and reports.

Pure Python 3, standard library only, no Godot. The design is docs/parallel-development/NARRATIVE_GRAPH.md (section 6 is the specification of this
tool); the overlay format is docs/parallel-development/graph/narrative.schema.md (format `rhythm_warfare.narrative.v1`).

    python tools/narrative/graph.py                       # validate the TARGET graph (game data + content/narrative/graph.json); exit 1 on any FAIL
    python tools/narrative/graph.py --graph today         # validate TODAY's graph (game data alone); it reports today's failures
    python tools/narrative/graph.py --graph both          # both, one after the other
    python tools/narrative/graph.py --strict              # every exception counts as a failure
    python tools/narrative/graph.py --export              # write narrative_graph.json, narrative_graph_target.json, narrative_graph.mmd, graph_today.json
    python tools/narrative/graph.py --report FILE         # write the Markdown report (both graphs)
    python tools/narrative/graph.py --content content --overlay content/narrative/graph.json --out docs/parallel-development/graph

Exit code 0: no rule fails (exceptions are allowed unless --strict). 1: at least one rule fails. 2: an input is unreadable or the overlay format is unknown.

A graph id is "<path>/<node>": `main/<scene>` for the main run, `<path>/<node>` for gospel, squadron and ember, `bassment/<passage>` for the Bassment. `$checkpoint`
is the placeholder of a return: it resolves to the hub of the location the quest was entered from.

How choices are counted (the design, section 2.5): a choice is one touched door, person or object, or the default taken. An automatic scene (no object to touch)
costs nothing. A hidden option (the pause menu, the system back key), a miss twin (`on_miss`, `test_fail`, `fight_lost`), an option that needs a flag or an item the
player has not got, and "stay in this scene" are not choices. Distinct destinations are counted, so a reactive object that leads where another leads adds nothing.
"""
from __future__ import annotations

import argparse
import collections
import heapq
import json
import random
import sys
from pathlib import Path

FORMAT = "rhythm_warfare.narrative.v1"
EXPORT_FORMAT = "rhythm_warfare.narrative.graph.v1"
CHECKPOINT = "$checkpoint"
MISS_OUTCOMES = ("on_miss", "test_fail", "fight_lost")
GODOT_TEST = "tests/test_narrative_*.gd"

# What today's graph is built on when there is no overlay (the overlay repeats these and rule 7 compares them).
SHIPPED_PATHS = ("gospel", "squadron", "ember")  # the fourth path, `stub`, is a developer test and not part of the shipped run
BUILTIN_LOCATIONS = [
    ("warehouse_rave", "Warehouse Rave", ["warehouse"], "main/warehouse"),
    ("hospital_ward", "Hospital Ward", ["hospital", "hospital_late"], "main/hospital"),
    ("mental_hospital", "Mental Hospital", ["ward", "ward_late"], "main/ward"),
    ("alien_spaceship", "Alien Spaceship", ["mothership"], "main/mothership"),
    ("hell", "Hell", ["underworld"], "main/underworld"),
]
QUEST_IDS = ("bassment", "gospel", "squadron", "ember")
QUEST_TITLES = {"bassment": "The Bassment", "gospel": "The Life of Jesus", "squadron": "The Mission Count", "ember": "The Ember Road"}
# Hidden ways out that the code gives every quest scene (RunPlay "Leave this path" and the trial's system back key). Not in the data files.
BUILTIN_HIDDEN = {"bassment": "system_back_key", "gospel": "pause_menu_leave", "squadron": "pause_menu_leave", "ember": "pause_menu_leave"}
HIDDEN_VIA = {"system_back_key": "system back key", "pause_menu_leave": "pause menu: Leave this path"}
DEFAULT_SETTINGS = {
    "min_choices": 3,
    "max_choices_to_quest": 5,
    "max_choices_to_quest_in_location": 2,
    "history_limit": 32,
    "hotspot_cap": 8,
    "hub_hotspot_cap": 10,
}
TOP_KEYS = {"format", "start", "settings", "locations", "quests", "entrances", "route_rules", "extra_routes", "exceptions", "status", "date", "note"}
RULE_TITLES = {
    1: "Each quest entry within the limit of choices from the start; entry never gated by rhythm or another quest",
    2: "All four quests from every mainline location and every scene of it; the mainline continues after a return",
    3: "Every quest has a working return to the hub of the location it was entered from",
    4: "Mainline locations are traversable",
    5: "Every scene has at least the minimum number of choices",
    6: "No unintended dead ends",
    7: "Every reference resolves",
    8: "Scene and music metadata valid",
    9: "Cycles and re-entry behave",
    10: "Route history and checkpoint stay consistent",
}


class InputError(Exception):
    """An input cannot be read, or the overlay format is unknown (exit code 2)."""


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InputError(f"cannot read {path}: {exc}")


# ----------------------------------------------------------------------------------------------------------------------------------------------- game data
class Game:
    """The game data the graph is built from. Read-only."""

    def __init__(self, content):
        self.content = Path(content)
        c = self.content
        run = load_json(c / "run/run.json")
        self.main = {n["id"]: n for n in run["nodes"]}
        self.main_worlds = [w["id"] for w in run["worlds"]]
        self.start_id = run["start_node"]
        self.start = "main/" + run["start_node"]
        self.hotspots = collections.defaultdict(list)  # graph id of the scene -> hotspots
        self.hotspot_ids = set()
        for f in sorted((c / "run/hotspots").glob("*.json")):
            for h in load_json(f)["hotspots"]:
                self.hotspots["main/" + h["scene"]].append(h)
                self.hotspot_ids.add(h["id"])
        self.paths = {}
        for p in SHIPPED_PATHS:
            r = load_json(c / "paths" / p / "run.json")
            self.paths[p] = {"nodes": {n["id"]: n for n in r["nodes"]}, "start": r["start_node"]}
            for f in sorted((c / "paths" / p / "hotspots").glob("*.json")):
                for h in load_json(f)["hotspots"]:
                    self.hotspots[p + "/" + h["scene"]].append(h)
                    self.hotspot_ids.add(h["id"])
        trial = load_json(c / "trial/passages.json")
        self.trial = trial
        self.passages = trial["passages"]
        self.passage_start = str(trial.get("start", 1))
        hs = c / "trial/hotspots.json"
        if hs.exists():
            for h in load_json(hs)["hotspots"]:
                self.hotspot_ids.add(h["id"])
        ts = c / "run/track_scenes.json"
        self.track_scenes = load_json(ts) if ts.exists() else {}
        self.catalogue = set()
        for f in sorted((c / "music/tracks").glob("*.json")) if (c / "music/tracks").exists() else []:
            d = load_json(f)
            self.catalogue.add(str(d.get("id", f.stem)))

    def scene_ids(self):
        out = ["main/" + k for k in self.main]
        for p in SHIPPED_PATHS:
            out += [p + "/" + k for k in self.paths[p]["nodes"]]
        out += ["bassment/" + k for k in self.passages]
        return out

    def entry_of(self, quest):
        if quest == "bassment":
            return "bassment/" + self.passage_start
        return quest + "/" + self.paths[quest]["start"]

    def endings(self):
        """The scenes where a quest ends in the data: path nodes with an `ending`, the Bassment's victory passage. Death passages are not completions."""
        out = {q: [] for q in QUEST_IDS}
        for p in SHIPPED_PATHS:
            out[p] = sorted(p + "/" + k for k, n in self.paths[p]["nodes"].items() if n.get("ending"))
        out["bassment"] = sorted("bassment/" + k for k, x in self.passages.items() if x.get("kind") == "victory")
        return out


# ------------------------------------------------------------------------------------------------------------------------------------------------- graph
class Graph:
    """Nodes (dict id -> record) and edges (list of records). `out` indexes the edges by their origin."""

    def __init__(self, kind, nodes, edges, locations, quests, settings, start):
        self.kind = kind  # "today" or "target"
        self.nodes = nodes
        self.edges = edges
        self.locations = locations  # list of {"id", "title", "worlds", "hub"}
        self.quests = quests  # list of {"id", "entry", "completion": [ids], ...}
        self.settings = settings
        self.start = start
        self.out = collections.defaultdict(list)
        for e in edges:
            self.out[e["from"]].append(e)
        self.hub_of = {l["id"]: l["hub"] for l in locations}
        self.entry_of = {q["id"]: q["entry"] for q in quests}
        self.quest_of_entry = {q["entry"]: q["id"] for q in quests}
        self.relevant_flags = set()
        for e in edges:
            c = e["condition"]
            self.relevant_flags |= {f for f in c.get("flags_all", []) + c.get("flags_none", []) if not f.startswith("keep:")}

    def loc(self, n):
        return self.nodes[n].get("location")

    def mainline(self):
        return [n for n, d in self.nodes.items() if d["category"] == "mainline"]

    def quest_scenes(self, q):
        return [n for n, d in self.nodes.items() if d.get("quest") == q]

    def resolve(self, e, origin):
        """The scene an edge leads to. `$checkpoint` resolves to the hub of `origin` (a location id); None when there is no origin."""
        if e["to"] == CHECKPOINT:
            return self.hub_of.get(origin) if origin else None
        return e["to"]

    # An edge is a choice the player can make: not hidden, not a miss twin, not locked by a flag or item (conservative), not automatic.
    def is_choice(self, e):
        return not e.get("hidden") and not e["condition"].get("auto") and self.is_visible(e)

    def is_visible(self, e):
        c = e["condition"]
        return not e.get("hidden") and c.get("outcome") not in MISS_OUTCOMES and not c.get("flags_all")

    def is_gated_entrance(self, e):
        return e["kind"] == "quest_entry" and bool(e.get("rhythm_gate"))

    def is_authored_return(self, e):
        return e["kind"] == "quest_return" and not e.get("hidden")


def edge_key(e):
    c = e["condition"]
    return (e["from"], e["to"], e["via"], e["kind"], c.get("outcome") or "", e.get("link") or "", bool(e.get("hidden")))


def new_edge(frm, to, via, kind, status, quest=None, **extra):
    e = {"from": frm, "to": to, "via": via, "kind": kind, "status": status,
         "condition": {"flags_all": [], "flags_none": [], "flags_set": []}}
    if quest:
        e["quest"] = quest
    for k, v in extra.items():
        if k == "condition":
            e["condition"].update(v)
        elif v is not None:
            e[k] = v
    return e


# ------------------------------------------------------------------------------------------------------------------------------------------ today's graph
def _resolve_route(game, route, here_quest):
    """(to, kind, quest) for a hotspot route: a scene of the same run, `path:<id>`, a Bassment passage number or `run:warehouse`."""
    if route.startswith("path:"):
        p = route[5:]
        if p not in game.paths:
            return None
        return game.entry_of(p), "quest_entry", p
    if route == "run:warehouse":
        return game.start, "quest_return", here_quest
    if route == "bassment":  # a hub's entrance into the Bassment, taken at the lap's end (ruling 15; N2.2): not the wizard's mid-scene passage number
        return game.entry_of("bassment"), "quest_entry", "bassment"
    return None


def _scene_edges(game, gid, quest, nodes_of_run, prefix):
    """The edges from one main-run or path scene: for every hotspot, its success outcome (a block passed) and its failure outcome (a block missed).
    An outcome without a route of its own goes on by the scene's default exit (`continues_by_default_exit`)."""
    hs = game.hotspots.get(gid, [])
    default_route = ""
    for h in hs:
        if h.get("default"):
            default_route = h["on_success"].get("route", "")
    node = nodes_of_run[gid.split("/", 1)[1]]
    edges = []

    def target(route):
        if route in nodes_of_run:
            return prefix + route, "scene", None
        if route.isdigit() and route in game.passages:
            return "bassment/" + route, "quest_entry", "bassment"
        r = _resolve_route(game, route, quest)
        return r

    for h in hs:
        for key, outcome in (("on_success", "on_pass"), ("on_failure", "on_miss")):
            o = h.get(key) or {}
            route = o.get("route", "")
            cont = False
            if not route:
                route, cont = default_route, True
            t = target(route) if route else None
            if t is None:
                continue
            to, kind, q = t
            av = h.get("available", {})
            e = new_edge(gid, to, h["id"], kind, "existing", quest=(q if kind != "scene" else None))
            e["condition"].update({"flags_all": list(av.get("flags_all", [])), "flags_none": list(av.get("flags_none", [])),
                                   "flags_set": list(o.get("flags_set", [])), "outcome": outcome, "object_kind": h.get("kind", "")})
            if h.get("default"):
                e["condition"]["default"] = True
            if cont:
                e["condition"]["continues_by_default_exit"] = True
            if kind == "quest_entry":
                e["rhythm_gate"] = outcome == "on_pass"  # the entrance is touched in the final window; a miss does not enter (the failure has no route)
                if str(node.get("trial_gate", "")) and q == "bassment" and route != "bassment":
                    e["legacy"] = True  # the wizard: mid-scene entrance outside the port
            edges.append(e)
    if not hs:  # an automatic scene: it goes on by itself, which costs no choice
        for nx in node.get("next", []):
            to = prefix + nx["to"]
            e = new_edge(gid, to, "auto", "scene", "existing")
            e["condition"]["auto"] = True
            edges.append(e)
    return edges


def build_today(game):
    """Today's graph, from the game data alone."""
    loc_of_world = {w: l[0] for l in BUILTIN_LOCATIONS for w in l[2]}
    hub_of = {l[0]: l[3] for l in BUILTIN_LOCATIONS}
    nodes, edges = {}, []
    for k, n in game.main.items():
        gid = "main/" + k
        loc = loc_of_world[n["world"]]
        nodes[gid] = {"id": gid, "title": n["title"], "world": n["world"], "category": "mainline", "location": loc, "hub": gid == hub_of[loc], "status": "existing"}
        edges += _scene_edges(game, gid, None, game.main, "main/")
    for p in SHIPPED_PATHS:
        for k, n in game.paths[p]["nodes"].items():
            gid = p + "/" + k
            nodes[gid] = {"id": gid, "title": n["title"], "world": n["world"], "category": "quest", "quest": p, "hub": False, "status": "existing"}
            if n.get("ending"):
                nodes[gid]["ending"] = n["ending"]
            edges += _scene_edges(game, gid, p, game.paths[p]["nodes"], p + "/")
    grants = {k: x.get("grants", []) for k, x in game.passages.items() if x.get("grants")}
    for k, x in game.passages.items():
        gid = "bassment/" + k
        nodes[gid] = {"id": gid, "title": x["title"], "world": x.get("zone", ""), "category": "quest", "quest": "bassment", "hub": False, "status": "existing"}
        if x.get("kind") in ("death", "victory"):
            nodes[gid]["ending"] = x["kind"]
        for i, c in enumerate(x["choices"]):
            via = f"trial.{k}.{i}"
            if c.get("to") is None:
                edges.append(new_edge(gid, game.start, via, "quest_return", "existing", quest="bassment", condition={"outcome": "exit", "default": bool(c.get("default"))}))
                continue
            dests = [("take", str(c["to"]))]
            if "test" in c:
                dests = [("test_pass", str(c["test"]["pass"])), ("test_fail", str(c["test"]["fail"]))]
            elif c.get("encounter"):
                dests = [("win_or_take", str(c["to"]))]
            for outcome, to in dests:
                e = new_edge(gid, "bassment/" + to, via, "scene", "existing")
                e["condition"].update({"outcome": outcome, "flags_set": [f"item:{g}" for g in grants.get(to, [])]})
                if c.get("default"):
                    e["condition"]["default"] = True
                if c.get("requires"):
                    e["condition"]["flags_all"] = [f"item:{c['requires']}"]
                edges.append(e)
            if c.get("encounter") and int(c.get("lives", 0) or 0) > 0:  # src/trial/trial_flow.gd: a fight lost `lives` times ends the adventure at passage 0
                e = new_edge(gid, "bassment/0", via, "scene", "existing", condition={"outcome": "fight_lost"})
                e["note"] = "engine rule (trial_flow.gd): a fight lost for good goes to passage 0"
                edges.append(e)
    for q in QUEST_IDS:  # the hidden ways out
        for n in [n for n, d in nodes.items() if d.get("quest") == q]:
            edges.append(new_edge(n, game.start, HIDDEN_VIA[BUILTIN_HIDDEN[q]], "quest_return", "existing", quest=q, hidden=True))
    for e in edges:
        if e["kind"] == "quest_return" and "quest" not in e:
            e["quest"] = nodes[e["from"]].get("quest")
    locations = [{"id": i, "title": t, "worlds": w, "hub": h} for i, t, w, h in BUILTIN_LOCATIONS]
    ends = game.endings()
    quests = [{"id": q, "title": QUEST_TITLES[q], "entry": game.entry_of(q), "completion": ends[q]} for q in QUEST_IDS]
    return Graph("today", nodes, edges, locations, quests, dict(DEFAULT_SETTINGS), game.start)


# ------------------------------------------------------------------------------------------------------------------------------------------------ search
def search(g, start, *, flags=True, skip_miss=True, ungated_only=False, hidden=False, origin0=None, want_path=False, maxcost=60, stop_at=None):
    """Fewest choices from `start` to every scene (Dijkstra; automatic edges cost 0). Returns {scene: cost} and, with want_path, {scene: [edges]}.

    flags=True follows the flags and items set on the way (a touch is assumed passed); flags=False uses only flag-free edges (conservative).
    skip_miss drops miss twins; ungated_only drops quest entrances that need a passed block; hidden=True lets the hidden leaves count as options.
    The state is (scene, flags, origin): `origin` is the location a quest was entered from, to resolve `$checkpoint`."""
    rel = g.relevant_flags
    pq = [(0, 0, start, frozenset(), origin0)]
    cnt = 1
    seen = {}
    pushed = {(start, frozenset(), origin0): 0}
    prev = {}
    result, paths = {}, {}
    while pq:
        d, _, n, fl, org = heapq.heappop(pq)
        key = (n, fl, org)
        if key in seen:
            continue
        seen[key] = d
        if n not in result:
            result[n] = d
            if stop_at and stop_at <= set(result):
                break
            if want_path:
                p, k = [], key
                while k in prev:
                    k, e = prev[k]
                    p.append(e)
                paths[n] = p[::-1]
        if d > maxcost:
            continue
        for e in g.out.get(n, []):
            c = e["condition"]
            if e.get("hidden") and not hidden:
                continue
            if skip_miss and c.get("outcome") in MISS_OUTCOMES:
                continue
            if ungated_only and g.is_gated_entrance(e):
                continue
            if flags:
                if any(f not in fl for f in c.get("flags_all", []) if not f.startswith("keep:")):
                    continue
                if any(f in fl for f in c.get("flags_none", []) if not f.startswith("keep:")):
                    continue
            elif c.get("flags_all"):
                continue
            t = g.resolve(e, org)
            if t is None or t not in g.nodes:
                continue
            norg = org
            if e["kind"] == "quest_entry":
                norg = g.loc(n) if g.nodes[n]["category"] == "mainline" else org
            elif e["kind"] == "quest_return" or g.nodes[t]["category"] == "mainline":
                norg = None
            nfl = (fl | {f for f in c.get("flags_set", []) if f in rel}) if flags else fl
            nkey = (t, nfl, norg)
            cost = 0 if c.get("auto") else 1
            if nkey in seen or pushed.get(nkey, 1e9) <= d + cost:
                continue
            pushed[nkey] = d + cost
            cnt += 1
            prev[nkey] = (key, e)
            heapq.heappush(pq, (d + cost, cnt, t, nfl, norg))
    return (result, paths) if want_path else result


def fewest_to_quests(g, start, **kw):
    """{quest: fewest choices from `start` to the quest's entry, or None}."""
    dist = search(g, start, stop_at={q["entry"] for q in g.quests}, **kw)
    return {q["id"]: dist.get(q["entry"]) for q in g.quests}


# ------------------------------------------------------------------------------------------------------------------------------------------ target graph
def load_overlay(path):
    ov = load_json(path)
    if not isinstance(ov, dict) or ov.get("format") != FORMAT:
        raise InputError(f"{path}: the overlay format is {ov.get('format') if isinstance(ov, dict) else None!r}, expected {FORMAT!r}")
    for k in ("start", "locations", "quests", "entrances"):
        if k not in ov:
            raise InputError(f"{path}: required key '{k}' is missing")
    return ov


def overlay_settings(ov):
    s = dict(DEFAULT_SETTINGS)
    s.update(ov.get("settings", {}))
    return s


def _object_pattern(pattern, scene=None, quest=None):
    out = pattern
    if scene is not None:
        out = out.replace("<scene>", scene.split("/", 1)[1])
    if quest is not None:
        out = out.replace("<quest>", quest)
    return out


def _copy(e):
    return json.loads(json.dumps(e))


def build_target(game, ov):
    """The target graph: today's graph from the game data, with the changes the overlay declares. Returns (graph, problems); a problem is a
    reference or structure error that rule 7 reports."""
    base = build_today(game)
    problems = []
    locs, quests = ov["locations"], ov["quests"]
    loc_of_world = {w: l["id"] for l in locs for w in l.get("worlds", [])}
    hubs = {l["id"]: l["hub"] for l in locs}
    nodes = {k: dict(v) for k, v in base.nodes.items()}
    for k, d in nodes.items():
        if d["category"] == "mainline":
            loc = loc_of_world.get(d["world"])
            if loc is None:
                problems.append(f"world {d['world']} of {k} belongs to no location")
            d["location"] = loc
            d["hub"] = hubs.get(loc) == k
    entry_of = {q["id"]: q["entry"] for q in quests}

    entrances = ov["entrances"]
    originals = set()  # existing objects whose gate the overlay removes (a "partial" entrance is a copy of one)
    authored = set()  # entrance objects the content now has as hotspots (status "existing"): the overlay's ungated edge stands for the hotspot's own edges (N2.2)
    for en in entrances:
        o = en.get("object", {})
        if o.get("status") == "partial" and o.get("copy_of"):
            originals.add(o["copy_of"])
        if o.get("status") == "existing" and o.get("id"):
            authored.add(o["id"])
    for x in ov.get("extra_routes", []):
        xo = x.get("object", {})
        if x.get("kind") == "quest_entry" and xo.get("status") == "existing" and xo.get("id"):
            authored.add(xo["id"])

    edges = []
    for e in base.edges:
        if e.get("hidden"):
            continue  # the hidden leaves are rebuilt from the quests' `hidden_fallbacks`
        c = e["condition"]
        if e["via"] in authored and e["kind"] != "quest_return":
            continue  # an authored entrance: the overlay's edge below is its route (ungated, through the port)
        if e["via"] in originals:
            if c.get("outcome") == "on_miss":
                continue  # an ungated entrance has no miss twin
            e = _copy(e)
            e["condition"] = {"flags_all": [], "flags_none": [], "flags_set": []}
            if e["kind"] == "quest_entry":
                e["rhythm_gate"] = False
                e["transition"] = "port"
            e["status"] = "changed"
            e["note"] = "today gated by a passed block and flags; in the target not gated"
        elif e["kind"] == "quest_return":
            if c.get("outcome") == "on_miss":
                continue  # a return is not rhythm-gated: no miss twin
            e = _copy(e)
            e["to"] = CHECKPOINT
            e["status"] = "changed"
            e["note"] = "authored way back; lands on the Floor today, on the checkpoint in the target"
        elif e["kind"] == "quest_entry" and e.get("legacy"):  # the wizard: a `legacy_way` of the Warehouse's Dungeon entrance
            e = _copy(e)
            e["transition"] = "legacy_mid_scene"
        edges.append(e)

    def add(e):
        edges.append(e)
        return e

    # 1. the hub entrances (their extra ways, the legacy wizard, are already in the data)
    for en in entrances:
        q = en.get("quest")
        if q not in entry_of:
            problems.append(f"entrance {en.get('id')}: unknown quest {q}")
            continue
        o = en.get("object", {})
        e = add(new_edge(en["scene"], entry_of[q], o.get("id", ""), "quest_entry", "existing" if o.get("id") in authored else "proposed", quest=q, entrance=en["id"],
                         rhythm_gate=bool(en.get("rhythm_gate")), transition=en.get("transition")))
        if o.get("status") == "partial":
            e["note"] = "a copy of " + str(o.get("copy_of")) + " on the hub"
        for cnd in en.get("conditions", []):
            e["condition"]["flags_all"] += list(cnd.get("flag_all", []))
            fn = cnd.get("flag_none", [])
            e["condition"]["flags_none"] += [fn] if isinstance(fn, str) else list(fn)
    # 2. the links between the hubs of a pair of locations
    for l in locs:
        for hl in l.get("hub_links", []):
            add(new_edge(l["hub"], hl["to"], hl["object"]["id"], "scene", "proposed", link="hub_to_hub"))
    # 3. the route rules
    rules = {r.get("id"): r for r in ov.get("route_rules", [])}
    for rid in rules:
        if rid not in ("to_hub", "back", "return"):
            problems.append(f"route rule {rid}: reserved id")
    if "to_hub" in rules:
        r = rules["to_hub"]
        for n, d in sorted(nodes.items()):
            if d["category"] == "mainline" and not d["hub"] and d.get("location"):
                add(new_edge(n, hubs[d["location"]], _object_pattern(r["object"], scene=n), r.get("kind", "scene"), "proposed", link="to_hub"))
    if "back" in rules:
        r = rules["back"]
        preds = collections.defaultdict(list)
        for e in base.edges:
            if e["kind"] == "scene" and nodes[e["from"]]["category"] == "quest" and nodes[e["from"]].get("quest") != "bassment" and not e.get("hidden") \
                    and e["condition"].get("outcome") not in MISS_OUTCOMES and e["from"] != e["to"] and e["to"] in nodes \
                    and nodes[e["to"]].get("quest") == nodes[e["from"]].get("quest") and e["from"] not in preds[e["to"]]:
                preds[e["to"]].append(e["from"])
        for n, d in sorted(nodes.items()):
            if d["category"] == "quest" and d.get("quest") != "bassment":
                for p in sorted(preds.get(n, [])):
                    add(new_edge(n, p, _object_pattern(r["object"], quest=d["quest"]), r.get("kind", "scene"), "proposed", link="back",
                                 condition={"previous_scene": True}))
    # 4. the returns of the quests and their hidden leaves
    for q in quests:
        rt = q.get("return", {})
        all_scenes = sorted(k for k, d in nodes.items() if d.get("quest") == q["id"])
        scenes = sorted(rt.get("scenes", [])) if rt.get("placement") == "listed" else all_scenes
        over = {o["scene"]: o["object"] for o in rt.get("overrides", [])}
        if "return" in rules:
            for n in scenes:
                if n in nodes:
                    add(new_edge(n, CHECKPOINT, over.get(n, rt.get("object", q["id"] + ".return")), "quest_return", "proposed", quest=q["id"], link="return"))
        for fb in rt.get("hidden_fallbacks", []):
            for n in all_scenes:
                add(new_edge(n, CHECKPOINT, HIDDEN_VIA.get(fb, fb), "quest_return", "changed", quest=q["id"], hidden=True,
                             note="exists today and lands on the Warehouse Floor; in the target it lands on the checkpoint"))
    # 5. routes added to one scene
    for x in ov.get("extra_routes", []):
        kind = x.get("kind")
        if x.get("scene") not in nodes:
            problems.append(f"extra route {x.get('object', {}).get('id')}: scene {x.get('scene')} does not exist")
            continue
        if kind == "quest_entry":
            q = x.get("quest")
            if q not in entry_of:
                problems.append(f"extra route on {x.get('scene')}: unknown quest {q}")
                continue
            add(new_edge(x["scene"], entry_of[q], x["object"]["id"], "quest_entry", "existing" if x["object"]["id"] in authored else "proposed", quest=q, link="extra_entrance", rhythm_gate=False,
                         transition="port"))
        elif kind in ("restart", "second_route"):
            if x.get("to") not in nodes:
                problems.append(f"extra route {x['object']['id']}: destination {x.get('to')} does not exist")
                continue
            e = add(new_edge(x["scene"], x["to"], x["object"]["id"], "scene", "proposed", link=kind))
            if x.get("owner_to_confirm"):
                e["owner_to_confirm"] = True
        else:
            problems.append(f"extra route on {x.get('scene')}: unknown kind {kind}")
    locations = [{"id": l["id"], "title": l.get("title", l["id"]), "worlds": l.get("worlds", []), "hub": l["hub"]} for l in locs]
    qlist = [{"id": q["id"], "title": q.get("title", ""), "entry": q["entry"], "completion": list(q.get("completion", {}).get("scenes", []))} for q in quests]
    kept = []
    for e in edges:  # an edge end must be a scene (or the checkpoint placeholder); the rest is a problem for rule 7, and the edge is left out
        bad = [end for end in (e["from"], e["to"]) if end != CHECKPOINT and end not in nodes]
        if bad:
            problems.append(f"edge {e['via']}: {bad[0]} is not a scene")
        else:
            kept.append(e)
    return Graph("target", nodes, kept, locations, qlist, overlay_settings(ov), ov["start"]), problems


# ------------------------------------------------------------------------------------------------------------------------------------------------- results
class Result:
    """The outcome of one rule. status: PASS, FAIL (offending ids in `fail`), EXCEPTION (declared exceptions listed in `exceptions`, none failing)."""

    def __init__(self, rule):
        self.rule = rule
        self.title = RULE_TITLES.get(rule, "")
        self.summary = ""
        self.lines = []  # detail lines for the report
        self.fail = []  # offending ids or messages
        self.exceptions = []  # {"id", "reason", "tracked_by", "count", "what"}
        self.not_checkable = []  # parts that data alone cannot decide
        self.warnings = []
        self.data = {}

    @property
    def status(self):
        if self.fail:
            return "FAIL"
        return "EXCEPTION" if self.exceptions else "PASS"


def exceptions_of(ov, rule):
    return [x for x in (ov or {}).get("exceptions", []) if x.get("rule") == rule]


def exception_form_errors(x):
    errs = []
    if not x.get("id"):
        errs.append("an exception has no id")
    for k in ("reason", "tracked_by"):
        if not x.get(k):
            errs.append(f"exception {x.get('id')}: no {k}" + (" (an exception that no later piece of work owns is an error)" if k == "tracked_by" else ""))
    if x.get("report_as") != "exception":
        errs.append(f"exception {x.get('id')}: report_as must be 'exception'")
    if x.get("kind") not in ("named_exception", "terminal_component"):
        errs.append(f"exception {x.get('id')}: kind must be named_exception or terminal_component")
    if not isinstance(x.get("rule"), int) or not 1 <= x["rule"] <= 10:
        errs.append(f"exception {x.get('id')}: rule must be 1 to 10")
    return errs


def _exc_record(x, count, what):
    return {"id": x["id"], "reason": x.get("reason", ""), "tracked_by": x.get("tracked_by", ""), "count": count, "what": what}


def _limit(g, key):
    return g.settings.get(key, DEFAULT_SETTINGS[key])


# ------------------------------------------------------------------------------------------------------------------------------------------------- helpers
def strongly_connected(nodes, adj):
    """Strongly connected components (iterative Tarjan). Returns a list of sets."""
    index, low, on, stack, out, counter = {}, {}, set(), [], [], [0]
    for root in sorted(nodes):
        if root in index:
            continue
        work = [(root, iter(sorted(adj.get(root, ()))))]
        index[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on.add(root)
        while work:
            v, it = work[-1]
            adv = False
            for w in it:
                if w not in nodes:
                    continue
                if w not in index:
                    index[w] = low[w] = counter[0]
                    counter[0] += 1
                    stack.append(w)
                    on.add(w)
                    work.append((w, iter(sorted(adj.get(w, ())))))
                    adv = True
                    break
                if w in on:
                    low[v] = min(low[v], index[w])
            if adv:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp = set()
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.add(w)
                    if w == v:
                        break
                out.append(comp)
    return out


def reach(g, start, edge_ok, nodes_ok=None):
    """Scenes reachable from `start` along the edges for which edge_ok(e) is true (`$checkpoint` is not followed)."""
    seen = {start}
    st = [start]
    while st:
        n = st.pop()
        for e in g.out.get(n, []):
            t = e["to"]
            if t == CHECKPOINT or t in seen or t not in g.nodes or not edge_ok(e):
                continue
            if nodes_ok and not nodes_ok(t):
                continue
            seen.add(t)
            st.append(t)
    return seen


def mainline_edge(g, e):
    return e["kind"] == "scene" and not e.get("hidden") and not e["condition"].get("flags_all") and g.nodes[e["from"]]["category"] == "mainline" \
        and e["to"] in g.nodes and g.nodes[e["to"]]["category"] == "mainline"


def distinct_choices(g, n):
    """(count, destinations) of the choices of a scene: distinct destinations of its choice edges. `$checkpoint` is one destination. A `back` option goes to the
    previous scene, which is one of several: the worst case over the possible predecessors counts."""
    base, backs = set(), set()
    for e in g.out.get(n, []):
        if not g.is_choice(e):
            continue
        if e["condition"].get("previous_scene"):
            backs.add(e["to"])
        elif e["to"] != n:
            base.add(e["to"])
    if not backs:
        return len(base), sorted(base)
    return min(len(base | {p}) for p in backs), sorted(base | backs)


def choice_objects(g, n):
    """The objects of a scene that lead somewhere (what the cap of the scene counts): choice edges with a route of their own, by object id."""
    return {e["via"] for e in g.out.get(n, []) if g.is_choice(e) and not e["condition"].get("continues_by_default_exit") and e["to"] != n}


# ------------------------------------------------------------------------------------------------------------------------------------------------- the rules
def rule_01(g, ov=None, game=None):
    """Rule 1. Each quest's entry is at most `max_choices_to_quest` (default 5) choices from `start`, counted twice: over all visible entrances, and over the entrances that
    are not gated by a passed block; both must reach every quest within the limit. No entrance edge may be gated by a passed block, by a flag, or name another quest, unless a
    declared exception lists its object; an exception that lists an object that is not gated (or does not exist) is stale and fails. Hidden leaves, miss twins and options
    that need a flag do not count as choices; the search follows the flags and items the player picks up on the way."""
    r = Result(1)
    lim = _limit(g, "max_choices_to_quest")
    every = fewest_to_quests(g, g.start)
    ungated = fewest_to_quests(g, g.start, ungated_only=True)
    with_hidden = fewest_to_quests(g, g.start, hidden=True)
    r.data.update({"all": every, "ungated": ungated, "with_hidden": with_hidden, "limit": lim})
    for q in g.quests:
        for name, d in (("any entrance", every), ("ungated entrances only", ungated)):
            v = d[q["id"]]
            if v is None or v > lim:
                r.fail.append(f"{q['id']}: {'not reachable' if v is None else str(v) + ' choices'} ({name}; limit {lim})")
    # the audit of the entrances
    excs = exceptions_of(ov, 1)
    for x in excs:
        r.fail += exception_form_errors(x)
    declared = {}
    for x in excs:
        for o in x.get("scope", {}).get("objects", []):
            declared[o] = x
    flagged = {}
    for e in g.edges:
        if e["kind"] != "quest_entry":
            continue
        c = e["condition"]
        why = []
        if g.is_gated_entrance(e):
            why.append("gated by a passed block")
        if c.get("flags_all") or c.get("flags_none"):
            why.append("needs flags " + ",".join(c.get("flags_all", []) + c.get("flags_none", [])))
        if e.get("transition") == "legacy_mid_scene":
            why.append("legacy mid-scene entrance outside the port")
        if why:
            flagged.setdefault(e["via"], []).append((e, why))
    for via, lst in sorted(flagged.items()):
        if via in declared:
            continue
        for e, why in lst:
            r.fail.append(f"undeclared gated entrance {via} in {e['from']} ({'; '.join(why)})")
    for x in excs:
        used = [o for o in x.get("scope", {}).get("objects", []) if o in flagged]
        stale = [o for o in x.get("scope", {}).get("objects", []) if o not in flagged]
        for o in stale:
            r.fail.append(f"stale exception {x['id']}: {o} is no longer gated or does not exist")
        if used:
            r.exceptions.append(_exc_record(x, sum(len(flagged[o]) for o in used), f"{sum(len(flagged[o]) for o in used)} gated entrance edges ({', '.join(used)})"))
    # the declared conditions of the overlay
    if ov:
        prefixes = {q["id"]: q.get("flag_prefixes", []) for q in ov["quests"]}

        def other_quest(flag, own):
            return any(flag.startswith(p) for qq, ps in prefixes.items() if qq != own for p in ps)

        for q in ov["quests"]:
            for cnd in q.get("entry_conditions", []):
                r.fail.append(f"quest {q['id']}: entry_conditions must be empty or genuinely needed, found {json.dumps(cnd, sort_keys=True)}")
        for en in ov["entrances"]:
            for cnd in en.get("conditions", []):
                text = json.dumps(cnd, sort_keys=True)
                fl = cnd.get("flag_all", []) + ([cnd["flag_none"]] if isinstance(cnd.get("flag_none"), str) else cnd.get("flag_none", []))
                if "passed_block" in text or "on_miss" in text or any(other_quest(f, en["quest"]) for f in fl):
                    r.fail.append(f"entrance {en['id']}: a condition names a passed block, a miss or another quest: {text}")
    parts = [f"{q['id']} {every[q['id']]}" for q in g.quests]
    pu = [str(ungated[q["id"]]) if ungated[q["id"]] is not None else "none" for q in g.quests]
    r.summary = f"quests within {lim} choices: " + ", ".join(parts) + f" (ungated entrances only: {', '.join(pu)})"
    return r


def rule_02(g, ov=None, game=None):
    """Rule 2. Each of the 5 locations offers each of the 4 quests: the hub shows an entrance for every quest that is not gated by a passed block (20 cells); from every scene
    of the location (late worlds included) every quest is at most `max_choices_to_quest_in_location` (default 2) ungated choices away; and the hub has a mainline exit
    (a scene route that is neither a `to_hub` nor a hub link), so that after a return the mainline continues."""
    r = Result(2)
    lim = _limit(g, "max_choices_to_quest_in_location")
    scenes_of = collections.defaultdict(list)
    for n, d in g.nodes.items():
        if d["category"] == "mainline":
            scenes_of[d["location"]].append(n)
    any_scene = hub_any = hub_ungated = 0
    rows = []
    worst_all = 0
    for l in g.locations:
        hub = l["hub"]
        for q in g.quests:
            qid = q["id"]
            ent = [e for e in g.edges if e["kind"] == "quest_entry" and e["quest"] == qid and e["from"] in scenes_of[l["id"]]]
            a = bool(ent)
            h_any = [e for e in ent if e["from"] == hub and g.is_choice(e)]
            h_ung = [e for e in h_any if not g.is_gated_entrance(e)]
            any_scene += a
            hub_any += bool(h_any)
            hub_ungated += bool(h_ung)
            if not h_ung:
                r.fail.append(f"{l['id']}.{qid}: the hub {hub} shows no entrance that is not gated" + (" (an entrance exists elsewhere in the location)" if a else ""))
            rows.append((l["id"], qid, a, bool(h_any), bool(h_ung)))
    for l in g.locations:
        worst = {q["id"]: (0, "") for q in g.quests}
        for s in sorted(scenes_of[l["id"]]):
            d = fewest_to_quests(g, s, ungated_only=True, flags=False)
            for q in g.quests:
                v = d[q["id"]]
                if v is None or v > lim:
                    r.fail.append(f"{s} to {q['id']}: {'not reachable' if v is None else str(v) + ' choices'} (limit {lim})")
                if v is not None and v > worst[q["id"]][0]:
                    worst[q["id"]] = (v, s)
                worst_all = None if (worst_all is None or v is None) else max(worst_all, v)
        rows_w = {qid: w for qid, w in worst.items()}
        r.data.setdefault("worst", {})[l["id"]] = rows_w
        exits = [e for e in g.out.get(l["hub"], []) if g.is_choice(e) and mainline_edge(g, e) and e.get("link") not in ("to_hub", "hub_to_hub") and e["to"] != l["hub"]]
        r.data.setdefault("exits", {})[l["id"]] = sorted({e["to"] for e in exits})
        if not exits:
            r.fail.append(f"{l['id']}: the hub {l['hub']} has no mainline exit")
    r.data.update({"cells_any_scene": any_scene, "cells_hub_any": hub_any, "cells_hub_ungated": hub_ungated, "cells": rows, "worst_choices": worst_all, "limit": lim})
    r.summary = f"{hub_ungated} of 20 cells have an ungated entrance on the hub ({any_scene} have one in some scene of the location); worst scene {'not reachable' if worst_all is None else str(worst_all) + ' choices'}"
    return r


def rule_03(g, ov=None, game=None):
    """Rule 3. Every quest scene offers a visible return (not hidden, not a miss twin, not flag-locked) whose landing is `$checkpoint`, the hub of the location the quest was
    entered from, and every quest scene is reachable from the quest's entry inside the quest. A return that lands on a fixed scene fails (it cannot land where the player
    entered). Hidden leaves never count. For each quest and each origin location with a hub entrance the check is the same, as the landing is the origin's hub."""
    r = Result(3)
    fixed = collections.Counter()
    total = with_ret = fixed_scenes = 0
    no_ret = []
    unreachable = []
    origins = collections.Counter()
    for q in g.quests:
        qid = q["id"]
        scenes = g.quest_scenes(qid)
        seen = reach(g, q["entry"], lambda e: e["kind"] == "scene" and not e.get("hidden"), lambda t: g.nodes[t].get("quest") == qid)
        for s in scenes:
            total += 1
            rets = [e for e in g.out.get(s, []) if e["kind"] == "quest_return" and g.is_choice(e)]
            good = [e for e in rets if e["to"] == CHECKPOINT]
            for e in rets:
                if e["to"] != CHECKPOINT:
                    fixed[e["to"]] += 1
            if good:
                with_ret += 1
            elif rets:
                with_ret += 1
                fixed_scenes += 1
                r.fail.append(f"{s}: the visible return lands on the fixed scene {rets[0]['to']}, not on the checkpoint")
            else:
                no_ret.append(s)
            if s not in seen:
                unreachable.append(s)
        for l in g.locations:
            if any(e["kind"] == "quest_entry" and e["quest"] == qid and e["from"] == l["hub"] and g.is_choice(e) for e in g.edges):
                origins[qid] += 1
    for s in no_ret:
        r.fail.append(f"{s}: no visible return")
    for s in unreachable:
        r.fail.append(f"{s}: not reachable from the entry of its quest")
    hidden = sum(1 for e in g.edges if e.get("hidden"))
    on_checkpoint = total - len(no_ret) - fixed_scenes
    r.data.update({"scenes": total, "with_visible_return": total - len(no_ret), "on_checkpoint": on_checkpoint, "fixed_landing_scenes": fixed_scenes, "without_visible_return": len(no_ret),
                   "fixed_landings": dict(fixed), "unreachable": unreachable, "origins": dict(origins), "hidden_leaves": sum(1 for e in g.edges if e.get("hidden")),
                   "authored_returns": sum(1 for e in g.edges if e["kind"] == "quest_return" and e["status"] == "changed" and not e.get("hidden"))})
    r.summary = f"{on_checkpoint} of {total} quest scenes have a visible return to the checkpoint; {fixed_scenes} have one that lands on a fixed scene ({', '.join(sorted(fixed)) or 'none'}); "                 f"{len(no_ret)} have none; {len(unreachable)} not reachable from the entry"
    return r


def rule_04(g, ov=None, game=None):
    """Rule 4. Searching from `start` over mainline scene edges only (flag-free, not hidden), every mainline scene is reached; from each hub every scene of its location is
    reached. The mutually reachable groups of locations are reported, and a mainline route back to the first location, if any."""
    r = Result(4)
    main = g.mainline()
    ok = lambda e: mainline_edge(g, e)
    seen = reach(g, g.start, ok)
    unr = sorted(n for n in main if n not in seen)
    for n in unr:
        r.fail.append(f"{n}: not reached from {g.start} by mainline routes")
    for l in g.locations:
        hr = reach(g, l["hub"], ok)
        miss = sorted(n for n in main if g.loc(n) == l["id"] and n not in hr)
        for n in miss:
            r.fail.append(f"{n}: not reached from the hub {l['hub']} of {l['id']}")
    adj = collections.defaultdict(set)
    for e in g.edges:
        if mainline_edge(g, e):
            adj[e["from"]].add(e["to"])
    comps = []
    for c in strongly_connected(set(main), adj):
        comps.append((sorted({g.loc(n) for n in c}), len(c)))
    comps.sort()
    back = sorted(n for n in reach(g, g.start, ok) if g.loc(n) == g.loc(g.start) and n != g.start and False)
    first_loc = g.loc(g.start)
    returns_to_first = any(g.loc(e["from"]) != first_loc and g.loc(e["to"]) == first_loc for e in g.edges if mainline_edge(g, e))
    r.data.update({"reached": len(seen), "mainline": len(main), "components": comps, "route_back_to_first_location": returns_to_first})
    r.summary = f"{len(seen)} of {len(main)} mainline scenes reached from the start; components: " + "; ".join(f"{'+'.join(c[0])} ({c[1]} scenes)" for c in comps if c[1] > 1) + \
                ("; a mainline route leads back to the first location" if returns_to_first else "; no mainline route leads back to the first location")
    return r


def rule_05(g, ov=None, game=None):
    """Rule 5. Every scene has at least `min_choices` (default 3) choices: distinct destinations among its visible, non-miss, flag-free, non-hidden edges (`$checkpoint` is one
    destination; for a `previous_scene` option the worst case over the possible predecessors). A declared exception lists the scenes of one quest that are excused; it fails
    when it is stale (a listed scene does not exist, belongs to another quest, or has enough choices: too wide) and every unlisted scene under the minimum fails."""
    r = Result(5)
    mn = _limit(g, "min_choices")
    counts = {n: distinct_choices(g, n)[0] for n in g.nodes}
    under = sorted(n for n, k in counts.items() if k < mn)
    excs = exceptions_of(ov, 5)
    excused = set()
    for x in excs:
        r.fail += exception_form_errors(x)
        sc = x.get("scope", {})
        listed = sc.get("scenes", [])
        qid = sc.get("quest")
        for s in listed:
            if s not in g.nodes:
                r.fail.append(f"exception {x['id']}: {s} is not a scene")
            elif qid and g.nodes[s].get("quest") != qid:
                r.fail.append(f"exception {x['id']}: {s} is not a scene of quest {qid}")
            elif counts[s] >= mn:
                r.fail.append(f"exception {x['id']} is too wide: {s} has {counts[s]} choices")
        really = [s for s in listed if s in counts and counts[s] < mn]
        excused |= set(really)
        if really:
            r.exceptions.append(_exc_record(x, len(really), f"{len(really)} scenes of {qid} under {mn} choices"))
    for n in under:
        if n not in excused:
            r.fail.append(f"{n}: {counts[n]} choices (minimum {mn})")
    groups = collections.OrderedDict()
    for n, d in g.nodes.items():
        gname = "mainline" if d["category"] == "mainline" else d["quest"]
        groups.setdefault(gname, []).append(n)
    table = []
    for gname, lst in groups.items():
        table.append((gname, len(lst), sum(1 for n in lst if counts[n] < mn), min(counts[n] for n in lst)))
    hist = collections.Counter(counts[n] for n in g.nodes if g.nodes[n]["category"] == "mainline")
    bhist = collections.Counter(counts[n] for n in g.nodes if g.nodes[n].get("quest") == "bassment")
    r.data.update({"counts": counts, "under": under, "excused": sorted(excused), "table": table, "mainline_hist": dict(sorted(hist.items())), "bassment_hist": dict(sorted(bhist.items()))})
    r.not_checkable.append("not checkable from data: that each destination is a visible, tappable object of adequate size (checked by the coverage audit, N1.5 and N2.6)")
    r.summary = f"{len(g.nodes) - len(under)} of {len(g.nodes)} scenes have {mn} or more choices; {len(excused)} excused by exception; {len(under) - len(excused)} under without excuse"
    return r


def reachable_optimistic(g, start):
    """Scenes reachable from `start` along any non-hidden edge (miss twins included), where an edge that needs flags or items is usable once every one of its flags has been set
    by some edge already used (flags only accumulate; a flag that must be absent is ignored). A superset of what a player can reach, so a scene it misses is really unreachable."""
    seen, flags, origins = {start}, set(), set()
    changed = True
    while changed:
        changed = False
        for n in sorted(seen):
            for e in g.out.get(n, []):
                if e.get("hidden"):
                    continue
                c = e["condition"]
                if any(f not in flags for f in c.get("flags_all", []) if not f.startswith("keep:")):
                    continue
                if e["kind"] == "quest_entry" and g.nodes[n]["category"] == "mainline" and g.loc(n) not in origins:
                    origins.add(g.loc(n))
                    changed = True
                targets = [g.hub_of[o] for o in sorted(origins)] if e["to"] == CHECKPOINT else [e["to"]]
                for t in targets:
                    if t in g.nodes and t not in seen:
                        seen.add(t)
                        changed = True
                new = set(c.get("flags_set", [])) - flags
                if new:
                    flags |= new
                    changed = True
    return seen


def rule_06(g, ov=None, game=None):
    """Rule 6. (a) Every scene has a visible way out (a choice edge to another scene). (b) Every scene is reachable from `start` by some route (all edges but the hidden
    leaves; flags and items followed). (c) Every quest scene reaches a mainline scene (a return, a hub). (d) Every mainline scene reaches a terminal component. (e) A terminal
    component (a closed group of mainline scenes with no route out apart from `to_hub` routes and quests, and no ending) must be declared by an exception that lists its worlds;
    a declared component that is not closed is stale."""
    r = Result(6)
    for n in sorted(g.nodes):
        outs = [e for e in g.out.get(n, []) if g.is_choice(e) and e["to"] != n]
        if not outs:
            r.fail.append(f"{n}: no visible way out")
    seen = reachable_optimistic(g, g.start)
    unreachable = sorted(n for n in g.nodes if n not in seen)
    for n in unreachable:
        r.fail.append(f"{n}: not reachable from {g.start}")
    # (c) and (d): optimistic reachability, ignoring flags
    rev = collections.defaultdict(set)
    for e in g.edges:
        if e.get("hidden"):
            continue
        t = e["to"]
        if t == CHECKPOINT:
            for l in g.locations:
                rev[l["hub"]].add(e["from"])
        else:
            rev[t].add(e["from"])

    def reaches_target(targets):
        seen = set(targets)
        st = list(targets)
        while st:
            n = st.pop()
            for p in rev.get(n, ()):
                if p not in seen:
                    seen.add(p)
                    st.append(p)
        return seen

    can_main = reaches_target([n for n in g.nodes if g.nodes[n]["category"] == "mainline"])
    trapped = sorted(n for n in g.nodes if g.nodes[n]["category"] == "quest" and n not in can_main)
    for n in trapped:
        r.fail.append(f"{n}: a quest scene that cannot reach the mainline")
    main = set(g.mainline())
    prog = collections.defaultdict(set)
    for e in g.edges:
        if mainline_edge(g, e) and e.get("link") != "to_hub":
            prog[e["from"]].add(e["to"])
    comps = strongly_connected(main, prog)
    terminal = []
    for c in comps:
        leaves = any(t not in c for n in c for t in prog.get(n, ()))
        has_cycle = len(c) > 1 or any(n in prog.get(n, ()) for n in c)
        if not leaves:
            terminal.append(c)
    term_scenes = set().union(*terminal) if terminal else set()
    excs = exceptions_of(ov, 6)
    declared_worlds = set()
    for x in excs:
        r.fail += exception_form_errors(x)
        ws = set(x.get("scope", {}).get("worlds", []))
        declared_worlds |= ws
        inside = {n for n in term_scenes if g.nodes[n]["world"] in ws}
        for w in sorted(ws):
            if not any(g.nodes[n]["world"] == w for n in term_scenes):
                r.fail.append(f"stale exception {x['id']}: world {w} is not part of a terminal component")
            elif any(g.nodes[n]["world"] == w for n in main if n not in term_scenes):
                r.fail.append(f"exception {x['id']} is too wide: world {w} also has scenes that lead on")
        if inside:
            r.exceptions.append(_exc_record(x, len(inside), f"terminal component of {len(inside)} scenes in worlds {', '.join(sorted(ws))}"))
    undeclared = sorted(n for n in term_scenes if g.nodes[n]["world"] not in declared_worlds)
    for n in undeclared:
        r.fail.append(f"{n}: in a terminal component with no way on (no ending) that no exception declares")
    if term_scenes:
        can_term = reaches_target(sorted(term_scenes))
        stuck = sorted(n for n in main if n not in can_term)
        for n in stuck:
            r.fail.append(f"{n}: a mainline scene that cannot reach the terminal component")
    r.data.update({"unreachable": unreachable, "trapped": trapped, "terminal_scenes": sorted(term_scenes), "terminal_components": len(terminal)})
    r.summary = f"{sum(1 for n in g.nodes if not [e for e in g.out.get(n, []) if g.is_choice(e) and e['to'] != n])} scenes without a way out; {len(unreachable)} unreachable; " \
                f"{len(trapped)} trapped in a quest; {len(term_scenes)} scenes in {len(terminal)} terminal component(s)"
    return r


def rule_07(g, ov=None, game=None):
    """Rule 7. Every reference resolves: every edge end is a scene; every route of the game data resolves; every overlay reference (start, locations, worlds, hubs, quests, entries,
    completion scenes, source files, entrances, objects, extra routes, exceptions) resolves against the game data; an `existing` object is a hotspot, a `partial` object names the
    hotspot it copies, a `proposed` object id collides with no hotspot id and is unique; every non-Bassment scene has an entry in `track_scenes.json`."""
    r = Result(7)
    checked = [0]

    def ok(cond, msg):
        checked[0] += 1
        if not cond:
            r.fail.append(msg)
        return cond

    for p in getattr(g, "data_problems", []):
        ok(False, p)
    for p in getattr(g, "build_problems", []):
        ok(False, p)
    for e in g.edges:
        ok(e["from"] in g.nodes and (e["to"] in g.nodes or e["to"] == CHECKPOINT), f"edge {e['via']}: unresolved end")
    for s in game.scene_ids() if game else []:
        ok(s in g.nodes, f"{s}: a scene of the game data is missing from the graph")
    if game:
        reg = game.track_scenes.get("paths", {})
        for n, d in sorted(g.nodes.items()):
            if d.get("quest") == "bassment":
                continue
            path, nid = n.split("/", 1)
            ok(nid in reg.get(path, {}), f"{n}: no entry in content/run/track_scenes.json")
    if ov:
        for k in ov:
            ok(k in TOP_KEYS, f"overlay: unknown top-level key {k}")
        locs = {l["id"]: l for l in ov["locations"]}
        ok(len(locs) == len(ov["locations"]) == 5, "overlay: exactly five locations with unique ids are required")
        ok(len({q["id"] for q in ov["quests"]}) == len(ov["quests"]) == 4 and {q["id"] for q in ov["quests"]} == set(QUEST_IDS), "overlay: exactly the four quests bassment, gospel, squadron, ember")
        hub_ids = {l["hub"] for l in ov["locations"]}
        ok(ov["start"] in hub_ids, f"overlay: start {ov['start']} is not the hub of a location")
        ok(not game or ov["start"] == game.start, f"overlay: start {ov['start']} differs from the start scene of run.json")
        worlds_seen = collections.Counter()
        for l in ov["locations"]:
            for w in l.get("worlds", []):
                worlds_seen[w] += 1
                ok(not game or w in game.main_worlds, f"location {l['id']}: world {w} is not in run.json")
            ok(l["hub"] in g.nodes and g.nodes[l["hub"]]["category"] == "mainline" and g.nodes[l["hub"]]["world"] in l.get("worlds", []),
               f"location {l['id']}: hub {l['hub']} is not a main scene of its worlds")
            for hl in l.get("hub_links", []):
                ok(hl.get("to_location") in locs and locs[hl["to_location"]]["hub"] == hl.get("to"), f"location {l['id']}: hub link to {hl.get('to')} is not the hub of {hl.get('to_location')}")
        for w in (game.main_worlds if game else []):
            ok(worlds_seen[w] == 1, f"world {w} must belong to exactly one location, found {worlds_seen[w]}")
        ends = game.endings() if game else {}
        for q in ov["quests"]:
            qid = q["id"]
            ok(not game or q["entry"] == game.entry_of(qid), f"quest {qid}: entry {q['entry']} differs from the data ({game.entry_of(qid) if game else ''})")
            ok(q["entry"] in g.nodes and g.nodes[q["entry"]].get("quest") == qid, f"quest {qid}: entry {q['entry']} is not a scene of the quest")
            for s in q.get("completion", {}).get("scenes", []):
                ok(s in g.nodes and g.nodes[s].get("quest") == qid, f"quest {qid}: completion scene {s} is not a scene of the quest")
            if game:
                ok(sorted(q.get("completion", {}).get("scenes", [])) == ends.get(qid), f"quest {qid}: completion scenes differ from the ending scenes of the data {ends.get(qid)}")
                ok((game.content.parent / q["scenes_source"]).exists(), f"quest {qid}: scenes_source {q.get('scenes_source')} does not exist")
                mu = q.get("music", {})
                if mu.get("registry"):
                    ok((game.content.parent / mu["registry"]).exists(), f"quest {qid}: music registry {mu['registry']} does not exist")
                    if q["system"] == "path":
                        ok(mu.get("path") in game.track_scenes.get("paths", {}), f"quest {qid}: music path {mu.get('path')} is not in track_scenes.json")
            ok(q.get("system") in ("path", "trial"), f"quest {qid}: system must be path or trial")
            rt = q.get("return", {})
            ok(rt.get("landing") == "checkpoint", f"quest {qid}: return.landing must be checkpoint")
            ok(rt.get("placement") in ("all_scenes", "listed"), f"quest {qid}: return.placement must be all_scenes or listed")
            for s in rt.get("scenes", []) + [o["scene"] for o in rt.get("overrides", [])]:
                ok(s in g.nodes and g.nodes[s].get("quest") == qid, f"quest {qid}: return scene {s} is not a scene of the quest")
            for fb in rt.get("hidden_fallbacks", []):
                ok(fb in HIDDEN_VIA, f"quest {qid}: unknown hidden fallback {fb}")
        pairs = collections.Counter()
        proposed_ids = collections.Counter()
        proposed_where = collections.defaultdict(set)
        hotspot_ids = game.hotspot_ids if game else set()

        def object_check(o, where, scene=None):
            st = o.get("status")
            ok(st in ("existing", "partial", "proposed"), f"{where}: object {o.get('id')} has status {st}")
            if st == "existing":
                ok(o["id"] in hotspot_ids, f"{where}: existing object {o['id']} is not a hotspot id in content/")
            elif st == "partial":
                ok(o.get("copy_of") in hotspot_ids, f"{where}: partial object {o['id']} must name the existing hotspot it copies (copy_of)")
                ok(o["id"] not in hotspot_ids, f"{where}: object {o['id']} collides with a hotspot id")
                proposed_ids[o["id"]] += 1
                proposed_where[o["id"]].add(scene)
            elif st == "proposed":
                ok(o["id"] not in hotspot_ids, f"{where}: proposed object {o['id']} collides with a hotspot id")
                proposed_ids[o["id"]] += 1
                proposed_where[o["id"]].add(scene)

        exc_ids = {x.get("id") for x in ov.get("exceptions", [])}
        for en in ov["entrances"]:
            pairs[(en.get("location"), en.get("quest"))] += 1
            ok(en.get("location") in locs, f"entrance {en.get('id')}: unknown location")
            ok(en.get("id") == f"{en.get('location')}.{en.get('quest')}", f"entrance {en.get('id')}: id must be <location>.<quest>")
            ok(en.get("location") in locs and en.get("scene") == locs[en["location"]]["hub"], f"entrance {en.get('id')}: scene {en.get('scene')} is not the hub of the location")
            object_check(en.get("object", {}), f"entrance {en.get('id')}", en.get("scene"))
            ok(en.get("transition") == "port", f"entrance {en.get('id')}: transition must be port (a legacy entrance is an extra way)")
            ok(en.get("rhythm_gate") is False, f"entrance {en.get('id')}: rhythm_gate must be false (a gated way in is a legacy_way)")
            lw = en.get("legacy_way")
            if lw:
                ok(lw.get("transition") == "legacy_mid_scene" and lw.get("rhythm_gate") is True, f"entrance {en.get('id')}: legacy_way must be a rhythm-gated legacy_mid_scene way")
                ok(lw.get("exception") in exc_ids, f"entrance {en.get('id')}: a legacy_way must name an exception")
                scenes = [en["scene"]] + list(lw.get("also_in", []))
                ok(lw.get("object", {}).get("id") in hotspot_ids, f"entrance {en.get('id')}: legacy_way object {lw.get('object', {}).get('id')} is not a hotspot id")
                for sc in scenes:
                    ok(any(e["from"] == sc and e["kind"] == "quest_entry" and e["quest"] == en["quest"] and e.get("transition") == "legacy_mid_scene" for e in g.edges),
                       f"entrance {en.get('id')}: no legacy entrance to {en['quest']} in {sc} in the data")
        for l in ov["locations"]:
            for q in ov["quests"]:
                ok(pairs[(l["id"], q["id"])] == 1, f"entrances: location {l['id']} and quest {q['id']} must have exactly one entrance, found {pairs[(l['id'], q['id'])]}")
            for hl in l.get("hub_links", []):
                object_check(hl.get("object", {}), f"hub link of {l['id']}", l["hub"])
        for x in ov.get("extra_routes", []):
            ok(x.get("scene") in g.nodes, f"extra route {x.get('object', {}).get('id')}: scene {x.get('scene')} does not exist")
            if x.get("kind") in ("restart", "second_route"):
                ok(x.get("to") in g.nodes, f"extra route {x.get('object', {}).get('id')}: destination {x.get('to')} does not exist")
                ok(x.get("owner_to_confirm") is True, f"extra route {x.get('object', {}).get('id')}: a restart or second route must be flagged owner_to_confirm")
            object_check(x.get("object", {}), f"extra route on {x.get('scene')}", x.get("scene"))
        for rr in ov.get("route_rules", []):
            ok(rr.get("id") in ("to_hub", "back", "return"), f"route rule {rr.get('id')}: reserved id")
            ok(rr.get("applies_to") in ("mainline_non_hub", "path_quest_scenes", "all_quest_scenes"), f"route rule {rr.get('id')}: applies_to {rr.get('applies_to')!r} is not one of the three values")
            ok(rr.get("target") in ("hub_of_location", "previous_scene", "checkpoint"), f"route rule {rr.get('id')}: bad target {rr.get('target')!r}")
        # an object id may be shared only by the placements of one definition (a restart object in the two ending scenes of a quest)
        for oid, n in proposed_ids.items():
            ok(n == 1 or oid.endswith(".restart"), f"proposed object id {oid} is used {n} times")
        seen_ids = set()
        for x in ov.get("exceptions", []):
            ok(x.get("id") not in seen_ids, f"exception {x.get('id')}: duplicate id")
            seen_ids.add(x.get("id"))
            ok(isinstance(x.get("rule"), int) and 1 <= x["rule"] <= 10, f"exception {x.get('id')}: rule must be 1 to 10")
            sc = x.get("scope", {})
            for s in sc.get("scenes", []):
                ok(s in g.nodes, f"exception {x.get('id')}: scene {s} does not exist")
            for o in sc.get("objects", []):
                ok(o in hotspot_ids, f"exception {x.get('id')}: object {o} is not a hotspot id")
            for w in sc.get("worlds", []):
                ok(not game or w in game.main_worlds, f"exception {x.get('id')}: world {w} is not in run.json")
            for en_id in sc.get("entrances", []):
                ok(en_id in {en.get("id") for en in ov["entrances"]}, f"exception {x.get('id')}: entrance {en_id} does not exist")
    r.data["checked"] = checked[0]
    r.summary = f"{checked[0]} references checked, {len(r.fail)} unresolved"
    return r


def rule_08(g, ov=None, game=None):
    """Rule 8. Every non-Bassment scene has a well-formed track assignment in `track_scenes.json` (a `track` id, alternates that each name a track); the Bassment's `music` block
    names its audio and chart (and its fight audio and chart). A track named in the registry without a catalogue file in `content/music/tracks/` is a warning, not a failure,
    until stage I4 has added the catalogue entries."""
    r = Result(8)
    named = set()
    ts = game.track_scenes if game else {}
    bad = 0
    for path, scenes in sorted(ts.get("paths", {}).items()):
        for nid, v in sorted(scenes.items()):
            gid = f"{path}/{nid}"
            ok = isinstance(v, dict) and isinstance(v.get("track"), str) and v["track"]
            alts = v.get("alternates", []) if isinstance(v, dict) else []
            ok = ok and isinstance(alts, list) and all(isinstance(a, dict) and isinstance(a.get("track"), str) and a["track"] for a in alts)
            if not ok:
                bad += 1
                r.fail.append(f"{gid}: malformed track assignment")
                continue
            named.add(v["track"])
            named |= {a["track"] for a in alts}
    music = (game.trial.get("music", {}) if game else {})
    for k in ("audio", "chart", "fight_audio", "fight_chart"):
        if not (isinstance(music.get(k), str) and music[k]):
            r.fail.append(f"bassment: the music block names no {k}")
    if ov:
        for q in ov["quests"]:
            if q.get("system") == "trial":
                for k in ("audio", "fight_audio"):
                    if q.get("music", {}).get(k) != music.get(k):
                        r.fail.append(f"quest {q['id']}: music.{k} {q.get('music', {}).get(k)!r} differs from passages.json {music.get(k)!r}")
    missing = sorted(named - (game.catalogue if game else set()))
    non_bassment = [n for n in g.nodes if g.nodes[n].get("quest") != "bassment"]
    assigned = sum(1 for n in non_bassment if n.split("/", 1)[1] in ts.get("paths", {}).get(n.split("/", 1)[0], {}))
    r.warnings.append(f"{len(missing)} of {len(named)} track ids named in track_scenes.json have no catalogue file in content/music/tracks/ (stage I4 adds them)")
    r.data.update({"assigned": assigned, "non_bassment": len(non_bassment), "named": len(named), "without_catalogue": len(missing), "missing_tracks": missing})
    r.not_checkable.append(f"not checkable from data: that a usable pack exists for each track, beat grids, first-drop times, the music sidecars (packs are outside the repository; checked by the Godot test {GODOT_TEST} with the music stream's validator)")
    r.summary = f"{assigned} of {len(non_bassment)} non-Bassment scenes assigned; {len(named)} track ids named, {len(missing)} without a catalogue file (warning)"
    return r


# ----------------------------------------------------------------------------------------------------------------------------------- model of the route state
class RouteModel:
    """A small model of the specified `RouteState` (NARRATIVE_GRAPH.md section 3) run on the graph: it tests the design, not the code. A request builds a destination and a
    pending change; nothing committed changes until `switched`, from where the player really landed. Rules 9 and 10 run on it."""

    def __init__(self, g):
        self.g = g
        self.limit = int(g.settings.get("history_limit", 32))
        self.ends = {c for q in g.quests for c in q["completion"]}
        self.state = {"node": g.start, "location": g.loc(g.start), "quest": "", "entry_origin": "", "checkpoint": "",
                      "progress": {q["id"]: {"scene": "", "completed": False, "visits": 0} for q in g.quests}, "history": [g.start]}
        self.pending = None
        self.next_id = 1

    def teleport(self, node):
        self.state.update({"node": node, "location": self.g.loc(node), "quest": "", "entry_origin": "", "checkpoint": "", "history": [node]})

    def snapshot(self):
        return json.dumps(self.state, sort_keys=True)

    def options(self):
        s = self.state
        return [e for e in self.g.out.get(s["node"], []) if self.g.is_choice(e) and (e["to"] != CHECKPOINT or s["quest"])]

    def request(self, e):
        s = self.state
        if e["kind"] == "quest_return":
            dest = s["checkpoint"]
        elif e["kind"] == "quest_entry":
            p = s["progress"][e["quest"]]
            dest = p["scene"] if (p["scene"] and not p["completed"]) else self.g.entry_of[e["quest"]]
        else:
            dest = e["to"]
        rid = self.next_id
        self.next_id += 1
        self.pending = {"id": rid, "edge": e, "dest": dest, "from": s["node"]}
        return rid

    def close(self, rid):
        if self.pending and self.pending["id"] == rid:
            self.pending = None

    def switched(self, rid, landed=None):
        p = self.pending
        assert p and p["id"] == rid
        g, s = self.g, self.state
        land = landed or p["dest"]
        node = g.nodes[land]
        if node["category"] == "quest":
            qn = node["quest"]
            if not s["quest"]:  # entering a quest from the mainline scene the request came from
                org = g.loc(p["from"])
                s.update({"quest": qn, "entry_origin": p["from"], "checkpoint": g.hub_of[org], "location": org})
                s["progress"][qn]["visits"] += 1
            s["progress"][qn]["scene"] = land
            if land in self.ends:
                s["progress"][qn]["completed"] = True
        else:
            if s["quest"]:  # a return: the scene left is saved, the quest fields are cleared
                s["progress"][s["quest"]]["scene"] = p["from"]
                s.update({"quest": "", "entry_origin": "", "checkpoint": ""})
            s["location"] = node["location"]
        s["node"] = land
        s["history"] = (s["history"] + [land])[-self.limit:]
        self.pending = None

    def invariants(self):
        s, g, errs = self.state, self.g, []
        if (s["quest"] == "") != (s["entry_origin"] == "") or (s["quest"] == "") != (s["checkpoint"] == ""):
            errs.append("quest, entry_origin and checkpoint are not all empty or all set")
        if s["quest"]:
            org = g.loc(s["entry_origin"])
            if s["checkpoint"] != g.hub_of[org]:
                errs.append("the checkpoint is not the hub of the entry origin's location")
            if s["location"] != org:
                errs.append("the location changed during a quest")
            if g.nodes[s["node"]].get("quest") != s["quest"]:
                errs.append("the current scene is not in the current quest")
        else:
            if g.nodes[s["node"]]["category"] != "mainline":
                errs.append("no quest, but the current scene is a quest scene")
            elif g.loc(s["node"]) != s["location"]:
                errs.append("the location does not match the current scene")
        if len(s["history"]) > self.limit or s["history"][-1] != s["node"]:
            errs.append("the history is not bounded or does not end at the current scene")
        for q, p in s["progress"].items():
            if p["scene"] and g.nodes[p["scene"]].get("quest") != q:
                errs.append(f"the saved scene of {q} belongs to another quest")
        return errs


def has_checkpoint(g):
    return any(e["to"] == CHECKPOINT and e["kind"] == "quest_return" and not e.get("hidden") for e in g.edges)


def random_walk(g, seed, steps=400):
    """One random walk of the model: requests that are closed before the lock (state must not change), failures after the lock (a fallback landing), and ordinary moves.
    Returns (counter, errors)."""
    rnd = random.Random(seed)
    m = RouteModel(g)
    log = collections.Counter()
    for _ in range(steps):
        s = m.state
        opts = m.options()
        if not opts:
            return log, [f"seed {seed}: no option at {s['node']}"]
        e = rnd.choice(opts)
        before = m.snapshot()
        rid = m.request(e)
        x = rnd.random()
        if x < 0.15:
            m.close(rid)
            log["closed"] += 1
            if m.snapshot() != before:
                return log, [f"seed {seed}: a closed request changed the committed state"]
            continue
        if x < 0.20 and e["kind"] == "scene":
            fb = [y for y in opts if y["kind"] == "scene" and y["to"] != CHECKPOINT and y["to"] != e["to"]]
            if fb:
                m.switched(rid, fb[0]["to"])
                log["fallback"] += 1
                errs = m.invariants()
                if errs:
                    return log, [f"seed {seed}: {x_} at {s['node']}" for x_ in errs]
                continue
        m.switched(rid)
        log[e["kind"]] += 1
        errs = m.invariants()
        if errs:
            return log, [f"seed {seed}: {x_} after {e['via']} at {s['node']}" for x_ in errs]
    return log, []


def _quest_path(g, start, goals, qid):
    """Fewest-choice route inside a quest (forward scene edges, item locks ignored) from `start` to any of `goals`: a list of edges, or None."""
    prev = {start: None}
    dq = collections.deque([start])
    while dq:
        n = dq.popleft()
        if n in goals:
            path = []
            while prev[n]:
                e = prev[n]
                path.append(e)
                n = e["from"]
            return path[::-1]
        for e in g.out.get(n, []):
            t = e["to"]
            if e["kind"] != "scene" or e.get("hidden") or e["condition"].get("outcome") in MISS_OUTCOMES or e["condition"].get("previous_scene") \
                    or t in prev or t not in g.nodes or g.nodes[t].get("quest") != qid:
                continue
            prev[t] = e
            dq.append(t)
    return None


def scripted_case(g, qid, loc):
    """Enter the quest from the hub of `loc`, move one scene, return, re-enter (resumes at the scene left), play to an ending, return, re-enter (restarts at the entry,
    `completed` kept). Returns a list of errors."""
    errs = []
    m = RouteModel(g)
    hub = g.hub_of[loc]
    m.teleport(hub)

    def take(e):
        rid = m.request(e)
        m.switched(rid)
        bad = m.invariants()
        errs.extend(f"{qid} from {loc}: {b}" for b in bad)

    def enter():
        es = [e for e in m.options() if e["kind"] == "quest_entry" and e["quest"] == qid and not g.is_gated_entrance(e)]
        if not es:
            errs.append(f"{qid} from {loc}: no ungated entrance in the hub {hub}")
            return False
        take(es[0])
        return True

    def leave():
        rs = [e for e in m.options() if e["kind"] == "quest_return" and e["to"] == CHECKPOINT]
        if not rs:
            errs.append(f"{qid} from {loc}: no visible return in {m.state['node']}")
            return False
        take(rs[0])
        return True

    entry = g.entry_of[qid]
    if not enter():
        return errs
    s = m.state
    if s["node"] != entry or s["quest"] != qid or s["checkpoint"] != hub or s["progress"][qid]["visits"] != 1:
        errs.append(f"{qid} from {loc}: the first entry did not land on {entry} with the checkpoint {hub}")
    nxt = [e for e in m.options() if e["kind"] == "scene" and e["to"] != CHECKPOINT and not e["condition"].get("previous_scene") and e["to"] != s["node"]]
    if nxt:
        take(nxt[0])
    left = m.state["node"]
    if not leave():
        return errs
    s = m.state
    if s["node"] != hub or s["quest"] or s["progress"][qid]["scene"] != left:
        errs.append(f"{qid} from {loc}: the return did not land on {hub} with the scene {left} saved")
    if not enter():
        return errs
    s = m.state
    if s["node"] != left or s["progress"][qid]["visits"] != 2:
        errs.append(f"{qid} from {loc}: the re-entry did not resume at {left} (landed on {s['node']}, visits {s['progress'][qid]['visits']})")
    ends = set(next(q for q in g.quests if q["id"] == qid)["completion"])
    path = _quest_path(g, m.state["node"], ends, qid) if m.state["node"] not in ends else []
    if path is None:
        errs.append(f"{qid} from {loc}: no way to an ending from {m.state['node']}")
        return errs
    for e in path:
        take(e)
    if not m.state["progress"][qid]["completed"]:
        errs.append(f"{qid} from {loc}: the ending was reached but the quest is not completed")
    if not leave():
        return errs
    if not enter():
        return errs
    s = m.state
    if s["node"] != entry or not s["progress"][qid]["completed"] or s["progress"][qid]["visits"] != 3:
        errs.append(f"{qid} from {loc}: after completion the re-entry did not restart at {entry} keeping `completed`")
    return errs


def rule_09(g, ov=None, game=None, walks=200):
    """Rule 9. (a) No group of quest scenes leads only to itself: every cycle inside a quest has a way out along the non-hidden edges (the mainline cycles that cannot be left
    are rule 6's declared terminal component). (b) For each quest and each origin location the scripted case holds: enter from the hub, move one scene, return (lands on the
    hub, the scene left is saved), re-enter (resumes there), play to an ending (completed), return, re-enter (restarts at the entry, `completed` kept). (c) 200 seeded random
    walks with closed and failed requests never get stuck. (b) and (c) run on a model of the route state; a graph with no checkpoint fails."""
    r = Result(9)
    closed = []
    for q in g.quests:
        qs = set(g.quest_scenes(q["id"]))
        adj = collections.defaultdict(set)
        leaves = set()
        for e in g.edges:
            if e["from"] in qs and not e.get("hidden"):
                if e["to"] in qs:
                    adj[e["from"]].add(e["to"])
                else:
                    leaves.add(e["from"])
        for c in strongly_connected(qs, adj):
            cyc = len(c) > 1 or any(n in adj.get(n, ()) for n in c)
            out_of_c = any(t not in c for n in c for t in adj.get(n, ())) or bool(c & leaves)
            if cyc and not out_of_c:
                closed.append(sorted(c))
    for c in closed:
        r.fail.append(f"a cycle that cannot be left: {', '.join(c[:6])}{' ...' if len(c) > 6 else ''}")
    cases = fails = 0
    if not has_checkpoint(g):
        r.fail.append("no route state is possible on this graph: no return lands on a checkpoint, so a return always lands on a fixed scene and a re-entry cannot resume")
        r.data.update({"cases": 0, "case_failures": 0, "walks": 0, "closed_cycles": len(closed), "model": False})
        r.summary = "not modelled: the graph has no checkpoint; " + f"{len(closed)} cycle(s) that cannot be left"
    else:
        for q in g.quests:
            for l in g.locations:
                cases += 1
                errs = scripted_case(g, q["id"], l["id"])
                if errs:
                    fails += 1
                    r.fail += errs[:3]
        walked = collections.Counter()
        stuck = 0
        for seed in range(walks):
            log, errs = random_walk(g, seed)
            walked.update(log)
            if errs and any("no option" in x for x in errs):
                stuck += 1
                r.fail.append(errs[0])
        r.data.update({"cases": cases, "case_failures": fails, "walks": walks, "walk_moves": dict(walked), "closed_cycles": len(closed), "model": True})
        r.summary = f"{cases - fails} of {cases} scripted re-entry cases pass; {walks} random walks ({sum(walked.values())} requests, {walked['closed']} closed, " \
                    f"{walked['fallback']} fallbacks), {stuck} stuck; {len(closed)} cycle(s) that cannot be left"
    r.not_checkable.append(f"not checkable from data: the real RouteState, QuestRouter and director (the model tests the design; checked by the Godot test {GODOT_TEST})")
    return r


def rule_10(g, ov=None, game=None, walks=200):
    """Rule 10. On the model of the route state, after every `switched` the invariants of NARRATIVE_GRAPH.md 3.1 hold (quest, entry origin and checkpoint all empty or all set;
    the checkpoint is the hub of the entry origin's location; the location does not change during a quest; the current scene belongs to the current quest; the history is
    at most `history_limit` and ends at the current scene; a quest's saved scene belongs to that quest); a request closed before the lock leaves the committed state
    byte for byte unchanged; a fallback landing recomputes the change."""
    r = Result(10)
    if not has_checkpoint(g):
        r.fail.append("no route state is possible on this graph: no return lands on a checkpoint")
        r.data.update({"walks": 0, "broken": 0, "model": False})
        r.summary = "not modelled: the graph has no checkpoint"
    else:
        total = collections.Counter()
        broken = 0
        for seed in range(walks):
            log, errs = random_walk(g, seed)
            total.update(log)
            errs = [x for x in errs if "no option" not in x]
            if errs:
                broken += 1
                r.fail.append(errs[0])
        r.data.update({"walks": walks, "walk_moves": dict(total), "broken": broken, "model": True})
        r.summary = f"{walks} random walks, {sum(total.values())} requests ({total['closed']} closed before the lock, {total['fallback']} fallback landings): {broken} walks with a broken invariant"
    r.not_checkable.append(f"not checkable from data: the invariants on the real classes against the mock and the real director (checked by the Godot test {GODOT_TEST})")
    return r


def check_cap(g, ov=None, game=None):
    """Informational check beside the ten rules (rulings 1 and 16): the choices a scene shows (objects that lead somewhere; reactive objects are a separate list and are not
    capped) are at most `hotspot_cap` (8), and in a hub at most `hub_hotspot_cap` (10). The hubs and scenes that need a `max_hotspots` override in run.json are listed."""
    r = Result(0)
    r.title = "Choices shown per scene against the cap (informational check, rulings 1 and 16)"
    cap, hub_cap = _limit(g, "hotspot_cap"), _limit(g, "hub_hotspot_cap")
    over, need_override = [], []
    biggest = (0, "")
    for n, d in sorted(g.nodes.items()):
        k = len(choice_objects(g, n))
        lim = hub_cap if d.get("hub") else cap
        if k > biggest[0]:
            biggest = (k, n)
        if k > lim:
            over.append(f"{n}: {k} choices (cap {lim})")
        node = game.main.get(n.split("/", 1)[1]) if game and n.startswith("main/") else None
        data_cap = int(node.get("max_hotspots", cap)) if node is not None else None  # (a node without max_hotspots has the default cap of 8, ruling 1)
        if d.get("hub") and data_cap is not None and k > data_cap and k <= hub_cap:
            need_override.append((n, k, data_cap))
    r.fail += over
    r.data.update({"biggest": biggest, "need_override": need_override, "cap": cap, "hub_cap": hub_cap,
                   "hubs": {n: len(choice_objects(g, n)) for n, d in g.nodes.items() if d.get("hub")}})
    r.summary = f"most choices in one scene: {biggest[0]} ({biggest[1]}); hubs: " + ", ".join(f"{n.split('/')[1]} {k}" for n, k in sorted(r.data["hubs"].items()))
    return r


RULES = [rule_01, rule_02, rule_03, rule_04, rule_05, rule_06, rule_07, rule_08, rule_09, rule_10]


def validate(g, ov=None, game=None, strict=False):
    """Runs the ten rules (and the informational cap check). Returns the list of results; with `strict` every exception becomes a failure."""
    results = [fn(g, ov, game) for fn in RULES]
    cap = check_cap(g, ov, game)
    results.append(cap)
    if strict:
        for r in results:
            for x in r.exceptions:
                r.fail.append(f"strict: exception {x['id']} ({x['what']})")
    return results


# ------------------------------------------------------------------------------------------------------------------------------------------------- export
def counts_of(g):
    return {"nodes": len(g.nodes), "edges": len(g.edges),
            "edges_by_status": dict(sorted(collections.Counter(e["status"] for e in g.edges).items())),
            "edges_by_kind": dict(sorted(collections.Counter(e["kind"] for e in g.edges).items()))}


def export_graph(g, overlay_name=None):
    """The machine-readable graph: sorted nodes and edges, no dates, so that the same data gives the same bytes."""
    meta = {
        "format": EXPORT_FORMAT,
        "graph": g.kind,
        "generated_by": "tools/narrative/graph.py (do not edit; run the tool)",
        "id_scheme": "<path>/<node>: main/<scene>, gospel/<node>, squadron/<node>, ember/<node>, bassment/<passage>; $checkpoint is the hub of the location a quest was entered from",
        "overlay": overlay_name or "",
        "start": g.start,
        "settings": dict(sorted(g.settings.items())),
        "locations": g.locations,
        "quests": g.quests,
        "counts": counts_of(g),
    }
    nodes = [g.nodes[k] for k in sorted(g.nodes)]
    edges = sorted(g.edges, key=edge_key)
    return {"meta": meta, "nodes": nodes, "edges": edges}


def dumps(obj):
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def write_text(path, text):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def mermaid(g):
    """The graph at location and quest level, as a Mermaid flowchart: mainline routes between locations, hub-to-hub links (dotted), and the quest entrances and returns."""
    lines = ["%% generated by tools/narrative/graph.py (do not edit; run the tool)", f"%% {g.kind} graph: locations and quests", "flowchart LR"]
    lid = {l["id"]: "L" + str(i) for i, l in enumerate(g.locations)}
    qid = {q["id"]: "Q" + str(i) for i, q in enumerate(g.quests)}
    for l in g.locations:
        t = g.nodes[l["hub"]]["title"]
        lines.append(f'  {lid[l["id"]]}["{l["title"]}<br/>hub: {t}"]')
    for q in g.quests:
        lines.append(f'  {qid[q["id"]]}(["{q["title"] or q["id"]}"])')
    lines.append("")
    pairs = collections.defaultdict(set)
    links = set()
    for e in g.edges:
        if e["kind"] != "scene" or e.get("hidden"):
            continue
        a, b = g.nodes[e["from"]], g.nodes[e["to"]] if e["to"] in g.nodes else None
        if b is None or a["category"] != "mainline" or b["category"] != "mainline" or a["location"] == b["location"]:
            continue
        if e.get("link") == "hub_to_hub":
            links.add((a["location"], b["location"]))
        else:
            pairs[(a["location"], b["location"])].add(a["title"])
    for (a, b), titles in sorted(pairs.items()):
        lines.append(f'  {lid[a]} -->|"{", ".join(sorted(titles))}"| {lid[b]}')
    done = set()
    for a, b in sorted(links):
        if (b, a) in done:
            continue
        done.add((a, b))
        two = (b, a) in links
        lines.append(f'  {lid[a]} {"<-.->" if two else "-.->"}|"proposed link"| {lid[b]}')
    lines.append("")
    has_cp = has_checkpoint(g)
    cells = set()
    for e in g.edges:
        if e["kind"] == "quest_entry" and g.nodes[e["from"]]["category"] == "mainline":
            cells.add((g.loc(e["from"]), e["quest"], bool(e.get("rhythm_gate"))))
    seen_cell = set()
    for l, q, gated in sorted(cells):
        if (l, q) in seen_cell:
            continue
        seen_cell.add((l, q))
        arrow = "<-->" if has_cp else "-->"
        lines.append(f"  {lid[l]} {arrow} {qid[q]}")
    if not has_cp:
        fixed = collections.defaultdict(set)
        for e in g.edges:
            if e["kind"] == "quest_return" and not e.get("hidden") and e["to"] in g.nodes:
                fixed[e["quest"]].add(g.loc(e["to"]))
        for q, ls in sorted(fixed.items()):
            for l in sorted(ls):
                lines.append(f'  {qid[q]} -->|"return, fixed landing"| {lid[l]}')
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------------------------------------------------------------------------------------- reports
def summary_counts(results):
    rules = [r for r in results if r.rule]
    return {"pass": sum(r.status == "PASS" for r in rules), "exception": sum(r.status == "EXCEPTION" for r in rules), "fail": sum(r.status == "FAIL" for r in rules),
            "exceptions": sum(len(r.exceptions) for r in rules), "not_checkable": sum(len(r.not_checkable) for r in rules)}


def _short(items, n):
    return list(items[:n]) + ([f"... and {len(items) - n} more"] if len(items) > n else [])


def console_lines(g, results, overlay_name=None, verbose=False):
    c = counts_of(g)
    out = [f"narrative graph ({g.kind}): {c['nodes']} nodes, {c['edges']} edges, " + (f"overlay {overlay_name}" if overlay_name else "no overlay (the game data alone)")]
    for r in results:
        tag = f"RULE {r.rule:02d}" if r.rule else "CHECK CAP"
        out.append(f"{tag} {r.status:<9}  {r.summary}")
        for f in (r.fail if verbose else _short(r.fail, 10)):
            out.append(f"{'':16}fail: {f}")
        for x in r.exceptions:
            out.append(f"{tag} EXCEPTION  {x['id']}: {x['what']}; {x['reason']} Tracked by: {x['tracked_by']}")
        for w in r.warnings:
            out.append(f"{tag} warning    {w}")
        for nc in r.not_checkable:
            out.append(f"{tag} NOT CHECKABLE  {nc}")
    s = summary_counts(results)
    out.append(f"SUMMARY pass {s['pass']}, exception {s['exception']} (declared exceptions {s['exceptions']}), fail {s['fail']}, not checkable from data {s['not_checkable']} part(s)")
    return out


def exit_code(all_results):
    return 1 if any(r.status == "FAIL" for results in all_results for r in results) else 0


def _md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return out


def _rule_section(r, g, detail):
    L = [f"### Rule {r.rule}. {r.title}" if r.rule else f"### Check: {r.title}", ""]
    doc = [fn.__doc__ for fn in RULES if fn.__name__ == f"rule_{r.rule:02d}"] if r.rule else [check_cap.__doc__]
    L += ["Statement: " + " ".join(doc[0].split()), ""]
    L += detail
    if detail:
        L.append("")
    L.append(f"Result: **{r.status}**. {r.summary}")
    if r.fail:
        L += ["", f"Offending ({len(r.fail)}):"]
        L += [f"- {f}" for f in _short(r.fail, 25)]
    for x in r.exceptions:
        L += ["", f"EXCEPTION `{x['id']}`: {x['what']}. {x['reason']} Tracked by: {x['tracked_by']}."]
    for w in r.warnings:
        L += ["", f"Warning: {w}."]
    for nc in r.not_checkable:
        L += ["", f"NOT CHECKABLE: {nc}."]
    L.append("")
    return L


def _details(r, g, game):
    d, L = r.data, []
    if r.rule == 1:
        L += _md_table(["Quest", "Choices, any entrance", "Choices, ungated entrances only", "Counting the hidden leaves too"],
                       [(q["id"], d["all"][q["id"]], d["ungated"][q["id"]] if d["ungated"][q["id"]] is not None else "not reachable", d["with_hidden"][q["id"]]) for q in g.quests])
    elif r.rule == 2:
        L += _md_table(["Location", "Quest", "Entrance in some scene", "Entrance on the hub", "Ungated entrance on the hub"],
                       [(l, q, "yes" if a else "no", "yes" if h else "no", "yes" if u else "no") for l, q, a, h, u in d["cells"]])
        L += ["", f"Worst scene of any location: {d['worst_choices']} ungated choices to a quest (limit {d['limit']}). Mainline exits of each hub:", ""]
        L += _md_table(["Location", "Mainline exits from the hub"], [(l, ", ".join(t)) for l, t in d["exits"].items()])
    elif r.rule == 3:
        L += [f"Quest scenes: {d['scenes']}. With a visible return: {d['with_visible_return']} (on the checkpoint {d['on_checkpoint']}, on a fixed scene {d['fixed_landing_scenes']}). Without: {d['without_visible_return']}. Fixed landings of visible returns: "
              f"{json.dumps(d['fixed_landings'], sort_keys=True)}. Not reachable from the entry: {len(d['unreachable'])}. Hub entrances per quest (origins): {json.dumps(d['origins'], sort_keys=True)}. "
              f"Hidden leaves: {d['hidden_leaves']} (never counted). Authored returns re-pointed: {d['authored_returns']}."]
    elif r.rule == 4:
        L += [f"Reached from `{g.start}`: {d['reached']} of {d['mainline']}.", ""]
        L += _md_table(["Locations in the group", "Scenes"], [(", ".join(c[0]), c[1]) for c in d["components"]])
        L += ["", "A mainline route leads back to the first location." if d["route_back_to_first_location"] else "No mainline route leads back to the first location."]
    elif r.rule == 5:
        L += _md_table(["Group", "Scenes", "Under the minimum", "Fewest choices in the group"], d["table"])
        L += ["", f"Mainline scenes by number of choices: {json.dumps(d['mainline_hist'])}. Bassment passages by number of choices (with the return, if the graph has one): {json.dumps(d['bassment_hist'])}."]
    elif r.rule == 6:
        L += [f"Terminal component: {len(d['terminal_scenes'])} scene(s): {', '.join(d['terminal_scenes'][:10])}."] if d["terminal_scenes"] else ["No terminal component."]
    elif r.rule == 7:
        L += [f"References checked: {d['checked']}."]
    elif r.rule == 8:
        L += [f"Non-Bassment scenes with a track assignment: {d['assigned']} of {d['non_bassment']}. Track ids named: {d['named']}; without a catalogue file: {d['without_catalogue']}."]
    elif r.rule in (9, 10):
        L += [json.dumps({k: v for k, v in d.items()}, sort_keys=True)]
    elif r.rule == 0:
        L += _md_table(["Hub", "Choices shown"], sorted(d["hubs"].items()))
        L += ["", f"Cap {d['cap']}; hub cap {d['hub_cap']}. Hubs that need a `max_hotspots` override in run.json above the node's own limit: " +
              (", ".join(f"{n} ({k} choices, node limit {c})" for n, k, c in d["need_override"]) or "none") + "."]
    return L


def markdown_report(entries, game, command):
    """`entries`: list of (graph, results, overlay_name)."""
    L = ["# Validation report: narrative graph", "",
         "Written by `tools/narrative/graph.py`; do not edit, rerun the tool. This replaces the paper check that was made before the tool existed.", "",
         f"Command: `{command}`", "",
         "Data read: `content/run/run.json`, `content/run/hotspots/*.json`, `content/paths/{gospel,squadron,ember}/run.json` and their hotspot files, `content/trial/passages.json`, "
         "`content/run/track_scenes.json`, `content/music/tracks/*.json`, and for the target graph `content/narrative/graph.json`. Nothing was run in Godot.", "",
         "Counting rule for choices (NARRATIVE_GRAPH.md 2.5): a choice is one touched door, person or object, or the default taken. Automatic scenes, hidden options (pause menu, back key), "
         "miss twins, options that need a flag or an item the player does not have, and staying in the scene are not choices. Rule 1 follows the flags and items the player picks up on the way "
         "(a touch is assumed passed); the other rules use flag-free edges only, which is conservative.", ""]
    for g, results, ov_name in entries:
        c = counts_of(g)
        s = summary_counts(results)
        L += [f"## {'Target' if g.kind == 'target' else 'Today'}: {'game data plus ' + ov_name if ov_name else 'game data alone'}", "",
              f"{c['nodes']} nodes, {c['edges']} edges (by status {json.dumps(c['edges_by_status'])}; by kind {json.dumps(c['edges_by_kind'])}).", ""]
        L += _md_table(["Rule", "What", "Result", "Numbers"], [(f"{r.rule}" if r.rule else "cap", r.title, r.status, r.summary) for r in results])
        L += ["", f"Summary: pass {s['pass']}, exception {s['exception']} ({s['exceptions']} declared exception(s) listed), fail {s['fail']}, "
                  f"parts not checkable from data {s['not_checkable']}.", ""]
        for r in results:
            L += _rule_section(r, g, _details(r, g, game))
    L += ["## Not checkable from data", "",
          "- Rule 5 shows that the distinct destinations exist, not that each is a visible, tappable object of adequate size (the coverage audit, N1.5 and N2.6).",
          f"- Rule 8: packs, beat grids, first-drop times and the music sidecars (the Godot test `{GODOT_TEST}` with the music stream's validator).",
          f"- Rules 9 and 10: the real `RouteState`, `QuestRouter` and director (the Godot test `{GODOT_TEST}`); the tool runs a model of the specified behaviour.",
          "- Timing: the transaction rule (state changes only on `switched`) cannot be shown on a static graph; the port conformance cases and the route tests cover it.", ""]
    return "\n".join(L).rstrip("\n") + "\n"


# ------------------------------------------------------------------------------------------------------------------------------------------------- command line
def prepare(content, overlay_path, want_target=True):
    game = Game(content)
    today = build_today(game)
    today.build_problems = []
    out = {"game": game, "today": today, "overlay": None, "target": None}
    if want_target:
        ov = load_overlay(overlay_path)
        target, problems = build_target(game, ov)
        target.build_problems = problems
        out["overlay"], out["target"] = ov, target
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Narrative graph: build, validate the ten rules, export, report.")
    ap.add_argument("--content", default="content", help="the content folder (default: content)")
    ap.add_argument("--overlay", default="content/narrative/graph.json", help="the overlay file")
    ap.add_argument("--out", default="docs/parallel-development/graph", help="folder of the exports")
    ap.add_argument("--graph", choices=("target", "today", "both"), default="target", help="which graph to validate (default: target)")
    ap.add_argument("--strict", action="store_true", help="every exception counts as a failure")
    ap.add_argument("--export", action="store_true", help="write narrative_graph.json, narrative_graph_target.json, narrative_graph.mmd and graph_today.json to --out")
    ap.add_argument("--report", metavar="FILE", help="write the Markdown report (both graphs) to FILE")
    ap.add_argument("--verbose", action="store_true", help="list every offender")
    a = ap.parse_args(argv)
    try:
        need_target = a.graph in ("target", "both") or a.export or bool(a.report)
        d = prepare(a.content, a.overlay, need_target)
        game = d["game"]
        results, entries = {}, []
        names = {"today": None, "target": a.overlay}
        todo = ["today", "target"] if (a.graph == "both" or a.report) else [a.graph]
        for k in todo:
            g = d[k]
            results[k] = validate(g, d["overlay"] if k == "target" else None, game, strict=a.strict)
            entries.append((g, results[k], names[k]))
        shown = [k for k in (["today", "target"] if a.graph == "both" else [a.graph])]
        for k in shown:
            print("\n".join(console_lines(d[k], results[k], names[k], a.verbose)))
            if len(shown) > 1:
                print()
        if a.export:
            out = Path(a.out)
            text = dumps(export_graph(d["target"], a.overlay.replace("\\", "/")))
            write_text(out / "narrative_graph.json", text)
            write_text(out / "narrative_graph_target.json", text)
            write_text(out / "narrative_graph.mmd", mermaid(d["target"]))
            write_text(out / "graph_today.json", dumps(export_graph(d["today"])))
            print(f"exported to {out}")
        if a.report:
            cmd = "python tools/narrative/graph.py --graph both --export --report " + a.report
            write_text(a.report, markdown_report([e for e in entries if e[0].kind == "today"] + [e for e in entries if e[0].kind == "target"], game, cmd))
            print(f"report written to {a.report}")
        return exit_code([results[k] for k in shown])
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
