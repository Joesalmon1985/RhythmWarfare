"""The choice-clarity audit tables (docs/CHOICE_CLARITY.md section 1).

    godot --headless --path . -s tools/run/choice_audit.gd -- all | grep '^AUDIT' > audit.jsonl
    python tools/run/choice_audit.py audit.jsonl > tables.md

For every scene of the main run and the paths: its options (hotspot id, kind, anchor, window, conditions), the default, and what the player can see of each option TODAY,
measured from the camera the player really has (perfect play, no taps) at beats 4 (the scene's start), 50 and 56 (the route window): on screen and how tall, or only an edge
beacon. The Bassment's 63 passages are grouped by the shape of their choice, from the data (content/trial/hotspots.json).

Option verdict: CLEAR = a person or a thing of the map, on screen in the window, at least 40 px tall for a person; UNCLEAR = on screen but only a light on an empty spot or a
doorway point (no object to read), or a person under 40 px; INVISIBLE = an edge beacon at both window beats, or an anchor that does not resolve. The scene's verdict is the worst
of its options at the start of the window. Separately: whether the CURRENT choice (the default before a touch) is shown by anything but a brighter ring: today never.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RUNS = {"main": ("content/run/run.json", "content/run/hotspots"), "gospel": ("content/paths/gospel/run.json", "content/paths/gospel/hotspots"),
        "squadron": ("content/paths/squadron/run.json", "content/paths/squadron/hotspots"), "ember": ("content/paths/ember/run.json", "content/paths/ember/hotspots")}
TITLES = {"main": "The main 174 BPM run", "gospel": "The Life of Jesus (Gospel)", "squadron": "The Mission Count (Squadron)", "ember": "The Ember Road"}
RANK = {"clear": 0, "unclear": 1, "invisible": 2}


def load(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as fh:
        return json.load(fh)


def hotspots(run: str) -> dict:
    out = defaultdict(list)
    d = os.path.join(ROOT, RUNS[run][1])
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            for h in load(os.path.join(RUNS[run][1], fn))["hotspots"]:
                out[str(h["scene"])].append(h)
    return out


def anchor_s(h) -> str:
    (k, v), = h["anchor"].items()
    if k == "pos":
        return "pos (empty spot)"
    return "%s %s" % (k, v)


def window(h) -> str:
    r = str(h.get("on_success", {}).get("route", ""))
    return "early" if (r.startswith("trial:") or r.isdigit()) else "final"


def seen(m: dict | None, h: dict) -> tuple:
    """(verdict, words) for one option at one beat's measurement."""
    if not m or not m.get("resolved"):
        return "invisible", "anchor does not resolve"
    k = next(iter(h["anchor"]))
    actor = "actor" in h["anchor"] or bool((h.get("acting") or {}).get("actor"))
    if m.get("edge"):
        return "invisible", "edge beacon only"
    tall = float(m.get("px_per_m", 0)) * (1.7 if actor or k == "thing" else 1.0)
    if actor and m.get("actor_present") is False:
        return "invisible", "person not in the room"
    if actor:
        v = "clear" if tall >= 40 else "unclear"
        return v, "person on screen, %d px tall%s" % (tall, "" if h.get("acting") else ", waves only (no acting)")
    if k == "thing":
        return "clear", "thing on screen (%d px)" % tall
    if h["kind"] == "exit":
        return "unclear", "doorway point: a light, no door object"
    return "unclear", "a light on an empty spot"


def scene_rows(run: str, audit: dict):
    rj = load(RUNS[run][0])
    hs = hotspots(run)
    rows = []
    for n in rj["nodes"]:
        sid = str(n["id"])
        lst = hs.get(sid, [])
        a = audit.get((run, sid), {}).get("at", {})
        anchors = Counter(json.dumps(h["anchor"], sort_keys=True) for h in lst)
        opts, worst, notes = [], "clear", set()
        for h in lst:
            verdicts = []
            for beat in ("50.0", "56.0"):
                verdicts.append(seen(a.get(beat, {}).get("hotspots", {}).get(h["id"]), h))
            best = min(verdicts, key=lambda v: RANK[v[0]])
            start = seen(a.get("4.0", {}).get("hotspots", {}).get(h["id"]), h)
            cond = []
            av = h.get("available", {})
            if av.get("flags_all"):
                cond.append("needs " + ",".join(av["flags_all"]))
            if av.get("flags_none"):
                cond.append("not " + ",".join(av["flags_none"]))
            if av.get("once"):
                cond.append("once")
            w = window(h)
            if w == "early":
                notes.add("early-window option (blocks 1-2) is never on show together with the others")
            if anchors[json.dumps(h["anchor"], sort_keys=True)] > 1:
                notes.add("two options share one anchor (%s)" % anchor_s(h))
            rt = str(h.get("on_success", {}).get("route", "")) or "(stays, then default)"
            opts.append({"id": h["id"], "kind": h["kind"], "anchor": anchor_s(h), "default": bool(h.get("default")), "window": w, "cond": "; ".join(cond), "route": rt,
                         "window_seen": best, "start_seen": start, "acting": bool(h.get("acting"))})
            if not av.get("flags_all") and RANK[best[0]] > RANK[worst]:
                worst = best[0]
        rows.append({"run": run, "scene": sid, "title": n.get("title", ""), "opts": opts, "verdict": worst, "notes": sorted(notes)})
    return rows


