"""The Balcony's three guides (docs/doom/scenes/balcony.md): `floor` (left: braids, magenta top, silver trousers: the Lounge's floor guide sprites, re-saved), `booth` (right: teal hair, orange
jacket, dark trousers) and `mothership` (ahead: white hair, the long pale-violet coat, as the Booth's), 160 x 256 billboard sprites in the Warehouse guides' layout (idle 1, available 5,
selected 2, committed 2), written to assets/story/doom_balcony/textures/guide_<who>_<state>_<n>.png.

PLACEHOLDER art (procedural, make_guides.py's sheet), not the painterly finish of art/reference/standard/guide_floor_sprite_standard.png. Names and frame counts are the contract.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_guides as mg  # noqa: E402
import make_lounge_guides as lg  # noqa: E402

OUT = os.path.join(mg.ROOT, "assets", "story", "doom_balcony", "textures")


def main():
    os.makedirs(OUT, exist_ok=True)
    base = {k: dict(v) for k, v in mg.GUIDES.items()}
    variants = {
        "booth": ("bar", dict(skin="#d8a880", hair="#2ab8b0", top="#e87820", vest="#d86a18", trousers="#2a2630", shoes="#14121a", curly=False, moustache=False, glasses=False, accent="#f0e8e0")),
        "mothership": ("stage", dict(skin="#d8c8e0", hair="#e8e0f8", top="#6a3a8e", vest="#4a2a6a", trousers="#2a1a3a", shoes="#1a1228", accent="#d8b0f0")),
    }
    n = 0
    for who, (arch, patch) in variants.items():
        mg.GUIDES[arch] = {**base[arch], **patch}
        for state, frames in mg.FRAMES.items():
            for i in range(frames):
                mg.draw_guide(arch, state, i).save(os.path.join(OUT, "guide_%s_%s_%d.png" % (who, state, i)))
                n += 1
        mg.GUIDES[arch] = dict(base[arch])
    for state, frames in mg.FRAMES.items():  # the Floor guide: the Lounge's sprites, the painting's braids, magenta top and silver trousers
        for i in range(frames):
            lg.draw("floor", state, i).save(os.path.join(OUT, "guide_floor_%s_%d.png" % (state, i)))
            n += 1
    return n


CROPPED = {"floor": "floor_dock", "mothership": "mothership_booth", "booth": "booth_balcony8"}  # who: the crop (tools/doom/art/make_dock_crop.py CROPS)


def main_cropped():
    """Stage D polish (ruling 36): all three guides CROPPED from the paintings: the Booth guide from this scene's painting (225 px there, leaning in the cabin door); the Floor
    guide from the Dock's painting (350 px there; in this one the stair's railing crosses her legs), the Mothership guide from the Booth's painting (200 px; 85 px in this one).
    `main` above (the procedural placeholders) is kept for reference only."""
    import make_dock_crop as mc
    os.makedirs(OUT, exist_ok=True)
    return sum(mc.write(mc.CROPS[key], OUT, who) for who, key in CROPPED.items())


if __name__ == "__main__":
    print("wrote %d guide frames to %s" % (main_cropped(), OUT))
