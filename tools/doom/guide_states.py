#!/usr/bin/env python3
"""The guide-state captures of a Doom scene (round 2 brief, "Additions from the independent review"; docs/briefs/DOOM_WORLDS_BRIEF.md section 8: "a selected-choice state"),
shot on the real run scene with the bot playing perfectly:

  * state_selected   the guide touched BEFORE the window opens (RW_CHOICE_PRESELECT=1, RW_RUN_SELECT=<hotspot>@44), shot at phase beat 47: the guide's selected sprite;
  * state_committed  the guide tapped IN the window (RW_RUN_SELECT=<hotspot>@50: ruling 39, a geography guide's tap commits at its beat), shot at beat 51.5: the committed sprite;
  * state_walk       the same tap without the camera override, shot at beat 52.5: the first frame of the walk-off along the route.

The first two stand the drawn camera at the scene's reference viewpoint (RW_STORY_CAM=<ref>; the hotspots follow it) because in a scene's FIRST phase the rail is still on its stay
loop when the window opens (the loop's three reveals take the opening bars; see the scene docs): the frames show what the player sees from the choice viewpoint in a later phase.

    import guide_states; rows = guide_states.shoot(scene, ref_waypoint, hotspot_id, tmp)      (tools/doom/shoot_dock.py, shoot_balcony.py, shoot_booth.py)

Returns [(name, PIL image)] at 16:9 (1280 x 720). RW_KEEP keeps them full size (state_*.jpg: no _16x9 suffix, so frame_check measures only the eight rail shots).
"""
import os

from PIL import Image

import shoot_scene as ss

RATE = 0.5
BPM = 174.0
NOISE = ("RID allocations", "leaked", "still in use", "ObjectDB", "WASAPI", "ERR_CANT_OPEN")


def frame_of(beat):
    return int(round((beat * 60.0 / BPM + 2.0) / RATE)) + 2


def _run(scene, tmp, name, beat, extra, res):
    env = {"XDG_DATA_HOME": tmp + "/data", "APPDATA": tmp + "/data", "RW_DOOM_WORLDS": "1", "RW_RUN_VIRTUAL": "1", "RW_STORY_RATE": str(RATE), "RW_RUN_START": scene,
           "RW_RUN_BOT": "perfect", "RW_RUN_ROUTES": ""}
    env.update(extra)
    text = ss.godot(["--path", ss.ROOT, "--resolution", res, "-s", "tools/shoot.gd", "--", "res://src/run/run_play.tscn", tmp, "%d:shot:%s" % (frame_of(beat), name)], env)
    for ln in text.splitlines():
        if ("ERROR" in ln or "SCRIPT" in ln) and not any(k in ln for k in NOISE):
            print("  ", ln)
    p = os.path.join(tmp, name + ".png")
    return Image.open(p).convert("RGB") if os.path.exists(p) else None


def shoot(scene, ref, hotspot, tmp, res="1280x720"):
    plan = [("state_selected", 47.0, {"RW_CHOICE_PRESELECT": "1", "RW_RUN_SELECT": "%s@44" % hotspot, "RW_STORY_CAM": ref}),
            ("state_committed", 51.5, {"RW_RUN_SELECT": "%s@50" % hotspot, "RW_STORY_CAM": ref}),
            ("state_walk", 52.5, {"RW_RUN_SELECT": "%s@50" % hotspot})]
    out = []
    for name, beat, extra in plan:
        im = _run(scene, tmp, name, beat, extra, res)
        if im is None:
            continue
        out.append((name, im))
        if os.environ.get("RW_KEEP"):
            os.makedirs(os.environ["RW_KEEP"], exist_ok=True)
            im.save(os.path.join(os.environ["RW_KEEP"], "%s.jpg" % name), quality=92)
    return out
