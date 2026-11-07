#!/usr/bin/env python3
"""Shots of the Copper Bar (docs/doom/scenes/bar.md), at 16:9 (1280x720) and 20:9 (1600x720), as ONE contact sheet under 1 MB (no per-frame JPEGs are kept).

    python3 tools/doom/shoot_bar.py [out_dir]          default docs/shots/doom/bar   -> contact_bar.jpg (and walk_stay.jpg, walk_ahead.jpg with --walk)

Every frame is a real run scene shot (HUD and pads on, RW_STORY_CAM stands the camera): the reference viewpoint beside the painting, the stay loop's three reveal holds and the
rail camera at song times, and each of the three route walks (up to the booth, left to the Floor, right to the Chill-out) in four frames from tools/doom/walk_poses.gd's poses.
The frames go to a temporary folder; only the sheet is written to out_dir.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shoot_scene as ss  # noqa: E402

ROOT = ss.ROOT
SCENE = "doom_bar"
PAINTING = os.path.join(ROOT, "art", "reference", "doom_worlds", "Copper Basement Bar, Three Hidden Routes-3.png")
RES = {"16x9": "1280x720", "20x9": "1600x720"}
RATE = 0.5


def shoot(tmp, name, asp, cam, secs):
    """One shot; returns the PNG path or None."""
    steps = "%d:shot:%s" % (int((secs + 2.0) / RATE) + 2, name)
    env = {"XDG_DATA_HOME": tmp + "/data", "RW_DOOM_WORLDS": "1", "RW_RUN_VIRTUAL": "1", "RW_STORY_RATE": str(RATE), "RW_RUN_START": SCENE, "RW_RUN_BOT": "perfect"}
    if cam != "-":
        env["RW_STORY_CAM"] = cam
    text = ss.godot(["--path", ROOT, "--resolution", RES[asp], "-s", "tools/shoot.gd", "--", "res://src/run/run_play.tscn", tmp, steps], env, timeout=300)
    bad = [ln for ln in text.splitlines() if ("SCRIPT ERROR" in ln or "ERROR" in ln) and not any(k in ln for k in ("RID allocations", "leaked", "still in use", "ObjectDB", "WASAPI", "ERR_CANT_OPEN"))]
    if bad:
        print("  errors in", name, asp, bad[:3])
    f = os.path.join(tmp, name + ".png")
    return f if os.path.exists(f) else None


def poses(route):
    text = ss.godot(["--headless", "--audio-driver", "Dummy", "--path", ROOT, "-s", "tools/doom/walk_poses.gd", "--", SCENE, route, "res://content/run/doom/run.json", SCENE])
    if "SCRIPT ERROR" in text:
        print("SCRIPT ERROR in walk_poses.gd\n" + text)
        sys.exit(1)
    out = []
    for ln in text.splitlines():
        m = ss.POSE.match(ln) if ln.startswith("WALK") else None
        if m:
            out.append(m.groups())
    return out


def main(out):
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="rw_bar_")
    tmp_u = tmp.replace("\\", "/")
    cells = {}  # (row, col) -> (image, label)
    try:
        painting = Image.open(PAINTING).convert("RGB")
        rows = []  # each row: list of (asp, name, cam, secs, label) or "painting"
        rows.append([("painting",), ("16x9", "ref", "wb_ref", 3, "reference viewpoint 16:9"), ("20x9", "ref", "wb_ref", 3, "reference viewpoint 20:9")])
        holds = [("bridge", "wb_bridge"), ("counter", "wb_counter"), ("way", "wb_way")]
        for asp in ("16x9", "20x9"):
            rows.append([(asp, "hold_" + n, c, 3, "stay hold %s %s" % (n, asp.replace("x", ":"))) for n, c in holds] + [(asp, "stumble", "wb_ref_back", 3, "stumble %s" % asp.replace("x", ":"))])
        rows.append([("16x9", "rail_%d" % k, "-", t, "rail camera t=%ds 16:9" % t) for k, t in enumerate((14, 28, 42, 56))])
        for route, label in (("ahead", "up to the booth"), ("left", "left to the Floor"), ("right", "right to the Chill-out")):
            ps = poses(route)
            pick = [ps[i] for i in (2, 5, 8, 11)] if len(ps) >= 12 else ps
            for asp in ("16x9", "20x9"):
                rows.append([(asp, "walk_%s_%d" % (route, k), "@" + p[2], 3, "%s %d/4 %s" % (label, k + 1, asp.replace("x", ":"))) for k, p in enumerate(pick)])
        for r, row in enumerate(rows):
            for c, cell in enumerate(row):
                if cell[0] == "painting":
                    cells[(r, c)] = (painting, "the painting")
                    continue
                asp, name, cam, secs, label = cell
                f = shoot(tmp_u, name + "_" + asp, asp, cam, secs)
                if f:
                    cells[(r, c)] = (Image.open(f).convert("RGB"), label)
                    print("shot", name, asp)
        w, h = 400, 225
        ncols = max(c for _r, c in cells) + 1
        nrows = max(r for r, _c in cells) + 1
        sheet = Image.new("RGB", (ncols * w, nrows * (h + 16)), (12, 12, 20))
        d = ImageDraw.Draw(sheet)
        for (r, c), (im, label) in cells.items():
            ch = int(w * 9 / 16) if label != "the painting" and "20:9" not in label else h
            tgt = (w, h)
            x, y = c * w, r * (h + 16)
            sheet.paste(im.resize(tgt, Image.LANCZOS), (x, y + 16))
            d.text((x + 3, y + 2), label, fill=(230, 230, 240))
        path = os.path.join(out, "contact_bar.jpg")
        q = 80
        while True:
            sheet.save(path, quality=q, optimize=True)
            if os.path.getsize(path) < 900 * 1024 or q <= 40:
                break
            q -= 5
        print("sheet", path, os.path.getsize(path) // 1024, "KB", sheet.size)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if "--walk" in sys.argv:
        os.environ["RW_SCENE"] = SCENE
        ss.SCENE = SCENE
        ss.walk(out, ["stay", "ahead"])


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0] if args else os.path.join(ROOT, "docs", "shots", "doom", "bar"))
