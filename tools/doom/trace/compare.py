"""Side-by-side of the ian-albert render (left, shrunk) and the traced plan (right, rotated 45 degrees clockwise so north is the upper right like the render).
python -I tools/doom/trace/compare.py [scene ...]   -> docs/shots/doom/compare_<scene>.jpg (under 300 KB; the renders themselves are never committed)
Needs Pillow (the project's art tools use it already) and the renders in RW_DOOM_RENDERS (default C:\\Users\\joesa\\rw-audio-work\\doom\\renders).
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RENDERS = os.environ.get("RW_DOOM_RENDERS", r"C:\Users\joesa\rw-audio-work\doom\renders")


def main(argv):
    with open(os.path.join(ROOT, "tools", "doom", "scenes.json"), encoding="utf-8") as f:
        scenes = json.load(f)
    for scene in argv or list(scenes):
        e = scenes[scene]
        render = Image.open(os.path.join(RENDERS, e["map"] + ".jpg")).convert("RGB")
        plan = Image.open(os.path.join(ROOT, e["plan"])).convert("RGB")
        plan = plan.rotate(-45, expand=True, fillcolor=(14, 16, 22), resample=Image.BICUBIC)
        H = 640
        a = render.resize((round(render.width * H / render.height), H), Image.LANCZOS)
        b = plan.resize((round(plan.width * H / plan.height), H), Image.LANCZOS)
        out = Image.new("RGB", (a.width + b.width + 8, H), (40, 40, 40))
        out.paste(a, (0, 0))
        out.paste(b, (a.width + 8, 0))
        path = os.path.join(ROOT, "docs", "shots", "doom", "compare_%s.jpg" % scene)
        q = 80
        while True:
            out.save(path, quality=q)
            if os.path.getsize(path) <= 290 * 1024 or q <= 40:
                break
            q -= 10
        print(scene, path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main(sys.argv[1:])
