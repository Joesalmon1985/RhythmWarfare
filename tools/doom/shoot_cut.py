#!/usr/bin/env python3
"""A strip of a real cut between two Doom geography worlds (docs/engine/GEOGRAPHY_WORLDS.md): the last beats of the threshold walk, the passage frame shutting, the first beats of the
arrival in the next world, at 16:9 (1280x720), as ONE jpg.

    python3 tools/doom/shoot_cut.py                          the Warehouse to the Bar (left)  -> docs/shots/doom/cuts/warehouse_to_bar.jpg
    python3 tools/doom/shoot_cut.py <start> <dir> <out.jpg>  another cut from a scene's first phase (dir: up | left | right)

Every frame is the real run scene (RW_DOOM_WORLDS=1, RW_RUN_VIRTUAL=1, the perfect bot, RW_RUN_ROUTES=<dir>), the HUD and pads on, shot by tools/shoot.gd in one run at
RW_STORY_RATE seconds of song per frame. The phase boundary is beat 64 of the first phase; the labels are the beat each frame was asked for (one frame of slack either way).
"""
import os
import shutil
import sys
import tempfile

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shoot_scene as ss  # noqa: E402

ROOT = ss.ROOT
BPM = 174.0  # content/run/run.json timing.bpm
RATE = 0.05
BEATS = [(61.3, "walk"), (62.3, "walk"), (63.0, "walk"), (63.5, "frame"), (63.9, "frame"), (64.2, "arrive"), (66.0, "arrive"), (69.0, "arrive")]
TW, TH = 480, 270


def main(start, dr, out):
    beat = 60.0 / BPM
    tmp = tempfile.mkdtemp(prefix="rw_cut_")
    tmp_u = tmp.replace("\\", "/")
    steps = []
    for i, (b, _k) in enumerate(BEATS):
        frame = int(round((b * beat + 2.0) / RATE)) + 1
        steps.append("%d:shot:cut_%02d" % (frame, i))
    env = {"XDG_DATA_HOME": tmp_u + "/data", "RW_DOOM_WORLDS": "1", "RW_RUN_VIRTUAL": "1", "RW_STORY_RATE": str(RATE), "RW_RUN_START": start, "RW_RUN_BOT": "perfect",
           "RW_RUN_ROUTES": dr}
    text = ss.godot(["--path", ROOT, "--resolution", "1280x720", "-s", "tools/shoot.gd", "--", "res://src/run/run_play.tscn", tmp_u] + steps, env, timeout=600)
    errs = [ln for ln in text.splitlines() if "SCRIPT ERROR" in ln]
    if errs:
        print("\n".join(errs[:5]))
    ims = []
    for i in range(len(BEATS)):
        f = os.path.join(tmp, "cut_%02d.png" % i)
        ims.append(Image.open(f).convert("RGB").resize((TW, TH), Image.LANCZOS) if os.path.exists(f) else Image.new("RGB", (TW, TH), (60, 0, 0)))
    cols = 4
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TW, rows * (TH + 22)), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(ims):
        x, y = (i % cols) * TW, (i // cols) * (TH + 22)
        sheet.paste(im, (x, y + 22))
        b, k = BEATS[i]
        d.text((x + 6, y + 4), "beat %.1f  %s  (%s %s)" % (b, k, start, dr), fill=(235, 235, 235))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out, quality=85)
    shutil.rmtree(tmp, ignore_errors=True)
    print("cut strip", out, "%d KB" % (os.path.getsize(out) // 1024), "SCRIPT ERRORS:", len(errs))


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3:
        main(a[0], a[1], a[2])
    else:
        main("doom_warehouse", "left", os.path.join(ROOT, "docs", "shots", "doom", "cuts", "warehouse_to_bar.jpg"))
