"""Two laps per path scene (docs/CONTINUOUS_RUN.md "Two laps", docs/HANDOVER.md A12).

A path's generator (tools/content/make_gospel.py, tools/paths/make_squadron.py, tools/run/make_ember.py) authors every scene for ONE 64-beat phase: its `cast` lines name beats 0 to 63. This module is the
last step of those generators: `finish_run(run, laps, single)` sets `path.laps` (the default of every scene of the path), gives the scenes that stay at one lap an explicit `"laps": 1`, and re-times the
`cast` lines of the scenes that play more, so the tables keep their one-phase beats and the data carries the stretched ones.

Re-timing rule (a scene that plays `laps` laps), per cast line at `at_beat` b:

* b < 48 (blocks 1 to 3 of the single phase): the story is spread over the laps, b * laps. The block boundaries 0, 16, 32 become 0, 32, 64 (laps = 2). A line that holds for 12 beats or more
  (`beats` >= 12, i.e. "until the next beat of the story") holds laps times as long, so the person stays in the act until the next line takes over.
* b >= 48 (the last block: the choice window, the commit and the reactions to it, beats 61 to 63): the line keeps its place in the LAST lap, b + 64 * (laps - 1), so the hotspot window, the commit and
  every reaction to it (conditional on the flags the outcome sets) play exactly as in a single phase.

Nothing is added and nothing is removed: the same lines, the same acts and faces, only later. A scene with `laps` 1 is returned unchanged.

    python3 tools/run/laps.py content/paths/gospel/run.json     # prints the laps and the cast of each scene (a check, writes nothing)
"""
from __future__ import annotations

import json
import sys

LAP_BEATS = 64
FINAL_BLOCK = 48  # first beat of the last block of a lap: the lines from here on keep their place in the last lap
HOLD_SCALED = 12  # a line that holds this many beats or more is stretched with the story
KEY_ORDER = ["schema", "path", "timing", "mix", "stages", "start_node", "worlds", "nodes", "cinematics"]


def retime_beat(b: float, laps: int) -> float:
    """The cast beat of a single-phase scene, in a scene of `laps` laps."""
    if laps <= 1:
        return b
    nb = b * laps if b < FINAL_BLOCK else b + LAP_BEATS * (laps - 1)
    return int(nb) if float(nb).is_integer() else nb


def retime_line(line: dict, laps: int) -> dict:
    out = dict(line)
    b = float(line["at_beat"])
    out["at_beat"] = retime_beat(b, laps)
    if laps > 1 and b < FINAL_BLOCK and "beats" in line and float(line["beats"]) >= HOLD_SCALED:
        nb = min(float(line["beats"]) * laps, float(LAP_BEATS))
        out["beats"] = int(nb) if nb.is_integer() else nb
    return out


def retime_cast(cast: list, laps: int) -> list:
    return [retime_line(c, laps) for c in cast]


def finish_run(run: dict, laps: int = 2, single: tuple | list | set = ()) -> dict:
    """Sets path.laps, the exceptions' `laps: 1` and re-times the cast of the scenes that play several laps; returns the run in the canonical key order."""
    single = set(single)
    ids = {n["id"] for n in run["nodes"]}
    unknown = single - ids
    if unknown:
        raise SystemExit("laps: unknown single-lap scene(s) %s" % ", ".join(sorted(unknown)))
    run["path"]["laps"] = laps
    nodes = []
    for n in run["nodes"]:
        n = dict(n)
        n_laps = 1 if n["id"] in single else laps
        if n["id"] in single and laps != 1:
            out: dict = {}
            for k, v in n.items():
                out[k] = v
                if k == "blurb":
                    out["laps"] = 1
            if "laps" not in out:
                out["laps"] = 1
            n = out
        if n_laps > 1 and n.get("cast"):
            n["cast"] = retime_cast(n["cast"], n_laps)
        nodes.append(n)
    run["nodes"] = nodes
    ordered = {k: run[k] for k in KEY_ORDER if k in run}
    ordered.update({k: v for k, v in run.items() if k not in ordered})
    return ordered


def describe(path: str) -> None:
    run = json.load(open(path, encoding="utf-8"))
    default = int(run["path"].get("laps", 1))
    print("%s: path.laps %d" % (path, default))
    for n in run["nodes"]:
        laps = int(n.get("laps", default))
        beats = sorted({float(c["at_beat"]) for c in n.get("cast", [])})
        print("  %-24s laps %d  cast beats %s" % (n["id"], laps, ", ".join(("%g" % b) for b in beats)))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        describe(p)
