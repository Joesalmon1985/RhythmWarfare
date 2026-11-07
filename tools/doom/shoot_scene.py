#!/usr/bin/env python3
"""Contact sheet of the shots tools/doom/shoot_scene.sh wrote: python3 tools/doom/shoot_scene.py <out_dir>  ->  <out_dir>/contact_16x9.jpg and contact_20x9.jpg (labelled, 3 columns).

    python3 tools/doom/shoot_scene.py walk <out_dir> [ahead] [stay]

The walk mode shows the camera path of the polyline moves (docs/story/HEIGHTS_AND_PATHS.md): tools/doom/walk_poses.gd plays the scene's `ahead` route (rail.routes.up) or its `stay`
loop (the good rail with its holds) on a StoryPlayer and prints 12 poses (the eye's real height included); each pose is shot on the real run scene (RW_STORY_CAM=@x:z:yaw:pitch:eye),
and the 12 frames go into one labelled strip image per route, <out_dir>/walk_<route>.jpg (4 x 3 frames, under 500 KB), with the pose table in walk_<route>.txt.
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
GODOT = os.environ.get("GODOT", os.path.join(ROOT, "tools", "dev", "godot.sh"))
SCENE = "doom_warehouse"
POSE = re.compile(r"WALK \S+ (\d+) t=(\S+) @(\S+) sector=(\S+) ground=(\S+) above=(\S+)")


def main(out):
    for asp in ("16x9", "20x9"):
        files = sorted(glob.glob(os.path.join(out, "*_%s.jpg" % asp)))
        files = [f for f in files if not os.path.basename(f).startswith("contact")]
        if not files:
            continue
        ref = [f for f in files if os.path.basename(f).startswith("ref_")]
        files = ref + [f for f in files if f not in ref]
        w = 560
        ims = [Image.open(f).convert("RGB") for f in files]
        h = int(w * ims[0].height / ims[0].width)
        cols = 3
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * w, rows * (h + 16)), (12, 12, 20))
        d = ImageDraw.Draw(sheet)
        for i, (f, im) in enumerate(zip(files, ims)):
            x, y = (i % cols) * w, (i // cols) * (h + 16)
            sheet.paste(im.resize((w, h)), (x, y + 16))
            d.text((x + 4, y + 2), os.path.basename(f).replace("_%s.jpg" % asp, ""), fill=(230, 230, 240))
        sheet.save(os.path.join(out, "contact_%s.jpg" % asp), quality=80)
        print("contact sheet", asp, len(files), "shots")


def bash_exe():
    """Git Bash on Windows (a bare `bash` can be the WSL one, which cannot see the project's path), else bash."""
    for c in (os.environ.get("BASH_EXE", ""), "C:/Program Files/Git/bin/bash.exe", "C:/Program Files/Git/usr/bin/bash.exe"):
        if c and os.path.exists(c):
            return c
    return "bash"


def godot(args, env_extra=None, timeout=300):
    env = dict(os.environ)
    env.update(env_extra or {})
    r = subprocess.run([bash_exe(), GODOT.replace("\\", "/")] + args, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
    return r.stdout


def walk(out, routes):
    os.makedirs(out, exist_ok=True)
    for route in routes:
        text = godot(["--headless", "--audio-driver", "Dummy", "--path", ROOT, "-s", "tools/doom/walk_poses.gd", "--", SCENE, route])
        if "SCRIPT ERROR" in text:
            print("SCRIPT ERROR in walk_poses.gd:\n" + text)
            sys.exit(1)
        rows = [ln for ln in text.splitlines() if ln.startswith(("WALK", "HOLD", "MOVE"))]
        poses = [ln for ln in rows if ln.startswith("WALK")]
        with open(os.path.join(out, "walk_%s.txt" % route), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(rows) + "\n")
        tmp = tempfile.mkdtemp(prefix="rw_walk_")
        tmp_u = tmp.replace("\\", "/")
        ims, labels = [], []
        for ln in poses:
            i, t, cam, sec, ground, above = POSE.match(ln).groups()
            name = "%s_%02d" % (route, int(i))
            env = {"XDG_DATA_HOME": tmp_u + "/data", "RW_DOOM_WORLDS": "1", "RW_RUN_VIRTUAL": "1", "RW_STORY_RATE": "0.5", "RW_RUN_START": SCENE, "RW_RUN_BOT": "perfect", "RW_STORY_CAM": "@" + cam}
            godot(["--path", ROOT, "--resolution", "1280x720", "-s", "tools/shoot.gd", "--", "res://src/run/run_play.tscn", tmp_u, "12:shot:" + name], env)
            f = os.path.join(tmp, name + ".png")
            if not os.path.exists(f):
                print("no shot for", name)
                continue
            ims.append(Image.open(f).convert("RGB"))
            labels.append("%d  t=%ss  %s  floor %s  eye over floor %s m" % (int(i), t, sec, ground, above))
            print("shot", name)
        if ims:
            w, h, cols = 400, 225, 4
            rows_n = (len(ims) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * w, rows_n * (h + 16)), (12, 12, 20))
            d = ImageDraw.Draw(sheet)
            for k, (im, lb) in enumerate(zip(ims, labels)):
                x, y = (k % cols) * w, (k // cols) * (h + 16)
                sheet.paste(im.resize((w, h), Image.LANCZOS), (x, y + 16))
                d.text((x + 3, y + 2), lb, fill=(230, 230, 240))
            path = os.path.join(out, "walk_%s.jpg" % route)
            q = 80
            while True:
                sheet.save(path, quality=q)
                if os.path.getsize(path) < 480 * 1024 or q <= 40:
                    break
                q -= 10
            print("strip", path, os.path.getsize(path) // 1024, "KB")
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    if sys.argv[1] == "walk":
        walk(sys.argv[2], sys.argv[3:] or ["ahead", "stay"])
    else:
        main(sys.argv[1])
