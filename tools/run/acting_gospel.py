#!/usr/bin/env python3
"""The acting shots of the Gospel path (Stage 3): every hotspot of content/paths/gospel that directs a person, in its five states (available, selected, committed, success, failure), the person framed at
about twice the usual size, into docs/shots/acting/gospel_<hotspot>.jpg (a strip) and docs/shots/acting/gospel_contact_acting.jpg (all strips). The same method as `tools/run/capture.sh --acting`
(RW_STORY_CAM=actor:<id>:<m>:<pitch>, RW_RUN_SELECT=<hotspot>@52, RW_RUN_CLEAN=1) at the path's tempo.

    python3 tools/run/acting_gospel.py [out dir]            GODOT=<console binary>   ONLY=<regex on the hotspot id>   (needs a display; one minute per hotspot)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import contact_acting  # noqa: E402

GODOT = os.environ.get("GODOT") or str(Path(os.environ.get("USERPROFILE", "~")) / "Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe")
RATE = 0.25
BEAT = 60.0 / 124.0
DIST, PITCH = 2.4, -7.0


def frames_of(beat: float) -> int:
    return int((beat * BEAT + 2.0) / RATE) + 2


def run(hid: str, scene: str, flags: str, cam: str, bot: str, shots: list, raw: Path, tmp: Path) -> None:
    name = hid.replace(".", "_")
    steps = [f"{frames_of(b)}:shot:gospel_{name}__{st}" for b, st in shots]
    env = dict(os.environ, XDG_DATA_HOME=str(tmp / "data"), APPDATA=str(tmp / "data"), RW_RUN_VIRTUAL="1", RW_STORY_RATE=str(RATE), RW_RUN_PATH="gospel", RW_RUN_START=scene, RW_RUN_BOT=bot,
               RW_RUN_ROUTES="", RW_RUN_CLEAN="1", RW_STORY_CAM=cam, RW_RUN_SELECT=f"{hid}@52")
    if flags:
        env["RW_RUN_FLAGS"] = flags
    subprocess.run([GODOT, "--path", str(ROOT), "-s", "tools/shoot.gd", "--", "res://src/run/run_play.tscn", str(raw)] + steps, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True)


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/shots/acting"
    only = os.environ.get("ONLY", "")
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for fn in sorted((ROOT / "content/paths/gospel/hotspots").glob("*.json")):
        doc = json.loads(fn.read_text(encoding="utf-8"))
        for h in doc["hotspots"]:
            a = h.get("acting")
            if not a:
                continue
            actor = a.get("actor") or (h.get("anchor") or {}).get("actor")
            if actor and (not only or re.search(only, h["id"])):
                rows.append((h["id"], h["scene"], actor, ",".join(h["available"].get("flags_all", [])), f"actor:{actor}:{DIST}:{PITCH}"))
    strips = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        raw = tmp / "raw"
        raw.mkdir()
        for hid, scene, actor, flags, cam in rows:
            print("acting", hid, actor, flush=True)
            run(hid, scene, flags, cam, "perfect", [(50.5, "available"), (56, "selected"), (61.0, "committed"), (62.6, "success")], raw, tmp)
            run(hid, scene, flags, cam, "blocks:1110", [(62.6, "failure")], raw, tmp)
            # the stitcher names panels <name>__<state>.png
            name = "gospel_" + hid.replace(".", "_")
            im = contact_acting.strip(raw, name, f"{hid} ({actor})")
            if im is not None:
                im.save(out / f"{name}.jpg", quality=80)
                strips.append(im)
    if strips:
        sheet = Image.new("RGB", (strips[0].width, sum(i.height for i in strips)), (14, 10, 22))
        y = 0
        for i in strips:
            sheet.paste(i, (0, y))
            y += i.height
        sheet.save(out / "gospel_contact_acting.jpg", quality=75)
        print("wrote", len(strips), "strips and the contact sheet into", out)


if __name__ == "__main__":
    main()
