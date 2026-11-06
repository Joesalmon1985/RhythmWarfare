"""The Bassment's rows of docs/VISUAL_COVERAGE.md (not a world table of the run: the Bassment's hotspots are made by tools/trial/make_hotspots.py into content/trial/hotspots.json).

`python tools/run/make_hotspots.py` calls bassment_section() when it writes the coverage doc. Nothing here writes a content/run/hotspots/ file.
"""
from __future__ import annotations

import json

from hotspots_common import ROOT


def bassment_section() -> list:
    """The Bassment's rows (content/trial/hotspots.json, written by tools/trial/make_hotspots.py): S = the choice's passage, F = what TrialFlow does with a miss."""
    hs = json.loads((ROOT / "content/trial/hotspots.json").read_text(encoding="utf-8"))["hotspots"]
    ps = json.loads((ROOT / "content/trial/passages.json").read_text(encoding="utf-8"))["passages"]
    def title(n):
        return "leave the dungeon" if str(n) == "exit" else "passage %s, %s" % (n, ps[str(n)]["title"])
    out = ["", "## The Bassment (workstream D, drawn by the same HotspotView)", "",
           "63 passages and the defeat passage, %d hotspots. Status `verified` = in the data (`check_maps.gd`, `tests/test_trial.gd`), wired in `TrialScene`, walked (`tools/trial/walk_trial.sh`: defaults and taps) and every passage's targets tapped from where the camera stands." % len(hs), "",
           "| Passage | Hotspot | Kind | S outcome | F outcome | Needs | Status |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for h in hs:
        n = int(h["scene"])
        succ = title(h["on_success"]["route"])
        f = h.get("on_failure")
        k = h["trial_kind"]
        if f is None:
            fail = "holds the place and becomes the default" if h["challenge"] else "-"
        elif "route" in f:
            fail = "luck miss: " + title(f["route"])
        else:
            fail = "lost fight: counts toward three, the retry is the default" if k == "encounter" else "holds the place"
        need = ", ".join(h["available"]["flags_all"]) or "always"
        dflt = " (default)" if h["default"] else ""
        out.append("| %d %s | %s%s | %s | %s | %s | %s | verified |" % (n, ps[str(n)]["title"], h["id"].split(".", 1)[1], dflt, k, succ, fail, need))
    out.append("")
    return out