def md_scene_table(rows) -> str:
    out = ["| Scene | Options: id (kind, anchor) -> route; [D] default; conditions | What the player sees in the window (beats 50/56) | At the scene's start (beat 4) | Verdict |",
           "| --- | --- | --- | --- | --- |"]
    for r in rows:
        o1 = "<br>".join("%s`%s` (%s, %s) -> %s%s%s" % ("[D] " if o["default"] else "", o["id"].split(".", 1)[-1] if "." in o["id"] else o["id"], o["kind"], o["anchor"], o["route"],
                                                   " *(early)*" if o["window"] == "early" else "", "; " + o["cond"] if o["cond"] else "") for o in r["opts"])
        o2 = "<br>".join("%s: %s" % (o["window_seen"][0].upper(), o["window_seen"][1]) for o in r["opts"])
        o3 = "<br>".join(o["start_seen"][1] for o in r["opts"])
        v = "**%s**" % r["verdict"].upper() + ("<br>" + "<br>".join(r["notes"]) if r["notes"] else "")
        out.append("| `%s` %s | %s | %s | %s | %s |" % (r["scene"], r["title"], o1, o2, o3, v))
    return "\n".join(out)


def bassment_groups() -> str:
    d = load("content/trial/hotspots.json")
    by = defaultdict(list)
    for h in d["hotspots"]:
        by[str(h["scene"])].append(h)
    groups = defaultdict(list)
    for p, lst in by.items():
        shape = " + ".join(sorted("%s%s" % (h["kind"], "(D)" if h.get("default") else "") for h in lst))
        groups[shape].append(p)
    out = ["| Choice shape (kinds, (D) the default) | Passages | What the player sees today | Verdict |", "| --- | --- | --- | --- |"]
    for shape, ps in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        n_exit = shape.count("exit")
        if n_exit == len(shape.split(" + ")) and n_exit >= 2:
            seen_, v = "two or more lit doorway points on waypoints, no door; the default ring brighter", "UNCLEAR (exits read only as light, nothing says which is current)"
        elif n_exit == 1 and len(shape.split(" + ")) == 1:
            seen_, v = "a single way on (no choice: the window only times the walk)", "n/a (not a branching point)"
        elif "encounter" in shape:
            seen_, v = "a creature billboard stands in the room (acts: block/offer/laugh...) beside lit doorway points", "UNCLEAR (the creature is visible; the other way is a light; current = brighter ring only)"
        else:
            seen_, v = "an item or a feature glows on an empty spot or a thing beside lit doorway points", "UNCLEAR"
        out.append("| %s | %s | %s | %s |" % (shape, ", ".join(sorted(ps, key=lambda s: int(s) if s.isdigit() else 999)), seen_, v))
    return "\n".join(out)


def main() -> int:
    audit = {}
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("AUDIT "):
                line = line[6:]
            line = line.strip()
            if line:
                j = json.loads(line)
                audit[(j["run"], j["scene"])] = j
    total = Counter()
    for run in RUNS:
        rows = scene_rows(run, audit)
        c = Counter(r["verdict"] for r in rows)
        total.update(c)
        print("### %s (%d scenes: %d clear, %d unclear, %d invisible)\n" % (TITLES[run], len(rows), c["clear"], c["unclear"], c["invisible"]))
        print(md_scene_table(rows))
        print()
    print("### The Bassment (63 passages, %s)\n" % "grouped by the shape of their choice; from the data and docs/shots/trial")
    print(bassment_groups())
    print()
    print("TOTAL %s" % dict(total), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
