#!/usr/bin/env python3
"""The framing of the acting shots (tools/run/capture.sh --acting): one line per character hotspot that directs a person,

    <hotspot id> <scene id> <actor id> <flags csv or -> <RW_STORY_CAM value>

The camera stands DIST metres from the person (wherever they are standing at that moment, StoryStage `RW_STORY_CAM=actor:<id>:<metres>:<pitch>`), on the side the scene's own camera stands, facing them,
so the person fills the picture at about twice the size of an ordinary view. `flags` are the world-state flags the hotspot needs to be on show (RW_RUN_FLAGS).

    python3 tools/run/acting_frames.py                 # every one
    python3 tools/run/acting_frames.py --list          # ids only
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = 2.4
PITCH = -7.0


def frames() -> list[tuple]:
    out = []
    for fn in sorted((ROOT / "content/run/hotspots").glob("*.json")):
        doc = json.loads(fn.read_text(encoding="utf-8"))
        for h in doc["hotspots"]:
            a = h.get("acting")
            if not a:
                continue
            actor = a.get("actor") or (h.get("anchor") or {}).get("actor")
            if not actor:
                continue
            flags = ",".join(h["available"].get("flags_all", [])) or "-"
            out.append((doc["world"], h["id"], h["scene"], actor, flags, "actor:%s:%.1f:%.1f" % (actor, DIST, PITCH)))
    return out


if __name__ == "__main__":
    for row in frames():
        print(" ".join(row) if "--list" not in sys.argv else row[1])
