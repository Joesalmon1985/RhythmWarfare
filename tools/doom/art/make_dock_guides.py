"""The Loading Dock's three guides (docs/doom/scenes/dock.md), 160 x 256 billboard sprites in the Warehouse guides' sheet layout (idle 1, available 5, selected 2, committed 2):

  * `floor` (left, through the club door: braids, magenta sequin top, silver trousers): the Lounge's Floor guide (tools/doom/art/make_lounge_guides.py), the same figure;
  * `mothership` (ahead, at the street's end: violet, pale hair, a pair of curved horns, long violet coat);
  * `underworld` (right, by the furnace: red skin, dark horns, a gold-brown waistcoat).

    python -I tools/doom/art/make_dock_guides.py     writes assets/story/doom_dock/textures/guide_<who>_<state>_<n>.png

Stage D polish: all three are now CROPPED from the paintings (see `main`). The text below describes the earlier procedural placeholders, which `variants` still draws.
PLACEHOLDER art, procedural, like the Warehouse's: NOT the painterly finish of art/reference/standard/guide_floor_sprite_standard.png. The painting's figures are the brief (the Underworld guide
sits on crates with a drum, the Mothership guide stands with an arm out; these are standing sprites with the shared poses). An art pass replaces the PNGs; names and frame counts are the contract.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_guides as mg  # noqa: E402
import make_lounge_guides as lg  # noqa: E402
from PIL import ImageDraw  # noqa: E402

ROOT = mg.ROOT
OUT = os.path.join(ROOT, "assets", "story", "doom_dock", "textures")
hexc = mg.hexc


def horns(im, col, tip="#e8e0c8", spread=1.0):
    """A pair of curved horns on the head (the head's top is about y 27, centre x 80), drawn over the finished sprite."""
    d = ImageDraw.Draw(im)
    for sx in (-1, 1):
        x0 = 80 + sx * 12
        pts = [(x0, 36), (x0 + sx * 6 * spread, 26), (x0 + sx * 12 * spread, 14), (x0 + sx * 12 * spread, 4), (x0 + sx * 15 * spread, 12), (x0 + sx * 15 * spread, 26), (x0 + sx * 7 * spread, 40)]
        d.polygon(pts, fill=hexc("#14101e"))
        inner = [(x0 + sx * 1, 36), (x0 + sx * 6 * spread, 27), (x0 + sx * 11 * spread, 15), (x0 + sx * 12 * spread, 7), (x0 + sx * 13 * spread, 14), (x0 + sx * 12 * spread, 26), (x0 + sx * 6 * spread, 38)]
        d.polygon(inner, fill=hexc(col))
        d.polygon([(x0 + sx * 11 * spread, 14), (x0 + sx * 12 * spread, 6), (x0 + sx * 13 * spread, 14)], fill=hexc(tip))
    return im


def variants():
    base = {k: dict(v) for k, v in mg.GUIDES.items()}
    return base, {
        "mothership": ("stage", dict(skin="#d8c8e0", hair="#e8e0f8", top="#6a3a8e", vest="#4a2a6a", trousers="#2a1a3a", shoes="#1a1228", accent="#d8b0f0"), "#cfc0e8"),
        "underworld": ("bar", dict(skin="#b8402c", hair="#2a1410", top="#8a2a20", vest="#a0782c", trousers="#4a1c18", shoes="#1c100c", curly=False, moustache=False, accent="#e0b020"), "#5a3626"),
    }


CROPPED = {"floor": "floor_dock", "mothership": "mothership_booth", "underworld": "underworld_dock7"}  # who: the crop (tools/doom/art/make_dock_crop.py CROPS)


def main():
    """Stage D polish (ruling 36): the three guides are CROPPED from the paintings (make_dock_crop.py): the Floor guide from this scene's painting (350 px tall there), the
    Mothership guide from the Booth's painting (200 px; 130 px in the Dock's), the Underworld guide from `Rainy Dock of Three Paths-7.png` (his legs hidden there: the sheet
    leaves them out and the scene seats him behind crates and his drum). The procedural figures above (`variants`, `horns`) are kept for reference only."""
    import make_dock_crop as mc
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for who, key in CROPPED.items():
        n += mc.write(mc.CROPS[key], OUT, who)
    return n

if __name__ == "__main__":
    print("wrote %d guide frames to %s" % (main(), OUT))
