#!/usr/bin/env python3
"""The Chill-out Lounge's shot tooling (docs/doom/scenes/lounge.md). The per-frame shots of tools/doom/shoot_lounge.sh are throw-aways (a temp folder); what is kept in docs/shots/doom/lounge/ is

    contact_lounge.jpg   ONE contact sheet under 1 MB: the painting beside the reference viewpoint, then every viewpoint, hold, approach and the stay loop at 16:9 and 20:9
    walk_strip.jpg       the camera path of the three routes (ahead, left, right) and the stay loop, 6 frames each, the eye's real height (under 500 KB)
    walk_<route>.txt     the pose tables (12 frames each) and the hold figures (how still the camera is during a hold)

    python3 tools/doom/shoot_lounge.py <tmp_dir_with_jpgs> <out_dir>        the sheet (run by shoot_lounge.sh)
    python3 tools/doom/shoot_lounge.py walk <out_dir> [ahead] [left] [right] [stay]
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shoot_scene as ss  # noqa: E402  (bash_exe, godot)

SCENE = "doom_lounge"
PAINTING = os.path.join(ROOT, "art", "reference", "doom_worlds", "Mustard octagonal lounge of three routes-2.png")
POSE = ss.POSE
LABELS = {"ref": "reference viewpoint lg_ref", "reveal_west": "reveal west", "reveal_north": "reveal north (Dock street)", "reveal_east": "reveal east (Bar arch)", "arrive_passage": "arrival (blue passage)",
          "approach_dock": "threshold ahead (Dock)", "approach_bar": "threshold left (Bar)", "approach_floor": "threshold right (Floor)", "stumble": "stumble", "stay_1": "stay loop t=14 s",
          "stay_2": "stay loop t=28 s", "stay_3": "stay loop t=42 s", "stay_4": "stay loop t=56 s"}
ORDER = list(LABELS)


def save_under(im, path, limit, q=82):
    while True:
        im.save(path, quality=q, optimize=True, progressive=True)
        if os.path.getsize(path) < limit or q <= 35:
            return q
        q -= 5


def sheet(tmp, out):
    w = 440
    items = []
    if os.path.exists(PAINTING):
        p = Image.open(PAINTING).convert("RGB")
        items.append(("the painting (target)", p.resize((w, int(w * p.height / p.width)), Image.LANCZOS)))
    for name in ORDER:
        for asp in ("16x9", "20x9"):
            f = os.path.join(tmp, "%s_%s.jpg" % (name, asp))
            if os.path.exists(f):
                im = Image.open(f).convert("RGB")
                items.append(("%s %s" % (LABELS[name], asp.replace("x", ":")), im.resize((w, int(w * im.height / im.width)), Image.LANCZOS)))
    if not items:
        print("no shots in", tmp)
        return
    cols = 4
    rows = [items[i:i + cols] for i in range(0, len(items), cols)]
    heights = [max(im.height for _l, im in r) + 14 for r in rows]
    s = Image.new("RGB", (cols * w, sum(heights)), (12, 12, 20))
    d = ImageDraw.Draw(s)
    y = 0
    for r, hh in zip(rows, heights):
        for k, (lb, im) in enumerate(r):
            s.paste(im, (k * w, y + 14))
            d.text((k * w + 4, y + 1), lb, fill=(230, 230, 240))
        y += hh
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "contact_lounge.jpg")
    q = save_under(s, path, 950 * 1024)
    print("contact sheet", path, len(items), "images", os.path.getsize(path) // 1024, "KB q", q)


def walk(out, routes):
    os.makedirs(out, exist_ok=True)
    strips = []
    for route in routes:
        text = ss.godot(["--headless", "--audio-driver", "Dummy", "--path", ROOT, "-s", "tools/doom/walk_poses.gd", "--", SCENE, route, "res://content/run/doom/run.json", SCENE])
        if "SCRIPT ERROR" in text:
            print("SCRIPT ERROR in walk_poses.gd:\n" + text)
            sys.exit(1)
        rows = [ln for ln in text.splitlines() if ln.startswith(("WALK", "HOLD", "MOVE"))]
        poses = [ln for ln in rows if ln.startswith("WALK")]
        with open(os.path.join(out, "walk_%s.txt" % route), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(rows) + "\n")
        pick = [0, 2, 4, 6, 9, 11] if len(poses) == 12 else list(range(len(poses)))
        pick = [poses[i] for i in pick if i < len(poses)]
        tmp = tempfile.mkdtemp(prefix="rw_lwalk_")
        tmp_u = tmp.replace("\\", "/")
        ims = []
        for ln in pick:
            i, t, cam, sec, ground, above = POSE.match(ln).groups()
            name = "%s_%02d" % (route, int(i))
            env = {"XDG_DATA_HOME": tmp_u + "/data", "RW_DOOM_WORLDS": "1", "RW_RUN_VIRTUAL": "1", "RW_STORY_RATE": "0.5", "RW_RUN_START": SCENE, "RW_RUN_BOT": "perfect", "RW_STORY_CAM": "@" + cam}
            ss.godot(["--path", ROOT, "--resolution", "1280x720", "-s", "tools/shoot.gd", "--", "res://src/run/run_play.tscn", tmp_u, "12:shot:" + name], env)
            f = os.path.join(tmp, name + ".png")
            if os.path.exists(f):
                ims.append((Image.open(f).convert("RGB"), "%s %d  t=%ss  eye %s m over the floor" % (route, int(i), t, above)))
                print("shot", name)
        shutil.rmtree(tmp, ignore_errors=True)
        strips.append(ims)
    if strips:
        w, h, cols = 320, 180, 6
        s = Image.new("RGB", (cols * w, len(strips) * (h + 14)), (12, 12, 20))
        d = ImageDraw.Draw(s)
        for r, ims in enumerate(strips):
            for k, (im, lb) in enumerate(ims):
                x, y = k * w, r * (h + 14)
                s.paste(im.resize((w, h), Image.LANCZOS), (x, y + 14))
                d.text((x + 3, y + 1), lb, fill=(230, 230, 240))
        path = os.path.join(out, "walk_strip.jpg")
        q = save_under(s, path, 480 * 1024)
        print("walk strip", path, os.path.getsize(path) // 1024, "KB q", q)


if __name__ == "__main__":
    if sys.argv[1] == "walk":
        walk(sys.argv[2], sys.argv[3:] or ["ahead", "left", "right", "stay"])
    else:
        sheet(sys.argv[1], sys.argv[2])
