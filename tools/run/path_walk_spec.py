#!/usr/bin/env python3
"""The walks of a path for tools/run/walk_run.sh --path <id>: prints `bot|routes|until_phase|start scene|expected scenes` for one walk, or the names of the walks.

    python3 tools/run/path_walk_spec.py <path> names        # perfect sloppy none (+ the names in content/paths/<path>/walks.json)
    python3 tools/run/path_walk_spec.py <path> <name>

Default walks: `perfect` follows every scene's default route to the first ending and on through the way back into the Warehouse (one phase of it is played); `sloppy` and `none` only check that every step
is a route of the scene before it and the saves are right. A path with branches adds walks that take them in content/paths/<path>/walks.json: {"<name>": {"bot": "perfect", "routes": "right,,up", "until": 5,
"start": "", "expect": "a,b,c" or "-"}} (routes: one direction per phase; the bot taps the hotspot that leads that way).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(argv):
    pid, what = argv[1], argv[2]
    d = ROOT / "content/paths" / pid
    run = json.loads((d / "run.json").read_text(encoding="utf-8"))
    extra = json.loads((d / "walks.json").read_text(encoding="utf-8")) if (d / "walks.json").exists() else {}
    if what == "names":
        print(" ".join(["perfect", "sloppy", "none"] + [k for k in extra if k not in ("perfect", "sloppy", "none")]))
        return 0
    nodes = {n["id"]: n for n in run["nodes"]}
    seq, cur = [], run["start_node"]
    while cur in nodes and cur not in seq:  # the default walk: first route of every scene
        seq.append(cur)
        cur = nodes[cur]["next"][0]["to"]
    seq.append("warehouse")  # the ending's way back
    walks = {"perfect": {"bot": "perfect", "routes": "", "until": len(seq) - 1, "start": "", "expect": ",".join(seq)},
             "sloppy": {"bot": "accuracy:0.55", "routes": "", "until": 3, "start": "", "expect": "-"},
             "none": {"bot": "none", "routes": "", "until": 3, "start": "", "expect": "-"}}
    walks.update(extra)
    w = walks[what]
    print("|".join([w["bot"], w["routes"], str(w["until"]), w["start"], w["expect"]]))
    return 0


sys.exit(main(sys.argv))
