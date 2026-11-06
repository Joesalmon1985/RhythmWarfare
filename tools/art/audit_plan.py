#!/usr/bin/env python3
"""The shot plan of the art audit (docs/art/VISUAL_AUDIT.md): one Godot launch per scene, several frames per launch.

    python tools/art/audit_plan.py [main|gospel|squadron|ember|all] [--rate 0.25]

Prints one line per launch:  <path or -> <scene id> <tag> <frame>:shot:<name> ...
Each launch starts the scene (RW_RUN_START) on the virtual clock with the perfect bot and the default exits, and shoots:
  a24   beat 24 of the first lap (the camera has walked in)
  mid   beat 40 of the last lap
  win   beat 54 of the last lap (the hotspot window, nothing touched)
  end   0.25 s before the scene's last downbeat (the last moment of the scene)
  nx0   0.3 s after it (the first moment of the next scene: the join)
  nx3   3 s after it
A frame f shows song time (f - 2) * rate - 2 (the 2 s countdown; tools/run/capture.sh uses the same formula).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load(which):
    if which == "main":
        return json.load(open(os.path.join(ROOT, "content/run/run.json"), encoding="utf-8")), 1
    r = json.load(open(os.path.join(ROOT, "content/paths", which, "run.json"), encoding="utf-8"))
    return r, int(r.get("path", {}).get("laps", 1))


def plan(which, rate):
    r, default_laps = load(which)
    bpm = float(r["timing"]["bpm"])
    pb = int(r["timing"]["phase_beats"])
    b = 60.0 / bpm
    for n in r["nodes"]:
        laps = int(n.get("laps", default_laps))
        p = pb * laps * b
        last = pb * (laps - 1) * b
        times = [("a24", 24 * b), ("mid", last + 40 * b), ("win", last + 54 * b), ("end", p - 0.25), ("nx0", p + 0.3), ("nx3", p + 3.0)]
        sid = n["id"].replace(".", "_")
        pre = "" if which == "main" else which + "__"
        steps = []
        for tag, t in times:
            f = int(round((t + 2.0) / rate)) + 2
            steps.append("%d:shot:%s%s__%s" % (f, pre, sid, tag))
        print("-" if which == "main" else which, n["id"], " ".join(steps))


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    rate = float(sys.argv[sys.argv.index("--rate") + 1]) if "--rate" in sys.argv else 0.25
    for w in (["main", "gospel", "squadron", "ember"] if which == "all" else [which]):
        plan(w, rate)
