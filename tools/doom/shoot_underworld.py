#!/usr/bin/env python3
"""Shots of the Underworld (docs/doom/scenes/underworld.md): the reference viewpoint beside the painting, the reveal holds, the three route thresholds and the arrival at 16:9 (1280x720) and 20:9
(1600x720), written as ONE contact sheet (docs/shots/doom/underworld/contact.jpg, under 1 MB) and one walk strip of the three routes (walk_strip.jpg). No per-frame dump is kept.

    python3 tools/doom/shoot_underworld.py [out_dir]            default out_dir docs/shots/doom/underworld     (needs a window: the real run scene, like tools/doom/shoot_scene.sh)
    RW_SHOTS=<regex> only the shots whose name matches.   RW_KEEP=<dir> also keeps each full-size shot there (for frame_check.py; do not commit them).

The camera poses of the walks come from tools/doom/walk_underworld.gd (the polyline moves of the underworld's rail, the eye's real height); each pose is shot on the real run scene (RW_STORY_CAM=@x:z:yaw:pitch:eye).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shoot_scene as ss  # noqa: E402

ROOT = ss.ROOT
SCENE = "doom_underworld"
PAINTING = os.path.join(ROOT, "art", "reference", "doom_worlds", "Three Paths Across the Basalt Abyss-4.png")
SHOTS = [("ref", "uw_ref,0,-14"), ("hold_ledge", "uw_ledge_view"), ("hold_cave", "uw_cave_view"), ("hold_stair", "uw_stair_view"), ("route_ahead", "uw_gate"), ("route_left", "uw_cave_in"),
         ("route_right", "uw_shelf_end"), ("arrive", "uw_arrive")]  # (round 2: `ref` is the run's own choice hold, pitched -14 (the rail place's `pitch`); the cave and stair views are views, no longer run holds)
ROUTES = ["up", "left", "right"]
RATE = 0.5


def env_for(tmp, cam):
    e = {"XDG_DATA_HOME": tmp + "/data", "RW_DOOM_WORLDS": "1", "RW_RUN_VIRTUAL": "1", "RW_STORY_RATE": str(RATE), "RW_RUN_START": SCENE, "RW_RUN_BOT": "perfect", "RW_STORY_CAM": cam}
    return e


def shoot(tmp, name, cam, res, secs=3):
    steps = "%d:shot:%s" % (int((secs + 2.0) / RATE) + 2, name)
    text = ss.godot(["--path", ROOT, "--resolution", res, "-s", "tools/shoot.gd", "--", "res://src/run/run_play.tscn", tmp, steps], env_for(tmp, cam))
    bad = [ln for ln in text.splitlines() if ("ERROR" in ln or "SCRIPT" in ln) and not any(k in ln for k in ("RID allocations", "leaked", "still in use", "ObjectDB", "WASAPI", "ERR_CANT_OPEN"))]
    for ln in bad:
        print("  ", ln)
    p = os.path.join(tmp, name + ".png")
    return Image.open(p).convert("RGB") if os.path.exists(p) else None


# round 2: the guide-state captures (DOOM_WORLDS_BRIEF.md section 8): the run's own camera (no RW_STORY_CAM), the guide ahead tapped at beat 50 of the choice window (RW_RUN_SELECT);
# `selected` is the hold just after the tap, `committed` the first frame of the walk-off (a tapped guide commits at once: "you chose, you go")
STATE_HOT = "doom_underworld.exit_mothership"
STATES = [("selected", 50.4), ("committed", 51.6)]


def shoot_states(tmp, res="1280x720"):
    steps = ["%d:shot:state_%s" % (int((b * 60.0 / 174.0 + 2.0) / RATE) + 2, n) for n, b in STATES]
    env = {"XDG_DATA_HOME": tmp + "/data_states", "RW_DOOM_WORLDS": "1", "RW_RUN_VIRTUAL": "1", "RW_STORY_RATE": str(RATE), "RW_RUN_START": SCENE, "RW_RUN_BOT": "perfect",
           "RW_RUN_SELECT": STATE_HOT + "@50"}
    ss.godot(["--path", ROOT, "--resolution", res, "-s", "tools/shoot.gd", "--", "res://src/run/run_play.tscn", tmp] + steps, env)
    out = {}
    for n, _b in STATES:
        q = os.path.join(tmp, "state_%s.png" % n)
        if os.path.exists(q):
            out[n] = Image.open(q).convert("RGB")
    return out


def label(im, text, w, h):
    out = Image.new("RGB", (w, h + 16), (12, 12, 20))
    out.paste(im.resize((w, h), Image.LANCZOS), (0, 16))
    ImageDraw.Draw(out).text((4, 2), text, fill=(230, 230, 240))
    return out


def save_under(im, path, limit):
    q = 85
    while True:
        im.save(path, quality=q, optimize=True)
        if os.path.getsize(path) < limit or q <= 35:
            break
        q -= 5
    print("wrote", path, os.path.getsize(path) // 1024, "KB (quality %d)" % q)


def poses(route):
    text = ss.godot(["--headless", "--audio-driver", "Dummy", "--path", ROOT, "-s", "tools/doom/walk_underworld.gd", "--", SCENE, route])
    if "SCRIPT ERROR" in text:
        print(text)
        sys.exit(1)
    return text


def main(out):
    only = os.environ.get("RW_SHOTS", "")
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="rw_underworld_").replace("\\", "/")
    shots = {}
    for asp, res in (("16x9", "1280x720"), ("20x9", "1600x720")):
        for name, wp in SHOTS:
            if only and not re.search(only, name):
                continue
            im = shoot(tmp, "%s_%s" % (name, asp), wp, res)
            if im is not None:
                shots[(name, asp)] = im
                if os.environ.get("RW_KEEP"):  # full-size copies for tools/doom/frame_check.py (never committed)
                    os.makedirs(os.environ["RW_KEEP"], exist_ok=True)
                    im.save(os.path.join(os.environ["RW_KEEP"], "%s_%s.jpg" % (name, asp)), quality=92)
                print("shot", name, asp)
    states = shoot_states(tmp) if not only or re.search(only, "state") else {}
    for n, im in states.items():
        if os.environ.get("RW_KEEP"):
            im.save(os.path.join(os.environ["RW_KEEP"], "state_%s.jpg" % n), quality=92)  # (not *_16x9: frame_check's eight are the viewpoints)
        print("shot state", n)
    # --- the one contact sheet: the painting beside the reference viewpoint, then every shot as a 16:9 | 20:9 pair
    W = 640
    rows = []
    if os.path.exists(PAINTING) and ("ref", "16x9") in shots:
        pt = Image.open(PAINTING).convert("RGB")
        row = Image.new("RGB", (2 * W, 360 + 16 + 16), (12, 12, 20))
        row.paste(label(pt, "the painting (Three Paths Across the Basalt Abyss-4)", W, 360), (0, 0))
        row.paste(label(shots[("ref", "16x9")], "ref 16:9 (uw_ref, choice viewpoint, 8 bars still)", W, 360), (W, 0))
        rows.append(row)
        rows.append(None)  # (the 20:9 ref goes in the next pair with a blank on the left)
    names = [n for n, _ in SHOTS]
    for n in names:
        a, b = shots.get((n, "16x9")), shots.get((n, "20x9"))
        if a is None or b is None:
            continue
        if n == "ref":
            continue
        row = Image.new("RGB", (2 * W, 360 + 16), (12, 12, 20))
        row.paste(label(a, "%s 16:9" % n, W, 360), (0, 0))
        row.paste(label(b, "%s 20:9" % n, W, 288), (W, 0))
        rows.append(row)
    if ("ref", "20x9") in shots:
        r20 = Image.new("RGB", (2 * W, 288 + 16), (12, 12, 20))
        r20.paste(label(shots[("ref", "20x9")], "ref 20:9", W, 288), (0, 0))
        rows[rows.index(None)] = r20
    if states:  # the guide-state pair: selected | committed (16:9, the run's own camera)
        row = Image.new("RGB", (2 * W, 360 + 16), (12, 12, 20))
        for k, n in enumerate(("selected", "committed")):
            if n in states:
                row.paste(label(states[n], "%s (the guide ahead tapped at beat 50, the run's own camera)" % n, W, 360), (k * W, 0))
        rows.append(row)
    rows = [r for r in rows if r is not None]
    if rows:
        sheet = Image.new("RGB", (2 * W, sum(r.height for r in rows)), (12, 12, 20))
        y = 0
        for r in rows:
            sheet.paste(r, (0, y))
            y += r.height
        save_under(sheet, os.path.join(out, "contact.jpg"), 1000 * 1024)
    # --- the walk strip: three routes, six frames each
    if not only:
        strip_rows = []
        for route in ROUTES:
            text = poses(route)
            lines = [ln for ln in text.splitlines() if ln.startswith("WALK")]
            with open(os.path.join(out, "walk_%s.txt" % route), "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(ln for ln in text.splitlines() if ln.startswith(("WALK", "HOLD", "MOVE"))) + "\n")
            pick = [0, 2, 4, 6, 8, 11]
            cells = []
            for k in pick:
                m = ss.POSE.match(lines[k])
                i, t, cam, sec, ground, above = m.groups()
                im = shoot(tmp, "walk_%s_%02d" % (route, k), "@" + cam, "1280x720")
                if im is not None:
                    cells.append(label(im, "%s %s t=%ss floor %s" % (route, i, t, ground), 280, 158))
            if cells:
                row = Image.new("RGB", (len(cells) * 280, 158 + 16), (12, 12, 20))
                for c, cell in enumerate(cells):
                    row.paste(cell, (c * 280, 0))
                strip_rows.append(row)
                print("walk", route)
        if strip_rows:
            sheet = Image.new("RGB", (strip_rows[0].width, sum(r.height for r in strip_rows)), (12, 12, 20))
            y = 0
            for r in strip_rows:
                sheet.paste(r, (0, y))
                y += r.height
            save_under(sheet, os.path.join(out, "walk_strip.jpg"), 500 * 1024)
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "shots", "doom", "underworld"))
